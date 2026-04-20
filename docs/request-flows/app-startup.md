# Flow: Application Startup

## Purpose

Initialize the FastAPI application and database backend on startup.

## Trigger

- `python -m app` or `uvicorn app.api.router:app`

## Entry Point

- File: `app/__main__.py`
- Calls: `uvicorn.run("app.api.router:app", ...)`

## Execution Path

1. **Parse CLI args** (`app/__main__.py`)
   - `--host` (default: 0.0.0.0)
   - `--port` (default: 8000)

2. **Load settings** (`app/config.py`)
   - Reads from environment variables
   - Falls back to `.env` file
   - Key settings: `GRAPH_BACKEND`, `HANA_*`, `JWT_SECRET`, `SKIP_AUTH`

3. **Create FastAPI app** (`app/api/router.py`)
   - Title: "Procurement Data API"
   - Version: "1.0.0"
   - Lifespan context manager attached

4. **Lifespan startup** (`app/api/router.py:lifespan`)
   - Calls `get_backend()` from `app/db/__init__.py`
   - Backend selection based on `settings.graph_backend`:
     - `"networkx"` → `NetworkXBackend` (loads CSV files)
     - `"hana"` (default) → `HANABackend` (connects to HANA Cloud)
   - Stores backend in `app.state.backend`

5. **Setup middleware**
   - CORS via `setup_cors(app)` from `app/api/middleware/cors.py`

6. **Include routers**
   - Health, vendors, materials, purchase-orders, contracts, invoices, payments
   - Graph endpoints
   - Query endpoints

7. **Start uvicorn server**
   - Listens on configured host:port

## Configuration

| Env Var | Default | Purpose |
|---------|---------|---------|
| `GRAPH_BACKEND` | `hana` | Backend selection |
| `HANA_HOST` | | HANA Cloud hostname |
| `HANA_PORT` | `443` | HANA Cloud port |
| `HANA_USER` | `DBADMIN` | Database user |
| `HANA_PASSWORD` | | Database password |
| `HANA_SCHEMA` | `PROCUREMENT` | Schema name |
| `SKIP_AUTH` | `false` | Skip JWT validation |
| `JWT_SECRET` | | JWT signing secret |

## Failure Modes

- Missing HANA credentials → Connection error on first request
- Invalid CSV_DIR for NetworkX → Backend initialization fails
- Port already in use → Uvicorn startup error

## Verification

```bash
python -m app --port 8001
curl http://localhost:8001/health
# {"status":"healthy","version":"1.0.0",...}
```
