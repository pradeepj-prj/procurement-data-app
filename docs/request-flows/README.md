# Request Flow Documentation

This folder documents how requests flow through the Procurement Data API.

## Flow Pages

### Startup
- [`app-startup.md`](./app-startup.md) - Application initialization and backend selection

### REST Endpoints
- [`get-vendors.md`](./get-vendors.md) - GET /vendors with filtering
- [`get-vendor-by-id.md`](./get-vendor-by-id.md) - GET /vendors/{id} with auth

### Graph Endpoints
- [`graph-vertex.md`](./graph-vertex.md) - GET /graph/vertices/{id}
- [`graph-cypher.md`](./graph-cypher.md) - POST /graph/cypher (OpenCypher)

### Query Endpoints
- [`p2p-chain.md`](./p2p-chain.md) - GET /queries/p2p-chain/{po_id}

## Authorization Flow

All protected endpoints follow this pattern:

1. Extract JWT from `Authorization: Bearer <token>` header
2. Decode and validate JWT (signature, expiration)
3. Extract scopes from JWT claims
4. Check route-level scope requirement
5. Execute query
6. Apply column-level filtering to response
7. Return filtered JSON

## Adding New Flows

Use [`template.md`](./template.md) as a starting point for documenting new endpoints.
