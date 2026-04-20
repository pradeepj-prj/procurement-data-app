# OpenCypher Query Guide

This guide explains how to use the `/graph/cypher` endpoint for graph pattern matching queries.

## Overview

The endpoint executes OpenCypher queries against the `PROCUREMENT_KG` graph workspace via HANA's `OPENCYPHER_TABLE()` function.

**Endpoint:** `POST /graph/cypher`

**Request:**
```json
{
  "query": "MATCH (v:Vendor) WHERE v.risk_score > 70 RETURN v.vendor_id, v.vendor_name",
  "params": {}
}
```

**Response:**
```json
{
  "columns": ["v.vendor_id", "v.vendor_name"],
  "rows": [
    {"v.vendor_id": "VND-001", "v.vendor_name": "Acme Corp"}
  ],
  "row_count": 1,
  "execution_time_ms": 45.2
}
```

## Basic Syntax

### Vertex Matching

Match vertices by label (vertex type):

```cypher
MATCH (v:Vendor)
RETURN v
LIMIT 10
```

Available labels: `Vendor`, `Material`, `PurchaseOrder`, `Contract`, `Invoice`, `GoodsReceipt`, `Payment`, `Plant`, `Category`, `PurchaseReq`

### Property Filtering

Filter by vertex properties:

```cypher
MATCH (v:Vendor)
WHERE v.risk_score > 70 AND v.country = 'JP'
RETURN v.vendor_id, v.vendor_name, v.risk_score
```

### Edge Traversal

Match connected vertices via edges:

```cypher
MATCH (vendor:Vendor)-[s:SUPPLIES]->(material:Material)
WHERE vendor.vendor_id = 'VND-HOKUYO'
RETURN material.material_id, material.description
```

Edge types: `SUPPLIES`, `ORDERED_FROM`, `CONTAINS_MATERIAL`, `UNDER_CONTRACT`, `INVOICED_FOR`, `RECEIVED_FOR`, `PAYS`, `BELONGS_TO_CATEGORY`, `CATEGORY_PARENT`, `LOCATED_AT`, `HAS_CONTRACT`, `REQUESTED_MATERIAL`, `INVOICED_BY_VENDOR`, `PAID_TO_VENDOR`

### Direction

```cypher
-- Outgoing edge (default)
MATCH (v)-[e:SUPPLIES]->(m)

-- Incoming edge
MATCH (v)<-[e:SUPPLIES]-(m)

-- Either direction
MATCH (v)-[e:SUPPLIES]-(m)
```

## Common Patterns

### Find vendors for a material

```cypher
MATCH (v:Vendor)-[:SUPPLIES]->(m:Material)
WHERE m.material_id = 'MAT-LIDAR-2D'
RETURN v.vendor_id, v.vendor_name, v.quality_score
ORDER BY v.quality_score DESC
```

### Multi-hop: PO → Vendor → Materials

```cypher
MATCH (po:PurchaseOrder)-[:ORDERED_FROM]->(v:Vendor)-[:SUPPLIES]->(m:Material)
WHERE po.po_id = 'PO-000001'
RETURN v.vendor_id, m.material_id, m.description
```

### P2P Chain

```cypher
MATCH (po:PurchaseOrder)-[:INVOICED_FOR]-(inv:Invoice)-[:PAYS]-(pay:Payment)
WHERE po.po_id = 'PO-000001'
RETURN po.po_id, inv.invoice_id, pay.payment_id, pay.total_amount
```

### Category hierarchy

```cypher
MATCH (cat:Category)-[:CATEGORY_PARENT*1..3]->(parent:Category)
WHERE cat.category_id = 'ELEC-SENS-LIDAR2D'
RETURN cat.category_id, parent.category_id, parent.category_name
```

### Variable-length paths

```cypher
-- Find all vertices within 3 hops of a vendor
MATCH path = (v:Vendor)-[*1..3]-(connected)
WHERE v.vendor_id = 'VND-HOKUYO'
RETURN DISTINCT connected.vertex_id, labels(connected)
LIMIT 50
```

## Parameters

Use `$param_name` syntax for parameterized queries:

```json
{
  "query": "MATCH (v:Vendor) WHERE v.risk_score > $min_risk RETURN v",
  "params": {"min_risk": 70}
}
```

## Supported Features

- Vertex labels
- Edge types
- Property filtering (=, <>, <, >, <=, >=)
- AND, OR, NOT in WHERE
- RETURN with aliases
- ORDER BY
- LIMIT
- Variable-length paths (`-[*1..N]->`)
- DISTINCT
- Parameters (`$name`)

## Limitations

- **Read-only**: No MERGE, CREATE, DELETE, SET, REMOVE
- **Max path depth**: 15 hops
- **No aggregations**: COUNT, SUM, AVG not supported in current version
- **No OPTIONAL MATCH**: All matches must succeed
- **Column filtering**: Results are filtered by user scopes (same as REST endpoints)

## Error Handling

Invalid queries return 400 Bad Request:

```json
{
  "detail": "OpenCypher query error: syntax error at position 15"
}
```

Write operations return 400:

```json
{
  "detail": "Only read operations are allowed. MERGE, CREATE, DELETE, SET, REMOVE are prohibited."
}
```

## Examples with curl

```bash
# Find high-risk vendors
curl -X POST http://localhost:8001/graph/cypher \
  -H "Content-Type: application/json" \
  -d '{
    "query": "MATCH (v:Vendor) WHERE v.risk_score > 70 RETURN v.vendor_id, v.risk_score ORDER BY v.risk_score DESC",
    "params": {}
  }'

# Materials supplied by a vendor
curl -X POST http://localhost:8001/graph/cypher \
  -H "Content-Type: application/json" \
  -d '{
    "query": "MATCH (v:Vendor)-[:SUPPLIES]->(m:Material) WHERE v.vendor_id = $vid RETURN m",
    "params": {"vid": "VND-HOKUYO"}
  }'
```
