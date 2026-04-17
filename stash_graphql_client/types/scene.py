"""Scene types from schema/types/scene.graphql."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any, ClassVar

from pydantic import BaseModel, Field

from .base import (
    BulkUpdateIds,
    BulkUpdateStrings,
    StashInput,
    StashObject,
    StashResult,
    belongs_to,
    habtm,
    has_many,
    has_many_through,
)
from .files import StashID, StashIDInput, VideoFile
from .metadata import CustomFieldsInput
from .scalars import Map, Time
from .unset import UNSET, UnsetType, is_set


if TYPE_CHECKING:
    from stash_graphql_client.client import StashClient

    from .gallery import Gallery
    from .group import Group
    from .markers import SceneMarker
    from .performer import Performer
    from .studio import Studio
    from .tag import Tag


class BulkUpdateIdMode(StrEnum):
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
    custom_fields: CustomFieldsInput | None | UnsetType = (
        UNSET  # CustomFieldsInput (appSchema >= 79)
    )


class SceneDestroyInput(StashInput):
    """Input for destroying a scene from schema/types/scene.graphql."""

    id: str  # ID!
    delete_file: bool | None | UnsetType = UNSET  # Boolean
    delete_generated: bool | None | UnsetType = UNSET  # Boolean
    destroy_file_entry: bool | None | UnsetType = UNSET  # Boolean (appSchema >= 84)


class ScenesDestroyInput(StashInput):
    """Input for destroying multiple scenes from schema/types/scene.graphql."""

    ids: list[str] | UnsetType = UNSET  # [ID!]!
    delete_file: bool | None | UnsetType = UNSET  # Boolean
    delete_generated: bool | None | UnsetType = UNSET  # Boolean
    destroy_file_entry: bool | None | UnsetType = UNSET  # Boolean (appSchema >= 84)


class SceneMergeInput(StashInput):
    """Input for merging scenes from schema/types/scene.graphql."""

    source: list[str] | UnsetType = UNSET  # [ID!]!
    destination: str | UnsetType = UNSET  # ID!
    values: SceneUpdateInput | None | UnsetType = UNSET  # SceneUpdateInput
    play_history: bool | None | UnsetType = UNSET  # Boolean
    o_history: bool | None | UnsetType = UNSET  # Boolean


class Scene(StashObject):
    """Scene type from schema/types/scene.graphql.

    Note: Inherits from StashObject for implementation convenience, not because
    Scene implements any interface in the schema. StashObject provides common
    functionality like find_by_id, save, and to_input methods."""

    __type_name__ = "Scene"
    __short_repr_fields__ = ("title",)
    __update_input_type__ = SceneUpdateInput
    __destroy_input_type__ = SceneDestroyInput
    __bulk_destroy_input_type__ = ScenesDestroyInput
    __merge_input_type__ = SceneMergeInput
    # No __create_input_type__ - scenes can only be updated, they are created by the server during scanning

    # Fields to track for changes
    __tracked_fields__ = {
        "title",  # SceneUpdateInput
        "code",  # SceneUpdateInput
        "details",  # SceneUpdateInput
        "director",  # SceneUpdateInput
        "date",  # SceneUpdateInput
        "studio",  # mapped to studio_id
        "urls",  # SceneUpdateInput
        "organized",  # SceneUpdateInput
        "files",  # mapped to file_ids
        "galleries",  # mapped to gallery_ids
        "groups",  # SceneUpdateInput
        "tags",  # mapped to tag_ids
        "performers",  # mapped to performer_ids
        # Side-mutation fields (excluded from to_input, handled by dedicated mutations)
        "resume_time",  # sceneSaveActivity
        "play_duration",  # sceneSaveActivity
        "o_counter",  # sceneAddO/sceneDeleteO/sceneResetO
        "o_history",  # sceneAddO/sceneDeleteO
        "play_count",  # sceneAddPlay/sceneDeletePlay/sceneResetPlayCount
        "play_history",  # sceneAddPlay/sceneDeletePlay
    }

    # Side mutations: fields persisted via separate GraphQL mutations.
    # Shared lambda refs ensure save() deduplicates by identity (id()) when
    # multiple fields map to the same handler (e.g., resume_time + play_duration).
    _sm_activity = lambda client, obj: Scene._save_activity(client, obj)  # noqa: E731, PLW0108
    _sm_o = lambda client, obj: Scene._save_o(client, obj)  # noqa: E731, PLW0108
    _sm_play = lambda client, obj: Scene._save_play(client, obj)  # noqa: E731, PLW0108
    __side_mutations__: ClassVar[dict] = {
        "resume_time": _sm_activity,
        "play_duration": _sm_activity,
        "o_counter": _sm_o,
        "o_history": _sm_o,
        "play_count": _sm_play,
        "play_history": _sm_play,
    }

    # Optional fields
    title: str | None | UnsetType = UNSET  # String
    code: str | None | UnsetType = UNSET  # String
    details: str | None | UnsetType = UNSET  # String
    director: str | None | UnsetType = UNSET  # String
    date: str | None | UnsetType = UNSET  # String
    rating100: int | None | UnsetType = Field(
        default=UNSET, ge=0, le=100
    )  # Int (1-100)
    o_counter: int | None | UnsetType = Field(
        default=UNSET, ge=0
    )  # Int (managed via _save_o side handler)
    studio: Studio | None | UnsetType = UNSET  # Studio
    interactive: bool | None | UnsetType = UNSET  # Boolean
    interactive_speed: int | None | UnsetType = UNSET  # Int
    # created_at and updated_at inherited from StashObject
    last_played_at: Time | None | UnsetType = UNSET  # Time
    resume_time: float | None | UnsetType = UNSET  # Float
    play_duration: float | None | UnsetType = UNSET  # Float
    play_count: int | None | UnsetType = Field(default=UNSET, ge=0)  # Int
    play_history: list[Time] | None | UnsetType = UNSET  # [Time!]
    o_history: list[Time] | None | UnsetType = UNSET  # [Time!]

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

    # Capability-gated fields (appSchema >= 79)
    custom_fields: Map | UnsetType = UNSET  # Map! (appSchema >= 79)

    # Relationship definitions with their mappings
    __relationships__ = {
        "galleries": habtm("Gallery", inverse_query_field="scenes"),
        "performers": habtm("Performer", inverse_query_field="scenes"),
        "tags": habtm("Tag", inverse_query_field="scenes"),
        "studio": belongs_to("Studio", inverse_query_field="scenes"),
        "groups": has_many_through(
            "Group",
            transform=lambda sg: SceneGroupInput(
                group_id=sg.group.id if hasattr(sg, "group") else sg.id,
                scene_index=sg.scene_index if hasattr(sg, "scene_index") else None,
            ),
            inverse_query_field="scenes",
        ),
        "stash_ids": habtm(
            "StashID",
            transform=lambda s: StashIDInput(endpoint=s.endpoint, stash_id=s.stash_id),
        ),
        "scene_markers": has_many("SceneMarker", inverse_query_field="scene"),
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
    # Side-Mutation Handlers (field-based)
    # =========================================================================

    @staticmethod
    async def _save_activity(client: StashClient, scene: Scene) -> None:
        """Side-mutation handler for resume_time and play_duration.

        Called by save() when either field is dirty. Uses the client's
        scene_save_activity mixin method.
        """
        await client.scene_save_activity(
            scene.id,
            resume_time=scene.resume_time if is_set(scene.resume_time) else None,
            play_duration=scene.play_duration if is_set(scene.play_duration) else None,
        )

    @staticmethod
    async def _save_o(client: StashClient, scene: Scene) -> None:
        """Side-mutation handler for o_counter and o_history.

        Computes diff between current and snapshot o_history to determine
        which entries were added/removed, then fires the appropriate client
        mixin methods. Updates local fields from the mutation response.
        """
        current_history = scene.o_history if is_set(scene.o_history) else []
        snapshot_history = scene._snapshot.get("o_history", [])

        current_set = set(current_history) if current_history else set()
        snapshot_set = set(snapshot_history) if snapshot_history else set()

        added = current_set - snapshot_set
        removed = snapshot_set - current_set

        if added:
            hmr = await client.scene_add_o(scene.id, times=list(added))
            scene.o_counter = hmr.count
            scene.o_history = hmr.history
        if removed:
            hmr = await client.scene_delete_o(scene.id, times=list(removed))
            scene.o_counter = hmr.count
            scene.o_history = hmr.history

    @staticmethod
    async def _save_play(client: StashClient, scene: Scene) -> None:
        """Side-mutation handler for play_count and play_history.

        Computes diff between current and snapshot play_history to determine
        which entries were added/removed, then fires the appropriate client
        mixin methods. Updates local fields from the mutation response.
        """
        current_history = scene.play_history if is_set(scene.play_history) else []
        snapshot_history = scene._snapshot.get("play_history", [])

        current_set = set(current_history) if current_history else set()
        snapshot_set = set(snapshot_history) if snapshot_history else set()

        added = current_set - snapshot_set
        removed = snapshot_set - current_set

        if added:
            hmr = await client.scene_add_play(scene.id, times=list(added))
            scene.play_count = hmr.count
            scene.play_history = hmr.history
        if removed:
            hmr = await client.scene_delete_play(scene.id, times=list(removed))
            scene.play_count = hmr.count
            scene.play_history = hmr.history

    # =========================================================================
    # Queued Side Operations
    # =========================================================================

    def reset_play_count(self) -> None:
        """Queue resetting play count to 0. Call save() to persist."""

        async def _op(client, obj) -> None:
            await client.scene_reset_play_count(obj.id)
            obj.play_count = 0
            obj.play_history = []

        self._queue_side_op(_op)

    def reset_o(self) -> None:
        """Queue resetting o-counter to 0. Call save() to persist."""

        async def _op(client, obj) -> None:
            await client.scene_reset_o(obj.id)
            obj.o_counter = 0
            obj.o_history = []

        self._queue_side_op(_op)

    def reset_activity(
        self, reset_resume: bool = True, reset_duration: bool = True
    ) -> None:
        """Queue resetting activity data. Call save() to persist."""

        async def _op(client, obj) -> None:
            await client.scene_reset_activity(
                obj.id,
                reset_resume=reset_resume,
                reset_duration=reset_duration,
            )
            if reset_resume:
                obj.resume_time = None
            if reset_duration:
                obj.play_duration = None

        self._queue_side_op(_op)

    def generate_screenshot(self, at: float | None = None) -> None:
        """Queue screenshot generation. Call save() to persist."""

        async def _op(client, obj) -> None:
            await client.scene_generate_screenshot(obj.id, at=at)

        self._queue_side_op(_op)

    # =========================================================================
    # Convenience Helper Methods for Bidirectional Relationships
    # =========================================================================

    async def add_to_gallery(self, gallery: Gallery) -> None:
        """Add scene to gallery (syncs inverse automatically, call save() to persist)."""
        await self._add_to_relationship("galleries", gallery)

    async def remove_from_gallery(self, gallery: Gallery) -> None:
        """Remove scene from gallery (syncs inverse automatically, call save() to persist)."""
        await self._remove_from_relationship("galleries", gallery)

    async def add_performer(self, performer: Performer) -> None:
        """Add performer to scene (syncs inverse automatically, call save() to persist)."""
        await self._add_to_relationship("performers", performer)

    async def remove_performer(self, performer: Performer) -> None:
        """Remove performer from scene (syncs inverse automatically, call save() to persist)."""
        await self._remove_from_relationship("performers", performer)

    async def add_tag(self, tag: Tag) -> None:
        """Add tag to scene (syncs inverse automatically, call save() to persist)."""
        await self._add_to_relationship("tags", tag)

    async def remove_tag(self, tag: Tag) -> None:
        """Remove tag from scene (syncs inverse automatically, call save() to persist)."""
        await self._remove_from_relationship("tags", tag)

    def set_studio(self, studio: Studio | None) -> None:
        """Set scene studio (call save() to persist)."""
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
    """Result type for finding scenes from schema/types/scene.graphql."""

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
    custom_fields: dict[str, Any] | None | UnsetType = UNSET  # Map (appSchema >= 79)


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
    custom_fields: CustomFieldsInput | None | UnsetType = (
        UNSET  # CustomFieldsInput (appSchema >= 79)
    )


class SceneParserResultType(BaseModel):
    """Result type for scene parser from schema/types/scene.graphql."""

    count: int | UnsetType = UNSET  # Int!
    results: list[SceneParserResult] | UnsetType = UNSET  # [SceneParserResult!]!


class AssignSceneFileInput(StashInput):
    """Input for assigning a file to a scene from schema/types/scene.graphql."""

    scene_id: str | UnsetType = UNSET  # ID!
    file_id: str | UnsetType = UNSET  # ID!


class SceneHashInput(StashInput):
    """Input for scene hash from schema/types/scene.graphql."""

    checksum: str | None | UnsetType = UNSET  # String
    oshash: str | None | UnsetType = UNSET  # String


class SceneMovieInput(StashInput):
    """Input for scene movie from schema/types/scene.graphql."""

    movie_id: str | UnsetType = UNSET  # ID!
    scene_index: int | None | UnsetType = UNSET  # Int


class HistoryMutationResult(BaseModel):
    """Result type for history mutation from schema/types/scene.graphql."""

    count: int | UnsetType = UNSET  # Int!
    history: list[Time] | UnsetType = UNSET  # [Time!]!
