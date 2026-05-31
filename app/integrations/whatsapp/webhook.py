"""
OpsPilot — Meta WhatsApp Cloud API Webhook Endpoints.
"""

from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, Query, Request, Response

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("integrations.whatsapp.webhook")

router = APIRouter(prefix="/integrations/whatsapp", tags=["WhatsApp Integration"])


@router.get("")
async def whatsapp_verify_webhook(
    mode: str = Query(None, alias="hub.mode"),
    challenge: str = Query(None, alias="hub.challenge"),
    verify_token: str = Query(None, alias="hub.verify_token"),
) -> Response:
    """
    Handles Meta's Webhook verification handshake request.

    Verifies that the incoming token matches WHATSAPP_VERIFY_TOKEN,
    then returns the challenge string as raw text.
    """
    settings = get_settings()
    configured_token = settings.WHATSAPP_VERIFY_TOKEN

    token_str = configured_token.get_secret_value() if configured_token else "opspilot_default_verify_token"

    if mode == "subscribe" and verify_token == token_str:
        logger.info("WhatsApp webhook signature successfully verified.")
        return Response(content=challenge, media_type="text/plain")

    logger.warning("WhatsApp webhook signature verification failed.")
    return Response(content="Forbidden", status_code=403)


@router.post("")
async def whatsapp_event_receiver(request: Request) -> dict[str, Any]:
    """
    Receives inbound real-time customer event dispatches from Meta.

    Spawns an out-of-band asynchronous processor task to keep response
    delivery under Meta's strict 2-second timeout limit.
    """
    try:
        payload = await request.json()
    except Exception:
        logger.warning("Received invalid non-JSON WhatsApp event payload.")
        return {"success": False, "error": "Invalid JSON"}

    # 1. Spawn processing in background to immediately return 200 OK
    from app.integrations.whatsapp.service import handle_incoming_whatsapp_payload

    # We trigger the processor out-of-band
    asyncio.create_task(handle_incoming_whatsapp_payload(payload))

    return {"success": True}
