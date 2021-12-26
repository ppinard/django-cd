""""""

# Standard library modules.

# Third party modules.
import pytest

# Local modules.
from django_cd.jobs import Job
from django_cd.actions import Action
from django_cd.models import JobRun, ActionRun, RunState

# Globals and constants variables.


class MockAction(Action):
    def __init__(self, name, state, relpath=""):
        super().__init__(name, relpath)
        self.state = state

    def _run(self, workdir, outputs, env):
        return self.state


@pytest.mark.django_db
@pytest.mark.parametrize("state", [RunState.SUCCESS, RunState.FAILED, RunState.ERROR])
def test_job_run(tmp_path, state):
    action = MockAction(name="action", state=state)
    job = Job("test", tmp_path, actions=[action])
    job.run()

    assert JobRun.objects.count() == 1

    jobrun = JobRun.objects.first()
    assert jobrun.name == "test"
    assert jobrun.state == state

    assert ActionRun.objects.count() == 1

    actionrun = ActionRun.objects.first()
    assert actionrun.name == "action"
    assert actionrun.state == state
