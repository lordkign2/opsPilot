"""
OpsPilot — AI Module: ORM Models.
"""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AILog(Base):
    """
    Audit log of all AI actions, requests, and outputs.
    Provides complete historical oversight for compliance and fine-tuning.
    """

    __tablename__ = "ai_logs"

    event_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=False)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Scoped to business workspace
    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationship
    business = relationship("Business", lazy="selectin")
