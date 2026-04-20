"""Material resource endpoints."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status



from app.api.middleware.auth import require_scope
from app.db.backend import DataBackend
from app.db.queries import relational
from app.security import AuthenticatedUser, Scopes, filter_rows

router = APIRouter(prefix="/materials", tags=["materials"])


def get_backend(request: Request) -> DataBackend:
    """Get the database backend from app state."""
    return request.app.state.backend


@router.get("")
async def list_materials(
    request: Request,
    user: AuthenticatedUser = Depends(require_scope(Scopes.READ)),
    category_id: str | None = Query(None, description="Filter by category"),
    material_type: str | None = Query(None, description="Filter by material type"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
) -> list[dict[str, Any]]:
    """List materials with optional filters."""
    backend = get_backend(request)

    # Build dynamic query
    schema = backend._schema if hasattr(backend, "_schema") else "PROCUREMENT"
    clauses = []
    params: list[Any] = []

    if category_id:
        clauses.append('"category_id" = ?')
        params.append(category_id)
    if material_type:
        clauses.append('"material_type" = ?')
        params.append(material_type)

    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    sql = f'SELECT * FROM "{schema}"."material_master"{where} LIMIT ?'
    params.append(limit)

    rows = backend.execute_sql(sql, tuple(params))
    return filter_rows(rows, user.scopes)


@router.get("/{material_id}")
async def get_material(
    request: Request,
    material_id: str,
    user: AuthenticatedUser = Depends(require_scope(Scopes.READ)),
) -> dict[str, Any]:
    """Get material details by ID."""
    backend = get_backend(request)
    sql, params = relational.material_by_id(material_id)
    rows = backend.execute_sql(sql, params)

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Material {material_id} not found",
        )

    filtered = filter_rows(rows, user.scopes)
    return filtered[0]


@router.get("/{material_id}/vendors")
async def get_material_vendors(
    request: Request,
    material_id: str,
    user: AuthenticatedUser = Depends(require_scope(Scopes.READ)),
) -> list[dict[str, Any]]:
    """Get vendors that supply a material."""
    backend = get_backend(request)
    sql, params = relational.vendors_for_material(material_id)
    rows = backend.execute_sql(sql, params)
    return filter_rows(rows, user.scopes)
