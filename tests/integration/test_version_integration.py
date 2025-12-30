"""Integration tests for version mixin functionality.

Tests version queries against a real Stash instance.
"""

import pytest

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
async def test_latestversion_returns_github_version(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test getting latest available Stash version from GitHub."""
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
        assert len(latest.version) > 0
        assert is_set(latest.shorthash)
        assert len(latest.shorthash) > 0
        assert is_set(latest.release_date)
        assert len(latest.release_date) > 0
        assert is_set(latest.url)
        assert len(latest.url) > 0

        # URL should be a valid GitHub release URL
        assert "github.com" in latest.url.lower()
        assert "stashapp/stash" in latest.url.lower()

        # Version should follow semantic versioning
        assert latest.version.startswith("v") or latest.version[0].isdigit()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_version_and_latestversion_compatibility(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test that current and latest version can be compared."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        current = await stash_client.version()
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
