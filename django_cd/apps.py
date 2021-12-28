""""""

# Standard library modules.
import sys

# Third party modules.
from django.apps import AppConfig
from django.conf import settings

# Local modules.
from loguru import logger

# Globals and constants variables.


class DjangoCdConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_cd"

    def ready(self):
        if "manage.py" in sys.argv and "runserver" not in sys.argv:
            return

        from .jobs import Job

        self.jobs = {}
        for filepath in settings.JOBFILES:
            job = Job.from_yaml(filepath)
            if job.name in self.jobs:
                logger.error(f"Job {job.name} already added")
                continue

            job.register()
            self.jobs[job.name] = job
