"""
OpsPilot — Notifications Module: Event Listeners.
"""

from __future__ import annotations

import uuid

from app.core.events import Event, event_bus
from app.core.logging import get_logger
from app.db.session import async_session_factory
from app.modules.notifications.schemas import NotificationCreate
from app.modules.notifications.service import NotificationService

logger = get_logger("notifications.events")


@event_bus.on("order.created")
async def handle_order_created(event: Event) -> None:
    """Handle order creation events by generating an in-app notification."""
    business_id_str = event.payload.get("business_id")
    order_id = event.payload.get("order_id")
    amount = event.payload.get("amount", 0.0)

    if not business_id_str:
        return

    business_id = uuid.UUID(business_id_str)

    async with async_session_factory() as db:
        service = NotificationService(db)
        payload = NotificationCreate(
            title="New Order Created",
            message=f"A new order (ID: {order_id}) has been created with a total amount of ₦{amount:,.2f}.",
            user_id=None,
        )
        await service.create_notification(business_id, payload)
        logger.info("Created notification for new order %s", order_id)


@event_bus.on("order.status_changed")
async def handle_order_status_changed(event: Event) -> None:
    """Handle order status change events by generating an in-app notification."""
    business_id_str = event.payload.get("business_id")
    order_id = event.payload.get("order_id")
    old_status = event.payload.get("old_status")
    new_status = event.payload.get("new_status")

    if not business_id_str:
        return

    business_id = uuid.UUID(business_id_str)

    async with async_session_factory() as db:
        service = NotificationService(db)
        payload = NotificationCreate(
            title="Order Status Updated",
            message=f"Order {order_id} status changed from '{old_status}' to '{new_status}'.",
            user_id=None,
        )
        await service.create_notification(business_id, payload)
        logger.info("Created notification for status update of order %s", order_id)


@event_bus.on("payment.successful")
async def handle_payment_successful(event: Event) -> None:
    """Handle successful payment events by generating an in-app notification."""
    # Note: payment.successful does not always include business_id explicitly in payload,
    # but we can look it up from the database or if it is supplied.
    # Wait, let's see if payments.successful includes order_id. Yes, event payload has:
    # {"payment_id": str(payment.id), "order_id": str(payment.order_id), "amount": float(payment.amount)}
    # Let's fetch the order to get the business_id.
    order_id_str = event.payload.get("order_id")
    amount = event.payload.get("amount", 0.0)

    if not order_id_str:
        return

    order_id = uuid.UUID(order_id_str)

    async with async_session_factory() as db:
        from app.modules.orders.repository import OrderRepository

        order_repo = OrderRepository(db)
        order = await order_repo.get_by_id(order_id)
        if not order:
            logger.error(
                "Order %s not found during payment notification generation.", order_id
            )
            return

        service = NotificationService(db)
        payload = NotificationCreate(
            title="Payment Received",
            message=f"Payment of ₦{amount:,.2f} has been verified for Order {order_id}.",
            user_id=None,
        )
        await service.create_notification(order.business_id, payload)
        logger.info("Created notification for successful payment of order %s", order_id)
