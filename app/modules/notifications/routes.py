"""
OpsPilot — Notifications Module: Routes.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query

from app.modules.auth.dependencies import CurrentBusinessId, CurrentUser
from app.modules.notifications.dependencies import NotificationServiceDep
from app.modules.notifications.schemas import NotificationResponse
from app.shared.response import paginated_response, success_response

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/", response_model=None)
async def list_notifications(
    business_id: CurrentBusinessId,
    user: CurrentUser,
    notification_service: NotificationServiceDep,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """List notifications for the current business workspace."""
    offset = (page - 1) * per_page
    notifications, total = await notification_service.get_notifications(
        business_id=business_id,
        user_id=user.id,
        offset=offset,
        limit=per_page,
    )

    data = [NotificationResponse.model_validate(n).model_dump(mode="json") for n in notifications]
    return paginated_response(data=data, total=total, page=page, per_page=per_page)


@router.patch("/{notification_id}/read", response_model=None)
async def mark_notification_read(
    notification_id: uuid.UUID,
    business_id: CurrentBusinessId,
    notification_service: NotificationServiceDep,
):
    """Mark a specific notification as read."""
    notification = await notification_service.mark_read(business_id, notification_id)
    return success_response(
        data=NotificationResponse.model_validate(notification).model_dump(mode="json"),
        message="Notification marked as read.",
    )


@router.post("/read-all", response_model=None)
async def mark_all_read(
    business_id: CurrentBusinessId,
    user: CurrentUser,
    notification_service: NotificationServiceDep,
):
    """Mark all notifications for current user as read."""
    count = await notification_service.mark_all_read(business_id, user_id=user.id)
    return success_response(data={"marked_count": count}, message="All notifications marked as read.")
