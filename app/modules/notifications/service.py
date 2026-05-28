"""
OpsPilot — Notifications Module: Service.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.notifications.models import Notification
from app.modules.notifications.repository import NotificationRepository
from app.modules.notifications.schemas import NotificationCreate


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = NotificationRepository(db)

    async def create_notification(
        self, business_id: uuid.UUID, payload: NotificationCreate
    ) -> Notification:
        """Create a new notification."""
        notification = Notification(
            business_id=business_id,
            user_id=payload.user_id,
            title=payload.title,
            message=payload.message,
        )
        notification = await self.repo.create(notification)
        await self.db.commit()
        return notification

    async def get_notification(
        self, business_id: uuid.UUID, notification_id: uuid.UUID
    ) -> Notification:
        """Fetch a notification ensuring business-scoped security."""
        notification = await self.repo.get_one_by(
            id=notification_id, business_id=business_id
        )
        if not notification:
            raise NotFoundError("Notification not found.")
        return notification

    async def mark_read(
        self, business_id: uuid.UUID, notification_id: uuid.UUID
    ) -> Notification:
        """Mark a specific notification as read."""
        notification = await self.get_notification(business_id, notification_id)
        notification = await self.repo.update(notification, read=True)
        await self.db.commit()
        return notification

    async def mark_all_read(
        self, business_id: uuid.UUID, user_id: uuid.UUID | None = None
    ) -> int:
        """Mark all notifications as read."""
        count = await self.repo.mark_all_read(business_id, user_id)
        await self.db.commit()
        return count

    async def get_notifications(
        self,
        business_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Notification], int]:
        """Fetch a paginated list of scoped notifications."""
        return await self.repo.get_notifications_scoped(
            business_id=business_id,
            user_id=user_id,
            offset=offset,
            limit=limit,
        )
