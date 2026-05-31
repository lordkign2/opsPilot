"""
OpsPilot — Orders Module: Events.
"""

from app.core.events import Event, event_bus
from app.core.logging import get_logger

logger = get_logger("orders.events")


@event_bus.on("order.created")
async def handle_order_created(event: Event) -> None:
    """Handle order creation event."""
    logger.info("Order created hook triggered for order %s", event.payload.get("order_id"))


@event_bus.on("order.status_changed")
async def handle_order_status_changed(event: Event) -> None:
    """Handle order status update event."""
    logger.info(
        "Order %s status changed from %s to %s",
        event.payload.get("order_id"),
        event.payload.get("old_status"),
        event.payload.get("new_status"),
    )
