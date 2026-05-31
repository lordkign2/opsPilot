"""
OpsPilot — Flutterwave Payments Gateway Integration.
"""

from __future__ import annotations

import hmac
import uuid

import httpx
from fastapi import APIRouter, Header, Request, Response

from app.core.config import get_settings
from app.core.events import event_bus
from app.core.logging import get_logger

logger = get_logger("integrations.payments.flutterwave")

router = APIRouter(prefix="/integrations/payments/flutterwave", tags=["Flutterwave Payments Integration"])


async def initialize_flutterwave_transaction(
    email: str, amount: float, tx_ref: str, callback_url: str | None = None
) -> str | None:
    """
    Initializes a new checkout payment transaction with Flutterwave.
    Returns the secure standard payment redirect link.

    If integration credentials are not configured, falls back to a sandbox mockup checkout url.
    """
    settings = get_settings()
    secret_key = settings.PAYSTACK_SECRET_KEY  # Generic key mapping placeholder or simulated

    # 1. Fallback Mock Checkout
    if not secret_key:
        logger.info(
            "[MOCK FLUTTERWAVE INITIALIZE] Reference: %s | Amount: ₦%.2f | Email: %s",
            tx_ref,
            amount,
            email,
        )
        return f"https://checkout.flutterwave.com/mock-{uuid.uuid4()}"

    # 2. Production Call
    url = "https://api.flutterwave.com/v3/payments"
    headers = {
        "Authorization": f"Bearer {secret_key.get_secret_value()}",
        "Content-Type": "application/json",
    }
    payload = {
        "tx_ref": tx_ref,
        "amount": amount,
        "currency": "NGN",
        "redirect_url": callback_url or "https://opspilot.com/callback",
        "customer": {
            "email": email,
        },
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=10.0)
            if response.status_code == 200:
                data = response.json()
                return str(data.get("data", {}).get("link"))
            else:
                logger.error("Flutterwave transaction initialization failure: %s", response.text)
                return None
    except Exception as e:
        logger.error("Flutterwave transaction connection failed: %s", e, exc_info=True)
        return None


@router.post("/webhook")
async def flutterwave_webhook(
    request: Request,
    verif_hash: str | None = Header(None, alias="verif-hash"),
) -> Response:
    """
    Verifies Flutterwave's secret verification hash passed in headers to prevent transaction spoofing.
    Upon verification, broadcasts payment.success onto the internal event_bus.
    """
    settings = get_settings()
    secret_hash = settings.FLUTTERWAVE_SECRET_HASH
    secret_str = secret_hash.get_secret_value() if secret_hash else "flutterwave_sandbox_hash"

    if not verif_hash:
        logger.warning("Flutterwave webhook challenge rejected: verif-hash is missing.")
        return Response(content="Missing verif-hash header", status_code=401)

    if not hmac.compare_digest(secret_str, verif_hash):
        logger.warning(
            "Flutterwave webhook hash verification failed. Expected: %s | Header: %s",
            secret_str,
            verif_hash,
        )
        return Response(content="Invalid verif-hash", status_code=401)

    # Decode JSON payload
    try:
        payload = await request.json()
    except Exception:
        return Response(content="Invalid JSON", status_code=400)

    # Check for charge status completion
    status = payload.get("status")
    data = payload.get("data", {}) if "data" in payload else payload

    # Flutterwave webhook schemas can put details directly or nested under data
    tx_ref = data.get("tx_ref")
    amount = data.get("amount", 0.0)
    customer_email = (
        data.get("customer", {}).get("email") if isinstance(data.get("customer"), dict) else data.get("customer.email")
    )

    # Meta tracking fields
    meta = data.get("meta", {}) or {}
    business_id = meta.get("business_id")
    order_id = meta.get("order_id")

    if status == "successful":
        logger.info(
            "Flutterwave Payment Verified! Ref: %s | Amount: ₦%.2f | Business: %s",
            tx_ref,
            amount,
            business_id,
        )

        # Broadcast payment success event
        await event_bus.emit(
            event_type="payment.success",
            payload={
                "business_id": business_id,
                "order_id": order_id,
                "amount": float(amount),
                "reference": tx_ref,
                "email": customer_email,
            },
            source_module="payments",
        )

    return Response(content="OK", status_code=200)
