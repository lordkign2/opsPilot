"""
OpsPilot — Payments Module: Schemas.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.modules.payments.models import PaymentProvider, PaymentStatus


class PaymentInitialize(BaseModel):
    order_id: uuid.UUID
    provider: PaymentProvider = PaymentProvider.PAYSTACK


class PaymentWebhook(BaseModel):
    event: str
    data: dict


class PaymentResponse(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    provider: PaymentProvider
    tx_ref: str
    status: PaymentStatus
    amount: float
    payment_url: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
