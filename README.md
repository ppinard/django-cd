# django-cd

![GitHub Workflow Status](https://img.shields.io/github/workflow/status/ppinard/django-cd/CI)
![PyPI](https://img.shields.io/pypi/v/django-cd)

Continuous deployment


## Installation

```
git clone git@github.com/ppinard/django-cd.git
cd django-cd
pip install -e .
```

## Django - settings.py

Add to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    "django_bootstrap5",
    "django_cd",
]
```

Add to settings.py:

```python
ACTIONS = {
    "command": "django_cd.actions.CommandAction",
    "git-checkout": "django_cd.actions.GitCheckoutAction",
    "python-run": "django_cd.actions.PythonAction",
    "python-pytest": "django_cd.actions.PythonPytestAction",
    "python-venv": "django_cd.actions.PythonVirtualEnvAction",
}
TRIGGERS = {
    "cron": "django_cd.triggers.CronTrigger",
}
NOTIFICATIONS = {
    "email": "django_cd.notifications.EmailNotification",
}

JOBFILES = []
WORKDIR = ""
```


## License

The library is provided under the MIT license license.

Copyright (c) 2021, Philippe Pinard





