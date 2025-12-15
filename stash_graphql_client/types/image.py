"""Image types from schema/types/image.graphql."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field, field_validator

from .base import (
    BulkUpdateIds,
    BulkUpdateStrings,
    RelationshipMetadata,
    StashInput,
    StashObject,
    StashResult,
)
from .files import ImageFile, VideoFile
from .unset import UNSET, UnsetType


if TYPE_CHECKING:
    from .gallery import Gallery
    from .performer import Performer
    from .studio import Studio
    from .tag import Tag

# VisualFile union type (VideoFile | ImageFile)
VisualFile = VideoFile | ImageFile


class ImageFileType(BaseModel):
    """Image file type from schema/types/image.graphql."""

    mod_time: datetime | UnsetType = UNSET  # Time!
    size: int | UnsetType = UNSET  # Int!
    width: int | UnsetType = UNSET  # Int!
    height: int | UnsetType = UNSET  # Int!


class ImagePathsType(BaseModel):
    """Image paths type from schema/types/image.graphql."""

    thumbnail: str | None | UnsetType = UNSET  # String (Resolver)
    preview: str | None | UnsetType = UNSET  # String (Resolver)
    image: str | None | UnsetType = UNSET  # String (Resolver)


class ImageUpdateInput(StashInput):
    """Input for updating images."""

    # Required fields
    id: str  # ID!

    # Optional fields
    client_mutation_id: str | None | UnsetType = Field(
        default=UNSET, alias="clientMutationId"
    )  # String
    title: str | None | UnsetType = UNSET  # String
    code: str | None | UnsetType = UNSET  # String
    rating100: int | None | UnsetType = UNSET  # Int (1-100)
    organized: bool | None | UnsetType = UNSET  # Boolean
    urls: list[str] | None | UnsetType = UNSET  # [String!]
    date: str | None | UnsetType = UNSET  # String
    details: str | None | UnsetType = UNSET  # String
    photographer: str | None | UnsetType = UNSET  # String
    studio_id: str | None | UnsetType = UNSET  # ID
    performer_ids: list[str] | None | UnsetType = UNSET  # [ID!]
    tag_ids: list[str] | None | UnsetType = UNSET  # [ID!]
    gallery_ids: list[str] | None | UnsetType = UNSET  # [ID!]
    primary_file_id: str | None | UnsetType = UNSET  # ID


class Image(StashObject):
    """Image type from schema."""

    __type_name__ = "Image"
    __update_input_type__ = ImageUpdateInput
    # No __create_input_type__ - images can only be updated

    # Fields to track for changes - only fields that can be written via input types
    __tracked_fields__ = {
        "title",  # ImageUpdateInput
        "code",  # ImageUpdateInput
        "urls",  # ImageUpdateInput
        "date",  # ImageUpdateInput
        "details",  # ImageUpdateInput
        "photographer",  # ImageUpdateInput
        "studio",  # mapped to studio_id
        "organized",  # ImageUpdateInput
        "galleries",  # mapped to gallery_ids
        "tags",  # mapped to tag_ids
        "performers",  # mapped to performer_ids
    }

    # Optional fields
    title: str | None | UnsetType = UNSET  # String
    code: str | None | UnsetType = UNSET  # String
    date: str | None | UnsetType = UNSET  # String
    rating100: int | None | UnsetType = Field(
        default=UNSET, ge=0, le=100
    )  # Int (0-100)
    details: str | None | UnsetType = UNSET  # String
    photographer: str | None | UnsetType = UNSET  # String
    studio: Studio | None | UnsetType = UNSET  # Studio
    o_counter: int | None | UnsetType = Field(default=UNSET, ge=0)  # Int (Resolver)

    # Required fields
    urls: list[str] | UnsetType = Field(default=UNSET)  # [String!]!
    organized: bool | UnsetType = UNSET  # Boolean!
    visual_files: list[VisualFile] | UnsetType = Field(
        default=UNSET
    )  # [VisualFile!]! - The image files (union of VideoFile | ImageFile)
    paths: ImagePathsType | UnsetType = Field(
        default=UNSET
    )  # ImagePathsType! (Resolver)
    galleries: list[Gallery] | UnsetType = Field(default=UNSET)  # [Gallery!]!
    tags: list[Tag] | UnsetType = Field(default=UNSET)  # [Tag!]!
    performers: list[Performer] | UnsetType = Field(default=UNSET)  # [Performer!]!

    # Relationship definitions with their mappings
    __relationships__ = {
        # Pattern B: Filter query relationship (many-to-one)
        "studio": RelationshipMetadata(
            target_field="studio_id",
            is_list=False,
            query_field="studio",
            inverse_type="Studio",
            query_strategy="filter_query",
            filter_query_hint="findImages(image_filter={studios: {value: [studio_id]}})",
            notes="Studio has image_count and filter queries, not direct images field",
        ),
        # Pattern A: Direct field relationships (many-to-many)
        "performers": RelationshipMetadata(
            target_field="performer_ids",
            is_list=True,
            query_field="performers",
            inverse_type="Performer",
            inverse_query_field="images",
            query_strategy="direct_field",
            notes="Backend auto-syncs image.performers and performer.images",
        ),
        "tags": RelationshipMetadata(
            target_field="tag_ids",
            is_list=True,
            query_field="tags",
            inverse_type="Tag",
            query_strategy="direct_field",
            notes="Tag has image_count resolver, not direct images list",
        ),
        "galleries": RelationshipMetadata(
            target_field="gallery_ids",
            is_list=True,
            query_field="galleries",
            inverse_type="Gallery",
            inverse_query_field="images",
            query_strategy="direct_field",
            notes="Backend auto-syncs image.galleries and gallery.images",
        ),
    }

    # Field definitions with their conversion functions
    __field_conversions__ = {
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

    @field_validator("visual_files", mode="before")
    @classmethod
    def _discriminate_visual_file_types(cls, value: Any) -> Any:
        """Discriminate VisualFile union types based on __typename.

        Converts raw dicts to the appropriate VisualFile type (VideoFile or ImageFile)
        based on __typename field.
        """
        if value is None or isinstance(value, type(UNSET)):
            return value

        if not isinstance(value, list):
            return value

        # Type mapping for VisualFile union
        type_map = {
            "VideoFile": VideoFile,
            "ImageFile": ImageFile,
        }

        result = []
        for item in value:
            if isinstance(item, dict) and "__typename" in item:
                typename = item["__typename"]
                file_type = type_map.get(typename)
                if file_type:
                    # Construct the correct type from the dict
                    result.append(file_type.model_validate(item))
                else:
                    # Unknown typename, skip
                    continue
            else:
                # Already constructed or no typename
                result.append(item)

        return result


class ImageDestroyInput(StashInput):
    """Input for destroying images from schema/types/image.graphql."""

    id: str  # ID!
    delete_file: bool | None | UnsetType = UNSET  # Boolean
    delete_generated: bool | None | UnsetType = UNSET  # Boolean


class ImagesDestroyInput(StashInput):
    """Input for destroying multiple images from schema/types/image.graphql."""

    ids: list[str] | UnsetType = UNSET  # [ID!]!
    delete_file: bool | None | UnsetType = UNSET  # Boolean
    delete_generated: bool | None | UnsetType = UNSET  # Boolean


class BulkImageUpdateInput(StashInput):
    """Input for bulk updating images."""

    # Optional fields
    client_mutation_id: str | None | UnsetType = Field(
        default=UNSET, alias="clientMutationId"
    )  # String
    ids: list[str] | UnsetType = UNSET  # [ID!]
    title: str | None | UnsetType = UNSET  # String
    code: str | None | UnsetType = UNSET  # String
    rating100: int | None | UnsetType = Field(
        default=UNSET, ge=0, le=100
    )  # Int (0-100)
    organized: bool | None | UnsetType = UNSET  # Boolean
    urls: BulkUpdateStrings | None | UnsetType = UNSET  # BulkUpdateStrings
    date: str | None | UnsetType = UNSET  # String
    details: str | None | UnsetType = UNSET  # String
    photographer: str | None | UnsetType = UNSET  # String
    studio_id: str | None | UnsetType = UNSET  # ID
    performer_ids: BulkUpdateIds | None | UnsetType = UNSET  # BulkUpdateIds
    tag_ids: BulkUpdateIds | None | UnsetType = UNSET  # BulkUpdateIds
    gallery_ids: BulkUpdateIds | None | UnsetType = UNSET  # BulkUpdateIds


class FindImagesResultType(StashResult):
    """Result type for finding images from schema/types/image.graphql."""

    count: int | UnsetType = UNSET  # Int!
    megapixels: float | UnsetType = UNSET  # Float! (Total megapixels of the images)
    filesize: float | UnsetType = UNSET  # Float! (Total file size in bytes)
    images: list[Image] | UnsetType = Field(default=UNSET)  # [Image!]!
