"""Unit tests for SceneClientMixin activity and counter mutation operations.

These tests cover the 8 newly implemented scene activity mutation functions:
- scene_add_o()
- scene_delete_o()
- scene_reset_o()
- scene_save_activity()
- scene_reset_activity()
- scene_add_play()
- scene_delete_play()
- scene_reset_play_count()

These tests mock at the HTTP boundary using respx, allowing real code execution
through the entire GraphQL client stack including serialization/deserialization.
"""

import json
from datetime import UTC, datetime

import httpx
import pytest
import respx
from pydantic import ValidationError

from stash_graphql_client import StashClient
from stash_graphql_client.errors import StashIntegrationError
from stash_graphql_client.types.unset import is_set
from tests.fixtures import create_graphql_response


# =============================================================================
# Scene O-Count Operations Tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_add_o_with_current_time(respx_stash_client: StashClient) -> None:
    """Test adding O-count entry with current time."""
    result_data = {
        "count": 1,
        "history": ["2024-01-15T10:30:00Z"],
    }

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("sceneAddO", result_data))
        ]
    )

    result = await respx_stash_client.scene_add_o("123")

    # Verify result
    assert result.count == 1
    assert is_set(result.history)
    assert len(result.history) == 1
    # history contains datetime objects, not strings
    expected_dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)
    assert result.history[0] == expected_dt

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "sceneAddO" in req["query"]
    assert req["variables"]["id"] == "123"
    assert req["variables"]["times"] is None


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_add_o_with_specific_times(respx_stash_client: StashClient) -> None:
    """Test adding O-count entry with specific timestamps."""
    result_data = {
        "count": 3,
        "history": [
            "2024-01-15T10:30:00Z",
            "2024-01-16T14:20:00Z",
            "2024-01-17T09:15:00Z",
        ],
    }

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("sceneAddO", result_data))
        ]
    )

    times = [
        datetime.fromisoformat("2024-01-15T10:30:00+00:00"),
        datetime.fromisoformat("2024-01-16T14:20:00+00:00"),
    ]
    result = await respx_stash_client.scene_add_o("123", times=times)

    # Verify result
    assert result.count == 3
    assert is_set(result.history)
    assert len(result.history) == 3

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "sceneAddO" in req["query"]
    assert req["variables"]["id"] == "123"
    # Times are serialized to ISO format strings
    assert req["variables"]["times"] == [t.isoformat() for t in times]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_add_o_with_datetime_times(respx_stash_client: StashClient) -> None:
    """Test adding O-count entry with datetime timestamps."""
    result_data = {
        "count": 1,
        "history": ["2024-01-15T10:30:00Z"],
    }

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("sceneAddO", result_data))
        ]
    )

    times = [datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)]
    await respx_stash_client.scene_add_o("123", times=times)

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["times"] == ["2024-01-15T10:30:00+00:00"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_add_o_error(respx_stash_client: StashClient) -> None:
    """Test scene_add_o error handling."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json={"errors": [{"message": "Failed to add O-count"}]})
        ]
    )

    with pytest.raises(Exception, match="Failed to add O-count"):
        await respx_stash_client.scene_add_o("123")

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_add_o_invalid_timestamp_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test scene_add_o rejects invalid timestamp strings."""
    with pytest.raises(ValidationError, match="Invalid time unit"):
        await respx_stash_client.scene_add_o("123", times=["<10s"])  # type: ignore[list-item]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_add_o_invalid_times_type_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test scene_add_o rejects non-list times values."""
    with pytest.raises(TypeError, match="times must be list\\[Timestamp\\] or None"):
        await respx_stash_client.scene_add_o("123", times="not-a-list")  # type: ignore[arg-type]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_delete_o_removes_last_entry(
    respx_stash_client: StashClient,
) -> None:
    """Test deleting last O-count entry."""
    result_data = {
        "count": 1,
        "history": ["2024-01-15T10:30:00Z"],
    }

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("sceneDeleteO", result_data)
            )
        ]
    )

    result = await respx_stash_client.scene_delete_o("123")

    # Verify result
    assert result.count == 1
    assert is_set(result.history)
    assert len(result.history) == 1

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "sceneDeleteO" in req["query"]
    assert req["variables"]["id"] == "123"
    assert req["variables"]["times"] is None


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_delete_o_with_specific_timestamp(
    respx_stash_client: StashClient,
) -> None:
    """Test deleting specific O-count timestamp."""
    result_data = {
        "count": 1,
        "history": ["2024-01-16T14:20:00Z"],
    }

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("sceneDeleteO", result_data)
            )
        ]
    )

    times = [datetime.fromisoformat("2024-01-15T10:30:00+00:00")]
    result = await respx_stash_client.scene_delete_o("123", times=times)

    # Verify result
    assert result.count == 1
    assert is_set(result.history)
    assert len(result.history) == 1

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "sceneDeleteO" in req["query"]
    assert req["variables"]["id"] == "123"
    # Times are serialized to ISO format strings
    assert req["variables"]["times"] == [t.isoformat() for t in times]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_delete_o_with_datetime_times(
    respx_stash_client: StashClient,
) -> None:
    """Test removing O-count entries with datetime timestamps."""
    result_data = {
        "count": 1,
        "history": ["2024-01-15T10:30:00Z"],
    }

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("sceneDeleteO", result_data)
            )
        ]
    )

    times = [datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)]
    await respx_stash_client.scene_delete_o("123", times=times)

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["times"] == ["2024-01-15T10:30:00+00:00"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_delete_o_error(respx_stash_client: StashClient) -> None:
    """Test scene_delete_o error handling."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json={"errors": [{"message": "Failed to delete O-count"}]}
            )
        ]
    )

    with pytest.raises(Exception, match="Failed to delete O-count"):
        await respx_stash_client.scene_delete_o("123")

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_delete_o_invalid_times_type_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test scene_delete_o rejects non-list times values."""
    with pytest.raises(TypeError, match="times must be list\\[Timestamp\\] or None"):
        await respx_stash_client.scene_delete_o("123", times="not-a-list")  # type: ignore[arg-type]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_delete_o_invalid_timestamp_type_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test scene_delete_o rejects non-str/datetime timestamp values."""
    with pytest.raises(StashIntegrationError, match="Timestamp scalar"):
        await respx_stash_client.scene_delete_o("123", times=[123])  # type: ignore[list-item]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_reset_o(respx_stash_client: StashClient) -> None:
    """Test resetting scene O-count to 0."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("sceneResetO", 0))
        ]
    )

    result = await respx_stash_client.scene_reset_o("123")

    # Verify result
    assert result == 0

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "sceneResetO" in req["query"]
    assert req["variables"]["id"] == "123"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_reset_o_error(respx_stash_client: StashClient) -> None:
    """Test scene_reset_o error handling."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json={"errors": [{"message": "Failed to reset O-count"}]}
            )
        ]
    )

    with pytest.raises(Exception, match="Failed to reset O-count"):
        await respx_stash_client.scene_reset_o("123")

    assert len(graphql_route.calls) == 1


# =============================================================================
# Scene Activity Tracking Tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_save_activity_resume_time(
    respx_stash_client: StashClient,
) -> None:
    """Test saving scene resume time."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("sceneSaveActivity", True))
        ]
    )

    result = await respx_stash_client.scene_save_activity("123", resume_time=120.5)

    # Verify result
    assert result is True

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "sceneSaveActivity" in req["query"]
    assert req["variables"]["id"] == "123"
    assert req["variables"]["resume_time"] == 120.5
    assert req["variables"]["playDuration"] is None


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_save_activity_play_duration(
    respx_stash_client: StashClient,
) -> None:
    """Test saving scene play duration."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("sceneSaveActivity", True))
        ]
    )

    result = await respx_stash_client.scene_save_activity("123", play_duration=300.0)

    # Verify result
    assert result is True

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "sceneSaveActivity" in req["query"]
    assert req["variables"]["id"] == "123"
    assert req["variables"]["resume_time"] is None
    assert req["variables"]["playDuration"] == 300.0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_save_activity_both_params(
    respx_stash_client: StashClient,
) -> None:
    """Test saving both resume time and play duration."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("sceneSaveActivity", True))
        ]
    )

    result = await respx_stash_client.scene_save_activity(
        "123", resume_time=120.5, play_duration=300.0
    )

    # Verify result
    assert result is True

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "sceneSaveActivity" in req["query"]
    assert req["variables"]["id"] == "123"
    assert req["variables"]["resume_time"] == 120.5
    assert req["variables"]["playDuration"] == 300.0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_save_activity_error(respx_stash_client: StashClient) -> None:
    """Test scene_save_activity error handling."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json={"errors": [{"message": "Failed to save activity"}]}
            )
        ]
    )

    with pytest.raises(Exception, match="Failed to save activity"):
        await respx_stash_client.scene_save_activity("123", resume_time=120.5)

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_reset_activity_resume_only(
    respx_stash_client: StashClient,
) -> None:
    """Test resetting scene resume time only."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("sceneResetActivity", True)
            )
        ]
    )

    result = await respx_stash_client.scene_reset_activity("123", reset_resume=True)

    # Verify result
    assert result is True

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "sceneResetActivity" in req["query"]
    assert req["variables"]["id"] == "123"
    assert req["variables"]["reset_resume"] is True
    assert req["variables"]["reset_duration"] is False


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_reset_activity_duration_only(
    respx_stash_client: StashClient,
) -> None:
    """Test resetting scene play duration only."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("sceneResetActivity", True)
            )
        ]
    )

    result = await respx_stash_client.scene_reset_activity("123", reset_duration=True)

    # Verify result
    assert result is True

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "sceneResetActivity" in req["query"]
    assert req["variables"]["id"] == "123"
    assert req["variables"]["reset_resume"] is False
    assert req["variables"]["reset_duration"] is True


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_reset_activity_both(respx_stash_client: StashClient) -> None:
    """Test resetting both resume time and play duration."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("sceneResetActivity", True)
            )
        ]
    )

    result = await respx_stash_client.scene_reset_activity(
        "123", reset_resume=True, reset_duration=True
    )

    # Verify result
    assert result is True

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "sceneResetActivity" in req["query"]
    assert req["variables"]["id"] == "123"
    assert req["variables"]["reset_resume"] is True
    assert req["variables"]["reset_duration"] is True


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_reset_activity_error(respx_stash_client: StashClient) -> None:
    """Test scene_reset_activity error handling."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json={"errors": [{"message": "Failed to reset activity"}]}
            )
        ]
    )

    with pytest.raises(Exception, match="Failed to reset activity"):
        await respx_stash_client.scene_reset_activity("123", reset_resume=True)

    assert len(graphql_route.calls) == 1


# =============================================================================
# Scene Play Count Operations Tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_add_play_with_current_time(
    respx_stash_client: StashClient,
) -> None:
    """Test adding play count entry with current time."""
    result_data = {
        "count": 1,
        "history": ["2024-01-15T10:30:00Z"],
    }

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("sceneAddPlay", result_data)
            )
        ]
    )

    result = await respx_stash_client.scene_add_play("123")

    # Verify result
    assert result.count == 1
    assert is_set(result.history)
    assert len(result.history) == 1
    # history contains datetime objects, not strings
    expected_dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)
    assert result.history[0] == expected_dt

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "sceneAddPlay" in req["query"]
    assert req["variables"]["id"] == "123"
    assert req["variables"]["times"] is None


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_add_play_with_specific_times(
    respx_stash_client: StashClient,
) -> None:
    """Test adding play count entry with specific timestamps."""
    result_data = {
        "count": 2,
        "history": ["2024-01-15T10:30:00Z", "2024-01-16T14:20:00Z"],
    }

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("sceneAddPlay", result_data)
            )
        ]
    )

    times = [datetime.fromisoformat("2024-01-15T10:30:00+00:00")]
    result = await respx_stash_client.scene_add_play("123", times=times)

    # Verify result
    assert result.count == 2
    assert is_set(result.history)
    assert len(result.history) == 2

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "sceneAddPlay" in req["query"]
    assert req["variables"]["id"] == "123"
    # Times are serialized to ISO format strings
    assert req["variables"]["times"] == [t.isoformat() for t in times]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_add_play_error(respx_stash_client: StashClient) -> None:
    """Test scene_add_play error handling."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json={"errors": [{"message": "Failed to add play count"}]}
            )
        ]
    )

    with pytest.raises(Exception, match="Failed to add play count"):
        await respx_stash_client.scene_add_play("123")

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_delete_play_removes_last_entry(
    respx_stash_client: StashClient,
) -> None:
    """Test deleting last play count entry."""
    result_data = {
        "count": 1,
        "history": ["2024-01-15T10:30:00Z"],
    }

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("sceneDeletePlay", result_data)
            )
        ]
    )

    result = await respx_stash_client.scene_delete_play("123")

    # Verify result
    assert result.count == 1
    assert is_set(result.history)
    assert len(result.history) == 1

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "sceneDeletePlay" in req["query"]
    assert req["variables"]["id"] == "123"
    assert req["variables"]["times"] is None


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_delete_play_with_specific_timestamp(
    respx_stash_client: StashClient,
) -> None:
    """Test deleting specific play count timestamp."""
    result_data = {
        "count": 0,
        "history": [],
    }

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("sceneDeletePlay", result_data)
            )
        ]
    )

    times = [datetime.fromisoformat("2024-01-15T10:30:00+00:00")]
    result = await respx_stash_client.scene_delete_play("123", times=times)

    # Verify result
    assert result.count == 0
    assert is_set(result.history)
    assert len(result.history) == 0

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "sceneDeletePlay" in req["query"]
    assert req["variables"]["id"] == "123"
    # Times are serialized to ISO format strings
    assert req["variables"]["times"] == [t.isoformat() for t in times]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_delete_play_error(respx_stash_client: StashClient) -> None:
    """Test scene_delete_play error handling."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json={"errors": [{"message": "Failed to delete play count"}]}
            )
        ]
    )

    with pytest.raises(Exception, match="Failed to delete play count"):
        await respx_stash_client.scene_delete_play("123")

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_reset_play_count(respx_stash_client: StashClient) -> None:
    """Test resetting scene play count to 0."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("sceneResetPlayCount", 0))
        ]
    )

    result = await respx_stash_client.scene_reset_play_count("123")

    # Verify result
    assert result == 0

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "sceneResetPlayCount" in req["query"]
    assert req["variables"]["id"] == "123"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_reset_play_count_error(respx_stash_client: StashClient) -> None:
    """Test scene_reset_play_count error handling."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json={"errors": [{"message": "Failed to reset play count"}]}
            )
        ]
    )

    with pytest.raises(Exception, match="Failed to reset play count"):
        await respx_stash_client.scene_reset_play_count("123")

    assert len(graphql_route.calls) == 1
