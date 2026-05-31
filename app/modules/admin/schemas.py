"""
OpsPilot — Super-Admin Module: Pydantic Validation Schemas.
"""

from __future__ import annotations

from pydantic import BaseModel

from app.modules.auth.models import UserRole


class MaintenanceRequest(BaseModel):
    """Payload to toggle system-wide maintenance mode."""

    is_active: bool


class RoleUpdateRequest(BaseModel):
    """Payload to promote or change a user's role."""

    role: UserRole


class BroadcastRequest(BaseModel):
    """Payload to dispatch a global websocket message."""

    message: str
    event_type: str = "system_alert"
