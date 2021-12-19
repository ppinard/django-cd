""""""

# Standard library modules.

# Third party modules.
from django.db import models

# Local modules.

# Globals and constants variables.


class RunState(models.TextChoices):
    NOT_STARTED = "not started"
    RUNNING = "running"
    ERROR = "error"
    FAILED = "failed"
    SUCCESS = "success"
    SKIPPED = "skipped"


class JobRun(models.Model):
    name = models.CharField(max_length=255)
    started_on = models.DateTimeField(auto_now_add=True)
    duration = models.DurationField(null=True)
    state = models.CharField(
        max_length=12, choices=RunState.choices, default=RunState.NOT_STARTED
    )


class ActionRun(models.Model):
    name = models.CharField(max_length=255)
    jobrun = models.ForeignKey(
        JobRun, on_delete=models.CASCADE, related_name="actionruns"
    )
    started_on = models.DateTimeField(auto_now_add=True)
    duration = models.DurationField(null=True)
    state = models.CharField(
        max_length=12, choices=RunState.choices, default=RunState.NOT_STARTED
    )
    output = models.TextField(null=True)


class TestResult(models.Model):
    name = models.CharField(max_length=255)
    actionrun = models.ForeignKey(
        ActionRun, on_delete=models.CASCADE, related_name="testresults"
    )
    state = models.CharField(
        max_length=12, choices=RunState.choices, default=RunState.NOT_STARTED
    )
    duration = models.DurationField()
