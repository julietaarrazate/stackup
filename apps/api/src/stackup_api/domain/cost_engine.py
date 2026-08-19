"""Cost Engine (docs section 12).

The single, pure, currency-aware place that turns a cost into normalized
monthly/annual figures and aggregates many costs. No I/O, no ORM — it accepts
plain values or any object satisfying `CostContribution`, so it is trivially
unit- and property-testable and is never duplicated in the frontend.

Normalization rules:
  - Only `active`, recurring costs contribute to recurring monthly/annual
    totals. `paused`/`ended` contribute 0; `one_time` billing contributes 0
    (it is a single charge, not a recurring cost); `custom` frequency cannot
    be normalized without an interval, so it also contributes 0 to recurring
    totals (such items are surfaced separately by callers, never silently
    summed).
  - weekly  -> amount * 52 / 12
  - monthly -> amount
  - quarterly -> amount / 3
  - yearly  -> amount / 12
Amounts of different currencies are never summed; aggregations always key by
currency (conversion is a separate reporting concern — ADR-009).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Protocol, TypeVar

from stackup_api.domain.money import quantize
from stackup_api.models.enums import BillingType, CostStatus, Frequency

_WEEKS_PER_YEAR = Decimal(52)
_MONTHS_PER_YEAR = Decimal(12)
_MONTHS_PER_QUARTER = Decimal(3)

# Factor to convert one period's amount into a monthly-equivalent amount.
_MONTHLY_FACTOR: dict[Frequency, Decimal] = {
    Frequency.weekly: _WEEKS_PER_YEAR / _MONTHS_PER_YEAR,
    Frequency.monthly: Decimal(1),
    Frequency.quarterly: Decimal(1) / _MONTHS_PER_QUARTER,
    Frequency.yearly: Decimal(1) / _MONTHS_PER_YEAR,
}


class CostContribution(Protocol):
    amount: Decimal
    currency: str
    frequency: Frequency
    billing_type: BillingType
    status: CostStatus


def _contributes(billing_type: BillingType, status: CostStatus) -> bool:
    return status == CostStatus.active and billing_type != BillingType.one_time


def monthly_equivalent(
    amount: Decimal,
    frequency: Frequency,
    billing_type: BillingType = BillingType.fixed,
    status: CostStatus = CostStatus.active,
) -> Decimal:
    """Monthly-equivalent amount (quantized). 0 if it does not recur."""
    if not _contributes(billing_type, status):
        return quantize(Decimal(0))
    factor = _MONTHLY_FACTOR.get(frequency)
    if factor is None:  # custom
        return quantize(Decimal(0))
    return quantize(amount * factor)


def annualized_cost(
    amount: Decimal,
    frequency: Frequency,
    billing_type: BillingType = BillingType.fixed,
    status: CostStatus = CostStatus.active,
) -> Decimal:
    """Annualized amount (quantized) = monthly-equivalent * 12."""
    monthly = monthly_equivalent(amount, frequency, billing_type, status)
    return quantize(monthly * _MONTHS_PER_YEAR)


T = TypeVar("T", bound=CostContribution)


def total_monthly_by_currency(items: list[T]) -> dict[str, Decimal]:
    """Sum monthly-equivalent per currency (currencies never mixed)."""
    totals: dict[str, Decimal] = {}
    for item in items:
        m = monthly_equivalent(
            item.amount, item.frequency, item.billing_type, item.status
        )
        if m == 0:
            continue
        totals[item.currency] = quantize(totals.get(item.currency, Decimal(0)) + m)
    return totals


def group_monthly_by_currency(
    items: list[T], key: str
) -> dict[str, dict[str, Decimal]]:
    """Monthly-equivalent totals grouped by `getattr(item, key)`, per currency.

    Returns {group_value: {currency: monthly_total}}. The group value is
    stringified so callers get JSON-friendly keys.
    """
    grouped: dict[str, dict[str, Decimal]] = {}
    for item in items:
        m = monthly_equivalent(
            item.amount, item.frequency, item.billing_type, item.status
        )
        if m == 0:
            continue
        group_value = str(getattr(item, key))
        bucket = grouped.setdefault(group_value, {})
        bucket[item.currency] = quantize(bucket.get(item.currency, Decimal(0)) + m)
    return grouped


def percentage_change(previous: Decimal, current: Decimal) -> Decimal | None:
    """Percent change from previous to current, or None if previous is 0."""
    if previous == 0:
        return None
    return quantize((current - previous) / previous * Decimal(100))
