"""Shared CostItem creation logic (Phase 4/8).

Extracted so the direct `POST /costs` endpoint and the Phase 8 detection
confirm flow both create cost items through the exact same validated path —
a Detection is never turned into a CostItem by any other route.
"""

from __future__ import annotations

import datetime
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from stackup_api.core.deps import WorkspaceContext
from stackup_api.domain.cost_engine import annualized_cost, monthly_equivalent
from stackup_api.models.application import Application, Environment
from stackup_api.models.cost import CostHistory, CostItem
from stackup_api.models.enums import CostStatus
from stackup_api.models.vendor import Service, Vendor
from stackup_api.schemas.cost import CostItemCreate, CostItemRead
from stackup_api.services.audit import record_audit


def serialize_cost_item(cost: CostItem) -> CostItemRead:
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


async def validate_application(
    session: AsyncSession, ctx: WorkspaceContext, application_id: uuid.UUID
) -> Application:
    app = await session.get(Application, application_id)
    if app is None or app.workspace_id != ctx.workspace.id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="application_id does not belong to this workspace.",
        )
    return app


async def validate_environment(
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


async def validate_service(
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


async def create_cost_item(
    session: AsyncSession, ctx: WorkspaceContext, payload: CostItemCreate
) -> CostItem:
    await validate_application(session, ctx, payload.application_id)
    await validate_environment(session, payload.application_id, payload.environment_id)
    await validate_service(session, ctx, payload.service_id)

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
    return cost
