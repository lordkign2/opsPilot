"""
OpsPilot — Auth Module: Repository Layer.

Database access abstraction for User entities.
Inherits from BaseRepository to avoid boilerplate.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import User
from app.shared.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """Data access layer for User records."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> User | None:
        """Fetch a user by email address (case-insensitive)."""
        result = await self.db.execute(select(User).where(func.lower(User.email) == email.lower()))
        return result.scalar_one_or_none()

    async def email_exists(self, email: str) -> bool:
        """Check if an email is already registered."""
        result = await self.db.execute(
            select(func.count()).select_from(User).where(func.lower(User.email) == email.lower())
        )
        return (result.scalar() or 0) > 0

    # Note: get_by_id, create, update, delete are inherited from BaseRepository.
    # get_by_business and count_by_business are also inherited.
