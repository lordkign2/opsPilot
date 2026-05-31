"""
OpsPilot — Orders Module: Routes.
"""

import uuid

from fastapi import APIRouter, Query

from app.modules.auth.dependencies import CurrentBusinessId
from app.modules.orders.dependencies import OrderServiceDep
from app.modules.orders.schemas import OrderCreate, OrderResponse, OrderStatusUpdate
from app.shared.response import paginated_response, success_response

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/", response_model=None, status_code=201)
async def create_order(
    payload: OrderCreate,
    business_id: CurrentBusinessId,
    order_service: OrderServiceDep,
):
    """Create a new order."""
    order = await order_service.create_order(business_id, payload)
    return success_response(
        data=OrderResponse.model_validate(order).model_dump(mode="json"),
        message="Order created successfully.",
    )


@router.get("/", response_model=None)
async def list_orders(
    business_id: CurrentBusinessId,
    order_service: OrderServiceDep,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """List all orders for the business."""
    offset = (page - 1) * per_page
    orders = await order_service.repo.get_by_business(business_id, offset=offset, limit=per_page)
    total = await order_service.repo.count_by_business(business_id)

    data = [OrderResponse.model_validate(o).model_dump(mode="json") for o in orders]
    return paginated_response(data=data, total=total, page=page, per_page=per_page)


@router.get("/{order_id}", response_model=None)
async def get_order(
    order_id: uuid.UUID,
    business_id: CurrentBusinessId,
    order_service: OrderServiceDep,
):
    """Get a specific order."""
    order = await order_service.get_order(business_id, order_id)
    return success_response(data=OrderResponse.model_validate(order).model_dump(mode="json"))


@router.patch("/{order_id}/status", response_model=None)
async def update_order_status(
    order_id: uuid.UUID,
    payload: OrderStatusUpdate,
    business_id: CurrentBusinessId,
    order_service: OrderServiceDep,
):
    """Update order status."""
    order = await order_service.update_status(business_id, order_id, payload)
    return success_response(
        data=OrderResponse.model_validate(order).model_dump(mode="json"),
        message="Order status updated.",
    )
