"""Vendor and Service models — a shared catalog with per-workspace extensions.

`workspace_id` is nullable:
  - NULL  -> platform catalog entry, visible to every workspace (seeded).
  - set   -> private to that workspace (custom vendor/service a member added).

Reads return global + own-workspace rows; writes only ever touch own-workspace
rows, so one workspace can neither see nor mutate another's custom vendors.
"""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Index, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from stackup_api.core.db import Base
from stackup_api.models.base import TimestampMixin, uuid_pk


class Vendor(TimestampMixin, Base):
    __tablename__ = "vendor"
    __table_args__ = (
        # Private vendors: unique slug within a workspace.
        UniqueConstraint("workspace_id", "slug", name="uq_vendor_workspace_slug"),
        # Global catalog vendors (workspace_id IS NULL): globally unique slug.
        Index(
            "uq_vendor_global_slug",
            "slug",
            unique=True,
            sqlite_where=text("workspace_id IS NULL"),
            postgresql_where=text("workspace_id IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("workspace.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(140), nullable=False)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    logo: Mapped[str | None] = mapped_column(String(500), nullable=True)
    category: Mapped[str | None] = mapped_column(String(80), nullable=True)

    services: Mapped[list[Service]] = relationship(
        back_populates="vendor",
        cascade="all, delete-orphan",
    )


class Service(TimestampMixin, Base):
    __tablename__ = "service"
    __table_args__ = (
        UniqueConstraint("vendor_id", "slug", name="uq_service_vendor_slug"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    vendor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("vendor.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(140), nullable=False)
    category: Mapped[str | None] = mapped_column(String(80), nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)

    vendor: Mapped[Vendor] = relationship(back_populates="services")
