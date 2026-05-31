"""
OpsPilot — Workflow Automation Module: Action Executors Registry.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.modules.notifications.schemas import NotificationCreate
from app.modules.notifications.service import NotificationService

logger = get_logger("workflows.actions")


async def execute_send_notification(db: AsyncSession, business_id: uuid.UUID, params: dict[str, Any]) -> dict[str, Any]:
    """Execute send_notification action inside the business workspace."""
    service = NotificationService(db)

    # Try parsing user_id if supplied as a string UUID
    user_id_str = params.get("user_id")
    user_id = None
    if user_id_str:
        try:
            user_id = uuid.UUID(user_id_str)
        except ValueError:
            pass

    payload = NotificationCreate(
        user_id=user_id,
        title=params.get("title", "OpsPilot Automation"),
        message=params.get("message", "A custom workflow action was triggered."),
    )
    notification = await service.create_notification(business_id, payload)
    return {
        "status": "success",
        "notification_id": str(notification.id),
        "title": notification.title,
    }


async def execute_generate_ai_message(
    db: AsyncSession, business_id: uuid.UUID, params: dict[str, Any]
) -> dict[str, Any]:
    """Execute generate_ai_message by calling our AIService chat assistant."""
    from app.modules.ai.service import AIService

    service = AIService(db)
    prompt = params.get("prompt", "Draft a professional response.")

    # Generate copy using assistant
    reply = await service.chat_with_assistant(business_id, prompt)
    return {
        "status": "success",
        "generated_message": reply,
    }


async def execute_send_whatsapp(db: AsyncSession, business_id: uuid.UUID, params: dict[str, Any]) -> dict[str, Any]:
    """Placeholder WhatsApp execution designed to mount Meta Cloud API in Phase 6."""
    phone = params.get("phone", "")
    message = params.get("message", "")

    logger.info(
        "[WhatsApp Mock] Sending message to %s for business %s: %s",
        phone,
        business_id,
        message,
    )
    return {
        "status": "success",
        "provider": "whatsapp_mock",
        "recipient": phone,
    }


async def execute_send_email(db: AsyncSession, business_id: uuid.UUID, params: dict[str, Any]) -> dict[str, Any]:
    """Placeholder transactional email execution designed to link Resend/Mailgun in Phase 6."""
    email = params.get("email", "")
    subject = params.get("subject", "Automation Alert")
    body = params.get("body", "")

    logger.info(
        "[Email Mock] Sending email to %s (subject: '%s') for business %s",
        email,
        subject,
        business_id,
    )
    return {
        "status": "success",
        "provider": "email_mock",
        "recipient": email,
    }


async def execute_create_task(db: AsyncSession, business_id: uuid.UUID, params: dict[str, Any]) -> dict[str, Any]:
    """Placeholder operational task mapping to create staff assignments."""
    title = params.get("title", "New Workflow Task")
    logger.info(
        "[Task Mock] Creating task '%s' for business workspace %s",
        title,
        business_id,
    )
    return {
        "status": "success",
        "task_title": title,
    }


# Map action types to active async runner methods
ACTION_REGISTRY = {
    "send_notification": execute_send_notification,
    "generate_ai_message": execute_generate_ai_message,
    "send_whatsapp": execute_send_whatsapp,
    "send_email": execute_send_email,
    "create_task": execute_create_task,
}


async def run_action(
    db: AsyncSession, action_type: str, business_id: uuid.UUID, params: dict[str, Any]
) -> dict[str, Any]:
    """Resolves and runs an action from the registry."""
    executor = ACTION_REGISTRY.get(action_type)
    if not executor:
        raise ValueError(f"Unsupported action type: {action_type}")

    return await executor(db, business_id, params)
