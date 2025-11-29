"""Tag type from schema/types/tag.graphql."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from pydantic import BaseModel, Field

from stash_graphql_client.logging import processing_logger as logger

from .base import StashObject


if TYPE_CHECKING:
    from stash_graphql_client.client import StashClient

T = TypeVar("T", bound="Tag")

# Note: metadata imports removed - not available in this project
# from metadata import Hashtag


class TagCreateInput(BaseModel):
    """Input for creating tags."""

    # Required fields
    name: str  # String!

    # Optional fields
    description: str | None = None  # String
    aliases: list[str] | None = None  # [String!]
    ignore_auto_tag: bool | None = None  # Boolean
    image: str | None = None  # String (URL or base64)
    parent_ids: list[str] | None = None  # [ID!]
    child_ids: list[str] | None = None  # [ID!]


class TagUpdateInput(BaseModel):
    """Input for updating tags."""

    # Required fields
    id: str  # ID!

    # Optional fields
    name: str | None = None  # String
    description: str | None = None  # String
    aliases: list[str] | None = None  # [String!]
    ignore_auto_tag: bool | None = None  # Boolean
    image: str | None = None  # String (URL or base64)
    parent_ids: list[str] | None = None  # [ID!]
    child_ids: list[str] | None = None  # [ID!]


class Tag(StashObject):
    """Tag type from schema/types/tag.graphql."""

    __type_name__ = "Tag"
    __update_input_type__ = TagUpdateInput
    __create_input_type__ = TagCreateInput

    # Fields to track for changes - only fields that can be written via input types
    __tracked_fields__ = {
        "name",  # TagCreateInput/TagUpdateInput
        "aliases",  # TagCreateInput/TagUpdateInput
        "description",  # TagCreateInput/TagUpdateInput
        "parents",  # mapped to parent_ids
        "children",  # mapped to child_ids
    }

    # Required fields
    name: str  # String!
    aliases: list[str] = Field(default_factory=list)  # [String!]!
    parents: list[Tag] = Field(default_factory=list)  # [Tag!]!
    children: list[Tag] = Field(default_factory=list)  # [Tag!]!

    # Optional fields
    description: str | None = None  # String
    image_path: str | None = None  # String (Resolver)

    # Field definitions with their conversion functions
    __field_conversions__ = {
        "name": str,
        "description": str,
        "aliases": list,
    }

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
        # Circular import: fragments uses types for GraphQL schema
        from stash_graphql_client import fragments

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

    __relationships__ = {
        # Standard ID relationships
        "parents": ("parent_ids", True, None),  # (target_field, is_list, transform)
        "children": ("child_ids", True, None),
    }


class TagDestroyInput(BaseModel):
    """Input for destroying a tag from schema/types/tag.graphql."""

    id: str  # ID!


class TagsMergeInput(BaseModel):
    """Input for merging tags from schema/types/tag.graphql."""

    source: list[str]  # [ID!]!
    destination: str  # ID!


class BulkTagUpdateInput(BaseModel):
    """Input for bulk updating tags from schema/types/tag.graphql."""

    ids: list[str]  # [ID!]!
    description: str | None = None  # String
    aliases: list[str] | None = None  # [String!]
    ignore_auto_tag: bool | None = None  # Boolean
    favorite: bool | None = None  # Boolean
    parent_ids: list[str] | None = None  # [ID!]
    child_ids: list[str] | None = None  # [ID!]


class FindTagsResultType(BaseModel):
    """Result type for finding tags from schema/types/tag.graphql."""

    count: int  # Int!
    tags: list[Tag]  # [Tag!]!
