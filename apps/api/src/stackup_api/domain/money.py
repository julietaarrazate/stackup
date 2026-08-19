"""Money helpers (ADR-009).

All amounts are Decimal, never float. Quantization is to 2 decimal places
with banker's rounding. Currency is an ISO 4217 code carried alongside every
amount — conversion between currencies is a reporting concern (ExchangeRate,
later), never something that overwrites a stored amount.
"""

from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal

CENTS = Decimal("0.01")


def quantize(amount: Decimal) -> Decimal:
    """Round to 2 decimal places (half-to-even)."""
    return amount.quantize(CENTS, rounding=ROUND_HALF_EVEN)


def is_positive(amount: Decimal) -> bool:
    return amount > Decimal(0)
