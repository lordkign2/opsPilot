"""
OpsPilot — CORS Middleware Configuration.

Configures Cross-Origin Resource Sharing based on env settings.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings


def add_cors_middleware(app: FastAPI) -> None:
    """Attach CORS middleware to the FastAPI application."""
    settings = get_settings()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )
