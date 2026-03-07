from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    GroundObjectViewset,
    ImageViewset,
    calculate_annotation_distance,
    project_point,
    save_odlc_session,
)

router = DefaultRouter()
router.register(r"image", ImageViewset, basename="image")
router.register(r"groundobject", GroundObjectViewset, basename="groundobject")

urlpatterns = [
    path("", include(router.urls)),
    path("odlc-session/save/", save_odlc_session, name="save_odlc_session"),
    path(
        "odlc-annotation-distance/",
        calculate_annotation_distance,
        name="calculate_annotation_distance",
    ),
    path("project-point/", project_point, name="project_point"),
]
