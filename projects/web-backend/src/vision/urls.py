from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import GroundObjectViewset, ImageViewset

router = DefaultRouter()
router.register(r"image", ImageViewset, basename="image")
router.register(r"groundobject", GroundObjectViewset, basename="groundobject")

urlpatterns = [
    path("", include(router.urls)),
]
