"""Detection review endpoints (Phase 8).

A Detection is only ever a suggestion. Confirming one creates a CostItem
through the exact same validated path as a manual entry
(`services.costs.create_cost_item`) — there is no other route from a
Detection to a CostItem.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from stackup_api.core.db import get_session
from stackup_api.core.deps import WorkspaceContext, get_workspace_context
from stackup_api.core.policy import Action, require
from stackup_api.models.enums import DetectionStatus
from stackup_api.models.integration import Detection
from stackup_api.schemas.cost import CostItemCreate, CostItemRead
from stackup_api.schemas.integration import DetectionRead
from stackup_api.services.costs import create_cost_item, serialize_cost_item

router = APIRouter(prefix="/workspaces/{workspace_id}/detections", tags=["detections"])


async def _get_detection(
    session: AsyncSession, ctx: WorkspaceContext, detection_id: uuid.UUID
) -> Detection:
    detection = await session.get(Detection, detection_id)
    if detection is None or detection.workspace_id != ctx.workspace.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Detection not found.")
    return detection


@router.get("", response_model=list[DetectionRead])
async def list_detections(
    detection_status: DetectionStatus | None = None,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> list[DetectionRead]:
    require(ctx.role, Action.DATA_READ)
    stmt = select(Detection).where(Detection.workspace_id == ctx.workspace.id)
    if detection_status is not None:
        stmt = stmt.where(Detection.status == detection_status)
    stmt = stmt.order_by(Detection.created_at.desc())
    rows = (await session.execute(stmt)).scalars().all()
    return [DetectionRead.model_validate(d) for d in rows]


@router.post("/{detection_id}/confirm", response_model=CostItemRead)
async def confirm_detection(
    detection_id: uuid.UUID,
    payload: CostItemCreate,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> CostItemRead:
    require(ctx.role, Action.DATA_WRITE)
    detection = await _get_detection(session, ctx, detection_id)
    if detection.status != DetectionStatus.pending:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Detection was already confirmed or dismissed."
        )

    cost = await create_cost_item(session, ctx, payload)
    detection.status = DetectionStatus.confirmed
    detection.cost_item_id = cost.id
    await session.commit()
    await session.refresh(cost)
    return serialize_cost_item(cost)


@router.post("/{detection_id}/dismiss", response_model=DetectionRead)
async def dismiss_detection(
    detection_id: uuid.UUID,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> DetectionRead:
    require(ctx.role, Action.DATA_WRITE)
    detection = await _get_detection(session, ctx, detection_id)
    if detection.status != DetectionStatus.pending:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Detection was already confirmed or dismissed."
        )
    detection.status = DetectionStatus.dismissed
    await session.commit()
    await session.refresh(detection)
    return DetectionRead.model_validate(detection)
