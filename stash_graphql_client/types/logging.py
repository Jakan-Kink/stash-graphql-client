"""Logging types from schema/types/logging.graphql."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel

from .scalars import Time
from .unset import UNSET, UnsetType


class LogLevel(StrEnum):
    """Log level enum from schema/types/logging.graphql."""

    TRACE = "Trace"
    DEBUG = "Debug"
    INFO = "Info"
    PROGRESS = "Progress"
    WARNING = "Warning"
    ERROR = "Error"


class LogEntry(BaseModel):
    """Log entry type from schema/types/logging.graphql."""

    time: Time | None | UnsetType = UNSET  # Time!
    level: LogLevel | None | UnsetType = UNSET  # LogLevel!
    message: str | None | UnsetType = UNSET  # String!
