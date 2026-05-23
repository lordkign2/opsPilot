"""
OpsPilot — Businesses Module: FastAPI Dependencies.

Provides business-scoped dependency injection.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.auth.dependencies import CurrentUser
from app.modules.auth.models import User
from app.modules.businesses.models import Business
from app.modules.businesses.service import BusinessService


async def get_business_service(
    db: AsyncSession = Depends(get_db),
) -> BusinessService:
    """Build a BusinessService with request-scoped DB session."""
    return BusinessService(db=db)


async def get_current_business(
    current_user: CurrentUser,
    service: BusinessService = Depends(get_business_service),
) -> Business:
    """Resolve the business associated with the current user."""
    return await service.get_current_business(current_user)


# ── Type Aliases ─────────────────────────────────────────────
BusinessServiceDep = Annotated[BusinessService, Depends(get_business_service)]
CurrentBusiness = Annotated[Business, Depends(get_current_business)]
