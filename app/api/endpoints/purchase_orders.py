"""Purchase order resource endpoints."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status



from app.api.middleware.auth import require_scope
from app.db.backend import DataBackend
from app.db.queries import relational
from app.security import AuthenticatedUser, Scopes, filter_rows

router = APIRouter(prefix="/purchase-orders", tags=["purchase-orders"])


def get_backend(request: Request) -> DataBackend:
    """Get the database backend from app state."""
    return request.app.state.backend


@router.get("")
async def list_purchase_orders(
    request: Request,
    user: AuthenticatedUser = Depends(require_scope(Scopes.READ)),
    vendor_id: str | None = Query(None, description="Filter by vendor"),
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    maverick: bool | None = Query(None, description="Filter maverick POs"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
) -> list[dict[str, Any]]:
    """List purchase orders with optional filters."""
    backend = get_backend(request)

    schema = backend._schema if hasattr(backend, "_schema") else "PROCUREMENT"
    clauses = []
    params: list[Any] = []

    if vendor_id:
        clauses.append('"vendor_id" = ?')
        params.append(vendor_id)
    if status_filter:
        clauses.append('"status" = ?')
        params.append(status_filter)
    if maverick is not None:
        clauses.append('"maverick_flag" = ?')
        params.append(1 if maverick else 0)

    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    sql = f'SELECT * FROM "{schema}"."po_header"{where} ORDER BY "po_date" DESC LIMIT ?'
    params.append(limit)

    rows = backend.execute_sql(sql, tuple(params))
    return filter_rows(rows, user.scopes)


@router.get("/{po_id}")
async def get_purchase_order(
    request: Request,
    po_id: str,
    user: AuthenticatedUser = Depends(require_scope(Scopes.READ)),
) -> dict[str, Any]:
    """Get purchase order details by ID."""
    backend = get_backend(request)
    sql, params = relational.po_by_id(po_id)
    rows = backend.execute_sql(sql, params)

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order {po_id} not found",
        )

    filtered = filter_rows(rows, user.scopes)
    return filtered[0]


@router.get("/{po_id}/line-items")
async def get_po_line_items(
    request: Request,
    po_id: str,
    user: AuthenticatedUser = Depends(require_scope(Scopes.READ)),
) -> list[dict[str, Any]]:
    """Get line items for a purchase order."""
    backend = get_backend(request)

    schema = backend._schema if hasattr(backend, "_schema") else "PROCUREMENT"
    sql = f'SELECT * FROM "{schema}"."po_line_item" WHERE "po_id" = ? ORDER BY "po_line_number"'
    rows = backend.execute_sql(sql, (po_id,))
    return filter_rows(rows, user.scopes)
