""""""

# Standard library modules.
import abc

# Third party modules.
from django.utils import timezone
import huey
import crontab

# Local modules.
from .tasks import schedule_job

# Globals and constants variables.


class Trigger(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def register(self, job):
        raise NotImplementedError

    @abc.abstractproperty
    def nextrun(self):
        raise NotImplementedError


class CronTrigger(Trigger):
    def __init__(self, expr):
        self.expr = expr

    def __str__(self):
        return f"cron ({self.expr})"

    def register(self, job):
        schedule_job(job, self.expr)

    @property
    def nextrun(self):
        cron = crontab.CronTab(self.expr)
        return cron.next(timezone.now(), return_datetime=True)
