"""
OpsPilot — Paystack Payments Gateway Integration.
"""

from __future__ import annotations

import hashlib
import hmac
from typing import Any
import uuid

import httpx
from fastapi import APIRouter, Header, Request, Response

from app.core.config import get_settings
from app.core.events import event_bus
from app.core.logging import get_logger

logger = get_logger("integrations.payments.paystack")

router = APIRouter(prefix="/integrations/payments/paystack", tags=["Paystack Payments Integration"])


async def initialize_paystack_transaction(
    email: str, amount_kobo: int, reference: str, callback_url: str | None = None
) -> str | None:
    """
    Initializes a new checkout payment transaction with Paystack.
    Returns the secure authorization checkout URL.
    
    If integration credentials are not configured, falls back to a sandbox mockup checkout url.
    """
    settings = get_settings()
    secret_key = settings.PAYSTACK_SECRET_KEY

    # 1. Fallback Mock Checkout
    if not secret_key:
        logger.info(
            "[MOCK PAYSTACK INITIALIZE] Reference: %s | Amount: ₦%.2f | Email: %s",
            reference,
            amount_kobo / 100.0,
            email,
        )
        return f"https://checkout.paystack.com/mock-{uuid.uuid4()}"

    # 2. Production Call
    url = "https://api.paystack.co/transaction/initialize"
    headers = {
        "Authorization": f"Bearer {secret_key.get_secret_value()}",
        "Content-Type": "application/json",
    }
    payload = {
        "email": email,
        "amount": amount_kobo,
        "reference": reference,
    }
    if callback_url:
        payload["callback_url"] = callback_url

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=10.0)
            if response.status_code == 200:
                data = response.json()
                return str(data.get("data", {}).get("authorization_url"))
            else:
                logger.error("Paystack transaction initialization failure: %s", response.text)
                return None
    except Exception as e:
        logger.error("Paystack transaction connection failed: %s", e, exc_info=True)
        return None


@router.post("/webhook")
async def paystack_webhook(
    request: Request,
    x_paystack_signature: str | None = Header(None),
) -> Response:
    """
    Verifies HMAC-SHA512 webhook signature from Paystack to prevent transaction spoofing.
    Upon verification, broadcasts payment.success onto the internal event_bus.
    """
    settings = get_settings()
    secret_key = settings.PAYSTACK_SECRET_KEY
    secret_str = secret_key.get_secret_value() if secret_key else "paystack_sandbox_secret"

    if not x_paystack_signature:
        logger.warning("Paystack webhook challenge rejected: x-paystack-signature is missing.")
        return Response(content="Missing signature header", status_code=401)

    raw_body = await request.body()
    computed_signature = hmac.new(
        secret_str.encode("utf-8"),
        raw_body,
        hashlib.sha512
    ).hexdigest()

    if not hmac.compare_digest(computed_signature, x_paystack_signature):
        logger.warning(
            "Paystack webhook signature verification failed. "
            "Computed: %s | Header: %s",
            computed_signature,
            x_paystack_signature,
        )
        return Response(content="Invalid signature", status_code=401)

    # Decode JSON payload
    try:
        payload = await request.json()
    except Exception:
        return Response(content="Invalid JSON", status_code=400)

    event_type = payload.get("event")
    data = payload.get("data", {})

    if event_type == "charge.success":
        ref = data.get("reference")
        amount_kobo = data.get("amount", 0)
        customer_email = data.get("customer", {}).get("email")
        
        # Extrapolate internal business and metadata parameters
        # In production webhooks, custom_fields are sent in metadata
        metadata = data.get("metadata", {})
        business_id = metadata.get("business_id")
        order_id = metadata.get("order_id")

        logger.info(
            "Paystack Charge Success Verified! Ref: %s | Amount: ₦%.2f | Business: %s",
            ref,
            amount_kobo / 100.0,
            business_id,
        )

        # Broadcast payment success event
        await event_bus.emit(
            event_type="payment.success",
            payload={
                "business_id": business_id,
                "order_id": order_id,
                "amount": amount_kobo / 100.0,
                "reference": ref,
                "email": customer_email,
            },
            source_module="payments",
        )

    return Response(content="OK", status_code=200)
