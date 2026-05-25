"""
OpsPilot — Businesses Module: Service Layer.

Business logic for business workspace management.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import event_bus
from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.logging import get_logger
from app.modules.auth.models import User, UserRole
from app.modules.businesses.models import Business
from app.modules.businesses.repository import BusinessRepository
from app.modules.businesses.schemas import UpdateBusinessRequest

logger = get_logger("businesses.service")


class BusinessService:
    """Business workspace management."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = BusinessRepository(db)

    async def get_business(self, business_id: uuid.UUID) -> Business:
        """Retrieve a business by ID, raising 404 if not found."""
        business = await self.repo.get_by_id(business_id)
        if not business:
            raise NotFoundError("Business not found.")
        return business

    async def get_current_business(self, user: User) -> Business:
        """
        Retrieve the business associated with the current user.
        """
        if not user.business_id:
            raise NotFoundError("No business associated with this account.")
        return await self.get_business(user.business_id)

    async def update_business(
        self,
        business_id: uuid.UUID,
        payload: UpdateBusinessRequest,
        user: User,
    ) -> Business:
        """
        Update business details.
        Only OWNER and MANAGER roles can update.
        """
        business = await self.get_business(business_id)

        # Authorization check
        if user.business_id != business.id:
            raise ForbiddenError("You do not belong to this business.")
        if user.role not in (UserRole.OWNER, UserRole.MANAGER):
            raise ForbiddenError(
                "Only owners and managers can update business details."
            )

        # Apply partial updates
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(business, field, value)

        business = await self.repo.update(business)
        await self.db.commit()

        await event_bus.emit(
            "business.updated",
            {
                "business_id": str(business.id),
                "updated_fields": list(update_data.keys()),
            },
            source_module="businesses",
        )

        logger.info("Business updated: %s", business.name)
        return business

    async def get_business_by_slug(self, slug: str) -> Business:
        """Retrieve a business by its slug."""
        business = await self.repo.get_by_slug(slug)
        if not business:
            raise NotFoundError("Business not found.")
        return business
