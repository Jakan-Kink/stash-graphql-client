"""Integration tests for studio mixin functionality.

Tests studio operations against a real Stash instance.
"""

import pytest

from stash_graphql_client import StashClient
from tests.fixtures import capture_graphql_calls


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_studios_returns_results(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding studios returns results (may be empty)."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        result = await stash_client.find_studios()

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_studios"
        assert "findStudios" in calls[0]["query"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Result should be valid even if empty
        assert result.count >= 0
        assert isinstance(result.studios, list)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_studios_with_pagination(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test studio pagination works correctly."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        result = await stash_client.find_studios(filter_={"per_page": 10, "page": 1})

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_studios"
        assert "findStudios" in calls[0]["query"]
        assert calls[0]["variables"]["filter"]["per_page"] == 10
        assert calls[0]["variables"]["filter"]["page"] == 1
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify response
        assert len(result.studios) <= 10


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_nonexistent_studio_returns_none(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding a nonexistent studio returns None."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        studio = await stash_client.find_studio("99999999")

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_studio"
        assert "findStudio" in calls[0]["query"]
        assert calls[0]["variables"]["id"] == "99999999"
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify response
        assert studio is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_studios_with_q_parameter(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding studios using q search parameter."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        result = await stash_client.find_studios(q="test")

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_studios"
        assert "findStudios" in calls[0]["query"]
        assert calls[0]["variables"]["filter"]["q"] == "test"
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Should return valid result (may or may not have matches)
        assert result.count >= 0
        assert isinstance(result.studios, list)
