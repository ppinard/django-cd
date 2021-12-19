""""""

# Standard library modules.
import datetime

# Third party modules.
from django import template
from django.template.defaultfilters import pluralize

# Local modules.
from django_cd.models import RunState


# Globals and constants variables.
register = template.Library()

backgrounds = {
    RunState.SUCCESS: "bg-success",
    RunState.ERROR: "bg-danger",
    RunState.FAILED: "bg-danger",
}

adjectives = {
    RunState.NOT_STARTED: "not started",
    RunState.RUNNING: "running",
    RunState.SUCCESS: "succeeded",
    RunState.ERROR: "failed",
    RunState.FAILED: "failed",
}


@register.filter
def state_background(state):
    return backgrounds.get(state, "bg-secondary")


@register.filter
def state_adjective(state):
    return adjectives.get(state)


@register.filter
def duration(value):
    remainder = value
    response = ""
    days = 0
    hours = 0
    minutes = 0
    seconds = 0

    if remainder.days > 0:
        days = remainder.days
        remainder -= datetime.timedelta(days=remainder.days)

    if round(remainder.seconds / 3600) > 1:
        hours = round(remainder.seconds / 3600)
        remainder -= datetime.timedelta(hours=hours)

    if round(remainder.seconds / 60) > 1:
        minutes = round(remainder.seconds / 60)
        remainder -= datetime.timedelta(minutes=minutes)

    seconds = remainder.seconds + remainder.microseconds / 1e6

    response = []
    if days:
        response.append(
            "{days} day{plural_suffix}".format(
                days=days,
                plural_suffix=pluralize(days),
            )
        )
    if hours:
        response.append(
            "{hours} hour{plural_suffix}".format(
                hours=hours,
                plural_suffix=pluralize(hours),
            )
        )
    if minutes:
        response.append(
            "{minutes} minute{plural_suffix}".format(
                minutes=minutes,
                plural_suffix=pluralize(minutes),
            )
        )
    if seconds:
        response.append(
            "{seconds:.3f} second{plural_suffix}".format(
                seconds=seconds,
                plural_suffix=pluralize(seconds),
            )
        )

    return ", ".join(response)
