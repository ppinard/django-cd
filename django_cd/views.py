""""""

# Standard library modules.

# Third party modules.
from django.shortcuts import render
from django.apps import apps
from django.http import HttpResponse, HttpResponseBadRequest

# Local modules.
from .models import JobRun, RunState
from .tasks import run_job

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


def _always_n(iterable, n):
    it = iter(iterable)
    for _ in range(n):
        try:
            yield next(it)
        except StopIteration:
            yield None


def jobruns(request):
    njobs = request.GET.get("njobs", 10)
    app = apps.get_app_config("django_cd")

    jobnames = dict(
        (n, n)
        for n in JobRun.objects.order_by("-started_on")
        .values_list("name", flat=True)
        .all()
    ).keys()

    rows = []
    for name in jobnames:
        runs = _always_n(
            JobRun.objects.filter(name=name)
            .order_by("-started_on")
            .values_list("id", "started_on", "state", named=True)[:njobs],
            njobs,
        )

        job = app.jobs.get(name)
        nextrun = job.nextrun if job is not None else None

        rows.append([name, runs, nextrun])

    return render(
        request,
        "django_cd/jobruns.html",
        context={
            "njobs": njobs,
            "available_jobs": app.jobs.keys(),
            "rows": rows,
            "colwidth": int(85 / (njobs + 1)),
        },
    )


def runjob(request):
    app = apps.get_app_config("django_cd")
    name = request.POST.get("jobname")
    job = app.jobs.get(name)

    if job is None:
        return HttpResponseBadRequest()

    run_job.schedule((job,), delay=0)
    return HttpResponse(status=204, headers={"HX-Refresh": "true"})
