from django.urls import path

from .views import list_annotation_images

urlpatterns = [
    path("images/", list_annotation_images, name="annotation-images"),
]

