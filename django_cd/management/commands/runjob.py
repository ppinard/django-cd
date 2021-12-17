""""""

# Standard library modules.
from pathlib import Path

# Third party modules.
from django.core.management.base import BaseCommand
from django.conf import settings

# Local modules.
from django_cd.jobs import Job

# Globals and constants variables.


class Command(BaseCommand):
    help = "Run job(s)"

    def add_arguments(self, parser):
        parser.add_argument("filepath", type=Path, nargs="+", help="Path job file")

    def handle(self, *args, **options):
        filepaths = options["filepath"]

        for filepath in filepaths:
            job = Job.from_yaml(filepath)
            job.run()
