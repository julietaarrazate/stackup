"""Audit logging helper (ADR-004).

Records privileged mutations. Never stores secrets or full file contents —
callers pass only the minimal before/after snapshots needed for an audit
trail.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from stackup_api.core.context import get_request_id
from stackup_api.models.audit import AuditEvent


async def record_audit(
    session: AsyncSession,
    *,
    actor_user_id: uuid.UUID | None,
    workspace_id: uuid.UUID | None,
    entity: str,
    action: str,
    entity_id: str | None = None,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditEvent:
    event = AuditEvent(
        actor_user_id=actor_user_id,
        workspace_id=workspace_id,
        entity=entity,
        entity_id=entity_id,
        action=action,
        before=before,
        after=after,
        request_id=get_request_id(),
        event_metadata=metadata,
    )
    session.add(event)
    return event
