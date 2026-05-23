"""
OpsPilot — Businesses Module: Repository Layer.

Database access abstraction for Business entities.
Inherits from BaseRepository to avoid boilerplate.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.businesses.models import Business
from app.shared.base_repository import BaseRepository


class BusinessRepository(BaseRepository[Business]):
    """Data access layer for Business records."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Business, db)

    async def get_by_slug(self, slug: str) -> Business | None:
        """Fetch a business by its unique slug."""
        return await self.get_one_by(slug=slug)

    async def slug_exists(self, slug: str) -> bool:
        """Check if a slug is already taken."""
        return await self.exists(slug=slug)

    # Note: get_by_id, create, update, delete are inherited from BaseRepository.
    # get_many (as list_all) and count are also inherited.
