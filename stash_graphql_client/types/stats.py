"""Statistics types from schema/types/stats.graphql."""

from __future__ import annotations

from pydantic import Field

from .base import StashResult
from .unset import UNSET, UnsetType


class StatsResultType(StashResult):
    """Statistics result type from schema/types/stats.graphql."""

    scene_count: int | None | UnsetType = Field(default=UNSET, ge=0)  # Int!
    scenes_size: float | None | UnsetType = UNSET  # Float!
    scenes_duration: float | None | UnsetType = UNSET  # Float!
    image_count: int | None | UnsetType = Field(default=UNSET, ge=0)  # Int!
    images_size: float | None | UnsetType = UNSET  # Float!
    gallery_count: int | None | UnsetType = Field(default=UNSET, ge=0)  # Int!
    performer_count: int | None | UnsetType = Field(default=UNSET, ge=0)  # Int!
    studio_count: int | None | UnsetType = Field(default=UNSET, ge=0)  # Int!
    group_count: int | None | UnsetType = Field(default=UNSET, ge=0)  # Int!
    tag_count: int | None | UnsetType = Field(default=UNSET, ge=0)  # Int!
    total_o_count: int | None | UnsetType = Field(default=UNSET, ge=0)  # Int!
    total_play_duration: float | None | UnsetType = UNSET  # Float!
    total_play_count: int | None | UnsetType = Field(default=UNSET, ge=0)  # Int!
    scenes_played: int | None | UnsetType = Field(default=UNSET, ge=0)  # Int!
