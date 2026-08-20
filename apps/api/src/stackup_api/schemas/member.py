"""Workspace membership API schemas."""

from __future__ import annotations

import datetime
import uuid

from pydantic import BaseModel, ConfigDict, EmailStr

from stackup_api.models.enums import WorkspaceRole


class MemberCreate(BaseModel):
    """Add an existing user (by email) to the workspace with a role."""

    email: EmailStr
    role: WorkspaceRole = WorkspaceRole.member


class MemberUpdate(BaseModel):
    role: WorkspaceRole


class MemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    email: str
    role: WorkspaceRole
    created_at: datetime.datetime
    updated_at: datetime.datetime
