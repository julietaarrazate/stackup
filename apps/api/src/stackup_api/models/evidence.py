"""Evidence and Expense models (docs §10, ADR-006)."""

from __future__ import annotations

import datetime
import uuid
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from stackup_api.core.db import Base
from stackup_api.models.base import TimestampMixin, uuid_pk
from stackup_api.models.cost import Money
from stackup_api.models.enums import EvidenceType, ExpenseStatus


class Evidence(Base):
    """Metadata for a stored file. The bytes live in object storage; only a
    random `storage_key` links here — never the user-supplied filename."""

    __tablename__ = "evidence"

    id: Mapped[uuid.UUID] = uuid_pk()
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspace.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[EvidenceType] = mapped_column(
        Enum(EvidenceType, native_enum=False, length=16), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    mime_type: Mapped[str] = mapped_column(String(120), nullable=False)
    size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Expense(TimestampMixin, Base):
    """A real payment against a CostItem (distinct from the cost itself)."""

    __tablename__ = "expense"
    __table_args__ = (CheckConstraint("amount > 0", name="ck_expense_amount_positive"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspace.id", ondelete="CASCADE"), nullable=False, index=True
    )
    cost_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cost_item.id", ondelete="CASCADE"), nullable=False, index=True
    )
    amount: Mapped[Decimal] = mapped_column(Money, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    paid_at: Mapped[datetime.date | None] = mapped_column(nullable=True)
    status: Mapped[ExpenseStatus] = mapped_column(
        Enum(ExpenseStatus, native_enum=False, length=16),
        nullable=False,
        default=ExpenseStatus.paid,
        index=True,
    )
    invoice_number: Mapped[str | None] = mapped_column(String(120), nullable=True)
    evidence_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("evidence.id", ondelete="SET NULL"), nullable=True, index=True
    )
