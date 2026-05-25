"""
OpsPilot — AI Module: Dependencies.
"""

from __future__ import annotations

from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.ai.service import AIService


def get_ai_service(db: AsyncSession = Depends(get_db)) -> AIService:
    return AIService(db)


AIServiceDep = Annotated[AIService, Depends(get_ai_service)]
