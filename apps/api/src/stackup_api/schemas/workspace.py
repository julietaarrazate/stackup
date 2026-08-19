"""Workspace API schemas."""

from __future__ import annotations

import datetime
import uuid

from pydantic import BaseModel, ConfigDict, Field

# ISO 4217 currency code; validated as data (extensible set — ADR-009).
CurrencyStr = str


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    base_currency: CurrencyStr = Field(default="USD", min_length=3, max_length=3)
    timezone: str = Field(default="UTC", max_length=64)


class WorkspaceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    base_currency: CurrencyStr | None = Field(default=None, min_length=3, max_length=3)
    timezone: str | None = Field(default=None, max_length=64)


class WorkspaceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    base_currency: str
    timezone: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
