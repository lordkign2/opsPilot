"""
OpsPilot — AI Module: Repository.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai.models import AILog
from app.shared.base_repository import BaseRepository


class AILogRepository(BaseRepository[AILog]):
    def __init__(self, db: AsyncSession):
        super().__init__(AILog, db)
