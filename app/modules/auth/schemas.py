"""
OpsPilot — Auth Module: Pydantic Schemas.

Request/response validation models for authentication endpoints.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.modules.auth.models import UserRole


# ── Registration ─────────────────────────────────────────────

class RegisterRequest(BaseModel):
    """Payload for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: str | None = Field(None, max_length=20)
    business_name: str = Field(..., min_length=2, max_length=200)
    industry: str | None = Field(None, max_length=100)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


# ── Login ────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    """Payload for user login."""
    email: EmailStr
    password: str


# ── Tokens ───────────────────────────────────────────────────

class TokenResponse(BaseModel):
    """JWT token pair returned after authentication."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Payload for token refresh."""
    refresh_token: str


# ── User Responses ───────────────────────────────────────────

class UserResponse(BaseModel):
    """Public representation of a user."""
    id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    phone: str | None
    role: UserRole
    is_active: bool
    is_verified: bool
    business_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserBriefResponse(BaseModel):
    """Minimal user info for embedding in other responses."""
    id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    role: UserRole

    model_config = {"from_attributes": True}


# ── Password ─────────────────────────────────────────────────

class ChangePasswordRequest(BaseModel):
    """Payload for changing password."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v
