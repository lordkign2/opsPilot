"""
OpsPilot — Centralised Exception Hierarchy.

Every custom exception maps to a well-defined HTTP status code.
The global exception handler in main.py converts these into
standardised JSON error responses.
"""

from __future__ import annotations

from typing import Any


class OpsPilotException(Exception):
    """Base exception for all application errors."""

    status_code: int = 500
    detail: str = "An unexpected error occurred."
    error_code: str = "INTERNAL_ERROR"

    def __init__(
        self,
        detail: str | None = None,
        *,
        error_code: str | None = None,
        headers: dict[str, str] | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        self.detail = detail or self.__class__.detail
        self.error_code = error_code or self.__class__.error_code
        self.headers = headers
        self.context = context or {}
        super().__init__(self.detail)


# ── 400 Bad Request ──────────────────────────────────────────


class BadRequestError(OpsPilotException):
    status_code = 400
    detail = "Bad request."
    error_code = "BAD_REQUEST"


class ValidationError(OpsPilotException):
    status_code = 422
    detail = "Validation failed."
    error_code = "VALIDATION_ERROR"


# ── 401 Unauthorized ─────────────────────────────────────────


class UnauthorizedError(OpsPilotException):
    status_code = 401
    detail = "Authentication required."
    error_code = "UNAUTHORIZED"


class InvalidCredentialsError(OpsPilotException):
    status_code = 401
    detail = "Invalid email or password."
    error_code = "INVALID_CREDENTIALS"


class TokenExpiredError(OpsPilotException):
    status_code = 401
    detail = "Token has expired."
    error_code = "TOKEN_EXPIRED"


class InvalidTokenError(OpsPilotException):
    status_code = 401
    detail = "Invalid or malformed token."
    error_code = "INVALID_TOKEN"


# ── 403 Forbidden ────────────────────────────────────────────


class ForbiddenError(OpsPilotException):
    status_code = 403
    detail = "You do not have permission to perform this action."
    error_code = "FORBIDDEN"


class InsufficientRoleError(OpsPilotException):
    status_code = 403
    detail = "Insufficient role privileges."
    error_code = "INSUFFICIENT_ROLE"


# ── 404 Not Found ────────────────────────────────────────────


class NotFoundError(OpsPilotException):
    status_code = 404
    detail = "Resource not found."
    error_code = "NOT_FOUND"


# ── 409 Conflict ─────────────────────────────────────────────


class ConflictError(OpsPilotException):
    status_code = 409
    detail = "Resource already exists."
    error_code = "CONFLICT"


class DuplicateEmailError(OpsPilotException):
    status_code = 409
    detail = "An account with this email already exists."
    error_code = "DUPLICATE_EMAIL"


class DuplicateSlugError(OpsPilotException):
    status_code = 409
    detail = "A business with this slug already exists."
    error_code = "DUPLICATE_SLUG"


# ── 429 Rate Limit ───────────────────────────────────────────


class RateLimitError(OpsPilotException):
    status_code = 429
    detail = "Too many requests. Please try again later."
    error_code = "RATE_LIMIT"


# ── 503 Service Unavailable ──────────────────────────────────


class ServiceUnavailableError(OpsPilotException):
    status_code = 503
    detail = "Service temporarily unavailable."
    error_code = "SERVICE_UNAVAILABLE"
