"""
OpsPilot — Notifications Module: Schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class NotificationCreate(BaseModel):
    title: str = Field(..., max_length=200)
    message: str = Field(...)
    user_id: uuid.UUID | None = None


class NotificationResponse(BaseModel):
    id: uuid.UUID
    business_id: uuid.UUID
    user_id: uuid.UUID | None
    title: str
    message: str
    read: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
