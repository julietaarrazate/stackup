"""Workspace and membership endpoints (Phase 2).

Every handler derives authorization from the session-resolved membership
(`get_workspace_context`) and the central policy module. Ownership is
protected by two invariants enforced here:
  1. only an owner may grant/modify/remove the `owner` role, and
  2. a workspace must always retain at least one owner.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from stackup_api.core.db import get_session
from stackup_api.core.deps import WorkspaceContext, get_workspace_context
from stackup_api.core.policy import Action, require
from stackup_api.core.users import current_active_user
from stackup_api.models.enums import WorkspaceRole
from stackup_api.models.user import User
from stackup_api.models.workspace import Workspace, WorkspaceMember
from stackup_api.schemas.member import MemberCreate, MemberRead, MemberUpdate
from stackup_api.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceRead,
    WorkspaceUpdate,
)
from stackup_api.services.audit import record_audit
from stackup_api.services.workspace import create_workspace_with_owner

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


def _member_read(member: WorkspaceMember, email: str) -> MemberRead:
    return MemberRead(
        id=member.id,
        workspace_id=member.workspace_id,
        user_id=member.user_id,
        email=email,
        role=member.role,
        created_at=member.created_at,
        updated_at=member.updated_at,
    )


async def _count_owners(session: AsyncSession, workspace_id: uuid.UUID) -> int:
    return (
        await session.scalar(
            select(func.count())
            .select_from(WorkspaceMember)
            .where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.role == WorkspaceRole.owner,
            )
        )
    ) or 0


@router.post("", response_model=WorkspaceRead, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    payload: WorkspaceCreate,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_session),
) -> Workspace:
    workspace = await create_workspace_with_owner(
        session,
        owner_id=user.id,
        name=payload.name,
        base_currency=payload.base_currency,
        timezone=payload.timezone,
    )
    await record_audit(
        session,
        actor_user_id=user.id,
        workspace_id=workspace.id,
        entity="workspace",
        entity_id=str(workspace.id),
        action="create",
        after={"name": workspace.name, "slug": workspace.slug},
    )
    await session.commit()
    await session.refresh(workspace)
    return workspace


@router.get("", response_model=list[WorkspaceRead])
async def list_my_workspaces(
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_session),
) -> list[Workspace]:
    result = await session.execute(
        select(Workspace)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(WorkspaceMember.user_id == user.id)
        .order_by(Workspace.created_at)
    )
    return list(result.scalars().all())


@router.get("/{workspace_id}", response_model=WorkspaceRead)
async def get_workspace(
    ctx: WorkspaceContext = Depends(get_workspace_context),
) -> Workspace:
    require(ctx.role, Action.WORKSPACE_READ)
    return ctx.workspace


@router.patch("/{workspace_id}", response_model=WorkspaceRead)
async def update_workspace(
    payload: WorkspaceUpdate,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> Workspace:
    require(ctx.role, Action.WORKSPACE_UPDATE)
    before = {
        "name": ctx.workspace.name,
        "base_currency": ctx.workspace.base_currency,
        "timezone": ctx.workspace.timezone,
    }
    data = payload.model_dump(exclude_unset=True)
    if "name" in data and data["name"] is not None:
        ctx.workspace.name = data["name"]
    if "base_currency" in data and data["base_currency"] is not None:
        ctx.workspace.base_currency = data["base_currency"].upper()
    if "timezone" in data and data["timezone"] is not None:
        ctx.workspace.timezone = data["timezone"]
    await record_audit(
        session,
        actor_user_id=ctx.user.id,
        workspace_id=ctx.workspace.id,
        entity="workspace",
        entity_id=str(ctx.workspace.id),
        action="update",
        before=before,
        after={
            "name": ctx.workspace.name,
            "base_currency": ctx.workspace.base_currency,
            "timezone": ctx.workspace.timezone,
        },
    )
    await session.commit()
    await session.refresh(ctx.workspace)
    return ctx.workspace


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> None:
    require(ctx.role, Action.WORKSPACE_DELETE)
    await record_audit(
        session,
        actor_user_id=ctx.user.id,
        workspace_id=ctx.workspace.id,
        entity="workspace",
        entity_id=str(ctx.workspace.id),
        action="delete",
        before={"name": ctx.workspace.name, "slug": ctx.workspace.slug},
    )
    await session.delete(ctx.workspace)
    await session.commit()


# --- Membership ---------------------------------------------------------


@router.get("/{workspace_id}/members", response_model=list[MemberRead])
async def list_members(
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> list[MemberRead]:
    require(ctx.role, Action.MEMBER_READ)
    result = await session.execute(
        select(WorkspaceMember, User.email)  # type: ignore[call-overload]
        .join(User, User.id == WorkspaceMember.user_id)
        .where(WorkspaceMember.workspace_id == ctx.workspace.id)
        .order_by(WorkspaceMember.created_at)
    )
    return [_member_read(member, email) for member, email in result.all()]


@router.post(
    "/{workspace_id}/members",
    response_model=MemberRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_member(
    payload: MemberCreate,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> MemberRead:
    require(ctx.role, Action.MEMBER_MANAGE)
    # Only an owner may grant the owner role.
    if payload.role == WorkspaceRole.owner:
        require(ctx.role, Action.OWNERSHIP_TRANSFER)

    target = await session.scalar(
        select(User).where(func.lower(User.email) == payload.email.lower())
    )
    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No user with that email exists.",
        )

    existing = await session.scalar(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == ctx.workspace.id,
            WorkspaceMember.user_id == target.id,
        )
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member of this workspace.",
        )

    member = WorkspaceMember(
        workspace_id=ctx.workspace.id,
        user_id=target.id,
        role=payload.role,
    )
    session.add(member)
    await record_audit(
        session,
        actor_user_id=ctx.user.id,
        workspace_id=ctx.workspace.id,
        entity="workspace_member",
        action="add",
        after={"user_id": str(target.id), "role": payload.role.value},
    )
    await session.commit()
    await session.refresh(member)
    return _member_read(member, target.email)


@router.patch("/{workspace_id}/members/{member_id}", response_model=MemberRead)
async def update_member_role(
    member_id: uuid.UUID,
    payload: MemberUpdate,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> MemberRead:
    require(ctx.role, Action.MEMBER_MANAGE)
    member = await session.get(WorkspaceMember, member_id)
    if member is None or member.workspace_id != ctx.workspace.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Member not found."
        )

    # Changing to/from owner is an ownership action (owner-only).
    if member.role == WorkspaceRole.owner or payload.role == WorkspaceRole.owner:
        require(ctx.role, Action.OWNERSHIP_TRANSFER)

    # Never leave the workspace without an owner.
    if (
        member.role == WorkspaceRole.owner
        and payload.role != WorkspaceRole.owner
        and await _count_owners(session, ctx.workspace.id) <= 1
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A workspace must have at least one owner.",
        )

    before_role = member.role.value
    member.role = payload.role
    await record_audit(
        session,
        actor_user_id=ctx.user.id,
        workspace_id=ctx.workspace.id,
        entity="workspace_member",
        entity_id=str(member.id),
        action="update_role",
        before={"role": before_role},
        after={"role": member.role.value},
    )
    await session.commit()
    await session.refresh(member)
    user = await session.get(User, member.user_id)
    assert user is not None  # FK guarantees this
    return _member_read(member, user.email)


@router.delete(
    "/{workspace_id}/members/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_member(
    member_id: uuid.UUID,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> None:
    require(ctx.role, Action.MEMBER_MANAGE)
    member = await session.get(WorkspaceMember, member_id)
    if member is None or member.workspace_id != ctx.workspace.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Member not found."
        )

    if member.role == WorkspaceRole.owner:
        require(ctx.role, Action.OWNERSHIP_TRANSFER)
        if await _count_owners(session, ctx.workspace.id) <= 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A workspace must have at least one owner.",
            )

    await record_audit(
        session,
        actor_user_id=ctx.user.id,
        workspace_id=ctx.workspace.id,
        entity="workspace_member",
        entity_id=str(member.id),
        action="remove",
        before={"user_id": str(member.user_id), "role": member.role.value},
    )
    await session.delete(member)
    await session.commit()
