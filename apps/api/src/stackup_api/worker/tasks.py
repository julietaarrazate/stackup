"""arq task functions (Phase 7, ADR-005)."""

from __future__ import annotations

import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from stackup_api.core.db import SessionLocal
from stackup_api.models.cost import CostItem
from stackup_api.models.enums import CostStatus
from stackup_api.services.audit import record_audit
from stackup_api.services.jobs import run_tracked_job


async def auto_end_expired_costs(
    ctx: dict[str, Any],
    *,
    session_factory: async_sessionmaker[AsyncSession] = SessionLocal,
) -> dict[str, Any]:
    """Soft-end CostItems whose `end_date` has passed but are still `active`.

    Nothing else in the app transitions status on end_date automatically, so
    without this a cost with a past end_date (e.g. a one-year contract) keeps
    counting at full price in every overview and report indefinitely.
    """
    today = datetime.date.today()

    async def _run() -> dict[str, Any]:
        async with session_factory() as session:
            stmt = select(CostItem).where(
                CostItem.status == CostStatus.active,
                CostItem.end_date.is_not(None),
                CostItem.end_date < today,
            )
            costs = list((await session.execute(stmt)).scalars().all())
            for cost in costs:
                cost.status = CostStatus.ended
                await record_audit(
                    session,
                    actor_user_id=None,
                    workspace_id=cost.workspace_id,
                    entity="cost_item",
                    entity_id=str(cost.id),
                    action="auto_end",
                    before={"status": "active"},
                    after={"status": "ended", "reason": "end_date reached"},
                )
            await session.commit()
            return {"ended_count": len(costs)}

    return await run_tracked_job(
        job_type="auto_end_expired_costs",
        idempotency_key=f"auto_end_expired_costs:{today.isoformat()}",
        run=_run,
        session_factory=session_factory,
    )
