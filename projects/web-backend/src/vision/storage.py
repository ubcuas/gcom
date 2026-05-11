import base64
from datetime import datetime, timezone

import boto3
from django.conf import settings

_client = None


def _s3():
    global _client
    if _client is None:
        _client = boto3.client("s3", region_name=settings.AWS_S3_REGION)
    return _client


def _date_prefix(received_at_ms: int | None) -> str:
    if received_at_ms:
        dt = datetime.fromtimestamp(received_at_ms / 1000, tz=timezone.utc)
    else:
        dt = datetime.now(timezone.utc)
    return dt.strftime("%Y/%m/%d")


def _put(
    session_id: str,
    record_id: str,
    b64: str,
    received_at_ms: int | None,
    suffix: str,
    content_type: str,
) -> str:
    key = f"odlc/{_date_prefix(received_at_ms)}/{session_id}/{record_id}{suffix}"
    _s3().put_object(
        Bucket=settings.AWS_S3_BUCKET,
        Key=key,
        Body=base64.b64decode(b64),
        ContentType=content_type,
    )
    return f"https://{settings.AWS_S3_BUCKET}.s3.{settings.AWS_S3_REGION}.amazonaws.com/{key}"


def upload_odlc_image(
    session_id: str, record_id: str, image_b64: str, received_at_ms: int | None
) -> str:
    """Upload a base64 JPEG to odlc/YYYY/MM/DD/<session>/<record>.jpg."""
    return _put(session_id, record_id, image_b64, received_at_ms, ".jpg", "image/jpeg")


def upload_odlc_depth(
    session_id: str, record_id: str, depth_b64: str, received_at_ms: int | None
) -> str:
    """Upload a base64 16UC1 PNG depthmap to odlc/YYYY/MM/DD/<session>/<record>_depth.png."""
    return _put(session_id, record_id, depth_b64, received_at_ms, "_depth.png", "image/png")
