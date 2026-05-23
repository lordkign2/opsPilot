"""
OpsPilot — Centralised Router Registry.

All module routers are registered here. Adding a new module
is a one-line change in this file — main.py never needs to
be touched again.

At 100+ endpoints across 8+ modules, this prevents main.py
from becoming a sprawling import dump.
"""

from __future__ import annotations

from fastapi import APIRouter, FastAPI

# ── API v1 Master Router ────────────────────────────────────
api_v1_router = APIRouter(prefix="/api/v1")


def register_routers(app: FastAPI) -> None:
    """
    Import and mount all module routers onto the v1 prefix.

    To add a new module:
    1. Create `app/modules/<name>/routes.py` with a `router` object.
    2. Add one import + one `include_router` line here.
    """

    # ── Auth ─────────────────────────────────────────────────
    from app.modules.auth.routes import router as auth_router
    api_v1_router.include_router(auth_router)

    # ── Businesses ───────────────────────────────────────────
    from app.modules.businesses.routes import router as businesses_router
    api_v1_router.include_router(businesses_router)

    # ── Customers ────────────────────────────────────────────
    from app.modules.customers.routes import router as customers_router
    api_v1_router.include_router(customers_router)

    # ── Orders ───────────────────────────────────────────────
    from app.modules.orders.routes import router as orders_router
    api_v1_router.include_router(orders_router)

    # ── Payments ─────────────────────────────────────────────
    from app.modules.payments.routes import router as payments_router
    api_v1_router.include_router(payments_router)

    # ── Future modules (Phase 3) ─────────────────────────────
    # from app.modules.ai.routes import router as ai_router
    # api_v1_router.include_router(ai_router)
    #
    # from app.modules.analytics.routes import router as analytics_router
    # api_v1_router.include_router(analytics_router)
    #
    # from app.modules.notifications.routes import router as notifications_router
    # api_v1_router.include_router(notifications_router)
    
    # ── Mount the v1 router onto the app ─────────────────────
    app.include_router(api_v1_router)


def register_event_handlers() -> None:
    """
    Import all event handler modules so they register
    their listeners on the event bus at startup.

    Adding a module? Import its events module here.
    """
    import app.modules.auth.events  # noqa: F401
    import app.modules.businesses.events  # noqa: F401
    import app.modules.audit.events  # noqa: F401
    import app.modules.customers.events  # noqa: F401
    import app.modules.orders.events  # noqa: F401
    import app.modules.payments.events  # noqa: F401

    # Future:
    # import app.modules.notifications.events  # noqa: F401
