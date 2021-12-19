""""""

# Standard library modules.
import abc

# Third party modules.
from django.core.mail import send_mail
from django.template import Engine, Context

# Local modules.

# Globals and constants variables.


class Notification(metaclass=abc.ABCMeta):
    @classmethod
    def notify(self, jobrun):
        raise NotImplementedError


class EmailNotification(Notification):
    def __init__(self, recipients):
        self.recipients = tuple(recipients)

    def __str__(self):
        return "email"

    def notify(self, jobrun):
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
