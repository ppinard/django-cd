""""""

# Standard library modules.
import abc

# Third party modules.
from apscheduler.triggers.cron import CronTrigger as _CronTrigger

# Local modules.

# Globals and constants variables.


class Trigger(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def register(self, scheduler, job):
        raise NotImplementedError


class CronTrigger(Trigger):
    def __init__(self, expr):
        self.expr = expr

    def __str__(self):
        return f"cron ({self.expr})"

    def register(self, scheduler, job):
        trigger = _CronTrigger.from_crontab(self.expr)
        scheduler.add_job(job.run, trigger)
