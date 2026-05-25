"""
OpsPilot — Auth Module: ORM Models.

Defines the User table with role-based access control.
"""

from __future__ import annotations

import enum
import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserRole(str, enum.Enum):
    """Roles within a business workspace."""

    OWNER = "owner"
    MANAGER = "manager"
    CASHIER = "cashier"
    SALES_REP = "sales_rep"


class User(Base):
    """
    Represents a platform user.

    Every user belongs to a business (multi-tenant, row-level isolation).
    The first user to register creates the business and becomes the OWNER.
    """

    __tablename__ = "users"

    # ── Profile ──────────────────────────────────────────────
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # ── Access Control ───────────────────────────────────────
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", create_constraint=True),
        default=UserRole.OWNER,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # ── Multi-Tenancy ────────────────────────────────────────
    business_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "businesses.id",
            ondelete="CASCADE",
            use_alter=True,
            name="fk_users_business_id_users",
        ),
        nullable=True,
        index=True,
    )

    # ── Relationships ────────────────────────────────────────
    business = relationship(
        "Business",
        back_populates="members",
        foreign_keys="[User.business_id]",
        lazy="selectin",
    )
