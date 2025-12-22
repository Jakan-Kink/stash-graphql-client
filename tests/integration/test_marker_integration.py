"""Integration tests for marker mixin functionality.

Tests scene marker operations against a real Stash instance.
"""

import pytest

from stash_graphql_client import StashClient
from tests.fixtures import capture_graphql_calls


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_markers_returns_results(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding markers returns results (may be empty)."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        result = await stash_client.find_markers()

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_markers"
        assert "findSceneMarkers" in calls[0]["query"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Result should be valid even if empty
        assert result.count >= 0
        assert isinstance(result.scene_markers, list)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_markers_with_pagination(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test marker pagination works correctly."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        result = await stash_client.find_markers(filter_={"per_page": 10, "page": 1})

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_markers"
        assert "findSceneMarkers" in calls[0]["query"]
        assert calls[0]["variables"]["filter"]["per_page"] == 10
        assert calls[0]["variables"]["filter"]["page"] == 1
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify response
        assert len(result.scene_markers) <= 10


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_nonexistent_marker_returns_none(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding a nonexistent marker returns None.

    When querying a nonexistent marker, Stash returns a GraphQL error:
    "scene marker with id 99999999 not found"
    The client catches this error and returns None.
    """
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        marker = await stash_client.find_marker("99999999")

        # Verify GraphQL call was made
        assert len(calls) == 1, "Expected 1 GraphQL call for find_marker"
        # Fixed in v0.5.0b6: now uses findSceneMarkers (plural) with IDs filter
        assert "findSceneMarkers" in calls[0]["query"]
        # Query wraps $id in array: ids: [$id], but variables just pass id: "..."
        assert calls[0]["variables"]["id"] == "99999999"
        # GraphQL error returned: "scene marker with id 99999999 not found"
        # This gets caught as an exception
        assert calls[0]["exception"] is not None
        assert "99999999 not found" in str(calls[0]["exception"])

        # Verify response (exception caught, None returned)
        assert marker is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_scene_marker_tags_for_scene(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test getting marker tags for a scene."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        # First get a scene
        scenes = await stash_client.find_scenes(filter_={"per_page": 1})
        if scenes.count == 0:
            pytest.skip("No scenes in test Stash instance")

        scene_id = scenes.scenes[0].id

        # Clear calls from find_scenes
        calls.clear()

        # Get marker tags
        marker_tags = await stash_client.scene_marker_tags(scene_id)

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for scene_marker_tags"
        assert "sceneMarkerTags" in calls[0]["query"]
        assert calls[0]["variables"]["scene_id"] == scene_id
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify response
        assert isinstance(marker_tags, list)
