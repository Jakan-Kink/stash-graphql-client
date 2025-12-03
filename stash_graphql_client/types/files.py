"""File types from schema/types/file.graphql."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator

from .base import StashObject


def fingerprint_resolver(parent: BaseFile, type: str) -> str:
    """Resolver for fingerprint field.

    Args:
        parent: The BaseFile instance (automatically passed by strawberry)
        type: The fingerprint type to look for

    Returns:
        The fingerprint value for the given type, or empty string if not found.
        This matches the GraphQL schema which defines the return type as String! (non-nullable).
    """
    for fp in parent.fingerprints:
        if fp.type_ == type:
            return fp.value
    return ""  # Return empty string instead of None to match GraphQL schema


class AssignSceneFileInput(BaseModel):
    """Input for assigning a file to a scene."""

    scene_id: str  # ID!
    file_id: str  # ID!


class BaseFile(StashObject):
    """Base interface for all file types from schema/types/file.graphql.

    Note: Inherits from StashObject since it has id, created_at, and updated_at
    fields in the schema, matching the common pattern."""

    __type_name__ = "BaseFile"

    # Required fields
    path: str  # String!
    basename: str  # String!
    parent_folder: Folder  # Folder! (replaces deprecated parent_folder_id)
    mod_time: datetime  # Time!
    size: int  # Int64!
    fingerprints: list[Fingerprint] = Field(default_factory=list)  # [Fingerprint!]!

    # Optional fields
    zip_file: BasicFile | None = None  # BasicFile (replaces deprecated zip_file_id)

    # Note: fingerprint field with resolver is not directly supported in Pydantic
    # Users should call fingerprint_resolver(instance, type) directly

    @model_validator(mode="before")
    @classmethod
    def handle_deprecated_id_fields(cls, data: Any) -> Any:
        """Convert deprecated ID fields to relationship objects for backward compatibility."""
        if isinstance(data, dict):
            # Handle deprecated parent_folder_id
            if "parent_folder_id" in data and "parent_folder" not in data:
                from datetime import datetime

                # Create a minimal Folder object from the ID with required fields
                data["parent_folder"] = {
                    "id": data["parent_folder_id"],
                    "path": "",  # Placeholder - will be populated by actual query
                    "mod_time": datetime.now(UTC),  # Placeholder
                }
                data.pop("parent_folder_id", None)

            # Handle deprecated zip_file_id
            if data.get("zip_file_id"):
                from datetime import datetime

                if "zip_file" not in data:
                    # Create a minimal BasicFile object from the ID with required fields
                    data["zip_file"] = {
                        "id": data["zip_file_id"],
                        "path": "",  # Placeholder
                        "basename": "",  # Placeholder
                        "parent_folder": {
                            "id": "",
                            "path": "",
                            "mod_time": datetime.now(UTC),
                        },
                        "mod_time": datetime.now(UTC),
                        "size": 0,
                        "fingerprints": [],
                    }
                data.pop("zip_file_id", None)
            elif "zip_file_id" in data:
                # zip_file_id exists but is None, just remove it
                data.pop("zip_file_id", None)

        return data

    async def to_input(self) -> dict[str, Any]:
        """Convert to GraphQL input.

        Returns:
            Dictionary of input fields for move or set fingerprints operations.
        """
        # Files don't have create/update operations, only move and set fingerprints
        if hasattr(self, "id"):
            # For move operation - return dict with proper field names
            return {
                "ids": [self.id],
                "destination_folder": None,  # Must be set by caller
                "destination_folder_id": None,  # Must be set by caller
                "destination_basename": self.basename,
            }
        raise ValueError("File must have an ID")


class BasicFile(BaseFile):
    """BasicFile type from schema/types/file.graphql.

    Implements BaseFile with no additional fields beyond the base interface."""

    __type_name__ = "BasicFile"


class FileSetFingerprintsInput(BaseModel):
    """Input for setting file fingerprints."""

    id: str  # ID!
    fingerprints: list[SetFingerprintsInput]  # [SetFingerprintsInput!]!


class FindFilesResultType(BaseModel):
    """Result type for finding files from schema/types/file.graphql."""

    count: int  # Int!
    megapixels: float  # Float!
    duration: float  # Float!
    size: int  # Int!
    files: list[BaseFile]  # [BaseFile!]!


class FindFoldersResultType(BaseModel):
    """Result type for finding folders from schema/types/file.graphql."""

    count: int  # Int!
    folders: list[Folder]  # [Folder!]!


class Fingerprint(BaseModel):
    """Fingerprint type from schema/types/file.graphql."""

    type_: str = Field(alias="type")  # String! - aliased to avoid built-in conflict
    value: str  # String!


class Folder(StashObject):
    """Folder type from schema/types/file.graphql.

    Note: Inherits from StashObject since it has id, created_at, and updated_at
    fields in the schema, matching the common pattern."""

    __type_name__ = "Folder"

    # Required fields
    path: str  # String!
    mod_time: datetime | None = None  # Time! - optional because Stash may not return it

    # Optional fields
    parent_folder: Folder | None = None  # Folder (replaces deprecated parent_folder_id)
    zip_file: BasicFile | None = None  # BasicFile (replaces deprecated zip_file_id)

    @model_validator(mode="before")
    @classmethod
    def handle_deprecated_id_fields(cls, data: Any) -> Any:
        """Convert deprecated ID fields to relationship objects for backward compatibility."""
        if isinstance(data, dict):
            # Handle deprecated parent_folder_id
            if data.get("parent_folder_id"):
                from datetime import datetime

                if "parent_folder" not in data:
                    # Create a minimal Folder object from the ID with required fields
                    data["parent_folder"] = {
                        "id": data["parent_folder_id"],
                        "path": "",  # Placeholder - will be populated by actual query
                        "mod_time": datetime.now(UTC),  # Placeholder
                    }
                data.pop("parent_folder_id", None)
            elif "parent_folder_id" in data:
                # parent_folder_id exists but is None, just remove it
                data.pop("parent_folder_id", None)

            # Handle deprecated zip_file_id
            if data.get("zip_file_id"):
                from datetime import datetime

                if "zip_file" not in data:
                    # Create a minimal BasicFile object from the ID with required fields
                    data["zip_file"] = {
                        "id": data["zip_file_id"],
                        "path": "",  # Placeholder
                        "basename": "",  # Placeholder
                        "parent_folder": {
                            "id": "",
                            "path": "",
                            "mod_time": datetime.now(UTC),
                        },
                        "mod_time": datetime.now(UTC),
                        "size": 0,
                        "fingerprints": [],
                    }
                data.pop("zip_file_id", None)
            elif "zip_file_id" in data:
                # zip_file_id exists but is None, just remove it
                data.pop("zip_file_id", None)

        return data

    async def to_input(self) -> dict[str, Any]:
        """Convert to GraphQL input.

        Returns:
            Dictionary of input fields for move operation.
        """
        # Folders don't have create/update operations, only move
        if hasattr(self, "id"):
            # For move operation - return dict with proper field names
            return {
                "ids": [self.id],
                "destination_folder": None,  # Must be set by caller
                "destination_folder_id": None,  # Must be set by caller
                "destination_basename": None,  # Not applicable for folders
            }
        raise ValueError("Folder must have an ID")


class GalleryFile(BaseFile):
    """Gallery file type from schema/types/file.graphql.

    Implements BaseFile with no additional fields and inherits StashObject through it.
    """

    __type_name__ = "GalleryFile"


class ImageFile(BaseFile):
    """Image file type from schema/types/file.graphql.

    Implements BaseFile and inherits StashObject through it."""

    __type_name__ = "ImageFile"

    # Required fields
    format: str  # String! (e.g., "jpeg", "png", "gif", "webp")
    width: int  # Int!
    height: int  # Int!


class MoveFilesInput(BaseModel):
    """Input for moving files."""

    ids: list[str]  # [ID!]!
    destination_folder: str | None = None  # String
    destination_folder_id: str | None = None  # ID
    destination_basename: str | None = None  # String


class SetFingerprintsInput(BaseModel):
    """Input for setting fingerprints."""

    type_: str = Field(alias="type")  # String! - aliased to avoid built-in conflict
    value: str | None = None  # String


class StashID(BaseModel):
    """StashID type from schema/types/stash-box.graphql."""

    endpoint: str  # String!
    stash_id: str  # String!
    updated_at: datetime  # Time!


class StashIDInput(BaseModel):
    """Input for StashID from schema/types/stash-box.graphql."""

    endpoint: str  # String!
    stash_id: str  # String!
    updated_at: datetime | None = None  # Time


class VideoFile(BaseFile):
    """Video file type from schema/types/file.graphql.

    Implements BaseFile and inherits StashObject through it."""

    __type_name__ = "VideoFile"

    # Required fields
    format: str  # String!
    width: int  # Int!
    height: int  # Int!
    duration: float  # Float!
    video_codec: str  # String!
    audio_codec: str  # String!
    frame_rate: float  # Float!  # frame_rate in schema
    bit_rate: int  # Int!  # bit_rate in schema


# Union type for VisualFile (VideoFile or ImageFile)
VisualFile = VideoFile | ImageFile
