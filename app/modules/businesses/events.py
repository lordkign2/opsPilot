"""
OpsPilot — Businesses Module: Internal Events.

Event handlers for business-related events.
"""

from __future__ import annotations

from app.core.events import Event, event_bus
from app.core.logging import get_logger

logger = get_logger("businesses.events")


@event_bus.on("business.updated")
async def on_business_updated(event: Event) -> None:
    """
    React to business updates.

    Future actions:
    - Invalidate cached business data
    - Notify team members of changes
    """
    logger.info(
        "Business %s updated: %s",
        event.payload.get("business_id"),
        event.payload.get("updated_fields"),
    )
