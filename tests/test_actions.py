""""""

# Standard library modules.

# Third party modules.
import pytest

# Local modules.
from django_cd.jobs import Job
from django_cd.actions import (
    CommandAction,
    GitCheckoutAction,
    PythonAction,
    PythonPytestAction,
    PythonVirtualEnvAction,
)
from django_cd.models import JobRun, ActionRun, RunState

# Globals and constants variables.


@pytest.mark.django_db
def test_action(tmp_path):
    actions = [
        CommandAction("command", 'echo "hello"'),
        GitCheckoutAction(
            "gitcheckout", "https://github.com/codecov/example-python.git"
        ),
        PythonVirtualEnvAction("venv", relpath="env"),
        PythonAction("python", "--version"),
        PythonPytestAction("pytest", args="tests.py", relpath="example-python"),
    ]

    job = Job("test", tmp_path, actions=actions)
    job.run()

    assert JobRun.objects.count() == 1

    jobrun = JobRun.objects.first()
    assert jobrun.name == "test"
    assert jobrun.state == RunState.SUCCESS

    assert ActionRun.objects.count() == 5
