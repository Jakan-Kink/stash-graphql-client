"""Gallery types from schema/types/gallery.graphql and gallery-chapter.graphql."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, ClassVar

from pydantic import BaseModel, Field

from .base import StashObject
from .enums import BulkUpdateIdMode
from .files import Folder, GalleryFile
from .image import Image


if TYPE_CHECKING:
    from .performer import Performer
    from .scene import Scene
    from .studio import Studio
    from .tag import Tag


class BulkGalleryUpdateInput(BaseModel):
    """Input for bulk updating galleries."""

    # Optional fields
    client_mutation_id: str | None = None  # String
    ids: list[str]  # [ID!]!
    code: str | None = None  # String
    url: str | None = None  # String @deprecated
    urls: BulkUpdateStrings | None = None  # BulkUpdateStrings
    date: str | None = None  # String
    details: str | None = None  # String
    photographer: str | None = None  # String
    rating100: int | None = None  # Int (1-100)
    organized: bool | None = None  # Boolean
    scene_ids: BulkUpdateIds | None = None  # BulkUpdateIds
    studio_id: str | None = None  # ID
    tag_ids: BulkUpdateIds | None = None  # BulkUpdateIds
    performer_ids: BulkUpdateIds | None = None  # BulkUpdateIds


class BulkUpdateIds(BaseModel):
    """Input for bulk ID updates."""

    ids: list[str]  # [ID!]!
    mode: BulkUpdateIdMode  # BulkUpdateIdMode!


class BulkUpdateStrings(BaseModel):
    """Input for bulk string updates."""

    values: list[str]  # [String!]!
    mode: BulkUpdateIdMode  # BulkUpdateIdMode!


class FindGalleriesResultType(BaseModel):
    """Result type for finding galleries."""

    count: int  # Int!
    galleries: list[Gallery]  # [Gallery!]!


class FindGalleryChaptersResultType(BaseModel):
    """Result type for finding gallery chapters."""

    count: int  # Int!
    chapters: list[GalleryChapter]  # [GalleryChapter!]!


class GalleryCreateInput(BaseModel):
    """Input for creating galleries."""

    # Required fields
    title: str  # String!

    # Optional fields
    code: str | None = None  # String
    url: str | None = None  # String @deprecated
    urls: list[str] | None = None  # [String!]
    date: str | None = None  # String
    details: str | None = None  # String
    photographer: str | None = None  # String
    rating100: int | None = None  # Int
    organized: bool | None = None  # Boolean
    scene_ids: list[str] | None = None  # [ID!]
    studio_id: str | None = None  # ID
    tag_ids: list[str] | None = None  # [ID!]
    performer_ids: list[str] | None = None  # [ID!]


class GalleryUpdateInput(BaseModel):
    """Input for updating galleries."""

    # Required fields
    id: str  # ID!

    # Optional fields
    client_mutation_id: str | None = None  # String
    title: str | None = None  # String
    code: str | None = None  # String
    url: str | None = None  # String @deprecated
    urls: list[str] | None = None  # [String!]
    date: str | None = None  # String
    details: str | None = None  # String
    photographer: str | None = None  # String
    rating100: int | None = None  # Int
    organized: bool | None = None  # Boolean
    scene_ids: list[str] | None = None  # [ID!]
    studio_id: str | None = None  # ID
    tag_ids: list[str] | None = None  # [ID!]
    performer_ids: list[str] | None = None  # [ID!]
    primary_file_id: str | None = None  # ID


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
        "url",  # Deprecated but still needed
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
    title: str | None = None
    code: str | None = None
    date: str | None = None
    details: str | None = None
    photographer: str | None = None
    rating100: int | None = None
    folder: Folder | None = None
    studio: Studio | None = None  # Forward reference
    cover: Image | None = None
    url: str | None = None  # Deprecated, but needed for compatibility

    # Required fields
    urls: list[str] = Field(default_factory=list)
    organized: bool = False
    files: list[GalleryFile] = Field(default_factory=list)
    chapters: list[GalleryChapter] = Field(default_factory=list)
    scenes: list[Scene] = Field(default_factory=list)
    # Note: image_count is a resolver field - use GalleryDetail for lazy-loaded counts
    tags: list[Tag] = Field(default_factory=list)
    performers: list[Performer] = Field(default_factory=list)
    # Note: paths field removed - use GalleryDetail for lazy-loaded path URLs

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
        "url": str,  # Deprecated but still needed
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
        # Standard ID relationships
        "studio": ("studio_id", False, None),  # (target_field, is_list, transform)
        "performers": ("performer_ids", True, None),
        "tags": ("tag_ids", True, None),
        "scenes": ("scene_ids", True, None),
    }


class GalleryAddInput(BaseModel):
    """Input for adding images to gallery."""

    gallery_id: str  # ID!
    image_ids: list[str]  # [ID!]!


class GalleryChapterCreateInput(BaseModel):
    """Input for creating gallery chapters."""

    gallery_id: str  # ID!
    title: str  # String!
    image_index: int  # Int!


class GalleryChapterUpdateInput(BaseModel):
    """Input for updating gallery chapters."""

    id: str  # ID!
    gallery_id: str | None = None  # ID
    title: str | None = None  # String
    image_index: int | None = None  # Int


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
    gallery: Gallery  # Gallery!
    title: str  # String!
    image_index: int  # Int!

    # Field definitions with their conversion functions
    __field_conversions__: ClassVar[dict] = {
        "title": str,
        "image_index": int,
    }

    __relationships__: ClassVar[dict] = {
        # Standard ID relationships
        "gallery": ("gallery_id", False, None),  # (target_field, is_list, transform)
    }


class GalleryDestroyInput(BaseModel):
    """Input for destroying galleries.

    If delete_file is true, then the zip file will be deleted if the gallery is zip-file-based.
    If gallery is folder-based, then any files not associated with other galleries will be
    deleted, along with the folder, if it is not empty."""

    ids: list[str]  # [ID!]!
    delete_file: bool | None = None  # Boolean
    delete_generated: bool | None = None  # Boolean


class GalleryPathsType(BaseModel):
    """Gallery paths type from schema/types/gallery.graphql."""

    cover: str = ""  # String!
    preview: str = ""  # String! # Resolver

    @classmethod
    def create_default(cls) -> GalleryPathsType:
        """Create a default instance with empty strings."""
        return cls()


class GalleryRemoveInput(BaseModel):
    """Input for removing images from gallery."""

    gallery_id: str  # ID!
    image_ids: list[str]  # [ID!]!


class GalleryResetCoverInput(BaseModel):
    """Input for resetting gallery cover."""

    gallery_id: str  # ID!


class GallerySetCoverInput(BaseModel):
    """Input for setting gallery cover."""

    gallery_id: str  # ID!
    cover_image_id: str  # ID!
