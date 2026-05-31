"""
OpsPilot — Push Notifications Client (Expo Integration).
"""

from __future__ import annotations

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("integrations.communications.push")


async def send_push_notification(expo_token: str, title: str, message: str) -> bool:
    """
    Sends a transactional push notification to web/mobile clients using the Expo Push Service.

    If credentials are not configured, falls back to logging the dispatch securely.
    """
    # 1. Validation check
    if not expo_token.startswith("ExponentPushToken["):
        logger.warning("Push failed: '%s' is not a valid Expo push token.", expo_token)
        return False

    settings = get_settings()
    access_token = settings.EXPO_ACCESS_TOKEN

    # 2. Fallback Mock Sandbox mode
    if not access_token:
        logger.info(
            "[MOCK PUSH DISPATCH] Token: %s | Title: %s | Message: %s",
            expo_token,
            title,
            message,
        )
        return True

    # 3. Production Call
    url = "https://exp.host/--/api/v2/push/send"
    headers = {
        "Authorization": f"Bearer {access_token.get_secret_value()}",
        "Content-Type": "application/json",
    }
    payload = {
        "to": expo_token,
        "title": title,
        "body": message,
        "sound": "default",
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=10.0)
            if response.status_code == 200:
                logger.info("Successfully fanned out push alert to token %s", expo_token)
                return True
            else:
                logger.error(
                    "Expo Push API error payload returned (%d): %s",
                    response.status_code,
                    response.text,
                )
                return False
    except Exception as e:
        logger.error("Outbound push transaction failed: %s", e, exc_info=True)
        return False
