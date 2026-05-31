"""
OpsPilot — Super-Admin Module: Repository Layer.
"""

from __future__ import annotations

import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import User
from app.modules.businesses.models import Business
from app.modules.workflows.models import Workflow


class AdminRepository:
    """Orchestrates global database overrides for platform operators."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Business Queries ─────────────────────────────────────

    async def get_business_by_id(self, business_id: uuid.UUID) -> Business | None:
        result = await self.db.execute(select(Business).where(Business.id == business_id))
        return result.scalar_one_or_none()

    async def list_businesses(self, limit: int, offset: int) -> tuple[list[Business], int]:
        total = await self.db.scalar(select(func.count()).select_from(Business)) or 0
        result = await self.db.execute(
            select(Business).order_by(Business.created_at.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all()), total

    async def hard_purge_business(self, business_id: uuid.UUID) -> None:
        # Cascade deletes: delete users belonging to this business to avoid FK failures
        await self.db.execute(delete(User).where(User.business_id == business_id))
        await self.db.execute(delete(Business).where(Business.id == business_id))
        await self.db.commit()

    # ── User Queries ─────────────────────────────────────────

    async def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def list_users(self, limit: int, offset: int) -> tuple[list[User], int]:
        total = await self.db.scalar(select(func.count()).select_from(User)) or 0
        result = await self.db.execute(select(User).order_by(User.created_at.desc()).limit(limit).offset(offset))
        return list(result.scalars().all()), total

    async def hard_purge_user(self, user_id: uuid.UUID) -> None:
        await self.db.execute(delete(User).where(User.id == user_id))
        await self.db.commit()

    # ── Workflow Queries ─────────────────────────────────────

    async def list_global_workflows(self, limit: int, offset: int) -> tuple[list[Workflow], int]:
        total = await self.db.scalar(select(func.count()).select_from(Workflow)) or 0
        result = await self.db.execute(
            select(Workflow).order_by(Workflow.created_at.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all()), total
