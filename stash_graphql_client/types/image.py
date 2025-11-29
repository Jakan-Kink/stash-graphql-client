"""Image types from schema/types/image.graphql."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field, model_validator

from .base import BulkUpdateIds, BulkUpdateStrings, StashObject


if TYPE_CHECKING:
    from .gallery import Gallery
    from .performer import Performer
    from .studio import Studio
    from .tag import Tag


class ImageFileType(BaseModel):
    """Image file type from schema/types/image.graphql."""

    mod_time: datetime  # Time!
    size: int  # Int!
    width: int  # Int!
    height: int  # Int!


class ImagePathsType(BaseModel):
    """Image paths type from schema/types/image.graphql."""

    thumbnail: str | None = None  # String (Resolver)
    preview: str | None = None  # String (Resolver)
    image: str | None = None  # String (Resolver)


class ImageUpdateInput(BaseModel):
    """Input for updating images."""

    # Required fields
    id: str  # ID!

    # Optional fields
    client_mutation_id: str | None = None  # String
    title: str | None = None  # String
    code: str | None = None  # String
    rating100: int | None = None  # Int (1-100)
    organized: bool | None = None  # Boolean
    url: str | None = None  # String @deprecated
    urls: list[str] | None = None  # [String!]
    date: str | None = None  # String
    details: str | None = None  # String
    photographer: str | None = None  # String
    studio_id: str | None = None  # ID
    performer_ids: list[str] | None = None  # [ID!]
    tag_ids: list[str] | None = None  # [ID!]
    gallery_ids: list[str] | None = None  # [ID!]
    primary_file_id: str | None = None  # ID


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
    title: str | None = None  # String
    code: str | None = None  # String
    date: str | None = None  # String
    details: str | None = None  # String
    photographer: str | None = None  # String
    studio: Studio | None = None  # Studio

    # Required fields
    urls: list[str] = Field(default_factory=list)  # [String!]!
    organized: bool = False  # Boolean!
    visual_files: list[Any] = Field(
        default_factory=list
    )  # [VisualFile!]! - The image files (replaces deprecated 'files' field)
    paths: ImagePathsType = Field(
        default_factory=ImagePathsType
    )  # ImagePathsType! (Resolver)
    galleries: list[Gallery] = Field(default_factory=list)  # [Gallery!]!
    tags: list[Tag] = Field(default_factory=list)  # [Tag!]!
    performers: list[Performer] = Field(default_factory=list)  # [Performer!]!

    # Relationship definitions with their mappings
    __relationships__ = {
        "studio": ("studio_id", False, None),  # (target_field, is_list, transform)
        "performers": ("performer_ids", True, None),
        "tags": ("tag_ids", True, None),
        "galleries": ("gallery_ids", True, None),
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

    @model_validator(mode="before")
    @classmethod
    def convert_files_to_visual_files(cls, data: Any) -> Any:
        """Convert deprecated 'files' field to 'visual_files'.

        The GraphQL schema uses 'files' but we use 'visual_files' internally.
        This validator handles the conversion when data comes from the API.

        Args:
            data: Input data (dict or object)

        Returns:
            Modified data with files converted to visual_files
        """
        # Handle dict input
        if isinstance(data, dict) and "files" in data:
            from .files import ImageFile, VideoFile

            files = data.pop("files")
            visual_files: list[Any] = []

            for file_data in files if isinstance(files, list) else [files]:
                # Determine if it's an ImageFile or VideoFile based on presence of duration
                if isinstance(file_data, dict):
                    if "duration" in file_data:
                        visual_files.append(VideoFile(**file_data))
                    else:
                        visual_files.append(ImageFile(**file_data))
                else:
                    # Already a VisualFile object
                    visual_files.append(file_data)

            # Set visual_files if not already set
            if "visual_files" not in data:
                data["visual_files"] = visual_files

        return data


class ImageDestroyInput(BaseModel):
    """Input for destroying images from schema/types/image.graphql."""

    id: str  # ID!
    delete_file: bool | None = None  # Boolean
    delete_generated: bool | None = None  # Boolean


class ImagesDestroyInput(BaseModel):
    """Input for destroying multiple images from schema/types/image.graphql."""

    ids: list[str]  # [ID!]!
    delete_file: bool | None = None  # Boolean
    delete_generated: bool | None = None  # Boolean


class BulkImageUpdateInput(BaseModel):
    """Input for bulk updating images."""

    # Optional fields
    client_mutation_id: str | None = None  # String
    ids: list[str]  # [ID!]
    rating100: int | None = None  # Int (1-100)
    organized: bool | None = None  # Boolean
    url: str | None = None  # String @deprecated
    urls: BulkUpdateStrings | None = None  # BulkUpdateStrings
    date: str | None = None  # String
    details: str | None = None  # String
    photographer: str | None = None  # String
    studio_id: str | None = None  # ID
    performer_ids: BulkUpdateIds | None = None  # BulkUpdateIds
    tag_ids: BulkUpdateIds | None = None  # BulkUpdateIds
    gallery_ids: BulkUpdateIds | None = None  # BulkUpdateIds


class FindImagesResultType(BaseModel):
    """Result type for finding images from schema/types/image.graphql."""

    count: int  # Int!
    megapixels: float  # Float! (Total megapixels of the images)
    filesize: float  # Float! (Total file size in bytes)
    images: list[Image] = Field(default_factory=list)  # [Image!]!
