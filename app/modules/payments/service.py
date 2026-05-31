"""
OpsPilot — Payments Module: Service.
"""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import event_bus
from app.core.exceptions import NotFoundError
from app.modules.orders.models import OrderStatus
from app.modules.orders.repository import OrderRepository
from app.modules.payments.models import Payment, PaymentStatus
from app.modules.payments.repository import PaymentRepository
from app.modules.payments.schemas import PaymentInitialize


class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = PaymentRepository(db)
        self.order_repo = OrderRepository(db)

    async def initialize_payment(self, business_id: uuid.UUID, payload: PaymentInitialize) -> Payment:
        """Stub implementation to initialize a payment."""
        order = await self.order_repo.get_one_by(id=payload.order_id, business_id=business_id)
        if not order:
            raise NotFoundError("Order not found or does not belong to your business.")

        # In a real implementation, we would call Paystack API here to get an authorization URL.
        # For now, we simulate success and return a mock URL.
        import random
        import string

        tx_ref = "tx-" + "".join(random.choices(string.ascii_letters + string.digits, k=12))

        payment = Payment(
            order_id=payload.order_id,
            provider=payload.provider,
            tx_ref=tx_ref,
            status=PaymentStatus.PENDING,
            amount=order.total_amount,
            payment_url=f"https://checkout.paystack.com/mock-{tx_ref}",
        )
        payment = await self.repo.create(payment)
        await self.db.commit()

        await event_bus.emit(
            "payment.initialized",
            {
                "payment_id": str(payment.id),
                "order_id": str(payment.order_id),
                "tx_ref": payment.tx_ref,
            },
            source_module="payments",
        )
        return payment

    async def verify_payment(self, tx_ref: str) -> Payment:
        """Verify a payment status. Can be called by frontend after redirect."""
        payment = await self.repo.get_one_by(tx_ref=tx_ref)
        if not payment:
            raise NotFoundError("Transaction reference not found.")

        # Simulate verification (in reality, check with Paystack API)
        if payment.status == PaymentStatus.PENDING:
            payment.status = PaymentStatus.SUCCESS
            await self.repo.update(payment)

            # Update order status
            order = await self.order_repo.get_by_id(payment.order_id)
            if order:
                order.status = OrderStatus.COMPLETED
                await self.order_repo.update(order)

            await self.db.commit()

            await event_bus.emit(
                "payment.successful",
                {
                    "payment_id": str(payment.id),
                    "order_id": str(payment.order_id),
                    "amount": float(payment.amount),
                },
                source_module="payments",
            )

        return payment

    async def handle_webhook(self, event: str, data: dict[str, Any]) -> None:
        """Handle incoming webhooks from payment provider."""
        # Stub logic
        tx_ref = data.get("reference")
        if event == "charge.success" and tx_ref:
            await self.verify_payment(tx_ref)
