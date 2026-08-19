"""Domain enumerations."""

from __future__ import annotations

import enum


class WorkspaceRole(enum.StrEnum):
    owner = "owner"
    admin = "admin"
    member = "member"
    viewer = "viewer"
