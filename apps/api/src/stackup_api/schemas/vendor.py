"""Vendor and Service API schemas."""

from __future__ import annotations

import datetime
import uuid

from pydantic import BaseModel, ConfigDict, Field


class VendorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    website: str | None = Field(default=None, max_length=500)
    logo: str | None = Field(default=None, max_length=500)
    category: str | None = Field(default=None, max_length=80)


class VendorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    website: str | None = Field(default=None, max_length=500)
    logo: str | None = Field(default=None, max_length=500)
    category: str | None = Field(default=None, max_length=80)


class VendorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID | None
    name: str
    slug: str
    website: str | None
    logo: str | None
    category: str | None
    # True when this is a shared catalog vendor (workspace_id is null).
    is_global: bool = False
    created_at: datetime.datetime
    updated_at: datetime.datetime

    @classmethod
    def from_model(cls, vendor: object) -> VendorRead:
        data = cls.model_validate(vendor)
        data.is_global = getattr(vendor, "workspace_id", None) is None
        return data


class ServiceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    category: str | None = Field(default=None, max_length=80)
    website: str | None = Field(default=None, max_length=500)


class ServiceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    category: str | None = Field(default=None, max_length=80)
    website: str | None = Field(default=None, max_length=500)


class ServiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    vendor_id: uuid.UUID
    name: str
    slug: str
    category: str | None
    website: str | None
    created_at: datetime.datetime
    updated_at: datetime.datetime
