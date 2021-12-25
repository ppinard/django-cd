""""""

# Standard library modules.
import abc

# Third party modules.
from django.utils import timezone
from apscheduler.triggers.cron import CronTrigger as _CronTrigger

# Local modules.

# Globals and constants variables.


class Trigger(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def register(self, scheduler, job):
        raise NotImplementedError

    @abc.abstractproperty
    def nextrun(self):
        raise NotImplementedError


class CronTrigger(Trigger):
    def __init__(self, expr):
        self.expr = expr

    def __str__(self):
        return f"cron ({self.expr})"

    def register(self, scheduler, job):
        trigger = _CronTrigger.from_crontab(self.expr)
        scheduler.add_job(job.run, trigger, id=job.name)

    @property
    def nextrun(self):
        trigger = _CronTrigger.from_crontab(self.expr)
        return trigger.get_next_fire_time(None, timezone.now())
