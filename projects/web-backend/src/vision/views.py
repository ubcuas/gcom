import json
from pathlib import Path

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets

from .models import GroundObject, Image
from .projection import deproject_pixel_to_point
from .serializers import GroundObjectSerializer, ImageSerializer

ODLC_SESSIONS_DIR = Path(__file__).resolve().parent.parent.parent / "odlc_sessions"


@csrf_exempt
@require_http_methods(["POST"])
def deproject_pixel(request):
    try:
        data = json.loads(request.body)
        pixel = data.get("pixel")
        depth = data.get("depth")

        if not isinstance(pixel, list) or len(pixel) != 2:
            return JsonResponse(
                {"error": "Invalid input: pixel must be a list of 2 floats"}, status=400
            )

        if not isinstance(depth, (int, float)):
            return JsonResponse(
                {"error": "Invalid input: depth must be a float"}, status=400
            )

        point = deproject_pixel_to_point(
            pixel=pixel, depth=float(depth)
        )

        return JsonResponse({"point": point})
    except (ValueError, NotImplementedError) as e:
        return JsonResponse({"error": str(e)}, status=400)
    except (KeyError, TypeError) as e:
        return JsonResponse({"error": "Invalid input", "details": str(e)}, status=400)
    except Exception as e:
        return JsonResponse(
            {"error": "Internal server error", "details": str(e)}, status=500
        )


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
        print(f"Error saving ODLC session: {e}")
        return JsonResponse(
            {"error": "Internal server error", "details": str(e)}, status=500
        )


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
