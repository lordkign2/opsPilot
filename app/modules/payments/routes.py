"""
OpsPilot — Payments Module: Routes.
"""

from fastapi import APIRouter

from app.modules.auth.dependencies import CurrentBusinessId
from app.modules.payments.dependencies import PaymentServiceDep
from app.modules.payments.schemas import (
    PaymentInitialize,
    PaymentResponse,
    PaymentWebhook,
)
from app.shared.response import success_response

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/", response_model=None, status_code=201)
async def initialize_payment(
    payload: PaymentInitialize,
    business_id: CurrentBusinessId,
    payment_service: PaymentServiceDep,
):
    """Initialize a new payment for an order."""
    payment = await payment_service.initialize_payment(business_id, payload)
    return success_response(
        data=PaymentResponse.model_validate(payment).model_dump(mode="json"),
        message="Payment initialized.",
    )


@router.get("/verify/{tx_ref}", response_model=None)
async def verify_payment(
    tx_ref: str,
    payment_service: PaymentServiceDep,
):
    """Verify payment status via reference."""
    payment = await payment_service.verify_payment(tx_ref)
    return success_response(
        data=PaymentResponse.model_validate(payment).model_dump(mode="json"),
        message="Payment verification complete.",
    )


@router.post("/webhook", response_model=None)
async def payment_webhook(
    payload: PaymentWebhook,
    payment_service: PaymentServiceDep,
):
    """Handle provider webhooks (unauthenticated public endpoint)."""
    # Note: In production, verify provider webhook signature here.
    await payment_service.handle_webhook(payload.event, payload.data)
    return success_response(message="Webhook processed.")
