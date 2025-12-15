"""Scalar types from schema/types/scalars.graphql."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

from pydantic import BeforeValidator, PlainSerializer

from stash_graphql_client.errors import StashIntegrationError


# Type aliases for simple scalars
Map = dict[str, Any]
BoolMap = dict[str, bool]
PluginConfigMap = dict[str, dict[str, Any]]
Int64 = int

# Any scalar - uses typing.Any (already imported)
# The GraphQL 'Any' scalar is mapped directly to Python's typing.Any

# Upload scalar - represents a multipart file upload
# In practice, this is handled by the HTTP transport layer and client code
# For type hints, we use Any since the actual type depends on the HTTP library
Upload = Any


def _parse_time(value: Any) -> datetime:
    """Parse Time scalar from string or return datetime directly.

    Args:
        value: String or datetime to parse

    Returns:
        Parsed datetime

    Raises:
        StashIntegrationError: If value is not a datetime or string
    """
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    raise StashIntegrationError(
        f"Time scalar: expected datetime or str, got {type(value).__name__}"
    )


def _serialize_time(value: datetime) -> str:
    """Serialize Time scalar to ISO format string.

    Args:
        value: Datetime to serialize

    Returns:
        ISO format string

    Raises:
        StashIntegrationError: If value is not a datetime
    """
    if isinstance(value, datetime):
        return value.isoformat()
    raise StashIntegrationError(
        f"Time scalar: expected datetime for serialization, got {type(value).__name__}"
    )


# Time scalar type - An RFC3339 timestamp
Time = Annotated[
    datetime,
    BeforeValidator(_parse_time),
    PlainSerializer(_serialize_time, return_type=str),
]


def _parse_timestamp_value(value: Any) -> datetime:
    """Parse Timestamp scalar from string or return datetime directly.

    Args:
        value: String or datetime to parse. Can be:
            - RFC3339 string (e.g., "2023-12-31T23:59:59Z")
            - Relative time in past (e.g., "<4h" for 4 hours ago)
            - Relative time in future (e.g., ">5m" for 5 minutes from now)
            - datetime object

    Returns:
        Parsed datetime

    Raises:
        StashIntegrationError: If value is not a datetime or string
    """
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return _parse_timestamp(value)
    raise StashIntegrationError(
        f"Timestamp scalar: expected datetime or str, got {type(value).__name__}"
    )


def _serialize_timestamp(value: datetime) -> str:
    """Serialize Timestamp scalar to ISO format string.

    Args:
        value: Datetime to serialize

    Returns:
        ISO format string

    Raises:
        StashIntegrationError: If value is not a datetime
    """
    if isinstance(value, datetime):
        return value.isoformat()
    raise StashIntegrationError(
        f"Timestamp scalar: expected datetime for serialization, got {type(value).__name__}"
    )


# Timestamp scalar type - RFC3339 string or relative time
Timestamp = Annotated[
    datetime,
    BeforeValidator(_parse_timestamp_value),
    PlainSerializer(_serialize_timestamp, return_type=str),
]


def _parse_timestamp(value: str) -> datetime:
    """Parse timestamp from string.

    Args:
        value: String to parse. Can be:
            - RFC3339 string (e.g., "2023-12-31T23:59:59Z")
            - Relative time in past (e.g., "<4h" for 4 hours ago)
            - Relative time in future (e.g., ">5m" for 5 minutes from now)

    Returns:
        Parsed datetime
    """
    # Handle relative times
    if value.startswith(("<", ">")):
        direction = -1 if value.startswith("<") else 1
        amount = value[1:-1]  # Remove direction and unit
        unit = value[-1]  # Get unit (h/m)

        # Convert to seconds
        if unit == "h":
            seconds = int(amount) * 3600
        elif unit == "m":
            seconds = int(amount) * 60
        else:
            raise ValueError(
                f"Invalid time unit: {unit}. Only 'h' (hours) and 'm' (minutes) are supported."
            )

        # Add/subtract from now
        return datetime.now(UTC) + timedelta(seconds=direction * seconds)

    # Handle RFC3339 string
    return datetime.fromisoformat(value)
