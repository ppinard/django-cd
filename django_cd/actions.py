""""""

# Standard library modules.
import abc
import datetime
from pathlib import Path
import shlex
import subprocess
import time

# Third party modules.

# Local modules.
from .models import ActionRun, RunState

# Globals and constants variables.


class Action(metaclass=abc.ABCMeta):
    def __init__(self, name):
        self.name = name
        self._actionrun = None

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}({self.name})>"

    def run(self, jobrun, workdir):
        workdir = Path(workdir)
        self._actionrun = ActionRun.objects.create(
            name=self.name, jobrun=jobrun, state=RunState.RUNNING
        )
        start_time = time.time()

        try:
            state, output = self._run(workdir)

        except Exception as ex:
            state = RunState.ERROR
            output = str(ex)

        end_time = time.time()
        self._actionrun.state = state
        self._actionrun.output = output
        self._actionrun.duration = datetime.timedelta(seconds=end_time - start_time)
        self._actionrun.save(update_fields=["duration", "state", "output"])

        return state

    @abc.abstractmethod
    def _run(self, workdir):
        raise NotImplementedError

    def add_artefact(self, filepath):
        if self._actionrun is None:
            raise RuntimeError

    def add_testresult(self, name, state):
        if self._actionrun is None:
            raise RuntimeError


class CommandAction(Action):
    def __init__(self, name, args):
        super().__init__(name)
        self.args = shlex.split(args)

    def _run(self, workdir):
        process = subprocess.run(self.args, capture_output=True, cwd=workdir)

        if process.returncode == 0:
            return (RunState.SUCCESS, process.stdout.decode("utf8"))
        else:
            return (RunState.FAILED, process.stderr.decode("utf8"))
