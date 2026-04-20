"""JWT authentication middleware and dependencies."""
from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status

from app.config import settings
from app.security.jwt import AuthenticatedUser, decode_jwt, extract_token
from app.security.scopes import Scopes


async def get_current_user(request: Request) -> AuthenticatedUser:
    """FastAPI dependency to get the current authenticated user.

    Extracts and validates JWT from Authorization header.
    """
    # Skip auth for development if configured
    if settings.skip_auth:
        return AuthenticatedUser(
            sub="dev-user",
            email="dev@example.com",
            scopes=[
                Scopes.READ,
                Scopes.CONTRACTS_READ,
                Scopes.FINANCE_READ,
                Scopes.TRANSACTIONS_READ,
                Scopes.SPEND_READ,
                Scopes.RESTRICTED_READ,
            ],
        )

    token = extract_token(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return decode_jwt(token)


def require_scope(required_scope: str):
    """Create a dependency that requires a specific scope.

    Usage:
        @router.get("/invoices")
        async def list_invoices(
            user: AuthenticatedUser = Depends(require_scope("procurement.finance.read"))
        ):
            ...
    """

    async def scope_checker(
        user: AuthenticatedUser = Depends(get_current_user),
    ) -> AuthenticatedUser:
        if not user.has_scope(required_scope):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required scope: {required_scope}",
            )
        return user

    return scope_checker


# Pre-built scope checkers for common scopes
require_read = require_scope(Scopes.READ)
require_contracts_read = require_scope(Scopes.CONTRACTS_READ)
require_finance_read = require_scope(Scopes.FINANCE_READ)
require_transactions_read = require_scope(Scopes.TRANSACTIONS_READ)
require_spend_read = require_scope(Scopes.SPEND_READ)
