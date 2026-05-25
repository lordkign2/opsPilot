"""
OpsPilot — Payments Module: Repository.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.payments.models import Payment
from app.shared.base_repository import BaseRepository


class PaymentRepository(BaseRepository[Payment]):
    def __init__(self, db: AsyncSession):
        super().__init__(Payment, db)
