"""Report API schemas (Phase 5). Money is serialized as strings (ADR-009)."""

from __future__ import annotations

import datetime
import uuid

from pydantic import BaseModel

from stackup_api.schemas.cost import MoneyStr


class CurrencyTotal(BaseModel):
    currency: str
    monthly: MoneyStr
    annualized: MoneyStr


class GroupTotal(BaseModel):
    label: str
    currency: str
    monthly: MoneyStr
    annualized: MoneyStr


class CertaintyTotal(BaseModel):
    certainty: str
    currency: str
    monthly: MoneyStr


class RecentChange(BaseModel):
    cost_id: uuid.UUID
    cost_name: str
    amount: MoneyStr
    currency: str
    effective_from: datetime.date
    reason: str | None


class OverviewReport(BaseModel):
    total: list[CurrencyTotal]
    by_certainty: list[CertaintyTotal]
    by_category: list[GroupTotal]
    by_vendor: list[GroupTotal]
    by_application: list[GroupTotal]
    recent_changes: list[RecentChange]
    cost_item_count: int


class EvolutionPoint(BaseModel):
    period: str  # "YYYY-MM"
    currency: str
    monthly: MoneyStr


class EvolutionReport(BaseModel):
    points: list[EvolutionPoint]
