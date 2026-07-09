"""Validation helpers for uploaded image and video files."""

import uuid

from app.core.config import settings
from app.utils.exceptions import BadRequestException

_EXTENSION_BY_CONTENT_TYPE = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
    "video/mp4": "mp4",
    "video/webm": "webm",
    "video/quicktime": "mov",
}


def validate_image_upload(content_type: str | None, size_bytes: int) -> None:
    """Raise `BadRequestException` if the upload fails type/size constraints."""
    if content_type not in settings.ALLOWED_IMAGE_CONTENT_TYPES:
        allowed = ", ".join(settings.ALLOWED_IMAGE_CONTENT_TYPES)
        raise BadRequestException(f"Unsupported image type '{content_type}'. Allowed types: {allowed}")

    if size_bytes <= 0:
        raise BadRequestException("Uploaded file is empty")

    if size_bytes > settings.MAX_UPLOAD_SIZE_BYTES:
        raise BadRequestException(f"Image exceeds the maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB")


def validate_video_upload(content_type: str | None, size_bytes: int) -> None:
    """Raise `BadRequestException` if the video upload fails type/size constraints."""
    if content_type not in settings.ALLOWED_VIDEO_CONTENT_TYPES:
        allowed = ", ".join(settings.ALLOWED_VIDEO_CONTENT_TYPES)
        raise BadRequestException(f"Unsupported video type '{content_type}'. Allowed types: {allowed}")

    if size_bytes <= 0:
        raise BadRequestException("Uploaded file is empty")

    if size_bytes > settings.MAX_VIDEO_UPLOAD_SIZE_BYTES:
        raise BadRequestException(f"Video exceeds the maximum allowed size of {settings.MAX_VIDEO_UPLOAD_SIZE_MB}MB")


def generate_unique_filename(content_type: str) -> str:
    """Generate a collision-free filename for a given image/video content type."""
    extension = _EXTENSION_BY_CONTENT_TYPE.get(content_type, "bin")
    return f"{uuid.uuid4().hex}.{extension}"
