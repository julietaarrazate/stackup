"""Request dependencies for workspace-scoped authorization (ADR-004).

`get_workspace_context` is the single primitive every workspace-scoped
endpoint depends on: it resolves the caller's membership in the workspace
named in the path. A non-member (or a nonexistent workspace) yields 404, not
403, so the API never reveals whether a workspace exists to someone outside
it. The workspace is always derived from the authenticated session's
membership — never trusted from a request body.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from stackup_api.core.db import get_session
from stackup_api.core.users import current_active_user
from stackup_api.models.enums import WorkspaceRole
from stackup_api.models.user import User
from stackup_api.models.workspace import Workspace, WorkspaceMember


@dataclass(slots=True)
class WorkspaceContext:
    workspace: Workspace
    membership: WorkspaceMember
    user: User

    @property
    def role(self) -> WorkspaceRole:
        return self.membership.role


async def get_workspace_context(
    workspace_id: uuid.UUID,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_session),
) -> WorkspaceContext:
    result = await session.execute(
        select(Workspace, WorkspaceMember)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(
            Workspace.id == workspace_id,
            WorkspaceMember.user_id == user.id,
        )
    )
    row = result.first()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found."
        )
    workspace, membership = row
    return WorkspaceContext(workspace=workspace, membership=membership, user=user)
