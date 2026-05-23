"""
OpsPilot — Audit Module: Models.

SOC2 compliant audit trails.
"""

import uuid
from typing import Any

from sqlalchemy import JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class AuditLog(Base):
    """Immutable audit log for all critical operations."""

    __tablename__ = "audit_logs"

    action: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    target_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    module: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Snapshot of the data or changes
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
