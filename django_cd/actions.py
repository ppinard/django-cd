""""""

# Standard library modules.
import abc
import datetime
from pathlib import Path
import shlex
import subprocess
import time
import sys
import venv
import tempfile
import string
import xml.etree.ElementTree as ElementTree

# Third party modules.
import yarl
from loguru import logger

# Local modules.
from .models import ActionRun, RunState, TestResult

# Globals and constants variables.


class Action(metaclass=abc.ABCMeta):
    def __init__(self, name, relpath=""):
        self.name = name
        self.relpath = relpath
        self._actionrun = None

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}({self.name})>"

    def __str__(self) -> str:
        return self.name

    def run(self, jobrun, workdir, env):
        # Create ActionRun
        self._actionrun = ActionRun.objects.create(
            name=self.name, jobrun=jobrun, state=RunState.RUNNING
        )

        # Update env
        workdir = Path(workdir).joinpath(self.relpath)
        env.update(
            {"workdir": workdir, "jobname": jobrun.name, "actionname": self.name}
        )

        # Start
        start_time = time.time()
        outputs = []

        try:
            state = self._run(workdir, outputs, env)

        except Exception as ex:
            logger.exception(f"While running action {self.name}")
            state = RunState.ERROR
            outputs.append(str(ex))

        # Save ActionRun
        end_time = time.time()
        self._actionrun.state = state
        self._actionrun.output = "\n".join(outputs)
        self._actionrun.duration = datetime.timedelta(seconds=end_time - start_time)
        self._actionrun.save(update_fields=["duration", "state", "output"])

        return state

    @abc.abstractmethod
    def _run(self, workdir, outputs, env):
        raise NotImplementedError

    def add_testresult(self, name, state, duration, output):
        if self._actionrun is None:
            return
        TestResult.objects.create(
            name=name,
            actionrun=self._actionrun,
            state=state,
            duration=duration,
            output=output,
        )


def _run_command(args, cwd, outputs, env, shell=False):
    # Interpolate args
    args = [string.Template(arg).substitute(env) for arg in args]

    # Run
    outputs.append(f'> {" ".join(args)}')
    process = subprocess.run(
        args,
        shell=shell,
        capture_output=True,
        cwd=cwd,
    )

    # Update outputs
    outputs += process.stdout.decode("utf8").splitlines()
    outputs += process.stderr.decode("utf8").splitlines()

    return RunState.SUCCESS if process.returncode == 0 else RunState.FAILED


def _run_python_command(args, cwd, outputs, env):
    python_exe = env.get("PYTHON_EXE", sys.executable)
    args = [python_exe] + list(args)
    return _run_command(args, cwd, outputs, env, shell=False)


class CommandAction(Action):
    def __init__(self, name, args, shell=False, relpath=""):
        super().__init__(name, relpath)
        self.args = shlex.split(args)
        self.shell = shell

    def _run(self, workdir, outputs, env):
        return _run_command(self.args, workdir, outputs, env, self.shell)


class GitCheckoutAction(Action):
    def __init__(self, name, repos_url, branch="master", relpath=""):
        super().__init__(name, relpath)
        self.repos_url = yarl.URL(repos_url)

        self.repos_name = self.repos_url.name
        self.repos_name = self.repos_name.rsplit(".")[0]

        self.branch = branch

    def _run(self, workdir, outputs, env):
        reposdir = workdir.joinpath(self.repos_name)

        # Clone
        if not reposdir.joinpath(".git").exists():
            args = ["git", "clone", str(self.repos_url)]
            state = _run_command(args, workdir, outputs, env, shell=False)
            if state != state.SUCCESS:
                return state

        # Clean
        args = ["git", "clean", "-xdf"]
        state = _run_command(args, reposdir, outputs, env, shell=False)
        if state != state.SUCCESS:
            return state

        # Checkout
        args = ["git", "checkout", self.branch]
        state = _run_command(args, reposdir, outputs, env, shell=False)
        if state != state.SUCCESS:
            return state

        # Pull
        args = ["git", "pull"]
        state = _run_command(args, reposdir, outputs, env, shell=False)

        return state


class PythonVirtualEnvAction(Action):
    def _run(self, workdir, outputs, env):
        # Create environment
        builder = venv.EnvBuilder(clear=True, with_pip=True)
        context = builder.ensure_directories(workdir)
        builder.create(workdir)

        env["PYTHON_EXE"] = context.env_exe

        # Update pip and setuptools
        return _run_python_command(
            ["-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"],
            workdir,
            outputs,
            env,
        )


class PythonAction(Action):
    def __init__(self, name, args, relpath=""):
        super().__init__(name, relpath)
        self.args = shlex.split(args)

    def _run(self, workdir, outputs, env):
        return _run_python_command(self.args, workdir, outputs, env)


class PythonPytestAction(Action):
    def __init__(self, name, args="", relpath=""):
        super().__init__(name, relpath)
        self.args = shlex.split(args)

    def _run(self, workdir, outputs, env):
        state = _run_python_command(
            ["-m", "pip", "install", "-U", "pytest"], workdir, outputs, env
        )
        if state != RunState.SUCCESS:
            return state

        with tempfile.NamedTemporaryFile(suffix=".xml", delete=True) as tmpfp:
            args = ["-m", "pytest", f"--junitxml={tmpfp.name}"] + self.args
            state = _run_python_command(args, workdir, outputs, env)
            self._parse_junitxml(tmpfp.name)

        return state

    def _parse_junitxml(self, filepath):
        root = ElementTree.parse(filepath).getroot()

        for element in root.iterfind(".//testcase"):
            name = f"{element.get('classname', '')}.{element.get('name', '')}"
            duration = datetime.timedelta(seconds=float(element.get("time", 0.0)))

            state = RunState.SUCCESS
            output = ""
            if element.find("error") is not None:
                state = RunState.ERROR
                output = element.findtext("error", "")
            elif element.find("failure") is not None:
                state = RunState.FAILED
                output = element.findtext("failure", "")
            elif element.find("skipped") is not None:
                state = RunState.SKIPPED
                output = element.findtext("skipped", "")

            self.add_testresult(name, state, duration, output)


class MsbuildAction(Action):
    VSDEVCMD = r"%ProgramFiles(x86)%\Microsoft Visual Studio\2019\Entreprise\Common7\Tools\VsDevCmd.bat"

    def __init__(
        self,
        name,
        solution_filepath,
        relpath="",
        file_logger_parameters=None,
        console_logger_parameters=None,
        maxcpucount=1,
        node_reuse=True,
        verbosity="normal",
        property=None,
        target=None,
    ):
        super().__init__(name, relpath)
        self.solution_filepath = solution_filepath
        self.file_logger_parameters = file_logger_parameters
        self.console_logger_parameters = console_logger_parameters
        self.maxcpucount = maxcpucount
        self.node_reuse = node_reuse
        self.verbosity = verbosity
        self.property = property
        self.target = target

    def _run(self, workdir, outputs, env):
        state = _run_command([self.VSDEVCMD], workdir, outputs, env)
        if state != RunState.SUCCESS:
            return state

        # Run msbuild
        args = ["msbuild", self.solution_filepath]
        if self.file_logger_parameters is not None:
            args += ["/fl", f"/flp:{self.file_logger_parameters}"]
        if self.console_logger_parameters is not None:
            args += [f"/clp:{self.console_logger_parameters}"]
        if self.maxcpucount is not None:
            args += [f"/maxCpuCount:{self.maxCpuCount}"]
        if self.node_reuse is not None:
            args += [f"/nr:{self.nose_reuse}"]
        if self.verbosity is not None:
            args += [f"/v:{self.verbosity}"]
        if self.property is not None:
            args += [f"/p:{self.property}"]
        if self.target is not None:
            args += [f"/t:{self.target}"]

        return _run_command(args, workdir, outputs, env)
