"""
OpsPilot — Payments Module: Dependencies.
"""

from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.payments.service import PaymentService

def get_payment_service(db: AsyncSession = Depends(get_db)) -> PaymentService:
    return PaymentService(db)

PaymentServiceDep = Annotated[PaymentService, Depends(get_payment_service)]
