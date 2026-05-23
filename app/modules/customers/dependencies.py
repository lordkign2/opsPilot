"""
OpsPilot — Customers Module: Dependencies.
"""

from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.customers.service import CustomerService

def get_customer_service(db: AsyncSession = Depends(get_db)) -> CustomerService:
    return CustomerService(db)

CustomerServiceDep = Annotated[CustomerService, Depends(get_customer_service)]
