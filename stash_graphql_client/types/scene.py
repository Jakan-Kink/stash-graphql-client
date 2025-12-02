"""Scene types from schema/types/scene.graphql."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from .base import BulkUpdateIds, BulkUpdateStrings, StashObject
from .files import StashID, StashIDInput, VideoFile


if TYPE_CHECKING:
    from .gallery import Gallery
    from .group import Group
    from .markers import SceneMarker
    from .performer import Performer
    from .studio import Studio
    from .tag import Tag


class AssignSceneFileInput(BaseModel):
    """Input for assigning a file to a scene from schema/types/scene.graphql."""

    scene_id: str  # ID!
    file_id: str  # ID!


class BulkSceneUpdateInput(BaseModel):
    """Input for bulk updating scenes."""

    # Optional fields
    clientMutationId: str | None = None  # String
    ids: list[str]  # [ID!]
    title: str | None = None  # String
    code: str | None = None  # String
    details: str | None = None  # String
    director: str | None = None  # String
    url: str | None = None  # String @deprecated(reason: "Use urls")
    urls: BulkUpdateStrings | None = None  # BulkUpdateStrings
    date: str | None = None  # String
    rating100: int | None = None  # Int (1-100)
    organized: bool | None = None  # Boolean
    studio_id: str | None = None  # ID
    gallery_ids: BulkUpdateIds | None = None  # BulkUpdateIds
    performer_ids: BulkUpdateIds | None = None  # BulkUpdateIds
    tag_ids: BulkUpdateIds | None = None  # BulkUpdateIds
    group_ids: BulkUpdateIds | None = None  # BulkUpdateIds
    movie_ids: BulkUpdateIds | None = (
        None  # BulkUpdateIds @deprecated(reason: "Use group_ids")
    )


class FindScenesResultType(BaseModel):
    """Result type for finding scenes from schema/types/scene.graphql.

    Fields:
    count: Total number of scenes
    duration: Total duration in seconds
    filesize: Total file size in bytes
    scenes: List of scenes
    """

    count: int  # Int!
    duration: float  # Float!
    filesize: float  # Float!
    scenes: list[Scene] = Field(default_factory=list)  # [Scene!]!


class HistoryMutationResult(BaseModel):
    """Result type for history mutation from schema/types/scene.graphql."""

    count: int  # Int!
    history: list[datetime]  # [Time!]!


class ParseSceneFilenameResult(BaseModel):
    """Result of parsing a scene filename."""

    scene: Scene  # Scene!
    title: str | None = None  # String
    code: str | None = None  # String
    details: str | None = None  # String
    director: str | None = None  # String
    url: str | None = None  # String
    date: str | None = None  # String
    # rating expressed as 1-5 (deprecated)
    rating: int | None = None  # Int @deprecated
    # rating expressed as 1-100
    rating100: int | None = None  # Int
    studio_id: str | None = None  # ID
    gallery_ids: list[str] | None = None  # [ID!]
    performer_ids: list[str] | None = None  # [ID!]
    movies: list[SceneMovieID] | None = None  # [SceneMovieID!]
    tag_ids: list[str] | None = None  # [ID!]


class ParseSceneFilenamesResult(BaseModel):
    """Results from parsing scene filenames."""

    count: int  # Int!
    results: list[ParseSceneFilenameResult] = Field(
        default_factory=list
    )  # [ParseSceneFilenameResult!]!


class SceneUpdateInput(BaseModel):
    """Input for updating scenes."""

    # Required fields
    id: str  # ID!

    # Optional fields
    client_mutation_id: str | None = None  # String
    title: str | None = None  # String
    code: str | None = None  # String
    details: str | None = None  # String
    director: str | None = None  # String
    url: str | None = None  # String @deprecated
    urls: list[str] | None = None  # [String!]
    date: str | None = None  # String
    rating100: int | None = None  # Int
    organized: bool | None = None  # Boolean
    studio_id: str | None = None  # ID
    gallery_ids: list[str] | None = None  # [ID!]
    performer_ids: list[str] | None = None  # [ID!]
    groups: list[SceneGroupInput] | None = None  # [SceneGroupInput!]
    tag_ids: list[str] | None = None  # [ID!]
    cover_image: str | None = None  # String (URL or base64)
    stash_ids: list[StashIDInput] | None = None  # [StashIDInput!]
    resume_time: float | None = None  # Float
    play_duration: float | None = None  # Float
    primary_file_id: str | None = None  # ID

    # Deprecated fields
    o_counter: int | None = None  # Int @deprecated
    play_count: int | None = None  # Int @deprecated


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
    title: str | None = None  # String
    code: str | None = None  # String
    details: str | None = None  # String
    director: str | None = None  # String
    date: str | None = None  # String
    rating100: int | None = None  # Int (1-100), not used in this client
    o_counter: int | None = None  # Int, not used in this client
    studio: Studio | None = None  # Studio

    # Interactive fields (from primary file)
    interactive: bool = False  # Boolean!
    interactive_speed: int | None = None  # Int

    # Playback tracking fields (from dataloaders)
    last_played_at: datetime | None = None  # Time
    play_count: int | None = None  # Int
    play_duration: float | None = None  # Float
    resume_time: float | None = None  # Float
    play_history: list[datetime] = Field(default_factory=list)  # [Time!]!
    o_history: list[datetime] = Field(default_factory=list)  # [Time!]!

    # Required fields
    urls: list[str] = Field(default_factory=list)  # [String!]!
    organized: bool = False  # Boolean!
    files: list[VideoFile] = Field(default_factory=list)  # [VideoFile!]!
    # Note: paths field removed - use SceneDetail for lazy-loaded path URLs
    scene_markers: list[SceneMarker] = Field(default_factory=list)  # [SceneMarker!]!
    galleries: list[Gallery] = Field(default_factory=list)  # [Gallery!]!
    groups: list[SceneGroup] = Field(default_factory=list)  # [SceneGroup!]!
    tags: list[Tag] = Field(default_factory=list)  # [Tag!]!
    performers: list[Performer] = Field(default_factory=list)  # [Performer!]!
    stash_ids: list[StashID] = Field(default_factory=list)  # [StashID!]!
    sceneStreams: list[SceneStreamEndpoint] = Field(
        default_factory=list
    )  # [SceneStreamEndpoint!]! (Return valid stream paths)

    # Optional lists
    captions: list[VideoCaption] = Field(default_factory=list)  # [VideoCaption!]

    # Relationship definitions with their mappings
    __relationships__ = {
        # Standard ID relationships
        "studio": ("studio_id", False, None),  # (target_field, is_list, transform)
        "performers": ("performer_ids", True, None),
        "tags": ("tag_ids", True, None),
        "galleries": ("gallery_ids", True, None),
        # Special case with custom transform
        "stash_ids": (
            "stash_ids",
            True,
            lambda s: StashIDInput(
                endpoint=s.endpoint, stash_id=s.stash_id, updated_at=s.updated_at
            ),
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


class SceneCreateInput(BaseModel):
    """Input for creating scenes."""

    # All fields optional
    title: str | None = None  # String
    code: str | None = None  # String
    details: str | None = None  # String
    director: str | None = None  # String
    url: str | None = None  # String @deprecated
    urls: list[str] | None = None  # [String!]
    date: str | None = None  # String
    rating100: int | None = None  # Int
    organized: bool | None = None  # Boolean
    studio_id: str | None = None  # ID
    gallery_ids: list[str] | None = None  # [ID!]
    performer_ids: list[str] | None = None  # [ID!]
    groups: list[SceneGroupInput] | None = None  # [SceneGroupInput!]
    tag_ids: list[str] | None = None  # [ID!]
    cover_image: str | None = None  # String (URL or base64)
    stash_ids: list[StashIDInput] | None = None  # [StashIDInput!]
    file_ids: list[str] | None = None  # [ID!]


class SceneDestroyInput(BaseModel):
    """Input for destroying a scene from schema/types/scene.graphql."""

    id: str  # ID!
    delete_file: bool | None = None  # Boolean
    delete_generated: bool | None = None  # Boolean


class SceneFileType(BaseModel):
    """Scene file type from schema/types/scene.graphql."""

    size: str  # String
    duration: float  # Float
    video_codec: str  # String
    audio_codec: str  # String
    width: int  # Int
    height: int  # Int
    framerate: float  # Float
    bitrate: int  # Int


class SceneGroup(BaseModel):
    """Scene group type from schema/types/scene.graphql."""

    group: Group  # Group!
    scene_index: int | None = None  # Int


class SceneGroupInput(BaseModel):
    """Input for scene group from schema/types/scene.graphql."""

    group_id: str  # ID!
    scene_index: int | None = None  # Int


class SceneHashInput(BaseModel):
    """Input for scene hash from schema/types/scene.graphql."""

    checksum: str | None = None  # String
    oshash: str | None = None  # String


class SceneMergeInput(BaseModel):
    """Input for merging scenes from schema/types/scene.graphql."""

    source: list[str]  # [ID!]!
    destination: str  # ID!
    values: SceneUpdateInput | None = None  # SceneUpdateInput
    play_history: bool | None = None  # Boolean
    o_history: bool | None = None  # Boolean


class SceneMovieID(BaseModel):
    """Movie ID with scene index."""

    movie_id: str  # ID!
    scene_index: str | None = None  # String


class SceneMovieInput(BaseModel):
    """Input for scene movie from schema/types/scene.graphql."""

    movie_id: str  # ID!
    scene_index: int | None = None  # Int


class SceneParserResult(BaseModel):
    """Result type for scene parser from schema/types/scene.graphql."""

    scene: Scene  # Scene!
    title: str | None = None  # String
    code: str | None = None  # String
    details: str | None = None  # String
    director: str | None = None  # String
    url: str | None = None  # String
    date: str | None = None  # String
    rating100: int | None = None  # Int (1-100)
    studio_id: str | None = None  # ID
    gallery_ids: list[str] | None = None  # [ID!]
    performer_ids: list[str] | None = None  # [ID!]

    tag_ids: list[str] | None = None  # [ID!]


class SceneParserResultType(BaseModel):
    """Result type for scene parser from schema/types/scene.graphql."""

    count: int  # Int!
    results: list[SceneParserResult] = Field(
        default_factory=list
    )  # [SceneParserResult!]!


class ScenePathsType(BaseModel):
    """Scene paths type from schema/types/scene.graphql."""

    screenshot: str | None = None  # String (Resolver)
    preview: str | None = None  # String (Resolver)
    stream: str | None = None  # String (Resolver)
    webp: str | None = None  # String (Resolver)
    vtt: str | None = None  # String (Resolver)
    sprite: str | None = None  # String (Resolver)
    funscript: str | None = None  # String (Resolver)
    interactive_heatmap: str | None = None  # String (Resolver)
    caption: str | None = None  # String (Resolver)


class SceneStreamEndpoint(BaseModel):
    """Scene stream endpoint type from schema/types/scene.graphql."""

    url: str  # String!
    mime_type: str | None = None  # String
    label: str | None = None  # String


class ScenesDestroyInput(BaseModel):
    """Input for destroying multiple scenes from schema/types/scene.graphql."""

    ids: list[str]  # [ID!]!
    delete_file: bool | None = None  # Boolean
    delete_generated: bool | None = None  # Boolean


class VideoCaption(BaseModel):
    """Video caption type from schema/types/scene.graphql."""

    language_code: str  # String!
    caption_type: str  # String!
