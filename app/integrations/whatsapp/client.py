"""
OpsPilot — Meta WhatsApp Cloud API Outbound Client.
"""

from __future__ import annotations

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("integrations.whatsapp.client")


async def send_whatsapp_message(to_phone: str, text: str) -> bool:
    """
    Dispatches an outbound text message to a client using the Meta WhatsApp Cloud API.

    If integration credentials are not configured, falls back to secure local logging simulating
    sandbox dispatch behavior to support local development seamlessly.
    """
    settings = get_settings()
    token = settings.WHATSAPP_TOKEN
    phone_id = settings.WHATSAPP_PHONE_NUMBER_ID

    # 1. Fallback Mock Sandbox mode
    if not token or not phone_id:
        logger.info(
            "[MOCK DISPATCH] WhatsApp Outbox -> To: %s | Content: %s",
            to_phone,
            text,
        )
        return True

    # 2. Production Dispatch
    url = f"https://graph.facebook.com/v20.0/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {token.get_secret_value()}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "text",
        "text": {"body": text},
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=10.0)
            if response.status_code in (200, 201):
                logger.info("Successfully dispatched WhatsApp message to %s", to_phone)
                return True
            else:
                logger.error(
                    "Meta API error payload returned (%d): %s",
                    response.status_code,
                    response.text,
                )
                return False
    except Exception as e:
        logger.error("Outbound WhatsApp connection failed: %s", e, exc_info=True)
        return False
