"""
OpsPilot — Orders Module: Service.
"""

import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import event_bus
from app.core.exceptions import NotFoundError, BadRequestError
from app.modules.orders.models import Order, OrderStatus
from app.modules.orders.repository import OrderRepository
from app.modules.orders.schemas import OrderCreate, OrderStatusUpdate
from app.modules.customers.repository import CustomerRepository

class OrderService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = OrderRepository(db)
        self.customer_repo = CustomerRepository(db)

    async def create_order(self, business_id: uuid.UUID, payload: OrderCreate) -> Order:
        """Create a new order for a customer."""
        customer = await self.customer_repo.get_one_by(id=payload.customer_id, business_id=business_id)
        if not customer:
            raise NotFoundError("Customer not found or does not belong to your business.")

        order = Order(
            business_id=business_id,
            customer_id=payload.customer_id,
            total_amount=payload.total_amount,
            notes=payload.notes,
            status=OrderStatus.PENDING,
        )
        order = await self.repo.create(order)
        await self.db.commit()

        await event_bus.emit(
            "order.created",
            {
                "order_id": str(order.id),
                "business_id": str(business_id),
                "customer_id": str(order.customer_id),
                "amount": float(order.total_amount),
            },
            source_module="orders",
        )
        return order

    async def get_order(self, business_id: uuid.UUID, order_id: uuid.UUID) -> Order:
        """Fetch an order ensuring it belongs to the correct business."""
        order = await self.repo.get_one_by(id=order_id, business_id=business_id)
        if not order:
            raise NotFoundError("Order not found.")
        return order

    async def update_status(self, business_id: uuid.UUID, order_id: uuid.UUID, payload: OrderStatusUpdate) -> Order:
        """Update the status of an order."""
        order = await self.get_order(business_id, order_id)
        
        if order.status == payload.status:
            return order

        old_status = order.status
        order.status = payload.status
        await self.repo.update(order)
        await self.db.commit()

        await event_bus.emit(
            "order.status_changed",
            {
                "order_id": str(order.id),
                "business_id": str(business_id),
                "old_status": old_status.value,
                "new_status": payload.status.value,
            },
            source_module="orders",
        )
        return order
