""""""

# Standard library modules.
import datetime

# Third party modules.
from django.shortcuts import render
from django.utils import timezone
import plotly.express as px
import pandas as pd
import numpy as np

# Local modules.
from .models import JobRun, RunState
from .utils import render_plotly

# Globals and constants variables.
colors = {
    RunState.SUCCESS: "#198754",
    RunState.ERROR: "#6f42c1",
    RunState.FAILED: "#dc3545",
    RunState.SKIPPED: "#ffc107",
    RunState.RUNNING: "gray-600",
}


def index(request):
    return render(request, "django_cd/index.html")


def jobrun(request, id):
    jobrun = JobRun.objects.get(pk=id)
    return render(request, "django_cd/jobrun.html", context={"jobrun": jobrun})


def jobruns(request):
    entries = JobRun.objects.order_by("-started_on")[:100]
    fields = ["id", "name", "started_on", "duration", "state"]

    df = pd.DataFrame(entries.values_list(*fields, named=True))
    df["ended_on"] = df["started_on"] + df["duration"]

    # Create a fake ended_on to make sure the job is visible
    df["fake_ended_on"] = df["started_on"].shift(1)
    df["fake_ended_on"][0] = df["ended_on"][0]
    df["fake_ended_on"] = df.apply(
        lambda x: min(
            x["fake_ended_on"],
            max(x["ended_on"], x["started_on"] + datetime.timedelta(minutes=10)),
        ),
        axis="columns",
    )

    print(df)

    xstart = df["started_on"].min()
    now = timezone.now()

    fig = px.timeline(
        df,
        x_start="started_on",
        x_end="fake_ended_on",
        y="name",
        hover_data={
            "id": True,
            "name": False,
            "started_on": "|%Y-%m-%d %H:%M:%S",
            "duration": False,
            "ended_on": "|%Y-%m-%d %H:%M:%S",
            "state": False,
            "fake_ended_on": False,
        },
        color="state",
        color_discrete_map=colors,
        custom_data=["id"],
    )
    fig.update_xaxes(
        autorange=False,
        range=[now - datetime.timedelta(days=1), now],
        rangeselector={
            "buttons": [
                {
                    "count": 10,
                    "label": "10min",
                    "step": "minute",
                    "stepmode": "backward",
                },
                {"count": 1, "label": "1h", "step": "hour", "stepmode": "backward"},
                {"count": 1, "label": "1d", "step": "day", "stepmode": "backward"},
                {"count": 1, "label": "1m", "step": "month", "stepmode": "backward"},
                {"step": "all"},
            ]
        },
        rangeslider={"range": [xstart, now]},
    )
    fig.update_yaxes(title={"text": "", "font": {"size": 18}})
    fig.update_traces(
        hovertemplate="<b>Job #%{customdata[0]}</b><br>Started on: %{base|%Y-%m-%d %H:%M:%S}<br>Ended on: %{customdata[2]|%Y-%m-%d %H:%M:%S}<extra></extra>"
    )

    return render_plotly(
        request, fig.data, fig.layout, template="django_cd/jobruns_graph.html"
    )
