from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    GroundObjectViewset,
    ImageViewset,
    capture_image,
    deproject_pixel,
    get_odlc_session,
    patch_odlc_record,
    post_odlc_record,
)

router = DefaultRouter()
router.register(r"image", ImageViewset, basename="image")
router.register(r"groundobject", GroundObjectViewset, basename="groundobject")

urlpatterns = [
    path("", include(router.urls)),
    path("odlc-session/<str:session_id>/", get_odlc_session, name="get_odlc_session"),
    path(
        "odlc-session/<str:session_id>/records/",
        post_odlc_record,
        name="post_odlc_record",
    ),
    path(
        "odlc-session/<str:session_id>/records/<str:record_id>/",
        patch_odlc_record,
        name="patch_odlc_record",
    ),
    path("deproject-pixel/", deproject_pixel, name="deproject_pixel"),
    path("capture/", capture_image, name="capture_image"),
]
