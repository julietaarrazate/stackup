"""GitHub integration models (Phase 8, roadmap): OAuth connection + Detection.

A Detection is a *suggestion* derived from scanning a repo's manifest files
(package.json, requirements.txt, render.yaml, vercel.json, ...) — it never
becomes a CostItem on its own. Only an explicit confirm (creating the cost
through the same validated path as a manual entry) does that, per the
roadmap's "never auto-created CostItems".
"""

from __future__ import annotations

import uuid

from sqlalchemy import Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from stackup_api.core.db import Base
from stackup_api.models.base import TimestampMixin, uuid_pk
from stackup_api.models.enums import DetectionConfidence, DetectionStatus


class GitHubConnection(TimestampMixin, Base):
    """One connected GitHub account per workspace."""

    __tablename__ = "github_connection"
    __table_args__ = (
        UniqueConstraint("workspace_id", name="uq_github_connection_workspace"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspace.id", ondelete="CASCADE"), nullable=False, index=True
    )
    github_login: Mapped[str] = mapped_column(String(120), nullable=False)
    # Fernet ciphertext (core/crypto.py) — never the raw OAuth token at rest.
    access_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)


class Detection(TimestampMixin, Base):
    __tablename__ = "detection"

    id: Mapped[uuid.UUID] = uuid_pk()
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspace.id", ondelete="CASCADE"), nullable=False, index=True
    )
    application_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("application.id", ondelete="CASCADE"), nullable=True, index=True
    )
    repo_full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(255), nullable=False)
    vendor_name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str | None] = mapped_column(String(80), nullable=True)
    evidence: Mapped[str] = mapped_column(String(500), nullable=False)
    confidence: Mapped[DetectionConfidence] = mapped_column(
        Enum(DetectionConfidence, native_enum=False, length=16), nullable=False
    )
    status: Mapped[DetectionStatus] = mapped_column(
        Enum(DetectionStatus, native_enum=False, length=16),
        nullable=False,
        default=DetectionStatus.pending,
        index=True,
    )
    cost_item_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("cost_item.id", ondelete="SET NULL"), nullable=True
    )

    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            "repo_full_name",
            "file_path",
            "vendor_name",
            name="uq_detection_signal",
        ),
    )
