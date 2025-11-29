"""Strawberry GraphQL types for Stash."""

from __future__ import annotations

# Base types
from .base import BulkUpdateIds, BulkUpdateStrings, StashObject

# Support types
from .config import (
    ConfigDefaultSettingsInput,
    ConfigDefaultSettingsResult,
    ConfigDisableDropdownCreate,
    ConfigDisableDropdownCreateInput,
    ConfigDLNAInput,
    ConfigDLNAResult,
    ConfigGeneralInput,
    ConfigGeneralResult,
    ConfigImageLightboxInput,
    ConfigImageLightboxResult,
    ConfigInterfaceInput,
    ConfigInterfaceResult,
    ConfigResult,
    Directory,
    GenerateAPIKeyInput,
    SetupInput,
    StashConfig,
    StashConfigInput,
)
from .enums import (
    BlobsStorageType,
    BulkUpdateIdMode,
    CircumisedEnum,
    CriterionModifier,
    FilterMode,
    GenderEnum,
    HashAlgorithm,
    ImageLightboxDisplayMode,
    ImageLightboxScrollMode,
    OnMultipleMatch,
    OrientationEnum,
    PackageType,
    PreviewPreset,
    ResolutionEnum,
    SortDirectionEnum,
    StreamingResolutionEnum,
)
from .files import (
    AssignSceneFileInput,
    BaseFile,
    FileSetFingerprintsInput,
    FindFilesResultType,
    FindFoldersResultType,
    Fingerprint,
    Folder,
    GalleryFile,
    ImageFile,
    MoveFilesInput,
    SceneHashInput,
    SetFingerprintsInput,
    StashID,
    VideoFile,
    VisualFile,
)
from .filters import (
    CircumcisionCriterionInput,
    CustomFieldCriterionInput,
    DateCriterionInput,
    DestroyFilterInput,
    FindFilterType,
    FloatCriterionInput,
    GalleryFilterType,
    GenderCriterionInput,
    GroupFilterType,
    HierarchicalMultiCriterionInput,
    ImageFilterType,
    IntCriterionInput,
    MultiCriterionInput,
    OrientationCriterionInput,
    PerformerFilterType,
    PhashDistanceCriterionInput,
    PHashDuplicationCriterionInput,
    ResolutionCriterionInput,
    SavedFilter,
    SavedFindFilterType,
    SaveFilterInput,
    SceneFilterType,
    SceneMarkerFilterType,
    SetDefaultFilterInput,
    StashIDCriterionInput,
    StringCriterionInput,
    StudioFilterType,
    TagFilterType,
    TimestampCriterionInput,
)

# Core types
from .gallery import (
    BulkGalleryUpdateInput,
    FindGalleriesResultType,
    FindGalleryChaptersResultType,
    Gallery,
    GalleryAddInput,
    GalleryChapter,
    GalleryChapterCreateInput,
    GalleryChapterUpdateInput,
    GalleryCreateInput,
    GalleryDestroyInput,
    GalleryPathsType,
    GalleryRemoveInput,
    GalleryResetCoverInput,
    GallerySetCoverInput,
    GalleryUpdateInput,
)
from .group import (
    BulkGroupUpdateInput,
    BulkUpdateGroupDescriptionsInput,
    FindGroupsResultType,
    Group,
    GroupCreateInput,
    GroupDescription,
    GroupDescriptionInput,
    GroupDestroyInput,
    GroupSubGroupAddInput,
    GroupSubGroupRemoveInput,
    GroupUpdateInput,
    ReorderSubGroupsInput,
)
from .image import (
    FindImagesResultType,
    Image,
    ImageDestroyInput,
    ImageFileType,
    ImagePathsType,
    ImagesDestroyInput,
)
from .job import FindJobInput, Job, JobStatus
from .logging import LogEntry, LogLevel
from .markers import (
    FindSceneMarkersResultType,
    MarkerStringsResultType,
    SceneMarker,
    SceneMarkerCreateInput,
    SceneMarkerTag,
    SceneMarkerUpdateInput,
)
from .metadata import (
    AnonymiseDatabaseInput,
    AutoTagMetadataInput,
    AutoTagMetadataOptions,
    BackupDatabaseInput,
    CleanGeneratedInput,
    CleanMetadataInput,
    CustomFieldsInput,
    ExportObjectsInput,
    ExportObjectTypeInput,
    GenerateMetadataInput,
    GenerateMetadataOptions,
    GeneratePreviewOptions,
    GeneratePreviewOptionsInput,
    IdentifyFieldOptions,
    IdentifyFieldOptionsInput,
    IdentifyMetadataOptions,
    IdentifyMetadataOptionsInput,
    ImportObjectsInput,
    MigrateInput,
    ScanMetaDataFilterInput,
    ScanMetadataInput,
    ScanMetadataOptions,
    SystemStatus,
)
from .not_implemented import (
    DLNAStatus,
    JobStatusUpdate,
    LatestVersion,
    SQLExecResult,
    SQLQueryResult,
    StashBoxValidationResult,
    Version,
)
from .performer import (
    FindPerformersResultType,
    Performer,
    PerformerCreateInput,
    PerformerUpdateInput,
)
from .scalars import Any, BoolMap, Int64, Map, PluginConfigMap, Time, Timestamp
from .scene import (
    BulkSceneUpdateInput,
    FindScenesResultType,
    HistoryMutationResult,
    ParseSceneFilenameResult,
    ParseSceneFilenamesResult,
    Scene,
    SceneCreateInput,
    SceneDestroyInput,
    SceneFileType,
    SceneGroup,
    SceneGroupInput,
    SceneMergeInput,
    SceneMovieID,
    SceneMovieInput,
    SceneParserResult,
    SceneParserResultType,
    ScenePathsType,
    ScenesDestroyInput,
    SceneStreamEndpoint,
    SceneUpdateInput,
)
from .studio import (
    FindStudiosResultType,
    Studio,
    StudioCreateInput,
    StudioDestroyInput,
    StudioUpdateInput,
)
from .tag import (
    BulkTagUpdateInput,
    FindTagsResultType,
    Tag,
    TagCreateInput,
    TagDestroyInput,
    TagsMergeInput,
    TagUpdateInput,
)


__all__: list[str] = [
    # Metadata types
    "AnonymiseDatabaseInput",
    # Scalar types
    "Any",
    # Scene types
    "AssignSceneFileInput",
    "AutoTagMetadataInput",
    "AutoTagMetadataOptions",
    "BackupDatabaseInput",
    # File types
    "BaseFile",
    # Enum types
    "BlobsStorageType",
    "BoolMap",
    # Gallery types
    "BulkGalleryUpdateInput",
    # Group types
    "BulkGroupUpdateInput",
    "BulkSceneUpdateInput",
    # Tag types
    "BulkTagUpdateInput",
    "BulkUpdateGroupDescriptionsInput",
    "BulkUpdateIdMode",
    # Base types
    "BulkUpdateIds",
    "BulkUpdateStrings",
    # Filter types
    "CircumcisionCriterionInput",
    "CircumisedEnum",
    "CleanGeneratedInput",
    "CleanMetadataInput",
    "ConfigDLNAInput",
    "ConfigDLNAResult",
    # Config types
    "ConfigDefaultSettingsInput",
    "ConfigDefaultSettingsResult",
    "ConfigDisableDropdownCreate",
    "ConfigDisableDropdownCreateInput",
    "ConfigGeneralInput",
    "ConfigGeneralResult",
    "ConfigImageLightboxInput",
    "ConfigImageLightboxResult",
    "ConfigInterfaceInput",
    "ConfigInterfaceResult",
    "ConfigResult",
    "CriterionModifier",
    "CustomFieldCriterionInput",
    "CustomFieldsInput",
    # Not Implemented types
    "DLNAStatus",
    "DateCriterionInput",
    "DestroyFilterInput",
    "Directory",
    "ExportObjectTypeInput",
    "ExportObjectsInput",
    "FileSetFingerprintsInput",
    "FilterMode",
    "FindFilesResultType",
    "FindFilterType",
    "FindFoldersResultType",
    "FindGalleriesResultType",
    "FindGalleryChaptersResultType",
    "FindGroupsResultType",
    # Image types
    "FindImagesResultType",
    # Job types
    "FindJobInput",
    # Performer types
    "FindPerformersResultType",
    # Marker types
    "FindSceneMarkersResultType",
    "FindScenesResultType",
    # Studio types
    "FindStudiosResultType",
    "FindTagsResultType",
    "Fingerprint",
    "FloatCriterionInput",
    "Folder",
    "Gallery",
    "GalleryAddInput",
    "GalleryChapter",
    "GalleryChapterCreateInput",
    "GalleryChapterUpdateInput",
    "GalleryCreateInput",
    "GalleryDestroyInput",
    "GalleryFile",
    "GalleryFilterType",
    "GalleryPathsType",
    "GalleryRemoveInput",
    "GalleryResetCoverInput",
    "GallerySetCoverInput",
    "GalleryUpdateInput",
    "GenderCriterionInput",
    "GenderEnum",
    "GenerateAPIKeyInput",
    "GenerateMetadataInput",
    "GenerateMetadataOptions",
    "GeneratePreviewOptions",
    "GeneratePreviewOptionsInput",
    "Group",
    "GroupCreateInput",
    "GroupDescription",
    "GroupDescriptionInput",
    "GroupDestroyInput",
    "GroupFilterType",
    "GroupSubGroupAddInput",
    "GroupSubGroupRemoveInput",
    "GroupUpdateInput",
    "HashAlgorithm",
    "HierarchicalMultiCriterionInput",
    "HistoryMutationResult",
    "IdentifyFieldOptions",
    "IdentifyFieldOptionsInput",
    "IdentifyMetadataOptions",
    "IdentifyMetadataOptionsInput",
    "Image",
    "ImageDestroyInput",
    "ImageFile",
    "ImageFileType",
    "ImageFilterType",
    "ImageLightboxDisplayMode",
    "ImageLightboxScrollMode",
    "ImagePathsType",
    "ImagesDestroyInput",
    "ImportObjectsInput",
    "Int64",
    "IntCriterionInput",
    "Job",
    "JobStatus",
    "JobStatusUpdate",
    "JobStatusUpdate",
    "LatestVersion",
    # Log types
    "LogEntry",
    "LogLevel",
    "Map",
    "MarkerStringsResultType",
    "MigrateInput",
    "MoveFilesInput",
    "MultiCriterionInput",
    "OnMultipleMatch",
    "OrientationCriterionInput",
    "OrientationEnum",
    "PHashDuplicationCriterionInput",
    "PackageType",
    "ParseSceneFilenameResult",
    "ParseSceneFilenamesResult",
    "Performer",
    "PerformerCreateInput",
    "PerformerFilterType",
    "PerformerUpdateInput",
    "PhashDistanceCriterionInput",
    "PluginConfigMap",
    "PreviewPreset",
    "ReorderSubGroupsInput",
    "ResolutionCriterionInput",
    "ResolutionEnum",
    "SQLExecResult",
    "SQLQueryResult",
    "SaveFilterInput",
    "SavedFilter",
    "SavedFindFilterType",
    "ScanMetaDataFilterInput",
    "ScanMetadataInput",
    "ScanMetadataOptions",
    # Core types
    "Scene",
    "SceneCreateInput",
    "SceneDestroyInput",
    "SceneFileType",
    "SceneFilterType",
    "SceneGroup",
    "SceneGroupInput",
    "SceneHashInput",
    "SceneMarker",
    "SceneMarkerCreateInput",
    "SceneMarkerFilterType",
    "SceneMarkerTag",
    "SceneMarkerUpdateInput",
    "SceneMergeInput",
    "SceneMovieID",
    "SceneMovieInput",
    "SceneParserResult",
    "SceneParserResultType",
    "ScenePathsType",
    "SceneStreamEndpoint",
    "SceneUpdateInput",
    "ScenesDestroyInput",
    "SetDefaultFilterInput",
    "SetFingerprintsInput",
    "SetupInput",
    "SortDirectionEnum",
    "StashBoxValidationResult",
    "StashConfig",
    "StashConfigInput",
    "StashID",
    "StashIDCriterionInput",
    "StashObject",
    "StreamingResolutionEnum",
    "StringCriterionInput",
    "Studio",
    "StudioCreateInput",
    "StudioDestroyInput",
    "StudioFilterType",
    "StudioUpdateInput",
    "SystemStatus",
    "Tag",
    "TagCreateInput",
    "TagDestroyInput",
    "TagFilterType",
    "TagUpdateInput",
    "TagsMergeInput",
    "Time",
    "Timestamp",
    "TimestampCriterionInput",
    "Version",
    "VideoFile",
    "VisualFile",
]

# =============================================================================
# Pydantic Model Rebuilds
# =============================================================================
# Rebuild all Pydantic models to resolve forward references and circular dependencies.
# This must be done after all types are imported.
#
# Forward references occur when a type annotation references a class that hasn't
# been defined yet. With `from __future__ import annotations`, all annotations
# become strings that need to be resolved.

# Base types
StashObject.model_rebuild()
BulkUpdateStrings.model_rebuild()
BulkUpdateIds.model_rebuild()

# Core domain types (StashObject subclasses with complex relationships)
Scene.model_rebuild()
Performer.model_rebuild()
Image.model_rebuild()
Gallery.model_rebuild()
GalleryChapter.model_rebuild()
Tag.model_rebuild()
Studio.model_rebuild()
Group.model_rebuild()
SceneMarker.model_rebuild()

# File types
Folder.model_rebuild()
BaseFile.model_rebuild()

# Config models (circular dependencies between StashConfig, ConfigResult, etc.)
ConfigResult.model_rebuild()
ConfigDefaultSettingsResult.model_rebuild()
ConfigGeneralResult.model_rebuild()
ConfigInterfaceResult.model_rebuild()
ConfigDLNAResult.model_rebuild()
ConfigImageLightboxResult.model_rebuild()
ConfigDisableDropdownCreate.model_rebuild()
StashConfig.model_rebuild()

# Metadata/operation models
ScanMetadataOptions.model_rebuild()
AutoTagMetadataOptions.model_rebuild()
GenerateMetadataOptions.model_rebuild()
GeneratePreviewOptions.model_rebuild()
IdentifyMetadataOptions.model_rebuild()
IdentifyFieldOptions.model_rebuild()

# Input types with complex relationships
SceneUpdateInput.model_rebuild()
SceneCreateInput.model_rebuild()
PerformerUpdateInput.model_rebuild()
PerformerCreateInput.model_rebuild()
GalleryUpdateInput.model_rebuild()
GalleryCreateInput.model_rebuild()
GalleryChapterUpdateInput.model_rebuild()
GalleryChapterCreateInput.model_rebuild()
GroupUpdateInput.model_rebuild()
GroupCreateInput.model_rebuild()
StudioUpdateInput.model_rebuild()
StudioCreateInput.model_rebuild()
TagUpdateInput.model_rebuild()
TagCreateInput.model_rebuild()

# Result types (contain lists of domain types)
FindFilesResultType.model_rebuild()
FindFoldersResultType.model_rebuild()
FindScenesResultType.model_rebuild()
FindPerformersResultType.model_rebuild()
FindImagesResultType.model_rebuild()
FindGalleriesResultType.model_rebuild()
FindGalleryChaptersResultType.model_rebuild()
FindGroupsResultType.model_rebuild()
FindStudiosResultType.model_rebuild()
FindTagsResultType.model_rebuild()
FindSceneMarkersResultType.model_rebuild()

# Filter types (reference domain types)
SceneFilterType.model_rebuild()
PerformerFilterType.model_rebuild()
GalleryFilterType.model_rebuild()
GroupFilterType.model_rebuild()
StudioFilterType.model_rebuild()
TagFilterType.model_rebuild()
ImageFilterType.model_rebuild()
SceneMarkerFilterType.model_rebuild()
