"""JWT validation and decoding."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import jwt
from fastapi import HTTPException, Request, status

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class AuthenticatedUser:
    """Decoded JWT claims for an authenticated user."""

    sub: str  # Subject (user ID)
    email: str | None = None
    scopes: list[str] = field(default_factory=list)
    raw_token: str = ""
    claims: dict[str, Any] = field(default_factory=dict)

    def has_scope(self, scope: str) -> bool:
        """Check if user has a specific scope."""
        return scope in self.scopes or "admin" in self.scopes


def decode_jwt(token: str) -> AuthenticatedUser:
    """Decode and validate a JWT token.

    For local development, uses JWT_SECRET from settings.
    In production with XSUAA, would validate against XSUAA public keys.
    """
    try:
        # For local dev, decode with secret
        # In production, this would verify against XSUAA keys
        if settings.jwt_secret:
            payload = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=["HS256"],
            )
        else:
            # No secret configured - decode without verification (dev only)
            logger.warning("JWT_SECRET not set - accepting tokens without verification")
            payload = jwt.decode(token, options={"verify_signature": False})

        # Extract scopes - XSUAA uses "scope" claim
        scopes = payload.get("scope", [])
        if isinstance(scopes, str):
            scopes = scopes.split()

        return AuthenticatedUser(
            sub=payload.get("sub", "unknown"),
            email=payload.get("email"),
            scopes=scopes,
            raw_token=token,
            claims=payload,
        )

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
        )


def extract_token(request: Request) -> str | None:
    """Extract bearer token from Authorization header."""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    return parts[1]
