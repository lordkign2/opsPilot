"""
OpsPilot — Auth Module: HTTP Routes.

All authentication endpoints.
Routes are thin — they delegate to the AuthService.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header

from app.modules.auth.dependencies import (
    AuthServiceDep,
    CurrentUser,
)
from app.modules.auth.schemas import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    UserResponse,
)
from app.shared.response import success_response

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ── POST /register ───────────────────────────────────────────


@router.post(
    "/register",
    response_model=None,
    status_code=201,
    summary="Register a new user and business",
)
async def register(
    payload: RegisterRequest,
    auth_service: AuthServiceDep,
) -> Any:
    """
    Create a new user account along with a business workspace.
    Returns the user profile and JWT tokens.
    """
    user, tokens = await auth_service.register(payload)
    return success_response(
        data={
            "user": UserResponse.model_validate(user).model_dump(mode="json"),
            "tokens": tokens.model_dump(),
        },
        message="Registration successful.",
    )


# ── POST /login ──────────────────────────────────────────────


@router.post(
    "/login",
    response_model=None,
    summary="Authenticate with email and password",
)
async def login(
    payload: LoginRequest,
    auth_service: AuthServiceDep,
) -> Any:
    """Authenticate a user and return JWT tokens."""
    user, tokens = await auth_service.login(payload)
    return success_response(
        data={
            "user": UserResponse.model_validate(user).model_dump(mode="json"),
            "tokens": tokens.model_dump(),
        },
        message="Login successful.",
    )


# ── POST /refresh ────────────────────────────────────────────


@router.post(
    "/refresh",
    response_model=None,
    summary="Refresh access token",
)
async def refresh_token(
    payload: RefreshTokenRequest,
    auth_service: AuthServiceDep,
) -> Any:
    """Exchange a valid refresh token for a new token pair."""
    tokens = await auth_service.refresh_tokens(payload.refresh_token)
    return success_response(
        data=tokens.model_dump(),
        message="Tokens refreshed.",
    )


# ── POST /logout ─────────────────────────────────────────────


@router.post(
    "/logout",
    response_model=None,
    summary="Logout and invalidate tokens",
)
async def logout(
    auth_service: AuthServiceDep,
    authorization: str = Header(..., alias="Authorization"),
    payload: RefreshTokenRequest | None = None,
) -> Any:
    """Blacklist the current access token and optionally the refresh token."""
    # Extract bearer token
    token = authorization.replace("Bearer ", "").strip()
    refresh = payload.refresh_token if payload else None

    await auth_service.logout(access_token=token, refresh_token=refresh)
    return success_response(message="Logged out successfully.")


# ── GET /me ──────────────────────────────────────────────────


@router.get(
    "/me",
    response_model=None,
    summary="Get current user profile",
)
async def get_me(current_user: CurrentUser) -> Any:
    """Return the authenticated user's profile."""
    return success_response(
        data=UserResponse.model_validate(current_user).model_dump(mode="json"),
    )


# ── PUT /change-password ─────────────────────────────────────


@router.put(
    "/change-password",
    response_model=None,
    summary="Change current user's password",
)
async def change_password(
    payload: ChangePasswordRequest,
    current_user: CurrentUser,
    auth_service: AuthServiceDep,
) -> Any:
    """Change the authenticated user's password."""
    await auth_service.change_password(current_user, payload)
    return success_response(message="Password changed successfully.")
