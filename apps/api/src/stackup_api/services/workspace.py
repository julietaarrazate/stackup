"""Workspace domain operations: slug generation, creation with owner."""

from __future__ import annotations

import re
import secrets
import unicodedata
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from stackup_api.models.enums import WorkspaceRole
from stackup_api.models.workspace import Workspace, WorkspaceMember

_SLUG_STRIP = re.compile(r"[^a-z0-9]+")


def slugify(name: str) -> str:
    # Transliterate accented characters (Oído -> oido) before stripping, so
    # Spanish names produce clean slugs rather than dashes for each accent.
    normalized = unicodedata.normalize("NFKD", name)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    base = _SLUG_STRIP.sub("-", ascii_only.strip().lower()).strip("-")
    return base or "workspace"


async def _unique_slug(session: AsyncSession, name: str) -> str:
    base = slugify(name)[:120]
    candidate = base
    while True:
        exists = await session.scalar(
            select(Workspace.id).where(Workspace.slug == candidate)
        )
        if exists is None:
            return candidate
        candidate = f"{base}-{secrets.token_hex(3)}"


async def create_workspace_with_owner(
    session: AsyncSession,
    *,
    owner_id: uuid.UUID,
    name: str,
    base_currency: str,
    timezone: str,
) -> Workspace:
    """Create a workspace and make the creator its owner, atomically."""
    workspace = Workspace(
        name=name,
        slug=await _unique_slug(session, name),
        base_currency=base_currency.upper(),
        timezone=timezone,
    )
    session.add(workspace)
    await session.flush()  # assign workspace.id

    session.add(
        WorkspaceMember(
            workspace_id=workspace.id,
            user_id=owner_id,
            role=WorkspaceRole.owner,
        )
    )
    await session.flush()
    return workspace
