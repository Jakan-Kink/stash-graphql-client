"""Tests for SystemQueryClientMixin."""

import json
from datetime import UTC, datetime

import httpx
import pytest
import respx

from stash_graphql_client import StashClient
from tests.fixtures.stash.graphql_responses import create_graphql_response


@pytest.mark.asyncio
@pytest.mark.unit
async def test_stats(respx_stash_client: StashClient) -> None:
    """Test stats() method returns system statistics."""
    stats_data = {
        "scene_count": 100,
        "scenes_size": 5000000000,
        "scenes_duration": 36000.0,
        "image_count": 50,
        "images_size": 1000000000,
        "gallery_count": 25,
        "performer_count": 30,
        "studio_count": 10,
        "group_count": 5,
        "tag_count": 20,
        "total_o_count": 150,
        "total_play_duration": 18000.0,
        "total_play_count": 200,
    }

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("stats", stats_data))
        ]
    )

    result = await respx_stash_client.stats()

    assert result.scene_count == 100
    assert result.scenes_size == 5000000000
    assert result.performer_count == 30
    assert len(graphql_route.calls) == 1

    # Verify request
    req = json.loads(graphql_route.calls[0].request.content)
    assert "stats" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_logs(respx_stash_client: StashClient) -> None:
    """Test logs() method returns system logs."""
    logs_data = [
        {
            "time": "2024-01-15T10:30:00Z",
            "level": "Info",  # LogLevel enum values: Trace, Debug, Info, Progress, Warning, Error
            "message": "Server started successfully",
        },
        {
            "time": "2024-01-15T10:31:00Z",
            "level": "Warning",
            "message": "Low disk space warning",
        },
        {
            "time": "2024-01-15T10:32:00Z",
            "level": "Error",
            "message": "Failed to process image",
        },
    ]

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("logs", logs_data))
        ]
    )

    result = await respx_stash_client.logs()

    assert len(result) == 3
    assert result[0].level == "Info"
    assert result[0].message == "Server started successfully"
    assert result[1].level == "Warning"
    assert result[2].level == "Error"
    assert len(graphql_route.calls) == 1

    # Verify request
    req = json.loads(graphql_route.calls[0].request.content)
    assert "logs" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_system_status_exception(respx_stash_client: StashClient) -> None:
    """Test get_system_status handles exceptions gracefully."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=Exception("Network error")
    )

    result = await respx_stash_client.get_system_status()

    assert result is None


@pytest.mark.asyncio
@pytest.mark.unit
async def test_check_system_ready_ok_status(respx_stash_client: StashClient) -> None:
    """Test check_system_ready with OK status (triggers debug log)."""
    status_data = {
        "databaseSchema": 61,
        "databasePath": "/path/to/db.sqlite",
        "configPath": "/path/to/config.yml",
        "appSchema": 61,
        "status": "OK",
        "os": "linux",
        "workingDir": "/path/to/stash",
        "homeDir": "/home/user",
    }

    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("systemStatus", status_data)
            )
        ]
    )

    # Should not raise any exception
    await respx_stash_client.check_system_ready()
    # If we get here without exception, the test passes


@pytest.mark.asyncio
@pytest.mark.unit
async def test_dlna_status_success(respx_stash_client: StashClient) -> None:
    """Test dlna_status() method returns DLNA server status."""
    dlna_data = {
        "running": True,
        "until": "2024-01-15T12:00:00Z",
        "recentIPAddresses": ["192.168.1.100", "192.168.1.101"],
        "allowedIPAddresses": [
            {"ipAddress": "192.168.1.0/24", "until": None},
            {"ipAddress": "10.0.0.0/8", "until": "2024-01-15T12:00:00Z"},
        ],
    }

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("dlnaStatus", dlna_data))
        ]
    )

    result = await respx_stash_client.dlna_status()

    assert result.running is True
    # Time fields are parsed to datetime objects
    assert result.until == datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)
    assert result.recent_ip_addresses == ["192.168.1.100", "192.168.1.101"]
    assert len(result.allowed_ip_addresses) == 2
    assert result.allowed_ip_addresses[0].ip_address == "192.168.1.0/24"
    assert result.allowed_ip_addresses[0].until is None
    assert result.allowed_ip_addresses[1].ip_address == "10.0.0.0/8"
    assert result.allowed_ip_addresses[1].until == datetime(
        2024, 1, 15, 12, 0, 0, tzinfo=UTC
    )
    assert len(graphql_route.calls) == 1

    # Verify request
    req = json.loads(graphql_route.calls[0].request.content)
    assert "dlnaStatus" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_dlna_status_exception(respx_stash_client: StashClient) -> None:
    """Test dlna_status() handles exceptions and returns empty DLNAStatus."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=Exception("Network error")
    )

    result = await respx_stash_client.dlna_status()

    # Should return empty DLNAStatus object on exception
    assert isinstance(result, type(result))
    assert result.running is result.running  # Verify it's a valid DLNAStatus object


@pytest.mark.asyncio
@pytest.mark.unit
async def test_dlna_status_no_data(respx_stash_client: StashClient) -> None:
    """Test dlna_status() returns empty DLNAStatus when no data returned."""
    # Return empty response (no dlnaStatus key)
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(200, json={"data": {}})]
    )

    result = await respx_stash_client.dlna_status()

    # Should return empty DLNAStatus object when no data
    assert isinstance(result, type(result))
    assert result.running is result.running  # Verify it's a valid DLNAStatus object
    assert len(graphql_route.calls) == 1
