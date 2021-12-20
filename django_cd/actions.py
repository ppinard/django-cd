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
        workdir = Path(workdir).joinpath(self.relpath)
        self._actionrun = ActionRun.objects.create(
            name=self.name, jobrun=jobrun, state=RunState.RUNNING
        )
        start_time = time.time()
        outputs = []

        try:
            state = self._run(workdir, outputs, env)

        except Exception as ex:
            logger.exception(f"While running action {self.name}")
            state = RunState.ERROR
            outputs.append(str(ex))

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


def _run_command(args, cwd, outputs, shell=False):
    outputs.append(f'> {" ".join(args)}')
    process = subprocess.run(
        args,
        shell=shell,
        capture_output=True,
        cwd=cwd,
    )

    outputs += process.stdout.decode("utf8").splitlines()
    outputs += process.stderr.decode("utf8").splitlines()

    return RunState.SUCCESS if process.returncode == 0 else RunState.FAILED


def _run_python_command(args, cwd, outputs, env):
    python_exe = env.get("PYTHON_EXE", sys.executable)
    args = [python_exe] + list(args)
    return _run_command(args, cwd, outputs)


class CommandAction(Action):
    def __init__(self, name, args, shell=False, relpath=""):
        super().__init__(name, relpath)
        self.args = shlex.split(args)
        self.shell = shell

    def _run(self, workdir, outputs, env):
        return _run_command(self.args, workdir, outputs, self.shell)


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
            state = _run_command(args, workdir, outputs, shell=False)
            if state != state.SUCCESS:
                return state

        # Clean
        args = ["git", "clean", "-xdf"]
        state = _run_command(args, reposdir, outputs, shell=False)
        if state != state.SUCCESS:
            return state

        # Checkout
        args = ["git", "checkout", self.branch]
        state = _run_command(args, reposdir, outputs, shell=False)
        if state != state.SUCCESS:
            return state

        # Pull
        args = ["git", "pull"]
        state = _run_command(args, reposdir, outputs, shell=False)

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
    def _run(self, workdir, outputs, env):
        state = _run_python_command(
            ["-m", "pip", "install", "-U", "pytest"], workdir, outputs, env
        )
        if state != RunState.SUCCESS:
            return state

        with tempfile.NamedTemporaryFile(suffix=".xml", delete=True) as tmpfp:
            state = _run_python_command(
                ["-m", "pytest", f"--junitxml={tmpfp.name}"], workdir, outputs, env
            )
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
