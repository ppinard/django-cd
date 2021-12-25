""""""

# Standard library modules.
import sys

# Third party modules.
from django.apps import AppConfig
from django.conf import settings
from apscheduler.schedulers.background import BackgroundScheduler

# Local modules.
from loguru import logger

# Globals and constants variables.


class DjangoCdConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_cd"

    def ready(self):
        if "runserver" not in sys.argv:
            return

        from .jobs import Job

        self.scheduler = BackgroundScheduler()
        self.scheduler.start()

        self.jobs = {}
        for filepath in settings.JOBFILES:
            job = Job.from_yaml(filepath)
            if job.name in self.jobs:
                logger.error(r"Job {job.name} already added")
                continue

            job.register(self.scheduler)
            self.jobs[job.name] = job
