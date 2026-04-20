# Flow: <Endpoint Name>

## Purpose

One sentence describing what this endpoint does.

## Trigger

- `GET /path` or `POST /path`

## Entry Point

- File: `app/api/endpoints/<module>.py`
- Function: `<function_name>()`

## Inputs

- Path params: `{id}`
- Query params: `?limit=50&status=ACTIVE`
- Headers: `Authorization: Bearer <token>`
- Body: (for POST)

## Auth

- Route scope: `procurement.read`
- Column restrictions: `bank_account` requires `procurement.restricted.read`

## Execution Path

1. JWT extracted from Authorization header
2. JWT validated, scopes extracted
3. Route scope check (403 if missing)
4. Backend obtained from `request.app.state.backend`
5. SQL query executed
6. Column filtering applied based on user scopes
7. JSON response returned

## SQL

```sql
SELECT * FROM "PROCUREMENT"."table_name" WHERE "COLUMN" = ?
```

## Response

```json
{
  "field": "value"
}
```

## Failure Modes

- 401 Unauthorized: Missing or invalid token
- 403 Forbidden: Missing required scope
- 404 Not Found: Entity not found
- 500 Internal Server Error: Database error

## Tests

- Unit: `tests/unit/api/test_<module>.py`
- Integration: `tests/integration/api/test_<module>.py`
