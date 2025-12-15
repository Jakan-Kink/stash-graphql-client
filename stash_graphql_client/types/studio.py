"""Studio type from schema/types/studio.graphql."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field, model_validator

from .base import (
    BulkUpdateIds,
    BulkUpdateStrings,
    RelationshipMetadata,
    StashInput,
    StashObject,
    StashResult,
)
from .files import StashID, StashIDInput
from .unset import UNSET, UnsetType


if TYPE_CHECKING:
    from .tag import Tag


class StudioCreateInput(StashInput):
    """Input for creating studios."""

    # Required fields
    name: str  # String!

    # Optional fields
    urls: list[str] | None | UnsetType = UNSET  # [String!]
    parent_id: str | None | UnsetType = UNSET  # ID
    image: str | None | UnsetType = UNSET  # String (URL or base64)
    stash_ids: list[StashIDInput] | None | UnsetType = UNSET  # [StashIDInput!]
    rating100: int | None | UnsetType = Field(default=UNSET, ge=0, le=100)  # Int
    favorite: bool | None | UnsetType = UNSET  # Boolean
    details: str | None | UnsetType = UNSET  # String
    aliases: list[str] | None | UnsetType = UNSET  # [String!]
    tag_ids: list[str] | None | UnsetType = UNSET  # [ID!]
    ignore_auto_tag: bool | None | UnsetType = UNSET  # Boolean


class StudioUpdateInput(StashInput):
    """Input for updating studios."""

    # Required fields
    id: str  # ID!

    # Optional fields
    name: str | None | UnsetType = UNSET  # String
    urls: list[str] | None | UnsetType = UNSET  # [String!]
    parent_id: str | None | UnsetType = UNSET  # ID
    image: str | None | UnsetType = UNSET  # String (URL or base64)
    stash_ids: list[StashIDInput] | None | UnsetType = UNSET  # [StashIDInput!]
    rating100: int | None | UnsetType = Field(default=UNSET, ge=0, le=100)  # Int
    favorite: bool | None | UnsetType = UNSET  # Boolean
    details: str | None | UnsetType = UNSET  # String
    aliases: list[str] | None | UnsetType = UNSET  # [String!]
    tag_ids: list[str] | None | UnsetType = UNSET  # [ID!]
    ignore_auto_tag: bool | None | UnsetType = UNSET  # Boolean


class Studio(StashObject):
    """Studio type from schema/types/studio.graphql."""

    __type_name__ = "Studio"
    __update_input_type__ = StudioUpdateInput
    __create_input_type__ = StudioCreateInput

    # Fields to track for changes - only fields that can be written via input types
    __tracked_fields__ = {
        "name",  # StudioCreateInput/StudioUpdateInput
        "aliases",  # StudioCreateInput/StudioUpdateInput
        "tags",  # mapped to tag_ids
        "stash_ids",  # StudioCreateInput/StudioUpdateInput
        "urls",  # StudioCreateInput/StudioUpdateInput
        "parent_studio",  # mapped to parent_id
        "details",  # StudioCreateInput/StudioUpdateInput
        "rating100",  # StudioCreateInput/StudioUpdateInput
        "favorite",  # StudioCreateInput/StudioUpdateInput
        "ignore_auto_tag",  # StudioCreateInput/StudioUpdateInput
    }

    # All fields are optional in client (fragment-based loading)
    name: str | None | UnsetType = UNSET  # String!
    urls: list[str] | None | UnsetType = UNSET  # [String!]!
    parent_studio: Studio | None | UnsetType = UNSET  # Studio
    child_studios: list[Studio] | None | UnsetType = UNSET  # [Studio!]!
    aliases: list[str] | None | UnsetType = UNSET  # [String!]!
    tags: list[Tag] | None | UnsetType = UNSET  # [Tag!]!
    ignore_auto_tag: bool | None | UnsetType = UNSET  # Boolean!
    image_path: str | None | UnsetType = UNSET  # String (Resolver)
    scene_count: int | None | UnsetType = Field(
        default=UNSET, ge=0
    )  # Int! (Resolver with depth param)
    image_count: int | None | UnsetType = Field(
        default=UNSET, ge=0
    )  # Int! (Resolver with depth param)
    gallery_count: int | None | UnsetType = Field(
        default=UNSET, ge=0
    )  # Int! (Resolver with depth param)
    performer_count: int | None | UnsetType = Field(
        default=UNSET, ge=0
    )  # Int! (Resolver with depth param)
    group_count: int | None | UnsetType = Field(
        default=UNSET, ge=0
    )  # Int! (Resolver with depth param)
    stash_ids: list[StashID] | None | UnsetType = UNSET  # [StashID!]!
    rating100: int | None | UnsetType = Field(
        default=UNSET, ge=0, le=100
    )  # Int (1-100)
    favorite: bool | None | UnsetType = UNSET  # Boolean!
    details: str | None | UnsetType = UNSET  # String
    groups: list[Any] | None | UnsetType = (
        UNSET  # [Group!]! - Any to avoid circular import
    )
    o_counter: int | None | UnsetType = Field(default=UNSET, ge=0)  # Int

    @model_validator(mode="before")
    @classmethod
    def handle_deprecated_url(cls, data: Any) -> Any:
        """Convert deprecated 'url' field to 'urls' list for backward compatibility."""
        # Pydantic always passes dict to before validators
        # Handle deprecated single url field
        if data.get("url"):
            if "urls" not in data or not data["urls"]:
                # Migrate url to urls
                data["urls"] = [data["url"]]
            elif data["url"] not in data["urls"]:
                # Ensure url is in urls
                data["urls"].insert(0, data["url"])
            # Remove the deprecated field
            data.pop("url", None)
        elif "url" in data:
            # url exists but is None/empty, just remove it
            data.pop("url", None)
        return data

    # Field definitions with their conversion functions
    __field_conversions__ = {
        "name": str,
        "urls": list,
        "aliases": list,
        "details": str,
    }

    __relationships__ = {
        "parent_studio": RelationshipMetadata(
            target_field="parent_id",
            is_list=False,
            query_field="parent_studio",
            inverse_type="Studio",  # Self-referential
            inverse_query_field="child_studios",
            query_strategy="direct_field",
            notes="Self-referential parent/child hierarchy",
        ),
        "tags": RelationshipMetadata(
            target_field="tag_ids",
            is_list=True,
            query_field="tags",
            inverse_type="Tag",
            inverse_query_field="studios",
            query_strategy="direct_field",
            notes="Backend auto-syncs studio.tags and tag.studios",
        ),
        "stash_ids": RelationshipMetadata(
            target_field="stash_ids",
            is_list=True,
            transform=lambda s: StashIDInput(endpoint=s.endpoint, stash_id=s.stash_id),
            query_field="stash_ids",
            notes="Requires transform to StashIDInput for mutations",
        ),
    }


class BulkStudioUpdateInput(StashInput):
    """Input for bulk updating studios from schema/types/studio.graphql."""

    ids: list[str]  # [ID!]!
    urls: BulkUpdateStrings | None | UnsetType = UNSET  # BulkUpdateStrings
    parent_id: str | None | UnsetType = UNSET  # ID
    rating100: int | None | UnsetType = Field(
        default=UNSET, ge=0, le=100
    )  # Int (1-100)
    favorite: bool | None | UnsetType = UNSET  # Boolean
    details: str | None | UnsetType = UNSET  # String
    tag_ids: BulkUpdateIds | None | UnsetType = UNSET  # BulkUpdateIds
    ignore_auto_tag: bool | None | UnsetType = UNSET  # Boolean


class StudioDestroyInput(StashInput):
    """Input for destroying a studio from schema/types/studio.graphql."""

    id: str  # ID!


class FindStudiosResultType(StashResult):
    """Result type for finding studios from schema/types/studio.graphql."""

    count: int | None | UnsetType = UNSET  # Int!
    studios: list[Studio] | None | UnsetType = UNSET  # [Studio!]!
