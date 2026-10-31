from copy import deepcopy
from typing import Any


ANNOTATION_IMAGES: list[dict[str, Any]] = [
    {
        "id": "IMG_0428",
        "time": "14:32:08",
        "location": "North field · 42.3618, −71.0572",
        "image": "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1800&q=85",
        "status": "Needs review",
        "annotations": [],
    },
    {
        "id": "IMG_0427",
        "time": "14:31:54",
        "location": "North field · 42.3615, −71.0570",
        "image": "https://images.unsplash.com/photo-1470770841072-f978cf4d019e?auto=format&fit=crop&w=1800&q=85",
        "status": "Annotated",
        "annotations": [],
    },
    {
        "id": "IMG_0426",
        "time": "14:31:40",
        "location": "North field · 42.3611, −71.0568",
        "image": "https://images.unsplash.com/photo-1501785888041-af3ef285b470?auto=format&fit=crop&w=1800&q=85",
        "status": "Annotated",
        "annotations": [],
    },
    {
        "id": "IMG_0425",
        "time": "14:31:26",
        "location": "North field · 42.3609, −71.0565",
        "image": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?auto=format&fit=crop&w=1800&q=85",
        "status": "Annotated",
        "annotations": [],
    },
]


def get_images() -> list[dict[str, Any]]:
    return deepcopy(ANNOTATION_IMAGES)


def set_annotations(image_id: str, annotations: list[dict[str, float]]) -> bool:
    for image in ANNOTATION_IMAGES:
        if image["id"] == image_id:
            image["annotations"] = deepcopy(annotations)
            return True
    return False

