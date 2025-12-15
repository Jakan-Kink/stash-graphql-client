"""Filter types from schema/types/filters.graphql."""

from __future__ import annotations

from typing import Any

from .base import StashInput, StashResult
from .enums import (
    CircumisedEnum,
    CriterionModifier,
    FilterMode,
    GenderEnum,
    OrientationEnum,
    ResolutionEnum,
    SortDirectionEnum,
)
from .unset import UNSET, UnsetType


class FindFilterType(StashInput):
    """Input for find filter."""

    q: str | None | UnsetType = UNSET  # String
    page: int | None | UnsetType = UNSET  # Int
    per_page: int | None | UnsetType = UNSET  # Int (-1 for all, default 25)
    sort: str | None | UnsetType = UNSET  # String
    direction: SortDirectionEnum | None | UnsetType = UNSET  # SortDirectionEnum


class SavedFindFilterType(StashInput):
    """Saved find filter type."""

    q: str | None | UnsetType = UNSET  # String
    page: int | None | UnsetType = UNSET  # Int
    per_page: int | None | UnsetType = UNSET  # Int (-1 for all, default 25)
    sort: str | None | UnsetType = UNSET  # String
    direction: SortDirectionEnum | None | UnsetType = UNSET  # SortDirectionEnum


class ResolutionCriterionInput(StashInput):
    """Input for resolution criterion."""

    value: ResolutionEnum  # ResolutionEnum!
    modifier: CriterionModifier  # CriterionModifier!


class OrientationCriterionInput(StashInput):
    """Input for orientation criterion."""

    value: list[OrientationEnum]  # [OrientationEnum!]!


class PHashDuplicationCriterionInput(StashInput):
    """Input for phash duplication criterion."""

    duplicated: bool | None | UnsetType = UNSET  # Boolean
    distance: int | None | UnsetType = UNSET  # Int


class StashIDCriterionInput(StashInput):
    """Input for StashID criterion."""

    endpoint: str | None | UnsetType = UNSET  # String
    stash_id: str | None | UnsetType = UNSET  # String
    modifier: CriterionModifier  # CriterionModifier!


class CustomFieldCriterionInput(StashInput):
    """Input for custom field criterion."""

    field: str  # String!
    value: list[Any] | None | UnsetType = UNSET  # [Any!]
    modifier: CriterionModifier  # CriterionModifier!


class StringCriterionInput(StashInput):
    """Input for string criterion."""

    value: str  # String!
    modifier: CriterionModifier  # CriterionModifier!


class IntCriterionInput(StashInput):
    """Input for integer criterion."""

    value: int  # Int!
    value2: int | None | UnsetType = UNSET  # Int
    modifier: CriterionModifier  # CriterionModifier!


class FloatCriterionInput(StashInput):
    """Input for float criterion."""

    value: float  # Float!
    value2: float | None | UnsetType = UNSET  # Float
    modifier: CriterionModifier  # CriterionModifier!


class MultiCriterionInput(StashInput):
    """Input for multi criterion."""

    value: list[str] | None | UnsetType = UNSET  # [ID!]
    modifier: CriterionModifier  # CriterionModifier!
    excludes: list[str] | None | UnsetType = UNSET  # [ID!]


class GenderCriterionInput(StashInput):
    """Input for gender criterion."""

    value: GenderEnum | None | UnsetType = UNSET  # GenderEnum
    value_list: list[GenderEnum] | None | UnsetType = UNSET  # [GenderEnum!]
    modifier: CriterionModifier  # CriterionModifier!


class CircumcisionCriterionInput(StashInput):
    """Input for circumcision criterion."""

    value: list[CircumisedEnum]  # [CircumisedEnum!]!
    modifier: CriterionModifier  # CriterionModifier!


class HierarchicalMultiCriterionInput(StashInput):
    """Input for hierarchical multi criterion."""

    value: list[str]  # [ID!]!
    modifier: CriterionModifier  # CriterionModifier!
    depth: int | None | UnsetType = UNSET  # Int
    excludes: list[str] | None | UnsetType = UNSET  # [ID!]


class DateCriterionInput(StashInput):
    """Input for date criterion."""

    value: str  # String!
    value2: str | None | UnsetType = UNSET  # String
    modifier: CriterionModifier  # CriterionModifier!


class TimestampCriterionInput(StashInput):
    """Input for timestamp criterion."""

    value: str  # String!
    value2: str | None | UnsetType = UNSET  # String
    modifier: CriterionModifier  # CriterionModifier!


class PhashDistanceCriterionInput(StashInput):
    """Input for phash distance criterion."""

    value: str  # String!
    modifier: CriterionModifier  # CriterionModifier!
    distance: int | None | UnsetType = UNSET  # Int


class SavedFilter(StashResult):
    """Saved filter type."""

    id: str  # ID!
    mode: FilterMode | UnsetType = UNSET  # FilterMode!
    name: str | UnsetType = UNSET  # String!
    find_filter: SavedFindFilterType | None | UnsetType = UNSET  # SavedFindFilterType
    object_filter: dict[str, Any] | None | UnsetType = UNSET  # Map
    ui_options: dict[str, Any] | None | UnsetType = UNSET  # Map


class SaveFilterInput(StashInput):
    """Input for saving filter."""

    id: str | None | UnsetType = UNSET  # ID
    mode: FilterMode  # FilterMode!
    name: str  # String!
    find_filter: FindFilterType | None | UnsetType = UNSET  # FindFilterType
    object_filter: dict[str, Any] | None | UnsetType = UNSET  # Map
    ui_options: dict[str, Any] | None | UnsetType = UNSET  # Map


class DestroyFilterInput(StashInput):
    """Input for destroying filter."""

    id: str  # ID!


class SetDefaultFilterInput(StashInput):
    """Input for setting default filter."""

    mode: FilterMode  # FilterMode!
    find_filter: FindFilterType | None | UnsetType = UNSET  # FindFilterType
    object_filter: dict[str, Any] | None | UnsetType = UNSET  # Map
    ui_options: dict[str, Any] | None | UnsetType = UNSET  # Map


# Core filter types


class PerformerFilterType(StashInput):
    """Input for performer filter."""

    AND: PerformerFilterType | None | UnsetType = UNSET
    OR: PerformerFilterType | None | UnsetType = UNSET
    NOT: PerformerFilterType | None | UnsetType = UNSET
    name: StringCriterionInput | None | UnsetType = UNSET
    disambiguation: StringCriterionInput | None | UnsetType = UNSET
    details: StringCriterionInput | None | UnsetType = UNSET
    filter_favorites: bool | None | UnsetType = UNSET
    birth_year: IntCriterionInput | None | UnsetType = UNSET
    age: IntCriterionInput | None | UnsetType = UNSET
    ethnicity: StringCriterionInput | None | UnsetType = UNSET
    country: StringCriterionInput | None | UnsetType = UNSET
    eye_color: StringCriterionInput | None | UnsetType = UNSET
    height_cm: IntCriterionInput | None | UnsetType = UNSET
    measurements: StringCriterionInput | None | UnsetType = UNSET
    fake_tits: StringCriterionInput | None | UnsetType = UNSET
    penis_length: FloatCriterionInput | None | UnsetType = UNSET
    circumcised: CircumcisionCriterionInput | None | UnsetType = UNSET
    career_length: StringCriterionInput | None | UnsetType = UNSET
    tattoos: StringCriterionInput | None | UnsetType = UNSET
    piercings: StringCriterionInput | None | UnsetType = UNSET
    aliases: StringCriterionInput | None | UnsetType = UNSET
    gender: GenderCriterionInput | None | UnsetType = UNSET
    is_missing: str | None | UnsetType = UNSET
    tags: HierarchicalMultiCriterionInput | None | UnsetType = UNSET
    tag_count: IntCriterionInput | None | UnsetType = UNSET
    scene_count: IntCriterionInput | None | UnsetType = UNSET
    image_count: IntCriterionInput | None | UnsetType = UNSET
    gallery_count: IntCriterionInput | None | UnsetType = UNSET
    play_count: IntCriterionInput | None | UnsetType = UNSET
    o_counter: IntCriterionInput | None | UnsetType = UNSET
    stash_id_endpoint: StashIDCriterionInput | None | UnsetType = UNSET
    rating100: IntCriterionInput | None | UnsetType = UNSET
    url: StringCriterionInput | None | UnsetType = UNSET
    hair_color: StringCriterionInput | None | UnsetType = UNSET
    weight: IntCriterionInput | None | UnsetType = UNSET
    death_year: IntCriterionInput | None | UnsetType = UNSET
    studios: HierarchicalMultiCriterionInput | None | UnsetType = UNSET
    groups: HierarchicalMultiCriterionInput | None | UnsetType = UNSET
    performers: MultiCriterionInput | None | UnsetType = UNSET
    ignore_auto_tag: bool | None | UnsetType = UNSET
    birthdate: DateCriterionInput | None | UnsetType = UNSET
    death_date: DateCriterionInput | None | UnsetType = UNSET
    scenes_filter: SceneFilterType | None | UnsetType = UNSET
    images_filter: ImageFilterType | None | UnsetType = UNSET
    galleries_filter: GalleryFilterType | None | UnsetType = UNSET
    tags_filter: TagFilterType | None | UnsetType = UNSET
    created_at: TimestampCriterionInput | None | UnsetType = UNSET
    updated_at: TimestampCriterionInput | None | UnsetType = UNSET
    custom_fields: list[CustomFieldCriterionInput] | None | UnsetType = UNSET


class SceneMarkerFilterType(StashInput):
    """Input for scene marker filter."""

    tags: HierarchicalMultiCriterionInput | None | UnsetType = UNSET
    scene_tags: HierarchicalMultiCriterionInput | None | UnsetType = UNSET
    performers: MultiCriterionInput | None | UnsetType = UNSET
    scenes: MultiCriterionInput | None | UnsetType = UNSET
    duration: FloatCriterionInput | None | UnsetType = UNSET
    created_at: TimestampCriterionInput | None | UnsetType = UNSET
    updated_at: TimestampCriterionInput | None | UnsetType = UNSET
    scene_date: DateCriterionInput | None | UnsetType = UNSET
    scene_created_at: TimestampCriterionInput | None | UnsetType = UNSET
    scene_updated_at: TimestampCriterionInput | None | UnsetType = UNSET
    scene_filter: SceneFilterType | None | UnsetType = UNSET


class SceneFilterType(StashInput):
    """Input for scene filter."""

    AND: SceneFilterType | None | UnsetType = UNSET
    OR: SceneFilterType | None | UnsetType = UNSET
    NOT: SceneFilterType | None | UnsetType = UNSET
    id: IntCriterionInput | None | UnsetType = UNSET
    title: StringCriterionInput | None | UnsetType = UNSET
    code: StringCriterionInput | None | UnsetType = UNSET
    details: StringCriterionInput | None | UnsetType = UNSET
    director: StringCriterionInput | None | UnsetType = UNSET
    oshash: StringCriterionInput | None | UnsetType = UNSET
    checksum: StringCriterionInput | None | UnsetType = UNSET
    phash_distance: PhashDistanceCriterionInput | None | UnsetType = UNSET
    path: StringCriterionInput | None | UnsetType = UNSET
    file_count: IntCriterionInput | None | UnsetType = UNSET
    rating100: IntCriterionInput | None | UnsetType = UNSET
    organized: bool | None | UnsetType = UNSET
    o_counter: IntCriterionInput | None | UnsetType = UNSET
    duplicated: PHashDuplicationCriterionInput | None | UnsetType = UNSET
    resolution: ResolutionCriterionInput | None | UnsetType = UNSET
    orientation: OrientationCriterionInput | None | UnsetType = UNSET
    framerate: IntCriterionInput | None | UnsetType = UNSET
    bitrate: IntCriterionInput | None | UnsetType = UNSET
    video_codec: StringCriterionInput | None | UnsetType = UNSET
    audio_codec: StringCriterionInput | None | UnsetType = UNSET
    duration: IntCriterionInput | None | UnsetType = UNSET
    has_markers: str | None | UnsetType = UNSET
    is_missing: str | None | UnsetType = UNSET
    studios: HierarchicalMultiCriterionInput | None | UnsetType = UNSET
    groups: HierarchicalMultiCriterionInput | None | UnsetType = UNSET
    galleries: MultiCriterionInput | None | UnsetType = UNSET
    tags: HierarchicalMultiCriterionInput | None | UnsetType = UNSET
    tag_count: IntCriterionInput | None | UnsetType = UNSET
    performer_tags: HierarchicalMultiCriterionInput | None | UnsetType = UNSET
    performer_favorite: bool | None | UnsetType = UNSET
    performer_age: IntCriterionInput | None | UnsetType = UNSET
    performers: MultiCriterionInput | None | UnsetType = UNSET
    performer_count: IntCriterionInput | None | UnsetType = UNSET
    stash_id_endpoint: StashIDCriterionInput | None | UnsetType = UNSET
    url: StringCriterionInput | None | UnsetType = UNSET
    interactive: bool | None | UnsetType = UNSET
    interactive_speed: IntCriterionInput | None | UnsetType = UNSET
    captions: StringCriterionInput | None | UnsetType = UNSET
    resume_time: IntCriterionInput | None | UnsetType = UNSET
    play_count: IntCriterionInput | None | UnsetType = UNSET
    play_duration: IntCriterionInput | None | UnsetType = UNSET
    last_played_at: TimestampCriterionInput | None | UnsetType = UNSET
    date: DateCriterionInput | None | UnsetType = UNSET
    created_at: TimestampCriterionInput | None | UnsetType = UNSET
    updated_at: TimestampCriterionInput | None | UnsetType = UNSET
    galleries_filter: GalleryFilterType | None | UnsetType = UNSET
    performers_filter: PerformerFilterType | None | UnsetType = UNSET
    studios_filter: StudioFilterType | None | UnsetType = UNSET
    tags_filter: TagFilterType | None | UnsetType = UNSET
    groups_filter: GroupFilterType | None | UnsetType = UNSET
    markers_filter: SceneMarkerFilterType | None | UnsetType = UNSET
    files_filter: FileFilterType | None | UnsetType = UNSET


class GroupFilterType(StashInput):
    """Input for group filter."""

    AND: GroupFilterType | None | UnsetType = UNSET
    OR: GroupFilterType | None | UnsetType = UNSET
    NOT: GroupFilterType | None | UnsetType = UNSET
    name: StringCriterionInput | None | UnsetType = UNSET
    director: StringCriterionInput | None | UnsetType = UNSET
    synopsis: StringCriterionInput | None | UnsetType = UNSET
    duration: IntCriterionInput | None | UnsetType = UNSET
    rating100: IntCriterionInput | None | UnsetType = UNSET
    studios: HierarchicalMultiCriterionInput | None | UnsetType = UNSET
    is_missing: str | None | UnsetType = UNSET
    url: StringCriterionInput | None | UnsetType = UNSET
    performers: MultiCriterionInput | None | UnsetType = UNSET
    tags: HierarchicalMultiCriterionInput | None | UnsetType = UNSET
    tag_count: IntCriterionInput | None | UnsetType = UNSET
    date: DateCriterionInput | None | UnsetType = UNSET
    created_at: TimestampCriterionInput | None | UnsetType = UNSET
    updated_at: TimestampCriterionInput | None | UnsetType = UNSET
    o_counter: IntCriterionInput | None | UnsetType = UNSET
    containing_groups: HierarchicalMultiCriterionInput | None | UnsetType = UNSET
    sub_groups: HierarchicalMultiCriterionInput | None | UnsetType = UNSET
    containing_group_count: IntCriterionInput | None | UnsetType = UNSET
    sub_group_count: IntCriterionInput | None | UnsetType = UNSET
    scenes_filter: SceneFilterType | None | UnsetType = UNSET
    studios_filter: StudioFilterType | None | UnsetType = UNSET


class StudioFilterType(StashInput):
    """Input for studio filter."""

    AND: StudioFilterType | None | UnsetType = UNSET
    OR: StudioFilterType | None | UnsetType = UNSET
    NOT: StudioFilterType | None | UnsetType = UNSET
    name: StringCriterionInput | None | UnsetType = UNSET
    details: StringCriterionInput | None | UnsetType = UNSET
    parents: MultiCriterionInput | None | UnsetType = UNSET
    stash_id_endpoint: StashIDCriterionInput | None | UnsetType = UNSET
    tags: HierarchicalMultiCriterionInput | None | UnsetType = UNSET
    is_missing: str | None | UnsetType = UNSET
    rating100: IntCriterionInput | None | UnsetType = UNSET
    favorite: bool | None | UnsetType = UNSET
    scene_count: IntCriterionInput | None | UnsetType = UNSET
    image_count: IntCriterionInput | None | UnsetType = UNSET
    gallery_count: IntCriterionInput | None | UnsetType = UNSET
    tag_count: IntCriterionInput | None | UnsetType = UNSET
    url: StringCriterionInput | None | UnsetType = UNSET
    aliases: StringCriterionInput | None | UnsetType = UNSET
    child_count: IntCriterionInput | None | UnsetType = UNSET
    ignore_auto_tag: bool | None | UnsetType = UNSET
    scenes_filter: SceneFilterType | None | UnsetType = UNSET
    images_filter: ImageFilterType | None | UnsetType = UNSET
    galleries_filter: GalleryFilterType | None | UnsetType = UNSET
    created_at: TimestampCriterionInput | None | UnsetType = UNSET
    updated_at: TimestampCriterionInput | None | UnsetType = UNSET


class GalleryFilterType(StashInput):
    """Input for gallery filter."""

    AND: GalleryFilterType | None | UnsetType = UNSET
    OR: GalleryFilterType | None | UnsetType = UNSET
    NOT: GalleryFilterType | None | UnsetType = UNSET
    id: IntCriterionInput | None | UnsetType = UNSET
    title: StringCriterionInput | None | UnsetType = UNSET
    details: StringCriterionInput | None | UnsetType = UNSET
    checksum: StringCriterionInput | None | UnsetType = UNSET
    path: StringCriterionInput | None | UnsetType = UNSET
    file_count: IntCriterionInput | None | UnsetType = UNSET
    is_missing: str | None | UnsetType = UNSET
    is_zip: bool | None | UnsetType = UNSET
    rating100: IntCriterionInput | None | UnsetType = UNSET
    organized: bool | None | UnsetType = UNSET
    average_resolution: ResolutionCriterionInput | None | UnsetType = UNSET
    has_chapters: str | None | UnsetType = UNSET
    scenes: MultiCriterionInput | None | UnsetType = UNSET
    studios: HierarchicalMultiCriterionInput | None | UnsetType = UNSET
    tags: HierarchicalMultiCriterionInput | None | UnsetType = UNSET
    tag_count: IntCriterionInput | None | UnsetType = UNSET
    performer_tags: HierarchicalMultiCriterionInput | None | UnsetType = UNSET
    performers: MultiCriterionInput | None | UnsetType = UNSET
    performer_count: IntCriterionInput | None | UnsetType = UNSET
    performer_favorite: bool | None | UnsetType = UNSET
    performer_age: IntCriterionInput | None | UnsetType = UNSET
    image_count: IntCriterionInput | None | UnsetType = UNSET
    url: StringCriterionInput | None | UnsetType = UNSET
    date: DateCriterionInput | None | UnsetType = UNSET
    created_at: TimestampCriterionInput | None | UnsetType = UNSET
    updated_at: TimestampCriterionInput | None | UnsetType = UNSET
    code: StringCriterionInput | None | UnsetType = UNSET
    photographer: StringCriterionInput | None | UnsetType = UNSET
    scenes_filter: SceneFilterType | None | UnsetType = UNSET
    images_filter: ImageFilterType | None | UnsetType = UNSET
    performers_filter: PerformerFilterType | None | UnsetType = UNSET
    studios_filter: StudioFilterType | None | UnsetType = UNSET
    tags_filter: TagFilterType | None | UnsetType = UNSET
    files_filter: FileFilterType | None | UnsetType = UNSET
    folders_filter: FolderFilterType | None | UnsetType = UNSET


class TagFilterType(StashInput):
    """Input for tag filter."""

    AND: TagFilterType | None | UnsetType = UNSET
    OR: TagFilterType | None | UnsetType = UNSET
    NOT: TagFilterType | None | UnsetType = UNSET
    name: StringCriterionInput | None | UnsetType = UNSET
    sort_name: StringCriterionInput | None | UnsetType = UNSET
    aliases: StringCriterionInput | None | UnsetType = UNSET
    favorite: bool | None | UnsetType = UNSET
    description: StringCriterionInput | None | UnsetType = UNSET
    is_missing: str | None | UnsetType = UNSET
    scene_count: IntCriterionInput | None | UnsetType = UNSET
    image_count: IntCriterionInput | None | UnsetType = UNSET
    gallery_count: IntCriterionInput | None | UnsetType = UNSET
    performer_count: IntCriterionInput | None | UnsetType = UNSET
    studio_count: IntCriterionInput | None | UnsetType = UNSET
    movie_count: IntCriterionInput | None | UnsetType = UNSET
    group_count: IntCriterionInput | None | UnsetType = UNSET
    marker_count: IntCriterionInput | None | UnsetType = UNSET
    parents: HierarchicalMultiCriterionInput | None | UnsetType = UNSET
    children: HierarchicalMultiCriterionInput | None | UnsetType = UNSET
    parent_count: IntCriterionInput | None | UnsetType = UNSET
    child_count: IntCriterionInput | None | UnsetType = UNSET
    ignore_auto_tag: bool | None | UnsetType = UNSET
    scenes_filter: SceneFilterType | None | UnsetType = UNSET
    images_filter: ImageFilterType | None | UnsetType = UNSET
    galleries_filter: GalleryFilterType | None | UnsetType = UNSET
    created_at: TimestampCriterionInput | None | UnsetType = UNSET
    updated_at: TimestampCriterionInput | None | UnsetType = UNSET


class ImageFilterType(StashInput):
    """Input for image filter."""

    AND: ImageFilterType | None | UnsetType = UNSET
    OR: ImageFilterType | None | UnsetType = UNSET
    NOT: ImageFilterType | None | UnsetType = UNSET
    title: StringCriterionInput | None | UnsetType = UNSET
    details: StringCriterionInput | None | UnsetType = UNSET
    id: IntCriterionInput | None | UnsetType = UNSET
    checksum: StringCriterionInput | None | UnsetType = UNSET
    path: StringCriterionInput | None | UnsetType = UNSET
    file_count: IntCriterionInput | None | UnsetType = UNSET
    rating100: IntCriterionInput | None | UnsetType = UNSET
    date: DateCriterionInput | None | UnsetType = UNSET
    url: StringCriterionInput | None | UnsetType = UNSET
    organized: bool | None | UnsetType = UNSET
    o_counter: IntCriterionInput | None | UnsetType = UNSET
    resolution: ResolutionCriterionInput | None | UnsetType = UNSET
    orientation: OrientationCriterionInput | None | UnsetType = UNSET
    is_missing: str | None | UnsetType = UNSET
    studios: HierarchicalMultiCriterionInput | None | UnsetType = UNSET
    tags: HierarchicalMultiCriterionInput | None | UnsetType = UNSET
    tag_count: IntCriterionInput | None | UnsetType = UNSET
    performer_tags: HierarchicalMultiCriterionInput | None | UnsetType = UNSET
    performers: MultiCriterionInput | None | UnsetType = UNSET
    performer_count: IntCriterionInput | None | UnsetType = UNSET
    performer_favorite: bool | None | UnsetType = UNSET
    performer_age: IntCriterionInput | None | UnsetType = UNSET
    galleries: MultiCriterionInput | None | UnsetType = UNSET
    created_at: TimestampCriterionInput | None | UnsetType = UNSET
    updated_at: TimestampCriterionInput | None | UnsetType = UNSET
    code: StringCriterionInput | None | UnsetType = UNSET
    photographer: StringCriterionInput | None | UnsetType = UNSET
    galleries_filter: GalleryFilterType | None | UnsetType = UNSET
    performers_filter: PerformerFilterType | None | UnsetType = UNSET
    studios_filter: StudioFilterType | None | UnsetType = UNSET
    tags_filter: TagFilterType | None | UnsetType = UNSET
    files_filter: FileFilterType | None | UnsetType = UNSET


class FileFilterType(StashInput):
    """Input for file filter."""

    AND: FileFilterType | None | UnsetType = UNSET
    OR: FileFilterType | None | UnsetType = UNSET
    NOT: FileFilterType | None | UnsetType = UNSET
    path: StringCriterionInput | None | UnsetType = UNSET
    basename: StringCriterionInput | None | UnsetType = UNSET
    dir: StringCriterionInput | None | UnsetType = UNSET
    parent_folder: HierarchicalMultiCriterionInput | None | UnsetType = UNSET
    zip_file: MultiCriterionInput | None | UnsetType = UNSET
    mod_time: TimestampCriterionInput | None | UnsetType = UNSET
    duplicated: PHashDuplicationCriterionInput | None | UnsetType = UNSET
    hashes: list[FingerprintFilterInput] | None | UnsetType = UNSET
    video_file_filter: VideoFileFilterInput | None | UnsetType = UNSET
    image_file_filter: ImageFileFilterInput | None | UnsetType = UNSET
    scene_count: IntCriterionInput | None | UnsetType = UNSET
    image_count: IntCriterionInput | None | UnsetType = UNSET
    gallery_count: IntCriterionInput | None | UnsetType = UNSET
    scenes_filter: SceneFilterType | None | UnsetType = UNSET
    images_filter: ImageFilterType | None | UnsetType = UNSET
    galleries_filter: GalleryFilterType | None | UnsetType = UNSET
    created_at: TimestampCriterionInput | None | UnsetType = UNSET
    updated_at: TimestampCriterionInput | None | UnsetType = UNSET


class FolderFilterType(StashInput):
    """Input for folder filter."""

    AND: FolderFilterType | None | UnsetType = UNSET
    OR: FolderFilterType | None | UnsetType = UNSET
    NOT: FolderFilterType | None | UnsetType = UNSET
    path: StringCriterionInput | None | UnsetType = UNSET
    parent_folder: HierarchicalMultiCriterionInput | None | UnsetType = UNSET
    zip_file: MultiCriterionInput | None | UnsetType = UNSET
    mod_time: TimestampCriterionInput | None | UnsetType = UNSET
    gallery_count: IntCriterionInput | None | UnsetType = UNSET
    files_filter: FileFilterType | None | UnsetType = UNSET
    galleries_filter: GalleryFilterType | None | UnsetType = UNSET
    created_at: TimestampCriterionInput | None | UnsetType = UNSET
    updated_at: TimestampCriterionInput | None | UnsetType = UNSET


class VideoFileFilterInput(StashInput):
    """Input for video file filter."""

    resolution: ResolutionCriterionInput | None | UnsetType = UNSET
    orientation: OrientationCriterionInput | None | UnsetType = UNSET
    framerate: IntCriterionInput | None | UnsetType = UNSET
    bitrate: IntCriterionInput | None | UnsetType = UNSET
    format: StringCriterionInput | None | UnsetType = UNSET
    video_codec: StringCriterionInput | None | UnsetType = UNSET
    audio_codec: StringCriterionInput | None | UnsetType = UNSET
    duration: IntCriterionInput | None | UnsetType = UNSET
    captions: StringCriterionInput | None | UnsetType = UNSET
    interactive: bool | None | UnsetType = UNSET
    interactive_speed: IntCriterionInput | None | UnsetType = UNSET


class ImageFileFilterInput(StashInput):
    """Input for image file filter."""

    format: StringCriterionInput | None | UnsetType = UNSET
    resolution: ResolutionCriterionInput | None | UnsetType = UNSET
    orientation: OrientationCriterionInput | None | UnsetType = UNSET


class FingerprintFilterInput(StashInput):
    """Input for fingerprint filter."""

    type: str  # String!
    value: str  # String!
    distance: int | None | UnsetType = UNSET  # Int (defaults to 0)
