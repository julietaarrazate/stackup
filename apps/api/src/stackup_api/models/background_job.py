"""BackgroundJob — durable record of async job runs (Phase 7, ADR-005).

Redis/arq is the broker; this table is the source of truth for job state, so
a stuck or failed job is queryable and re-triggerable even if Redis data is
lost. `idempotency_key` is unique so a job accidentally enqueued twice (e.g.
a retried HTTP request, an overlapping cron tick) never runs its side
effects twice.
"""

from __future__ import annotations

import datetime
import uuid
from typing import Any

from sqlalchemy import JSON, DateTime, Enum, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from stackup_api.core.db import Base
from stackup_api.models.base import TimestampMixin, uuid_pk
from stackup_api.models.enums import JobStatus

# JSONB on PostgreSQL, plain JSON elsewhere (SQLite in tests).
JSONType = JSON().with_variant(JSONB(), "postgresql")


class BackgroundJob(TimestampMixin, Base):
    __tablename__ = "background_job"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_background_job_idempotency_key"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    job_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, native_enum=False, length=16),
        nullable=False,
        default=JobStatus.queued,
    )
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    result: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    last_error: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    started_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
