""""""

# Standard library modules.

# Third party modules.
from django.shortcuts import render

# Local modules.
from .models import JobRun, RunState

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


def always_n(iterable, n):
    it = iter(iterable)
    for _ in range(n):
        try:
            yield next(it)
        except StopIteration:
            yield None


def jobruns(request):
    names = sorted(JobRun.objects.values_list("name", flat=True).distinct().all())

    ordered_jobruns = {}
    for name in names:
        ordered_jobruns[name] = always_n(
            JobRun.objects.filter(name=name)
            .order_by("-started_on")
            .values_list("id", "started_on", "state", named=True),
            10,
        )

    return render(
        request, "django_cd/jobruns.html", context={"ordered_jobruns": ordered_jobruns}
    )
