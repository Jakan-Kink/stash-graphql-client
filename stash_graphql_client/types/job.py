"""Job types from schema/types/job.graphql."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class JobStatus(str, Enum):
    """Job status enum from schema/types/job.graphql."""

    READY = "READY"
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"
    STOPPING = "STOPPING"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class JobStatusUpdateType(str, Enum):
    """Job status update type enum from schema/types/job.graphql."""

    ADD = "ADD"
    REMOVE = "REMOVE"
    UPDATE = "UPDATE"


class FindJobInput(BaseModel):
    """Input for finding jobs from schema/types/job.graphql."""

    id: str  # ID!


class Job(BaseModel):
    """Job type from schema/types/job.graphql."""

    id: str  # ID!
    status: JobStatus  # JobStatus!
    subTasks: list[str]  # [String!]
    description: str  # String!
    progress: float | None = None  # Float
    startTime: datetime | None = None  # Time
    endTime: datetime | None = None  # Time
    addTime: datetime  # Time!
    error: str | None = None  # String


class JobStatusUpdate(BaseModel):
    """Job status update type from schema/types/job.graphql."""

    type: JobStatusUpdateType  # JobStatusUpdateType!
    job: Job  # Job!
