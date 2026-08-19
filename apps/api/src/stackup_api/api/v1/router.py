"""Aggregate router for /api/v1.

Resource routers (workspaces, applications, costs, ...) are mounted here as
they are built in later phases.
"""

from __future__ import annotations

from fastapi import APIRouter

api_router = APIRouter(prefix="/api/v1")


@api_router.get("/meta", tags=["meta"])
async def meta() -> dict[str, str]:
    """Minimal, unauthenticated API metadata for smoke-testing the mount."""
    return {"api": "stackup", "version": "v1"}
