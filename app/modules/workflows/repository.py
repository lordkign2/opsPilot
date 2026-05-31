"""
OpsPilot — Workflow Automation Module: Repositories.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.workflows.models import Workflow, WorkflowExecutionLog
from app.shared.base_repository import BaseRepository


class WorkflowRepository(BaseRepository[Workflow]):
    """
    Handles data access for Workflow rule definitions.
    """

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Workflow, db)

    async def get_active_by_trigger(self, business_id: uuid.UUID, trigger_type: str) -> list[Workflow]:
        """
        Fetch active workflows scoped to a specific business and trigger event.

        Leverages the composite database index for sub-millisecond retrieval.
        """
        stmt = select(self.model).where(
            self.model.business_id == business_id,
            self.model.trigger_type == trigger_type,
            self.model.is_active == True,
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


class WorkflowExecutionLogRepository(BaseRepository[WorkflowExecutionLog]):
    """
    Handles data access for Workflow execution audit trails.
    """

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(WorkflowExecutionLog, db)
