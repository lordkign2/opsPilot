"""
OpsPilot — Auth Module: FastAPI Dependencies.

Provides `get_current_user` and role-checking dependencies
for injection into protected routes.
"""

from __future__ import annotations

import uuid
from typing import Annotated

import redis.asyncio as aioredis
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.db.redis import get_redis
from app.db.session import get_db
from app.modules.auth.models import User, UserRole
from app.modules.auth.service import AuthService

# ── Bearer Token Extraction ──────────────────────────────────
security_scheme = HTTPBearer(auto_error=False)


async def get_auth_service(
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> AuthService:
    """Build an AuthService instance with request-scoped dependencies."""
    return AuthService(db=db, redis=redis)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    """
    FastAPI dependency that extracts and validates the JWT from
    the Authorization header, returning the authenticated User.
    """
    if not credentials:
        raise UnauthorizedError("Missing authentication token.")

    return await auth_service.get_current_user(credentials.credentials)


async def get_current_active_user(
    user: User = Depends(get_current_user),
) -> User:
    """Ensures the user is active."""
    if not user.is_active:
        raise ForbiddenError("Your account has been deactivated.")
    return user


# ── Role-Based Access ────────────────────────────────────────


def require_role(*roles: UserRole):
    """
    Dependency factory that restricts access to users with
    specific roles.

    Usage:
        @router.get("/admin-only", dependencies=[Depends(require_role(UserRole.OWNER))])
    """

    async def role_checker(
        user: User = Depends(get_current_active_user),
    ) -> User:
        if user.role not in roles:
            raise ForbiddenError(f"This action requires one of: {', '.join(r.value for r in roles)}")
        return user

    return role_checker


# ── Type Aliases ─────────────────────────────────────────────
CurrentUser = Annotated[User, Depends(get_current_active_user)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


async def get_current_super_admin(
    user: User = Depends(get_current_active_user),
) -> User:
    """Ensures the user has the SUPER_ADMIN role."""
    if user.role != UserRole.SUPER_ADMIN:
        raise ForbiddenError("This endpoint requires super administrative privileges.")
    return user


CurrentSuperAdmin = Annotated[User, Depends(get_current_super_admin)]


async def get_current_business_id(
    user: User = Depends(get_current_active_user),
) -> uuid.UUID:
    """Ensures the user belongs to a business and returns the business ID."""
    if not user.business_id:
        raise ForbiddenError("You must be assigned to a business to perform this action.")
    return user.business_id


CurrentBusinessId = Annotated[uuid.UUID, Depends(get_current_business_id)]
