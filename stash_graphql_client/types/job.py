"""Job types from schema/types/job.graphql."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from .base import FromGraphQLMixin, StashInput
from .scalars import Time
from .unset import UNSET, UnsetType


class JobStatus(str, Enum):
    """Job status enum from schema/types/job.graphql."""

    READY = "READY"
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"
    STOPPING = "STOPPING"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class Job(FromGraphQLMixin, BaseModel):
    """Job type from schema/types/job.graphql."""

    id: str | None | UnsetType = UNSET  # ID!
    status: JobStatus | None | UnsetType = UNSET  # JobStatus!
    sub_tasks: list[str] | None | UnsetType = Field(
        default=UNSET, alias="subTasks"
    )  # [String!]
    description: str | None | UnsetType = UNSET  # String!
    progress: float | None | UnsetType = UNSET  # Float
    start_time: Time | None | UnsetType = Field(
        default=UNSET, alias="startTime"
    )  # Time
    end_time: Time | None | UnsetType = Field(default=UNSET, alias="endTime")  # Time
    add_time: Time | None | UnsetType = Field(default=UNSET, alias="addTime")  # Time!
    error: str | None | UnsetType = UNSET  # String


class FindJobInput(StashInput):
    """Input for finding jobs from schema/types/job.graphql."""

    id: str  # ID!


class JobStatusUpdateType(str, Enum):
    """Job status update type enum from schema/types/job.graphql."""

    ADD = "ADD"
    REMOVE = "REMOVE"
    UPDATE = "UPDATE"


class JobStatusUpdate(FromGraphQLMixin, BaseModel):
    """Job status update type from schema/types/job.graphql."""

    type: JobStatusUpdateType  # JobStatusUpdateType!
    job: Job  # Job!
