"""Invoice resource endpoints."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status



from app.api.middleware.auth import require_scope
from app.db.backend import DataBackend
from app.security import AuthenticatedUser, Scopes, filter_rows

router = APIRouter(prefix="/invoices", tags=["invoices"])


def get_backend(request: Request) -> DataBackend:
    """Get the database backend from app state."""
    return request.app.state.backend


@router.get("")
async def list_invoices(
    request: Request,
    user: AuthenticatedUser = Depends(require_scope(Scopes.FINANCE_READ)),
    vendor_id: str | None = Query(None, description="Filter by vendor"),
    match_status: str | None = Query(None, description="Filter by match status"),
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
) -> list[dict[str, Any]]:
    """List invoices with optional filters."""
    backend = get_backend(request)

    schema = backend._schema if hasattr(backend, "_schema") else "PROCUREMENT"
    clauses = []
    params: list[Any] = []

    if vendor_id:
        clauses.append('"vendor_id" = ?')
        params.append(vendor_id)
    if match_status:
        clauses.append('"match_status" = ?')
        params.append(match_status)
    if status_filter:
        clauses.append('"status" = ?')
        params.append(status_filter)

    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    sql = f'SELECT * FROM "{schema}"."invoice_header"{where} ORDER BY "invoice_date" DESC LIMIT ?'
    params.append(limit)

    rows = backend.execute_sql(sql, tuple(params))
    return filter_rows(rows, user.scopes)


@router.get("/{invoice_id}")
async def get_invoice(
    request: Request,
    invoice_id: str,
    user: AuthenticatedUser = Depends(require_scope(Scopes.FINANCE_READ)),
) -> dict[str, Any]:
    """Get invoice details by ID."""
    backend = get_backend(request)

    schema = backend._schema if hasattr(backend, "_schema") else "PROCUREMENT"
    sql = f'SELECT * FROM "{schema}"."invoice_header" WHERE "invoice_id" = ?'
    rows = backend.execute_sql(sql, (invoice_id,))

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )

    filtered = filter_rows(rows, user.scopes)
    return filtered[0]
