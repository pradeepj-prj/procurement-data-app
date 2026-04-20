"""SQL queries against the HANA relational tables.

Every function returns ``(sql, params)`` — a parameterized query string
and a tuple of bind values.  The caller is responsible for executing.
"""
from __future__ import annotations

from app.config import settings

_S = settings.hana_schema


# ---------------------------------------------------------------------------
# Vendor queries
# ---------------------------------------------------------------------------

def vendor_by_id(vendor_id: str) -> tuple[str, tuple]:
    return (
        f'SELECT * FROM "{_S}"."vendor_master" WHERE "VENDOR_ID" = ?',
        (vendor_id,),
    )


def filter_vendors(
    *,
    min_risk_score: int | None = None,
    country: str | None = None,
    status: str | None = None,
    limit: int = 50,
) -> tuple[str, tuple]:
    """Dynamically-filtered vendor lookup."""
    clauses: list[str] = []
    params: list[str | int] = []

    if min_risk_score is not None:
        clauses.append('"RISK_SCORE" >= ?')
        params.append(min_risk_score)
    if country is not None:
        clauses.append('"COUNTRY" = ?')
        params.append(country)
    if status is not None:
        clauses.append('"STATUS" = ?')
        params.append(status)

    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    return (
        f'SELECT * FROM "{_S}"."vendor_master"{where} LIMIT ?',
        (*params, limit),
    )


# ---------------------------------------------------------------------------
# Material queries
# ---------------------------------------------------------------------------

def material_by_id(material_id: str) -> tuple[str, tuple]:
    return (
        f'SELECT * FROM "{_S}"."material_master" WHERE "MATERIAL_ID" = ?',
        (material_id,),
    )


# ---------------------------------------------------------------------------
# Source list joins (vendor ↔ material)
# ---------------------------------------------------------------------------

def materials_for_vendor(vendor_id: str) -> tuple[str, tuple]:
    """Materials supplied by a vendor (via source_list)."""
    return (
        f'SELECT m.* FROM "{_S}"."material_master" m '
        f'JOIN "{_S}"."source_list" s ON s."MATERIAL_ID" = m."MATERIAL_ID" '
        f'WHERE s."VENDOR_ID" = ?',
        (vendor_id,),
    )


def vendors_for_material(material_id: str) -> tuple[str, tuple]:
    """Vendors that supply a material (via source_list)."""
    return (
        f'SELECT v.* FROM "{_S}"."vendor_master" v '
        f'JOIN "{_S}"."source_list" s ON s."VENDOR_ID" = v."VENDOR_ID" '
        f'WHERE s."MATERIAL_ID" = ?',
        (material_id,),
    )


# ---------------------------------------------------------------------------
# Contract queries
# ---------------------------------------------------------------------------

def contract_by_id(contract_id: str) -> tuple[str, tuple]:
    return (
        f'SELECT * FROM "{_S}"."contract_header" WHERE "CONTRACT_ID" = ?',
        (contract_id,),
    )


def contracts_for_vendor(vendor_id: str) -> tuple[str, tuple]:
    return (
        f'SELECT * FROM "{_S}"."contract_header" WHERE "VENDOR_ID" = ?',
        (vendor_id,),
    )


# ---------------------------------------------------------------------------
# Purchase order queries
# ---------------------------------------------------------------------------

def po_by_id(po_id: str) -> tuple[str, tuple]:
    return (
        f'SELECT * FROM "{_S}"."po_header" WHERE "PO_ID" = ?',
        (po_id,),
    )


def pos_for_vendor(vendor_id: str) -> tuple[str, tuple]:
    return (
        f'SELECT * FROM "{_S}"."po_header" WHERE "VENDOR_ID" = ?',
        (vendor_id,),
    )


def pos_for_material(material_id: str) -> tuple[str, tuple]:
    """POs containing a material (via po_line_item)."""
    return (
        f'SELECT DISTINCT h.* FROM "{_S}"."po_header" h '
        f'JOIN "{_S}"."po_line_item" li ON li."PO_ID" = h."PO_ID" '
        f'WHERE li."MATERIAL_ID" = ?',
        (material_id,),
    )


def pos_for_contract(contract_id: str) -> tuple[str, tuple]:
    """POs linked to a contract (via po_line_item)."""
    return (
        f'SELECT DISTINCT h.* FROM "{_S}"."po_header" h '
        f'JOIN "{_S}"."po_line_item" li ON li."PO_ID" = h."PO_ID" '
        f'WHERE li."CONTRACT_ID" = ?',
        (contract_id,),
    )


def pos_for_plant(plant_id: str) -> tuple[str, tuple]:
    return (
        f'SELECT * FROM "{_S}"."po_header" WHERE "PLANT_ID" = ?',
        (plant_id,),
    )


# ---------------------------------------------------------------------------
# Spend aggregation
# ---------------------------------------------------------------------------

def spend_by_vendor(limit: int = 20) -> tuple[str, tuple]:
    """Total PO spend per vendor, descending."""
    return (
        f'SELECT h."VENDOR_ID", v."VENDOR_NAME", '
        f'SUM(h."TOTAL_NET_VALUE") AS "TOTAL_SPEND", '
        f'COUNT(*) AS "PO_COUNT" '
        f'FROM "{_S}"."po_header" h '
        f'JOIN "{_S}"."vendor_master" v ON v."VENDOR_ID" = h."VENDOR_ID" '
        f'GROUP BY h."VENDOR_ID", v."VENDOR_NAME" '
        f'ORDER BY "TOTAL_SPEND" DESC LIMIT ?',
        (limit,),
    )
