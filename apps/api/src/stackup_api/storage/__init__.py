"""Object storage for evidence files (ADR-006).

A small backend abstraction so the app can run without external infra in
dev/test (in-process backend) while using Cloudflare R2 in real
environments. Evidence is never stored on Render's ephemeral filesystem and
never served publicly — downloads always go through an authorized API
endpoint.
"""

from __future__ import annotations

from stackup_api.storage.base import StorageBackend
from stackup_api.storage.factory import get_storage

__all__ = ["StorageBackend", "get_storage"]
