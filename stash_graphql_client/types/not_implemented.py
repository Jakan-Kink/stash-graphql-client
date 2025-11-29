"""Types for NotImplementedMixin."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class Version(BaseModel):
    """Version information from schema/types/version.graphql."""

    version: str  # String!
    hash: str  # String!
    build_time: str  # String!


class LatestVersion(BaseModel):
    """Latest version information from schema/types/version.graphql."""

    version: str  # String!
    shorthash: str  # String!
    release_date: str  # String!
    url: str  # String!
    notes: str | None = None  # String


class SQLQueryResult(BaseModel):
    """Result of a SQL query from schema/types/sql.graphql."""

    rows: list[dict[str, Any]]  # [Map!]!
    columns: list[str]  # [String!]!


class SQLExecResult(BaseModel):
    """Result of a SQL exec from schema/types/sql.graphql."""

    rows_affected: int  # Int!


class StashBoxValidationResult(BaseModel):
    """Result of stash-box validation from schema/types/stash-box.graphql."""

    valid: bool  # Boolean!
    status: str  # String!


class DLNAStatus(BaseModel):
    """DLNA status from schema/types/dlna.graphql."""

    running: bool  # Boolean!
    until: str | None = None  # String
    recent_ips: list[str]  # [String!]!


class JobStatusUpdate(BaseModel):
    """Job status update from schema/types/job.graphql."""

    type: str  # String!
    message: str | None = None  # String
    progress: float | None = None  # Float
    status: str | None = None  # String
    error: str | None = None  # String
    job: dict[str, Any] | None = None  # Job
