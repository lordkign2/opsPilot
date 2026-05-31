"""
OpsPilot — Auth Module: Service Layer.

All business logic for authentication lives here.
Routes call services; services call repositories.
"""

from __future__ import annotations

import uuid

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import event_bus
from app.core.exceptions import (
    DuplicateEmailError,
    InvalidCredentialsError,
    InvalidTokenError,
    NotFoundError,
    UnauthorizedError,
)
from app.core.logging import get_logger
from app.core.security import (
    JWTError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.modules.auth.models import User, UserRole
from app.modules.auth.repository import UserRepository
from app.modules.auth.schemas import (
    ChangePasswordRequest,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)

logger = get_logger("auth.service")


class AuthService:
    """Authentication and user management business logic."""

    def __init__(
        self,
        db: AsyncSession,
        redis: aioredis.Redis | None = None,
    ) -> None:
        self.db = db
        self.repo = UserRepository(db)
        self.redis = redis

    # ── Registration ─────────────────────────────────────────

    async def register(self, payload: RegisterRequest) -> tuple[User, TokenResponse]:
        """
        Register a new user and their business.

        Flow:
        1. Check email uniqueness
        2. Create Business record
        3. Create User record (OWNER role, linked to business)
        4. Generate tokens
        5. Emit 'user.registered' event
        """
        if await self.repo.email_exists(payload.email):
            raise DuplicateEmailError()

        # Import here to avoid circular imports at module level
        from app.modules.businesses.models import Business
        from app.modules.businesses.repository import BusinessRepository

        business_repo = BusinessRepository(self.db)

        # Create the business
        business = Business(
            name=payload.business_name,
            slug=self._generate_slug(payload.business_name),
            industry=payload.industry,
        )
        business = await business_repo.create(business)

        # Create the user
        user = User(
            email=payload.email.lower(),
            password_hash=hash_password(payload.password),
            first_name=payload.first_name,
            last_name=payload.last_name,
            phone=payload.phone,
            role=UserRole.OWNER,
            business_id=business.id,
            is_active=True,
            is_verified=False,
        )
        user = await self.repo.create(user)

        # Link business owner
        business.owner_id = user.id
        await self.db.flush()

        await self.db.commit()

        # Generate tokens
        tokens = self._generate_tokens(user)

        # Emit event
        await event_bus.emit(
            "user.registered",
            {
                "user_id": str(user.id),
                "email": user.email,
                "business_id": str(business.id),
            },
            source_module="auth",
        )

        logger.info("User registered: %s (business: %s)", user.email, business.name)
        return user, tokens

    # ── Login ────────────────────────────────────────────────

    async def login(self, payload: LoginRequest) -> tuple[User, TokenResponse]:
        """
        Authenticate a user with email/password.

        Returns the user and a token pair.
        """
        user = await self.repo.get_by_email(payload.email)
        if not user or user.deleted_at is not None:
            raise InvalidCredentialsError()

        if not verify_password(payload.password, user.password_hash):
            raise InvalidCredentialsError()

        if not user.is_active:
            raise UnauthorizedError("Your account has been deactivated.")

        tokens = self._generate_tokens(user)

        await event_bus.emit(
            "user.logged_in",
            {"user_id": str(user.id), "email": user.email},
            source_module="auth",
        )

        logger.info("User logged in: %s", user.email)
        return user, tokens

    # ── Token Refresh ────────────────────────────────────────

    async def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        """
        Issue a new token pair using a valid refresh token.
        The old refresh token is blacklisted.
        """
        try:
            payload = decode_token(refresh_token)
        except JWTError as e:
            raise InvalidTokenError() from e

        if payload.get("type") != "refresh":
            raise InvalidTokenError("Expected a refresh token.")

        # Check if token is blacklisted
        if await self._is_token_blacklisted(refresh_token):
            raise InvalidTokenError("Token has been revoked.")

        user_id = payload.get("sub")
        if not user_id:
            raise InvalidTokenError()

        user = await self.repo.get_by_id(uuid.UUID(user_id))
        if not user or not user.is_active:
            raise UnauthorizedError()

        # Blacklist old refresh token
        await self._blacklist_token(refresh_token, payload)

        return self._generate_tokens(user)

    # ── Logout ───────────────────────────────────────────────

    async def logout(self, access_token: str, refresh_token: str | None = None) -> None:
        """
        Blacklist the current access token (and optionally the refresh token).
        """
        try:
            payload = decode_token(access_token)
            await self._blacklist_token(access_token, payload)
        except JWTError:
            pass  # Token already expired, nothing to blacklist

        if refresh_token:
            try:
                payload = decode_token(refresh_token)
                await self._blacklist_token(refresh_token, payload)
            except JWTError:
                pass

    # ── Get Current User ─────────────────────────────────────

    async def get_current_user(self, token: str) -> User:
        """Decode a token and return the associated user."""
        try:
            payload = decode_token(token)
        except JWTError as e:
            raise InvalidTokenError() from e

        if payload.get("type") != "access":
            raise InvalidTokenError("Expected an access token.")

        if await self._is_token_blacklisted(token):
            raise InvalidTokenError("Token has been revoked.")

        user_id = payload.get("sub")
        if not user_id:
            raise InvalidTokenError()

        user = await self.repo.get_by_id(uuid.UUID(user_id))
        if not user or user.deleted_at is not None:
            raise NotFoundError("User not found.")
        if not user.is_active:
            raise UnauthorizedError("Account deactivated.")
        if user.business and user.business.deleted_at is not None:
            raise UnauthorizedError("Business workspace has been deleted.")

        # Set user and business logging context variables for trace decor
        from app.core.logging import business_id_ctx, user_id_ctx

        user_id_ctx.set(str(user.id))
        business_id_ctx.set(str(user.business_id) if user.business_id else None)

        return user

    # ── Change Password ──────────────────────────────────────

    async def change_password(self, user: User, payload: ChangePasswordRequest) -> None:
        """Change a user's password after verifying the current one."""
        if not verify_password(payload.current_password, user.password_hash):
            raise InvalidCredentialsError("Current password is incorrect.")

        user.password_hash = hash_password(payload.new_password)
        await self.repo.update(user)
        await self.db.commit()

        logger.info("Password changed for user: %s", user.email)

    # ── Private Helpers ──────────────────────────────────────

    def _generate_tokens(self, user: User) -> TokenResponse:
        """Create an access + refresh token pair for a user."""
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value,
            "business_id": str(user.business_id) if user.business_id else None,
        }
        return TokenResponse(
            access_token=create_access_token(token_data),
            refresh_token=create_refresh_token(token_data),
        )

    async def _blacklist_token(self, token: str, payload: dict) -> None:
        """Add a token to the Redis blacklist with TTL matching its expiry."""
        if not self.redis:
            logger.warning("Redis client is not configured; skipping token blacklisting.")
            return

        import time

        exp = payload.get("exp", 0)
        ttl = max(int(exp - time.time()), 0)
        if ttl > 0:
            await self.redis.setex(f"blacklist:{token}", ttl, "1")

    async def _is_token_blacklisted(self, token: str) -> bool:
        """Check if a token has been blacklisted."""
        if not self.redis:
            return False
        return bool(await self.redis.get(f"blacklist:{token}"))

    @staticmethod
    def _generate_slug(name: str) -> str:
        """Generate a URL-safe slug from a business name."""
        import re

        slug = name.lower().strip()
        slug = re.sub(r"[^\w\s-]", "", slug)
        slug = re.sub(r"[\s_]+", "-", slug)
        slug = re.sub(r"-+", "-", slug).strip("-")
        # Add a short random suffix for uniqueness
        slug = f"{slug}-{uuid.uuid4().hex[:6]}"
        return slug
