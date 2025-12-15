"""Package types from schema/types/package.graphql."""

from __future__ import annotations

from pydantic import BaseModel, Field

from .base import FromGraphQLMixin, StashInput
from .scalars import Map, Timestamp
from .unset import UNSET, UnsetType


class Package(FromGraphQLMixin, BaseModel):
    """Package type from schema/types/package.graphql."""

    package_id: str | UnsetType = Field(default=UNSET, alias="package_id")  # String!
    name: str | UnsetType = UNSET  # String!
    version: str | None | UnsetType = UNSET  # String
    date: Timestamp | None | UnsetType = UNSET  # Timestamp
    requires: list[Package] | UnsetType = UNSET  # [Package!]!
    source_url: str | UnsetType = Field(default=UNSET, alias="sourceURL")  # String!
    source_package: Package | None | UnsetType = Field(
        default=UNSET, alias="source_package"
    )  # Package
    metadata: Map | UnsetType = UNSET  # Map!


class PackageSpecInput(StashInput):
    """Input for specifying a package from schema/types/package.graphql."""

    id: str  # String!
    source_url: str = Field(alias="sourceURL")  # String! (camelCase in schema)


class PackageSource(FromGraphQLMixin, BaseModel):
    """Package source type from schema/types/package.graphql."""

    name: str | None | UnsetType = UNSET  # String
    url: str | UnsetType = UNSET  # String!
    local_path: str | None | UnsetType = Field(
        default=UNSET, alias="local_path"
    )  # String


class PackageSourceInput(StashInput):
    """Input for package source from schema/types/package.graphql."""

    name: str | None | UnsetType = UNSET  # String
    url: str  # String!
    local_path: str | None | UnsetType = UNSET  # String (snake_case in schema)
