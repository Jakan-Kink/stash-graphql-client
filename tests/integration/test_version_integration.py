"""Integration tests for version mixin functionality.

Tests version queries against a real Stash instance.
Note: latestversion tests are mocked to avoid external GitHub API calls.
"""

import httpx
import pytest
import respx

from stash_graphql_client import StashClient
from stash_graphql_client.types import LatestVersion, Version
from stash_graphql_client.types.unset import is_set
from tests.fixtures import capture_graphql_calls


@pytest.mark.integration
@pytest.mark.asyncio
async def test_version_returns_current_version(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test getting current Stash version information."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        version = await stash_client.version()

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for version"
        assert "version" in calls[0]["query"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify response type
        assert version is not None
        assert isinstance(version, Version)

        # Verify required fields are present and non-empty
        assert version.version is not None
        assert is_set(version.version)
        assert len(version.version) > 0
        assert version.hash is not None
        assert is_set(version.hash)
        assert len(version.hash) > 0
        assert version.build_time is not None
        assert is_set(version.build_time)
        assert len(version.build_time) > 0

        # Version should follow semantic versioning pattern (v0.0.0 or similar)
        assert version.version.startswith("v") or version.version[0].isdigit()


@pytest.mark.integration
@pytest.mark.asyncio
@respx.mock
async def test_latestversion_returns_github_version(
    respx_mock, stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test getting latest available Stash version from GitHub (mocked)."""
    # Mock the GraphQL response to avoid external GitHub API calls
    mock_response = {
        "data": {
            "latestversion": {
                "version": "v0.26.2",
                "shorthash": "abc123def",
                "release_date": "2024-01-15",
                "url": "https://github.com/stashapp/stash/releases/tag/v0.26.2",
            }
        }
    }

    respx.post("http://localhost:9999/graphql").mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        latest = await stash_client.latestversion()

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for latestversion"
        assert "latestversion" in calls[0]["query"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify response type
        assert latest is not None
        assert isinstance(latest, LatestVersion)

        # Verify required fields are present and non-empty
        assert is_set(latest.version)
        assert latest.version == "v0.26.2"
        assert is_set(latest.shorthash)
        assert latest.shorthash == "abc123def"
        assert is_set(latest.release_date)
        assert latest.release_date == "2024-01-15"
        assert is_set(latest.url)
        assert latest.url == "https://github.com/stashapp/stash/releases/tag/v0.26.2"

        # URL should be a valid GitHub release URL
        assert "github.com" in latest.url.lower()
        assert "stashapp/stash" in latest.url.lower()

        # Version should follow semantic versioning
        assert latest.version.startswith("v")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_version_and_latestversion_compatibility(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test that current and latest version can be compared (latestversion mocked)."""
    # Get real version first, then mock latestversion to avoid external GitHub API calls
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        # Get real version from Stash
        current = await stash_client.version()

        # Mock the latestversion response to avoid external GitHub API calls
        mock_latest_response = {
            "data": {
                "latestversion": {
                    "version": "v0.26.2",
                    "shorthash": "abc123def",
                    "release_date": "2024-01-15",
                    "url": "https://github.com/stashapp/stash/releases/tag/v0.26.2",
                }
            }
        }

        with respx.mock:
            respx.post("http://localhost:9999/graphql").mock(
                return_value=httpx.Response(200, json=mock_latest_response)
            )
            latest = await stash_client.latestversion()

        # Verify GraphQL calls (2 calls total)
        assert len(calls) == 2, "Expected 2 GraphQL calls (version + latestversion)"
        assert "version" in calls[0]["query"]
        assert "latestversion" in calls[1]["query"]
        assert calls[0]["result"] is not None
        assert calls[1]["result"] is not None
        assert calls[0]["exception"] is None
        assert calls[1]["exception"] is None

        # Both should return valid version strings that can be compared
        assert current.version is not None
        assert is_set(current.version)
        assert is_set(latest.version)

        # Both should have version info in similar format
        # (both start with 'v' or both are numeric)
        current_starts_with_v = current.version.startswith("v")
        latest_starts_with_v = latest.version.startswith("v")

        # They should follow the same versioning scheme
        assert current_starts_with_v == latest_starts_with_v
