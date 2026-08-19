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


class BillingType(enum.StrEnum):
    fixed = "fixed"
    usage = "usage"
    one_time = "one_time"


class Frequency(enum.StrEnum):
    weekly = "weekly"
    monthly = "monthly"
    quarterly = "quarterly"
    yearly = "yearly"
    custom = "custom"


class Certainty(enum.StrEnum):
    confirmed = "confirmed"
    estimated = "estimated"
    projected = "projected"


class CostStatus(enum.StrEnum):
    active = "active"
    paused = "paused"
    ended = "ended"
