"""Version types from schema/types/version.graphql."""

from __future__ import annotations

from pydantic import BaseModel

from .base import FromGraphQLMixin
from .unset import UNSET, UnsetType


class Version(FromGraphQLMixin, BaseModel):
    """Version information."""

    version: str | None | UnsetType = UNSET
    hash: str | UnsetType = UNSET
    build_time: str | UnsetType = UNSET  # GraphQL uses snake_case, so no alias needed


class LatestVersion(FromGraphQLMixin, BaseModel):
    """Latest version information."""

    version: str | UnsetType = UNSET
    shorthash: str | UnsetType = UNSET
    release_date: str | UnsetType = UNSET  # GraphQL uses snake_case, so no alias needed
    url: str | UnsetType = UNSET
