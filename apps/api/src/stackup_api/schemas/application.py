"""Application and Environment API schemas."""

from __future__ import annotations

import datetime
import uuid

from pydantic import BaseModel, ConfigDict, Field

from stackup_api.models.enums import ApplicationStatus, EnvironmentType


class ApplicationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    production_url: str | None = Field(default=None, max_length=500)
    repository_url: str | None = Field(default=None, max_length=500)
    logo: str | None = Field(default=None, max_length=500)


class ApplicationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    status: ApplicationStatus | None = None
    production_url: str | None = Field(default=None, max_length=500)
    repository_url: str | None = Field(default=None, max_length=500)
    logo: str | None = Field(default=None, max_length=500)


class ApplicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    slug: str
    description: str | None
    status: ApplicationStatus
    production_url: str | None
    repository_url: str | None
    logo: str | None
    created_at: datetime.datetime
    updated_at: datetime.datetime


class EnvironmentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    type: EnvironmentType = EnvironmentType.production
    url: str | None = Field(default=None, max_length=500)


class EnvironmentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    type: EnvironmentType | None = None
    url: str | None = Field(default=None, max_length=500)


class EnvironmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    application_id: uuid.UUID
    name: str
    type: EnvironmentType
    url: str | None
    created_at: datetime.datetime
    updated_at: datetime.datetime
