"""
OpsPilot — Audit Module: Event Listeners.

Listens to system-wide events and logs them for SOC2 compliance.
"""

from app.core.events import Event, event_bus
from app.core.logging import get_logger
from app.db.session import async_session_factory
from app.modules.audit.service import AuditService

logger = get_logger("audit.events")


@event_bus.on("user.logged_in")
@event_bus.on("user.registered")
async def handle_audit_events(event: Event) -> None:
    """Log critical user and system events to the audit trail."""
    async with async_session_factory() as db:
        audit_service = AuditService(db)
        await audit_service.log_action(
            action=event.event_type,
            module=event.source_module,
            actor_id=event.payload.get("user_id"),
            payload=event.payload,
        )
        logger.info("Audit log recorded for %s", event.event_type)
