"""
OpsPilot — Auth Module: Internal Events.

Event handlers that react to auth-related events.
"""

from __future__ import annotations

from app.core.events import Event, event_bus
from app.core.logging import get_logger

logger = get_logger("auth.events")


@event_bus.on("user.registered")
async def on_user_registered(event: Event) -> None:
    """
    React to a new user registration.

    Future actions:
    - Send welcome email
    - Create default business settings
    - Trigger onboarding workflow
    """
    logger.info(
        "New user registered: %s (business: %s)",
        event.payload.get("email"),
        event.payload.get("business_id"),
    )


@event_bus.on("user.logged_in")
async def on_user_logged_in(event: Event) -> None:
    """
    React to a user login.

    Future actions:
    - Update last_login timestamp
    - Log login analytics
    """
    logger.info("User logged in: %s", event.payload.get("email"))
