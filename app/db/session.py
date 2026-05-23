"""
OpsPilot — Async Database Session Management.

Creates the async engine, session factory, and provides a
FastAPI-compatible dependency for per-request sessions.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

settings = get_settings()

# ── Engine ───────────────────────────────────────────────────
engine = create_async_engine(
    settings.DATABASE_URL.get_secret_value(),
    echo=settings.DATABASE_ECHO,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
    pool_recycle=300,
)

# ── Session Factory ──────────────────────────────────────────
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# ── Dependency ───────────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields a database session.

    The session is automatically closed when the request ends.
    Callers should commit explicitly in the service layer.
    """
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
