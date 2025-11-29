"""Logging types from schema/types/logging.graphql."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class LogLevel(str, Enum):
    """Log level enum from schema/types/logging.graphql."""

    TRACE = "Trace"
    DEBUG = "Debug"
    INFO = "Info"
    PROGRESS = "Progress"
    WARNING = "Warning"
    ERROR = "Error"


class LogEntry(BaseModel):
    """Log entry type from schema/types/logging.graphql."""

    time: datetime  # Time!
    level: LogLevel  # LogLevel!
    message: str  # String!
