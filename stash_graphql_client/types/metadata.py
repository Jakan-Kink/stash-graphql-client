"""Metadata types from schema/types/metadata.graphql."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .enums import (
    IdentifyFieldStrategy,
    ImportDuplicateEnum,
    ImportMissingRefEnum,
    PreviewPreset,
    SystemStatusEnum,
)


# Upload is only referenced in comments, not actually used
# if TYPE_CHECKING:
#     from strawberry.file_uploads import Upload
# else:
#     from strawberry.file_uploads import Upload


class AnonymiseDatabaseInput(BaseModel):
    """Input for database anonymisation from schema/types/metadata.graphql."""

    download: bool | None = None  # Boolean


class AutoTagMetadataInput(BaseModel):
    """Input for auto-tagging metadata from schema/types/metadata.graphql."""

    paths: list[str] | None = None  # [String!] (Paths to tag, null for all files)
    performers: list[str] | None = (
        None  # [String!] (IDs of performers to tag files with, or "*" for all)
    )
    studios: list[str] | None = (
        None  # [String!] (IDs of studios to tag files with, or "*" for all)
    )
    tags: list[str] | None = (
        None  # [String!] (IDs of tags to tag files with, or "*" for all)
    )


class AutoTagMetadataOptions(BaseModel):
    """Auto-tag metadata options from schema/types/metadata.graphql."""

    performers: list[str] | None = (
        None  # [String!] (IDs of performers to tag files with, or "*" for all)
    )
    studios: list[str] | None = (
        None  # [String!] (IDs of studios to tag files with, or "*" for all)
    )
    tags: list[str] | None = (
        None  # [String!] (IDs of tags to tag files with, or "*" for all)
    )


class BackupDatabaseInput(BaseModel):
    """Input for database backup from schema/types/metadata.graphql."""

    download: bool | None = None  # Boolean


class CleanGeneratedInput(BaseModel):
    """Input for cleaning generated files from schema/types/metadata.graphql."""

    blob_files: bool | None = Field(
        None, alias="blobFiles"
    )  # Boolean (Clean blob files without blob entries)
    sprites: bool | None = (
        None  # Boolean (Clean sprite and vtt files without scene entries)
    )
    screenshots: bool | None = (
        None  # Boolean (Clean preview files without scene entries)
    )
    transcodes: bool | None = (
        None  # Boolean (Clean scene transcodes without scene entries)
    )
    markers: bool | None = None  # Boolean (Clean marker files without marker entries)
    image_thumbnails: bool | None = Field(
        None,
        alias="imageThumbnails",  # Boolean (Clean image thumbnails/clips without image entries)
    )
    dry_run: bool = Field(
        alias="dryRun"
    )  # Boolean (Do a dry run. Don't delete any files)


class CleanMetadataInput(BaseModel):
    """Input for metadata cleaning from schema/types/metadata.graphql."""

    paths: list[str]  # [String!]
    dry_run: bool = Field(
        alias="dryRun"
    )  # Boolean! (Do a dry run. Don't delete any files)


class CustomFieldsInput(BaseModel):
    """Input for custom fields from schema/types/metadata.graphql."""

    full: dict[str, Any] | None = (
        None  # Map (If populated, the entire custom fields map will be replaced with this value)
    )
    partial: dict[str, Any] | None = (
        None  # Map (If populated, only the keys in this map will be updated)
    )


class ExportObjectTypeInput(BaseModel):
    """Input for export object type from schema/types/metadata.graphql."""

    ids: list[str] | None = None  # [String!]
    all: bool | None = None  # Boolean


class ExportObjectsInput(BaseModel):
    """Input for exporting objects from schema/types/metadata.graphql."""

    scenes: ExportObjectTypeInput | None = None  # ExportObjectTypeInput
    images: ExportObjectTypeInput | None = None  # ExportObjectTypeInput
    studios: ExportObjectTypeInput | None = None  # ExportObjectTypeInput
    performers: ExportObjectTypeInput | None = None  # ExportObjectTypeInput
    tags: ExportObjectTypeInput | None = None  # ExportObjectTypeInput
    groups: ExportObjectTypeInput | None = None  # ExportObjectTypeInput
    movies: ExportObjectTypeInput | None = (
        None  # ExportObjectTypeInput @deprecated(reason: "Use groups instead")
    )
    galleries: ExportObjectTypeInput | None = None  # ExportObjectTypeInput
    include_dependencies: bool | None = Field(
        None, alias="includeDependencies"
    )  # Boolean


class GenerateMetadataInput(BaseModel):
    """Input for metadata generation from schema/types/metadata.graphql."""

    covers: bool = False  # Boolean
    sprites: bool = False  # Boolean
    previews: bool = False  # Boolean
    image_previews: bool = Field(False, alias="imagePreviews")  # Boolean
    preview_options: GeneratePreviewOptionsInput | None = Field(
        None,
        alias="previewOptions",  # GeneratePreviewOptionsInput
    )
    markers: bool = False  # Boolean
    marker_image_previews: bool = Field(False, alias="markerImagePreviews")  # Boolean
    marker_screenshots: bool = Field(False, alias="markerScreenshots")  # Boolean
    transcodes: bool = False  # Boolean
    force_transcodes: bool = Field(False, alias="forceTranscodes")  # Boolean
    phashes: bool = False  # Boolean
    interactive_heatmaps_speeds: bool = Field(
        False, alias="interactiveHeatmapsSpeeds"
    )  # Boolean
    image_thumbnails: bool = Field(False, alias="imageThumbnails")  # Boolean
    clip_previews: bool = Field(False, alias="clipPreviews")  # Boolean
    scene_ids: list[str] | None = Field(
        None, alias="sceneIDs"
    )  # [ID!] (scene ids to generate for)
    marker_ids: list[str] | None = Field(
        None, alias="markerIDs"
    )  # [ID!] (marker ids to generate for)
    overwrite: bool = False  # Boolean (overwrite existing media)


class GenerateMetadataOptions(BaseModel):
    """Metadata generation options from schema/types/metadata.graphql."""

    covers: bool | None = None  # Boolean
    sprites: bool | None = None  # Boolean
    previews: bool | None = None  # Boolean
    image_previews: bool | None = Field(None, alias="imagePreviews")  # Boolean
    preview_options: GeneratePreviewOptions | None = Field(
        None, alias="previewOptions"
    )  # GeneratePreviewOptions
    markers: bool | None = None  # Boolean
    marker_image_previews: bool | None = Field(
        None, alias="markerImagePreviews"
    )  # Boolean
    marker_screenshots: bool | None = Field(None, alias="markerScreenshots")  # Boolean
    transcodes: bool | None = None  # Boolean
    phashes: bool | None = None  # Boolean
    interactive_heatmaps_speeds: bool | None = Field(
        None, alias="interactiveHeatmapsSpeeds"
    )  # Boolean
    image_thumbnails: bool | None = Field(None, alias="imageThumbnails")  # Boolean
    clip_previews: bool | None = Field(None, alias="clipPreviews")  # Boolean


class GeneratePreviewOptions(BaseModel):
    """Preview generation options from schema/types/metadata.graphql."""

    preview_segments: int | None = Field(
        None, alias="previewSegments"
    )  # Int (Number of segments in a preview file)
    preview_segment_duration: float | None = Field(
        None,
        alias="previewSegmentDuration",  # Float (Preview segment duration, in seconds)
    )
    preview_exclude_start: str | None = Field(
        None,
        alias="previewExcludeStart",  # String (Duration of start of video to exclude when generating previews)
    )
    preview_exclude_end: str | None = Field(
        None,
        alias="previewExcludeEnd",  # String (Duration of end of video to exclude when generating previews)
    )
    preview_preset: PreviewPreset | None = Field(
        None,
        alias="previewPreset",  # PreviewPreset (Preset when generating preview)
    )


class GeneratePreviewOptionsInput(BaseModel):
    """Input for preview generation options from schema/types/metadata.graphql."""

    preview_segments: int | None = Field(
        None, alias="previewSegments"
    )  # Int (Number of segments in a preview file)
    preview_segment_duration: float | None = Field(
        None,
        alias="previewSegmentDuration",  # Float (Preview segment duration, in seconds)
    )
    preview_exclude_start: str | None = Field(
        None,
        alias="previewExcludeStart",  # String (Duration of start of video to exclude when generating previews)
    )
    preview_exclude_end: str | None = Field(
        None,
        alias="previewExcludeEnd",  # String (Duration of end of video to exclude when generating previews)
    )
    preview_preset: PreviewPreset | None = Field(
        None,
        alias="previewPreset",  # PreviewPreset (Preset when generating preview)
    )


class IdentifyFieldOptions(BaseModel):
    """Identify field options from schema/types/metadata.graphql."""

    field: str  # String!
    strategy: IdentifyFieldStrategy  # IdentifyFieldStrategy!
    create_missing: bool = Field(
        alias="createMissing"
    )  # Boolean (creates missing objects if needed - only applicable for performers, tags and studios)


class IdentifyFieldOptionsInput(BaseModel):
    """Input for identify field options from schema/types/metadata.graphql."""

    field: str  # String!
    strategy: IdentifyFieldStrategy  # IdentifyFieldStrategy!
    create_missing: bool | None = Field(
        None,
        alias="createMissing",  # Boolean (creates missing objects if needed - only applicable for performers, tags and studios)
    )


class IdentifyMetadataOptions(BaseModel):
    """Identify metadata options from schema/types/metadata.graphql."""

    field_options: list[IdentifyFieldOptions] | None = Field(
        None,
        alias="fieldOptions",  # [IdentifyFieldOptions!] (any fields missing from here are defaulted to MERGE and createMissing false)
    )
    set_cover_image: bool | None = Field(
        None, alias="setCoverImage"
    )  # Boolean (defaults to true if not provided)
    set_organized: bool | None = Field(None, alias="setOrganized")  # Boolean
    include_male_performers: bool | None = Field(
        None,
        alias="includeMalePerformers",  # Boolean (defaults to true if not provided)
    )
    skip_multiple_matches: bool | None = Field(
        None,
        alias="skipMultipleMatches",  # Boolean (defaults to true if not provided)
    )
    skip_multiple_match_tag: str | None = Field(
        None,
        alias="skipMultipleMatchTag",  # String (tag to tag skipped multiple matches with)
    )
    skip_single_name_performers: bool | None = Field(
        None,
        alias="skipSingleNamePerformers",  # Boolean (defaults to true if not provided)
    )
    skip_single_name_performer_tag: str | None = Field(
        None,
        alias="skipSingleNamePerformerTag",  # String (tag to tag skipped single name performers with)
    )


class IdentifyMetadataOptionsInput(BaseModel):
    """Input for identify metadata options from schema/types/metadata.graphql."""

    field_options: list[IdentifyFieldOptionsInput] | None = Field(
        None,
        alias="fieldOptions",  # [IdentifyFieldOptionsInput!] (any fields missing from here are defaulted to MERGE and createMissing false)
    )
    set_cover_image: bool | None = Field(
        None, alias="setCoverImage"
    )  # Boolean (defaults to true if not provided)
    set_organized: bool | None = Field(None, alias="setOrganized")  # Boolean
    include_male_performers: bool | None = Field(
        None,
        alias="includeMalePerformers",  # Boolean (defaults to true if not provided)
    )
    skip_multiple_matches: bool | None = Field(
        None,
        alias="skipMultipleMatches",  # Boolean (defaults to true if not provided)
    )
    skip_multiple_match_tag: str | None = Field(
        None,
        alias="skipMultipleMatchTag",  # String (tag to tag skipped multiple matches with)
    )
    skip_single_name_performers: bool | None = Field(
        None,
        alias="skipSingleNamePerformers",  # Boolean (defaults to true if not provided)
    )
    skip_single_name_performer_tag: str | None = Field(
        None,
        alias="skipSingleNamePerformerTag",  # String (tag to tag skipped single name performers with)
    )


class ImportObjectsInput(BaseModel):
    """Input for importing objects from schema/types/metadata.graphql."""

    file: Any  # Upload!
    duplicate_behaviour: ImportDuplicateEnum = Field(
        alias="duplicateBehaviour"
    )  # ImportDuplicateEnum!
    missing_ref_behaviour: ImportMissingRefEnum = Field(
        alias="missingRefBehaviour"
    )  # ImportMissingRefEnum!


class MigrateInput(BaseModel):
    """Input for migration from schema/types/metadata.graphql."""

    backup_path: str = Field(alias="backupPath")  # String!


class MigrateSceneScreenshotsInput(BaseModel):
    """Input for migrating scene screenshots from schema/types/metadata.graphql."""

    delete_files: bool | None = Field(None, alias="deleteFiles")  # Boolean
    overwrite_existing: bool | None = Field(None, alias="overwriteExisting")  # Boolean


class MigrateBlobsInput(BaseModel):
    """Input for migrating blobs from schema/types/metadata.graphql."""

    delete_old: bool | None = Field(None, alias="deleteOld")  # Boolean


class ScanMetaDataFilterInput(BaseModel):
    """Filter options for meta data scanning from schema/types/metadata.graphql."""

    min_mod_time: datetime | None = Field(
        None,
        alias="minModTime",  # Timestamp (If set, files with a modification time before this time point are ignored by the scan)
    )


class ScanMetadataInput(BaseModel):
    """Input for metadata scanning from schema/types/metadata.graphql."""

    paths: list[str]  # [String!]
    rescan: bool | None = (
        None  # Boolean (Forces a rescan on files even if modification time is unchanged)
    )
    scan_generate_covers: bool | None = Field(
        None, alias="scanGenerateCovers"
    )  # Boolean (Generate covers during scan)
    scan_generate_previews: bool | None = Field(
        None, alias="scanGeneratePreviews"
    )  # Boolean (Generate previews during scan)
    scan_generate_image_previews: bool | None = Field(
        None,
        alias="scanGenerateImagePreviews",  # Boolean (Generate image previews during scan)
    )
    scan_generate_sprites: bool | None = Field(
        None, alias="scanGenerateSprites"
    )  # Boolean (Generate sprites during scan)
    scan_generate_phashes: bool | None = Field(
        None, alias="scanGeneratePhashes"
    )  # Boolean (Generate phashes during scan)
    scan_generate_thumbnails: bool | None = Field(
        None,
        alias="scanGenerateThumbnails",  # Boolean (Generate image thumbnails during scan)
    )
    scan_generate_clip_previews: bool | None = Field(
        None,
        alias="scanGenerateClipPreviews",  # Boolean (Generate image clip previews during scan)
    )
    filter: ScanMetaDataFilterInput | None = (
        None  # ScanMetaDataFilterInput (Filter options for the scan)
    )


class ScanMetadataOptions(BaseModel):
    """Metadata scan options from schema/types/metadata.graphql."""

    rescan: bool  # Boolean! (Forces a rescan on files even if modification time is unchanged)
    scan_generate_covers: bool = Field(
        alias="scanGenerateCovers"
    )  # Boolean! (Generate covers during scan)
    scan_generate_previews: bool = Field(
        alias="scanGeneratePreviews"
    )  # Boolean! (Generate previews during scan)
    scan_generate_image_previews: bool = Field(
        alias="scanGenerateImagePreviews"
    )  # Boolean! (Generate image previews during scan)
    scan_generate_sprites: bool = Field(
        alias="scanGenerateSprites"
    )  # Boolean! (Generate sprites during scan)
    scan_generate_phashes: bool = Field(
        alias="scanGeneratePhashes"
    )  # Boolean! (Generate phashes during scan)
    scan_generate_thumbnails: bool = Field(
        alias="scanGenerateThumbnails"
    )  # Boolean! (Generate image thumbnails during scan)
    scan_generate_clip_previews: bool = Field(
        alias="scanGenerateClipPreviews"  # Boolean! (Generate image clip previews during scan)
    )


class SystemStatus(BaseModel):
    """System status type from schema/types/metadata.graphql."""

    database_schema: int | None = Field(None, alias="databaseSchema")  # Int
    database_path: str | None = Field(None, alias="databasePath")  # String
    config_path: str | None = Field(None, alias="configPath")  # String
    app_schema: int = Field(alias="appSchema")  # Int!
    status: SystemStatusEnum  # SystemStatusEnum!
    os: str  # String!
    working_dir: str = Field(alias="workingDir")  # String!
    home_dir: str = Field(alias="homeDir")  # String!
    ffmpeg_path: str | None = Field(None, alias="ffmpegPath")  # String
    ffprobe_path: str | None = Field(None, alias="ffprobePath")  # String
