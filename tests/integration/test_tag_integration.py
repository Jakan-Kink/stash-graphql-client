"""Integration tests for tag mixin functionality.

Tests tag operations against a real Stash instance.
"""

import pytest

from stash_graphql_client import StashClient


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_tags_returns_results(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding tags returns results (may be empty)."""
    async with stash_cleanup_tracker(stash_client, auto_capture=False):
        result = await stash_client.find_tags()

        # Result should be valid even if empty
        assert result.count >= 0
        assert isinstance(result.tags, list)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_tags_with_pagination(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test tag pagination works correctly."""
    async with stash_cleanup_tracker(stash_client, auto_capture=False):
        result = await stash_client.find_tags(filter_={"per_page": 10, "page": 1})

        assert len(result.tags) <= 10


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_nonexistent_tag_returns_none(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding a nonexistent tag returns None."""
    async with stash_cleanup_tracker(stash_client, auto_capture=False):
        tag = await stash_client.find_tag("99999999")

        assert tag is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_tags_with_q_parameter(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding tags using q search parameter."""
    async with stash_cleanup_tracker(stash_client, auto_capture=False):
        result = await stash_client.find_tags(q="test")

        # Should return valid result (may or may not have matches)
        assert result.count >= 0
        assert isinstance(result.tags, list)
