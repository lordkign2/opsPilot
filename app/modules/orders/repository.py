"""
OpsPilot — Orders Module: Repository.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.orders.models import Order
from app.shared.base_repository import BaseRepository


class OrderRepository(BaseRepository[Order]):
    def __init__(self, db: AsyncSession):
        super().__init__(Order, db)
