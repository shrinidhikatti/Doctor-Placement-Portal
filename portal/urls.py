from django.urls import path

from . import views

app_name = "portal"

urlpatterns = [
    path("", views.apply, name="apply"),
    path("api/facilities/", views.facilities_json, name="facilities-json"),
]
