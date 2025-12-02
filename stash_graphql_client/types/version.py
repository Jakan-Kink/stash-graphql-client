"""Version types from schema/types/version.graphql."""

from __future__ import annotations

from pydantic import BaseModel


class LatestVersion(BaseModel):
    """Latest version information from schema/types/version.graphql."""

    version: str  # String!
    shorthash: str  # String!
    release_date: str  # String!
    url: str  # String!


class Version(BaseModel):
    """Version information from schema/types/version.graphql."""

    version: str | None = None  # String
    hash: str  # String!
    build_time: str  # String!
