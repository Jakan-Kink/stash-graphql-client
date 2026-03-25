"""Gallery types from schema/types/gallery.graphql and gallery-chapter.graphql."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, ClassVar

from pydantic import BaseModel, Field

from .base import (
    BulkUpdateIds,
    RelationshipMetadata,
    StashInput,
    StashObject,
    StashResult,
)
from .enums import BulkUpdateIdMode
from .files import Folder, GalleryFile
from .image import Image
from .metadata import CustomFieldsInput
from .scalars import Map
from .unset import UNSET, UnsetType, is_set


if TYPE_CHECKING:
    from stash_graphql_client.client import StashClient

    from .performer import Performer
    from .scene import Scene
    from .studio import Studio
    from .tag import Tag


class GalleryPathsType(BaseModel):
    """Gallery paths type from schema/types/gallery.graphql."""

    cover: str = ""  # String!
    preview: str = ""  # String! # Resolver

    @classmethod
    def create_default(cls) -> GalleryPathsType:
        """Create a default instance with empty strings."""
        return cls()


class GalleryChapterCreateInput(StashInput):
    """Input for creating gallery chapters."""

    gallery_id: str  # ID!
    title: str  # String!
    image_index: int  # Int!


class GalleryChapterUpdateInput(StashInput):
    """Input for updating gallery chapters."""

    id: str  # ID!
    gallery_id: str | None | UnsetType = UNSET  # ID
    title: str | None | UnsetType = UNSET  # String
    image_index: int | None | UnsetType = UNSET  # Int


class GalleryChapter(StashObject):
    """Gallery chapter type from schema/types/gallery-chapter.graphql.

    Note: Inherits from StashObject since it has id, created_at, and updated_at
    fields in the schema, matching the common pattern."""

    __type_name__ = "GalleryChapter"
    __short_repr_fields__ = ("title",)
    __update_input_type__ = GalleryChapterUpdateInput
    __create_input_type__ = GalleryChapterCreateInput

    # Fields to track for changes
    __tracked_fields__: ClassVar[set[str]] = {
        "gallery",
        "title",
        "image_index",
    }

    # Required fields
    gallery: Gallery | UnsetType = UNSET  # Gallery!
    title: str | UnsetType = UNSET  # String!
    image_index: int | UnsetType = UNSET  # Int!

    # Field definitions with their conversion functions
    __field_conversions__: ClassVar[dict] = {
        "title": str,
        "image_index": int,
    }

    __relationships__: ClassVar[dict] = {
        "gallery": RelationshipMetadata(
            target_field="gallery_id",
            is_list=False,
            query_field="gallery",
            inverse_type="Gallery",
            inverse_query_field="chapters",
            query_strategy="direct_field",
            notes="Backend auto-syncs gallery_chapter.gallery and gallery.chapters",
        ),
    }


class FindGalleryChaptersResultType(StashResult):
    """Result type for finding gallery chapters."""

    count: int  # Int!
    chapters: list[GalleryChapter]  # [GalleryChapter!]!


class GalleryCreateInput(StashInput):
    """Input for creating galleries."""

    # Required fields
    title: str  # String!

    # Optional fields
    code: str | None | UnsetType = UNSET  # String
    urls: list[str] | None | UnsetType = UNSET  # [String!]
    date: str | None | UnsetType = UNSET  # String
    details: str | None | UnsetType = UNSET  # String
    photographer: str | None | UnsetType = UNSET  # String
    rating100: int | None | UnsetType = Field(default=UNSET, ge=0, le=100)  # Int
    organized: bool | None | UnsetType = UNSET  # Boolean
    scene_ids: list[str] | None | UnsetType = UNSET  # [ID!]
    studio_id: str | None | UnsetType = UNSET  # ID
    tag_ids: list[str] | None | UnsetType = UNSET  # [ID!]
    performer_ids: list[str] | None | UnsetType = UNSET  # [ID!]
    custom_fields: dict[str, Any] | None | UnsetType = UNSET  # Map (appSchema >= 81)


class GalleryUpdateInput(StashInput):
    """Input for updating galleries."""

    # Required fields
    id: str  # ID!

    # Optional fields
    client_mutation_id: str | None | UnsetType = Field(
        default=UNSET, alias="clientMutationId"
    )  # String
    title: str | None | UnsetType = UNSET  # String
    code: str | None | UnsetType = UNSET  # String
    urls: list[str] | None | UnsetType = UNSET  # [String!]
    date: str | None | UnsetType = UNSET  # String
    details: str | None | UnsetType = UNSET  # String
    photographer: str | None | UnsetType = UNSET  # String
    rating100: int | None | UnsetType = Field(default=UNSET, ge=0, le=100)  # Int
    organized: bool | None | UnsetType = UNSET  # Boolean
    scene_ids: list[str] | None | UnsetType = UNSET  # [ID!]
    studio_id: str | None | UnsetType = UNSET  # ID
    tag_ids: list[str] | None | UnsetType = UNSET  # [ID!]
    performer_ids: list[str] | None | UnsetType = UNSET  # [ID!]
    primary_file_id: str | None | UnsetType = UNSET  # ID
    custom_fields: CustomFieldsInput | None | UnsetType = (
        UNSET  # CustomFieldsInput (appSchema >= 81)
    )


class GalleryDestroyInput(StashInput):
    """Input for destroying galleries.

    If delete_file is true, then the zip file will be deleted if the gallery is zip-file-based.
    If gallery is folder-based, then any files not associated with other galleries will be
    deleted, along with the folder, if it is not empty."""

    ids: list[str]  # [ID!]!
    delete_file: bool | None | UnsetType = UNSET  # Boolean
    delete_generated: bool | None | UnsetType = UNSET  # Boolean
    destroy_file_entry: bool | None | UnsetType = UNSET  # Boolean (appSchema >= 84)


class Gallery(StashObject):
    """Gallery type from schema/types/gallery.graphql."""

    __type_name__ = "Gallery"
    __short_repr_fields__ = ("title",)
    __update_input_type__ = GalleryUpdateInput
    __create_input_type__ = GalleryCreateInput
    __destroy_input_type__ = GalleryDestroyInput

    # Fields to track for changes
    __tracked_fields__: ClassVar[set[str]] = {
        "title",
        "code",
        "date",
        "details",
        "photographer",
        "rating100",
        "urls",
        "organized",
        "files",
        "chapters",
        "scenes",
        "tags",
        "performers",
        "studio",
        "cover",
        "images",
    }

    # Side mutations: fields persisted via separate GraphQL mutations
    # Lambdas are intentional: forward references to methods defined below
    __side_mutations__: ClassVar[dict] = {
        "cover": lambda client, obj: Gallery._save_cover(client, obj),  # noqa: PLW0108
        "images": lambda client, obj: Gallery._save_images(client, obj),  # noqa: PLW0108
    }

    # Optional fields
    title: str | None | UnsetType = UNSET
    code: str | None | UnsetType = UNSET
    date: str | None | UnsetType = UNSET
    details: str | None | UnsetType = UNSET
    photographer: str | None | UnsetType = UNSET
    rating100: int | None | UnsetType = Field(default=UNSET, ge=0, le=100)
    folder: Folder | None | UnsetType = UNSET
    studio: Studio | None | UnsetType = UNSET  # Forward reference
    cover: Image | None | UnsetType = UNSET

    # Required fields
    urls: list[str] | UnsetType = UNSET
    organized: bool | UnsetType = UNSET
    files: list[GalleryFile] | UnsetType = UNSET
    chapters: list[GalleryChapter] | UnsetType = UNSET
    scenes: list[Scene] | UnsetType = UNSET
    images: list[Image] | UnsetType = UNSET  # Reverse of Image.galleries
    image_count: int | UnsetType = Field(default=UNSET, ge=0)
    tags: list[Tag] | UnsetType = UNSET
    performers: list[Performer] | UnsetType = UNSET
    paths: GalleryPathsType | UnsetType = UNSET

    # Capability-gated fields (appSchema >= 81)
    custom_fields: Map | UnsetType = UNSET  # Map! (appSchema >= 81)

    async def image(self, index: int) -> Image:
        """Get image at index from this gallery.

        Uses the GraphQL `gallery.image(index)` resolver to fetch a specific image
        by its position in the gallery.

        Args:
            index: Zero-based index of the image in the gallery

        Returns:
            Image object at the specified index

        Raises:
            ValueError: If gallery ID is not set or index is out of bounds
            RuntimeError: If no StashEntityStore is configured

        Examples:
            ```python
            gallery = await client.find_gallery("123")

            # Get first image
            first_image = await gallery.image(0)

            # Get last image (if you know the count)
            if is_set(gallery.image_count):
                last_image = await gallery.image(gallery.image_count - 1)
            ```
        """
        from stash_graphql_client.fragments import fragment_store
        from stash_graphql_client.types.unset import is_set

        # Validate gallery has ID
        if not is_set(self.id) or self.id is None:
            raise ValueError("Cannot get image: gallery ID is not set")

        # Validate store is configured
        if self._store is None:
            raise RuntimeError(
                "Cannot get image: no StashEntityStore configured. "
                "Use StashContext to properly initialize the entity store."
            )

        # Query the gallery.image(index) resolver via store's client
        query = f"""
        {fragment_store.IMAGE_QUERY_FRAGMENTS}
        query GalleryImage($galleryId: ID!, $index: Int!) {{
            findGallery(id: $galleryId) {{
                image(index: $index) {{
                    ...ImageFragment
                }}
            }}
        }}
        """

        try:
            result = await self._store._client.execute(
                query, {"galleryId": self.id, "index": index}
            )
        except Exception as e:
            raise ValueError(
                f"Failed to fetch image at index {index} from gallery {self.id}: {e}"
            ) from e

        # Extract image data
        gallery_data = result.get("findGallery")
        if not gallery_data:
            raise ValueError(f"Gallery {self.id} not found")

        image_data = gallery_data.get("image")
        if not image_data:
            raise ValueError(
                f"No image found at index {index} in gallery {self.id}. "
                f"Gallery has {self.image_count if is_set(self.image_count) else 'unknown'} images."
            )

        # Use from_graphql() - the canonical method for GraphQL responses
        # This ensures proper _received_fields tracking and identity map integration
        return Image.from_graphql(image_data)

    @staticmethod
    async def _save_cover(client: StashClient, gallery: Gallery) -> None:
        """Side-mutation handler for the cover field.

        Called by save() after the main mutation. Sets or resets the gallery
        cover image via the dedicated client mixin methods.
        """
        cover = gallery.cover
        if is_set(cover) and cover is not None:
            await client.set_gallery_cover(gallery.id, cover.id)
        else:
            await client.reset_gallery_cover(gallery.id)

    @staticmethod
    async def _save_images(client: StashClient, gallery: Gallery) -> None:
        """Side-mutation handler for the images field.

        Called by save() after the main mutation. Computes the diff between
        current and snapshot images and fires addGalleryImages /
        removeGalleryImages bulk mutations accordingly.
        """
        current = gallery.images if is_set(gallery.images) else []
        snapshot = gallery._snapshot.get("images", [])
        current_ids = {img.id for img in current} if current else set()
        snapshot_ids = {img.id for img in snapshot} if snapshot else set()

        added = current_ids - snapshot_ids
        removed = snapshot_ids - current_ids

        if added:
            await client.add_gallery_images(gallery.id, list(added))
        if removed:
            await client.remove_gallery_images(gallery.id, list(removed))

    async def add_image(self, image: Image) -> None:
        """Add image (syncs Image.galleries inverse, call save() to persist)."""
        await self._add_to_relationship("images", image)

    async def remove_image(self, image: Image) -> None:
        """Remove image (syncs Image.galleries inverse, call save() to persist)."""
        await self._remove_from_relationship("images", image)

    async def add_performer(self, performer: Performer) -> None:
        """Add performer (syncs inverse automatically, call save() to persist)."""
        await self._add_to_relationship("performers", performer)

    async def remove_performer(self, performer: Performer) -> None:
        """Remove performer (syncs inverse automatically, call save() to persist)."""
        await self._remove_from_relationship("performers", performer)

    async def add_scene(self, scene: Scene) -> None:
        """Add scene (syncs inverse automatically, call save() to persist)."""
        await self._add_to_relationship("scenes", scene)

    async def remove_scene(self, scene: Scene) -> None:
        """Remove scene (syncs inverse automatically, call save() to persist)."""
        await self._remove_from_relationship("scenes", scene)

    async def add_tag(self, tag: Tag) -> None:
        """Add tag (syncs inverse automatically, call save() to persist)."""
        await self._add_to_relationship("tags", tag)

    async def remove_tag(self, tag: Tag) -> None:
        """Remove tag (syncs inverse automatically, call save() to persist)."""
        await self._remove_from_relationship("tags", tag)

    # Field definitions with their conversion functions
    __field_conversions__: ClassVar[dict] = {
        "title": str,
        "code": str,
        "urls": list,
        "details": str,
        "photographer": str,
        "rating100": int,
        "organized": bool,
        "date": lambda d: (
            d.strftime("%Y-%m-%d")
            if isinstance(d, datetime)
            else (
                datetime.fromisoformat(d).strftime("%Y-%m-%d")
                if isinstance(d, str)
                else None
            )
        ),
    }

    __relationships__: ClassVar[dict] = {
        # Pattern B: Filter query relationship (many-to-one)
        "studio": RelationshipMetadata(
            target_field="studio_id",
            is_list=False,
            query_field="studio",
            inverse_type="Studio",
            query_strategy="filter_query",
            filter_query_hint="findGalleries(gallery_filter={studios: {value: [studio_id]}})",
            notes="Studio has gallery_count and filter queries, not direct galleries field",
        ),
        # Pattern A: Direct field relationships (many-to-many)
        "performers": RelationshipMetadata(
            target_field="performer_ids",
            is_list=True,
            query_field="performers",
            inverse_type="Performer",
            query_strategy="direct_field",
            notes="Performer has gallery_count resolver, not direct galleries list",
        ),
        "tags": RelationshipMetadata(
            target_field="tag_ids",
            is_list=True,
            query_field="tags",
            inverse_type="Tag",
            query_strategy="direct_field",
            notes="Tag has gallery_count resolver, not direct galleries list",
        ),
        "scenes": RelationshipMetadata(
            target_field="scene_ids",
            is_list=True,
            query_field="scenes",
            inverse_type="Scene",
            inverse_query_field="galleries",
            query_strategy="direct_field",
            notes="Backend auto-syncs gallery.scenes and scene.galleries",
        ),
        # Side-mutation relationship: managed via addGalleryImages/removeGalleryImages
        # Not in GalleryUpdateInput — excluded from to_input() by __side_mutations__
        "images": RelationshipMetadata(
            target_field="image_ids",
            is_list=True,
            query_field="images",
            inverse_type="Image",
            inverse_query_field="galleries",
            query_strategy="filter_query",
            filter_query_hint="findImages(image_filter={galleries: {value: [gallery_id]}})",
            notes="Gallery has image(index) resolver, not images list. "
            "Managed via addGalleryImages/removeGalleryImages side mutations.",
        ),
    }


class BulkUpdateStrings(StashInput):
    """Input for bulk string updates."""

    values: list[str]  # [String!]!
    mode: BulkUpdateIdMode  # BulkUpdateIdMode!


class GalleryAddInput(StashInput):
    """Input for adding images to gallery."""

    gallery_id: str  # ID!
    image_ids: list[str]  # [ID!]!


class GalleryRemoveInput(StashInput):
    """Input for removing images from gallery."""

    gallery_id: str  # ID!
    image_ids: list[str]  # [ID!]!


class GallerySetCoverInput(StashInput):
    """Input for setting gallery cover."""

    gallery_id: str  # ID!
    cover_image_id: str  # ID!


class GalleryResetCoverInput(StashInput):
    """Input for resetting gallery cover."""

    gallery_id: str  # ID!


class BulkGalleryUpdateInput(StashInput):
    """Input for bulk updating galleries."""

    # Required fields
    ids: list[str]  # [ID!]!

    # Optional fields
    client_mutation_id: str | None | UnsetType = Field(
        default=UNSET, alias="clientMutationId"
    )  # String
    code: str | None | UnsetType = UNSET  # String
    urls: BulkUpdateStrings | None | UnsetType = UNSET  # BulkUpdateStrings
    date: str | None | UnsetType = UNSET  # String
    details: str | None | UnsetType = UNSET  # String
    photographer: str | None | UnsetType = UNSET  # String
    rating100: int | None | UnsetType = Field(
        default=UNSET, ge=0, le=100
    )  # Int (1-100)
    organized: bool | None | UnsetType = UNSET  # Boolean
    scene_ids: BulkUpdateIds | None | UnsetType = UNSET  # BulkUpdateIds
    studio_id: str | None | UnsetType = UNSET  # ID
    tag_ids: BulkUpdateIds | None | UnsetType = UNSET  # BulkUpdateIds
    performer_ids: BulkUpdateIds | None | UnsetType = UNSET  # BulkUpdateIds
    custom_fields: CustomFieldsInput | None | UnsetType = (
        UNSET  # CustomFieldsInput (appSchema >= 81)
    )


class FindGalleriesResultType(StashResult):
    """Result type for finding galleries."""

    count: int  # Int!
    galleries: list[Gallery]  # [Gallery!]!
