"""
OpsPilot — Request ID Middleware.

Assigns a unique X-Request-ID to every request for tracing.
The ID is injected into the context variable used by the
structured logger.
"""

from __future__ import annotations

import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import request_id_ctx


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that:
    1. Reads an incoming X-Request-ID header (or generates one)
    2. Sets it in the context variable for logging
    3. Returns it in the response header
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Set context var for structured logging
        token = request_id_ctx.set(request_id)

        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            request_id_ctx.reset(token)
