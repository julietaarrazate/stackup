"""User model (fastapi-users compatible)."""

from __future__ import annotations

import datetime

from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from stackup_api.core.db import Base


class User(SQLAlchemyBaseUserTableUUID, Base):
    """Application user.

    Inherits id (UUID), email, hashed_password, is_active, is_superuser,
    is_verified from fastapi-users. Domain relationships (workspace
    membership) are modeled on WorkspaceMember, keeping this table auth-only.
    """

    __tablename__ = "user"

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
