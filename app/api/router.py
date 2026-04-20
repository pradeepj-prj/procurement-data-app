from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.endpoints.contracts import router as contracts_router
from app.api.endpoints.graph import router as graph_router
from app.api.endpoints.health import router as health_router
from app.api.endpoints.queries import router as queries_router
from app.api.endpoints.invoices import router as invoices_router
from app.api.endpoints.materials import router as materials_router
from app.api.endpoints.payments import router as payments_router
from app.api.endpoints.purchase_orders import router as purchase_orders_router
from app.api.endpoints.vendors import router as vendors_router
from app.api.middleware.cors import setup_cors

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialise shared resources on startup; clean up on shutdown."""
    from app.db import get_backend

    logger.info("Initialising database backend…")
    app.state.backend = get_backend()
    logger.info("Backend ready: %s", type(app.state.backend).__name__)
    yield


app = FastAPI(
    title="Procurement Data API",
    version="1.0.0",
    lifespan=lifespan,
)

setup_cors(app)
app.include_router(health_router, tags=["health"])
app.include_router(vendors_router)
app.include_router(materials_router)
app.include_router(purchase_orders_router)
app.include_router(contracts_router)
app.include_router(invoices_router)
app.include_router(payments_router)
app.include_router(graph_router)
app.include_router(queries_router)
