"""Application and Environment endpoints (Phase 3).

All routes are nested under /workspaces/{workspace_id} so the workspace — and
thus authorization — is always derived from the session-resolved membership
(get_workspace_context), never from the request body.
"""

from __future__ import annotations

import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from stackup_api.core.db import get_session
from stackup_api.core.deps import WorkspaceContext, get_workspace_context
from stackup_api.core.policy import Action, require
from stackup_api.core.slug import slugify
from stackup_api.models.application import Application, Environment
from stackup_api.models.enums import ApplicationStatus
from stackup_api.schemas.application import (
    ApplicationCreate,
    ApplicationRead,
    ApplicationUpdate,
    EnvironmentCreate,
    EnvironmentRead,
    EnvironmentUpdate,
)
from stackup_api.services.audit import record_audit

router = APIRouter(
    prefix="/workspaces/{workspace_id}/applications", tags=["applications"]
)


async def _unique_app_slug(
    session: AsyncSession, workspace_id: uuid.UUID, name: str
) -> str:
    base = slugify(name)[:120]
    candidate = base
    while True:
        exists = await session.scalar(
            select(Application.id).where(
                Application.workspace_id == workspace_id,
                Application.slug == candidate,
            )
        )
        if exists is None:
            return candidate
        candidate = f"{base}-{secrets.token_hex(3)}"


async def _get_application(
    session: AsyncSession, ctx: WorkspaceContext, application_id: uuid.UUID
) -> Application:
    app = await session.get(Application, application_id)
    if app is None or app.workspace_id != ctx.workspace.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Application not found."
        )
    return app


@router.post("", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
async def create_application(
    payload: ApplicationCreate,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> Application:
    require(ctx.role, Action.DATA_WRITE)
    app = Application(
        workspace_id=ctx.workspace.id,
        name=payload.name,
        slug=await _unique_app_slug(session, ctx.workspace.id, payload.name),
        description=payload.description,
        production_url=payload.production_url,
        repository_url=payload.repository_url,
        logo=payload.logo,
        status=ApplicationStatus.active,
    )
    session.add(app)
    await record_audit(
        session,
        actor_user_id=ctx.user.id,
        workspace_id=ctx.workspace.id,
        entity="application",
        action="create",
        after={"name": app.name, "slug": app.slug},
    )
    await session.commit()
    await session.refresh(app)
    return app


@router.get("", response_model=list[ApplicationRead])
async def list_applications(
    status_filter: ApplicationStatus | None = None,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> list[Application]:
    require(ctx.role, Action.DATA_READ)
    stmt = select(Application).where(Application.workspace_id == ctx.workspace.id)
    if status_filter is not None:
        stmt = stmt.where(Application.status == status_filter)
    stmt = stmt.order_by(Application.created_at)
    return list((await session.execute(stmt)).scalars().all())


@router.get("/{application_id}", response_model=ApplicationRead)
async def get_application(
    application_id: uuid.UUID,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> Application:
    require(ctx.role, Action.DATA_READ)
    return await _get_application(session, ctx, application_id)


@router.patch("/{application_id}", response_model=ApplicationRead)
async def update_application(
    application_id: uuid.UUID,
    payload: ApplicationUpdate,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> Application:
    require(ctx.role, Action.DATA_WRITE)
    app = await _get_application(session, ctx, application_id)
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(app, field, value)
    await record_audit(
        session,
        actor_user_id=ctx.user.id,
        workspace_id=ctx.workspace.id,
        entity="application",
        entity_id=str(app.id),
        action="update",
        after=data,
    )
    await session.commit()
    await session.refresh(app)
    return app


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(
    application_id: uuid.UUID,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> None:
    require(ctx.role, Action.DATA_WRITE)
    app = await _get_application(session, ctx, application_id)
    await record_audit(
        session,
        actor_user_id=ctx.user.id,
        workspace_id=ctx.workspace.id,
        entity="application",
        entity_id=str(app.id),
        action="delete",
        before={"name": app.name, "slug": app.slug},
    )
    await session.delete(app)
    await session.commit()


# --- Environments (nested) ---------------------------------------------


@router.get("/{application_id}/environments", response_model=list[EnvironmentRead])
async def list_environments(
    application_id: uuid.UUID,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> list[Environment]:
    require(ctx.role, Action.DATA_READ)
    await _get_application(session, ctx, application_id)
    stmt = (
        select(Environment)
        .where(Environment.application_id == application_id)
        .order_by(Environment.created_at)
    )
    return list((await session.execute(stmt)).scalars().all())


@router.post(
    "/{application_id}/environments",
    response_model=EnvironmentRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_environment(
    application_id: uuid.UUID,
    payload: EnvironmentCreate,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> Environment:
    require(ctx.role, Action.DATA_WRITE)
    await _get_application(session, ctx, application_id)
    env = Environment(
        application_id=application_id,
        name=payload.name,
        type=payload.type,
        url=payload.url,
    )
    session.add(env)
    await record_audit(
        session,
        actor_user_id=ctx.user.id,
        workspace_id=ctx.workspace.id,
        entity="environment",
        action="create",
        after={"application_id": str(application_id), "name": env.name},
    )
    await session.commit()
    await session.refresh(env)
    return env


async def _get_environment(
    session: AsyncSession,
    ctx: WorkspaceContext,
    application_id: uuid.UUID,
    env_id: uuid.UUID,
) -> Environment:
    await _get_application(session, ctx, application_id)
    env = await session.get(Environment, env_id)
    if env is None or env.application_id != application_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Environment not found."
        )
    return env


@router.patch(
    "/{application_id}/environments/{environment_id}",
    response_model=EnvironmentRead,
)
async def update_environment(
    application_id: uuid.UUID,
    environment_id: uuid.UUID,
    payload: EnvironmentUpdate,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> Environment:
    require(ctx.role, Action.DATA_WRITE)
    env = await _get_environment(session, ctx, application_id, environment_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(env, field, value)
    await session.commit()
    await session.refresh(env)
    return env


@router.delete(
    "/{application_id}/environments/{environment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_environment(
    application_id: uuid.UUID,
    environment_id: uuid.UUID,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> None:
    require(ctx.role, Action.DATA_WRITE)
    env = await _get_environment(session, ctx, application_id, environment_id)
    await session.delete(env)
    await session.commit()
