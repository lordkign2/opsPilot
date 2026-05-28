"""
OpsPilot — Application Entry Point.

Wires together all modules, middleware, and lifecycle events
into a single FastAPI application instance.

This file should rarely need editing. New modules are added
via `app/core/registry.py` — not here.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.exceptions import OpsPilotException
from app.core.logging import get_logger, setup_logging
from app.core.registry import register_event_handlers, register_routers
from app.middleware.cors import add_cors_middleware
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_id import RequestIDMiddleware
from app.shared.response import error_response

settings = get_settings()
logger = get_logger("main")


# ── Lifecycle ────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application startup and shutdown hooks."""
    setup_logging()
    register_event_handlers()

    # Start horizontal broadcaster for WebSockets (Phase 4)
    from app.websocket.broadcaster import start_broadcaster
    start_broadcaster()



    logger.info(
        "Starting %s v%s [%s]",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.APP_ENV.value,
    )

    yield

    # Shutdown
    from app.db.redis import redis_client
    from app.db.session import engine
    from app.websocket.broadcaster import stop_broadcaster

    await stop_broadcaster()
    await engine.dispose()
    await redis_client.close()
    logger.info("Shutdown complete.")


# ── Application ──────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered business operations platform for SMEs",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    lifespan=lifespan,
)


# ── Middleware (outermost → innermost) ───────────────────────

add_cors_middleware(app)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware, default_limit=60, auth_limit=10)


# ── Global Exception Handlers ───────────────────────────────


@app.exception_handler(OpsPilotException)
async def opspilot_exception_handler(
    request: Request, exc: OpsPilotException
) -> JSONResponse:
    """Convert custom exceptions into standardised JSON errors."""
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
            message=exc.detail,
            error_code=exc.error_code,
            details=exc.context if exc.context else None,
        ),
        headers=exc.headers,
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unhandled exceptions."""
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content=error_response(
            message="An unexpected error occurred.",
            error_code="INTERNAL_ERROR",
        ),
    )


# ── Register All Module Routers ──────────────────────────────

register_routers(app)


# ── Health Check ─────────────────────────────────────────────


@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV.value,
    }


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "version": settings.APP_VERSION,
        "docs": "/docs" if settings.is_development else None,
    }
