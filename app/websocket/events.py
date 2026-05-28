"""
OpsPilot — Event Bridge.

Bridges the local internal event_bus events directly into the Redis Pub/Sub gateway.
"""

from __future__ import annotations

import logging
from typing import Any

from app.core.events import Event, event_bus
from app.websocket.broadcaster import publish_event

logger = logging.getLogger("opspilot.websocket.events")


async def forward_event_to_websockets(event: Event) -> None:
    """Helper to forward any standard local Event to the WebSocket gateway."""
    payload = event.payload
    # Extract business_id from payload (most business events have it)
    business_id = payload.get("business_id")
    if not business_id:
        logger.debug("Skipped forwarding event '%s' - missing business_id in payload.", event.event_type)
        return

    # Forward to Redis fanout broadcaster
    await publish_event(
        business_id=str(business_id),
        event_type=event.event_type,
        payload=payload,
    )


# ── Register Bridge Handlers ──────────────────────────────────

# List of events we want to fanout in real-time to active UI clients
WS_FORWARDABLE_EVENTS = [
    "order.created",
    "order.updated",
    "payment.success",
    "payment.failed",
    "notification.created",
    "analytics.updated",
    "ai.insight.generated",
    "ai.response.chunk",
]


def register_ws_event_bridge() -> None:
    """Registers WebSocket bridge listeners on the local core event_bus."""
    for event_type in WS_FORWARDABLE_EVENTS:
        event_bus.subscribe(event_type, forward_event_to_websockets)
        logger.debug("Bridged event '%s' to WebSocket fanout listener", event_type)
