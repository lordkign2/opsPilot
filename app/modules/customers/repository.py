"""
OpsPilot — Customers Module: Repository.
"""

import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.customers.models import Customer
from app.shared.base_repository import BaseRepository


class CustomerRepository(BaseRepository[Customer]):
    def __init__(self, db: AsyncSession):
        super().__init__(Customer, db)

    async def search_customers(
        self,
        business_id: uuid.UUID,
        query: str,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Customer], int]:
        """Search customers by name, phone, or email within a business."""
        stmt = select(Customer).where(Customer.business_id == business_id)

        if query:
            search_term = f"%{query}%"
            stmt = stmt.where(
                or_(
                    Customer.name.ilike(search_term),
                    Customer.phone.ilike(search_term),
                    Customer.email.ilike(search_term),
                )
            )

        # Count total matches using SQLAlchemy 2.0 pattern
        from sqlalchemy import func

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await self.db.scalar(count_stmt)

        stmt = stmt.order_by(Customer.created_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total or 0
