"""
OpsPilot — Maintenance Mode Middleware.

Intercepts requests and blocks non-administrative traffic when system maintenance is active.
"""

from __future__ import annotations

import logging
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.security import decode_token
from app.shared.response import error_response

logger = logging.getLogger("opspilot.middleware.maintenance")


class MaintenanceModeMiddleware(BaseHTTPMiddleware):
    """Checks Redis for active maintenance mode, blocking non-admin traffic with 503."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path

        # Bypass checks for health endpoints, Swagger documentation, and admin router paths
        if path in ("/health", "/healthz", "/", "/docs", "/redoc", "/openapi.json") or path.startswith("/api/v1/admin"):
            return await call_next(request)

        # Retrieve direct Redis client (using the global app-level client, supporting overrides for testing)
        from app.db.redis import get_redis, redis_client

        client: Any = redis_client
        if hasattr(request.app, "dependency_overrides") and get_redis in request.app.dependency_overrides:
            override = request.app.dependency_overrides[get_redis]
            if callable(override):
                try:
                    import inspect

                    if inspect.isasyncgenfunction(override) or inspect.isgeneratorfunction(override):
                        gen = override()
                        if inspect.isasyncgen(gen):
                            client = await gen.__anext__()
                        else:
                            client = next(gen)
                    else:
                        client = override()
                except Exception as e:
                    logger.error("Failed to resolve Redis dependency override: %s", e)

        try:
            # Check maintenance flag
            is_maintenance = await client.get("opspilot:maintenance_mode")
            if is_maintenance == b"true":
                # Check for super admin credentials to bypass maintenance mode
                auth_header = request.headers.get("Authorization")
                if auth_header and auth_header.startswith("Bearer "):
                    token = auth_header.split(" ")[1]
                    try:
                        payload = decode_token(token)
                        # Let super admin users pass completely
                        if payload.get("role") == "super_admin":
                            return await call_next(request)
                    except Exception:
                        pass  # Invalid token, fall through to block request

                logger.warning("Request to %s blocked due to active maintenance mode", path)
                return JSONResponse(
                    status_code=503,
                    content=error_response(
                        message="The system is currently undergoing scheduled maintenance. Please try again later.",
                        error_code="SERVICE_UNAVAILABLE",
                    ),
                )
        except Exception as e:
            # Fall back to letting the request pass to avoid completely taking down the app if Redis behaves unexpectedly
            logger.error("Error in MaintenanceModeMiddleware: %s", e)

        return await call_next(request)
