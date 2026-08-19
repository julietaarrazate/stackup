"""In-process storage backend for dev/test only.

Not durable and not for production (ADR-006 forbids ephemeral storage for
real evidence); the config guard rejects it in production.
"""

from __future__ import annotations


class MemoryStorage:
    def __init__(self) -> None:
        self._objects: dict[str, tuple[bytes, str]] = {}

    async def put(self, key: str, data: bytes, content_type: str) -> None:
        self._objects[key] = (data, content_type)

    async def get(self, key: str) -> bytes:
        if key not in self._objects:
            raise FileNotFoundError(key)
        return self._objects[key][0]

    async def delete(self, key: str) -> None:
        self._objects.pop(key, None)
