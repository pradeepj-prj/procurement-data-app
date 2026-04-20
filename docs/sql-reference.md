# SQL Reference

This document lists all SQL queries used by the Procurement Data API.

## Query Library Location

- Relational queries: `app/db/queries/relational.py`
- Graph view queries: `app/db/queries/graph.py`

All queries return `(sql, params)` tuples for parameterized execution.

---

## Relational Queries

### vendor_by_id

Lookup a single vendor by ID.

```sql
SELECT * FROM "PROCUREMENT"."vendor_master" WHERE "VENDOR_ID" = ?
```

**Parameters:** `vendor_id: str`
**Tables:** `vendor_master`

---

### filter_vendors

Filter vendors by risk score, country, and/or status.

```sql
SELECT * FROM "PROCUREMENT"."vendor_master"
WHERE "RISK_SCORE" >= ?
  AND "COUNTRY" = ?
  AND "STATUS" = ?
LIMIT ?
```

**Parameters:** `min_risk_score: int`, `country: str`, `status: str`, `limit: int`
**Tables:** `vendor_master`

---

### material_by_id

Lookup a single material by ID.

```sql
SELECT * FROM "PROCUREMENT"."material_master" WHERE "MATERIAL_ID" = ?
```

**Parameters:** `material_id: str`
**Tables:** `material_master`

---

### materials_for_vendor

Get materials supplied by a vendor (via source_list).

```sql
SELECT m.*
FROM "PROCUREMENT"."material_master" m
JOIN "PROCUREMENT"."source_list" s ON s."MATERIAL_ID" = m."MATERIAL_ID"
WHERE s."VENDOR_ID" = ?
```

**Parameters:** `vendor_id: str`
**Tables:** `material_master`, `source_list`
**Graph Edge:** E_SUPPLIES (Vendor → Material)

---

### vendors_for_material

Get vendors that supply a material (via source_list).

```sql
SELECT v.*
FROM "PROCUREMENT"."vendor_master" v
JOIN "PROCUREMENT"."source_list" s ON s."VENDOR_ID" = v."VENDOR_ID"
WHERE s."MATERIAL_ID" = ?
```

**Parameters:** `material_id: str`
**Tables:** `vendor_master`, `source_list`
**Graph Edge:** E_SUPPLIES (Material ← Vendor)

---

### contract_by_id

Lookup a contract by ID.

```sql
SELECT * FROM "PROCUREMENT"."contract_header" WHERE "CONTRACT_ID" = ?
```

**Parameters:** `contract_id: str`
**Tables:** `contract_header`

---

### contracts_for_vendor

Get contracts for a vendor.

```sql
SELECT * FROM "PROCUREMENT"."contract_header" WHERE "VENDOR_ID" = ?
```

**Parameters:** `vendor_id: str`
**Tables:** `contract_header`
**Graph Edge:** E_HAS_CONTRACT (Vendor → Contract)

---

### po_by_id

Lookup a purchase order by ID.

```sql
SELECT * FROM "PROCUREMENT"."po_header" WHERE "PO_ID" = ?
```

**Parameters:** `po_id: str`
**Tables:** `po_header`

---

### pos_for_vendor

Get purchase orders for a vendor.

```sql
SELECT * FROM "PROCUREMENT"."po_header" WHERE "VENDOR_ID" = ?
```

**Parameters:** `vendor_id: str`
**Tables:** `po_header`
**Graph Edge:** E_ORDERED_FROM (PO → Vendor)

---

### spend_by_vendor

Aggregated PO spend per vendor.

```sql
SELECT
    h."VENDOR_ID",
    v."VENDOR_NAME",
    SUM(h."TOTAL_NET_VALUE") AS "TOTAL_SPEND",
    COUNT(*) AS "PO_COUNT"
FROM "PROCUREMENT"."po_header" h
JOIN "PROCUREMENT"."vendor_master" v ON v."VENDOR_ID" = h."VENDOR_ID"
GROUP BY h."VENDOR_ID", v."VENDOR_NAME"
ORDER BY "TOTAL_SPEND" DESC
LIMIT ?
```

**Parameters:** `limit: int`
**Tables:** `po_header`, `vendor_master`

---

## Graph View Queries

### vertex_by_id

Lookup any vertex by ID from the unified vertex view.

```sql
SELECT * FROM "PROCUREMENT"."V_ALL_VERTICES" WHERE "VERTEX_ID" = ?
```

**Parameters:** `vertex_id: str`
**Views:** `V_ALL_VERTICES`

---

### search_vertices

Search vertices by label or ID substring.

```sql
SELECT * FROM "PROCUREMENT"."V_ALL_VERTICES"
WHERE ("LABEL" LIKE ? OR "VERTEX_ID" LIKE ?)
  AND "VERTEX_TYPE" = ?
LIMIT ?
```

**Parameters:** `query: str` (wrapped with %), `vertex_type: str`, `limit: int`
**Views:** `V_ALL_VERTICES`

---

### neighbors

Find vertices connected to a source vertex via edges.

```sql
-- Outgoing edges
SELECT v."VERTEX_ID", v."VERTEX_TYPE", v."LABEL",
       e."EDGE_TYPE", 'outgoing' AS "DIRECTION"
FROM "PROCUREMENT"."E_ALL_EDGES" e
JOIN "PROCUREMENT"."V_ALL_VERTICES" v ON v."VERTEX_ID" = e."TARGET_VERTEX"
WHERE e."SOURCE_VERTEX" = ?
  AND e."EDGE_TYPE" = ?

UNION ALL

-- Incoming edges
SELECT v."VERTEX_ID", v."VERTEX_TYPE", v."LABEL",
       e."EDGE_TYPE", 'incoming' AS "DIRECTION"
FROM "PROCUREMENT"."E_ALL_EDGES" e
JOIN "PROCUREMENT"."V_ALL_VERTICES" v ON v."VERTEX_ID" = e."SOURCE_VERTEX"
WHERE e."TARGET_VERTEX" = ?
  AND e."EDGE_TYPE" = ?
```

**Parameters:** `vertex_id: str`, `edge_type: str` (optional)
**Views:** `E_ALL_EDGES`, `V_ALL_VERTICES`

---

### vertex_counts

Count vertices by type.

```sql
SELECT "VERTEX_TYPE", COUNT(*) AS "COUNT"
FROM "PROCUREMENT"."V_ALL_VERTICES"
GROUP BY "VERTEX_TYPE"
```

**Parameters:** None
**Views:** `V_ALL_VERTICES`

---

### edge_counts

Count edges by type.

```sql
SELECT "EDGE_TYPE", COUNT(*) AS "COUNT"
FROM "PROCUREMENT"."E_ALL_EDGES"
GROUP BY "EDGE_TYPE"
```

**Parameters:** None
**Views:** `E_ALL_EDGES`

---

## Complex Query Patterns

### P2P Chain (PO → GR → Invoice → Payment)

Multi-step query to assemble the procure-to-pay chain:

1. Get PO header
2. Get goods receipts for PO
3. Get invoices for PO
4. Get payments for those invoices

See `app/api/endpoints/queries.py:get_p2p_chain`

---

### Spend by Category

Aggregate line item spend by material category.

```sql
SELECT
    ch."CATEGORY_ID",
    ch."CATEGORY_NAME",
    ch."LEVEL",
    SUM(li."NET_VALUE") AS "TOTAL_SPEND",
    COUNT(DISTINCT li."PO_ID") AS "PO_COUNT",
    COUNT(*) AS "LINE_ITEM_COUNT"
FROM "PROCUREMENT"."po_line_item" li
JOIN "PROCUREMENT"."material_master" m ON m."MATERIAL_ID" = li."MATERIAL_ID"
JOIN "PROCUREMENT"."category_hierarchy" ch ON ch."CATEGORY_ID" = m."CATEGORY_ID"
GROUP BY ch."CATEGORY_ID", ch."CATEGORY_NAME", ch."LEVEL"
ORDER BY "TOTAL_SPEND" DESC
LIMIT ?
```

**Tables:** `po_line_item`, `material_master`, `category_hierarchy`
