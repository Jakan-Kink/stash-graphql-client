"""StashBox types from schema/types/stash-box.graphql.

Note: StashID and StashIDInput are defined in files.py to avoid circular imports.
"""

from __future__ import annotations

from pydantic import BaseModel

from .base import StashInput
from .unset import UNSET, UnsetType


class StashBox(BaseModel):
    """StashBox configuration from schema/types/stash-box.graphql."""

    endpoint: str | None | UnsetType = UNSET  # String!
    api_key: str | None | UnsetType = UNSET  # String!
    name: str | None | UnsetType = UNSET  # String!
    max_requests_per_minute: int | None | UnsetType = UNSET  # Int!


class StashBoxInput(StashInput):
    """Input for StashBox configuration from schema/types/stash-box.graphql."""

    endpoint: str  # String!
    api_key: str  # String!
    name: str  # String!
    max_requests_per_minute: int | None | UnsetType = UNSET  # Int - defaults to 240


class StashBoxFingerprintSubmissionInput(StashInput):
    """Input for StashBox fingerprint submission from schema/types/stash-box.graphql."""

    scene_ids: list[str]  # [String!]!
    stash_box_endpoint: str | None | UnsetType = UNSET  # String


class StashBoxDraftSubmissionInput(StashInput):
    """Input for StashBox draft submission from schema/types/stash-box.graphql."""

    id: str  # String!
    stash_box_endpoint: str | None | UnsetType = UNSET  # String


class StashBoxValidationResult(BaseModel):
    """Result of StashBox validation from schema/types/config.graphql."""

    valid: bool | UnsetType = UNSET  # Boolean!
    status: str | UnsetType = UNSET  # String!
