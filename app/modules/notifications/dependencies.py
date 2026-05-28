"""
OpsPilot — Notifications Module: Dependencies.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.notifications.service import NotificationService


def get_notification_service(db: AsyncSession = Depends(get_db)) -> NotificationService:
    return NotificationService(db)


NotificationServiceDep = Annotated[
    NotificationService, Depends(get_notification_service)
]
