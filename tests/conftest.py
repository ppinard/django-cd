""""""

# Standard library modules.
from pathlib import Path
import tempfile
import shutil

# Third party modules.
from django.conf import settings

# Local modules.

# Globals and constants variables.
tmpdir = Path(tempfile.mkdtemp())


def pytest_configure():
    extra_settings = {
        "SECRET_KEY": "django-insecure-qhnch=9_ym@a^9lo%wxpzjtfavqbq8p60&b8!bjr(utxyz$3_j",
        "INSTALLED_APPS": [
            "django.contrib.admin",
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sessions",
            "django.contrib.messages",
            "django.contrib.staticfiles",
            "django_bootstrap5",
            "django_cd",
        ],
        "DATABASES": {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": tmpdir.joinpath("db.sqlite3"),
            }
        },
        "ACTIONS": {
            "command": "django_cd.actions.CommandAction",
            "git-checkout": "django_cd.actions.GitCheckoutAction",
            "python-run": "django_cd.actions.PythonAction",
            "python-pytest": "django_cd.actions.PythonPytestAction",
            "python-venv": "django_cd.actions.PythonVirtualEnvAction",
        },
        "TRIGGERS": {
            "cron": "django_cd.triggers.CronTrigger",
        },
        "NOTIFICATIONS": {
            "email": "django_cd.notifications.EmailNotification",
        },
    }

    settings.configure(DEBUG=True, **extra_settings)


def pytest_unconfigure():
    shutil.rmtree(tmpdir)
