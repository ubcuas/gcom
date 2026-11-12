from django.urls import path

from . import views

urlpatterns = [
    path("no-fly-zones", views.get_no_fly_zones, name="get_no_fly_zones"),
    path(
        "area_of_interest",
        views.process_area_of_interest,
        name="process_area_of_interest",
    ),
]
