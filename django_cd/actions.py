""""""

# Standard library modules.
import abc
import datetime
from pathlib import Path
import shlex
import subprocess
import time

# Third party modules.
import yarl

# Local modules.
from .models import ActionRun, RunState

# Globals and constants variables.


class Action(metaclass=abc.ABCMeta):
    def __init__(self, name, relpath=""):
        self.name = name
        self.relpath = relpath
        self._actionrun = None

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}({self.name})>"

    def run(self, jobrun, workdir):
        workdir = Path(workdir).joinpath(self.relpath)
        self._actionrun = ActionRun.objects.create(
            name=self.name, jobrun=jobrun, state=RunState.RUNNING
        )
        start_time = time.time()
        outputs = []

        try:
            state = self._run(workdir, outputs)

        except Exception as ex:
            state = RunState.ERROR
            outputs.append(str(ex))

        end_time = time.time()
        self._actionrun.state = state
        self._actionrun.output = "\n".join(outputs)
        self._actionrun.duration = datetime.timedelta(seconds=end_time - start_time)
        self._actionrun.save(update_fields=["duration", "state", "output"])

        return state

    @abc.abstractmethod
    def _run(self, workdir, outputs):
        raise NotImplementedError


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

    return process.returncode == 0


class CommandAction(Action):
    def __init__(self, name, args, shell=False, relpath=""):
        super().__init__(name, relpath)
        self.args = shlex.split(args)
        self.shell = shell

    def _run(self, workdir, outputs):
        success = _run_command(self.args, workdir, outputs, self.shell)
        return RunState.SUCCESS if success else RunState.FAILED


class GitCheckoutAction(Action):
    def __init__(self, name, repos_url, branch="master", relpath=""):
        super().__init__(name, relpath)
        self.repos_url = yarl.URL(repos_url)

        self.repos_name = self.repos_url.name
        self.repos_name = self.repos_name.rsplit(".")[0]

        self.branch = branch

    def _run(self, workdir, outputs):
        reposdir = workdir.joinpath(self.repos_name)

        # Clone
        if not reposdir.joinpath(".git").exists():
            args = ["git", "clone", reposdir.resolve()]
            success = _run_command(args, workdir, outputs, shell=False)
            if not success:
                return RunState.FAILED

        # Clean
        args = ["git", "clean", "-xdf"]
        success = _run_command(args, reposdir, outputs, shell=False)
        if not success:
            return RunState.FAILED

        # Checkout
        args = ["git", "checkout", self.branch]
        success = _run_command(args, reposdir, outputs, shell=False)
        if not success:
            return RunState.FAILED

        # Pull
        args = ["git", "pull"]
        success = _run_command(args, reposdir, outputs, shell=False)
        if not success:
            return RunState.FAILED

        return RunState.SUCCESS
