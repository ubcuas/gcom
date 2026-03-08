from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    GroundObjectViewset,
    ImageViewset,
    deproject_pixel,
    save_odlc_session,
)

router = DefaultRouter()
router.register(r"image", ImageViewset, basename="image")
router.register(r"groundobject", GroundObjectViewset, basename="groundobject")

urlpatterns = [
    path("", include(router.urls)),
    path("odlc-session/save/", save_odlc_session, name="save_odlc_session"),
    path("deproject-pixel/", deproject_pixel, name="deproject_pixel"),
]
