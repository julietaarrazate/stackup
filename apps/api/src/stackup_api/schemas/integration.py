"""GitHub integration API schemas (Phase 8)."""

from __future__ import annotations

import datetime
import uuid

from pydantic import BaseModel, ConfigDict

from stackup_api.models.enums import DetectionConfidence, DetectionStatus


class GitHubAuthorizeResponse(BaseModel):
    authorize_url: str


class GitHubCallback(BaseModel):
    code: str
    state: str


class GitHubConnectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    github_login: str
    created_at: datetime.datetime


class GitHubRepo(BaseModel):
    full_name: str
    private: bool
    default_branch: str


class ScanRequest(BaseModel):
    repo_full_name: str
    application_id: uuid.UUID | None = None


class DetectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    application_id: uuid.UUID | None
    repo_full_name: str
    file_path: str
    vendor_name: str
    category: str | None
    evidence: str
    confidence: DetectionConfidence
    status: DetectionStatus
    cost_item_id: uuid.UUID | None
    created_at: datetime.datetime
