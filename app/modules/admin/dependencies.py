"""
OpsPilot — Super-Admin Module: FastAPI Dependencies.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.admin.service import AdminService


async def get_admin_service(
    db: AsyncSession = Depends(get_db),
) -> AdminService:
    """Build an AdminService instance with request-scoped dependencies."""
    return AdminService(db=db)


AdminServiceDep = Annotated[AdminService, Depends(get_admin_service)]
