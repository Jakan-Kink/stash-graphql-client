"""Integration tests for performer mixin functionality.

Tests performer operations against a real Stash instance.
"""

import pytest

from stash_graphql_client import StashClient
from stash_graphql_client.types.unset import is_set
from tests.fixtures import capture_graphql_calls


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_performers_returns_results(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding performers returns results (may be empty)."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        result = await stash_client.find_performers()

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_performers"
        assert "findPerformers" in calls[0]["query"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Result should be valid even if empty
        assert is_set(result.count)
        assert result.count >= 0
        assert isinstance(result.performers, list)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_performers_with_pagination(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test performer pagination works correctly."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        result = await stash_client.find_performers(filter_={"per_page": 10, "page": 1})

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_performers"
        assert "findPerformers" in calls[0]["query"]
        assert calls[0]["variables"]["filter"]["per_page"] == 10
        assert calls[0]["variables"]["filter"]["page"] == 1
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify response
        assert is_set(result.performers)
        assert len(result.performers) <= 10


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_nonexistent_performer_returns_none(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding a nonexistent performer returns None."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        performer = await stash_client.find_performer("99999999")

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_performer"
        assert "findPerformer" in calls[0]["query"]
        assert calls[0]["variables"]["id"] == "99999999"
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify response
        assert performer is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_performer_by_name_filter(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding performer using name filter."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        # Search for a performer that likely doesn't exist
        result = await stash_client.find_performers(
            performer_filter={
                "name": {"value": "NonexistentPerformer12345", "modifier": "EQUALS"}
            }
        )

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_performers"
        assert "findPerformers" in calls[0]["query"]
        assert "performer_filter" in calls[0]["variables"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify response
        assert result.count == 0
        assert is_set(result.performers)
        assert len(result.performers) == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_performers_with_q_parameter(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding performers using q search parameter."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        result = await stash_client.find_performers(q="test")

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_performers"
        assert "findPerformers" in calls[0]["query"]
        # q parameter is added to filter dict
        assert calls[0]["variables"]["filter"]["q"] == "test"
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Should return valid result (may or may not have matches)
        assert is_set(result.count)
        assert result.count >= 0
        assert isinstance(result.performers, list)
