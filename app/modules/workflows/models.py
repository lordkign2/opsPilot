"""
OpsPilot — Workflow Automation Module: ORM Models.
"""

from __future__ import annotations

import enum
import uuid
from typing import Any

from sqlalchemy import Boolean, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class LogDepth(str, enum.Enum):
    """Controls the write logging density of rules executions to avoid DB write exhaustion."""
    ALL = "all"
    ERRORS_ONLY = "errors_only"
    NONE = "none"


class Workflow(Base):
    """
    Represents a multi-tenant business workflow automation rule.
    """

    __tablename__ = "workflows"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    trigger_type: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., 'order.created'
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Store conditions and actions as binary JSONB for fast JSON operations
    conditions: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)
    actions: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)
    
    log_depth: Mapped[str] = mapped_column(String(20), default=LogDepth.ALL.value, nullable=False)

    # Scoped to business
    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    business = relationship("Business", lazy="selectin")
    executions = relationship("WorkflowExecutionLog", back_populates="workflow", cascade="all, delete-orphan")

    # Composite index for sub-millisecond database lookup fallbacks
    __table_args__ = (
        Index("ix_workflow_lookup", "business_id", "trigger_type", "is_active"),
    )


class WorkflowExecutionLog(Base):
    """
    Audits execution runs of automations.
    """

    __tablename__ = "workflow_execution_logs"

    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g., 'success', 'failed', 'skipped'
    error_message: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    workflow = relationship("Workflow", back_populates="executions", lazy="selectin")
