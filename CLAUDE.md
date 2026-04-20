# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Project

REST API for SAP procurement data. Provides relational queries, graph traversal, and OpenCypher queries over a procurement knowledge graph stored in SAP HANA Cloud.

This is the **data layer** — a separate AI layer (`procurement-genai-backend`) calls this API.

## Sibling Repos

| Repo | Purpose |
|------|---------|
| `procurement-data-generator` | Generates the procurement dataset (29 tables, ~10K rows) and deploys to HANA Cloud |
| `procurement-genai-backend` | AI/Agent layer using LangGraph + SAP GenAI Hub, calls this API |
| `procurement-ui` | React frontend for chat, graph visualization, and trace display |

## Data Source: HANA Cloud

The API queries data in HANA Cloud under the `PROCUREMENT` schema.

### Relational Tables (29)

Key tables: `vendor_master`, `material_master`, `po_header`, `po_line_item`, `contract_header`, `invoice_header`, `payment`, `source_list`, `category_hierarchy`

### Graph Workspace

- **10 vertex views**: V_VENDOR, V_MATERIAL, V_PLANT, V_CATEGORY, V_PURCHASE_ORDER, V_CONTRACT, V_INVOICE, V_GOODS_RECEIPT, V_PAYMENT, V_PURCHASE_REQ
- **14 edge views**: E_SUPPLIES, E_ORDERED_FROM, E_CONTAINS_MATERIAL, E_UNDER_CONTRACT, E_INVOICED_FOR, E_RECEIVED_FOR, E_PAYS, etc.
- **Graph workspace**: PROCUREMENT_KG (for OpenCypher queries)

## API Design

### REST Resources
- `/vendors`, `/vendors/{id}`, `/vendors/{id}/materials`
- `/materials`, `/materials/{id}`, `/materials/{id}/vendors`
- `/purchase-orders`, `/contracts`, `/invoices`, `/payments`

### Graph Endpoints
- `/graph/vertices/{id}` — vertex by ID
- `/graph/vertices?q=...` — search vertices
- `/graph/neighbors/{id}` — neighbor traversal
- `/graph/cypher` — OpenCypher query execution

### Query Endpoints
- `/queries/p2p-chain/{po_id}` — PO→GR→INV→PAY chain
- `/queries/spend-by-vendor` — spend aggregation
- `/queries/materials-for-plant/{plant}` — materials at plant

## Authorization

**Two-layer model:**
1. **Route-level**: Endpoints require specific scopes (e.g., `procurement.finance.read` for `/invoices`)
2. **Column-level**: Sensitive fields (e.g., `bank_account`) redacted unless user has `procurement.restricted.read`

## Environment Variables

```bash
# Graph backend
GRAPH_BACKEND=hana          # or "networkx" for local dev with CSV

# HANA Cloud
HANA_HOST=
HANA_PORT=443
HANA_USER=DBADMIN
HANA_PASSWORD=
HANA_SCHEMA=PROCUREMENT

# JWT Auth
JWT_SECRET=                 # For local dev; in prod use XSUAA

# Local dev (NetworkX fallback)
CSV_DIR=../procurement-data-generator/output/csv
```

## Running Locally

```bash
# Install dependencies
pip install -e .[dev]

# Start with NetworkX backend (no HANA needed)
GRAPH_BACKEND=networkx python -m app --port 8001

# Test
curl http://localhost:8001/health
curl http://localhost:8001/vendors
```

## Testing

```bash
# Unit tests (no external deps)
pytest tests/unit/ -v

# Integration tests (requires HANA)
HANA_HOST=... pytest tests/integration/ -v
```
