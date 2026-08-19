"""Application and Environment models (workspace-scoped)."""

from __future__ import annotations

import uuid

from sqlalchemy import Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from stackup_api.core.db import Base
from stackup_api.models.base import TimestampMixin, uuid_pk
from stackup_api.models.enums import ApplicationStatus, EnvironmentType


class Application(TimestampMixin, Base):
    __tablename__ = "application"
    __table_args__ = (
        UniqueConstraint("workspace_id", "slug", name="uq_application_workspace_slug"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspace.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(140), nullable=False)
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus, native_enum=False, length=16),
        nullable=False,
        default=ApplicationStatus.active,
    )
    production_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    repository_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    logo: Mapped[str | None] = mapped_column(String(500), nullable=True)

    environments: Mapped[list[Environment]] = relationship(
        back_populates="application",
        cascade="all, delete-orphan",
    )


class Environment(TimestampMixin, Base):
    __tablename__ = "environment"
    __table_args__ = (
        UniqueConstraint(
            "application_id", "name", name="uq_environment_application_name"
        ),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    application_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("application.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    type: Mapped[EnvironmentType] = mapped_column(
        Enum(EnvironmentType, native_enum=False, length=16),
        nullable=False,
        default=EnvironmentType.production,
    )
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    application: Mapped[Application] = relationship(back_populates="environments")
