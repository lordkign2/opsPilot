"""
OpsPilot — Orders Module: Repository.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.base_repository import BaseRepository
from app.modules.orders.models import Order

class OrderRepository(BaseRepository[Order]):
    def __init__(self, db: AsyncSession):
        super().__init__(Order, db)
