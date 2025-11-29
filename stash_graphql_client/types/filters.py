"""Filter types from schema/types/filters.graphql."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from .enums import (
    CircumisedEnum,
    CriterionModifier,
    FilterMode,
    GenderEnum,
    OrientationEnum,
    ResolutionEnum,
    SortDirectionEnum,
)


class FindFilterType(BaseModel):
    """Input for find filter."""

    q: str | None = None  # String
    page: int | None = None  # Int
    per_page: int | None = None  # Int (-1 for all, default 25)
    sort: str | None = None  # String
    direction: SortDirectionEnum | None = None  # SortDirectionEnum


class SavedFindFilterType(BaseModel):
    """Saved find filter type."""

    q: str | None = None  # String
    page: int | None = None  # Int
    per_page: int | None = None  # Int (-1 for all, default 25)
    sort: str | None = None  # String
    direction: SortDirectionEnum | None = None  # SortDirectionEnum


class ResolutionCriterionInput(BaseModel):
    """Input for resolution criterion."""

    value: ResolutionEnum  # ResolutionEnum!
    modifier: CriterionModifier  # CriterionModifier!


class OrientationCriterionInput(BaseModel):
    """Input for orientation criterion."""

    value: list[OrientationEnum]  # [OrientationEnum!]!


class PHashDuplicationCriterionInput(BaseModel):
    """Input for phash duplication criterion."""

    duplicated: bool | None = None  # Boolean
    distance: int | None = None  # Int


class StashIDCriterionInput(BaseModel):
    """Input for StashID criterion."""

    endpoint: str | None = None  # String
    stash_id: str | None = None  # String
    modifier: CriterionModifier  # CriterionModifier!


class CustomFieldCriterionInput(BaseModel):
    """Input for custom field criterion."""

    field: str  # String!
    value: list[Any] | None = None  # [Any!]
    modifier: CriterionModifier  # CriterionModifier!


class StringCriterionInput(BaseModel):
    """Input for string criterion."""

    value: str  # String!
    modifier: CriterionModifier  # CriterionModifier!


class IntCriterionInput(BaseModel):
    """Input for integer criterion."""

    value: int  # Int!
    value2: int | None = None  # Int
    modifier: CriterionModifier  # CriterionModifier!


class FloatCriterionInput(BaseModel):
    """Input for float criterion."""

    value: float  # Float!
    value2: float | None = None  # Float
    modifier: CriterionModifier  # CriterionModifier!


class MultiCriterionInput(BaseModel):
    """Input for multi criterion."""

    value: list[str] | None = None  # [ID!]
    modifier: CriterionModifier  # CriterionModifier!
    excludes: list[str] | None = None  # [ID!]


class GenderCriterionInput(BaseModel):
    """Input for gender criterion."""

    value: GenderEnum | None = None  # GenderEnum
    value_list: list[GenderEnum] | None = None  # [GenderEnum!]
    modifier: CriterionModifier  # CriterionModifier!


class CircumcisionCriterionInput(BaseModel):
    """Input for circumcision criterion."""

    value: list[CircumisedEnum]  # [CircumisedEnum!]!
    modifier: CriterionModifier  # CriterionModifier!


class HierarchicalMultiCriterionInput(BaseModel):
    """Input for hierarchical multi criterion."""

    value: list[str]  # [ID!]!
    modifier: CriterionModifier  # CriterionModifier!
    depth: int | None = None  # Int
    excludes: list[str] | None = None  # [ID!]


class DateCriterionInput(BaseModel):
    """Input for date criterion."""

    value: str  # String!
    value2: str | None = None  # String
    modifier: CriterionModifier  # CriterionModifier!


class TimestampCriterionInput(BaseModel):
    """Input for timestamp criterion."""

    value: str  # String!
    value2: str | None = None  # String
    modifier: CriterionModifier  # CriterionModifier!


class PhashDistanceCriterionInput(BaseModel):
    """Input for phash distance criterion."""

    value: str  # String!
    modifier: CriterionModifier  # CriterionModifier!
    distance: int | None = None  # Int


class SavedFilter(BaseModel):
    """Saved filter type."""

    id: str  # ID!
    mode: FilterMode  # FilterMode!
    name: str  # String!
    find_filter: SavedFindFilterType | None = None  # SavedFindFilterType
    object_filter: dict[str, Any] | None = None  # Map
    ui_options: dict[str, Any] | None = None  # Map


class SaveFilterInput(BaseModel):
    """Input for saving filter."""

    id: str | None = None  # ID
    mode: FilterMode  # FilterMode!
    name: str  # String!
    find_filter: FindFilterType | None = None  # FindFilterType
    object_filter: dict[str, Any] | None = None  # Map
    ui_options: dict[str, Any] | None = None  # Map


class DestroyFilterInput(BaseModel):
    """Input for destroying filter."""

    id: str  # ID!


class SetDefaultFilterInput(BaseModel):
    """Input for setting default filter."""

    mode: FilterMode  # FilterMode!
    find_filter: FindFilterType | None = None  # FindFilterType
    object_filter: dict[str, Any] | None = None  # Map
    ui_options: dict[str, Any] | None = None  # Map


# Core filter types


class PerformerFilterType(BaseModel):
    """Input for performer filter."""

    AND: PerformerFilterType | None = None
    OR: PerformerFilterType | None = None
    NOT: PerformerFilterType | None = None
    name: StringCriterionInput | None = None
    disambiguation: StringCriterionInput | None = None
    details: StringCriterionInput | None = None
    filter_favorites: bool | None = None
    birth_year: IntCriterionInput | None = None
    age: IntCriterionInput | None = None
    ethnicity: StringCriterionInput | None = None
    country: StringCriterionInput | None = None
    eye_color: StringCriterionInput | None = None
    height_cm: IntCriterionInput | None = None
    measurements: StringCriterionInput | None = None
    fake_tits: StringCriterionInput | None = None
    penis_length: FloatCriterionInput | None = None
    circumcised: CircumcisionCriterionInput | None = None
    career_length: StringCriterionInput | None = None
    tattoos: StringCriterionInput | None = None
    piercings: StringCriterionInput | None = None
    aliases: StringCriterionInput | None = None
    gender: GenderCriterionInput | None = None
    is_missing: str | None = None
    tags: HierarchicalMultiCriterionInput | None = None
    tag_count: IntCriterionInput | None = None
    scene_count: IntCriterionInput | None = None
    image_count: IntCriterionInput | None = None
    gallery_count: IntCriterionInput | None = None
    play_count: IntCriterionInput | None = None
    o_counter: IntCriterionInput | None = None
    stash_id_endpoint: StashIDCriterionInput | None = None
    rating100: IntCriterionInput | None = None
    url: StringCriterionInput | None = None
    hair_color: StringCriterionInput | None = None
    weight: IntCriterionInput | None = None
    death_year: IntCriterionInput | None = None
    studios: HierarchicalMultiCriterionInput | None = None
    performers: MultiCriterionInput | None = None
    ignore_auto_tag: bool | None = None
    birthdate: DateCriterionInput | None = None
    death_date: DateCriterionInput | None = None
    scenes_filter: SceneFilterType | None = None
    images_filter: ImageFilterType | None = None
    galleries_filter: GalleryFilterType | None = None
    tags_filter: TagFilterType | None = None
    created_at: TimestampCriterionInput | None = None
    updated_at: TimestampCriterionInput | None = None
    custom_fields: list[CustomFieldCriterionInput] | None = None


class SceneMarkerFilterType(BaseModel):
    """Input for scene marker filter."""

    tags: HierarchicalMultiCriterionInput | None = None
    scene_tags: HierarchicalMultiCriterionInput | None = None
    performers: MultiCriterionInput | None = None
    scenes: MultiCriterionInput | None = None
    duration: FloatCriterionInput | None = None
    created_at: TimestampCriterionInput | None = None
    updated_at: TimestampCriterionInput | None = None
    scene_date: DateCriterionInput | None = None
    scene_created_at: TimestampCriterionInput | None = None
    scene_updated_at: TimestampCriterionInput | None = None
    scene_filter: SceneFilterType | None = None


class SceneFilterType(BaseModel):
    """Input for scene filter."""

    AND: SceneFilterType | None = None
    OR: SceneFilterType | None = None
    NOT: SceneFilterType | None = None
    id: IntCriterionInput | None = None
    title: StringCriterionInput | None = None
    code: StringCriterionInput | None = None
    details: StringCriterionInput | None = None
    director: StringCriterionInput | None = None
    oshash: StringCriterionInput | None = None
    checksum: StringCriterionInput | None = None
    phash_distance: PhashDistanceCriterionInput | None = None
    path: StringCriterionInput | None = None
    file_count: IntCriterionInput | None = None
    rating100: IntCriterionInput | None = None
    organized: bool | None = None
    o_counter: IntCriterionInput | None = None
    duplicated: PHashDuplicationCriterionInput | None = None
    resolution: ResolutionCriterionInput | None = None
    orientation: OrientationCriterionInput | None = None
    framerate: IntCriterionInput | None = None
    bitrate: IntCriterionInput | None = None
    video_codec: StringCriterionInput | None = None
    audio_codec: StringCriterionInput | None = None
    duration: IntCriterionInput | None = None
    has_markers: str | None = None
    is_missing: str | None = None
    studios: HierarchicalMultiCriterionInput | None = None
    groups: HierarchicalMultiCriterionInput | None = None
    galleries: MultiCriterionInput | None = None
    tags: HierarchicalMultiCriterionInput | None = None
    tag_count: IntCriterionInput | None = None
    performer_tags: HierarchicalMultiCriterionInput | None = None
    performer_favorite: bool | None = None
    performer_age: IntCriterionInput | None = None
    performers: MultiCriterionInput | None = None
    performer_count: IntCriterionInput | None = None
    stash_id_endpoint: StashIDCriterionInput | None = None
    url: StringCriterionInput | None = None
    interactive: bool | None = None
    interactive_speed: IntCriterionInput | None = None
    captions: StringCriterionInput | None = None
    resume_time: IntCriterionInput | None = None
    play_count: IntCriterionInput | None = None
    play_duration: IntCriterionInput | None = None
    last_played_at: TimestampCriterionInput | None = None
    date: DateCriterionInput | None = None
    created_at: TimestampCriterionInput | None = None
    updated_at: TimestampCriterionInput | None = None
    galleries_filter: GalleryFilterType | None = None
    performers_filter: PerformerFilterType | None = None
    studios_filter: StudioFilterType | None = None
    tags_filter: TagFilterType | None = None
    groups_filter: GroupFilterType | None = None
    markers_filter: SceneMarkerFilterType | None = None


class GroupFilterType(BaseModel):
    """Input for group filter."""

    AND: GroupFilterType | None = None
    OR: GroupFilterType | None = None
    NOT: GroupFilterType | None = None
    name: StringCriterionInput | None = None
    director: StringCriterionInput | None = None
    synopsis: StringCriterionInput | None = None
    duration: IntCriterionInput | None = None
    rating100: IntCriterionInput | None = None
    studios: HierarchicalMultiCriterionInput | None = None
    is_missing: str | None = None
    url: StringCriterionInput | None = None
    performers: MultiCriterionInput | None = None
    tags: HierarchicalMultiCriterionInput | None = None
    tag_count: IntCriterionInput | None = None
    date: DateCriterionInput | None = None
    created_at: TimestampCriterionInput | None = None
    updated_at: TimestampCriterionInput | None = None
    containing_groups: HierarchicalMultiCriterionInput | None = None
    sub_groups: HierarchicalMultiCriterionInput | None = None
    containing_group_count: IntCriterionInput | None = None
    sub_group_count: IntCriterionInput | None = None
    scenes_filter: SceneFilterType | None = None
    studios_filter: StudioFilterType | None = None


class StudioFilterType(BaseModel):
    """Input for studio filter."""

    AND: StudioFilterType | None = None
    OR: StudioFilterType | None = None
    NOT: StudioFilterType | None = None
    name: StringCriterionInput | None = None
    details: StringCriterionInput | None = None
    parents: MultiCriterionInput | None = None
    stash_id_endpoint: StashIDCriterionInput | None = None
    tags: HierarchicalMultiCriterionInput | None = None
    is_missing: str | None = None
    rating100: IntCriterionInput | None = None
    favorite: bool | None = None
    scene_count: IntCriterionInput | None = None
    image_count: IntCriterionInput | None = None
    gallery_count: IntCriterionInput | None = None
    tag_count: IntCriterionInput | None = None
    url: StringCriterionInput | None = None
    aliases: StringCriterionInput | None = None
    child_count: IntCriterionInput | None = None
    ignore_auto_tag: bool | None = None
    scenes_filter: SceneFilterType | None = None
    images_filter: ImageFilterType | None = None
    galleries_filter: GalleryFilterType | None = None
    created_at: TimestampCriterionInput | None = None
    updated_at: TimestampCriterionInput | None = None


class GalleryFilterType(BaseModel):
    """Input for gallery filter."""

    AND: GalleryFilterType | None = None
    OR: GalleryFilterType | None = None
    NOT: GalleryFilterType | None = None
    id: IntCriterionInput | None = None
    title: StringCriterionInput | None = None
    details: StringCriterionInput | None = None
    checksum: StringCriterionInput | None = None
    path: StringCriterionInput | None = None
    file_count: IntCriterionInput | None = None
    is_missing: str | None = None
    is_zip: bool | None = None
    rating100: IntCriterionInput | None = None
    organized: bool | None = None
    average_resolution: ResolutionCriterionInput | None = None
    has_chapters: str | None = None
    scenes: MultiCriterionInput | None = None
    studios: HierarchicalMultiCriterionInput | None = None
    tags: HierarchicalMultiCriterionInput | None = None
    tag_count: IntCriterionInput | None = None
    performer_tags: HierarchicalMultiCriterionInput | None = None
    performers: MultiCriterionInput | None = None
    performer_count: IntCriterionInput | None = None
    performer_favorite: bool | None = None
    performer_age: IntCriterionInput | None = None
    image_count: IntCriterionInput | None = None
    url: StringCriterionInput | None = None
    date: DateCriterionInput | None = None
    created_at: TimestampCriterionInput | None = None
    updated_at: TimestampCriterionInput | None = None
    code: StringCriterionInput | None = None
    photographer: StringCriterionInput | None = None
    scenes_filter: SceneFilterType | None = None
    images_filter: ImageFilterType | None = None
    performers_filter: PerformerFilterType | None = None
    studios_filter: StudioFilterType | None = None
    tags_filter: TagFilterType | None = None


class TagFilterType(BaseModel):
    """Input for tag filter."""

    AND: TagFilterType | None = None
    OR: TagFilterType | None = None
    NOT: TagFilterType | None = None
    name: StringCriterionInput | None = None
    aliases: StringCriterionInput | None = None
    favorite: bool | None = None
    description: StringCriterionInput | None = None
    is_missing: str | None = None
    scene_count: IntCriterionInput | None = None
    image_count: IntCriterionInput | None = None
    gallery_count: IntCriterionInput | None = None
    performer_count: IntCriterionInput | None = None
    studio_count: IntCriterionInput | None = None
    group_count: IntCriterionInput | None = None
    marker_count: IntCriterionInput | None = None
    parents: HierarchicalMultiCriterionInput | None = None
    children: HierarchicalMultiCriterionInput | None = None
    parent_count: IntCriterionInput | None = None
    child_count: IntCriterionInput | None = None
    ignore_auto_tag: bool | None = None
    scenes_filter: SceneFilterType | None = None
    images_filter: ImageFilterType | None = None
    galleries_filter: GalleryFilterType | None = None
    created_at: TimestampCriterionInput | None = None
    updated_at: TimestampCriterionInput | None = None


class ImageFilterType(BaseModel):
    """Input for image filter."""

    AND: ImageFilterType | None = None
    OR: ImageFilterType | None = None
    NOT: ImageFilterType | None = None
    title: StringCriterionInput | None = None
    details: StringCriterionInput | None = None
    id: IntCriterionInput | None = None
    checksum: StringCriterionInput | None = None
    path: StringCriterionInput | None = None
    file_count: IntCriterionInput | None = None
    rating100: IntCriterionInput | None = None
    date: DateCriterionInput | None = None
    url: StringCriterionInput | None = None
    organized: bool | None = None
    o_counter: IntCriterionInput | None = None
    resolution: ResolutionCriterionInput | None = None
    orientation: OrientationCriterionInput | None = None
    is_missing: str | None = None
    studios: HierarchicalMultiCriterionInput | None = None
    tags: HierarchicalMultiCriterionInput | None = None
    tag_count: IntCriterionInput | None = None
    performer_tags: HierarchicalMultiCriterionInput | None = None
    performers: MultiCriterionInput | None = None
    performer_count: IntCriterionInput | None = None
    performer_favorite: bool | None = None
    performer_age: IntCriterionInput | None = None
    galleries: MultiCriterionInput | None = None
    created_at: TimestampCriterionInput | None = None
    updated_at: TimestampCriterionInput | None = None
    code: StringCriterionInput | None = None
    photographer: StringCriterionInput | None = None
    galleries_filter: GalleryFilterType | None = None
    performers_filter: PerformerFilterType | None = None
    studios_filter: StudioFilterType | None = None
    tags_filter: TagFilterType | None = None
