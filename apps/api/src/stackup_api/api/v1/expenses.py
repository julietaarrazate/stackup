"""Expense endpoints (Phase 6) — payments against a CostItem.

An Expense is a real payment, distinct from the CostItem's list price. The
referenced cost item and evidence must both belong to the workspace.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from stackup_api.core.db import get_session
from stackup_api.core.deps import WorkspaceContext, get_workspace_context
from stackup_api.core.policy import Action, require
from stackup_api.models.cost import CostItem
from stackup_api.models.evidence import Evidence, Expense
from stackup_api.schemas.evidence import ExpenseCreate, ExpenseRead, ExpenseUpdate
from stackup_api.services.audit import record_audit

router = APIRouter(prefix="/workspaces/{workspace_id}/expenses", tags=["expenses"])


async def _validate_cost(
    session: AsyncSession, ctx: WorkspaceContext, cost_item_id: uuid.UUID
) -> None:
    cost = await session.get(CostItem, cost_item_id)
    if cost is None or cost.workspace_id != ctx.workspace.id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="cost_item_id does not belong to this workspace.",
        )


async def _validate_evidence(
    session: AsyncSession, ctx: WorkspaceContext, evidence_id: uuid.UUID | None
) -> None:
    if evidence_id is None:
        return
    ev = await session.get(Evidence, evidence_id)
    if ev is None or ev.workspace_id != ctx.workspace.id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="evidence_id does not belong to this workspace.",
        )


async def _get_expense(
    session: AsyncSession, ctx: WorkspaceContext, expense_id: uuid.UUID
) -> Expense:
    exp = await session.get(Expense, expense_id)
    if exp is None or exp.workspace_id != ctx.workspace.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found."
        )
    return exp


@router.post("", response_model=ExpenseRead, status_code=status.HTTP_201_CREATED)
async def create_expense(
    payload: ExpenseCreate,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> Expense:
    require(ctx.role, Action.DATA_WRITE)
    await _validate_cost(session, ctx, payload.cost_item_id)
    await _validate_evidence(session, ctx, payload.evidence_id)
    expense = Expense(
        workspace_id=ctx.workspace.id,
        cost_item_id=payload.cost_item_id,
        amount=payload.amount,
        currency=payload.currency.upper(),
        paid_at=payload.paid_at,
        status=payload.status,
        invoice_number=payload.invoice_number,
        evidence_id=payload.evidence_id,
    )
    session.add(expense)
    await record_audit(
        session,
        actor_user_id=ctx.user.id,
        workspace_id=ctx.workspace.id,
        entity="expense",
        action="create",
        after={"amount": str(expense.amount), "currency": expense.currency},
    )
    await session.commit()
    await session.refresh(expense)
    return expense


@router.get("", response_model=list[ExpenseRead])
async def list_expenses(
    cost_item_id: uuid.UUID | None = None,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> list[Expense]:
    require(ctx.role, Action.DATA_READ)
    stmt = select(Expense).where(Expense.workspace_id == ctx.workspace.id)
    if cost_item_id is not None:
        stmt = stmt.where(Expense.cost_item_id == cost_item_id)
    stmt = stmt.order_by(Expense.created_at.desc())
    return list((await session.execute(stmt)).scalars().all())


@router.get("/{expense_id}", response_model=ExpenseRead)
async def get_expense(
    expense_id: uuid.UUID,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> Expense:
    require(ctx.role, Action.DATA_READ)
    return await _get_expense(session, ctx, expense_id)


@router.patch("/{expense_id}", response_model=ExpenseRead)
async def update_expense(
    expense_id: uuid.UUID,
    payload: ExpenseUpdate,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> Expense:
    require(ctx.role, Action.DATA_WRITE)
    expense = await _get_expense(session, ctx, expense_id)
    data = payload.model_dump(exclude_unset=True)
    if "evidence_id" in data:
        await _validate_evidence(session, ctx, data["evidence_id"])
    for field, value in data.items():
        if field == "currency" and value is not None:
            value = value.upper()
        setattr(expense, field, value)
    await session.commit()
    await session.refresh(expense)
    return expense


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
    expense_id: uuid.UUID,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> None:
    require(ctx.role, Action.DATA_WRITE)
    expense = await _get_expense(session, ctx, expense_id)
    await session.delete(expense)
    await session.commit()
