"""Studio type from schema/types/studio.graphql."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

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
from .metadata import CustomFieldsInput
from .scalars import Map
from .unset import UNSET, UnsetType


if TYPE_CHECKING:
    from .gallery import Gallery
    from .group import Group
    from .image import Image
    from .scene import Scene
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
    organized: bool | None | UnsetType = UNSET  # Boolean (appSchema >= 80)
    custom_fields: dict[str, Any] | None | UnsetType = UNSET  # Map (appSchema >= 76)


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
    organized: bool | None | UnsetType = UNSET  # Boolean (appSchema >= 80)
    custom_fields: CustomFieldsInput | None | UnsetType = (
        UNSET  # CustomFieldsInput (appSchema >= 76)
    )


class StudioDestroyInput(StashInput):
    """Input for destroying a studio from schema/types/studio.graphql."""

    id: str  # ID!


class Studio(StashObject):
    """Studio type from schema/types/studio.graphql."""

    __type_name__ = "Studio"
    __short_repr_fields__ = ("name",)
    __update_input_type__ = StudioUpdateInput
    __create_input_type__ = StudioCreateInput
    __destroy_input_type__ = StudioDestroyInput

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
        "organized",  # StudioUpdateInput (appSchema >= 80)
        # Side-mutation fields (excluded from to_input, handled by bulk updates)
        "scenes",  # bulkSceneUpdate with studio_id
        "images",  # bulkImageUpdate with studio_id
        "galleries",  # bulkGalleryUpdate with studio_id
        "groups",  # bulkGroupUpdate with studio_id
    }

    # Side mutations: content entities are writable via bulk updates using scalar
    # studio_id FK (StudioUpdateInput has no scene_ids/image_ids/gallery_ids/group_ids).
    __side_mutations__: ClassVar[dict] = {
        "scenes": StashObject._make_bulk_relationship_handler(
            "scenes",
            "bulk_scene_update",
            "studio_id",
            use_bulk_ids=False,
        ),
        "images": StashObject._make_bulk_relationship_handler(
            "images",
            "bulk_image_update",
            "studio_id",
            use_bulk_ids=False,
        ),
        "galleries": StashObject._make_bulk_relationship_handler(
            "galleries",
            "bulk_gallery_update",
            "studio_id",
            use_bulk_ids=False,
        ),
        "groups": StashObject._make_bulk_relationship_handler(
            "groups",
            "bulk_group_update",
            "studio_id",
            use_bulk_ids=False,
        ),
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
    groups: list[Group] | None | UnsetType = UNSET  # [Group!]!
    scenes: list[Scene] | None | UnsetType = UNSET  # queryable via FindScenes filter
    images: list[Image] | None | UnsetType = UNSET  # queryable via FindImages filter
    galleries: list[Gallery] | None | UnsetType = (
        UNSET  # queryable via FindGalleries filter
    )
    o_counter: int | None | UnsetType = Field(default=UNSET, ge=0)  # Int

    # Capability-gated fields
    custom_fields: Map | UnsetType = UNSET  # Map! (appSchema >= 76)
    organized: bool | None | UnsetType = UNSET  # Boolean (appSchema >= 80)

    @model_validator(mode="before")
    @classmethod
    def handle_deprecated_url(cls, data: Any) -> Any:
        """Convert deprecated 'url' field to 'urls' list for backward compatibility."""
        if not isinstance(data, dict):
            return data
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
        "rating100": int,
        "favorite": bool,
        "ignore_auto_tag": bool,
        "organized": bool,
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
        "child_studios": RelationshipMetadata(
            target_field="",  # Read-only: no child_ids in StudioInput (managed via parent_id on children)
            is_list=True,
            query_field="child_studios",
            inverse_type="Studio",  # Self-referential
            inverse_query_field="parent_studio",
            query_strategy="direct_field",
            notes="Self-referential parent/child hierarchy. Children managed via parent_id on child studios.",
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
        # Side-mutation relationships: writable via bulk updates on content entities
        "scenes": RelationshipMetadata(
            target_field="scene_ids",
            is_list=True,
            query_field="scenes",
            inverse_type="Scene",
            inverse_query_field="studio",
            query_strategy="filter_query",
            filter_query_hint="findScenes(scene_filter={studios: {value: [studio_id]}})",
            notes="Writable via bulkSceneUpdate(studio_id). Direct FK (scenes.studio_id).",
        ),
        "images": RelationshipMetadata(
            target_field="image_ids",
            is_list=True,
            query_field="images",
            inverse_type="Image",
            inverse_query_field="studio",
            query_strategy="filter_query",
            filter_query_hint="findImages(image_filter={studios: {value: [studio_id]}})",
            notes="Writable via bulkImageUpdate(studio_id). Direct FK (images.studio_id).",
        ),
        "galleries": RelationshipMetadata(
            target_field="gallery_ids",
            is_list=True,
            query_field="galleries",
            inverse_type="Gallery",
            inverse_query_field="studio",
            query_strategy="filter_query",
            filter_query_hint="findGalleries(gallery_filter={studios: {value: [studio_id]}})",
            notes="Writable via bulkGalleryUpdate(studio_id). Direct FK (galleries.studio_id).",
        ),
        "groups": RelationshipMetadata(
            target_field="group_ids",
            is_list=True,
            query_field="groups",
            inverse_type="Group",
            inverse_query_field="studio",
            query_strategy="filter_query",
            filter_query_hint="findGroups(group_filter={studios: {value: [studio_id]}})",
            notes="Writable via bulkGroupUpdate(studio_id). Direct FK (groups.studio_id).",
        ),
    }

    # =========================================================================
    # Convenience Helper Methods for Bidirectional Relationships
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

    async def add_group(self, group: Group) -> None:
        """Add group (syncs inverse automatically, call save() to persist)."""
        await self._add_to_relationship("groups", group)

    async def remove_group(self, group: Group) -> None:
        """Remove group (syncs inverse automatically, call save() to persist)."""
        await self._remove_from_relationship("groups", group)

    async def set_parent_studio(self, parent: Studio | None) -> None:
        """Set parent studio (syncs inverse automatically, call save() to persist)."""
        if parent is None:
            self.parent_studio = None
        else:
            await self._add_to_relationship("parent_studio", parent)

    async def add_child_studio(self, child: Studio) -> None:
        """Add child studio (syncs inverse automatically, call save() to persist)."""
        await self._add_to_relationship("child_studios", child)

    async def remove_child_studio(self, child: Studio) -> None:
        """Remove child studio (syncs inverse automatically, call save() to persist)."""
        await self._remove_from_relationship("child_studios", child)


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
    organized: bool | None | UnsetType = UNSET  # Boolean (appSchema >= 84)


class FindStudiosResultType(StashResult):
    """Result type for finding studios from schema/types/studio.graphql."""

    count: int | None | UnsetType = UNSET  # Int!
    studios: list[Studio] | None | UnsetType = UNSET  # [Studio!]!
