"""Storage backend selection + upload validation."""

from __future__ import annotations

import secrets
import uuid
from functools import lru_cache

from stackup_api.core.config import get_settings
from stackup_api.storage.base import StorageBackend
from stackup_api.storage.memory import MemoryStorage

# Allowed evidence content types -> canonical file extension.
ALLOWED_MIME: dict[str, str] = {
    "application/pdf": "pdf",
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/webp": "webp",
}


@lru_cache
def get_storage() -> StorageBackend:
    settings = get_settings()
    if settings.storage_configured:
        from stackup_api.storage.r2 import R2Storage

        return R2Storage(settings)
    return MemoryStorage()


def build_storage_key(workspace_id: uuid.UUID, content_type: str) -> str:
    """A random, non-guessable key. The user filename is never used as a path."""
    ext = ALLOWED_MIME.get(content_type, "bin")
    return f"evidence/{workspace_id}/{uuid.uuid4().hex}{secrets.token_hex(4)}.{ext}"


class UploadValidationError(ValueError):
    pass


def validate_upload(*, content_type: str, size: int, max_mb: int) -> None:
    if content_type not in ALLOWED_MIME:
        raise UploadValidationError(
            f"Unsupported file type '{content_type}'. Allowed: "
            f"{', '.join(sorted(ALLOWED_MIME))}."
        )
    if size <= 0:
        raise UploadValidationError("Empty file.")
    if size > max_mb * 1024 * 1024:
        raise UploadValidationError(f"File exceeds the {max_mb} MB limit.")
