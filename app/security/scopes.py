"""Scope definitions for procurement data access."""
from __future__ import annotations


class Scopes:
    """Available authorization scopes."""

    # Base read access
    READ = "procurement.read"

    # Domain-specific read access
    CONTRACTS_READ = "procurement.contracts.read"
    FINANCE_READ = "procurement.finance.read"
    TRANSACTIONS_READ = "procurement.transactions.read"
    SPEND_READ = "procurement.spend.read"

    # Restricted data access
    RESTRICTED_READ = "procurement.restricted.read"

    # Admin
    ADMIN = "admin"


# Fields that require specific scopes to view
RESTRICTED_FIELDS: dict[str, str] = {
    "bank_account": Scopes.RESTRICTED_READ,
    "bank_country": Scopes.RESTRICTED_READ,
    "bank_key": Scopes.RESTRICTED_READ,
    "tax_id": Scopes.RESTRICTED_READ,
}

# Route scope requirements
ROUTE_SCOPES: dict[str, str] = {
    # Vendors
    "/vendors": Scopes.READ,
    "/vendors/{id}": Scopes.READ,
    "/vendors/{id}/materials": Scopes.READ,
    "/vendors/{id}/contracts": Scopes.CONTRACTS_READ,
    "/vendors/{id}/purchase-orders": Scopes.READ,
    # Materials
    "/materials": Scopes.READ,
    "/materials/{id}": Scopes.READ,
    "/materials/{id}/vendors": Scopes.READ,
    # Purchase orders
    "/purchase-orders": Scopes.READ,
    "/purchase-orders/{id}": Scopes.READ,
    "/purchase-orders/{id}/line-items": Scopes.READ,
    # Contracts
    "/contracts": Scopes.CONTRACTS_READ,
    "/contracts/{id}": Scopes.CONTRACTS_READ,
    # Invoices
    "/invoices": Scopes.FINANCE_READ,
    "/invoices/{id}": Scopes.FINANCE_READ,
    # Payments
    "/payments": Scopes.FINANCE_READ,
    "/payments/{id}": Scopes.FINANCE_READ,
    # Graph
    "/graph/vertices": Scopes.READ,
    "/graph/vertices/{id}": Scopes.READ,
    "/graph/neighbors/{id}": Scopes.READ,
    "/graph/summary": Scopes.READ,
    "/graph/cypher": Scopes.READ,
    # Queries
    "/queries/p2p-chain/{po_id}": Scopes.TRANSACTIONS_READ,
    "/queries/invoice-context/{inv_id}": Scopes.FINANCE_READ,
    "/queries/spend-by-vendor": Scopes.SPEND_READ,
    "/queries/spend-by-category": Scopes.SPEND_READ,
    "/queries/category-tree/{code}": Scopes.READ,
    "/queries/invoice-aging": Scopes.FINANCE_READ,
    "/queries/overdue-invoices": Scopes.FINANCE_READ,
    "/queries/materials-for-plant/{plant}": Scopes.READ,
}
