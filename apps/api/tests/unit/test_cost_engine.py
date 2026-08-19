"""Cost Engine unit + invariant tests (docs sections 12, 32)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

import pytest

from stackup_api.domain.cost_engine import (
    annualized_cost,
    group_monthly_by_currency,
    monthly_equivalent,
    percentage_change,
    total_monthly_by_currency,
)
from stackup_api.models.enums import BillingType, CostStatus, Frequency

D = Decimal


@dataclass
class Cost:
    amount: Decimal
    currency: str
    frequency: Frequency
    billing_type: BillingType = BillingType.fixed
    status: CostStatus = CostStatus.active
    category: str = ""


# --- monthly_equivalent -------------------------------------------------


def test_monthly_of_monthly_is_itself() -> None:
    assert monthly_equivalent(D("20.00"), Frequency.monthly) == D("20.00")


def test_monthly_of_yearly_is_amount_over_12() -> None:
    assert monthly_equivalent(D("120.00"), Frequency.yearly) == D("10.00")


def test_monthly_of_quarterly_is_amount_over_3() -> None:
    assert monthly_equivalent(D("30.00"), Frequency.quarterly) == D("10.00")


def test_monthly_of_weekly() -> None:
    # 10 * 52 / 12 = 43.333... -> 43.33
    assert monthly_equivalent(D("10.00"), Frequency.weekly) == D("43.33")


def test_one_time_does_not_recur() -> None:
    assert monthly_equivalent(
        D("500.00"), Frequency.monthly, BillingType.one_time
    ) == D("0.00")


def test_custom_frequency_not_normalized() -> None:
    assert monthly_equivalent(D("99.00"), Frequency.custom) == D("0.00")


@pytest.mark.parametrize("status", [CostStatus.paused, CostStatus.ended])
def test_inactive_costs_contribute_zero(status: CostStatus) -> None:
    assert monthly_equivalent(
        D("20.00"), Frequency.monthly, BillingType.fixed, status
    ) == D("0.00")


# --- annualized ---------------------------------------------------------


def test_annualized_of_yearly_is_amount() -> None:
    assert annualized_cost(D("120.00"), Frequency.yearly) == D("120.00")


def test_annualized_of_monthly_is_times_12() -> None:
    assert annualized_cost(D("20.00"), Frequency.monthly) == D("240.00")


# --- invariants (property-style) ---------------------------------------


@pytest.mark.parametrize(
    "amount", [D("0.01"), D("1.00"), D("19.99"), D("1234.56"), D("100000.00")]
)
def test_invariant_annualized_is_monthly_times_12(amount: Decimal) -> None:
    for freq in (
        Frequency.weekly,
        Frequency.monthly,
        Frequency.quarterly,
        Frequency.yearly,
    ):
        monthly = monthly_equivalent(amount, freq)
        assert annualized_cost(amount, freq) == (monthly * 12).quantize(D("0.01"))


@pytest.mark.parametrize("amount", [D("12.00"), D("120.00"), D("1200.00"), D("999.96")])
def test_invariant_yearly_monthly_equals_amount_over_12(amount: Decimal) -> None:
    assert monthly_equivalent(amount, Frequency.yearly) == (amount / 12).quantize(
        D("0.01")
    )


def test_no_float_leakage() -> None:
    result = monthly_equivalent(D("10.00"), Frequency.weekly)
    assert isinstance(result, Decimal)


# --- aggregations -------------------------------------------------------


def test_total_monthly_by_currency_keeps_currencies_separate() -> None:
    items = [
        Cost(D("20.00"), "USD", Frequency.monthly),
        Cost(D("120.00"), "USD", Frequency.yearly),  # -> 10/mo
        Cost(D("3000.00"), "ARS", Frequency.monthly),
        Cost(D("500.00"), "USD", Frequency.monthly, BillingType.one_time),  # 0
    ]
    totals = total_monthly_by_currency(items)
    assert totals == {"USD": D("30.00"), "ARS": D("3000.00")}


def test_group_monthly_by_currency() -> None:
    items = [
        Cost(D("20.00"), "USD", Frequency.monthly, category="infrastructure"),
        Cost(D("10.00"), "USD", Frequency.monthly, category="software"),
    ]
    grouped = group_monthly_by_currency(items, "category")
    assert grouped["infrastructure"]["USD"] == D("20.00")
    assert grouped["software"]["USD"] == D("10.00")


# --- percentage change --------------------------------------------------


def test_percentage_change() -> None:
    assert percentage_change(D("20.00"), D("25.00")) == D("25.00")


def test_percentage_change_from_zero_is_none() -> None:
    assert percentage_change(D("0"), D("25.00")) is None
