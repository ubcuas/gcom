import json
import threading
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
_SESSION_LOCK = threading.Lock()
_PATCHABLE_FIELDS = {"flagged", "textInput", "metadata", "annotations"}


def _session_path(session_id: str) -> Path:
    return ODLC_SESSIONS_DIR / f"{session_id}.json"


def _read_session(session_id: str) -> dict | None:
    path = _session_path(session_id)
    if not path.exists():
        return None
    return json.loads(path.read_text())


def _write_session(session_id: str, data: dict) -> None:
    ODLC_SESSIONS_DIR.mkdir(exist_ok=True)
    _session_path(session_id).write_text(json.dumps(data))


def _empty_session(session_id: str) -> dict:
    return {"sessionId": session_id, "records": []}


def _stub_record(record_id: str, updates: dict) -> dict:
    return {
        "id": record_id,
        "receivedAt": 0,
        "image": None,
        "flagged": False,
        "textInput": "",
        "metadata": "",
        "annotations": [],
        **{k: v for k, v in updates.items() if k in _PATCHABLE_FIELDS},
    }


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

        point = deproject_pixel_to_point(pixel=pixel, depth=float(depth))

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
@require_http_methods(["GET"])
def get_odlc_session(request, session_id: str):
    try:
        with _SESSION_LOCK:
            data = _read_session(session_id)
        if data is None:
            return JsonResponse({"error": "Session not found"}, status=404)
        return JsonResponse(data)
    except Exception as e:
        print(f"Error reading ODLC session: {e}")
        return JsonResponse(
            {"error": "Internal server error", "details": str(e)}, status=500
        )


@csrf_exempt
@require_http_methods(["POST"])
def post_odlc_record(request, session_id: str):
    try:
        record = json.loads(request.body)
        if not isinstance(record, dict) or not record.get("id"):
            return JsonResponse({"error": "Invalid record"}, status=400)

        with _SESSION_LOCK:
            data = _read_session(session_id) or _empty_session(session_id)
            records = data.get("records", [])
            existing_idx = next(
                (i for i, r in enumerate(records) if r.get("id") == record["id"]),
                None,
            )
            if existing_idx is not None:
                # Preserve any patched fields that may have landed before POST
                merged = {**record}
                for field in _PATCHABLE_FIELDS:
                    if field in records[existing_idx] and records[existing_idx][
                        field
                    ] not in (None, "", [], False):
                        merged[field] = records[existing_idx][field]
                records[existing_idx] = merged
            else:
                records.append(record)
            data["records"] = records
            _write_session(session_id, data)

        return HttpResponse(status=200)
    except (KeyError, ValueError, TypeError) as e:
        return JsonResponse({"error": "Invalid input", "details": str(e)}, status=400)
    except Exception as e:
        print(f"Error posting ODLC record: {e}")
        return JsonResponse(
            {"error": "Internal server error", "details": str(e)}, status=500
        )


@csrf_exempt
@require_http_methods(["PATCH"])
def patch_odlc_record(request, session_id: str, record_id: str):
    try:
        updates = json.loads(request.body)
        if not isinstance(updates, dict):
            return JsonResponse({"error": "Invalid updates"}, status=400)
        filtered = {k: v for k, v in updates.items() if k in _PATCHABLE_FIELDS}

        with _SESSION_LOCK:
            data = _read_session(session_id) or _empty_session(session_id)
            records = data.get("records", [])
            existing_idx = next(
                (i for i, r in enumerate(records) if r.get("id") == record_id),
                None,
            )
            if existing_idx is not None:
                records[existing_idx] = {**records[existing_idx], **filtered}
            else:
                records.append(_stub_record(record_id, filtered))
            data["records"] = records
            _write_session(session_id, data)

        return HttpResponse(status=200)
    except (KeyError, ValueError, TypeError) as e:
        return JsonResponse({"error": "Invalid input", "details": str(e)}, status=400)
    except Exception as e:
        print(f"Error patching ODLC record: {e}")
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
