"""
OpsPilot — Notifications Module: Repository.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.notifications.models import Notification
from app.shared.base_repository import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    def __init__(self, db: AsyncSession):
        super().__init__(Notification, db)

    async def mark_all_read(
        self, business_id: uuid.UUID, user_id: uuid.UUID | None = None
    ) -> int:
        """Mark all notifications as read for a business (and user optionally)."""
        stmt = (
            update(Notification)
            .where(Notification.business_id == business_id)
            .where(Notification.read == False)
        )
        if user_id:
            stmt = stmt.where(Notification.user_id == user_id)

        stmt = stmt.values(read=True)
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount

    async def get_notifications_scoped(
        self,
        business_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Notification], int]:
        """Fetch notifications that are either workspace-wide (user_id is Null) or targeted to this user."""
        from sqlalchemy import func, or_

        stmt = select(Notification).where(Notification.business_id == business_id)
        if user_id:
            stmt = stmt.where(
                or_(Notification.user_id == user_id, Notification.user_id.is_(None))
            )
        else:
            stmt = stmt.where(Notification.user_id.is_(None))

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await self.db.scalar(count_stmt) or 0

        # Paginated results
        stmt = stmt.order_by(Notification.created_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total
