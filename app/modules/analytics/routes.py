"""
OpsPilot — Analytics Module: Routes.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.modules.auth.dependencies import CurrentBusinessId
from app.modules.analytics.dependencies import AnalyticsServiceDep
from app.shared.response import success_response

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview", response_model=None)
async def get_overview(
    business_id: CurrentBusinessId,
    analytics_service: AnalyticsServiceDep,
):
    """Retrieve operational dashboard overview analytics."""
    data = await analytics_service.get_overview(business_id)
    return success_response(data=data, message="Dashboard overview fetched successfully.")


@router.get("/revenue", response_model=None)
async def get_revenue_history(
    business_id: CurrentBusinessId,
    analytics_service: AnalyticsServiceDep,
    days: int = Query(30, ge=1, le=365),
):
    """Retrieve successful revenue trend statistics."""
    trend = await analytics_service.get_revenue_history(business_id, days=days)
    return success_response(
        data={"days": days, "trend": trend},
        message="Revenue history trends fetched successfully."
    )


@router.get("/orders", response_model=None)
async def get_order_distribution(
    business_id: CurrentBusinessId,
    analytics_service: AnalyticsServiceDep,
):
    """Retrieve order status distribution statistics."""
    data = await analytics_service.get_order_distribution(business_id)
    return success_response(data=data, message="Order status distribution fetched successfully.")
