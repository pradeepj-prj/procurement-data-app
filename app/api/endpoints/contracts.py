"""Contract resource endpoints."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status



from app.api.middleware.auth import require_scope
from app.db.backend import DataBackend
from app.db.queries import relational
from app.security import AuthenticatedUser, Scopes, filter_rows

router = APIRouter(prefix="/contracts", tags=["contracts"])


def get_backend(request: Request) -> DataBackend:
    """Get the database backend from app state."""
    return request.app.state.backend


@router.get("")
async def list_contracts(
    request: Request,
    user: AuthenticatedUser = Depends(require_scope(Scopes.CONTRACTS_READ)),
    vendor_id: str | None = Query(None, description="Filter by vendor"),
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
) -> list[dict[str, Any]]:
    """List contracts with optional filters."""
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

    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    sql = f'SELECT * FROM "{schema}"."contract_header"{where} ORDER BY "valid_from" DESC LIMIT ?'
    params.append(limit)

    rows = backend.execute_sql(sql, tuple(params))
    return filter_rows(rows, user.scopes)


@router.get("/{contract_id}")
async def get_contract(
    request: Request,
    contract_id: str,
    user: AuthenticatedUser = Depends(require_scope(Scopes.CONTRACTS_READ)),
) -> dict[str, Any]:
    """Get contract details by ID."""
    backend = get_backend(request)
    sql, params = relational.contract_by_id(contract_id)
    rows = backend.execute_sql(sql, params)

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract {contract_id} not found",
        )

    filtered = filter_rows(rows, user.scopes)
    return filtered[0]
