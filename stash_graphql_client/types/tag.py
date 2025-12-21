"""Tag type from schema/types/tag.graphql."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from pydantic import Field

from stash_graphql_client import fragments
from stash_graphql_client.logging import processing_logger as logger

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
    from stash_graphql_client.client import StashClient

T = TypeVar("T", bound="Tag")

# Note: metadata imports removed - not available in this project
# from metadata import Hashtag


class TagCreateInput(StashInput):
    """Input for creating tags."""

    # Required fields
    name: str  # String!

    # Optional fields
    sort_name: str | None | UnsetType = UNSET  # String
    description: str | None | UnsetType = UNSET  # String
    aliases: list[str] | None | UnsetType = UNSET  # [String!]
    ignore_auto_tag: bool | None | UnsetType = UNSET  # Boolean
    favorite: bool | None | UnsetType = UNSET  # Boolean
    image: str | None | UnsetType = UNSET  # String (URL or base64)
    stash_ids: list[StashIDInput] | None | UnsetType = UNSET  # [StashIDInput!]
    parent_ids: list[str] | None | UnsetType = UNSET  # [ID!]
    child_ids: list[str] | None | UnsetType = UNSET  # [ID!]


class TagUpdateInput(StashInput):
    """Input for updating tags."""

    # Required fields
    id: str  # ID!

    # Optional fields
    name: str | None | UnsetType = UNSET  # String
    sort_name: str | None | UnsetType = UNSET  # String
    description: str | None | UnsetType = UNSET  # String
    aliases: list[str] | None | UnsetType = UNSET  # [String!]
    ignore_auto_tag: bool | None | UnsetType = UNSET  # Boolean
    favorite: bool | None | UnsetType = UNSET  # Boolean
    image: str | None | UnsetType = UNSET  # String (URL or base64)
    stash_ids: list[StashIDInput] | None | UnsetType = UNSET  # [StashIDInput!]
    parent_ids: list[str] | None | UnsetType = UNSET  # [ID!]
    child_ids: list[str] | None | UnsetType = UNSET  # [ID!]


class Tag(StashObject):
    """Tag type from schema/types/tag.graphql."""

    __type_name__ = "Tag"
    __update_input_type__ = TagUpdateInput
    __create_input_type__ = TagCreateInput

    # Fields to track for changes - only fields that can be written via input types
    __tracked_fields__ = {
        "name",  # TagCreateInput/TagUpdateInput
        "sort_name",  # TagCreateInput/TagUpdateInput
        "aliases",  # TagCreateInput/TagUpdateInput
        "description",  # TagCreateInput/TagUpdateInput
        "parents",  # mapped to parent_ids
        "children",  # mapped to child_ids
        "favorite",  # TagCreateInput/TagUpdateInput
        "ignore_auto_tag",  # TagCreateInput/TagUpdateInput
        "stash_ids",  # TagCreateInput/TagUpdateInput
    }

    # All fields are optional in client (fragment-based loading)
    name: str | None | UnsetType = UNSET  # String!
    sort_name: str | None | UnsetType = UNSET  # String
    description: str | None | UnsetType = UNSET  # String
    aliases: list[str] | None | UnsetType = UNSET  # [String!]!
    ignore_auto_tag: bool | None | UnsetType = UNSET  # Boolean!
    created_at: str | None | UnsetType = UNSET  # Time!
    updated_at: str | None | UnsetType = UNSET  # Time!
    favorite: bool | None | UnsetType = UNSET  # Boolean!
    stash_ids: list[StashID] | None | UnsetType = UNSET  # [StashID!]!
    image_path: str | None | UnsetType = UNSET  # String (Resolver)
    scene_count: int | None | UnsetType = Field(
        default=UNSET, ge=0
    )  # Int! (Resolver with depth param)
    scene_marker_count: int | None | UnsetType = Field(
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
    studio_count: int | None | UnsetType = Field(
        default=UNSET, ge=0
    )  # Int! (Resolver with depth param)
    group_count: int | None | UnsetType = Field(
        default=UNSET, ge=0
    )  # Int! (Resolver with depth param)
    parents: list[Tag] | None | UnsetType = UNSET  # [Tag!]!
    children: list[Tag] | None | UnsetType = UNSET  # [Tag!]!
    parent_count: int | None | UnsetType = Field(default=UNSET, ge=0)  # Int! (Resolver)
    child_count: int | None | UnsetType = Field(default=UNSET, ge=0)  # Int! (Resolver)

    # Field definitions with their conversion functions
    __field_conversions__ = {
        "name": str,
        "sort_name": str,
        "description": str,
        "aliases": list,
    }

    __relationships__ = {
        # Self-referential parent/child hierarchy (Pattern A: direct fields)
        "parents": RelationshipMetadata(
            target_field="parent_ids",
            is_list=True,
            query_field="parents",
            inverse_type="Tag",  # Self-referential!
            inverse_query_field="children",
            query_strategy="direct_field",
            notes="Backend auto-syncs both parent_ids and child_ids bidirectionally",
        ),
        "children": RelationshipMetadata(
            target_field="child_ids",
            is_list=True,
            query_field="children",
            inverse_type="Tag",  # Self-referential!
            inverse_query_field="parents",
            query_strategy="direct_field",
            notes="Backend auto-syncs both child_ids and parent_ids bidirectionally",
        ),
        # Special case: Complex transform for StashID
        "stash_ids": RelationshipMetadata(
            target_field="stash_ids",
            is_list=True,
            transform=lambda s: StashIDInput(endpoint=s.endpoint, stash_id=s.stash_id),
            query_field="stash_ids",
            notes="Requires transform to StashIDInput for mutations",
        ),
    }

    # =========================================================================
    # Convenience Helper Methods for Self-Referential Relationships
    # =========================================================================

    def add_parent(self, parent_tag: Tag) -> None:
        """Add a parent tag to this tag's parents list.

        In-memory operation only. Call store.save(tag) to persist changes.
        Automatically maintains bidirectional consistency by updating parent_tag.children.

        Args:
            parent_tag: The Tag instance to add as a parent

        Example:
            >>> child_tag = await client.find_tag("child_id")
            >>> parent_tag = await client.find_tag("parent_id")
            >>> child_tag.add_parent(parent_tag)  # Also updates parent_tag.children
            >>> await store.save(child_tag)  # Persist the change
        """
        if parent_tag not in self.parents:
            self.parents.append(parent_tag)
            # Maintain bidirectional consistency
            if self not in parent_tag.children:
                parent_tag.children.append(self)

    def remove_parent(self, parent_tag: Tag) -> None:
        """Remove a parent tag from this tag's parents list.

        In-memory operation only. Call store.save(tag) to persist changes.
        Automatically maintains bidirectional consistency by updating parent_tag.children.

        Args:
            parent_tag: The Tag instance to remove as a parent

        Example:
            >>> child_tag.remove_parent(parent_tag)  # Also updates parent_tag.children
            >>> await store.save(child_tag)  # Persist the change
        """
        if parent_tag in self.parents:
            self.parents.remove(parent_tag)
            # Maintain bidirectional consistency
            if self in parent_tag.children:
                parent_tag.children.remove(self)

    def add_child(self, child_tag: Tag) -> None:
        """Add a child tag to this tag's children list.

        In-memory operation only. Call store.save(tag) to persist changes.
        Automatically maintains bidirectional consistency by updating child_tag.parents.

        Args:
            child_tag: The Tag instance to add as a child

        Example:
            >>> parent_tag = await client.find_tag("parent_id")
            >>> child_tag = await client.find_tag("child_id")
            >>> parent_tag.add_child(child_tag)  # Also updates child_tag.parents
            >>> await store.save(parent_tag)  # Persist the change
        """
        if child_tag not in self.children:
            self.children.append(child_tag)
            # Maintain bidirectional consistency
            if self not in child_tag.parents:
                child_tag.parents.append(self)

    def remove_child(self, child_tag: Tag) -> None:
        """Remove a child tag from this tag's children list.

        In-memory operation only. Call store.save(tag) to persist changes.
        Automatically maintains bidirectional consistency by updating child_tag.parents.

        Args:
            child_tag: The Tag instance to remove as a child

        Example:
            >>> parent_tag.remove_child(child_tag)  # Also updates child_tag.parents
            >>> await store.save(parent_tag)  # Persist the change
        """
        if child_tag in self.children:
            self.children.remove(child_tag)
            # Maintain bidirectional consistency
            if self in child_tag.parents:
                child_tag.parents.remove(self)

    async def get_all_descendants(self) -> list[Tag]:
        """Get all descendant tags recursively (children, grandchildren, etc.).

        Returns:
            List of all descendant tags in the hierarchy
        """
        descendants: list[Tag] = []
        visited: set[str] = set()

        async def collect_descendants(tag: Tag) -> None:
            """Recursively collect all descendants."""
            for child in tag.children:
                if child.id not in visited:
                    visited.add(child.id)
                    descendants.append(child)
                    await collect_descendants(child)

        await collect_descendants(self)
        return descendants

    async def get_all_ancestors(self) -> list[Tag]:
        """Get all ancestor tags recursively (parents, grandparents, etc.).

        Returns:
            List of all ancestor tags in the hierarchy
        """
        ancestors: list[Tag] = []
        visited: set[str] = set()

        async def collect_ancestors(tag: Tag) -> None:
            """Recursively collect all ancestors."""
            for parent in tag.parents:
                if parent.id not in visited:
                    visited.add(parent.id)
                    ancestors.append(parent)
                    await collect_ancestors(parent)

        await collect_ancestors(self)
        return ancestors

    @classmethod
    async def find_by_name(
        cls: type[T],
        client: StashClient,
        name: str,
    ) -> T | None:
        """Find tag by name (case-insensitive search).

        Args:
            client: "StashClient" instance
            name: Tag name to search for

        Returns:
            Tag instance if found, None otherwise
        """
        # Build query using proper TAG_FIELDS fragment
        query = f"""
            {fragments.FIND_TAGS_QUERY}
        """
        try:
            # Try exact match first (EQUALS modifier)
            result = await client.execute(
                query,
                {
                    "filter": None,
                    "tag_filter": {"name": {"value": name, "modifier": "EQUALS"}},
                },
            )
            tags_data = result.get("findTags", {}).get("tags", [])
            if tags_data:
                logger.debug(f"Found tag by exact match: {name}")
                return cls(**tags_data[0])

            # If no exact match, try case-insensitive search with INCLUDES
            # This handles cases where Stash has "diva" but we're searching for "Diva"
            result = await client.execute(
                query,
                {
                    "filter": None,
                    "tag_filter": {"name": {"value": name, "modifier": "INCLUDES"}},
                },
            )
            tags_data = result.get("findTags", {}).get("tags", [])

            # Filter results to find case-insensitive exact match
            name_lower = name.lower()
            for tag_data in tags_data:
                if tag_data.get("name", "").lower() == name_lower:
                    logger.debug(
                        f"Found tag by case-insensitive match: {name} -> {tag_data.get('name')}"
                    )
                    return cls(**tag_data)

            logger.debug(f"No tag found for: {name}")
            return None
        except Exception as e:
            logger.error(f"Error searching for tag '{name}': {e}")
            return None


class TagDestroyInput(StashInput):
    """Input for destroying a tag from schema/types/tag.graphql."""

    id: str  # ID!


class TagsMergeInput(StashInput):
    """Input for merging tags from schema/types/tag.graphql."""

    source: list[str]  # [ID!]!
    destination: str  # ID!


class BulkTagUpdateInput(StashInput):
    """Input for bulk updating tags from schema/types/tag.graphql."""

    ids: list[str]  # [ID!]!
    description: str | None | UnsetType = UNSET  # String
    aliases: BulkUpdateStrings | None | UnsetType = UNSET  # BulkUpdateStrings
    ignore_auto_tag: bool | None | UnsetType = UNSET  # Boolean
    favorite: bool | None | UnsetType = UNSET  # Boolean
    parent_ids: BulkUpdateIds | None | UnsetType = UNSET  # BulkUpdateIds
    child_ids: BulkUpdateIds | None | UnsetType = UNSET  # BulkUpdateIds


class FindTagsResultType(StashResult):
    """Result type for finding tags from schema/types/tag.graphql."""

    count: int  # Int!
    tags: list[Tag]  # [Tag!]!
