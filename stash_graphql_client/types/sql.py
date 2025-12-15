"""SQL types from schema/types/sql.graphql."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from .scalars import Int64
from .unset import UNSET, UnsetType


class SQLQueryResult(BaseModel):
    """Result from SQL query from schema/types/sql.graphql."""

    columns: list[str] | None | UnsetType = (
        UNSET  # [String!]! - Column names in result set order
    )
    rows: list[list[Any]] | None | UnsetType = UNSET  # [[Any]!]! - Returned rows


class SQLExecResult(BaseModel):
    """Result from SQL execution from schema/types/sql.graphql."""

    rows_affected: Int64 | None | UnsetType = (
        UNSET  # Int64 - Rows affected (UPDATE/INSERT/DELETE)
    )
    last_insert_id: Int64 | None | UnsetType = (
        UNSET  # Int64 - Last insert ID from auto-increment
    )
