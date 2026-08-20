"""User API schemas (fastapi-users)."""

from __future__ import annotations

import uuid

from fastapi_users import schemas
from pydantic import Field


class UserRead(schemas.BaseUser[uuid.UUID]):
    full_name: str | None = None


class UserCreate(schemas.BaseUserCreate):
    full_name: str | None = Field(default=None, max_length=160)


class UserUpdate(schemas.BaseUserUpdate):
    full_name: str | None = Field(default=None, max_length=160)
