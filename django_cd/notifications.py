""""""

# Standard library modules.
import abc

# Third party modules.
from django.core.mail import send_mail
from django.template import Engine, Context

# Local modules.
from .models import RunState

# Globals and constants variables.


class Notification(metaclass=abc.ABCMeta):
    @classmethod
    def notify(self, jobrun):
        raise NotImplementedError


class EmailNotification(Notification):
    def __init__(self, recipients, on_success=False, on_failure=True):
        self.recipients = tuple(recipients)
        self.on_success = on_success
        self.on_failure = on_failure

    def __str__(self):
        return "email"

    def notify(self, jobrun):
        if (jobrun.state in [RunState.ERROR, RunState.FAILED] and self.on_failure) or (
            jobrun.state == RunState.SUCCESS and self.on_success
        ):
            engine = Engine.get_default()
            template = engine.get_template("django_cd/jobrun_report.html")
            context = Context({"jobrun": jobrun})

            html_message = template.render(context)
            send_mail(
                subject=f"Job report - {jobrun.name} - {jobrun.state}",
                message="",
                from_email=None,
                recipient_list=self.recipients,
                html_message=html_message,
            )
