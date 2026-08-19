"""SQLAlchemy ORM models.

Every model module is imported here so `Base.metadata` is fully populated for
Alembic autogenerate and `alembic check`. Models are added per phase
(auth/workspace in Phase 2; Application/Vendor/Service in Phase 3;
CostItem/CostHistory in Phase 4; etc.).
"""

from __future__ import annotations

from stackup_api.core.db import Base
from stackup_api.models.access_token import AccessToken
from stackup_api.models.application import Application, Environment
from stackup_api.models.audit import AuditEvent
from stackup_api.models.cost import CostHistory, CostItem
from stackup_api.models.enums import (
    ApplicationStatus,
    BillingType,
    Certainty,
    CostStatus,
    EnvironmentType,
    Frequency,
    WorkspaceRole,
)
from stackup_api.models.user import User
from stackup_api.models.vendor import Service, Vendor
from stackup_api.models.workspace import Workspace, WorkspaceMember

__all__ = [
    "Base",
    "User",
    "AccessToken",
    "Workspace",
    "WorkspaceMember",
    "WorkspaceRole",
    "AuditEvent",
    "Application",
    "Environment",
    "ApplicationStatus",
    "EnvironmentType",
    "Vendor",
    "Service",
    "CostItem",
    "CostHistory",
    "BillingType",
    "Frequency",
    "Certainty",
    "CostStatus",
]
