""""""

# Standard library modules.
from pathlib import Path
import time
import datetime

# Third party modules.
import yaml
from django.conf import settings
from django.utils.module_loading import import_string
from loguru import logger

# Local modules.
from .models import JobRun, RunState

# Globals and constants variables.


class Job:
    def __init__(self, name, workdir, triggers=None, actions=None, notifications=None):
        self.name = name
        self.workdir = workdir

        if triggers is None:
            triggers = []
        self.triggers = tuple(triggers)

        if actions is None:
            triggers = []
        self.actions = tuple(actions)

        if notifications is None:
            notifications = []
        self.notifications = tuple(notifications)

    @classmethod
    def from_yaml(cls, filepath):
        with open(filepath, "r") as fp:
            d = yaml.load(fp.read(), Loader=yaml.Loader)

        jobname = d["name"]
        workdir = Path(d.get("workdir", settings.WORKDIR))

        triggers = []
        for trigger_kwargs in d.get("triggers", []):
            uses = trigger_kwargs.pop("uses")

            import_name = settings.TRIGGERS[uses]
            trigger_class = import_string(import_name)
            trigger = trigger_class(**trigger_kwargs)
            triggers.append(trigger)

        actions = []
        for action_kwargs in d.get("actions", []):
            name = action_kwargs.pop("name")
            uses = action_kwargs.pop("uses")

            import_name = settings.ACTIONS[uses]
            action_class = import_string(import_name)
            action = action_class(name=name, **action_kwargs)
            actions.append(action)

        notifications = []
        for notification_kwargs in d.get("notifications", []):
            uses = notification_kwargs.pop("uses")

            import_name = settings.NOTIFICATIONS[uses]
            notification_class = import_string(import_name)
            notification = notification_class(**notification_kwargs)
            notifications.append(notification)

        return cls(jobname, workdir, triggers, actions, notifications)

    def register(self, scheduler):
        for trigger in self.triggers:
            trigger.register(scheduler, self)
            logger.info(f"Registered trigger: {trigger}")

    def run(self, notify=True):
        logger.info(f"Job: {self.name} ({self.workdir})")

        # Create JobRun
        jobrun = JobRun.objects.create(name=self.name, state=RunState.RUNNING)

        # Run actions
        start_time = time.time()
        nactions = len(self.actions)
        states = set()
        env = {}

        for i, action in enumerate(self.actions):
            logger.info(f"Action ({i+1}/{nactions}): {action}")

            state = action.run(jobrun, self.workdir, env)
            states.add(state)

            logger.info(f"Action ({i+1}/{nactions}): {action} ({state})")

            if state != RunState.SUCCESS:
                break

        end_time = time.time()

        # Determine job state
        if not states:
            jobrun.state = RunState.NOT_STARTED
        elif RunState.ERROR in states:
            jobrun.state = RunState.ERROR
        elif RunState.FAILED in states:
            jobrun.state = RunState.FAILED
        elif RunState.RUNNING in states:
            jobrun.state = RunState.RUNNING
        else:
            jobrun.state = RunState.SUCCESS

        # Save JobRun
        jobrun.duration = datetime.timedelta(seconds=end_time - start_time)
        jobrun.save(update_fields=["duration", "state"])

        # Notifications
        if notify:
            for notification in self.notifications:
                notification.notify(jobrun)
                logger.info(f"  Notification: {notification}")

    @property
    def nextrun(self):
        if not self.triggers:
            return None

        return min(trigger.nextrun for trigger in self.triggers)
