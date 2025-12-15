"""Tests for stash_graphql_client.types.scalars module.

Tests Time and Timestamp scalar parsing and serialization.
"""

from datetime import UTC, datetime

import pytest
from pydantic import BaseModel

from stash_graphql_client.errors import StashIntegrationError
from stash_graphql_client.types.scalars import (
    Time,
    Timestamp,
    _parse_time,
    _parse_timestamp,
)


@pytest.mark.unit
def test_parse_time_with_datetime() -> None:
    """Test _parse_time() with datetime input.

    This covers line 41 in scalars.py - return value when already datetime.
    """
    dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)
    result = _parse_time(dt)
    assert result == dt
    assert isinstance(result, datetime)


@pytest.mark.unit
def test_parse_time_with_string() -> None:
    """Test _parse_time() with ISO string input.

    This covers line 43 in scalars.py - parsing ISO string.
    """
    iso_string = "2024-01-15T10:30:00"
    result = _parse_time(iso_string)
    assert isinstance(result, datetime)
    assert result.year == 2024
    assert result.month == 1
    assert result.day == 15


@pytest.mark.unit
def test_parse_time_with_invalid_type() -> None:
    """Test _parse_time() raises error for invalid type.

    This covers line 44 in scalars.py - StashIntegrationError raise.
    """
    with pytest.raises(StashIntegrationError, match="expected datetime or str"):
        _parse_time(123)

    with pytest.raises(StashIntegrationError, match="expected datetime or str"):
        _parse_time(None)


@pytest.mark.unit
def test_time_scalar_in_pydantic() -> None:
    """Test Time scalar works in Pydantic models."""

    class TestModel(BaseModel):
        timestamp: Time

    # Test with string
    model1 = TestModel(timestamp="2024-01-15T10:30:00")
    assert isinstance(model1.timestamp, datetime)

    # Test with datetime
    dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)
    model2 = TestModel(timestamp=dt)
    assert model2.timestamp == dt


@pytest.mark.unit
def test_parse_timestamp_relative_past_hours() -> None:
    """Test _parse_timestamp() with relative past time in hours.

    This covers lines 141-148 in scalars.py - parsing "<4h" format.
    """
    result = _parse_timestamp("<4h")

    # Should be approximately 4 hours ago
    now = datetime.now(UTC)
    diff = now - result
    # Allow some margin for test execution time
    assert 3.99 * 3600 <= diff.total_seconds() <= 4.01 * 3600


@pytest.mark.unit
def test_parse_timestamp_relative_past_minutes() -> None:
    """Test _parse_timestamp() with relative past time in minutes.

    This covers lines 149-150 in scalars.py - parsing "<30m" format.
    """
    result = _parse_timestamp("<30m")

    # Should be approximately 30 minutes ago
    now = datetime.now(UTC)
    diff = now - result
    # Allow some margin
    assert 29.9 * 60 <= diff.total_seconds() <= 30.1 * 60


@pytest.mark.unit
def test_parse_timestamp_relative_future_hours() -> None:
    """Test _parse_timestamp() with relative future time in hours.

    This covers line 142 direction=1 and lines 147-148.
    """
    result = _parse_timestamp(">2h")

    # Should be approximately 2 hours from now
    now = datetime.now(UTC)
    diff = result - now
    # Allow some margin
    assert 1.99 * 3600 <= diff.total_seconds() <= 2.01 * 3600


@pytest.mark.unit
def test_parse_timestamp_relative_future_minutes() -> None:
    """Test _parse_timestamp() with relative future time in minutes.

    This covers line 142 direction=1 and lines 149-150.
    """
    result = _parse_timestamp(">15m")

    # Should be approximately 15 minutes from now
    now = datetime.now(UTC)
    diff = result - now
    # Allow some margin
    assert 14.9 * 60 <= diff.total_seconds() <= 15.1 * 60


@pytest.mark.unit
def test_parse_timestamp_invalid_unit() -> None:
    """Test _parse_timestamp() raises error for invalid unit.

    This covers lines 152-154 in scalars.py - ValueError for invalid unit.
    """
    with pytest.raises(ValueError, match="Invalid time unit"):
        _parse_timestamp("<5s")  # seconds not supported

    with pytest.raises(ValueError, match="Invalid time unit"):
        _parse_timestamp(">10d")  # days not supported


@pytest.mark.unit
def test_parse_timestamp_rfc3339_string() -> None:
    """Test _parse_timestamp() with RFC3339 string.

    This covers line 160 in scalars.py - parsing RFC3339 format.
    """
    iso_string = "2024-01-15T10:30:00"
    result = _parse_timestamp(iso_string)
    assert isinstance(result, datetime)
    assert result.year == 2024
    assert result.month == 1
    assert result.day == 15
    assert result.hour == 10
    assert result.minute == 30


@pytest.mark.unit
def test_timestamp_scalar_in_pydantic() -> None:
    """Test Timestamp scalar works in Pydantic models."""

    class TestModel(BaseModel):
        created: Timestamp

    # Test with RFC3339 string
    model1 = TestModel(created="2024-01-15T10:30:00")
    assert isinstance(model1.created, datetime)

    # Test with relative time
    model2 = TestModel(created="<1h")
    assert isinstance(model2.created, datetime)
    # Should be in the past
    assert model2.created < datetime.now(UTC)


@pytest.mark.unit
def test_serialize_timestamp_success() -> None:
    """Test timestamp serialization with valid datetime.

    This covers line 114 in scalars.py - return value.isoformat().
    """
    from stash_graphql_client.types.scalars import _serialize_timestamp

    dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)
    result = _serialize_timestamp(dt)

    assert isinstance(result, str)
    assert result == "2024-01-15T10:30:00+00:00"


@pytest.mark.unit
def test_serialize_timestamp_invalid_type() -> None:
    """Test timestamp serialization raises error for invalid type.

    This covers lines 115-117 in scalars.py - error in _serialize_timestamp.
    """
    from stash_graphql_client.types.scalars import _serialize_timestamp

    with pytest.raises(
        StashIntegrationError, match="expected datetime for serialization"
    ):
        _serialize_timestamp("not a datetime")

    with pytest.raises(
        StashIntegrationError, match="expected datetime for serialization"
    ):
        _serialize_timestamp(123)


@pytest.mark.unit
def test_parse_timestamp_value_with_datetime() -> None:
    """Test _parse_timestamp_value() with datetime input.

    This covers line 92-93 in scalars.py - return value when already datetime.
    """
    from stash_graphql_client.types.scalars import _parse_timestamp_value

    dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)
    result = _parse_timestamp_value(dt)
    assert result == dt


@pytest.mark.unit
def test_parse_timestamp_value_with_string() -> None:
    """Test _parse_timestamp_value() with string input.

    This covers lines 94-95 in scalars.py - parsing string.
    """
    from stash_graphql_client.types.scalars import _parse_timestamp_value

    result = _parse_timestamp_value("<2h")
    assert isinstance(result, datetime)
    # Should be in the past
    assert result < datetime.now(UTC)


@pytest.mark.unit
def test_parse_timestamp_value_invalid_type() -> None:
    """Test _parse_timestamp_value() raises error for invalid type.

    This covers lines 96-98 in scalars.py - StashIntegrationError raise.
    """
    from stash_graphql_client.types.scalars import _parse_timestamp_value

    with pytest.raises(StashIntegrationError, match="expected datetime or str"):
        _parse_timestamp_value(123)

    with pytest.raises(StashIntegrationError, match="expected datetime or str"):
        _parse_timestamp_value(None)
