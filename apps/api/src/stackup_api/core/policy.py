"""Centralized authorization policy (ADR-004).

All role-based permission decisions live here. Route handlers call
`require(role, action)` — no ad-hoc role checks scattered across controllers.
Actions are coarse-grained and grow per phase; the matrix below is the single
source of truth for what each role may do.
"""

from __future__ import annotations

import enum

from fastapi import HTTPException, status

from stackup_api.models.enums import WorkspaceRole


class Action(enum.StrEnum):
    # Workspace-level
    WORKSPACE_READ = "workspace:read"
    WORKSPACE_UPDATE = "workspace:update"
    WORKSPACE_DELETE = "workspace:delete"
    # Membership
    MEMBER_READ = "member:read"
    MEMBER_MANAGE = "member:manage"  # add/remove members, change non-owner roles
    OWNERSHIP_TRANSFER = "ownership:transfer"
    # Operational data (applications, environments, vendors, services, costs,
    # expenses, evidence) — used from Phase 3 onward.
    DATA_READ = "data:read"
    DATA_WRITE = "data:write"


# Role → allowed actions. Higher roles are supersets, but we list explicitly
# rather than rely on ordering so the grant is auditable at a glance.
_MATRIX: dict[WorkspaceRole, frozenset[Action]] = {
    WorkspaceRole.owner: frozenset(Action),  # everything
    WorkspaceRole.admin: frozenset(
        {
            Action.WORKSPACE_READ,
            Action.WORKSPACE_UPDATE,
            Action.MEMBER_READ,
            Action.MEMBER_MANAGE,
            Action.DATA_READ,
            Action.DATA_WRITE,
        }
    ),
    WorkspaceRole.member: frozenset(
        {
            Action.WORKSPACE_READ,
            Action.MEMBER_READ,
            Action.DATA_READ,
            Action.DATA_WRITE,
        }
    ),
    WorkspaceRole.viewer: frozenset(
        {
            Action.WORKSPACE_READ,
            Action.MEMBER_READ,
            Action.DATA_READ,
        }
    ),
}


def has_permission(role: WorkspaceRole, action: Action) -> bool:
    return action in _MATRIX[role]


def require(role: WorkspaceRole, action: Action) -> None:
    """Raise 403 if the role may not perform the action."""
    if not has_permission(role, action):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{role.value}' is not permitted to {action.value}.",
        )
