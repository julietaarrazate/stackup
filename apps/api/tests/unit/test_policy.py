"""RBAC policy matrix tests (ADR-004)."""

from __future__ import annotations

import pytest

from stackup_api.core.policy import Action, has_permission, require
from stackup_api.models.enums import WorkspaceRole


def test_owner_can_do_everything() -> None:
    for action in Action:
        assert has_permission(WorkspaceRole.owner, action)


def test_viewer_is_read_only() -> None:
    assert has_permission(WorkspaceRole.viewer, Action.WORKSPACE_READ)
    assert has_permission(WorkspaceRole.viewer, Action.DATA_READ)
    assert not has_permission(WorkspaceRole.viewer, Action.DATA_WRITE)
    assert not has_permission(WorkspaceRole.viewer, Action.WORKSPACE_UPDATE)
    assert not has_permission(WorkspaceRole.viewer, Action.MEMBER_MANAGE)


def test_member_can_write_data_but_not_manage_members() -> None:
    assert has_permission(WorkspaceRole.member, Action.DATA_WRITE)
    assert not has_permission(WorkspaceRole.member, Action.MEMBER_MANAGE)
    assert not has_permission(WorkspaceRole.member, Action.WORKSPACE_UPDATE)


def test_admin_manages_members_but_not_ownership_or_delete() -> None:
    assert has_permission(WorkspaceRole.admin, Action.MEMBER_MANAGE)
    assert has_permission(WorkspaceRole.admin, Action.WORKSPACE_UPDATE)
    assert not has_permission(WorkspaceRole.admin, Action.OWNERSHIP_TRANSFER)
    assert not has_permission(WorkspaceRole.admin, Action.WORKSPACE_DELETE)


def test_require_raises_403_when_denied() -> None:
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        require(WorkspaceRole.viewer, Action.DATA_WRITE)
    assert exc.value.status_code == 403


def test_require_passes_when_allowed() -> None:
    require(WorkspaceRole.member, Action.DATA_WRITE)  # no raise
