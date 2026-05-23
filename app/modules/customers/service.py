"""
OpsPilot — Customers Module: Service.
"""

import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import event_bus
from app.core.exceptions import NotFoundError, ConflictError
from app.modules.customers.models import Customer
from app.modules.customers.repository import CustomerRepository
from app.modules.customers.schemas import CustomerCreate, CustomerUpdate

class CustomerService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = CustomerRepository(db)

    async def create_customer(self, business_id: uuid.UUID, payload: CustomerCreate) -> Customer:
        """Create a new customer for a business."""
        # Check if phone already exists for this business
        existing = await self.repo.get_one_by(business_id=business_id, phone=payload.phone)
        if existing:
            raise ConflictError("A customer with this phone number already exists.")

        customer = Customer(
            business_id=business_id,
            name=payload.name,
            phone=payload.phone,
            email=payload.email,
            notes=payload.notes,
        )
        customer = await self.repo.create(customer)
        await self.db.commit()

        await event_bus.emit(
            "customer.created",
            {
                "customer_id": str(customer.id),
                "business_id": str(business_id),
                "phone": customer.phone,
            },
            source_module="customers",
        )
        return customer

    async def get_customer(self, business_id: uuid.UUID, customer_id: uuid.UUID) -> Customer:
        """Fetch a customer ensuring they belong to the correct business."""
        customer = await self.repo.get_one_by(id=customer_id, business_id=business_id)
        if not customer:
            raise NotFoundError("Customer not found.")
        return customer

    async def update_customer(self, business_id: uuid.UUID, customer_id: uuid.UUID, payload: CustomerUpdate) -> Customer:
        """Update customer details."""
        customer = await self.get_customer(business_id, customer_id)
        
        if payload.phone and payload.phone != customer.phone:
            existing = await self.repo.get_one_by(business_id=business_id, phone=payload.phone)
            if existing:
                raise ConflictError("A customer with this phone number already exists.")

        update_data = payload.model_dump(exclude_unset=True)
        customer = await self.repo.update(customer, **update_data)
        await self.db.commit()

        return customer
