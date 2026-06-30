from django.urls import path

from . import views

app_name = "portal"

urlpatterns = [
    path("", views.apply, name="apply"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("api/facilities/", views.facilities_json, name="facilities-json"),
]
