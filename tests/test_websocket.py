"""
OpsPilot — WebSocket Gateway Test Suite.
"""

from __future__ import annotations

import asyncio
import uuid

import pytest
from fastapi import WebSocketDisconnect
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import event_bus
from app.main import app
from app.modules.auth.models import User, UserRole
from app.modules.auth.service import AuthService
from app.modules.businesses.models import Business


@pytest.fixture
async def ws_test_data(db_session: AsyncSession) -> dict:
    """Setup active business, owner user, and a valid access token for testing."""
    # 1. Create Business
    business = Business(
        name="WS Test Bakery",
        slug=f"ws-test-bakery-{uuid.uuid4()}",
        industry="Retail",
    )
    db_session.add(business)
    await db_session.flush()

    # 2. Create Owner User
    owner = User(
        email=f"ws-owner-{uuid.uuid4()}@testbakery.com",
        password_hash="fake_hash",
        first_name="WebSocket",
        last_name="Tester",
        role=UserRole.OWNER,
        business_id=business.id,
        is_active=True,
        is_verified=True,
    )
    db_session.add(owner)
    await db_session.flush()
    await db_session.commit()

    # 3. Generate JWT Token using AuthService
    auth_service = AuthService(db_session, redis=None)
    token_data = auth_service._generate_tokens(owner)

    return {
        "business": business,
        "owner": owner,
        "token": token_data.access_token,
    }


def test_websocket_auth_failures():
    """Verify that WebSocket connection is rejected if JWT token is missing or invalid."""
    with TestClient(app) as client:
        # 1. No token provided
        with client.websocket_connect("/api/v1/ws") as websocket, pytest.raises(WebSocketDisconnect):
            websocket.receive_json()

        # 2. Invalid token provided
        with (
            client.websocket_connect("/api/v1/ws?token=invalid_token") as websocket,
            pytest.raises(WebSocketDisconnect),
        ):
            websocket.receive_json()


@pytest.mark.asyncio
async def test_websocket_lifecycle_and_broadcasts(ws_test_data: dict):
    """Test successful connection, presence tracking, and receiving events over WebSocket."""
    token = ws_test_data["token"]
    business_id = str(ws_test_data["business"].id)
    user_id = str(ws_test_data["owner"].id)

    with TestClient(app) as client, client.websocket_connect(f"/api/v1/ws?token={token}") as websocket:
        # 1. Verify connection initiates presence list broadcast
        initial_msg = await asyncio.to_thread(websocket.receive_json)
        assert initial_msg["event"] == "presence.update"
        assert len(initial_msg["payload"]["presence"]) == 1
        assert initial_msg["payload"]["presence"][0]["user_id"] == user_id
        assert initial_msg["payload"]["presence"][0]["status"] == "online"

        # 2. Test sending presence updates to the server
        await asyncio.to_thread(
            websocket.send_json, {"type": "presence", "status": "busy", "current_view": "order:123"}
        )

        # Wait for the presence update broadcast back
        presence_msg = await asyncio.to_thread(websocket.receive_json)
        assert presence_msg["event"] == "presence.update"
        active_presence = presence_msg["payload"]["presence"][0]
        assert active_presence["status"] == "busy"
        assert active_presence["current_view"] == "order:123"

        # 3. Simulate emitting a local event on the core event bus
        # This should bridge to WebSockets and push order details
        await event_bus.emit(
            event_type="order.created",
            payload={
                "business_id": business_id,
                "order_id": str(uuid.uuid4()),
                "amount": 4200.0,
            },
            source_module="orders",
        )

        # Receive and verify the pushed event
        broadcast_msg = await asyncio.to_thread(websocket.receive_json)
        assert broadcast_msg["event"] == "order.created"
        assert broadcast_msg["business_id"] == business_id
        assert broadcast_msg["payload"]["amount"] == 4200.0
