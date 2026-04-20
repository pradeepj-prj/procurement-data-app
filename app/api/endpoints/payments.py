"""Payment resource endpoints."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status



from app.api.middleware.auth import require_scope
from app.db.backend import DataBackend
from app.security import AuthenticatedUser, Scopes, filter_rows

router = APIRouter(prefix="/payments", tags=["payments"])


def get_backend(request: Request) -> DataBackend:
    """Get the database backend from app state."""
    return request.app.state.backend


@router.get("")
async def list_payments(
    request: Request,
    user: AuthenticatedUser = Depends(require_scope(Scopes.FINANCE_READ)),
    vendor_id: str | None = Query(None, description="Filter by vendor"),
    payment_method: str | None = Query(None, description="Filter by payment method"),
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
) -> list[dict[str, Any]]:
    """List payments with optional filters."""
    backend = get_backend(request)

    schema = backend._schema if hasattr(backend, "_schema") else "PROCUREMENT"
    clauses = []
    params: list[Any] = []

    if vendor_id:
        clauses.append('"vendor_id" = ?')
        params.append(vendor_id)
    if payment_method:
        clauses.append('"payment_method" = ?')
        params.append(payment_method)
    if status_filter:
        clauses.append('"status" = ?')
        params.append(status_filter)

    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    sql = f'SELECT * FROM "{schema}"."payment"{where} ORDER BY "payment_date" DESC LIMIT ?'
    params.append(limit)

    rows = backend.execute_sql(sql, tuple(params))
    return filter_rows(rows, user.scopes)


@router.get("/{payment_id}")
async def get_payment(
    request: Request,
    payment_id: str,
    user: AuthenticatedUser = Depends(require_scope(Scopes.FINANCE_READ)),
) -> dict[str, Any]:
    """Get payment details by ID."""
    backend = get_backend(request)

    schema = backend._schema if hasattr(backend, "_schema") else "PROCUREMENT"
    sql = f'SELECT * FROM "{schema}"."payment" WHERE "payment_id" = ?'
    rows = backend.execute_sql(sql, (payment_id,))

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment {payment_id} not found",
        )

    filtered = filter_rows(rows, user.scopes)
    return filtered[0]
