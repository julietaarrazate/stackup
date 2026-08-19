"""AuditEvent — records privileged mutations (ADR-004)."""

from __future__ import annotations

import datetime
import uuid
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from stackup_api.core.db import Base
from stackup_api.models.base import uuid_pk

# JSONB on PostgreSQL, plain JSON elsewhere (SQLite in tests).
JSONType = JSON().with_variant(JSONB(), "postgresql")


class AuditEvent(Base):
    __tablename__ = "audit_event"

    id: Mapped[uuid.UUID] = uuid_pk()
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("workspace.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    entity: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    before: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    after: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    event_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSONType, nullable=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
