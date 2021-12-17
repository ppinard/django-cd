""""""

# Standard library modules.
import datetime

# Third party modules.
from django.shortcuts import render
import plotly.express as px
import pandas as pd

# Local modules.
from .models import JobRun, RunState
from .plotlyutil import render_plotly

# Globals and constants variables.
colors = {RunState.SUCCESS: "green", RunState.ERROR: "red", RunState.FAILED: "yellow"}


def index(request):
    return render(request, "django_cd/index.html")


def jobrun(request, id):
    jobrun = JobRun.objects.get(pk=id)
    return render(request, "django_cd/jobrun.html", context={"jobrun": jobrun})


def jobruns(request):
    entries = JobRun.objects.order_by("-started_on")[:100]
    fields = ["id", "name", "started_on", "duration", "state"]
    df = pd.DataFrame(entries.values_list(*fields, named=True))
    df["ended_on"] = df["started_on"].shift(1)

    xend = df["ended_on"][0]

    fig = px.timeline(
        df,
        x_start="started_on",
        x_end="ended_on",
        y="name",
        hover_data={
            "name": False,
            "started_on": True,
            "duration": False,
            "ended_on": True,
            "state": False,
        },
        color="state",
        color_discrete_map=colors,
        custom_data=["id"],
    )
    fig.update_xaxes(
        autorange=True,
        rangeselector={
            "buttons": [
                {"step": "all"},
                {"count": 1, "label": "1h", "step": "hour", "stepmode": "backward"},
                {"count": 1, "label": "1d", "step": "day", "stepmode": "backward"},
            ]
        },
        rangeslider={"range": [xend - datetime.timedelta(days=1), xend]},
    )
    fig.update_yaxes(title={"text": "", "font": {"size": 18}})
    fig.update_traces(selected={"marker": {"color": "red"}})

    return render_plotly(request, fig.data, fig.layout)
