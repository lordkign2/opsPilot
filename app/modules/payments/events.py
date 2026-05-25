"""
OpsPilot — Payments Module: Events.
"""

from app.core.events import Event, event_bus
from app.core.logging import get_logger

logger = get_logger("payments.events")


@event_bus.on("payment.initialized")
async def handle_payment_initialized(event: Event) -> None:
    logger.info(
        "Payment initialized for order %s (Tx: %s)",
        event.payload.get("order_id"),
        event.payload.get("tx_ref"),
    )


@event_bus.on("payment.successful")
async def handle_payment_successful(event: Event) -> None:
    logger.info(
        "Payment successful for order %s. Amount: %s",
        event.payload.get("order_id"),
        event.payload.get("amount"),
    )
