from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets

from .models import GroundObject, Image
from .serializers import GroundObjectSerializer, ImageSerializer


# Create your views here.
@extend_schema_view(
    list=extend_schema(description="List all images"),
    create=extend_schema(description="Upload a new image"),
    retrieve=extend_schema(description="Get details of a specific image"),
    update=extend_schema(description="Update a specific image"),
    partial_update=extend_schema(description="Partially update a specific image"),
    destroy=extend_schema(description="Delete a specific image"),
)
class ImageViewset(viewsets.ModelViewSet):
    """
    Viewset for CRUD operations on Image.
    Handles images captured by the drone, including both visible and thermal types.
    """

    queryset = Image.objects.all()
    serializer_class = ImageSerializer


@extend_schema_view(
    list=extend_schema(description="List all ground objects"),
    create=extend_schema(description="Create a new ground object"),
    retrieve=extend_schema(description="Get details of a specific ground object"),
    update=extend_schema(description="Update a specific ground object"),
    partial_update=extend_schema(
        description="Partially update a specific ground object"
    ),
    destroy=extend_schema(description="Delete a specific ground object"),
)
class GroundObjectViewset(viewsets.ModelViewSet):
    """
    Viewset for CRUD operations on GroundObjects.
    Ground objects are identified targets with properties like type, shape, color, and location.
    """

    queryset = GroundObject.objects.all()
    serializer_class = GroundObjectSerializer
