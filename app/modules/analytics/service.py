"""
OpsPilot — Analytics Module: Service.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.customers.models import Customer
from app.modules.orders.models import Order, OrderStatus
from app.modules.payments.models import Payment, PaymentStatus


class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_overview(self, business_id: uuid.UUID) -> dict:
        """Get aggregate operational metrics for a business workspace."""
        # 1. Total Successful Payments (Revenue)
        revenue_stmt = (
            select(func.sum(Payment.amount))
            .join(Order, Payment.order_id == Order.id)
            .where(Order.business_id == business_id)
            .where(Payment.status == PaymentStatus.SUCCESS)
        )
        total_revenue = await self.db.scalar(revenue_stmt) or 0.0

        # 2. Total Customers Count
        customer_stmt = select(func.count(Customer.id)).where(
            Customer.business_id == business_id
        )
        total_customers = await self.db.scalar(customer_stmt) or 0

        # 3. Total Orders Count & Breakdown
        orders_stmt = select(func.count(Order.id)).where(
            Order.business_id == business_id
        )
        total_orders = await self.db.scalar(orders_stmt) or 0

        completed_orders_stmt = (
            select(func.count(Order.id))
            .where(Order.business_id == business_id)
            .where(Order.status == OrderStatus.COMPLETED)
        )
        completed_orders = await self.db.scalar(completed_orders_stmt) or 0

        # 4. Averages
        avg_order_value = 0.0
        if total_orders > 0:
            avg_stmt = select(func.avg(Order.total_amount)).where(
                Order.business_id == business_id
            )
            avg_order_value = float(await self.db.scalar(avg_stmt) or 0.0)

        conversion_rate = 0.0
        if total_orders > 0:
            conversion_rate = (completed_orders / total_orders) * 100

        return {
            "total_revenue": float(total_revenue),
            "total_customers": total_customers,
            "total_orders": total_orders,
            "completed_orders": completed_orders,
            "average_order_value": avg_order_value,
            "order_conversion_rate": conversion_rate,
        }

    async def get_revenue_history(
        self, business_id: uuid.UUID, days: int = 30
    ) -> list[dict]:
        """Fetch daily revenue trends for the specified past number of days."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        # Truncate timestamp to date and sum successful payments
        stmt = (
            select(
                func.date(Payment.created_at).label("date"),
                func.sum(Payment.amount).label("amount"),
            )
            .join(Order, Payment.order_id == Order.id)
            .where(Order.business_id == business_id)
            .where(Payment.status == PaymentStatus.SUCCESS)
            .where(Payment.created_at >= cutoff_date)
            .group_by(func.date(Payment.created_at))
            .order_by(func.date(Payment.created_at).asc())
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        # Build list of days so that even days with zero sales are represented nicely
        trend = []
        date_map = {row.date: float(row.amount) for row in rows}

        for i in range(days):
            d = (cutoff_date + timedelta(days=i + 1)).date()
            trend.append({"date": d.isoformat(), "revenue": date_map.get(d, 0.0)})

        return trend

    async def get_order_distribution(self, business_id: uuid.UUID) -> dict:
        """Get the absolute counts and percentages for each order status."""
        stmt = (
            select(Order.status, func.count(Order.id))
            .where(Order.business_id == business_id)
            .group_by(Order.status)
        )
        result = await self.db.execute(stmt)
        rows = result.all()

        breakdown = {status.value: 0 for status in OrderStatus}
        total = 0
        for status, count in rows:
            breakdown[status.value] = count
            total += count

        distribution = {}
        for status_val, count in breakdown.items():
            percentage = 0.0
            if total > 0:
                percentage = (count / total) * 100
            distribution[status_val] = {"count": count, "percentage": percentage}

        return {"total_orders": total, "distribution": distribution}
