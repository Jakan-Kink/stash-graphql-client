"""Group types from schema/types/group.graphql."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from .base import (
    BulkUpdateIds,
    BulkUpdateStrings,
    RelationshipMetadata,
    StashInput,
    StashObject,
    StashResult,
)
from .enums import BulkUpdateIdMode
from .unset import UNSET, UnsetType


if TYPE_CHECKING:
    from .scene import Scene
    from .studio import Studio
    from .tag import Tag


class GroupDescription(BaseModel):
    """Group description type from schema."""

    group: Group | UnsetType = UNSET  # Group!
    description: str | None | UnsetType = UNSET  # String


class GroupCreateInput(StashInput):
    """Input for creating groups from schema/types/group.graphql."""

    # Required fields
    name: str | UnsetType = UNSET  # String!

    # Optional fields
    aliases: str | None | UnsetType = UNSET  # String
    duration: int | None | UnsetType = UNSET  # Int (in seconds)
    date: str | None | UnsetType = UNSET  # String
    rating100: int | None | UnsetType = Field(
        default=UNSET, ge=0, le=100
    )  # Int (1-100)
    studio_id: str | None | UnsetType = UNSET  # ID
    director: str | None | UnsetType = UNSET  # String
    synopsis: str | None | UnsetType = UNSET  # String
    urls: list[str] | None | UnsetType = UNSET  # [String!]
    tag_ids: list[str] | None | UnsetType = UNSET  # [ID!]
    containing_groups: list[GroupDescriptionInput] | None | UnsetType = (
        UNSET  # [GroupDescriptionInput!]
    )
    sub_groups: list[GroupDescriptionInput] | None | UnsetType = (
        UNSET  # [GroupDescriptionInput!]
    )
    front_image: str | None | UnsetType = (
        UNSET  # String (URL or base64 encoded data URL)
    )
    back_image: str | None | UnsetType = UNSET  # String (URL or base64)


class GroupUpdateInput(StashInput):
    """Input for updating groups from schema/types/group.graphql."""

    # Required fields
    id: str  # ID!

    # Optional fields
    name: str | None | UnsetType = UNSET  # String
    aliases: str | None | UnsetType = UNSET  # String
    duration: int | None | UnsetType = UNSET  # Int (in seconds)
    date: str | None | UnsetType = UNSET  # String
    rating100: int | None | UnsetType = Field(
        default=UNSET, ge=0, le=100
    )  # Int (1-100)
    studio_id: str | None | UnsetType = UNSET  # ID
    director: str | None | UnsetType = UNSET  # String
    synopsis: str | None | UnsetType = UNSET  # String
    urls: list[str] | None | UnsetType = UNSET  # [String!]
    tag_ids: list[str] | None | UnsetType = UNSET  # [ID!]
    containing_groups: list[GroupDescriptionInput] | None | UnsetType = (
        UNSET  # [GroupDescriptionInput!]
    )
    sub_groups: list[GroupDescriptionInput] | None | UnsetType = (
        UNSET  # [GroupDescriptionInput!]
    )
    front_image: str | None | UnsetType = (
        UNSET  # String (URL or base64 encoded data URL)
    )
    back_image: str | None | UnsetType = (
        UNSET  # String (URL or base64 encoded data URL)
    )


class Group(StashObject):
    """Group type from schema."""

    __type_name__ = "Group"
    __update_input_type__ = GroupUpdateInput
    __create_input_type__ = GroupCreateInput

    # Fields to track for changes - only fields that can be written via input types
    __tracked_fields__ = {
        "name",  # GroupCreateInput/GroupUpdateInput
        "urls",  # GroupCreateInput/GroupUpdateInput
        "tags",  # mapped to tag_ids
        "containing_groups",  # GroupCreateInput/GroupUpdateInput
        "sub_groups",  # GroupCreateInput/GroupUpdateInput
        "aliases",  # GroupCreateInput/GroupUpdateInput
        "duration",  # GroupCreateInput/GroupUpdateInput
        "date",  # GroupCreateInput/GroupUpdateInput
        "studio",  # mapped to studio_id
        "director",  # GroupCreateInput/GroupUpdateInput
        "synopsis",  # GroupCreateInput/GroupUpdateInput
    }

    # Required fields
    name: str | UnsetType = UNSET  # String!
    urls: list[str] | UnsetType = Field(default=UNSET)  # [String!]!
    tags: list[Tag] | UnsetType = Field(default=UNSET)  # [Tag!]!
    containing_groups: list[GroupDescription] | UnsetType = Field(
        default=UNSET
    )  # [GroupDescription!]!
    sub_groups: list[GroupDescription] | UnsetType = Field(
        default=UNSET
    )  # [GroupDescription!]!
    scenes: list[Scene] | UnsetType = Field(default=UNSET)  # [Scene!]!

    # Optional fields
    aliases: str | None | UnsetType = UNSET  # String
    duration: int | None | UnsetType = UNSET  # Int (in seconds)
    date: str | None | UnsetType = UNSET  # String
    rating100: int | None | UnsetType = Field(
        default=UNSET, ge=0, le=100
    )  # Int (0-100)
    studio: Studio | None | UnsetType = UNSET  # Studio
    director: str | None | UnsetType = UNSET  # String
    synopsis: str | None | UnsetType = UNSET  # String
    front_image_path: str | None | UnsetType = UNSET  # String (Resolver)
    back_image_path: str | None | UnsetType = UNSET  # String (Resolver)
    scene_count: int | None | UnsetType = Field(
        default=UNSET, ge=0
    )  # Int! (Resolver with optional depth)
    performer_count: int | None | UnsetType = Field(
        default=UNSET, ge=0
    )  # Int! (Resolver with optional depth)
    sub_group_count: int | None | UnsetType = Field(
        default=UNSET, ge=0
    )  # Int! (Resolver with optional depth)
    o_counter: int | None | UnsetType = Field(default=UNSET, ge=0)  # Int (Resolver)

    # Field definitions with their conversion functions
    __field_conversions__ = {
        "name": str,
        "urls": list,
        "aliases": str,
        "duration": int,
        "date": str,
        "rating100": int,
        "director": str,
        "synopsis": str,
    }

    __relationships__ = {
        "studio": RelationshipMetadata(
            target_field="studio_id",
            is_list=False,
            query_field="studio",
            inverse_type="Studio",
            query_strategy="filter_query",
            filter_query_hint="findGroups(group_filter={studios: {value: [studio_id]}})",
            notes="Studio has group_count and filter queries, not direct groups field",
        ),
        "tags": RelationshipMetadata(
            target_field="tag_ids",
            is_list=True,
            query_field="tags",
            inverse_type="Tag",
            inverse_query_field="groups",
            query_strategy="direct_field",
            notes="Backend auto-syncs group.tags and tag.groups",
        ),
        # Pattern C: Complex objects with metadata
        "containing_groups": RelationshipMetadata(
            target_field="containing_groups",
            is_list=True,
            transform=lambda g: GroupDescriptionInput(
                group_id=g.group.id if hasattr(g, "group") else g.id,
                description=g.description if hasattr(g, "description") else None,
            ),
            query_field="containing_groups",
            inverse_type="Group",
            inverse_query_field="sub_groups",
            query_strategy="complex_object",
            notes="Uses GroupDescription wrapper with nested group + description metadata",
        ),
        "sub_groups": RelationshipMetadata(
            target_field="sub_groups",
            is_list=True,
            transform=lambda g: GroupDescriptionInput(
                group_id=g.group.id if hasattr(g, "group") else g.id,
                description=g.description if hasattr(g, "description") else None,
            ),
            query_field="sub_groups",
            inverse_type="Group",
            inverse_query_field="containing_groups",
            query_strategy="complex_object",
            notes="Uses GroupDescription wrapper with nested group + description metadata",
        ),
    }


class GroupDescriptionInput(StashInput):
    """Input for group description."""

    group_id: str | UnsetType = UNSET  # ID!
    description: str | None | UnsetType = UNSET  # String


class BulkUpdateGroupDescriptionsInput(StashInput):
    """Input for bulk updating group descriptions."""

    groups: list[GroupDescriptionInput] | UnsetType = UNSET  # [GroupDescriptionInput!]!
    mode: BulkUpdateIdMode | UnsetType = UNSET  # BulkUpdateIdMode!


class BulkGroupUpdateInput(StashInput):
    """Input for bulk updating groups."""

    client_mutation_id: str | None | UnsetType = Field(
        default=UNSET, alias="clientMutationId"
    )  # String
    ids: list[str] | UnsetType = UNSET  # [ID!]
    rating100: int | None | UnsetType = Field(default=UNSET, ge=0, le=100)  # Int
    studio_id: str | None | UnsetType = UNSET  # ID
    director: str | None | UnsetType = UNSET  # String
    urls: BulkUpdateStrings | None | UnsetType = UNSET  # BulkUpdateStrings
    tag_ids: BulkUpdateIds | None | UnsetType = UNSET  # BulkUpdateIds
    containing_groups: BulkUpdateGroupDescriptionsInput | None | UnsetType = (
        UNSET  # BulkUpdateGroupDescriptionsInput
    )
    sub_groups: BulkUpdateGroupDescriptionsInput | None | UnsetType = (
        UNSET  # BulkUpdateGroupDescriptionsInput
    )


class GroupDestroyInput(StashInput):
    """Input for destroying groups."""

    id: str  # ID!


class ReorderSubGroupsInput(StashInput):
    """Input for reordering sub groups from schema/types/group.graphql.

    Fields:
        group_id: str of the group to reorder sub groups for
        sub_group_ids: strs of the sub groups to reorder. These must be a subset of the current sub groups.
            Sub groups will be inserted in this order at the insert_index.
        insert_at_id: The sub-group ID at which to insert the sub groups
        insert_after: If true, the sub groups will be inserted after the insert_index,
            otherwise they will be inserted before"""

    group_id: str | UnsetType = UNSET  # ID!
    sub_group_ids: list[str] | UnsetType = UNSET  # [ID!]!
    insert_at_id: str | UnsetType = UNSET  # ID!
    insert_after: bool | UnsetType = UNSET  # Boolean


class FindGroupsResultType(StashResult):
    """Result type for finding groups."""

    count: int | UnsetType = UNSET  # Int!
    groups: list[Group] | UnsetType = UNSET  # [Group!]!


class GroupSubGroupAddInput(StashInput):
    """Input for adding sub groups from schema/types/group.graphql.

    Fields:
        containing_group_id: str of the group to add sub groups to
        sub_groups: List of sub groups to add
        insert_index: The index at which to insert the sub groups. If not provided,
            the sub groups will be appended to the end"""

    containing_group_id: str | UnsetType = UNSET  # ID!
    sub_groups: list[GroupDescriptionInput] | UnsetType = (
        UNSET  # [GroupDescriptionInput!]!
    )
    insert_index: int | None | UnsetType = UNSET  # Int


class GroupSubGroupRemoveInput(StashInput):
    """Input for removing sub groups."""

    containing_group_id: str | UnsetType = UNSET  # ID!
    sub_group_ids: list[str] | UnsetType = UNSET  # [ID!]!
