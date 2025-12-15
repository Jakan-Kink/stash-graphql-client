"""Integration tests for performer mixin functionality.

Tests performer operations against a real Stash instance.
"""

import pytest

from stash_graphql_client import StashClient


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_performers_returns_results(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding performers returns results (may be empty)."""
    async with stash_cleanup_tracker(stash_client, auto_capture=False):
        result = await stash_client.find_performers()

        # Result should be valid even if empty
        assert result.count >= 0
        assert isinstance(result.performers, list)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_performers_with_pagination(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test performer pagination works correctly."""
    async with stash_cleanup_tracker(stash_client, auto_capture=False):
        result = await stash_client.find_performers(filter_={"per_page": 10, "page": 1})

        assert len(result.performers) <= 10


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_nonexistent_performer_returns_none(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding a nonexistent performer returns None."""
    async with stash_cleanup_tracker(stash_client, auto_capture=False):
        performer = await stash_client.find_performer("99999999")

        assert performer is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_performer_by_name_filter(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding performer using name filter."""
    async with stash_cleanup_tracker(stash_client, auto_capture=False):
        # Search for a performer that likely doesn't exist
        result = await stash_client.find_performers(
            performer_filter={
                "name": {"value": "NonexistentPerformer12345", "modifier": "EQUALS"}
            }
        )

        assert result.count == 0
        assert len(result.performers) == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_performers_with_q_parameter(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding performers using q search parameter."""
    async with stash_cleanup_tracker(stash_client, auto_capture=False):
        result = await stash_client.find_performers(q="test")

        # Should return valid result (may or may not have matches)
        assert result.count >= 0
        assert isinstance(result.performers, list)
