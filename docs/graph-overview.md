# Graph Overview

This document describes the procurement knowledge graph stored in SAP HANA Cloud.

## Architecture

The graph is implemented as SQL views over 29 relational tables:

- **10 vertex views** — represent entities (vendors, materials, POs, etc.)
- **14 edge views** — represent relationships (supplies, ordered_from, pays, etc.)
- **2 unified views** — combine all vertices/edges for traversal
- **1 graph workspace** — registers the graph for HANA's graph engine

## Vertex Views

| View | Source Table | Key Fields |
|------|--------------|------------|
| `V_VENDOR` | `vendor_master` | vendor_id, vendor_name, risk_score, quality_score |
| `V_MATERIAL` | `material_master` | material_id, description, category_id, criticality |
| `V_PLANT` | `plant` | plant_id, plant_name, country, city |
| `V_CATEGORY` | `category_hierarchy` | category_id, category_name, level, parent_category_id |
| `V_PURCHASE_ORDER` | `po_header` | po_id, po_date, vendor_id, status, total_net_value |
| `V_CONTRACT` | `contract_header` | contract_id, vendor_id, valid_from, valid_to, status |
| `V_INVOICE` | `invoice_header` | invoice_id, invoice_date, vendor_id, match_status |
| `V_GOODS_RECEIPT` | `gr_header` | gr_id, gr_date, po_id, status |
| `V_PAYMENT` | `payment` | payment_id, payment_date, vendor_id, total_amount |
| `V_PURCHASE_REQ` | `pr_header` | pr_id, pr_date, status, priority |

### Unified Vertex View

`V_ALL_VERTICES` combines all vertex views with these columns:
- `VERTEX_ID` — unique identifier (e.g., "VND-HOKUYO", "PO-000001")
- `VERTEX_TYPE` — entity type (e.g., "VENDOR", "PURCHASE_ORDER")
- `LABEL` — human-readable name/description

## Edge Views

| View | Relationship | Source → Target |
|------|--------------|-----------------|
| `E_SUPPLIES` | Vendor supplies Material | `vendor_id` → `material_id` |
| `E_ORDERED_FROM` | PO ordered from Vendor | `po_id` → `vendor_id` |
| `E_CONTAINS_MATERIAL` | PO contains Material | `po_id` → `material_id` |
| `E_UNDER_CONTRACT` | PO under Contract | `po_id` → `contract_id` |
| `E_INVOICED_FOR` | Invoice for PO | `invoice_id` → `po_id` |
| `E_RECEIVED_FOR` | GR received for PO | `gr_id` → `po_id` |
| `E_PAYS` | Payment pays Invoice | `payment_id` → `invoice_id` |
| `E_BELONGS_TO_CATEGORY` | Material belongs to Category | `material_id` → `category_id` |
| `E_CATEGORY_PARENT` | Category has parent Category | `category_id` → `parent_category_id` |
| `E_LOCATED_AT` | PO located at Plant | `po_id` → `plant_id` |
| `E_HAS_CONTRACT` | Vendor has Contract | `vendor_id` → `contract_id` |
| `E_REQUESTED_MATERIAL` | PR requests Material | `pr_id` → `material_id` |
| `E_INVOICED_BY_VENDOR` | Invoice by Vendor | `invoice_id` → `vendor_id` |
| `E_PAID_TO_VENDOR` | Payment to Vendor | `payment_id` → `vendor_id` |

### Unified Edge View

`E_ALL_EDGES` combines all edge views with these columns:
- `EDGE_ID` — unique identifier (computed)
- `SOURCE_VERTEX` — source vertex ID
- `TARGET_VERTEX` — target vertex ID
- `EDGE_TYPE` — relationship type (e.g., "SUPPLIES", "ORDERED_FROM")

## Graph Workspace

```sql
CREATE GRAPH WORKSPACE "PROCUREMENT"."PROCUREMENT_KG"
    EDGE TABLE "PROCUREMENT"."E_ALL_EDGES"
        SOURCE COLUMN "SOURCE_VERTEX"
        TARGET COLUMN "TARGET_VERTEX"
        KEY COLUMN "EDGE_ID"
    VERTEX TABLE "PROCUREMENT"."V_ALL_VERTICES"
        KEY COLUMN "VERTEX_ID";
```

This workspace enables:
- OpenCypher queries via `OPENCYPHER_TABLE()`
- Graph algorithms via GraphScript
- Pattern matching with `MATCH` clause

## Common Traversal Patterns

### Find vendors supplying a material

**Via SQL JOIN:**
```sql
SELECT v.* FROM vendor_master v
JOIN source_list s ON s.vendor_id = v.vendor_id
WHERE s.material_id = 'MAT-LIDAR-2D'
```

**Via Graph API:**
```
GET /graph/neighbors/MAT-LIDAR-2D?edge_type=SUPPLIES&direction=incoming
```

### P2P Chain traversal

```
PO-000001 ─[ORDERED_FROM]──► VND-HOKUYO
    │
    ├─[RECEIVED_FOR]◄── GR-000001
    │
    ├─[INVOICED_FOR]◄── INV-000001 ─[INVOICED_BY_VENDOR]──► VND-HOKUYO
    │                       │
    │                       └─[PAYS]◄── PAY-000001 ─[PAID_TO_VENDOR]──► VND-HOKUYO
```

### Category hierarchy

```
ELEC (Electronics, Level 1)
  └─[CATEGORY_PARENT]◄── ELEC-SENS (Sensors, Level 2)
                            └─[CATEGORY_PARENT]◄── ELEC-SENS-LIDAR2D (2D LiDAR, Level 3)
                                                      └─[BELONGS_TO_CATEGORY]◄── MAT-LIDAR-2D
```

## Entity ID Conventions

| Prefix | Entity Type |
|--------|-------------|
| `VND-` | Vendor |
| `MAT-` | Material |
| `PO-` | Purchase Order |
| `CTR-` | Contract |
| `INV-` | Invoice |
| `GR-` | Goods Receipt |
| `PAY-` | Payment |
| `PR-` | Purchase Requisition |
| `SG01`, `MY01`, `VN01` | Plant codes |
| `ELEC`, `MECH`, etc. | Category codes |
