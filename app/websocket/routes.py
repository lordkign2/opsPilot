"""
OpsPilot — WebSocket Route Handlers.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.websocket.auth import authenticate_websocket
from app.websocket.connection import ActiveConnection
from app.websocket.manager import ws_manager

logger = logging.getLogger("opspilot.websocket.routes")

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str | None = None) -> None:
    """
    WebSocket Gateway Endpoint.

    Establishes real-time connection. Authenticates via query parameter `?token=...`
    and maintains presence tracking. Supports incoming message handlers for view-states.
    """
    # 1. Accept initial handshake request
    await websocket.accept()

    # 2. Authenticate the socket session
    user = await authenticate_websocket(websocket, token)
    if not user:
        # authenticate_websocket takes care of closing standard WS code
        return

    b_id = str(user.business_id)
    u_id = str(user.id)

    # 3. Create active session mapping
    connection = ActiveConnection(websocket=websocket, user_id=u_id, business_id=b_id)
    ws_manager.connect(connection)

    try:
        # Broadcast presence change to other workspace users
        await ws_manager.broadcast_to_business(
            business_id=b_id,
            event_type="presence.update",
            payload={"presence": ws_manager.get_presence(b_id)},
        )

        # 4. Connection loop — listen for client-side events (e.g. active tab/presence changes)
        import json

        while True:
            try:
                data = await websocket.receive_json()
            except (ValueError, TypeError, json.JSONDecodeError) as parse_err:
                logger.warning(
                    "Malformed frame payload received from user %s in business %s: %s",
                    u_id,
                    b_id,
                    parse_err,
                )
                await connection.send_json(
                    {
                        "event": "error",
                        "business_id": b_id,
                        "payload": {"message": "Invalid frame payload. Expected valid JSON format."},
                    }
                )
                continue

            msg_type = data.get("type")

            if msg_type == "presence":
                status = data.get("status", "online")
                view = data.get("current_view")
                ws_manager.update_presence(b_id, u_id, status, view)

                # Broadcast updated presence list
                await ws_manager.broadcast_to_business(
                    business_id=b_id,
                    event_type="presence.update",
                    payload={"presence": ws_manager.get_presence(b_id)},
                )

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected gracefully for user %s", u_id)
    except Exception as e:
        logger.error("Error in WebSocket session loop for user %s: %s", u_id, e, exc_info=True)

    finally:
        # 5. Clean up presence and connections
        ws_manager.disconnect(connection)

        # Broadcast leaving status to business workspace
        await ws_manager.broadcast_to_business(
            business_id=b_id,
            event_type="presence.update",
            payload={"presence": ws_manager.get_presence(b_id)},
        )
