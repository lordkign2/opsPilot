"""
OpsPilot — Customers Module: Events.
"""

from app.core.events import Event, event_bus
from app.core.logging import get_logger

logger = get_logger("customers.events")


@event_bus.on("customer.created")
async def handle_customer_created(event: Event) -> None:
    """Handle customer creation event."""
    logger.info(
        "Customer created hook triggered for customer %s",
        event.payload.get("customer_id"),
    )
    # In the future, this can trigger AI analysis or welcome messages
