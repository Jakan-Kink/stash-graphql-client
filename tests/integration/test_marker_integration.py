"""Integration tests for marker mixin functionality.

Tests scene marker operations against a real Stash instance.
"""

import pytest

from stash_graphql_client import StashClient
from stash_graphql_client.types import BulkSceneMarkerUpdateInput, SceneMarker, Tag
from stash_graphql_client.types.unset import is_set
from tests.fixtures import capture_graphql_calls, dump_graphql_calls


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
        try:
            result = await stash_client.find_markers()
        finally:
            dump_graphql_calls(calls)

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_markers"
        assert "findSceneMarkers" in calls[0]["query"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Result should be valid even if empty
        assert is_set(result.count)
        assert result.count is not None
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
        try:
            result = await stash_client.find_markers(
                filter_={"per_page": 10, "page": 1}
            )
        finally:
            dump_graphql_calls(calls)

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_markers"
        assert "findSceneMarkers" in calls[0]["query"]
        assert calls[0]["variables"]["filter"]["per_page"] == 10
        assert calls[0]["variables"]["filter"]["page"] == 1
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify response
        assert is_set(result.scene_markers)
        assert result.scene_markers is not None
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
        try:
            marker = await stash_client.find_marker("99999999")
        finally:
            dump_graphql_calls(calls)

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
        try:
            scenes = await stash_client.find_scenes(filter_={"per_page": 1})
        finally:
            dump_graphql_calls(calls, "find_scenes")
        if scenes.count == 0:
            pytest.skip("No scenes in test Stash instance")

        assert is_set(scenes.scenes)
        scene_id = scenes.scenes[0].id

        # Clear calls from find_scenes
        calls.clear()

        # Get marker tags
        try:
            marker_tags = await stash_client.scene_marker_tags(scene_id)
        finally:
            dump_graphql_calls(calls, "scene_marker_tags")

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for scene_marker_tags"
        assert "sceneMarkerTags" in calls[0]["query"]
        assert calls[0]["variables"]["scene_id"] == scene_id
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify response
        assert isinstance(marker_tags, list)


# =============================================================================
# Marker mutation lifecycle tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_scenes
@pytest.mark.xdist_group(name="marker_mutations")
async def test_create_update_destroy_marker(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test full marker lifecycle: create, update, destroy."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        # Find an existing scene to attach the marker to
        try:
            scenes = await stash_client.find_scenes(filter_={"per_page": 1})
        finally:
            dump_graphql_calls(calls, "find_scenes")
        if scenes.count == 0:
            pytest.skip("No scenes in test Stash instance")

        assert is_set(scenes.scenes)
        scene = scenes.scenes[0]
        calls.clear()

        # Create a tag for the primary_tag (required field on SceneMarker)
        try:
            tag = await stash_client.create_tag(Tag(name="SGC Inttest Marker Tag"))
        finally:
            dump_graphql_calls(calls, "create_tag")
        cleanup["tags"].append(tag.id)
        assert tag.id is not None

        # Create the marker
        try:
            marker = await stash_client.create_marker(
                SceneMarker(
                    title="SGC Inttest Marker",
                    seconds=10.0,
                    scene=scene,
                    primary_tag=tag,
                )
            )
        finally:
            dump_graphql_calls(calls, "create_marker")
        cleanup["markers"].append(marker.id)
        assert marker.id is not None
        assert is_set(marker.title)
        assert marker.title == "SGC Inttest Marker"

        calls.clear()

        # Update the marker
        marker.title = "SGC Inttest Marker Updated"
        try:
            updated = await stash_client.update_marker(marker)
        finally:
            dump_graphql_calls(calls, "update_marker")

        assert len(calls) == 1, "Expected 1 GraphQL call for update_marker"
        assert "sceneMarkerUpdate" in calls[0]["query"]
        assert calls[0]["exception"] is None

        assert updated.id == marker.id
        assert is_set(updated.title)
        assert updated.title == "SGC Inttest Marker Updated"

        calls.clear()

        # Destroy the marker
        try:
            result = await stash_client.scene_marker_destroy(marker.id)
        finally:
            dump_graphql_calls(calls, "scene_marker_destroy")

        assert len(calls) == 1, "Expected 1 GraphQL call for scene_marker_destroy"
        assert "sceneMarkerDestroy" in calls[0]["query"]
        assert calls[0]["exception"] is None
        assert result is True

        cleanup["markers"].remove(marker.id)


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_scenes
@pytest.mark.xdist_group(name="marker_mutations")
async def test_bulk_scene_marker_update(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test bulk updating multiple scene markers' primary tag in a single call.

    Requires has_bulk_scene_marker_update capability (bulkSceneMarkerUpdate mutation).
    Requires at least one scene in the Stash instance.
    """
    if not stash_client._capabilities.has_mutation("bulkSceneMarkerUpdate"):
        pytest.skip("Server does not support bulkSceneMarkerUpdate")

    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        # Find an existing scene to attach markers to
        try:
            scenes = await stash_client.find_scenes(filter_={"per_page": 1})
        finally:
            dump_graphql_calls(calls, "find_scenes")
        if scenes.count == 0:
            pytest.skip("No scenes in test Stash instance")

        assert is_set(scenes.scenes)
        scene = scenes.scenes[0]
        calls.clear()

        # Create two tags: one as initial primary_tag, one as the bulk-update target
        try:
            tag_initial = await stash_client.create_tag(
                Tag(name="SGC Inttest Bulk Marker Tag A")
            )
        finally:
            dump_graphql_calls(calls, "create_tag")
        try:
            tag_target = await stash_client.create_tag(
                Tag(name="SGC Inttest Bulk Marker Tag B")
            )
        finally:
            dump_graphql_calls(calls, "create_tag")
        cleanup["tags"].append(tag_initial.id)
        cleanup["tags"].append(tag_target.id)
        assert tag_initial.id is not None
        assert tag_target.id is not None

        # Create two markers on the existing scene
        try:
            marker_a = await stash_client.create_marker(
                SceneMarker(
                    title="SGC Inttest Bulk Marker A",
                    seconds=1.0,
                    scene=scene,
                    primary_tag=tag_initial,
                )
            )
        finally:
            dump_graphql_calls(calls, "create_marker")
        try:
            marker_b = await stash_client.create_marker(
                SceneMarker(
                    title="SGC Inttest Bulk Marker B",
                    seconds=2.0,
                    scene=scene,
                    primary_tag=tag_initial,
                )
            )
        finally:
            dump_graphql_calls(calls, "create_marker")
        cleanup["markers"].append(marker_a.id)
        cleanup["markers"].append(marker_b.id)
        assert marker_a.id is not None
        assert marker_b.id is not None

        calls.clear()

        # Bulk update both markers to use tag_target as primary_tag
        try:
            updated_markers = await stash_client.bulk_scene_marker_update(
                BulkSceneMarkerUpdateInput(
                    ids=[marker_a.id, marker_b.id],
                    primary_tag_id=tag_target.id,
                )
            )
        finally:
            dump_graphql_calls(calls, "bulk_scene_marker_update")

        assert len(calls) == 1, "Expected 1 GraphQL call for bulk_scene_marker_update"
        assert "bulkSceneMarkerUpdate" in calls[0]["query"]
        assert calls[0]["exception"] is None

        assert len(updated_markers) == 2
        for m in updated_markers:
            assert is_set(m.primary_tag)
            assert m.primary_tag is not None
            assert m.primary_tag.id == tag_target.id
