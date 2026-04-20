"""Graph endpoints for vertex/edge traversal and OpenCypher queries."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel

from app.api.middleware.auth import require_scope
from app.config import settings
from app.db.backend import DataBackend
from app.security import AuthenticatedUser, Scopes, filter_columns

router = APIRouter(prefix="/graph", tags=["graph"])


def get_backend(request: Request) -> DataBackend:
    """Get the database backend from app state."""
    return request.app.state.backend


@router.get("/vertices/{vertex_id}")
async def get_vertex(
    request: Request,
    vertex_id: str,
    user: AuthenticatedUser = Depends(require_scope(Scopes.READ)),
) -> dict[str, Any]:
    """Get a vertex by ID."""
    backend = get_backend(request)
    vertex = backend.get_vertex(vertex_id)

    if not vertex:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vertex {vertex_id} not found",
        )

    return filter_columns(vertex, user.scopes)


@router.get("/vertices")
async def search_vertices(
    request: Request,
    user: AuthenticatedUser = Depends(require_scope(Scopes.READ)),
    q: str = Query(..., min_length=1, description="Search query"),
    vertex_type: str | None = Query(None, description="Filter by vertex type"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
) -> list[dict[str, Any]]:
    """Search vertices by label or ID."""
    backend = get_backend(request)
    vertices = backend.search_vertices(q, vertex_type=vertex_type, limit=limit)
    return [filter_columns(v, user.scopes) for v in vertices]


@router.get("/neighbors/{vertex_id}")
async def get_neighbors(
    request: Request,
    vertex_id: str,
    user: AuthenticatedUser = Depends(require_scope(Scopes.READ)),
    edge_type: str | None = Query(None, description="Filter by edge type"),
    direction: str = Query("both", description="Direction: outgoing, incoming, both"),
) -> list[dict[str, Any]]:
    """Get neighboring vertices connected by edges."""
    if direction not in ("outgoing", "incoming", "both"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="direction must be 'outgoing', 'incoming', or 'both'",
        )

    backend = get_backend(request)
    neighbors = backend.get_neighbors(vertex_id, edge_type=edge_type, direction=direction)
    return [filter_columns(n, user.scopes) for n in neighbors]


@router.get("/summary")
async def get_graph_summary(
    request: Request,
    user: AuthenticatedUser = Depends(require_scope(Scopes.READ)),
) -> dict[str, Any]:
    """Get summary counts of vertices and edges by type."""
    backend = get_backend(request)
    return {
        "vertex_counts": backend.get_vertex_counts(),
        "edge_counts": backend.get_edge_counts(),
    }


# OpenCypher query models
class CypherRequest(BaseModel):
    """Request body for OpenCypher query."""

    query: str
    params: dict[str, Any] = {}


class CypherResponse(BaseModel):
    """Response from OpenCypher query."""

    columns: list[str]
    rows: list[dict[str, Any]]
    row_count: int
    execution_time_ms: float


@router.post("/cypher")
async def execute_cypher(
    request: Request,
    body: CypherRequest,
    user: AuthenticatedUser = Depends(require_scope(Scopes.READ)),
) -> CypherResponse:
    """Execute an OpenCypher query against the graph workspace.

    Uses HANA's OPENCYPHER_TABLE() function for graph pattern matching.
    Only read operations are allowed (no MERGE, CREATE, DELETE).
    """
    import time

    backend = get_backend(request)

    # Validate query - must be read-only
    query_upper = body.query.upper()
    if any(keyword in query_upper for keyword in ["MERGE", "CREATE", "DELETE", "SET", "REMOVE"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only read operations are allowed. MERGE, CREATE, DELETE, SET, REMOVE are prohibited.",
        )

    # Check if backend supports execute_sql (HANA only)
    if not hasattr(backend, "execute_sql"):
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="OpenCypher queries require HANA backend",
        )

    try:
        # Build the OPENCYPHER_TABLE SQL
        schema = settings.hana_schema
        cypher_sql = f'''
            SELECT * FROM OPENCYPHER_TABLE(
                GRAPH WORKSPACE "{schema}"."PROCUREMENT_KG",
                $${body.query}$$
            )
        '''

        start_time = time.perf_counter()

        try:
            rows = backend.execute_sql(cypher_sql, ())
        except NotImplementedError:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="OpenCypher queries require HANA backend",
            )

        execution_time_ms = (time.perf_counter() - start_time) * 1000

        # Extract column names from first row if available
        columns = list(rows[0].keys()) if rows else []

        # Apply column filtering
        filtered_rows = [filter_columns(row, user.scopes) for row in rows]

        return CypherResponse(
            columns=columns,
            rows=filtered_rows,
            row_count=len(filtered_rows),
            execution_time_ms=round(execution_time_ms, 2),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OpenCypher query error: {e}",
        )
