"""
OpsPilot — Transactional Email Client (Resend Integration).
"""

from __future__ import annotations

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("integrations.communications.email")


async def send_transactional_email(to_email: str, subject: str, html_content: str) -> bool:
    """
    Sends a transactional HTML email using the Resend Cloud API.

    If Resend credentials are not configured, falls back to logging the dispatch securely.
    """
    settings = get_settings()
    api_key = settings.RESEND_API_KEY

    # 1. Fallback Mock Sandbox mode
    if not api_key:
        logger.info(
            "[MOCK EMAIL DISPATCH] To: %s | Subject: %s | Preview: %s...",
            to_email,
            subject,
            html_content[:100].replace("\n", " "),
        )
        return True

    # 2. Production Call
    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {api_key.get_secret_value()}",
        "Content-Type": "application/json",
    }
    payload = {
        "from": "OpsPilot Alerts <alerts@opspilot.com>",
        "to": [to_email],
        "subject": subject,
        "html": html_content,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=10.0)
            if response.status_code in (200, 201):
                logger.info("Successfully dispatched transactional email to %s", to_email)
                return True
            else:
                logger.error(
                    "Resend API error payload returned (%d): %s",
                    response.status_code,
                    response.text,
                )
                return False
    except Exception as e:
        logger.error("Outbound email connection failed: %s", e, exc_info=True)
        return False
