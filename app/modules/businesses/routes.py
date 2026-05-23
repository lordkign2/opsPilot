"""
OpsPilot — Businesses Module: HTTP Routes.

Business workspace management endpoints.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from app.modules.auth.dependencies import CurrentUser, require_role
from app.modules.auth.models import UserRole
from app.modules.businesses.dependencies import (
    BusinessServiceDep,
    CurrentBusiness,
)
from app.modules.businesses.schemas import (
    BusinessResponse,
    UpdateBusinessRequest,
)
from app.shared.response import success_response

router = APIRouter(prefix="/businesses", tags=["Businesses"])


# ── GET /current ─────────────────────────────────────────────

@router.get(
    "/current",
    response_model=None,
    summary="Get current user's business",
)
async def get_current_business(current_business: CurrentBusiness):
    """Return the business associated with the authenticated user."""
    return success_response(
        data=BusinessResponse.model_validate(current_business).model_dump(mode="json"),
    )


# ── GET /{business_id} ──────────────────────────────────────

@router.get(
    "/{business_id}",
    response_model=None,
    summary="Get business by ID",
)
async def get_business(
    business_id: uuid.UUID,
    service: BusinessServiceDep,
    current_user: CurrentUser,
):
    """Retrieve a specific business by its ID."""
    business = await service.get_business(business_id)
    return success_response(
        data=BusinessResponse.model_validate(business).model_dump(mode="json"),
    )


# ── PATCH /{business_id} ────────────────────────────────────

@router.patch(
    "/{business_id}",
    response_model=None,
    summary="Update business details",
)
async def update_business(
    business_id: uuid.UUID,
    payload: UpdateBusinessRequest,
    service: BusinessServiceDep,
    current_user: CurrentUser,
):
    """
    Update a business workspace.
    Requires OWNER or MANAGER role.
    """
    business = await service.update_business(business_id, payload, current_user)
    return success_response(
        data=BusinessResponse.model_validate(business).model_dump(mode="json"),
        message="Business updated successfully.",
    )


# ── GET /slug/{slug} ────────────────────────────────────────

@router.get(
    "/slug/{slug}",
    response_model=None,
    summary="Get business by slug",
)
async def get_business_by_slug(
    slug: str,
    service: BusinessServiceDep,
):
    """Retrieve a business by its URL slug (public endpoint)."""
    business = await service.get_business_by_slug(slug)
    return success_response(
        data=BusinessResponse.model_validate(business).model_dump(mode="json"),
    )
