"""
OpsPilot — Businesses Module: ORM Models.

Defines the Business (tenant) entity.
"""

from __future__ import annotations

import datetime
import enum
import uuid

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SubscriptionPlan(str, enum.Enum):
    """Available subscription tiers."""

    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class Business(Base):
    """
    Represents a business workspace (tenant).

    All data in the platform is scoped to a business via `business_id` FKs.
    """

    __tablename__ = "businesses"

    # ── Identity ─────────────────────────────────────────────
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(250), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # ── Contact ──────────────────────────────────────────────
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Subscription ─────────────────────────────────────────
    subscription_plan: Mapped[SubscriptionPlan] = mapped_column(
        Enum(SubscriptionPlan, name="subscription_plan", create_constraint=True),
        default=SubscriptionPlan.FREE,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    deleted_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # ── Ownership ────────────────────────────────────────────
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
            use_alter=True,
            name="fk_businesses_owner_id_businesses",
        ),
        nullable=True,
    )

    # ── Relationships ────────────────────────────────────────
    members = relationship(
        "User",
        back_populates="business",
        foreign_keys="User.business_id",
        lazy="selectin",
    )
