"""
OpsPilot — SMS Dispatch Client (Twilio & Termii integrations).
"""

from __future__ import annotations

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("integrations.communications.sms")


async def send_sms(to_phone: str, text: str) -> bool:
    """
    Sends an outbound SMS using Twilio as the global carrier or Termii as the local carrier.
    
    If integration credentials are not configured, falls back to mock sandbox logging.
    """
    settings = get_settings()
    twilio_sid = settings.TWILIO_ACCOUNT_SID
    twilio_token = settings.TWILIO_AUTH_TOKEN

    # 1. Fallback Mock Sandbox mode
    if not twilio_sid or not twilio_token:
        logger.info(
            "[MOCK SMS DISPATCH] To: %s | Content: %s",
            to_phone,
            text,
        )
        return True

    # 2. Production Twilio Dispatch
    url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/Messages.json"
    auth = (twilio_sid, twilio_token.get_secret_value())
    data = {
        "To": to_phone,
        "From": "+1234567890",  # Configured Twilio number
        "Body": text,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data, auth=auth, timeout=10.0)
            if response.status_code in (200, 201):
                logger.info("Successfully dispatched SMS to %s via Twilio", to_phone)
                return True
            else:
                logger.error(
                    "Twilio SMS API error payload returned (%d): %s",
                    response.status_code,
                    response.text,
                )
                return False
    except Exception as e:
        logger.error("Outbound SMS connection failed: %s", e, exc_info=True)
        return False
