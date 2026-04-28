"""Metadata types from schema/types/metadata.graphql."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, ClassVar

from pydantic import BaseModel, Field, field_validator, model_validator

from .base import FromGraphQLMixin, StashInput
from .enums import (
    GenderEnum,
    IdentifyFieldStrategy,
    ImportDuplicateEnum,
    ImportMissingRefEnum,
    PreviewPreset,
    SystemStatusEnum,
)
from .unset import UNSET, UnsetType, is_set


# Server-side limit from pkg/sqlite/custom_fields.go (maxCustomFieldNameLength).
# Length is checked in BYTES (Go's len()) — UTF-8 multi-byte chars count for
# more than one. We mirror that to avoid surprising server-side rejections.
_CUSTOM_FIELD_NAME_MAX_BYTES = 64


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

    __safe_to_eat__: ClassVar[frozenset[str]] = frozenset(
        {
            "paths",
            "imageIDs",
            "galleryIDs",
            "imagePhashes",
        }
    )

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
    imagePhashes: bool | UnsetType = UNSET  # Boolean (appSchema >= 84)
    imageIDs: list[str] | None | UnsetType = (
        UNSET  # [ID!] (image ids to generate for) (appSchema >= 84)
    )
    galleryIDs: list[str] | None | UnsetType = (
        UNSET  # [ID!] (gallery ids to generate for) (appSchema >= 84)
    )
    paths: list[str] | None | UnsetType = (
        UNSET  # [String!] (paths to run generate on, in addition to the other ID lists)
    )
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
    scanGenerateImagePhashes: bool | None | UnsetType = (
        UNSET  # Boolean (Generate image phashes during scan) (appSchema >= 84)
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
    scanGenerateImagePhashes: bool | UnsetType = (
        UNSET  # Boolean! (Generate image phashes during scan) (appSchema >= 84)
    )


class CleanMetadataInput(StashInput):
    """Input for metadata cleaning from schema/types/metadata.graphql."""

    paths: list[str] | UnsetType = UNSET  # [String!]
    ignore_zip_file_contents: bool | UnsetType = Field(
        default=UNSET, alias="ignoreZipFileContents"
    )  # Boolean (Skip checking zip file contents during clean)
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
    performerGenders: list[GenderEnum] | None | UnsetType = (
        UNSET  # [GenderEnum!] (only identify performers with these genders) (appSchema >= 84)
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
    performerGenders: list[GenderEnum] | None | UnsetType = (
        UNSET  # [GenderEnum!] (only identify performers with these genders) (appSchema >= 84)
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
    include_blobs: bool | None | UnsetType = Field(
        default=UNSET, alias="includeBlobs"
    )  # Boolean (appSchema >= 84)


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


def _validate_custom_field_name(name: str) -> None:
    """Mirror server-side validation in customFieldsStore.validateCustomFieldName.

    Raises ValueError when the key would be rejected by the Stash backend.
    """
    if not isinstance(name, str):
        raise ValueError(
            f"custom field name must be a string, got {type(name).__name__}"
        )
    if not name.strip():
        raise ValueError("custom field name cannot be empty or whitespace-only")
    if name != name.strip():
        raise ValueError(
            f"custom field name {name!r} cannot have leading or trailing whitespace"
        )
    if len(name.encode("utf-8")) > _CUSTOM_FIELD_NAME_MAX_BYTES:
        raise ValueError(
            f"custom field name {name!r} exceeds {_CUSTOM_FIELD_NAME_MAX_BYTES} "
            f"bytes (UTF-8); Stash rejects longer field names"
        )


def _validate_custom_field_value(name: str, value: Any) -> None:
    """Mirror server-side rejection in getSQLValueFromCustomFieldInput.

    The Stash backend explicitly rejects nested structures (arrays / objects)
    because the BLOB column stores scalars and the maintainers haven't solved
    the JSON-string-vs-regular-string disambiguation. Consumers needing
    structured data must json.dumps() themselves on write and json.loads()
    on read (see MMsD's _mm_d watermark pattern).
    """
    if isinstance(value, (list, dict)):
        raise TypeError(
            f"custom field {name!r}: values must be scalar "
            f"(str/int/float/bool/None); got {type(value).__name__}. "
            f"Use json.dumps() for nested structures."
        )


class CustomFieldsInput(StashInput):
    """Input for custom fields from schema/types/metadata.graphql.

    Validates against the server-side rules in
    ``stash-server/pkg/sqlite/custom_fields.go``:

    - Field names: non-empty, no leading/trailing whitespace, ≤64 UTF-8 bytes.
    - Values: scalars only (str/int/float/bool/None); nested structures rejected.
    - ``full`` and ``partial`` are mutually exclusive — when both are sent the
      server silently picks ``full`` and drops ``partial``, which is a footgun.
    - Keys cannot appear in both ``partial`` and ``remove`` (server raises
      ``"cannot be in both values and delete keys"``).
    """

    full: dict[str, Any] | None | UnsetType = (
        UNSET  # Map (If populated, the entire custom fields map will be replaced with this value)
    )
    partial: dict[str, Any] | None | UnsetType = (
        UNSET  # Map (If populated, only the keys in this map will be updated)
    )
    remove: list[str] | None | UnsetType = (
        UNSET  # [String!] (If populated, these keys will be removed from the custom fields)
    )

    @field_validator("full", "partial", mode="after")
    @classmethod
    def _check_keys_and_values(cls, v: Any) -> Any:
        if not isinstance(v, dict):
            return v
        for k, val in v.items():
            _validate_custom_field_name(k)
            _validate_custom_field_value(k, val)
        return v

    @field_validator("remove", mode="after")
    @classmethod
    def _check_remove_keys(cls, v: Any) -> Any:
        if not isinstance(v, list):
            return v
        for k in v:
            _validate_custom_field_name(k)
        return v

    @model_validator(mode="after")
    def _check_mode_combinations(self) -> CustomFieldsInput:
        full_set = is_set(self.full) and self.full is not None
        partial_set = is_set(self.partial) and self.partial is not None
        if full_set and partial_set:
            raise ValueError(
                "CustomFieldsInput.full and partial are mutually exclusive — "
                "the server silently picks full and drops partial."
            )
        if partial_set and is_set(self.remove) and self.remove:
            partial_keys = set(self.partial or {})  # type: ignore[arg-type]
            overlap = partial_keys & set(self.remove)  # type: ignore[arg-type]
            if overlap:
                raise ValueError(
                    f"keys cannot appear in both partial and remove: {sorted(overlap)}"
                )
        return self


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
