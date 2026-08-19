"""Domain enumerations."""

from __future__ import annotations

import enum


class WorkspaceRole(enum.StrEnum):
    owner = "owner"
    admin = "admin"
    member = "member"
    viewer = "viewer"


class ApplicationStatus(enum.StrEnum):
    active = "active"
    archived = "archived"


class EnvironmentType(enum.StrEnum):
    development = "development"
    staging = "staging"
    production = "production"
    other = "other"
