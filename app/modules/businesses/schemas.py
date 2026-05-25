"""
OpsPilot — Businesses Module: Pydantic Schemas.

Request/response validation for business endpoints.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.businesses.models import SubscriptionPlan

# ── Create / Update ──────────────────────────────────────────


class CreateBusinessRequest(BaseModel):
    """Payload to create a new business (standalone, not via registration)."""

    name: str = Field(..., min_length=2, max_length=200)
    description: str | None = Field(None, max_length=1000)
    industry: str | None = Field(None, max_length=100)
    email: str | None = None
    phone: str | None = Field(None, max_length=20)
    address: str | None = None


class UpdateBusinessRequest(BaseModel):
    """Partial update payload for a business."""

    name: str | None = Field(None, min_length=2, max_length=200)
    description: str | None = Field(None, max_length=1000)
    industry: str | None = Field(None, max_length=100)
    email: str | None = None
    phone: str | None = Field(None, max_length=20)
    address: str | None = None
    logo_url: str | None = None


# ── Responses ────────────────────────────────────────────────


class BusinessResponse(BaseModel):
    """Full business representation."""

    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    industry: str | None
    logo_url: str | None
    email: str | None
    phone: str | None
    address: str | None
    subscription_plan: SubscriptionPlan
    owner_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BusinessBriefResponse(BaseModel):
    """Minimal business info for embedding in other responses."""

    id: uuid.UUID
    name: str
    slug: str
    industry: str | None
    subscription_plan: SubscriptionPlan

    model_config = {"from_attributes": True}
