"""
OpsPilot — Payments Module: ORM Models.
"""

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PaymentProvider(str, enum.Enum):
    PAYSTACK = "paystack"
    FLUTTERWAVE = "flutterwave"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class Payment(Base):
    """Represents a payment transaction for an order."""

    __tablename__ = "payments"

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[PaymentProvider] = mapped_column(
        Enum(PaymentProvider, name="payment_provider", create_constraint=True),
        nullable=False,
    )
    tx_ref: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status", create_constraint=True),
        default=PaymentStatus.PENDING,
        nullable=False,
        index=True,
    )
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    payment_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    order = relationship("Order", lazy="selectin")
