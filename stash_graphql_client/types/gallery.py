"""Gallery types from schema/types/gallery.graphql and gallery-chapter.graphql."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, ClassVar

from pydantic import BaseModel, Field

from .base import RelationshipMetadata, StashInput, StashObject, StashResult
from .enums import BulkUpdateIdMode
from .files import Folder, GalleryFile
from .image import Image
from .unset import UNSET, UnsetType


if TYPE_CHECKING:
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


class Gallery(StashObject):
    """Gallery type from schema/types/gallery.graphql."""

    __type_name__ = "Gallery"
    __update_input_type__ = GalleryUpdateInput
    __create_input_type__ = GalleryCreateInput

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
    image_count: int | UnsetType = Field(default=UNSET, ge=0)
    tags: list[Tag] | UnsetType = UNSET
    performers: list[Performer] | UnsetType = UNSET
    paths: GalleryPathsType | UnsetType = UNSET

    async def image(self, index: int) -> Image:
        """Get image at index."""
        # TODO: Implement this resolver
        raise NotImplementedError("image resolver not implemented")

    # Note: from_content method removed - Post/Message types not available in this project
    # @classmethod
    # async def from_content(cls, content, performer=None, studio=None) -> "Gallery":
    #     """Create gallery from post or message."""
    #     # Implementation depends on Post/Message types from metadata module
    #     pass

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
            inverse_query_field="galleries",
            query_strategy="direct_field",
            notes="Backend auto-syncs gallery.performers and performer.galleries",
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
    }


class BulkUpdateStrings(StashInput):
    """Input for bulk string updates."""

    values: list[str]  # [String!]!
    mode: BulkUpdateIdMode  # BulkUpdateIdMode!


class BulkUpdateIds(StashInput):
    """Input for bulk ID updates."""

    ids: list[str]  # [ID!]!
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


class GalleryDestroyInput(StashInput):
    """Input for destroying galleries.

    If delete_file is true, then the zip file will be deleted if the gallery is zip-file-based.
    If gallery is folder-based, then any files not associated with other galleries will be
    deleted, along with the folder, if it is not empty."""

    ids: list[str]  # [ID!]!
    delete_file: bool | None | UnsetType = UNSET  # Boolean
    delete_generated: bool | None | UnsetType = UNSET  # Boolean


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


class FindGalleriesResultType(StashResult):
    """Result type for finding galleries."""

    count: int  # Int!
    galleries: list[Gallery]  # [Gallery!]!
