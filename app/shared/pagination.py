"""
OpsPilot — Pagination Utilities.

Offset-based pagination parameters extracted from query strings.
"""

from __future__ import annotations

from fastapi import Query


class PaginationParams:
    """
    Common pagination query parameters.

    Usage in routes:
        async def list_items(pagination: PaginationParams = Depends()):
            ...
    """

    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number (1-indexed)"),
        per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    ) -> None:
        self.page = page
        self.per_page = per_page

    @property
    def offset(self) -> int:
        """Calculate the SQL OFFSET value."""
        return (self.page - 1) * self.per_page

    @property
    def limit(self) -> int:
        """Alias for per_page, used as SQL LIMIT."""
        return self.per_page
