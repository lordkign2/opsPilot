"""
OpsPilot — Super-Admin Module: Service Layer.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.admin.repository import AdminRepository
from app.modules.audit.service import AuditService
from app.modules.auth.models import UserRole
from app.websocket.manager import ws_manager

logger = logging.getLogger("opspilot.admin.service")


class AdminService:
    """Core business logic for super-administrative overrides and platform telemetry."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = AdminRepository(db)

    # ── System health & Telemetry ────────────────────────────

    async def get_system_health(self, redis: aioredis.Redis) -> dict[str, Any]:
        """Ping database/Redis, count active websockets, and collect telemetry."""
        # 1. Ping PostgreSQL
        db_ok = False
        try:
            await self.db.execute(select(1))
            db_ok = True
        except Exception as e:
            logger.error("DB Health check failed: %s", e)

        # 2. Ping Redis
        redis_ok = False
        try:
            ping_res = redis.ping()
            import inspect

            if inspect.isawaitable(ping_res):
                await ping_res
            redis_ok = True
        except Exception as e:
            logger.error("Redis Health check failed: %s", e)

        # 3. Active WebSocket Session count
        ws_connections_count = sum(len(conns) for conns in ws_manager._connections.values())

        # 4. Telemetry (Process statistics)
        memory_percent = 0.0
        cpu_percent = 0.0
        try:
            import psutil  # type: ignore

            memory_percent = psutil.virtual_memory().percent
            cpu_percent = psutil.cpu_percent(interval=None)
        except Exception:
            pass

        system_status = "healthy" if (db_ok and redis_ok) else "degraded"

        return {
            "status": system_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "services": {
                "postgres": "connected" if db_ok else "disconnected",
                "redis": "connected" if redis_ok else "disconnected",
            },
            "metrics": {
                "websocket_sessions": ws_connections_count,
                "memory_usage_percent": memory_percent,
                "cpu_usage_percent": cpu_percent,
            },
        }

    # ── System compliance Logs ───────────────────────────────

    async def get_system_logs(self, limit: int, offset: int) -> tuple[list[dict[str, Any]], int]:
        """Query SOC2 database compliance audit logs paginated."""
        audit_service = AuditService(self.db)
        logs, total = await audit_service.get_logs(limit=limit, offset=offset)

        logs_dump = []
        for log in logs:
            logs_dump.append(
                {
                    "id": str(log.id),
                    "action": log.action,
                    "module": log.module,
                    "actor_id": str(log.actor_id) if log.actor_id else None,
                    "target_id": log.target_id,
                    "payload": log.payload,
                    "ip_address": log.ip_address,
                    "user_agent": log.user_agent,
                    "created_at": log.created_at.isoformat() if log.created_at else None,
                }
            )
        return logs_dump, total

    # ── Maintenance Mode Control ─────────────────────────────

    async def toggle_maintenance_mode(self, redis: aioredis.Redis, is_active: bool) -> bool:
        """Toggle system maintenance mode in Redis."""
        value = "true" if is_active else "false"
        await redis.set("opspilot:maintenance_mode", value)
        logger.warning("Super-Admin toggled maintenance mode to %s", value)
        return is_active

    # ── Business overrides ───────────────────────────────────

    async def list_businesses(self, limit: int, offset: int) -> tuple[list[dict[str, Any]], int]:
        """List all businesses registered on the platform."""
        businesses, total = await self.repo.list_businesses(limit, offset)
        data = []
        for biz in businesses:
            data.append(
                {
                    "id": str(biz.id),
                    "name": biz.name,
                    "slug": biz.slug,
                    "industry": biz.industry,
                    "subscription_plan": biz.subscription_plan.value if biz.subscription_plan else "free",
                    "is_active": biz.is_active,
                    "deleted_at": biz.deleted_at.isoformat() if biz.deleted_at else None,
                    "created_at": biz.created_at.isoformat() if biz.created_at else None,
                }
            )
        return data, total

    async def toggle_business_status(self, business_id: uuid.UUID) -> dict[str, Any]:
        """Suspend or activate a business tenant."""
        biz = await self.repo.get_business_by_id(business_id)
        if not biz:
            raise NotFoundError("Business workspace not found.")

        biz.is_active = not biz.is_active
        await self.db.commit()

        logger.info("Super-Admin toggled business %s active to %s", biz.id, biz.is_active)
        return {"business_id": str(biz.id), "is_active": biz.is_active}

    async def soft_delete_business(self, business_id: uuid.UUID) -> dict[str, Any]:
        """Soft-deletes a business workspace workspace."""
        biz = await self.repo.get_business_by_id(business_id)
        if not biz:
            raise NotFoundError("Business workspace not found.")

        if biz.deleted_at is None:
            biz.deleted_at = datetime.now(timezone.utc)
            await self.db.commit()
            logger.warning("Super-Admin soft-deleted business %s", biz.id)

        assert biz.deleted_at is not None
        return {"business_id": str(biz.id), "deleted_at": biz.deleted_at.isoformat()}

    async def hard_purge_business(self, business_id: uuid.UUID) -> None:
        """GDPR Cascading hard-purge of a business."""
        biz = await self.repo.get_business_by_id(business_id)
        if not biz:
            raise NotFoundError("Business workspace not found.")

        await self.repo.hard_purge_business(business_id)

    # ── User overrides ───────────────────────────────────────

    async def list_users(self, limit: int, offset: int) -> tuple[list[dict[str, Any]], int]:
        """List all users globally."""
        users, total = await self.repo.list_users(limit, offset)
        data = []
        for u in users:
            data.append(
                {
                    "id": str(u.id),
                    "email": u.email,
                    "first_name": u.first_name,
                    "last_name": u.last_name,
                    "role": u.role.value if u.role else None,
                    "business_id": str(u.business_id) if u.business_id else None,
                    "is_active": u.is_active,
                    "deleted_at": u.deleted_at.isoformat() if u.deleted_at else None,
                    "created_at": u.created_at.isoformat() if u.created_at else None,
                }
            )
        return data, total

    async def update_user_role(self, user_id: uuid.UUID, role: UserRole) -> dict[str, Any]:
        """Promote or update a user's role."""
        user = await self.repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User account not found.")

        old_role = user.role.value
        user.role = role

        if role == UserRole.SUPER_ADMIN:
            user.business_id = None

        await self.db.commit()
        logger.warning("Super-Admin promoted user %s from %s to %s", user.id, old_role, user.role.value)

        return {
            "user_id": str(user.id),
            "role": user.role.value,
            "business_id": str(user.business_id) if user.business_id else None,
        }

    async def toggle_user_status(self, user_id: uuid.UUID) -> dict[str, Any]:
        """Suspend or activate a user account."""
        user = await self.repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User account not found.")

        user.is_active = not user.is_active
        await self.db.commit()

        logger.warning("Super-Admin toggled user %s active status to %s", user.id, user.is_active)
        return {"user_id": str(user.id), "is_active": user.is_active}

    async def soft_delete_user(self, user_id: uuid.UUID) -> dict[str, Any]:
        """Soft-deletes a user account."""
        user = await self.repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User account not found.")

        if user.deleted_at is None:
            user.deleted_at = datetime.now(timezone.utc)
            await self.db.commit()
            logger.warning("Super-Admin soft-deleted user %s", user.id)

        assert user.deleted_at is not None
        return {"user_id": str(user.id), "deleted_at": user.deleted_at.isoformat()}

    async def hard_purge_user(self, user_id: uuid.UUID) -> None:
        """GDPR absolute purge of a user account."""
        user = await self.repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User account not found.")

        await self.repo.hard_purge_user(user_id)

    # ── Workflow Inspection ──────────────────────────────────

    async def list_global_workflows(self, limit: int, offset: int) -> tuple[list[dict[str, Any]], int]:
        """Audit workflow rules globally."""
        rules, total = await self.repo.list_global_workflows(limit, offset)
        data = []
        for r in rules:
            data.append(
                {
                    "id": str(r.id),
                    "business_id": str(r.business_id),
                    "name": r.name,
                    "trigger_type": r.trigger_type,
                    "is_active": r.is_active,
                    "actions_count": len(r.actions) if r.actions else 0,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
            )
        return data, total

    # ── WebSocket Direct Controls ────────────────────────────

    async def get_websocket_sessions(self) -> list[dict[str, Any]]:
        """List active WebSocket connection metadata."""
        active_sessions = []
        for b_id, conns in ws_manager._connections.items():
            for conn in conns:
                client_ip = None
                try:
                    if conn.websocket and conn.websocket.client:
                        client_ip = conn.websocket.client.host
                except Exception:
                    pass

                active_sessions.append(
                    {
                        "business_id": b_id,
                        "user_id": str(conn.user_id),
                        "ip_address": client_ip,
                    }
                )
        return active_sessions

    async def broadcast_system_alert(self, message: str, event_type: str) -> int:
        """Dispatches a global WebSocket alert message."""
        logger.warning("Super-Admin dispatching global broadcast alert: %s", message)

        disconnected = []
        ws_message = {
            "event": event_type,
            "payload": {
                "message": message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }

        all_conns = []
        for conns in ws_manager._connections.values():
            all_conns.extend(conns)

        if not all_conns:
            return 0

        async def send(conn):
            success = await conn.send_json(ws_message)
            if not success:
                disconnected.append(conn)

        await asyncio.gather(*(send(conn) for conn in all_conns))

        # Cleanup stale connections
        for conn in disconnected:
            ws_manager.disconnect(conn)

        return len(all_conns) - len(disconnected)
