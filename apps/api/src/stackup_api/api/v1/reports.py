"""Report endpoints (Phase 5) — nested under /workspaces/{id}/reports.

All aggregation runs in the backend service; the client never recomputes cost
math. Every endpoint requires DATA_READ and is scoped to the caller's
workspace via get_workspace_context.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from stackup_api.core.db import get_session
from stackup_api.core.deps import WorkspaceContext, get_workspace_context
from stackup_api.core.policy import Action, require
from stackup_api.schemas.report import EvolutionReport, GroupTotal, OverviewReport
from stackup_api.services import reports

router = APIRouter(prefix="/workspaces/{workspace_id}/reports", tags=["reports"])


@router.get("/overview", response_model=OverviewReport)
async def overview(
    application_id: uuid.UUID | None = None,
    environment_id: uuid.UUID | None = None,
    category: str | None = None,
    currency: str | None = None,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> OverviewReport:
    require(ctx.role, Action.DATA_READ)
    return await reports.compute_overview(
        session,
        ctx.workspace.id,
        application_id=application_id,
        environment_id=environment_id,
        category=category,
        currency=currency,
    )


@router.get("/by-application", response_model=list[GroupTotal])
async def by_application(
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> list[GroupTotal]:
    require(ctx.role, Action.DATA_READ)
    return (await reports.compute_overview(session, ctx.workspace.id)).by_application


@router.get("/by-vendor", response_model=list[GroupTotal])
async def by_vendor(
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> list[GroupTotal]:
    require(ctx.role, Action.DATA_READ)
    return (await reports.compute_overview(session, ctx.workspace.id)).by_vendor


@router.get("/by-category", response_model=list[GroupTotal])
async def by_category(
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> list[GroupTotal]:
    require(ctx.role, Action.DATA_READ)
    return (await reports.compute_overview(session, ctx.workspace.id)).by_category


@router.get("/evolution", response_model=EvolutionReport)
async def evolution(
    months: int = Query(default=6, ge=1, le=24),
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> EvolutionReport:
    require(ctx.role, Action.DATA_READ)
    return await reports.compute_evolution(session, ctx.workspace.id, months=months)
