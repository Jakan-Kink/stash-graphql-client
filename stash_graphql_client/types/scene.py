"""Scene types from schema/types/scene.graphql."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from .base import (
    BulkUpdateIds,
    BulkUpdateStrings,
    RelationshipMetadata,
    StashInput,
    StashObject,
    StashResult,
)
from .files import StashID, StashIDInput, VideoFile
from .scalars import Time
from .unset import UNSET, UnsetType


if TYPE_CHECKING:
    from .gallery import Gallery
    from .group import Group
    from .markers import SceneMarker
    from .performer import Performer
    from .studio import Studio
    from .tag import Tag


class BulkUpdateIdMode(str, Enum):
    """Bulk update ID mode from schema/types/scene.graphql."""

    SET = "SET"
    ADD = "ADD"
    REMOVE = "REMOVE"


class SceneGroup(BaseModel):
    """Scene group type from schema/types/scene.graphql."""

    group: Group | UnsetType = UNSET  # Group!
    scene_index: int | None | UnsetType = UNSET  # Int


class SceneMovie(BaseModel):
    """Scene movie type from schema/types/scene.graphql."""

    movie: Group | UnsetType = UNSET  # Movie! (Movie is deprecated, using Group)
    scene_index: int | None | UnsetType = UNSET  # Int


class VideoCaption(BaseModel):
    """Video caption type from schema/types/scene.graphql."""

    language_code: str | None | UnsetType = UNSET  # String!
    caption_type: str | None | UnsetType = UNSET  # String!


class SceneFileType(BaseModel):
    """Scene file type from schema/types/scene.graphql."""

    size: str | None | UnsetType = UNSET  # String
    duration: float | None | UnsetType = UNSET  # Float
    video_codec: str | None | UnsetType = UNSET  # String
    audio_codec: str | None | UnsetType = UNSET  # String
    width: int | None | UnsetType = UNSET  # Int
    height: int | None | UnsetType = UNSET  # Int
    framerate: float | None | UnsetType = UNSET  # Float
    bitrate: int | None | UnsetType = UNSET  # Int


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


class SceneStreamEndpoint(BaseModel):
    """Scene stream endpoint type from schema/types/scene.graphql."""

    url: str | UnsetType = UNSET  # String!
    mime_type: str | None | UnsetType = UNSET  # String
    label: str | None | UnsetType = UNSET  # String


class SceneGroupInput(StashInput):
    """Input for scene group from schema/types/scene.graphql."""

    group_id: str | UnsetType = UNSET  # ID!
    scene_index: int | None | UnsetType = UNSET  # Int


class SceneUpdateInput(StashInput):
    """Input for updating scenes."""

    # Required fields
    id: str  # ID!

    # Optional fields
    client_mutation_id: str | None | UnsetType = Field(
        default=UNSET, alias="clientMutationId"
    )  # String (camelCase in schema)
    title: str | None | UnsetType = UNSET  # String
    code: str | None | UnsetType = UNSET  # String
    details: str | None | UnsetType = UNSET  # String
    director: str | None | UnsetType = UNSET  # String
    urls: list[str] | None | UnsetType = UNSET  # [String!]
    date: str | None | UnsetType = UNSET  # String
    rating100: int | None | UnsetType = Field(default=UNSET, ge=0, le=100)  # Int
    organized: bool | None | UnsetType = UNSET  # Boolean
    studio_id: str | None | UnsetType = UNSET  # ID (snake_case in schema)
    gallery_ids: list[str] | None | UnsetType = UNSET  # [ID!] (snake_case in schema)
    performer_ids: list[str] | None | UnsetType = UNSET  # [ID!] (snake_case in schema)
    groups: list[SceneGroupInput] | None | UnsetType = UNSET  # [SceneGroupInput!]
    tag_ids: list[str] | None | UnsetType = UNSET  # [ID!] (snake_case in schema)
    cover_image: str | None | UnsetType = (
        UNSET  # String (URL or base64, snake_case in schema)
    )
    stash_ids: list[StashIDInput] | None | UnsetType = (
        UNSET  # [StashIDInput!] (snake_case in schema)
    )
    resume_time: float | None | UnsetType = UNSET  # Float (snake_case in schema)
    play_duration: float | None | UnsetType = UNSET  # Float (snake_case in schema)
    primary_file_id: str | None | UnsetType = UNSET  # ID (snake_case in schema)


class Scene(StashObject):
    """Scene type from schema/types/scene.graphql.

    Note: Inherits from StashObject for implementation convenience, not because
    Scene implements any interface in the schema. StashObject provides common
    functionality like find_by_id, save, and to_input methods."""

    __type_name__ = "Scene"
    __update_input_type__ = SceneUpdateInput
    # No __create_input_type__ - scenes can only be updated, they are created by the server during scanning

    # Fields to track for changes - only fields that can be written via input types
    __tracked_fields__ = {
        "title",  # SceneCreateInput/SceneUpdateInput
        "code",  # SceneCreateInput/SceneUpdateInput
        "details",  # SceneCreateInput/SceneUpdateInput
        "director",  # SceneCreateInput/SceneUpdateInput
        "date",  # SceneCreateInput/SceneUpdateInput
        "studio",  # mapped to studio_id
        "urls",  # SceneCreateInput/SceneUpdateInput
        "organized",  # SceneCreateInput/SceneUpdateInput
        "files",  # mapped to file_ids
        "galleries",  # mapped to gallery_ids
        "groups",  # SceneCreateInput/SceneUpdateInput
        "tags",  # mapped to tag_ids
        "performers",  # mapped to performer_ids
    }

    # Optional fields
    title: str | None | UnsetType = UNSET  # String
    code: str | None | UnsetType = UNSET  # String
    details: str | None | UnsetType = UNSET  # String
    director: str | None | UnsetType = UNSET  # String
    date: str | None | UnsetType = UNSET  # String
    rating100: int | None | UnsetType = Field(
        default=UNSET, ge=0, le=100
    )  # Int (1-100), not used in this client
    o_counter: int | None | UnsetType = Field(
        default=UNSET, ge=0
    )  # Int, not used in this client
    studio: Studio | None | UnsetType = UNSET  # Studio
    interactive: bool | None | UnsetType = UNSET  # Boolean
    interactive_speed: int | None | UnsetType = Field(
        default=UNSET, alias="interactiveSpeed"
    )  # Int
    # created_at and updated_at inherited from StashObject
    last_played_at: Time | None | UnsetType = Field(
        default=UNSET, alias="lastPlayedAt"
    )  # Time
    resume_time: float | None | UnsetType = Field(
        default=UNSET, alias="resumeTime"
    )  # Float
    play_duration: float | None | UnsetType = Field(
        default=UNSET, alias="playDuration"
    )  # Float
    play_count: int | None | UnsetType = Field(
        default=UNSET, ge=0, alias="playCount"
    )  # Int
    play_history: list[Time] | None | UnsetType = Field(
        default=UNSET, alias="playHistory"
    )  # [Time!]
    o_history: list[Time] | None | UnsetType = Field(
        default=UNSET, alias="oHistory"
    )  # [Time!]

    # Required fields
    urls: list[str] | UnsetType = UNSET  # [String!]!
    organized: bool | UnsetType = UNSET  # Boolean!
    files: list[VideoFile] | UnsetType = UNSET  # [VideoFile!]!
    paths: ScenePathsType | UnsetType = UNSET  # ScenePathsType! (Resolver)
    scene_markers: list[SceneMarker] | UnsetType = UNSET  # [SceneMarker!]!
    galleries: list[Gallery] | UnsetType = UNSET  # [Gallery!]!
    groups: list[SceneGroup] | UnsetType = UNSET  # [SceneGroup!]!
    tags: list[Tag] | UnsetType = UNSET  # [Tag!]!
    performers: list[Performer] | UnsetType = UNSET  # [Performer!]!
    stash_ids: list[StashID] | UnsetType = UNSET  # [StashID!]!
    scene_streams: list[SceneStreamEndpoint] | UnsetType = Field(
        default=UNSET, alias="sceneStreams"
    )  # [SceneStreamEndpoint!]! (Return valid stream paths)

    # Optional lists
    captions: list[VideoCaption] | None | UnsetType = (
        UNSET  # [VideoCaption!] - nullable list
    )

    # Relationship definitions with their mappings
    __relationships__ = {
        # Pattern A: Direct field relationships (many-to-many)
        "galleries": RelationshipMetadata(
            target_field="gallery_ids",
            is_list=True,
            query_field="galleries",
            inverse_type="Gallery",
            inverse_query_field="scenes",
            query_strategy="direct_field",
            notes="Backend auto-syncs both scene.galleries and gallery.scenes",
        ),
        "performers": RelationshipMetadata(
            target_field="performer_ids",
            is_list=True,
            query_field="performers",
            inverse_type="Performer",
            inverse_query_field="scenes",
            query_strategy="direct_field",
            notes="Backend auto-syncs scene.performers and performer.scenes",
        ),
        "tags": RelationshipMetadata(
            target_field="tag_ids",
            is_list=True,
            query_field="tags",
            inverse_type="Tag",
            inverse_query_field=None,  # Tag only has scene_count, not scenes list
            query_strategy="direct_field",
            notes="Tag has scene_count resolver, not direct scenes list",
        ),
        # Pattern B: Filter query relationship (many-to-one)
        "studio": RelationshipMetadata(
            target_field="studio_id",
            is_list=False,
            query_field="studio",
            inverse_type="Studio",
            inverse_query_field=None,  # No direct scenes field on Studio
            query_strategy="filter_query",
            filter_query_hint="findScenes(scene_filter={studios: {value: [studio_id]}})",
            notes="Studio uses filter-based queries. Use client.find_scenes(scene_filter=...) for inverse.",
        ),
        # Special case: Complex transform for StashID
        "stash_ids": RelationshipMetadata(
            target_field="stash_ids",
            is_list=True,
            transform=lambda s: StashIDInput(endpoint=s.endpoint, stash_id=s.stash_id),
            query_field="stash_ids",
            notes="Requires transform to StashIDInput for mutations",
        ),
    }

    # Field definitions with their conversion functions
    __field_conversions__ = {
        "title": str,
        "code": str,
        "details": str,
        "director": str,
        "urls": list,
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

    # =========================================================================
    # Convenience Helper Methods for Bidirectional Relationships
    # =========================================================================

    def add_to_gallery(self, gallery: Gallery) -> None:
        """Add this scene to a gallery.

        In-memory operation only. Call store.save(scene) to persist changes.
        The backend automatically syncs gallery.scenes when you save.

        Args:
            gallery: The Gallery instance to add this scene to

        Example:
            >>> scene = await client.find_scene("scene_id")
            >>> gallery = await client.find_gallery("gallery_id")
            >>> scene.add_to_gallery(gallery)
            >>> await store.save(scene)  # Persist the change
        """
        if self.galleries is UNSET:
            self.galleries = []
        if gallery not in self.galleries:
            self.galleries.append(gallery)

    def remove_from_gallery(self, gallery: Gallery) -> None:
        """Remove this scene from a gallery.

        In-memory operation only. Call store.save(scene) to persist changes.
        The backend automatically syncs gallery.scenes when you save.

        Args:
            gallery: The Gallery instance to remove this scene from

        Example:
            >>> scene.remove_from_gallery(gallery)
            >>> await store.save(scene)  # Persist the change
        """
        if self.galleries is not UNSET and gallery in self.galleries:
            self.galleries.remove(gallery)

    def add_performer(self, performer: Performer) -> None:
        """Add a performer to this scene.

        In-memory operation only. Call store.save(scene) to persist changes.
        The backend automatically syncs performer.scenes when you save.

        Args:
            performer: The Performer instance to add

        Example:
            >>> scene.add_performer(performer)
            >>> await store.save(scene)  # Persist the change
        """
        if self.performers is UNSET:
            self.performers = []
        if performer not in self.performers:
            self.performers.append(performer)

    def remove_performer(self, performer: Performer) -> None:
        """Remove a performer from this scene.

        In-memory operation only. Call store.save(scene) to persist changes.

        Args:
            performer: The Performer instance to remove

        Example:
            >>> scene.remove_performer(performer)
            >>> await store.save(scene)  # Persist the change
        """
        if self.performers is not UNSET and performer in self.performers:
            self.performers.remove(performer)

    def add_tag(self, tag: Tag) -> None:
        """Add a tag to this scene.

        In-memory operation only. Call store.save(scene) to persist changes.
        The backend automatically syncs tag.scene_count when you save.

        Args:
            tag: The Tag instance to add

        Example:
            >>> scene.add_tag(tag)
            >>> await store.save(scene)  # Persist the change
        """
        if self.tags is UNSET:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: Tag) -> None:
        """Remove a tag from this scene.

        In-memory operation only. Call store.save(scene) to persist changes.
        The backend automatically syncs tag.scene_count when you save.

        Args:
            tag: The Tag instance to remove

        Example:
            >>> scene.remove_tag(tag)
            >>> await store.save(scene)  # Persist the change
        """
        if self.tags is not UNSET and tag in self.tags:
            self.tags.remove(tag)

    def set_studio(self, studio: Studio | None) -> None:
        """Set the studio for this scene.

        In-memory operation only. Call store.save(scene) to persist changes.
        The backend automatically syncs studio.scene_count when you save.

        Args:
            studio: The Studio instance to set, or None to remove

        Example:
            >>> scene.set_studio(studio)
            >>> await store.save(scene)  # Persist the change
        """
        self.studio = studio


class SceneMovieID(BaseModel):
    """Movie ID with scene index."""

    movie_id: str | UnsetType = UNSET  # ID!
    scene_index: str | None | UnsetType = UNSET  # String


class SceneParserInput(StashInput):
    """Input for scene parser from schema/types/scene.graphql."""

    ignore_words: list[str] | None | UnsetType = Field(
        default=UNSET, alias="ignoreWords"
    )  # [String!]
    whitespace_characters: str | None | UnsetType = Field(
        default=UNSET, alias="whitespaceCharacters"
    )  # String
    capitalize_title: bool | None | UnsetType = Field(
        default=UNSET, alias="capitalizeTitle"
    )  # Boolean
    ignore_organized: bool | None | UnsetType = Field(
        default=UNSET, alias="ignoreOrganized"
    )  # Boolean


class FindScenesResultType(StashResult):
    """Result type for finding scenes from schema/types/scene.graphql.

    Fields:
    count: Total number of scenes
    duration: Total duration in seconds
    filesize: Total file size in bytes
    scenes: List of scenes
    """

    count: int | UnsetType = UNSET  # Int!
    duration: float | UnsetType = UNSET  # Float!
    filesize: float | UnsetType = UNSET  # Float!
    scenes: list[Scene] | UnsetType = UNSET  # [Scene!]!


class SceneParserResult(BaseModel):
    """Result type for scene parser from schema/types/scene.graphql."""

    scene: Scene | UnsetType = UNSET  # Scene!
    title: str | None | UnsetType = UNSET  # String
    code: str | None | UnsetType = UNSET  # String
    details: str | None | UnsetType = UNSET  # String
    director: str | None | UnsetType = UNSET  # String
    url: str | None | UnsetType = UNSET  # String
    date: str | None | UnsetType = UNSET  # String
    rating100: int | None | UnsetType = Field(
        default=UNSET, ge=0, le=100
    )  # Int (1-100)
    studio_id: str | None | UnsetType = UNSET  # ID
    gallery_ids: list[str] | None | UnsetType = UNSET  # [ID!]
    performer_ids: list[str] | None | UnsetType = UNSET  # [ID!]
    movies: list[SceneMovieID] | None | UnsetType = UNSET  # [SceneMovieID!]
    tag_ids: list[str] | None | UnsetType = UNSET  # [ID!]


class SceneCreateInput(StashInput):
    """Input for creating scenes."""

    # All fields optional
    title: str | None | UnsetType = UNSET  # String
    code: str | None | UnsetType = UNSET  # String
    details: str | None | UnsetType = UNSET  # String
    director: str | None | UnsetType = UNSET  # String
    urls: list[str] | None | UnsetType = UNSET  # [String!]
    date: str | None | UnsetType = UNSET  # String
    rating100: int | None | UnsetType = Field(default=UNSET, ge=0, le=100)  # Int
    organized: bool | None | UnsetType = UNSET  # Boolean
    studio_id: str | None | UnsetType = UNSET  # ID
    gallery_ids: list[str] | None | UnsetType = UNSET  # [ID!]
    performer_ids: list[str] | None | UnsetType = UNSET  # [ID!]
    groups: list[SceneGroupInput] | None | UnsetType = UNSET  # [SceneGroupInput!]
    tag_ids: list[str] | None | UnsetType = UNSET  # [ID!]
    cover_image: str | None | UnsetType = UNSET  # String (URL or base64)
    stash_ids: list[StashIDInput] | None | UnsetType = UNSET  # [StashIDInput!]
    file_ids: list[str] | None | UnsetType = UNSET  # [ID!]


class BulkSceneUpdateInput(StashInput):
    """Input for bulk updating scenes."""

    # Optional fields
    client_mutation_id: str | None | UnsetType = Field(
        default=UNSET, alias="clientMutationId"
    )  # String (camelCase in schema)
    ids: list[str] | UnsetType = UNSET  # [ID!]
    title: str | None | UnsetType = UNSET  # String
    code: str | None | UnsetType = UNSET  # String
    details: str | None | UnsetType = UNSET  # String
    director: str | None | UnsetType = UNSET  # String
    urls: BulkUpdateStrings | None | UnsetType = UNSET  # BulkUpdateStrings
    date: str | None | UnsetType = UNSET  # String
    rating100: int | None | UnsetType = Field(
        default=UNSET, ge=0, le=100
    )  # Int (1-100)
    organized: bool | None | UnsetType = UNSET  # Boolean
    studio_id: str | None | UnsetType = UNSET  # ID (snake_case in schema)
    gallery_ids: BulkUpdateIds | None | UnsetType = (
        UNSET  # BulkUpdateIds (snake_case in schema)
    )
    performer_ids: BulkUpdateIds | None | UnsetType = (
        UNSET  # BulkUpdateIds (snake_case in schema)
    )
    tag_ids: BulkUpdateIds | None | UnsetType = (
        UNSET  # BulkUpdateIds (snake_case in schema)
    )
    group_ids: BulkUpdateIds | None | UnsetType = (
        UNSET  # BulkUpdateIds (snake_case in schema)
    )


class SceneParserResultType(BaseModel):
    """Result type for scene parser from schema/types/scene.graphql."""

    count: int | UnsetType = UNSET  # Int!
    results: list[SceneParserResult] | UnsetType = UNSET  # [SceneParserResult!]!


class AssignSceneFileInput(StashInput):
    """Input for assigning a file to a scene from schema/types/scene.graphql."""

    scene_id: str | UnsetType = UNSET  # ID!
    file_id: str | UnsetType = UNSET  # ID!


class SceneDestroyInput(StashInput):
    """Input for destroying a scene from schema/types/scene.graphql."""

    id: str  # ID!
    delete_file: bool | None | UnsetType = UNSET  # Boolean
    delete_generated: bool | None | UnsetType = UNSET  # Boolean


class SceneHashInput(StashInput):
    """Input for scene hash from schema/types/scene.graphql."""

    checksum: str | None | UnsetType = UNSET  # String
    oshash: str | None | UnsetType = UNSET  # String


class SceneMergeInput(StashInput):
    """Input for merging scenes from schema/types/scene.graphql."""

    source: list[str] | UnsetType = UNSET  # [ID!]!
    destination: str | UnsetType = UNSET  # ID!
    values: SceneUpdateInput | None | UnsetType = UNSET  # SceneUpdateInput
    play_history: bool | None | UnsetType = UNSET  # Boolean
    o_history: bool | None | UnsetType = UNSET  # Boolean


class SceneMovieInput(StashInput):
    """Input for scene movie from schema/types/scene.graphql."""

    movie_id: str | UnsetType = UNSET  # ID!
    scene_index: int | None | UnsetType = UNSET  # Int


class ScenesDestroyInput(StashInput):
    """Input for destroying multiple scenes from schema/types/scene.graphql."""

    ids: list[str] | UnsetType = UNSET  # [ID!]!
    delete_file: bool | None | UnsetType = UNSET  # Boolean
    delete_generated: bool | None | UnsetType = UNSET  # Boolean


class HistoryMutationResult(BaseModel):
    """Result type for history mutation from schema/types/scene.graphql."""

    count: int | UnsetType = UNSET  # Int!
    history: list[Time] | UnsetType = UNSET  # [Time!]!
