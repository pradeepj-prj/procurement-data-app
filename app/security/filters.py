"""Column-level filtering based on user scopes."""
from __future__ import annotations

from typing import Any

from app.security.scopes import RESTRICTED_FIELDS


def filter_columns(data: dict[str, Any], user_scopes: list[str]) -> dict[str, Any]:
    """Filter out restricted columns based on user scopes.

    Args:
        data: Row data as dictionary
        user_scopes: List of scopes the user has

    Returns:
        Filtered dictionary with restricted fields removed or set to None
    """
    if "admin" in user_scopes:
        return data

    result = {}
    for key, value in data.items():
        if key in RESTRICTED_FIELDS:
            required_scope = RESTRICTED_FIELDS[key]
            if required_scope not in user_scopes:
                result[key] = None  # Redact the value
            else:
                result[key] = value
        else:
            result[key] = value

    return result


def filter_rows(
    rows: list[dict[str, Any]], user_scopes: list[str]
) -> list[dict[str, Any]]:
    """Filter columns for a list of rows.

    Args:
        rows: List of row dictionaries
        user_scopes: List of scopes the user has

    Returns:
        List of filtered dictionaries
    """
    return [filter_columns(row, user_scopes) for row in rows]
