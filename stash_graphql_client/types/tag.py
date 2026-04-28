"""Tag type from schema/types/tag.graphql."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, TypeVar

from pydantic import Field

from stash_graphql_client.fragments import fragment_store
from stash_graphql_client.logging import processing_logger as logger

from .base import (
    BulkUpdateIds,
    BulkUpdateStrings,
    StashInput,
    StashObject,
    StashResult,
    habtm,
    has_many,
)
from .files import StashID, StashIDInput
from .metadata import CustomFieldsInput
from .scalars import Map
from .unset import UNSET, UnsetType, is_set


if TYPE_CHECKING:
    from stash_graphql_client.client import StashClient

    from .gallery import Gallery
    from .group import Group
    from .image import Image
    from .markers import SceneMarker
    from .performer import Performer
    from .scene import Scene
    from .studio import Studio

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
    custom_fields: dict[str, Any] | None | UnsetType = UNSET  # Map (appSchema >= 77)


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
    custom_fields: CustomFieldsInput | None | UnsetType = (
        UNSET  # CustomFieldsInput (appSchema >= 77)
    )


class TagDestroyInput(StashInput):
    """Input for destroying a tag from schema/types/tag.graphql."""

    id: str  # ID!


class TagsMergeInput(StashInput):
    """Input for merging tags from schema/types/tag.graphql."""

    source: list[str]  # [ID!]!
    destination: str  # ID!
    values: TagUpdateInput | None | UnsetType = (
        UNSET  # TagUpdateInput (appSchema >= 84)
    )


class Tag(StashObject):
    """A label attachable to most entity types, with hierarchy support.

    ``parents`` and ``children`` are self-referential habtm lists.
    ``*_count`` fields are server-side resolvers — read-only.

    Content relationship list fields are queryable here but writable only via
    the owning entity's bulk update mutations; assignments fire bulk-update
    side mutations on ``save()`` (see ``__side_mutations__`` and the Side
    Mutations guide).
    """

    __type_name__ = "Tag"
    __short_repr_fields__ = ("name",)
    __update_input_type__ = TagUpdateInput
    __create_input_type__ = TagCreateInput
    __destroy_input_type__ = TagDestroyInput
    __merge_input_type__ = TagsMergeInput

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
        "custom_fields",  # tagUpdate via CustomFieldsInput diff (appSchema >= 77)
        # Side-mutation fields (excluded from to_input, handled by bulk updates)
        "scenes",  # bulkSceneUpdate with tag_ids
        "images",  # bulkImageUpdate with tag_ids
        "galleries",  # bulkGalleryUpdate with tag_ids
        "performers",  # bulkPerformerUpdate with tag_ids
        "groups",  # bulkGroupUpdate with tag_ids
        "scene_markers",  # bulkSceneMarkerUpdate with tag_ids
    }

    # Side mutations: content entities are writable via bulk updates using
    # BulkUpdateIds for tag_ids (TagUpdateInput has no scene_ids/image_ids/etc.).
    __side_mutations__: ClassVar[dict] = {
        "scenes": StashObject._make_bulk_relationship_handler(
            "scenes",
            "bulk_scene_update",
            "tag_ids",
        ),
        "images": StashObject._make_bulk_relationship_handler(
            "images",
            "bulk_image_update",
            "tag_ids",
        ),
        "galleries": StashObject._make_bulk_relationship_handler(
            "galleries",
            "bulk_gallery_update",
            "tag_ids",
        ),
        "performers": StashObject._make_bulk_relationship_handler(
            "performers",
            "bulk_performer_update",
            "tag_ids",
        ),
        "groups": StashObject._make_bulk_relationship_handler(
            "groups",
            "bulk_group_update",
            "tag_ids",
        ),
        "scene_markers": StashObject._make_bulk_relationship_handler(
            "scene_markers",
            "bulk_scene_marker_update",
            "tag_ids",
        ),
        "custom_fields": StashObject._make_custom_fields_handler(
            capability_attr="has_tag_custom_fields",
            update_method_name="update_tag",
        ),
    }

    # All fields are optional in client (fragment-based loading)
    name: str | None | UnsetType = UNSET  # String!
    sort_name: str | None | UnsetType = UNSET  # String
    description: str | None | UnsetType = UNSET  # String
    aliases: list[str] | None | UnsetType = UNSET  # [String!]!
    ignore_auto_tag: bool | None | UnsetType = UNSET  # Boolean!
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

    # Content relationship fields (queryable via Find* filters, writable via bulk updates)
    scenes: list[Scene] | UnsetType = UNSET  # via FindScenes filter
    images: list[Image] | UnsetType = UNSET  # via FindImages filter
    galleries: list[Gallery] | UnsetType = UNSET  # via FindGalleries filter
    performers: list[Performer] | UnsetType = UNSET  # via FindPerformers filter
    groups: list[Group] | UnsetType = UNSET  # via FindGroups filter
    studios: list[Studio] | UnsetType = UNSET  # already bidirectional with Studio.tags
    scene_markers: list[SceneMarker] | UnsetType = UNSET  # via FindSceneMarkers filter

    # Capability-gated fields (appSchema >= 77)
    custom_fields: Map | UnsetType = UNSET  # Map! (appSchema >= 77)

    # Field definitions with their conversion functions
    __field_conversions__ = {
        "name": str,
        "sort_name": str,
        "description": str,
        "aliases": list,
    }

    __relationships__ = {
        "parents": habtm("Tag", inverse_query_field="children"),
        "children": habtm("Tag", inverse_query_field="parents"),
        "stash_ids": habtm(
            "StashID",
            transform=lambda s: StashIDInput(endpoint=s.endpoint, stash_id=s.stash_id),
        ),
        "scenes": has_many("Scene", inverse_query_field="tags"),
        "images": has_many("Image", inverse_query_field="tags"),
        "galleries": has_many("Gallery", inverse_query_field="tags"),
        "performers": has_many("Performer", inverse_query_field="tags"),
        "groups": has_many("Group", inverse_query_field="tags"),
        "scene_markers": has_many("SceneMarker", inverse_query_field="tags"),
        "studios": has_many("Studio", inverse_query_field="tags"),
    }

    # =========================================================================
    # Convenience Helper Methods for Self-Referential Relationships
    # =========================================================================

    async def add_parent(self, parent_tag: Tag) -> None:
        """Add parent tag (syncs inverse automatically, call save() to persist)."""
        await self._add_to_relationship("parents", parent_tag)

    async def remove_parent(self, parent_tag: Tag) -> None:
        """Remove parent tag (syncs inverse automatically, call save() to persist)."""
        await self._remove_from_relationship("parents", parent_tag)

    async def add_child(self, child_tag: Tag) -> None:
        """Add child tag (syncs inverse automatically, call save() to persist)."""
        await self._add_to_relationship("children", child_tag)

    async def remove_child(self, child_tag: Tag) -> None:
        """Remove child tag (syncs inverse automatically, call save() to persist)."""
        await self._remove_from_relationship("children", child_tag)

    # =========================================================================
    # Convenience Helper Methods for Content Relationships
    # =========================================================================

    async def add_scene(self, scene: Scene) -> None:
        """Add scene (syncs inverse automatically, call save() to persist)."""
        await self._add_to_relationship("scenes", scene)

    async def remove_scene(self, scene: Scene) -> None:
        """Remove scene (syncs inverse automatically, call save() to persist)."""
        await self._remove_from_relationship("scenes", scene)

    async def add_image(self, image: Image) -> None:
        """Add image (syncs inverse automatically, call save() to persist)."""
        await self._add_to_relationship("images", image)

    async def remove_image(self, image: Image) -> None:
        """Remove image (syncs inverse automatically, call save() to persist)."""
        await self._remove_from_relationship("images", image)

    async def add_gallery(self, gallery: Gallery) -> None:
        """Add gallery (syncs inverse automatically, call save() to persist)."""
        await self._add_to_relationship("galleries", gallery)

    async def remove_gallery(self, gallery: Gallery) -> None:
        """Remove gallery (syncs inverse automatically, call save() to persist)."""
        await self._remove_from_relationship("galleries", gallery)

    async def add_performer(self, performer: Performer) -> None:
        """Add performer (syncs inverse automatically, call save() to persist)."""
        await self._add_to_relationship("performers", performer)

    async def remove_performer(self, performer: Performer) -> None:
        """Remove performer (syncs inverse automatically, call save() to persist)."""
        await self._remove_from_relationship("performers", performer)

    async def add_group(self, group: Group) -> None:
        """Add group (syncs inverse automatically, call save() to persist)."""
        await self._add_to_relationship("groups", group)

    async def remove_group(self, group: Group) -> None:
        """Remove group (syncs inverse automatically, call save() to persist)."""
        await self._remove_from_relationship("groups", group)

    async def add_scene_marker(self, marker: SceneMarker) -> None:
        """Add scene marker (syncs inverse automatically, call save() to persist)."""
        await self._add_to_relationship("scene_markers", marker)

    async def remove_scene_marker(self, marker: SceneMarker) -> None:
        """Remove scene marker (syncs inverse automatically, call save() to persist)."""
        await self._remove_from_relationship("scene_markers", marker)

    # =========================================================================
    # Tree Traversal Methods
    # =========================================================================

    async def get_all_descendants(self) -> list[Tag]:
        """Get all descendant tags recursively (children, grandchildren, etc.).

        Returns:
            List of all descendant tags in the hierarchy
        """
        descendants: list[Tag] = []
        visited: set[str] = set()

        async def collect_descendants(tag: Tag) -> None:
            """Recursively collect all descendants."""
            # Type narrowing: check if children is set and not None
            if is_set(tag.children) and tag.children is not None:
                for child in tag.children:
                    # Type narrowing: child.id should always be set for persisted tags
                    if child.id is not None and child.id not in visited:
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
            # Type narrowing: check if parents is set and not None
            if is_set(tag.parents) and tag.parents is not None:
                for parent in tag.parents:
                    # Type narrowing: parent.id should always be set for persisted tags
                    if parent.id is not None and parent.id not in visited:
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
            {fragment_store.FIND_TAGS_QUERY}
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
            tags_data = (result.get("findTags") or {}).get("tags") or []
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
            tags_data = (result.get("findTags") or {}).get("tags") or []

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
