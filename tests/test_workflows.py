"""
OpsPilot — Workflow Automation Module: Automated Test Suite.
"""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from unittest.mock import patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import event_bus
from app.modules.auth.models import User, UserRole
from app.modules.auth.service import AuthService
from app.modules.businesses.models import Business
from app.modules.notifications.models import Notification
from app.modules.workflows.models import WorkflowExecutionLog


@pytest.fixture
async def workflow_test_data(db_session: AsyncSession) -> dict:
    """Setup testing business context and JWT credentials."""
    # 1. Create Business
    business = Business(
        name="Automation SME Shop",
        slug=f"automation-sme-{uuid.uuid4()}",
        industry="Retail",
    )
    db_session.add(business)
    await db_session.flush()

    # 2. Create Owner User
    owner = User(
        email=f"automation-owner-{uuid.uuid4()}@smeworx.com",
        password_hash="fake_hash",
        first_name="Automation",
        last_name="Architect",
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


@pytest.mark.asyncio
async def test_workflow_crud_and_rule_execution(
    client: AsyncClient, workflow_test_data: dict, db_session: AsyncSession
):
    """
    Test Workflow creation, dynamic filter matching, template interpolation,
    out-of-band asynchronous processing, and execution logging.
    """
    token = workflow_test_data["token"]
    business_id = str(workflow_test_data["business"].id)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create a dynamic operational workflow rule via API
    # Trigger: 'payment.success'
    # Condition: 'amount' > 50000
    # Action: 'send_notification' with dynamic template resolver
    create_payload = {
        "name": "Big Ticket Alert",
        "description": "Notify owner on large payments",
        "trigger_type": "payment.success",
        "is_active": True,
        "conditions": [{"field": "amount", "operator": "gt", "value": 50000}],
        "actions": [
            {
                "type": "send_notification",
                "params": {"title": "VIP Transaction!", "message": "High-value order {{order_id}} paid: ₦{{amount}}"},
            }
        ],
        "log_depth": "all",
    }

    # Ensure triggers are registered on the event bus
    from app.modules.workflows.triggers import register_workflow_trigger_listeners

    register_workflow_trigger_listeners()

    response = await client.post("/api/v1/workflows/", json=create_payload, headers=headers)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True
    workflow_id = res_json["data"]["id"]
    assert workflow_id is not None

    # Define custom async session maker patch to bridge the test transaction to background tasks
    @asynccontextmanager
    async def mock_session_maker():
        yield db_session

    with patch("app.modules.workflows.triggers.async_session_factory", mock_session_maker):
        # ── Test Run Case A: Low Amount Payment (Should be skipped by filters) ──
        order_id_low = str(uuid.uuid4())
        await event_bus.emit(
            event_type="payment.success",
            payload={
                "business_id": business_id,
                "order_id": order_id_low,
                "amount": 25000.0,  # Below 50,000 threshold
            },
            source_module="payments",
        )

        # Assert skipped log exists in database, but no notifications were triggered
        stmt_logs = select(WorkflowExecutionLog).where(
            WorkflowExecutionLog.business_id == uuid.UUID(business_id), WorkflowExecutionLog.status == "skipped"
        )
        logs_res = await db_session.execute(stmt_logs)
        skipped_logs = logs_res.scalars().all()
        assert len(skipped_logs) == 1
        assert "skipped" in skipped_logs[0].status

        stmt_notifs = select(Notification).where(Notification.business_id == uuid.UUID(business_id))
        notifs_res = await db_session.execute(stmt_notifs)
        assert len(notifs_res.scalars().all()) == 0

        # ── Test Run Case B: High Amount Payment (Should match, resolve template, run actions) ──
        order_id_high = str(uuid.uuid4())
        await event_bus.emit(
            event_type="payment.success",
            payload={
                "business_id": business_id,
                "order_id": order_id_high,
                "amount": 75000.0,  # Exceeds 50,000 threshold
            },
            source_module="payments",
        )

        # Assert successful log is documented and dynamic template variables resolved into a new alert
        stmt_success = select(WorkflowExecutionLog).where(
            WorkflowExecutionLog.business_id == uuid.UUID(business_id), WorkflowExecutionLog.status == "success"
        )
        success_res = await db_session.execute(stmt_success)
        success_logs = success_res.scalars().all()
        assert len(success_logs) == 1

        stmt_alerts = select(Notification).where(Notification.business_id == uuid.UUID(business_id))
        alerts_res = await db_session.execute(stmt_alerts)
        alerts = alerts_res.scalars().all()
        assert len(alerts) == 1
        assert alerts[0].title == "VIP Transaction!"
        assert order_id_high in alerts[0].message
        assert "75000" in alerts[0].message

        # ── Test Run Case C: Clean API Logs Feeds ──
        logs_response = await client.get("/api/v1/workflows/logs", headers=headers)
        assert logs_response.status_code == 200
        logs_json = logs_response.json()
        assert logs_json["success"] is True
        assert len(logs_json["data"]) >= 2  # one skipped, one success log
