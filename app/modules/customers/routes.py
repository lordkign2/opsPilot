"""
OpsPilot — Customers Module: Routes.
"""

import uuid
from fastapi import APIRouter, Query

from app.modules.auth.dependencies import CurrentBusinessId
from app.modules.customers.dependencies import CustomerServiceDep
from app.modules.customers.schemas import CustomerCreate, CustomerResponse, CustomerUpdate
from app.shared.response import success_response, paginated_response

router = APIRouter(prefix="/customers", tags=["Customers"])

@router.post("/", response_model=None, status_code=201)
async def create_customer(
    payload: CustomerCreate,
    business_id: CurrentBusinessId,
    customer_service: CustomerServiceDep,
):
    """Create a new customer."""
    customer = await customer_service.create_customer(business_id, payload)
    return success_response(
        data=CustomerResponse.model_validate(customer).model_dump(mode="json"),
        message="Customer created successfully."
    )

@router.get("/", response_model=None)
async def list_customers(
    business_id: CurrentBusinessId,
    customer_service: CustomerServiceDep,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """List all customers for the business."""
    offset = (page - 1) * per_page
    customers = await customer_service.repo.get_by_business(
        business_id, offset=offset, limit=per_page
    )
    total = await customer_service.repo.count_by_business(business_id)
    
    data = [CustomerResponse.model_validate(c).model_dump(mode="json") for c in customers]
    return paginated_response(data=data, total=total, page=page, per_page=per_page)

@router.get("/search", response_model=None)
async def search_customers(
    query: str,
    business_id: CurrentBusinessId,
    customer_service: CustomerServiceDep,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """Search customers by name, phone, or email."""
    offset = (page - 1) * per_page
    customers, total = await customer_service.repo.search_customers(
        business_id=business_id,
        query=query,
        offset=offset,
        limit=per_page,
    )
    
    data = [CustomerResponse.model_validate(c).model_dump(mode="json") for c in customers]
    return paginated_response(data=data, total=total, page=page, per_page=per_page)

@router.get("/{customer_id}", response_model=None)
async def get_customer(
    customer_id: uuid.UUID,
    business_id: CurrentBusinessId,
    customer_service: CustomerServiceDep,
):
    """Get a specific customer."""
    customer = await customer_service.get_customer(business_id, customer_id)
    return success_response(data=CustomerResponse.model_validate(customer).model_dump(mode="json"))

@router.patch("/{customer_id}", response_model=None)
async def update_customer(
    customer_id: uuid.UUID,
    payload: CustomerUpdate,
    business_id: CurrentBusinessId,
    customer_service: CustomerServiceDep,
):
    """Update a specific customer."""
    customer = await customer_service.update_customer(business_id, customer_id, payload)
    return success_response(
        data=CustomerResponse.model_validate(customer).model_dump(mode="json"),
        message="Customer updated successfully."
    )
