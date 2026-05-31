"""
OpsPilot — Audit Module: Service.
"""

from typing import Any

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
        payload: dict[str, Any] | None = None,
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

    async def get_logs(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[AuditLog], int]:
        """Retrieve global audit logs with pagination and total count."""
        from sqlalchemy import func, select

        count_query = select(func.count()).select_from(AuditLog)
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        logs = list(result.scalars().all())

        return logs, total
