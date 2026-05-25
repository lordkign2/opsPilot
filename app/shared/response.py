"""
OpsPilot — Standardised API Response Envelope.

Every API response follows a consistent shape:
{
    "success": true,
    "message": "...",
    "data": { ... },
    "meta": { ... }
}
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginationMeta(BaseModel):
    """Pagination metadata included in list responses."""

    page: int
    per_page: int
    total: int
    total_pages: int


class APIResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""

    success: bool = True
    message: str = "Request successful."
    data: T | None = None
    meta: dict[str, Any] | None = None


def success_response(
    data: Any = None,
    message: str = "Request successful.",
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a success response dict."""
    return {
        "success": True,
        "message": message,
        "data": data,
        "meta": meta,
    }


def error_response(
    message: str = "An error occurred.",
    error_code: str = "ERROR",
    details: Any = None,
) -> dict[str, Any]:
    """Build an error response dict."""
    return {
        "success": False,
        "message": message,
        "error_code": error_code,
        "details": details,
    }


def paginated_response(
    data: list[Any],
    total: int,
    page: int,
    per_page: int,
    message: str = "Request successful.",
) -> dict[str, Any]:
    """Build a paginated list response."""
    total_pages = (total + per_page - 1) // per_page if per_page > 0 else 0
    return {
        "success": True,
        "message": message,
        "data": data,
        "meta": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
        },
    }
