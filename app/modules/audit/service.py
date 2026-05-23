"""
OpsPilot — Audit Module: Service.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.audit.models import AuditLog

class AuditService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_action(
        self,
        action: str,
        module: str,
        actor_id: str | None = None,
        target_id: str | None = None,
        payload: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        """Record an immutable audit event."""
        import uuid
        log_entry = AuditLog(
            action=action,
            module=module,
            actor_id=uuid.UUID(actor_id) if actor_id else None,
            target_id=target_id,
            payload=payload,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.add(log_entry)
        await self.db.commit()
        return log_entry
