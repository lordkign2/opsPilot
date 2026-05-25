"""
OpsPilot — Customers Module: Schemas.
"""

import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

# E.164 phone number pattern: + followed by 1 to 14 digits
E164_REGEX = re.compile(r"^\+[1-9]\d{1,14}$")


class CustomerCreate(BaseModel):
    name: str = Field(..., max_length=200)
    phone: str = Field(
        ..., description="Phone number in E.164 format (e.g., +2348012345678)"
    )
    email: str | None = None
    notes: str | None = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not E164_REGEX.match(v):
            raise ValueError(
                "Phone number must be in E.164 format including country code."
            )
        return v


class CustomerUpdate(BaseModel):
    name: str | None = Field(None, max_length=200)
    phone: str | None = Field(None, description="Phone number in E.164 format")
    email: str | None = None
    notes: str | None = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if v and not E164_REGEX.match(v):
            raise ValueError(
                "Phone number must be in E.164 format including country code."
            )
        return v


class CustomerResponse(BaseModel):
    id: uuid.UUID
    business_id: uuid.UUID
    name: str
    phone: str
    email: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
