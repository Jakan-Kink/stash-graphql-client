"""File types from schema/types/file.graphql."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from .base import StashInput, StashObject, StashResult
from .scalars import Time
from .unset import UNSET, UnsetType


def fingerprint_resolver(parent: BaseFile, type: str) -> str:
    """Resolver for fingerprint field.

    Args:
        parent: The BaseFile instance (automatically passed by strawberry)
        type: The fingerprint type to look for

    Returns:
        The fingerprint value for the given type, or empty string if not found.
        This matches the GraphQL schema which defines the return type as String! (non-nullable).
    """
    # Handle UNSET case
    if isinstance(parent.fingerprints, UnsetType):
        return ""

    for fp in parent.fingerprints:
        if fp.type_ == type:
            return fp.value
    return ""  # Return empty string instead of None to match GraphQL schema


class SetFingerprintsInput(StashInput):
    """Input for setting fingerprints."""

    type_: str = Field(alias="type")  # String! - aliased to avoid built-in conflict
    value: str | None | UnsetType = UNSET  # String


class FileSetFingerprintsInput(StashInput):
    """Input for setting file fingerprints."""

    id: str  # ID!
    fingerprints: list[SetFingerprintsInput]  # [SetFingerprintsInput!]!


class MoveFilesInput(StashInput):
    """Input for moving files."""

    ids: list[str]  # [ID!]!
    destination_folder: str | None | UnsetType = UNSET  # String
    destination_folder_id: str | None | UnsetType = UNSET  # ID
    destination_basename: str | None | UnsetType = UNSET  # String


class Fingerprint(BaseModel):
    """Fingerprint type from schema/types/file.graphql."""

    type_: str = Field(alias="type")  # String! - aliased to avoid built-in conflict
    value: str  # String!


class BaseFile(StashObject):
    """Base interface for all file types from schema/types/file.graphql.

    Note: Inherits from StashObject since it has id, created_at, and updated_at
    fields in the schema, matching the common pattern."""

    __type_name__ = "BaseFile"

    # Required fields
    path: str | UnsetType = UNSET  # String!
    basename: str | UnsetType = UNSET  # String!
    parent_folder: Folder | UnsetType = UNSET  # Folder!
    mod_time: datetime | UnsetType = UNSET  # Time!
    size: int | UnsetType = UNSET  # Int64!
    fingerprints: list[Fingerprint] | UnsetType = UNSET  # [Fingerprint!]!

    # Optional fields
    zip_file: BasicFile | None | UnsetType = UNSET  # BasicFile

    # Note: fingerprint field with resolver is not directly supported in Pydantic
    # Users should call fingerprint_resolver(instance, type) directly

    async def to_input(self) -> dict[str, Any]:
        """Convert to GraphQL input.

        Returns:
            Dictionary of input fields for move or set fingerprints operations.
        """
        # Files don't have create/update operations, only move and set fingerprints
        # For move operation - return dict with proper field names
        return {
            "ids": [self.id],
            "destination_folder": None,  # Must be set by caller
            "destination_folder_id": None,  # Must be set by caller
            "destination_basename": self.basename,
        }


class BasicFile(BaseFile):
    """BasicFile type from schema/types/file.graphql.

    Implements BaseFile with no additional fields beyond the base interface."""

    __type_name__ = "BasicFile"


class ImageFile(BaseFile):
    """Image file type from schema/types/file.graphql.

    Implements BaseFile and inherits StashObject through it."""

    __type_name__ = "ImageFile"

    # Required fields
    format: str | UnsetType = UNSET  # String!
    width: int | UnsetType = UNSET  # Int!
    height: int | UnsetType = UNSET  # Int!


class VideoFile(BaseFile):
    """Video file type from schema/types/file.graphql.

    Implements BaseFile and inherits StashObject through it."""

    __type_name__ = "VideoFile"

    # Required fields
    format: str | UnsetType = UNSET  # String!
    width: int | UnsetType = UNSET  # Int!
    height: int | UnsetType = UNSET  # Int!
    duration: float | UnsetType = UNSET  # Float!
    video_codec: str | UnsetType = UNSET  # String!
    audio_codec: str | UnsetType = UNSET  # String!
    frame_rate: float | UnsetType = UNSET  # Float!  # frame_rate in schema
    bit_rate: int | UnsetType = UNSET  # Int!  # bit_rate in schema


# Union type for VisualFile (VideoFile or ImageFile)
VisualFile = VideoFile | ImageFile


class GalleryFile(BaseFile):
    """Gallery file type from schema/types/file.graphql.

    Implements BaseFile with no additional fields and inherits StashObject through it.
    """

    __type_name__ = "GalleryFile"


class ScenePathsType(BaseModel):
    """Scene paths type from schema/types/scene.graphql."""

    screenshot: str | None | UnsetType = UNSET  # String (Resolver)
    preview: str | None | UnsetType = UNSET  # String (Resolver)
    stream: str | None | UnsetType = UNSET  # String (Resolver)
    webp: str | None | UnsetType = UNSET  # String (Resolver)
    vtt: str | None | UnsetType = UNSET  # String (Resolver)
    sprite: str | None | UnsetType = UNSET  # String (Resolver)
    funscript: str | None | UnsetType = UNSET  # String (Resolver)
    interactive_heatmap: str | None | UnsetType = UNSET  # String (Resolver)
    caption: str | None | UnsetType = UNSET  # String (Resolver)


class StashIDInput(StashInput):
    """Input for StashID from schema/types/stash-box.graphql."""

    endpoint: str  # String!
    stash_id: str  # String!
    updated_at: Time | None | UnsetType = UNSET  # Time


class StashID(BaseModel):
    """StashID type from schema/types/stash-box.graphql."""

    endpoint: str | None | UnsetType = UNSET  # String!
    stash_id: str | None | UnsetType = UNSET  # String!
    updated_at: Time | None | UnsetType = UNSET  # Time!


class VideoCaption(BaseModel):
    """Video caption type from schema/types/scene.graphql."""

    language_code: str  # String!
    caption_type: str  # String!


class Folder(StashObject):
    """Folder type from schema/types/file.graphql.

    Note: Inherits from StashObject since it has id, created_at, and updated_at
    fields in the schema, matching the common pattern."""

    __type_name__ = "Folder"

    # Required fields
    path: str | UnsetType = UNSET  # String!
    mod_time: datetime | UnsetType = UNSET  # Time!

    # Optional fields
    parent_folder: Folder | None | UnsetType = UNSET  # Folder
    zip_file: BasicFile | None | UnsetType = UNSET  # BasicFile

    async def to_input(self) -> dict[str, Any]:
        """Convert to GraphQL input.

        Returns:
            Dictionary of input fields for move operation.
        """
        # Folders don't have create/update operations, only move
        # For move operation - return dict with proper field names
        return {
            "ids": [self.id],
            "destination_folder": None,  # Must be set by caller
            "destination_folder_id": None,  # Must be set by caller
            "destination_basename": None,  # Not applicable for folders
        }


class AssignSceneFileInput(StashInput):
    """Input for assigning a file to a scene."""

    scene_id: str  # ID!
    file_id: str  # ID!


class SceneHashInput(StashInput):
    """Input for finding a scene by hash."""

    checksum: str | None | UnsetType = UNSET  # String
    oshash: str | None | UnsetType = UNSET  # String


class FindFilesResultType(StashResult):
    """Result type for finding files from schema/types/file.graphql."""

    count: int  # Int!
    megapixels: float  # Float!
    duration: float  # Float!
    size: int  # Int!
    files: list[BaseFile]  # [BaseFile!]!

    @field_validator("files", mode="before")
    @classmethod
    def _discriminate_file_types(cls, value: Any) -> Any:
        """Discriminate BaseFile interface types based on __typename.

        Converts raw dicts to the appropriate BaseFile subclass based on __typename field.
        """
        if not isinstance(value, list):
            return value

        # Type mapping for BaseFile interface
        type_map = {
            "VideoFile": VideoFile,
            "ImageFile": ImageFile,
            "GalleryFile": GalleryFile,
            "BasicFile": BasicFile,
        }

        result = []
        for item in value:
            if isinstance(item, dict) and "__typename" in item:
                typename = item["__typename"]
                file_type = type_map.get(typename, BaseFile)
                # Construct the correct type from the dict
                result.append(file_type.model_validate(item))
            else:
                # Already constructed or no typename
                result.append(item)

        return result


class FindFoldersResultType(StashResult):
    """Result type for finding folders from schema/types/file.graphql."""

    count: int  # Int!
    folders: list[Folder]  # [Folder!]!
