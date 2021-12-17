""""""

# Standard library modules.
import json
import uuid

# Third party modules.
from django.shortcuts import render
import plotly

# Local modules.

# Globals and constants variables.


def render_plotly(request, data, layout):
    id = str(uuid.uuid4())
    graph = {"data": data, "layout": layout}
    return render(
        request,
        "plotly.html",
        context={
            "id": id,
            "graph": json.dumps(graph, cls=plotly.utils.PlotlyJSONEncoder),
        },
    )
