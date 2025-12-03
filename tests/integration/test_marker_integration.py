"""Integration tests for marker mixin functionality.

Tests scene marker operations against a real Stash instance.
"""

import pytest

from stash_graphql_client import StashClient


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_markers_returns_results(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding markers returns results (may be empty)."""
    async with stash_cleanup_tracker(stash_client, auto_capture=False):
        result = await stash_client.find_markers()

        # Result should be valid even if empty
        assert result.count >= 0
        assert isinstance(result.scene_markers, list)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_markers_with_pagination(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test marker pagination works correctly."""
    async with stash_cleanup_tracker(stash_client, auto_capture=False):
        result = await stash_client.find_markers(filter_={"per_page": 10, "page": 1})

        assert len(result.scene_markers) <= 10


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_nonexistent_marker_returns_none(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding a nonexistent marker returns None."""
    async with stash_cleanup_tracker(stash_client, auto_capture=False):
        marker = await stash_client.find_marker("99999999")

        assert marker is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_scene_marker_tags_for_scene(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test getting marker tags for a scene."""
    async with stash_cleanup_tracker(stash_client, auto_capture=False):
        # First get a scene
        scenes = await stash_client.find_scenes(filter_={"per_page": 1})
        if scenes.count == 0:
            pytest.skip("No scenes in test Stash instance")

        scene_id = scenes.scenes[0].id
        marker_tags = await stash_client.scene_marker_tags(scene_id)

        # Should return a list (may be empty)
        assert isinstance(marker_tags, list)
