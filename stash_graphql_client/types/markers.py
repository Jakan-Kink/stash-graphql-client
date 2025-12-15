"""Scene marker types from schema/types/scene-marker.graphql and scene-marker-tag.graphql."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel

from .base import (
    BulkUpdateIds,
    RelationshipMetadata,
    StashInput,
    StashObject,
    StashResult,
)
from .scalars import Time
from .unset import UNSET, UnsetType


if TYPE_CHECKING:
    from .scene import Scene
    from .tag import Tag


class SceneMarkerTag(BaseModel):
    """Scene marker tag type from schema/types/scene-marker-tag.graphql."""

    tag: Tag | UnsetType = UNSET  # Tag! (from schema/types/scene-marker-tag.graphql)
    scene_markers: list[SceneMarker] | UnsetType = (
        UNSET  # [SceneMarker!]! (from schema/types/scene-marker-tag.graphql)
    )


class SceneMarkerCreateInput(StashInput):
    """Input for creating scene markers from schema/types/scene-marker.graphql."""

    title: str | UnsetType = UNSET  # String!
    seconds: float | UnsetType = (
        UNSET  # Float! (The required start time of the marker (in seconds). Supports decimals.)
    )
    end_seconds: float | None | UnsetType = (
        UNSET  # Float (The optional end time of the marker (in seconds). Supports decimals.)
    )
    scene_id: str | UnsetType = UNSET  # ID!
    primary_tag_id: str | UnsetType = UNSET  # ID!
    tag_ids: list[str] | None | UnsetType = UNSET  # [ID!]


class SceneMarkerUpdateInput(StashInput):
    """Input for updating scene markers from schema/types/scene-marker.graphql."""

    id: str  # ID!
    title: str | None | UnsetType = UNSET  # String
    seconds: float | None | UnsetType = (
        UNSET  # Float (The start time of the marker (in seconds). Supports decimals.)
    )
    end_seconds: float | None | UnsetType = (
        UNSET  # Float (The end time of the marker (in seconds). Supports decimals.)
    )
    scene_id: str | None | UnsetType = UNSET  # ID
    primary_tag_id: str | None | UnsetType = UNSET  # ID
    tag_ids: list[str] | None | UnsetType = UNSET  # [ID!]


class BulkSceneMarkerUpdateInput(StashInput):
    """Input for bulk updating scene markers from schema/types/scene-marker.graphql."""

    ids: list[str] | None | UnsetType = UNSET  # [ID!]
    title: str | None | UnsetType = UNSET  # String
    primary_tag_id: str | None | UnsetType = UNSET  # ID
    tag_ids: BulkUpdateIds | None | UnsetType = UNSET  # BulkUpdateIds


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

    # All fields optional (GraphQL required fields may not be in fragment)
    scene: Scene | None | UnsetType = UNSET  # Scene!
    title: str | None | UnsetType = UNSET  # String!
    seconds: float | None | UnsetType = (
        UNSET  # Float! (The required start time of the marker (in seconds). Supports decimals.)
    )
    primary_tag: Tag | None | UnsetType = UNSET  # Tag!
    tags: list[Tag] | None | UnsetType = UNSET  # [Tag!]!
    stream: str | None | UnsetType = (
        UNSET  # String! (The path to stream this marker) (Resolver)
    )
    preview: str | None | UnsetType = (
        UNSET  # String! (The path to the preview image for this marker) (Resolver)
    )
    screenshot: str | None | UnsetType = (
        UNSET  # String! (The path to the screenshot image for this marker) (Resolver)
    )
    end_seconds: float | None | UnsetType = (
        UNSET  # Float (The optional end time of the marker (in seconds). Supports decimals.)
    )
    created_at: Time | None | UnsetType = UNSET  # Time!
    updated_at: Time | None | UnsetType = UNSET  # Time!

    # Field definitions with their conversion functions
    __field_conversions__ = {
        "title": str,
        "seconds": float,
        "end_seconds": float,
    }

    __relationships__ = {
        "scene": RelationshipMetadata(
            target_field="scene_id",
            is_list=False,
            query_field="scene",
            inverse_type="Scene",
            inverse_query_field="scene_markers",
            query_strategy="direct_field",
            notes="Backend auto-syncs scene_marker.scene and scene.scene_markers",
        ),
        "primary_tag": RelationshipMetadata(
            target_field="primary_tag_id",
            is_list=False,
            query_field="primary_tag",
            inverse_type="Tag",
            query_strategy="direct_field",
            notes="Primary tag for this scene marker",
        ),
        "tags": RelationshipMetadata(
            target_field="tag_ids",
            is_list=True,
            query_field="tags",
            inverse_type="Tag",
            query_strategy="direct_field",
            notes="Backend auto-syncs scene_marker.tags and tag.scene_markers",
        ),
    }


class FindSceneMarkersResultType(StashResult):
    """Result type for finding scene markers from schema/types/scene-marker.graphql."""

    count: int | None | UnsetType = UNSET  # Int!
    scene_markers: list[SceneMarker] | None | UnsetType = UNSET  # [SceneMarker!]!


class MarkerStringsResultType(StashResult):
    """Result type for marker strings from schema/types/scene-marker.graphql."""

    count: int | None | UnsetType = UNSET  # Int!
    id: str  # ID!
    title: str | None | UnsetType = UNSET  # String!
