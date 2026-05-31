"""
OpsPilot — Rate Limiting Middleware.

Simple in-memory rate limiter per client IP.
In production, swap to Redis-backed sliding window
for multi-instance deployments.
"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.logging import get_logger

logger = get_logger("middleware.rate_limit")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Token-bucket rate limiter per client IP.

    Defaults: 60 requests/minute for general endpoints,
    10 requests/minute for auth endpoints (login, register).
    """

    def __init__(
        self,
        app: Any,
        *,
        default_limit: int = 60,
        auth_limit: int = 10,
        window_seconds: int = 60,
    ) -> None:
        super().__init__(app)
        self.default_limit = default_limit
        self.auth_limit = auth_limit
        self.window_seconds = window_seconds
        self._buckets: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip health checks
        if request.url.path in ("/health", "/healthz", "/"):
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        path = request.url.path

        # Determine rate limit
        is_auth = any(path.startswith(p) for p in ("/api/v1/auth/login", "/api/v1/auth/register"))
        limit = self.auth_limit if is_auth else self.default_limit

        # Bucket key
        bucket_key = f"{client_ip}:{path}" if is_auth else client_ip

        # Clean expired entries
        now = time.time()
        cutoff = now - self.window_seconds
        self._buckets[bucket_key] = [t for t in self._buckets[bucket_key] if t > cutoff]

        if len(self._buckets[bucket_key]) >= limit:
            logger.warning("Rate limit hit: %s (%s)", bucket_key, path)
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "message": "Too many requests. Please try again later.",
                    "error_code": "RATE_LIMIT",
                },
                headers={"Retry-After": str(self.window_seconds)},
            )

        self._buckets[bucket_key].append(now)
        return await call_next(request)

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        """Extract client IP, respecting proxy headers."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
