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


class EvidenceType(enum.StrEnum):
    invoice = "invoice"
    receipt = "receipt"
    contract = "contract"
    screenshot = "screenshot"
    other = "other"


class ExpenseStatus(enum.StrEnum):
    pending = "pending"
    paid = "paid"
    failed = "failed"
    refunded = "refunded"


class JobStatus(enum.StrEnum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"


class DetectionStatus(enum.StrEnum):
    pending = "pending"
    confirmed = "confirmed"
    dismissed = "dismissed"


class DetectionConfidence(enum.StrEnum):
    high = "high"
    medium = "medium"
