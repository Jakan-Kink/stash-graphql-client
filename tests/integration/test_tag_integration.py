"""Integration tests for tag mixin functionality.

Tests tag operations against a real Stash instance.
"""

import pytest

from stash_graphql_client import StashClient
from tests.fixtures import capture_graphql_calls


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_tags_returns_results(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding tags returns results (may be empty)."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        result = await stash_client.find_tags()

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_tags"
        assert "findTags" in calls[0]["query"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Result should be valid even if empty
        assert result.count >= 0
        assert isinstance(result.tags, list)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_tags_with_pagination(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test tag pagination works correctly."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        result = await stash_client.find_tags(filter_={"per_page": 10, "page": 1})

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_tags"
        assert "findTags" in calls[0]["query"]
        assert calls[0]["variables"]["filter"]["per_page"] == 10
        assert calls[0]["variables"]["filter"]["page"] == 1
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify response
        assert len(result.tags) <= 10


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_nonexistent_tag_returns_none(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding a nonexistent tag returns None."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        tag = await stash_client.find_tag("99999999")

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_tag"
        assert "findTag" in calls[0]["query"]
        assert calls[0]["variables"]["id"] == "99999999"
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify response
        assert tag is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_tags_with_q_parameter(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding tags using q search parameter."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        result = await stash_client.find_tags(q="test")

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_tags"
        assert "findTags" in calls[0]["query"]
        # q parameter is added to filter dict
        assert calls[0]["variables"]["filter"]["q"] == "test"
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Should return valid result (may or may not have matches)
        assert result.count >= 0
        assert isinstance(result.tags, list)
