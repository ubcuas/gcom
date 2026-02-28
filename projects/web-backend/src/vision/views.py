import json
from pathlib import Path

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets

from .models import GroundObject, Image
from .serializers import GroundObjectSerializer, ImageSerializer

ODLC_SESSIONS_DIR = Path(__file__).resolve().parent.parent.parent / "odlc_sessions"


@csrf_exempt
@require_http_methods(["POST"])
def save_odlc_session(request):
    try:
        data = json.loads(request.body)
        session_id = data.get("sessionId")
        images = data.get("images")

        if not session_id or not isinstance(images, list):
            return JsonResponse({"error": "Invalid input"}, status=400)

        ODLC_SESSIONS_DIR.mkdir(exist_ok=True)
        session_file = ODLC_SESSIONS_DIR / f"{session_id}.json"
        session_file.write_text(json.dumps({"sessionId": session_id, "images": images}))

        return HttpResponse(status=200)
    except (KeyError, ValueError, TypeError) as e:
        return JsonResponse({"error": "Invalid input", "details": str(e)}, status=400)
    except Exception as e:
        return JsonResponse(
            {"error": "Internal server error", "details": str(e)}, status=500
        )


@csrf_exempt
@require_http_methods(["POST"])
def calculate_annotation_distance(request):
    """
    Stub: accept two points (normalized 0-1) and return a distance.
    Replace with real calibration/scale logic later.
    """
    try:
        data = json.loads(request.body)
        p1 = data.get("p1")
        p2 = data.get("p2")
        if not isinstance(p1, dict) or not isinstance(p2, dict):
            return JsonResponse(
                {"error": "Invalid input: p1 and p2 required"}, status=400
            )
        x1, y1 = float(p1.get("x", 0)), float(p1.get("y", 0))
        x2, y2 = float(p2.get("x", 0)), float(p2.get("y", 0))
        # Placeholder: Euclidean distance in normalized space (scale to mock units)
        distance = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5 * 100.0
        return JsonResponse({"distance": round(distance, 4)})
    except (TypeError, ValueError) as e:
        return JsonResponse({"error": "Invalid input", "details": str(e)}, status=400)


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
