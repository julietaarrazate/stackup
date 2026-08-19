"""CostItem and CostHistory — the core of the product (ADR-009, docs §10)."""

from __future__ import annotations

import datetime
import uuid
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from stackup_api.core.db import Base
from stackup_api.models.base import TimestampMixin, uuid_pk
from stackup_api.models.enums import BillingType, Certainty, CostStatus, Frequency

# NUMERIC(14, 2) — money is Decimal end to end, never float (ADR-009).
Money = Numeric(14, 2, asdecimal=True)


class CostItem(TimestampMixin, Base):
    __tablename__ = "cost_item"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_cost_item_amount_positive"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspace.id", ondelete="CASCADE"), nullable=False, index=True
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("application.id", ondelete="CASCADE"), nullable=False, index=True
    )
    environment_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("environment.id", ondelete="SET NULL"), nullable=True, index=True
    )
    service_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("service.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    category: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)

    billing_type: Mapped[BillingType] = mapped_column(
        Enum(BillingType, native_enum=False, length=16), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Money, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    frequency: Mapped[Frequency] = mapped_column(
        Enum(Frequency, native_enum=False, length=16), nullable=False
    )
    status: Mapped[CostStatus] = mapped_column(
        Enum(CostStatus, native_enum=False, length=16),
        nullable=False,
        default=CostStatus.active,
        index=True,
    )
    certainty: Mapped[Certainty] = mapped_column(
        Enum(Certainty, native_enum=False, length=16),
        nullable=False,
        default=Certainty.confirmed,
        index=True,
    )

    start_date: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    history: Mapped[list[CostHistory]] = relationship(
        back_populates="cost_item",
        cascade="all, delete-orphan",
        order_by="CostHistory.effective_from",
    )


class CostHistory(Base):
    """Append-only ledger of a CostItem's price over time (docs §23)."""

    __tablename__ = "cost_history"

    id: Mapped[uuid.UUID] = uuid_pk()
    cost_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cost_item.id", ondelete="CASCADE"), nullable=False, index=True
    )
    amount: Mapped[Decimal] = mapped_column(Money, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    effective_from: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    cost_item: Mapped[CostItem] = relationship(back_populates="history")
