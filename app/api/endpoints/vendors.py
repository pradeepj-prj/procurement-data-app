"""Vendor resource endpoints."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.api.middleware.auth import require_scope
from app.db.backend import DataBackend
from app.db.queries import relational
from app.security import AuthenticatedUser, Scopes, filter_rows

router = APIRouter(prefix="/vendors", tags=["vendors"])


def get_backend(request: Request) -> DataBackend:
    """Get the database backend from app state."""
    return request.app.state.backend


@router.get("")
async def list_vendors(
    request: Request,
    user: AuthenticatedUser = Depends(require_scope(Scopes.READ)),
    risk_score_gte: int | None = Query(None, description="Minimum risk score"),
    country: str | None = Query(None, description="Filter by country"),
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
) -> list[dict[str, Any]]:
    """List vendors with optional filters."""
    backend = get_backend(request)
    sql, params = relational.filter_vendors(
        min_risk_score=risk_score_gte,
        country=country,
        status=status_filter,
        limit=limit,
    )
    rows = backend.execute_sql(sql, params)
    return filter_rows(rows, user.scopes)


@router.get("/{vendor_id}")
async def get_vendor(
    request: Request,
    vendor_id: str,
    user: AuthenticatedUser = Depends(require_scope(Scopes.READ)),
) -> dict[str, Any]:
    """Get vendor details by ID."""
    backend = get_backend(request)
    sql, params = relational.vendor_by_id(vendor_id)
    rows = backend.execute_sql(sql, params)

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vendor {vendor_id} not found",
        )

    filtered = filter_rows(rows, user.scopes)
    return filtered[0]


@router.get("/{vendor_id}/materials")
async def get_vendor_materials(
    request: Request,
    vendor_id: str,
    user: AuthenticatedUser = Depends(require_scope(Scopes.READ)),
) -> list[dict[str, Any]]:
    """Get materials supplied by a vendor."""
    backend = get_backend(request)
    sql, params = relational.materials_for_vendor(vendor_id)
    rows = backend.execute_sql(sql, params)
    return filter_rows(rows, user.scopes)


@router.get("/{vendor_id}/contracts")
async def get_vendor_contracts(
    request: Request,
    vendor_id: str,
    user: AuthenticatedUser = Depends(require_scope(Scopes.CONTRACTS_READ)),
) -> list[dict[str, Any]]:
    """Get contracts with a vendor."""
    backend = get_backend(request)
    sql, params = relational.contracts_for_vendor(vendor_id)
    rows = backend.execute_sql(sql, params)
    return filter_rows(rows, user.scopes)


@router.get("/{vendor_id}/purchase-orders")
async def get_vendor_purchase_orders(
    request: Request,
    vendor_id: str,
    user: AuthenticatedUser = Depends(require_scope(Scopes.READ)),
) -> list[dict[str, Any]]:
    """Get purchase orders to a vendor."""
    backend = get_backend(request)
    sql, params = relational.pos_for_vendor(vendor_id)
    rows = backend.execute_sql(sql, params)
    return filter_rows(rows, user.scopes)
