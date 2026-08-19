"""Report computation (Phase 5).

Aggregation happens in the backend, not the client (docs §24/§35). Costs for a
single workspace are modest in number, so we load the workspace's rows (always
filtered by workspace_id) and aggregate with the Cost Engine. Currencies are
never mixed. SQL-side normalization is a future optimization; correctness and
isolation come first here.
"""

from __future__ import annotations

import calendar
import datetime
import uuid
from collections import defaultdict
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from stackup_api.domain.cost_engine import annualized_cost, monthly_equivalent
from stackup_api.domain.money import quantize
from stackup_api.models.application import Application
from stackup_api.models.cost import CostHistory, CostItem
from stackup_api.models.enums import CostStatus
from stackup_api.models.vendor import Service, Vendor
from stackup_api.schemas.report import (
    CertaintyTotal,
    CurrencyTotal,
    EvolutionPoint,
    EvolutionReport,
    GroupTotal,
    OverviewReport,
    RecentChange,
)

# (label, currency) -> [monthly, annualized]
_Accum = dict[tuple[str, str], list[Decimal]]


def _add(
    acc: _Accum, label: str, currency: str, monthly: Decimal, annual: Decimal
) -> None:
    if monthly == 0 and annual == 0:
        return
    bucket = acc.setdefault((label, currency), [Decimal(0), Decimal(0)])
    bucket[0] = quantize(bucket[0] + monthly)
    bucket[1] = quantize(bucket[1] + annual)


def _to_group_totals(acc: _Accum) -> list[GroupTotal]:
    return [
        GroupTotal(label=label, currency=cur, monthly=vals[0], annualized=vals[1])
        for (label, cur), vals in sorted(
            acc.items(), key=lambda kv: (-kv[1][0], kv[0][0])
        )
    ]


async def _load_costs_with_names(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    *,
    application_id: uuid.UUID | None = None,
    environment_id: uuid.UUID | None = None,
    category: str | None = None,
    currency: str | None = None,
) -> list[tuple[CostItem, str, str]]:
    stmt = (
        select(CostItem, Application.name, Vendor.name)
        .join(Application, Application.id == CostItem.application_id)
        .join(Service, Service.id == CostItem.service_id)
        .join(Vendor, Vendor.id == Service.vendor_id)
        .where(CostItem.workspace_id == workspace_id)
    )
    if application_id is not None:
        stmt = stmt.where(CostItem.application_id == application_id)
    if environment_id is not None:
        stmt = stmt.where(CostItem.environment_id == environment_id)
    if category is not None:
        stmt = stmt.where(CostItem.category == category)
    if currency is not None:
        stmt = stmt.where(CostItem.currency == currency.upper())
    rows = (await session.execute(stmt)).all()
    return [(row[0], row[1], row[2]) for row in rows]


async def compute_overview(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    **filters: object,
) -> OverviewReport:
    costs = await _load_costs_with_names(session, workspace_id, **filters)  # type: ignore[arg-type]

    total: _Accum = {}
    certainty: dict[tuple[str, str], Decimal] = defaultdict(lambda: Decimal(0))
    by_category: _Accum = {}
    by_vendor: _Accum = {}
    by_application: _Accum = {}

    for cost, app_name, vendor_name in costs:
        m = monthly_equivalent(
            cost.amount, cost.frequency, cost.billing_type, cost.status
        )
        a = annualized_cost(cost.amount, cost.frequency, cost.billing_type, cost.status)
        _add(total, "total", cost.currency, m, a)
        _add(by_category, cost.category or "sin categoría", cost.currency, m, a)
        _add(by_vendor, vendor_name, cost.currency, m, a)
        _add(by_application, app_name, cost.currency, m, a)
        if m != 0:
            key = (cost.certainty.value, cost.currency)
            certainty[key] = quantize(certainty[key] + m)

    totals = [
        CurrencyTotal(currency=cur, monthly=vals[0], annualized=vals[1])
        for (_label, cur), vals in total.items()
    ]
    by_certainty = [
        CertaintyTotal(certainty=cert, currency=cur, monthly=amount)
        for (cert, cur), amount in sorted(certainty.items())
    ]

    recent = await _recent_changes(session, workspace_id)

    return OverviewReport(
        total=totals,
        by_certainty=by_certainty,
        by_category=_to_group_totals(by_category),
        by_vendor=_to_group_totals(by_vendor),
        by_application=_to_group_totals(by_application),
        recent_changes=recent,
        cost_item_count=len(costs),
    )


async def _recent_changes(
    session: AsyncSession, workspace_id: uuid.UUID, limit: int = 8
) -> list[RecentChange]:
    stmt = (
        select(CostHistory, CostItem.name)
        .join(CostItem, CostItem.id == CostHistory.cost_item_id)
        .where(CostItem.workspace_id == workspace_id)
        .order_by(CostHistory.created_at.desc())
        .limit(limit)
    )
    rows = (await session.execute(stmt)).all()
    return [
        RecentChange(
            cost_id=h.cost_item_id,
            cost_name=name,
            amount=h.amount,
            currency=h.currency,
            effective_from=h.effective_from,
            reason=h.reason,
        )
        for h, name in rows
    ]


def _month_reference(year: int, month: int, today: datetime.date) -> datetime.date:
    """A representative in-month date: month end, or today for the current month."""
    if year == today.year and month == today.month:
        return today
    last_day = calendar.monthrange(year, month)[1]
    return datetime.date(year, month, last_day)


def _iter_months(today: datetime.date, count: int) -> list[tuple[int, int]]:
    months: list[tuple[int, int]] = []
    y, m = today.year, today.month
    for _ in range(count):
        months.append((y, m))
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    return list(reversed(months))


async def compute_evolution(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    months: int = 6,
) -> EvolutionReport:
    costs = {
        c.id: c
        for c in (
            await session.execute(
                select(CostItem).where(CostItem.workspace_id == workspace_id)
            )
        ).scalars()
    }
    if not costs:
        return EvolutionReport(points=[])

    history = (
        (
            await session.execute(
                select(CostHistory).where(CostHistory.cost_item_id.in_(costs.keys()))
            )
        )
        .scalars()
        .all()
    )
    by_cost: dict[uuid.UUID, list[CostHistory]] = defaultdict(list)
    for h in history:
        by_cost[h.cost_item_id].append(h)

    today = datetime.date.today()
    points: list[EvolutionPoint] = []
    for year, month in _iter_months(today, months):
        ref = _month_reference(year, month, today)
        per_currency: dict[str, Decimal] = defaultdict(lambda: Decimal(0))
        for cost_id, cost in costs.items():
            effective = _effective_entry(by_cost.get(cost_id, []), ref)
            if effective is None:
                continue
            m = monthly_equivalent(
                effective.amount,
                cost.frequency,
                cost.billing_type,
                CostStatus.active,
            )
            if m != 0:
                per_currency[effective.currency] = quantize(
                    per_currency[effective.currency] + m
                )
        for currency, monthly in per_currency.items():
            points.append(
                EvolutionPoint(
                    period=f"{year:04d}-{month:02d}",
                    currency=currency,
                    monthly=monthly,
                )
            )
    return EvolutionReport(points=points)


def _effective_entry(
    entries: list[CostHistory], ref: datetime.date
) -> CostHistory | None:
    """The price entry effective on `ref` — [effective_from, effective_to)."""
    for entry in entries:
        if entry.effective_from <= ref and (
            entry.effective_to is None or ref < entry.effective_to
        ):
            return entry
    return None
