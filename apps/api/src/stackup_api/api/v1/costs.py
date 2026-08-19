"""CostItem endpoints (Phase 4) — nested under /workspaces/{id}/costs.

Every cost is validated against the workspace on write: its application must
belong to the workspace, its environment (if any) to that application, and
its service to a vendor visible to the workspace (global or own). Amount /
currency changes append a CostHistory row so price evolution is auditable.
Deleting a cost soft-ends it (status=ended), preserving its history (docs
§28: no physical deletion of entities with important history).
"""

from __future__ import annotations

import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from stackup_api.core.db import get_session
from stackup_api.core.deps import WorkspaceContext, get_workspace_context
from stackup_api.core.policy import Action, require
from stackup_api.domain.cost_engine import annualized_cost, monthly_equivalent
from stackup_api.models.application import Application, Environment
from stackup_api.models.cost import CostHistory, CostItem
from stackup_api.models.enums import BillingType, Certainty, CostStatus, Frequency
from stackup_api.models.vendor import Service, Vendor
from stackup_api.schemas.cost import (
    CostHistoryRead,
    CostItemCreate,
    CostItemRead,
    CostItemUpdate,
)
from stackup_api.services.audit import record_audit

router = APIRouter(prefix="/workspaces/{workspace_id}/costs", tags=["costs"])


def _serialize(cost: CostItem) -> CostItemRead:
    return CostItemRead(
        id=cost.id,
        workspace_id=cost.workspace_id,
        application_id=cost.application_id,
        environment_id=cost.environment_id,
        service_id=cost.service_id,
        name=cost.name,
        description=cost.description,
        category=cost.category,
        billing_type=cost.billing_type,
        amount=cost.amount,
        currency=cost.currency,
        frequency=cost.frequency,
        status=cost.status,
        certainty=cost.certainty,
        start_date=cost.start_date,
        end_date=cost.end_date,
        notes=cost.notes,
        monthly_equivalent=monthly_equivalent(
            cost.amount, cost.frequency, cost.billing_type, cost.status
        ),
        annualized_cost=annualized_cost(
            cost.amount, cost.frequency, cost.billing_type, cost.status
        ),
        created_at=cost.created_at,
        updated_at=cost.updated_at,
    )


async def _validate_application(
    session: AsyncSession, ctx: WorkspaceContext, application_id: uuid.UUID
) -> Application:
    app = await session.get(Application, application_id)
    if app is None or app.workspace_id != ctx.workspace.id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="application_id does not belong to this workspace.",
        )
    return app


async def _validate_environment(
    session: AsyncSession, application_id: uuid.UUID, environment_id: uuid.UUID | None
) -> None:
    if environment_id is None:
        return
    env = await session.get(Environment, environment_id)
    if env is None or env.application_id != application_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="environment_id does not belong to the given application.",
        )


async def _validate_service(
    session: AsyncSession, ctx: WorkspaceContext, service_id: uuid.UUID
) -> None:
    row = (
        await session.execute(
            select(Service, Vendor)
            .join(Vendor, Vendor.id == Service.vendor_id)
            .where(Service.id == service_id)
        )
    ).first()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="service_id is invalid.",
        )
    _service, vendor = row
    if vendor.workspace_id not in (None, ctx.workspace.id):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="service_id belongs to a vendor not visible to this workspace.",
        )


async def _get_cost(
    session: AsyncSession, ctx: WorkspaceContext, cost_id: uuid.UUID
) -> CostItem:
    cost = await session.get(CostItem, cost_id)
    if cost is None or cost.workspace_id != ctx.workspace.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cost not found."
        )
    return cost


@router.post("", response_model=CostItemRead, status_code=status.HTTP_201_CREATED)
async def create_cost(
    payload: CostItemCreate,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> CostItemRead:
    require(ctx.role, Action.DATA_WRITE)
    await _validate_application(session, ctx, payload.application_id)
    await _validate_environment(session, payload.application_id, payload.environment_id)
    await _validate_service(session, ctx, payload.service_id)

    cost = CostItem(
        workspace_id=ctx.workspace.id,
        application_id=payload.application_id,
        environment_id=payload.environment_id,
        service_id=payload.service_id,
        name=payload.name,
        description=payload.description,
        category=payload.category,
        billing_type=payload.billing_type,
        amount=payload.amount,
        currency=payload.currency.upper(),
        frequency=payload.frequency,
        certainty=payload.certainty,
        status=CostStatus.active,
        start_date=payload.start_date,
        end_date=payload.end_date,
        notes=payload.notes,
    )
    session.add(cost)
    await session.flush()

    # Seed the history ledger with the opening price.
    session.add(
        CostHistory(
            cost_item_id=cost.id,
            amount=cost.amount,
            currency=cost.currency,
            effective_from=cost.start_date or datetime.date.today(),
            reason="initial",
        )
    )
    await record_audit(
        session,
        actor_user_id=ctx.user.id,
        workspace_id=ctx.workspace.id,
        entity="cost_item",
        entity_id=str(cost.id),
        action="create",
        after={
            "name": cost.name,
            "amount": str(cost.amount),
            "currency": cost.currency,
        },
    )
    await session.commit()
    await session.refresh(cost)
    return _serialize(cost)


@router.get("", response_model=list[CostItemRead])
async def list_costs(
    application_id: uuid.UUID | None = None,
    environment_id: uuid.UUID | None = None,
    category: str | None = None,
    status_filter: CostStatus | None = None,
    certainty: Certainty | None = None,
    billing_type: BillingType | None = None,
    frequency: Frequency | None = None,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> list[CostItemRead]:
    require(ctx.role, Action.DATA_READ)
    stmt = select(CostItem).where(CostItem.workspace_id == ctx.workspace.id)
    if application_id is not None:
        stmt = stmt.where(CostItem.application_id == application_id)
    if environment_id is not None:
        stmt = stmt.where(CostItem.environment_id == environment_id)
    if category is not None:
        stmt = stmt.where(CostItem.category == category)
    if status_filter is not None:
        stmt = stmt.where(CostItem.status == status_filter)
    if certainty is not None:
        stmt = stmt.where(CostItem.certainty == certainty)
    if billing_type is not None:
        stmt = stmt.where(CostItem.billing_type == billing_type)
    if frequency is not None:
        stmt = stmt.where(CostItem.frequency == frequency)
    stmt = stmt.order_by(CostItem.created_at)
    costs = (await session.execute(stmt)).scalars().all()
    return [_serialize(c) for c in costs]


@router.get("/{cost_id}", response_model=CostItemRead)
async def get_cost(
    cost_id: uuid.UUID,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> CostItemRead:
    require(ctx.role, Action.DATA_READ)
    return _serialize(await _get_cost(session, ctx, cost_id))


@router.patch("/{cost_id}", response_model=CostItemRead)
async def update_cost(
    cost_id: uuid.UUID,
    payload: CostItemUpdate,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> CostItemRead:
    require(ctx.role, Action.DATA_WRITE)
    cost = await _get_cost(session, ctx, cost_id)
    data = payload.model_dump(exclude_unset=True)
    change_reason = data.pop("change_reason", None)

    if "environment_id" in data:
        await _validate_environment(
            session, cost.application_id, data["environment_id"]
        )

    old_amount, old_currency = cost.amount, cost.currency
    for field, value in data.items():
        if field == "currency" and value is not None:
            value = value.upper()
        setattr(cost, field, value)

    # Record a history entry when the price (amount or currency) changed.
    price_changed = cost.amount != old_amount or cost.currency != old_currency
    if price_changed:
        today = datetime.date.today()
        last = (
            (
                await session.execute(
                    select(CostHistory)
                    .where(
                        CostHistory.cost_item_id == cost.id,
                        CostHistory.effective_to.is_(None),
                    )
                    .order_by(CostHistory.effective_from.desc())
                )
            )
            .scalars()
            .first()
        )
        if last is not None:
            last.effective_to = today
        session.add(
            CostHistory(
                cost_item_id=cost.id,
                amount=cost.amount,
                currency=cost.currency,
                effective_from=today,
                reason=change_reason,
            )
        )

    await record_audit(
        session,
        actor_user_id=ctx.user.id,
        workspace_id=ctx.workspace.id,
        entity="cost_item",
        entity_id=str(cost.id),
        action="update",
        before={"amount": str(old_amount), "currency": old_currency},
        after={"amount": str(cost.amount), "currency": cost.currency},
    )
    await session.commit()
    await session.refresh(cost)
    return _serialize(cost)


@router.delete("/{cost_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cost(
    cost_id: uuid.UUID,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Soft-end the cost (status=ended), preserving its history (docs §28)."""
    require(ctx.role, Action.DATA_WRITE)
    cost = await _get_cost(session, ctx, cost_id)
    cost.status = CostStatus.ended
    if cost.end_date is None:
        cost.end_date = datetime.date.today()
    await record_audit(
        session,
        actor_user_id=ctx.user.id,
        workspace_id=ctx.workspace.id,
        entity="cost_item",
        entity_id=str(cost.id),
        action="end",
        before={"status": "active"},
        after={"status": "ended"},
    )
    await session.commit()


@router.get("/{cost_id}/history", response_model=list[CostHistoryRead])
async def get_cost_history(
    cost_id: uuid.UUID,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> list[CostHistory]:
    require(ctx.role, Action.DATA_READ)
    await _get_cost(session, ctx, cost_id)
    stmt = (
        select(CostHistory)
        .where(CostHistory.cost_item_id == cost_id)
        .order_by(CostHistory.effective_from)
    )
    return list((await session.execute(stmt)).scalars().all())
