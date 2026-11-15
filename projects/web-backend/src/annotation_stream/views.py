import json
from typing import Any

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .state import get_images


@require_http_methods(["GET"])
def list_annotation_images(request):
    """Return the replaceable image-feed contract used by the annotation UI."""
    return JsonResponse(get_images(), safe=False)


def parse_annotations(payload: Any) -> list[dict[str, float]] | None:
    if not isinstance(payload, list):
        return None

    annotations: list[dict[str, float]] = []
    for annotation in payload:
        if not isinstance(annotation, dict):
            return None
        values = {key: annotation.get(key) for key in ("x", "y", "width", "height")}
        if not all(isinstance(value, (int, float)) for value in values.values()):
            return None
        if not all(0 <= value <= 1 for value in values.values()):
            return None
        if values["x"] + values["width"] > 1 or values["y"] + values["height"] > 1:
            return None
        annotations.append({key: float(value) for key, value in values.items()})
    return annotations


def parse_annotation_update(data: Any) -> tuple[str, list[dict[str, float]]] | None:
    if not isinstance(data, dict) or not isinstance(data.get("imageId"), str):
        return None
    annotations = parse_annotations(data.get("annotations"))
    if annotations is None:
        return None
    return data["imageId"], annotations


def annotation_update_response(image_id: str, annotations: list[dict[str, float]]):
    from .state import set_annotations

    if not set_annotations(image_id, annotations):
        return JsonResponse({"error": "Unknown image"}, status=404)
    return JsonResponse({"imageId": image_id, "annotations": annotations})

