"""
OpsPilot — Base Repository (Generic CRUD).

Provides a reusable base repository that eliminates boilerplate
across all modules. Every module repository inherits from this
and only adds domain-specific queries.

With 100+ endpoints, this prevents duplicating the same 7 CRUD
methods in every repository file.
"""

from __future__ import annotations

import uuid
from typing import Any, Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

# Generic type for ORM model
ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Generic async repository providing standard CRUD operations.

    Usage:
        class CustomerRepository(BaseRepository[Customer]):
            def __init__(self, db: AsyncSession):
                super().__init__(Customer, db)

            async def search_by_phone(self, phone: str) -> list[Customer]:
                # domain-specific query
                ...
    """

    def __init__(self, model: type[ModelType], db: AsyncSession) -> None:
        self.model = model
        self.db = db

    # ── Single Record ────────────────────────────────────────

    async def get_by_id(self, record_id: uuid.UUID) -> ModelType | None:
        """Fetch a single record by primary key."""
        result = await self.db.execute(select(self.model).where(self.model.id == record_id))
        return result.scalar_one_or_none()

    async def get_by_id_or_raise(self, record_id: uuid.UUID, *, detail: str = "Resource not found.") -> ModelType:
        """Fetch by ID or raise NotFoundError."""
        from app.core.exceptions import NotFoundError

        record = await self.get_by_id(record_id)
        if not record:
            raise NotFoundError(detail)
        return record

    async def get_one_by(self, **filters: Any) -> ModelType | None:
        """Fetch a single record matching arbitrary column filters."""
        stmt = select(self.model)
        for attr, value in filters.items():
            stmt = stmt.where(getattr(self.model, attr) == value)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    # ── Multiple Records ─────────────────────────────────────

    async def get_many(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        order_by: str = "created_at",
        descending: bool = True,
        filters: dict[str, Any] | None = None,
    ) -> list[ModelType]:
        """
        Fetch a paginated list of records with optional filtering.

        Filters are simple equality checks on model columns.
        For complex queries, override in the child repository.
        """
        stmt = select(self.model)

        if filters:
            for attr, value in filters.items():
                if hasattr(self.model, attr):
                    stmt = stmt.where(getattr(self.model, attr) == value)

        col = getattr(self.model, order_by, self.model.created_at)
        stmt = stmt.order_by(col.desc() if descending else col.asc())
        stmt = stmt.offset(offset).limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count(self, *, filters: dict[str, Any] | None = None) -> int:
        """Count records with optional filtering."""
        stmt = select(func.count()).select_from(self.model)

        if filters:
            for attr, value in filters.items():
                if hasattr(self.model, attr):
                    stmt = stmt.where(getattr(self.model, attr) == value)

        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def exists(self, **filters: Any) -> bool:
        """Check if any record matches the given filters."""
        return (await self.count(filters=filters)) > 0

    # ── Write Operations ─────────────────────────────────────

    async def create(self, record: ModelType) -> ModelType:
        """Persist a new record and return it with generated fields."""
        self.db.add(record)
        await self.db.flush()
        await self.db.refresh(record)
        return record

    async def create_many(self, records: list[ModelType]) -> list[ModelType]:
        """Bulk insert multiple records."""
        self.db.add_all(records)
        await self.db.flush()
        for record in records:
            await self.db.refresh(record)
        return records

    async def update(self, record: ModelType, **updates: Any) -> ModelType:
        """
        Apply partial updates to a record.

        Accepts either keyword arguments for field updates,
        or just flushes if the caller has already mutated the object.
        """
        for attr, value in updates.items():
            if hasattr(record, attr):
                setattr(record, attr, value)

        await self.db.flush()
        await self.db.refresh(record)
        return record

    async def delete(self, record: ModelType) -> None:
        """Delete a record."""
        await self.db.delete(record)
        await self.db.flush()

    async def soft_delete(self, record: ModelType) -> ModelType:
        """
        Soft-delete by setting is_active=False (if the model has it).
        Falls back to hard delete if no is_active column.
        """
        if hasattr(record, "is_active"):
            record.is_active = False  # type: ignore
            await self.db.flush()
            await self.db.refresh(record)
            return record
        else:
            await self.delete(record)
            return record

    # ── Scoped Queries (Multi-Tenant) ────────────────────────

    async def get_by_business(
        self,
        business_id: uuid.UUID,
        *,
        offset: int = 0,
        limit: int = 20,
        order_by: str = "created_at",
        descending: bool = True,
        extra_filters: dict[str, Any] | None = None,
    ) -> list[ModelType]:
        """
        Fetch records scoped to a specific business.
        Requires the model to have a `business_id` column.
        """
        filters = {"business_id": business_id}
        if extra_filters:
            filters.update(extra_filters)

        return await self.get_many(
            offset=offset,
            limit=limit,
            order_by=order_by,
            descending=descending,
            filters=filters,
        )

    async def count_by_business(
        self,
        business_id: uuid.UUID,
        *,
        extra_filters: dict[str, Any] | None = None,
    ) -> int:
        """Count records scoped to a business."""
        filters = {"business_id": business_id}
        if extra_filters:
            filters.update(extra_filters)
        return await self.count(filters=filters)
