""""""

# Standard library modules.

# Third party modules.
from django.urls import path

# Local modules.
from . import views

# Globals and constants variables.

app_name = "django_cd"
urlpatterns = [
    path("", views.index, name="index"),
    path("jobruns", views.jobruns, name="jobruns"),
    path("jobruns/<int:id>", views.jobrun, name="jobrun"),
]
