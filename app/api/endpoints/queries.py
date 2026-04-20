"""Query endpoints for complex procurement patterns."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.api.middleware.auth import require_scope
from app.config import settings
from app.db.backend import DataBackend
from app.db.queries import relational
from app.security import AuthenticatedUser, Scopes, filter_rows

router = APIRouter(prefix="/queries", tags=["queries"])


def get_backend(request: Request) -> DataBackend:
    """Get the database backend from app state."""
    return request.app.state.backend


@router.get("/p2p-chain/{po_id}")
async def get_p2p_chain(
    request: Request,
    po_id: str,
    user: AuthenticatedUser = Depends(require_scope(Scopes.TRANSACTIONS_READ)),
) -> dict[str, Any]:
    """Get the full procure-to-pay chain for a PO.

    Returns: PO → Goods Receipts → Invoices → Payments
    """
    backend = get_backend(request)
    schema = settings.hana_schema

    # Get PO header
    po_sql, po_params = relational.po_by_id(po_id)
    po_rows = backend.execute_sql(po_sql, po_params)
    if not po_rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order {po_id} not found",
        )

    # Get Goods Receipts for PO
    gr_sql = f'SELECT * FROM "{schema}"."gr_header" WHERE "PO_ID" = ?'
    gr_rows = backend.execute_sql(gr_sql, (po_id,))

    # Get Invoices for PO
    inv_sql = f'SELECT * FROM "{schema}"."invoice_header" WHERE "PO_ID" = ?'
    inv_rows = backend.execute_sql(inv_sql, (po_id,))

    # Get Payments for those invoices
    invoice_ids = [inv["INVOICE_ID"] for inv in inv_rows] if inv_rows else []
    pay_rows = []
    if invoice_ids:
        placeholders = ",".join(["?" for _ in invoice_ids])
        pay_sql = f'''
            SELECT p.* FROM "{schema}"."payment" p
            JOIN "{schema}"."payment_invoice_link" pil ON pil."PAYMENT_ID" = p."PAYMENT_ID"
            WHERE pil."INVOICE_ID" IN ({placeholders})
        '''
        pay_rows = backend.execute_sql(pay_sql, tuple(invoice_ids))

    return {
        "purchase_order": filter_rows(po_rows, user.scopes)[0],
        "goods_receipts": filter_rows(gr_rows, user.scopes),
        "invoices": filter_rows(inv_rows, user.scopes),
        "payments": filter_rows(pay_rows, user.scopes),
    }


@router.get("/spend-by-vendor")
async def get_spend_by_vendor(
    request: Request,
    user: AuthenticatedUser = Depends(require_scope(Scopes.SPEND_READ)),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
) -> list[dict[str, Any]]:
    """Get aggregated PO spend by vendor, ordered by total spend descending."""
    backend = get_backend(request)
    sql, params = relational.spend_by_vendor(limit)
    rows = backend.execute_sql(sql, params)
    return filter_rows(rows, user.scopes)


@router.get("/spend-by-category")
async def get_spend_by_category(
    request: Request,
    user: AuthenticatedUser = Depends(require_scope(Scopes.SPEND_READ)),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
) -> list[dict[str, Any]]:
    """Get aggregated PO line item spend by category."""
    backend = get_backend(request)
    schema = settings.hana_schema

    sql = f'''
        SELECT
            ch."CATEGORY_ID",
            ch."CATEGORY_NAME",
            ch."LEVEL",
            SUM(li."NET_VALUE") AS "TOTAL_SPEND",
            COUNT(DISTINCT li."PO_ID") AS "PO_COUNT",
            COUNT(*) AS "LINE_ITEM_COUNT"
        FROM "{schema}"."po_line_item" li
        JOIN "{schema}"."material_master" m ON m."MATERIAL_ID" = li."MATERIAL_ID"
        JOIN "{schema}"."category_hierarchy" ch ON ch."CATEGORY_ID" = m."CATEGORY_ID"
        GROUP BY ch."CATEGORY_ID", ch."CATEGORY_NAME", ch."LEVEL"
        ORDER BY "TOTAL_SPEND" DESC
        LIMIT ?
    '''
    rows = backend.execute_sql(sql, (limit,))
    return filter_rows(rows, user.scopes)


@router.get("/materials-for-plant/{plant_id}")
async def get_materials_for_plant(
    request: Request,
    plant_id: str,
    user: AuthenticatedUser = Depends(require_scope(Scopes.READ)),
) -> list[dict[str, Any]]:
    """Get materials sourced at a specific plant."""
    backend = get_backend(request)
    schema = settings.hana_schema

    sql = f'''
        SELECT DISTINCT m.*
        FROM "{schema}"."material_master" m
        JOIN "{schema}"."source_list" s ON s."MATERIAL_ID" = m."MATERIAL_ID"
        WHERE s."PLANT_ID" = ?
    '''
    rows = backend.execute_sql(sql, (plant_id,))
    return filter_rows(rows, user.scopes)


@router.get("/category-tree/{category_id}")
async def get_category_tree(
    request: Request,
    category_id: str,
    user: AuthenticatedUser = Depends(require_scope(Scopes.READ)),
) -> dict[str, Any]:
    """Get category hierarchy and materials for a category."""
    backend = get_backend(request)
    schema = settings.hana_schema

    # Get the category
    cat_sql = f'SELECT * FROM "{schema}"."category_hierarchy" WHERE "CATEGORY_ID" = ?'
    cat_rows = backend.execute_sql(cat_sql, (category_id,))
    if not cat_rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category {category_id} not found",
        )

    # Get child categories
    children_sql = f'SELECT * FROM "{schema}"."category_hierarchy" WHERE "PARENT_CATEGORY_ID" = ?'
    children_rows = backend.execute_sql(children_sql, (category_id,))

    # Get materials in this category
    materials_sql = f'SELECT * FROM "{schema}"."material_master" WHERE "CATEGORY_ID" = ?'
    materials_rows = backend.execute_sql(materials_sql, (category_id,))

    return {
        "category": filter_rows(cat_rows, user.scopes)[0],
        "children": filter_rows(children_rows, user.scopes),
        "materials": filter_rows(materials_rows, user.scopes),
    }


@router.get("/invoice-aging")
async def get_invoice_aging(
    request: Request,
    user: AuthenticatedUser = Depends(require_scope(Scopes.FINANCE_READ)),
) -> list[dict[str, Any]]:
    """Get invoice counts grouped by match status and age buckets."""
    backend = get_backend(request)
    schema = settings.hana_schema

    sql = f'''
        SELECT
            "MATCH_STATUS",
            "STATUS",
            COUNT(*) AS "INVOICE_COUNT",
            SUM("TOTAL_NET_AMOUNT") AS "TOTAL_AMOUNT"
        FROM "{schema}"."invoice_header"
        GROUP BY "MATCH_STATUS", "STATUS"
        ORDER BY "INVOICE_COUNT" DESC
    '''
    rows = backend.execute_sql(sql, ())
    return filter_rows(rows, user.scopes)


@router.get("/overdue-invoices")
async def get_overdue_invoices(
    request: Request,
    user: AuthenticatedUser = Depends(require_scope(Scopes.FINANCE_READ)),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
) -> list[dict[str, Any]]:
    """Get invoices that are past due date and not fully paid."""
    backend = get_backend(request)
    schema = settings.hana_schema

    sql = f'''
        SELECT i.*, v."VENDOR_NAME"
        FROM "{schema}"."invoice_header" i
        JOIN "{schema}"."vendor_master" v ON v."VENDOR_ID" = i."VENDOR_ID"
        WHERE i."DUE_DATE" < CURRENT_DATE
          AND i."STATUS" != 'PAID'
        ORDER BY i."DUE_DATE" ASC
        LIMIT ?
    '''
    rows = backend.execute_sql(sql, (limit,))
    return filter_rows(rows, user.scopes)


@router.get("/invoice-context/{invoice_id}")
async def get_invoice_context(
    request: Request,
    invoice_id: str,
    user: AuthenticatedUser = Depends(require_scope(Scopes.FINANCE_READ)),
) -> dict[str, Any]:
    """Get full context for an invoice: PO, GR, payments, vendor."""
    backend = get_backend(request)
    schema = settings.hana_schema

    # Get invoice
    inv_sql = f'SELECT * FROM "{schema}"."invoice_header" WHERE "INVOICE_ID" = ?'
    inv_rows = backend.execute_sql(inv_sql, (invoice_id,))
    if not inv_rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )

    invoice = inv_rows[0]
    po_id = invoice.get("PO_ID")
    vendor_id = invoice.get("VENDOR_ID")

    # Get related PO
    po_rows = []
    if po_id:
        po_sql, po_params = relational.po_by_id(po_id)
        po_rows = backend.execute_sql(po_sql, po_params)

    # Get GRs for the PO
    gr_rows = []
    if po_id:
        gr_sql = f'SELECT * FROM "{schema}"."gr_header" WHERE "PO_ID" = ?'
        gr_rows = backend.execute_sql(gr_sql, (po_id,))

    # Get vendor
    vendor_rows = []
    if vendor_id:
        vendor_sql, vendor_params = relational.vendor_by_id(vendor_id)
        vendor_rows = backend.execute_sql(vendor_sql, vendor_params)

    # Get payments for this invoice
    pay_sql = f'''
        SELECT p.* FROM "{schema}"."payment" p
        JOIN "{schema}"."payment_invoice_link" pil ON pil."PAYMENT_ID" = p."PAYMENT_ID"
        WHERE pil."INVOICE_ID" = ?
    '''
    pay_rows = backend.execute_sql(pay_sql, (invoice_id,))

    return {
        "invoice": filter_rows(inv_rows, user.scopes)[0],
        "purchase_order": filter_rows(po_rows, user.scopes)[0] if po_rows else None,
        "goods_receipts": filter_rows(gr_rows, user.scopes),
        "vendor": filter_rows(vendor_rows, user.scopes)[0] if vendor_rows else None,
        "payments": filter_rows(pay_rows, user.scopes),
    }
