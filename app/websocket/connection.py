"""
OpsPilot — WebSocket Connection Wrapper.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger("opspilot.websocket.connection")


class ActiveConnection:
    """Wraps a FastAPI WebSocket connection to ensure safe delivery and typing."""

    def __init__(self, websocket: WebSocket, user_id: str, business_id: str) -> None:
        self.websocket = websocket
        self.user_id = user_id
        self.business_id = business_id

    async def send_json(self, data: dict[str, Any]) -> bool:
        """
        Sends a JSON object safely to the client.
        Returns True if successful, False if connection is lost.
        """
        try:
            await self.websocket.send_json(data)
            return True
        except Exception as e:
            logger.warning(
                "Failed to send message to user %s in business %s: %s",
                self.user_id,
                self.business_id,
                e,
            )
            return False
