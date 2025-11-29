"""Scene marker types from schema/types/scene-marker.graphql and scene-marker-tag.graphql."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from .base import StashObject


if TYPE_CHECKING:
    from .scene import Scene
    from .tag import Tag


class SceneMarkerTag(BaseModel):
    """Scene marker tag type from schema/types/scene-marker-tag.graphql."""

    tag: Tag  # Tag! (from schema/types/scene-marker-tag.graphql)
    scene_markers: list[SceneMarker] = Field(
        default_factory=list
    )  # [SceneMarker!]! (from schema/types/scene-marker-tag.graphql)


class SceneMarkerCreateInput(BaseModel):
    """Input for creating scene markers from schema/types/scene-marker.graphql."""

    title: str  # String!
    seconds: float  # Float! (The required start time of the marker (in seconds). Supports decimals.)
    end_seconds: float | None = (
        None  # Float (The optional end time of the marker (in seconds). Supports decimals.)
    )
    scene_id: str  # ID!
    primary_tag_id: str  # ID!
    tag_ids: list[str] | None = None  # [ID!]


class SceneMarkerUpdateInput(BaseModel):
    """Input for updating scene markers from schema/types/scene-marker.graphql."""

    id: str  # ID!
    title: str | None = None  # String
    seconds: float | None = (
        None  # Float (The start time of the marker (in seconds). Supports decimals.)
    )
    end_seconds: float | None = (
        None  # Float (The end time of the marker (in seconds). Supports decimals.)
    )
    scene_id: str | None = None  # ID
    primary_tag_id: str | None = None  # ID
    tag_ids: list[str] | None = None  # [ID!]


class SceneMarker(StashObject):
    """Scene marker type from schema/types/scene-marker.graphql."""

    __type_name__ = "SceneMarker"
    __update_input_type__ = SceneMarkerUpdateInput
    __create_input_type__ = SceneMarkerCreateInput

    # Fields to track for changes
    __tracked_fields__ = {
        "title",
        "seconds",
        "end_seconds",
        "scene",
        "primary_tag",
        "tags",
    }

    # Required fields
    scene: Scene  # Scene!
    title: str  # String!
    seconds: float  # Float! (The required start time of the marker (in seconds). Supports decimals.)
    primary_tag: Tag  # Tag!
    tags: list[Tag] = Field(default_factory=list)  # [Tag!]!
    stream: str  # String! (The path to stream this marker) (Resolver)
    preview: str  # String! (The path to the preview image for this marker) (Resolver)
    screenshot: (
        str  # String! (The path to the screenshot image for this marker) (Resolver)
    )

    # Optional fields
    end_seconds: float | None = (
        None  # Float (The optional end time of the marker (in seconds). Supports decimals.)
    )

    # Field definitions with their conversion functions
    __field_conversions__ = {
        "title": str,
        "seconds": float,
        "end_seconds": float,
    }

    __relationships__ = {
        # Standard ID relationships
        "scene": ("scene_id", False, None),  # (target_field, is_list, transform)
        "primary_tag": ("primary_tag_id", False, None),
        "tags": ("tag_ids", True, None),
    }


class FindSceneMarkersResultType(BaseModel):
    """Result type for finding scene markers from schema/types/scene-marker.graphql."""

    count: int  # Int!
    scene_markers: list[SceneMarker]  # [SceneMarker!]!


class MarkerStringsResultType(BaseModel):
    """Result type for marker strings from schema/types/scene-marker.graphql."""

    count: int  # Int!
    id: str  # ID!
    title: str  # String!
