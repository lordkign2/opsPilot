"""
OpsPilot — Shared FastAPI Dependencies.

Global dependencies used across multiple modules.
Module-specific dependencies live in their own `dependencies.py`.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

# Type alias for the DB session dependency
DBSession = Annotated[AsyncSession, Depends(get_db)]
