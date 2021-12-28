""""""

# Standard library modules.

# Third party modules.
import huey
from huey.contrib.djhuey import db_task
from django.conf import settings

# Local modules.

# Globals and constants variables.


@db_task()
def run_job(job):
    job.run()


@db_task()
def schedule_job(job, expr):
    if not hasattr(settings, "HUEY"):
        raise RuntimeError("HUEY is not defined in settings")

    schedule = huey.crontab(*expr.split(), strict=True)
    settings.HUEY.periodic_task(schedule, name=job.name)(job.run)
