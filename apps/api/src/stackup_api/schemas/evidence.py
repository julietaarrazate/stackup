"""Evidence and Expense API schemas."""

from __future__ import annotations

import datetime
import uuid

from pydantic import BaseModel, ConfigDict, Field

from stackup_api.models.enums import EvidenceType, ExpenseStatus
from stackup_api.schemas.cost import MoneyStr


class EvidenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    type: EvidenceType
    filename: str
    mime_type: str
    size: int
    created_at: datetime.datetime


class ExpenseCreate(BaseModel):
    cost_item_id: uuid.UUID
    amount: MoneyStr = Field(gt=0, max_digits=14, decimal_places=2)
    currency: str = Field(min_length=3, max_length=3)
    paid_at: datetime.date | None = None
    status: ExpenseStatus = ExpenseStatus.paid
    invoice_number: str | None = Field(default=None, max_length=120)
    evidence_id: uuid.UUID | None = None


class ExpenseUpdate(BaseModel):
    amount: MoneyStr | None = Field(default=None, gt=0, max_digits=14, decimal_places=2)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    paid_at: datetime.date | None = None
    status: ExpenseStatus | None = None
    invoice_number: str | None = Field(default=None, max_length=120)
    evidence_id: uuid.UUID | None = None


class ExpenseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    cost_item_id: uuid.UUID
    amount: MoneyStr
    currency: str
    paid_at: datetime.date | None
    status: ExpenseStatus
    invoice_number: str | None
    evidence_id: uuid.UUID | None
    created_at: datetime.datetime
    updated_at: datetime.datetime
