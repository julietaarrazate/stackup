"""Lightweight rate limiting for sensitive endpoints (auth).

This ships with an in-memory fixed-window backend so limits work in dev/test
and single-instance deployments today. It is deliberately small and behind a
single dependency type so a Redis (Upstash) backend can replace the store in
Phase 5+ without touching call sites (ADR-005). The in-memory store is
per-process, so it is NOT sufficient across multiple API instances — that is
exactly why the Redis backend is planned before horizontal scaling.
"""

from __future__ import annotations

import time
from collections import defaultdict

from fastapi import HTTPException, Request, status


class _FixedWindowStore:
    def __init__(self) -> None:
        self._hits: dict[str, list[float]] = defaultdict(list)

    def hit(self, key: str, *, limit: int, window_seconds: int) -> bool:
        now = time.monotonic()
        cutoff = now - window_seconds
        bucket = [t for t in self._hits[key] if t > cutoff]
        bucket.append(now)
        self._hits[key] = bucket
        return len(bucket) > limit


_store = _FixedWindowStore()


class RateLimiter:
    """FastAPI dependency enforcing `limit` requests per `window_seconds`.

    Keyed by client IP + endpoint path, which is adequate for abuse
    protection on auth endpoints without a user identity yet.
    """

    def __init__(self, *, limit: int, window_seconds: int) -> None:
        self.limit = limit
        self.window_seconds = window_seconds

    async def __call__(self, request: Request) -> None:
        client = request.client.host if request.client else "unknown"
        key = f"{client}:{request.url.path}"
        if _store.hit(key, limit=self.limit, window_seconds=self.window_seconds):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later.",
            )


def reset_rate_limits() -> None:
    """Test helper: clear all recorded hits."""
    _store._hits.clear()
