"""CostItem and CostHistory API schemas (ADR-009).

Money is a Decimal on input (accepts string or number) and serialized as a
STRING on output, so amounts never round-trip through a float on the wire.
"""

from __future__ import annotations

import datetime
import uuid
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer, model_validator

from stackup_api.models.enums import BillingType, Certainty, CostStatus, Frequency

# Decimal in, string out.
MoneyStr = Annotated[Decimal, PlainSerializer(str, return_type=str, when_used="json")]


class CostItemCreate(BaseModel):
    application_id: uuid.UUID
    service_id: uuid.UUID
    environment_id: uuid.UUID | None = None
    name: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    category: str | None = Field(default=None, max_length=80)
    billing_type: BillingType = BillingType.fixed
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    currency: str = Field(min_length=3, max_length=3)
    frequency: Frequency = Frequency.monthly
    certainty: Certainty = Certainty.confirmed
    start_date: datetime.date | None = None
    end_date: datetime.date | None = None
    notes: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def _dates_coherent(self) -> CostItemCreate:
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError("end_date cannot be before start_date")
        return self


class CostItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    category: str | None = Field(default=None, max_length=80)
    billing_type: BillingType | None = None
    amount: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    frequency: Frequency | None = None
    status: CostStatus | None = None
    certainty: Certainty | None = None
    environment_id: uuid.UUID | None = None
    start_date: datetime.date | None = None
    end_date: datetime.date | None = None
    notes: str | None = Field(default=None, max_length=2000)
    # Optional note explaining an amount/currency change, stored on CostHistory.
    change_reason: str | None = Field(default=None, max_length=500)


class CostItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    application_id: uuid.UUID
    environment_id: uuid.UUID | None
    service_id: uuid.UUID
    name: str
    description: str | None
    category: str | None
    billing_type: BillingType
    amount: MoneyStr
    currency: str
    frequency: Frequency
    status: CostStatus
    certainty: Certainty
    start_date: datetime.date | None
    end_date: datetime.date | None
    notes: str | None
    # Computed by the Cost Engine (not stored).
    monthly_equivalent: MoneyStr
    annualized_cost: MoneyStr
    created_at: datetime.datetime
    updated_at: datetime.datetime


class CostHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    cost_item_id: uuid.UUID
    amount: MoneyStr
    currency: str
    effective_from: datetime.date
    effective_to: datetime.date | None
    reason: str | None
    created_at: datetime.datetime
