"""Metadata types from schema/types/metadata.graphql."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from .base import FromGraphQLMixin, StashInput
from .enums import (
    IdentifyFieldStrategy,
    ImportDuplicateEnum,
    ImportMissingRefEnum,
    PreviewPreset,
    SystemStatusEnum,
)
from .unset import UNSET, UnsetType


if TYPE_CHECKING:
    from .scraped_types import ScraperSource, ScraperSourceInput


class GeneratePreviewOptionsInput(StashInput):
    """Input for preview generation options from schema/types/metadata.graphql."""

    previewSegments: int | None | UnsetType = (
        UNSET  # Int (Number of segments in a preview file)
    )
    previewSegmentDuration: float | None | UnsetType = (
        UNSET  # Float (Preview segment duration, in seconds)
    )
    previewExcludeStart: str | None | UnsetType = (
        UNSET  # String (Duration of start of video to exclude when generating previews)
    )
    previewExcludeEnd: str | None | UnsetType = (
        UNSET  # String (Duration of end of video to exclude when generating previews)
    )
    previewPreset: PreviewPreset | None | UnsetType = (
        UNSET  # PreviewPreset (Preset when generating preview)
    )


class GenerateMetadataInput(StashInput):
    """Input for metadata generation from schema/types/metadata.graphql."""

    covers: bool | UnsetType = UNSET  # Boolean
    sprites: bool | UnsetType = UNSET  # Boolean
    previews: bool | UnsetType = UNSET  # Boolean
    imagePreviews: bool | UnsetType = UNSET  # Boolean
    previewOptions: GeneratePreviewOptionsInput | None | UnsetType = (
        UNSET  # GeneratePreviewOptionsInput
    )
    markers: bool | UnsetType = UNSET  # Boolean
    markerImagePreviews: bool | UnsetType = UNSET  # Boolean
    markerScreenshots: bool | UnsetType = UNSET  # Boolean
    transcodes: bool | UnsetType = UNSET  # Boolean
    forceTranscodes: bool | UnsetType = UNSET  # Boolean
    phashes: bool | UnsetType = UNSET  # Boolean
    interactiveHeatmapsSpeeds: bool | UnsetType = UNSET  # Boolean
    imageThumbnails: bool | UnsetType = UNSET  # Boolean
    clipPreviews: bool | UnsetType = UNSET  # Boolean
    sceneIDs: list[str] | None | UnsetType = UNSET  # [ID!] (scene ids to generate for)
    markerIDs: list[str] | None | UnsetType = (
        UNSET  # [ID!] (marker ids to generate for)
    )
    overwrite: bool | UnsetType = UNSET  # Boolean (overwrite existing media)


class GeneratePreviewOptions(BaseModel):
    """Preview generation options from schema/types/metadata.graphql."""

    previewSegments: int | None | UnsetType = (
        UNSET  # Int (Number of segments in a preview file)
    )
    previewSegmentDuration: float | None | UnsetType = (
        UNSET  # Float (Preview segment duration, in seconds)
    )
    previewExcludeStart: str | None | UnsetType = (
        UNSET  # String (Duration of start of video to exclude when generating previews)
    )
    previewExcludeEnd: str | None | UnsetType = (
        UNSET  # String (Duration of end of video to exclude when generating previews)
    )
    previewPreset: PreviewPreset | None | UnsetType = (
        UNSET  # PreviewPreset (Preset when generating preview)
    )


class GenerateMetadataOptions(BaseModel):
    """Metadata generation options from schema/types/metadata.graphql."""

    covers: bool | None | UnsetType = UNSET  # Boolean
    sprites: bool | None | UnsetType = UNSET  # Boolean
    previews: bool | None | UnsetType = UNSET  # Boolean
    imagePreviews: bool | None | UnsetType = UNSET  # Boolean
    previewOptions: GeneratePreviewOptions | None | UnsetType = (
        UNSET  # GeneratePreviewOptions
    )
    markers: bool | None | UnsetType = UNSET  # Boolean
    markerImagePreviews: bool | None | UnsetType = UNSET  # Boolean
    markerScreenshots: bool | None | UnsetType = UNSET  # Boolean
    transcodes: bool | None | UnsetType = UNSET  # Boolean
    phashes: bool | None | UnsetType = UNSET  # Boolean
    interactiveHeatmapsSpeeds: bool | None | UnsetType = UNSET  # Boolean
    imageThumbnails: bool | None | UnsetType = UNSET  # Boolean
    clipPreviews: bool | None | UnsetType = UNSET  # Boolean


class ScanMetaDataFilterInput(StashInput):
    """Filter options for meta data scanning from schema/types/metadata.graphql."""

    minModTime: datetime | None | UnsetType = (
        UNSET  # Timestamp (If set, files with a modification time before this time point are ignored by the scan)
    )


class ScanMetadataInput(StashInput):
    """Input for metadata scanning from schema/types/metadata.graphql."""

    paths: list[str] | UnsetType = UNSET  # [String!]
    rescan: bool | None | UnsetType = (
        UNSET  # Boolean (Forces a rescan on files even if modification time is unchanged)
    )
    scanGenerateCovers: bool | None | UnsetType = (
        UNSET  # Boolean (Generate covers during scan)
    )
    scanGeneratePreviews: bool | None | UnsetType = (
        UNSET  # Boolean (Generate previews during scan)
    )
    scanGenerateImagePreviews: bool | None | UnsetType = (
        UNSET  # Boolean (Generate image previews during scan)
    )
    scanGenerateSprites: bool | None | UnsetType = (
        UNSET  # Boolean (Generate sprites during scan)
    )
    scanGeneratePhashes: bool | None | UnsetType = (
        UNSET  # Boolean (Generate phashes during scan)
    )
    scanGenerateThumbnails: bool | None | UnsetType = (
        UNSET  # Boolean (Generate image thumbnails during scan)
    )
    scanGenerateClipPreviews: bool | None | UnsetType = (
        UNSET  # Boolean (Generate image clip previews during scan)
    )
    filter: ScanMetaDataFilterInput | None | UnsetType = (
        UNSET  # ScanMetaDataFilterInput (Filter options for the scan)
    )


class ScanMetadataOptions(BaseModel):
    """Metadata scan options from schema/types/metadata.graphql."""

    rescan: bool | UnsetType = (
        UNSET  # Boolean! (Forces a rescan on files even if modification time is unchanged)
    )
    scanGenerateCovers: bool | UnsetType = (
        UNSET  # Boolean! (Generate covers during scan)
    )
    scanGeneratePreviews: bool | UnsetType = (
        UNSET  # Boolean! (Generate previews during scan)
    )
    scanGenerateImagePreviews: bool | UnsetType = (
        UNSET  # Boolean! (Generate image previews during scan)
    )
    scanGenerateSprites: bool | UnsetType = (
        UNSET  # Boolean! (Generate sprites during scan)
    )
    scanGeneratePhashes: bool | UnsetType = (
        UNSET  # Boolean! (Generate phashes during scan)
    )
    scanGenerateThumbnails: bool | UnsetType = (
        UNSET  # Boolean! (Generate image thumbnails during scan)
    )
    scanGenerateClipPreviews: bool | UnsetType = (
        UNSET  # Boolean! (Generate image clip previews during scan)
    )


class CleanMetadataInput(StashInput):
    """Input for metadata cleaning from schema/types/metadata.graphql."""

    paths: list[str] | UnsetType = UNSET  # [String!]
    dry_run: bool | UnsetType = Field(
        default=UNSET, alias="dryRun"
    )  # Boolean! (Do a dry run. Don't delete any files)


class CleanGeneratedInput(StashInput):
    """Input for cleaning generated files from schema/types/metadata.graphql."""

    blob_files: bool | None | UnsetType = Field(
        default=UNSET, alias="blobFiles"
    )  # Boolean (Clean blob files without blob entries)
    sprites: bool | None | UnsetType = (
        UNSET  # Boolean (Clean sprite and vtt files without scene entries)
    )
    screenshots: bool | None | UnsetType = (
        UNSET  # Boolean (Clean preview files without scene entries)
    )
    transcodes: bool | None | UnsetType = (
        UNSET  # Boolean (Clean scene transcodes without scene entries)
    )
    markers: bool | None | UnsetType = (
        UNSET  # Boolean (Clean marker files without marker entries)
    )
    image_thumbnails: bool | None | UnsetType = Field(
        default=UNSET, alias="imageThumbnails"
    )  # Boolean (Clean image thumbnails/clips without image entries)
    dry_run: bool | None | UnsetType = Field(
        default=UNSET, alias="dryRun"
    )  # Boolean (Do a dry run. Don't delete any files)


class AutoTagMetadataInput(StashInput):
    """Input for auto-tagging metadata from schema/types/metadata.graphql."""

    paths: list[str] | None | UnsetType = (
        UNSET  # [String!] (Paths to tag, null for all files)
    )
    performers: list[str] | None | UnsetType = (
        UNSET  # [String!] (IDs of performers to tag files with, or "*" for all)
    )
    studios: list[str] | None | UnsetType = (
        UNSET  # [String!] (IDs of studios to tag files with, or "*" for all)
    )
    tags: list[str] | None | UnsetType = (
        UNSET  # [String!] (IDs of tags to tag files with, or "*" for all)
    )


class AutoTagMetadataOptions(BaseModel):
    """Auto-tag metadata options from schema/types/metadata.graphql."""

    performers: list[str] | None | UnsetType = (
        UNSET  # [String!] (IDs of performers to tag files with, or "*" for all)
    )
    studios: list[str] | None | UnsetType = (
        UNSET  # [String!] (IDs of studios to tag files with, or "*" for all)
    )
    tags: list[str] | None | UnsetType = (
        UNSET  # [String!] (IDs of tags to tag files with, or "*" for all)
    )


class IdentifyFieldOptionsInput(StashInput):
    """Input for identify field options from schema/types/metadata.graphql."""

    field: str | UnsetType = UNSET  # String!
    strategy: IdentifyFieldStrategy | UnsetType = UNSET  # IdentifyFieldStrategy!
    createMissing: bool | None | UnsetType = (
        UNSET  # Boolean (creates missing objects if needed - only applicable for performers, tags and studios)
    )


class IdentifyMetadataOptionsInput(StashInput):
    """Input for identify metadata options from schema/types/metadata.graphql."""

    fieldOptions: list[IdentifyFieldOptionsInput] | None | UnsetType = (
        UNSET  # [IdentifyFieldOptionsInput!] (any fields missing from here are defaulted to MERGE and createMissing false)
    )
    setCoverImage: bool | None | UnsetType = (
        UNSET  # Boolean (defaults to true if not provided)
    )
    setOrganized: bool | None | UnsetType = UNSET  # Boolean
    includeMalePerformers: bool | None | UnsetType = (
        UNSET  # Boolean (defaults to true if not provided)
    )
    skipMultipleMatches: bool | None | UnsetType = (
        UNSET  # Boolean (defaults to true if not provided)
    )
    skipMultipleMatchTag: str | None | UnsetType = (
        UNSET  # String (tag to tag skipped multiple matches with)
    )
    skipSingleNamePerformers: bool | None | UnsetType = (
        UNSET  # Boolean (defaults to true if not provided)
    )
    skipSingleNamePerformerTag: str | None | UnsetType = (
        UNSET  # String (tag to tag skipped single name performers with)
    )


class IdentifyFieldOptions(BaseModel):
    """Identify field options from schema/types/metadata.graphql."""

    field: str | UnsetType = UNSET  # String!
    strategy: IdentifyFieldStrategy | UnsetType = UNSET  # IdentifyFieldStrategy!
    createMissing: bool | UnsetType = (
        UNSET  # Boolean (creates missing objects if needed - only applicable for performers, tags and studios)
    )


class IdentifyMetadataOptions(BaseModel):
    """Identify metadata options from schema/types/metadata.graphql."""

    fieldOptions: list[IdentifyFieldOptions] | None | UnsetType = (
        UNSET  # [IdentifyFieldOptions!] (any fields missing from here are defaulted to MERGE and createMissing false)
    )
    setCoverImage: bool | None | UnsetType = (
        UNSET  # Boolean (defaults to true if not provided)
    )
    setOrganized: bool | None | UnsetType = UNSET  # Boolean
    includeMalePerformers: bool | None | UnsetType = (
        UNSET  # Boolean (defaults to true if not provided)
    )
    skipMultipleMatches: bool | None | UnsetType = (
        UNSET  # Boolean (defaults to true if not provided)
    )
    skipMultipleMatchTag: str | None | UnsetType = (
        UNSET  # String (tag to tag skipped multiple matches with)
    )
    skipSingleNamePerformers: bool | None | UnsetType = (
        UNSET  # Boolean (defaults to true if not provided)
    )
    skipSingleNamePerformerTag: str | None | UnsetType = (
        UNSET  # String (tag to tag skipped single name performers with)
    )


class ExportObjectTypeInput(StashInput):
    """Input for export object type from schema/types/metadata.graphql."""

    ids: list[str] | None | UnsetType = UNSET  # [String!]
    all: bool | None | UnsetType = UNSET  # Boolean


class ExportObjectsInput(StashInput):
    """Input for exporting objects from schema/types/metadata.graphql."""

    scenes: ExportObjectTypeInput | None | UnsetType = UNSET  # ExportObjectTypeInput
    images: ExportObjectTypeInput | None | UnsetType = UNSET  # ExportObjectTypeInput
    studios: ExportObjectTypeInput | None | UnsetType = UNSET  # ExportObjectTypeInput
    performers: ExportObjectTypeInput | None | UnsetType = (
        UNSET  # ExportObjectTypeInput
    )
    tags: ExportObjectTypeInput | None | UnsetType = UNSET  # ExportObjectTypeInput
    groups: ExportObjectTypeInput | None | UnsetType = UNSET  # ExportObjectTypeInput
    galleries: ExportObjectTypeInput | None | UnsetType = UNSET  # ExportObjectTypeInput
    include_dependencies: bool | None | UnsetType = Field(
        default=UNSET, alias="includeDependencies"
    )  # Boolean


class ImportObjectsInput(StashInput):
    """Input for importing objects from schema/types/metadata.graphql."""

    file: Any | UnsetType = UNSET  # Upload!
    duplicate_behaviour: ImportDuplicateEnum | UnsetType = Field(
        default=UNSET, alias="duplicateBehaviour"
    )  # ImportDuplicateEnum!
    missing_ref_behaviour: ImportMissingRefEnum | UnsetType = Field(
        default=UNSET, alias="missingRefBehaviour"
    )  # ImportMissingRefEnum!


class BackupDatabaseInput(StashInput):
    """Input for database backup from schema/types/metadata.graphql."""

    download: bool | None | UnsetType = UNSET  # Boolean


class AnonymiseDatabaseInput(StashInput):
    """Input for database anonymisation from schema/types/metadata.graphql."""

    download: bool | None | UnsetType = UNSET  # Boolean


class SystemStatus(FromGraphQLMixin, BaseModel):
    """System status type from schema/types/metadata.graphql."""

    databaseSchema: int | None | UnsetType = UNSET  # Int
    databasePath: str | None | UnsetType = UNSET  # String
    configPath: str | None | UnsetType = UNSET  # String
    appSchema: int | UnsetType = UNSET  # Int!
    status: SystemStatusEnum | UnsetType = UNSET  # SystemStatusEnum!
    os: str | UnsetType = UNSET  # String!
    workingDir: str | UnsetType = UNSET  # String!
    homeDir: str | UnsetType = UNSET  # String!
    ffmpegPath: str | None | UnsetType = UNSET  # String
    ffprobePath: str | None | UnsetType = UNSET  # String


class MigrateInput(StashInput):
    """Input for migration from schema/types/metadata.graphql."""

    backup_path: str | UnsetType = Field(default=UNSET, alias="backupPath")  # String!


class CustomFieldsInput(StashInput):
    """Input for custom fields from schema/types/metadata.graphql."""

    full: dict[str, Any] | None | UnsetType = (
        UNSET  # Map (If populated, the entire custom fields map will be replaced with this value)
    )
    partial: dict[str, Any] | None | UnsetType = (
        UNSET  # Map (If populated, only the keys in this map will be updated)
    )


class IdentifySourceInput(StashInput):
    """Input for identify source from schema/types/metadata.graphql."""

    source: ScraperSourceInput | UnsetType = UNSET  # ScraperSourceInput!
    options: IdentifyMetadataOptionsInput | None | UnsetType = (
        UNSET  # IdentifyMetadataOptionsInput (Options defined for a source override the defaults)
    )


class IdentifySource(BaseModel):
    """Identify source type from schema/types/metadata.graphql."""

    source: ScraperSource | UnsetType = UNSET  # ScraperSource!
    options: IdentifyMetadataOptions | None | UnsetType = (
        UNSET  # IdentifyMetadataOptions (Options defined for a source override the defaults)
    )


class IdentifyMetadataInput(StashInput):
    """Input for identify metadata from schema/types/metadata.graphql."""

    sources: list[IdentifySourceInput] | UnsetType = (
        UNSET  # [IdentifySourceInput!]! (An ordered list of sources to identify items with. Only the first source that finds a match is used.)
    )
    options: IdentifyMetadataOptionsInput | None | UnsetType = (
        UNSET  # IdentifyMetadataOptionsInput (Options defined here override the configured defaults)
    )
    sceneIDs: list[str] | None | UnsetType = UNSET  # [ID!] (scene ids to identify)
    paths: list[str] | None | UnsetType = (
        UNSET  # [String!] (paths of scenes to identify - ignored if scene ids are set)
    )


class IdentifyMetadataTaskOptions(BaseModel):
    """Identify metadata task options from schema/types/metadata.graphql."""

    sources: list[IdentifySource] | UnsetType = (
        UNSET  # [IdentifySource!]! (An ordered list of sources to identify items with. Only the first source that finds a match is used.)
    )
    options: IdentifyMetadataOptions | None | UnsetType = (
        UNSET  # IdentifyMetadataOptions (Options defined here override the configured defaults)
    )


class MigrateSceneScreenshotsInput(StashInput):
    """Input for migrating scene screenshots from schema/types/migration.graphql."""

    delete_files: bool | None | UnsetType = Field(
        UNSET, alias="deleteFiles"
    )  # Boolean (if true, delete screenshot files after migrating)
    overwrite_existing: bool | None | UnsetType = Field(
        UNSET, alias="overwriteExisting"
    )  # Boolean (if true, overwrite existing covers with the covers from the screenshots directory)


class MigrateBlobsInput(StashInput):
    """Input for migrating blobs from schema/types/migration.graphql."""

    delete_old: bool | None | UnsetType = Field(
        UNSET, alias="deleteOld"
    )  # Boolean (if true, delete blob data from old storage system)
