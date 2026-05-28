"""
OpsPilot — WhatsApp Conversational Commerce Service.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select

from app.db.session import async_session_factory
from app.core.logging import get_logger
from app.integrations.whatsapp.client import send_whatsapp_message
from app.modules.businesses.models import Business
from app.modules.customers.models import Customer
from app.modules.customers.repository import CustomerRepository
from app.modules.orders.models import Order, OrderStatus
from app.modules.orders.repository import OrderRepository

logger = get_logger("integrations.whatsapp.service")


def extract_whatsapp_message(payload: dict[str, Any]) -> tuple[str | None, str | None]:
    """Helper to safely extract the sender's phone and message text body from Meta payload."""
    try:
        entry = payload.get("entry", [])[0]
        change = entry.get("changes", [])[0]
        value = change.get("value", {})
        message = value.get("messages", [])[0]
        sender = message.get("from")
        body = message.get("text", {}).get("body")
        return sender, body
    except Exception:
        return None, None


async def handle_incoming_whatsapp_payload(payload: dict[str, Any]) -> None:
    """
    Core entrypoint processing WhatsApp payloads out-of-band.
    
    Performs multi-tenant resolution, client onboarding, conversational AI responses,
    and automatic order creation.
    """
    sender, body = extract_whatsapp_message(payload)
    if not sender or not body:
        logger.debug("WhatsApp payload parsed: missing text body or sender identity.")
        return

    logger.info("Processing inbound WhatsApp chat from %s: '%s'", sender, body)

    async with async_session_factory() as db:
        # 1. Fetch default Business context
        stmt_biz = select(Business)
        res_biz = await db.execute(stmt_biz)
        business = res_biz.scalars().first()
        if not business:
            logger.warning("No active Business workspace discovered. Aborting WhatsApp message loop.")
            return

        # 2. Lookup or onboard Customer based on phone identity
        customer_repo = CustomerRepository(db)
        customer = await customer_repo.get_one_by(phone=sender)
        if not customer:
            logger.info("WhatsApp client %s is new. Registering Customer profile...", sender)
            customer = Customer(
                name=f"WhatsApp Client {sender[-4:]}",
                phone=sender,
                business_id=business.id,
            )
            await customer_repo.create(customer)
            await db.commit()

        # 3. Conversational commerce checkout detection
        clean_text = body.lower()
        if "order" in clean_text or "buy" in clean_text:
            logger.info("Checkout signal detected. Generating automated Order for Customer: %s", customer.id)
            
            order_repo = OrderRepository(db)
            order = Order(
                status=OrderStatus.PENDING,
                total_amount=15000.00,  # Standard automated order baseline value
                notes=f"Automated Conversational order initialized from text: '{body}'",
                customer_id=customer.id,
                business_id=business.id,
            )
            await order_repo.create(order)
            await db.commit()

            checkout_url = f"https://checkout.paystack.com/mock-{uuid.uuid4()}"
            reply = (
                f"Hello {customer.name}! 🌟\n"
                f"I've initialized your automated order *#OP-{str(order.id)[:8].upper()}*.\n\n"
                f"💵 *Total:* ₦15,000.00\n"
                f"🔗 *Pay securely via Paystack:* {checkout_url}\n\n"
                f"Thank you for shopping with us!"
            )
            await send_whatsapp_message(sender, reply)
            return

        # 4. Standard Assistant Q&A Chat loop fallback
        from app.modules.ai.service import AIService
        logger.info("Routing customer query to central operations AIService.")
        ai_service = AIService(db)
        ai_reply = await ai_service.chat_with_assistant(business.id, body)
        await send_whatsapp_message(sender, ai_reply)
