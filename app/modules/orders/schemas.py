"""
OpsPilot — Orders Module: Schemas.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.orders.models import OrderStatus


class OrderCreate(BaseModel):
    customer_id: uuid.UUID
    total_amount: float = Field(..., gt=0)
    notes: str | None = None


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


class OrderResponse(BaseModel):
    id: uuid.UUID
    business_id: uuid.UUID
    customer_id: uuid.UUID
    status: OrderStatus
    total_amount: float
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
