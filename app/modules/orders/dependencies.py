"""
OpsPilot — Orders Module: Dependencies.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.orders.service import OrderService


def get_order_service(db: AsyncSession = Depends(get_db)) -> OrderService:
    return OrderService(db)


OrderServiceDep = Annotated[OrderService, Depends(get_order_service)]
