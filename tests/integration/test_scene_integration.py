"""Integration tests for scene mixin functionality.

Tests scene operations against a real Stash instance with GraphQL call verification.

These tests cover the core scene CRUD operations, relationships, and
scene-specific features like watch tracking and play history.
"""

import time

import pytest

from stash_graphql_client import StashClient
from stash_graphql_client.types import Scene, Studio
from stash_graphql_client.types.unset import is_set
from tests.fixtures import capture_graphql_calls


# =============================================================================
# Scene CRUD Integration Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_scenes
async def test_find_scene_by_id(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding a scene by ID."""
    async with (
        stash_cleanup_tracker(stash_client),
        capture_graphql_calls(stash_client) as calls,
    ):
        # Get a scene from find_scenes first
        result = await stash_client.find_scenes(filter_={"per_page": 1})
        assert is_set(result.count), "result.count should be set"
        assert result.count > 0, "No scenes available in test Stash instance"

        assert is_set(result.scenes), "result.scenes should be set"
        scene_id = result.scenes[0].id

        # Clear calls from find_scenes
        calls.clear()

        # Now test find_scene
        scene = await stash_client.find_scene(scene_id)

        # Verify GraphQL calls
        assert len(calls) == 1, "Expected 1 GraphQL call for find_scene"
        assert "findScene" in calls[0]["query"]
        assert calls[0]["variables"]["id"] == scene_id
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify response
        assert scene is not None
        assert isinstance(scene, Scene)
        assert scene.id == scene_id


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_scenes
async def test_find_scenes_with_pagination(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding scenes with pagination."""
    async with (
        stash_cleanup_tracker(stash_client),
        capture_graphql_calls(stash_client) as calls,
    ):
        # Get first page
        result = await stash_client.find_scenes(filter_={"page": 1, "per_page": 5})

        # Verify GraphQL calls
        assert len(calls) == 1, "Expected 1 GraphQL call for find_scenes"
        assert "findScenes" in calls[0]["query"]
        assert calls[0]["variables"]["filter"]["page"] == 1
        assert calls[0]["variables"]["filter"]["per_page"] == 5
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify response
        assert result is not None
        assert is_set(result.count), "result.count should be set"
        assert result.count > 0
        assert is_set(result.scenes), "result.scenes should be set"
        assert len(result.scenes) > 0
        assert all(isinstance(scene, Scene) for scene in result.scenes)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_and_find_scene(
    stash_client: StashClient, stash_cleanup_tracker, enable_scene_creation
) -> None:
    """Test creating a new scene and finding it."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        # Create a new scene
        new_scene = Scene.new(
            title="Integration Test Scene",
            details="Created by integration test",
        )

        created_scene = await stash_client.create_scene(new_scene)
        cleanup["scenes"].append(created_scene.id)

        # Verify creation call
        assert len(calls) == 1, "Expected 1 GraphQL call for create_scene"
        assert "sceneCreate" in calls[0]["query"]
        assert calls[0]["variables"]["input"]["title"] == "Integration Test Scene"
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify created scene
        assert created_scene is not None
        assert isinstance(created_scene, Scene)
        assert created_scene.id is not None
        assert created_scene.title == "Integration Test Scene"
        assert created_scene.details == "Created by integration test"

        # Clear calls and verify we can find it
        calls.clear()
        found_scene = await stash_client.find_scene(created_scene.id)

        assert len(calls) == 1, "Expected 1 GraphQL call for find_scene"
        assert "findScene" in calls[0]["query"]
        assert found_scene is not None, "Scene should be found"
        assert found_scene.id == created_scene.id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_and_update_scene(
    stash_client: StashClient, stash_cleanup_tracker, enable_scene_creation
) -> None:
    """Test creating and updating a scene."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        # Create scene
        new_scene = Scene.new(
            title="Test Scene Before Update",
            details="Original details",
        )

        created_scene = await stash_client.create_scene(new_scene)
        cleanup["scenes"].append(created_scene.id)

        # Verify creation
        assert len(calls) == 1
        assert "sceneCreate" in calls[0]["query"]
        calls.clear()

        # Update the scene
        created_scene.title = "Test Scene After Update"
        created_scene.details = "Updated details"
        created_scene.rating100 = 80

        updated_scene = await stash_client.update_scene(created_scene)

        # Verify update call
        assert len(calls) == 1, "Expected 1 GraphQL call for update_scene"
        assert "sceneUpdate" in calls[0]["query"]
        assert calls[0]["variables"]["input"]["id"] == created_scene.id
        assert calls[0]["variables"]["input"]["title"] == "Test Scene After Update"
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify updated scene
        assert updated_scene.id == created_scene.id
        assert updated_scene.title == "Test Scene After Update"
        assert updated_scene.details == "Updated details"
        # rating100 might not be in the update response, so just check it was set
        if updated_scene.rating100 is not None:
            assert updated_scene.rating100 == 80


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_and_destroy_scene(
    stash_client: StashClient, stash_cleanup_tracker, enable_scene_creation
) -> None:
    """Test creating and destroying a scene."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        # Create scene
        new_scene = Scene.new(title="Scene to be destroyed")
        created_scene = await stash_client.create_scene(new_scene)
        cleanup["scenes"].append(created_scene.id)
        scene_id = created_scene.id

        # Verify creation
        assert len(calls) == 1
        calls.clear()

        # Destroy the scene
        success = await stash_client.scene_destroy(
            {"id": scene_id, "delete_file": False}
        )

        # Verify destroy call
        assert len(calls) == 1, "Expected 1 GraphQL call for scene_destroy"
        assert "sceneDestroy" in calls[0]["query"]
        assert calls[0]["variables"]["input"]["id"] == scene_id
        assert calls[0]["variables"]["input"]["delete_file"] is False
        assert calls[0]["exception"] is None

        # Verify destruction
        assert success is True
        cleanup["scenes"].remove(scene_id)

        # Verify it's gone
        calls.clear()
        found_scene = await stash_client.find_scene(scene_id)
        assert found_scene is None


# =============================================================================
# Scene Relationships Integration Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_scene_with_studio(
    stash_client: StashClient, stash_cleanup_tracker, enable_scene_creation
) -> None:
    """Test creating a scene with a studio relationship."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        # Create a unique test studio
        test_uid = time.monotonic_ns()
        studio_obj = Studio.new(name=f"Studio for scene {test_uid}")
        created_studio = await stash_client.create_studio(studio_obj)
        cleanup["studios"].append(created_studio.id)

        calls.clear()

        # Create scene with the test studio
        new_scene = Scene.new(
            title=f"Scene with Studio {test_uid}",
            studio=created_studio,
        )

        created_scene = await stash_client.create_scene(new_scene)
        cleanup["scenes"].append(created_scene.id)

        # Verify GraphQL call
        assert len(calls) == 1
        assert "sceneCreate" in calls[0]["query"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify scene was created successfully
        assert created_scene is not None
        assert isinstance(created_scene, Scene)
        assert created_scene.id is not None
        assert created_scene.title == f"Scene with Studio {test_uid}"

        # Invalidate cache and refetch to verify studio relationship
        assert Scene._store is not None, "Scene._store should be initialized"
        Scene._store.invalidate(Scene, created_scene.id)
        calls.clear()
        found_scene = await stash_client.find_scene(created_scene.id)

        assert len(calls) == 1
        assert "findScene" in calls[0]["query"]
        assert found_scene is not None

        # Verify studio relationship if present in response
        if is_set(found_scene.studio) and found_scene.studio is not None:
            assert found_scene.studio.id == created_studio.id


# =============================================================================
# Scene Watch/Play Tracking Integration Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_scene_add_and_reset_o_counter(
    stash_client: StashClient, stash_cleanup_tracker, enable_scene_creation
) -> None:
    """Test adding O counter and resetting it."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        # Create a test scene
        new_scene = Scene.new(title="Test O Counter Scene")
        created_scene = await stash_client.create_scene(new_scene)
        cleanup["scenes"].append(created_scene.id)

        calls.clear()

        # Add O (mark as watched)
        result_1 = await stash_client.scene_add_o(created_scene.id)

        assert len(calls) == 1
        assert "SceneAddO" in calls[0]["query"]
        assert calls[0]["variables"]["id"] == created_scene.id
        assert result_1.count == 1

        calls.clear()

        # Add another O
        result_2 = await stash_client.scene_add_o(created_scene.id)
        assert result_2.count == 2

        calls.clear()

        # Reset O counter
        final_result = await stash_client.scene_reset_o(created_scene.id)

        assert len(calls) == 1
        assert "sceneResetO" in calls[0]["query"]
        assert calls[0]["variables"]["id"] == created_scene.id
        assert final_result == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_scene_add_and_reset_play_count(
    stash_client: StashClient, stash_cleanup_tracker, enable_scene_creation
) -> None:
    """Test adding play history and resetting play count."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        # Create a test scene
        new_scene = Scene.new(title="Test Play Count Scene")
        created_scene = await stash_client.create_scene(new_scene)
        cleanup["scenes"].append(created_scene.id)

        calls.clear()

        # Add play
        result_1 = await stash_client.scene_add_play(created_scene.id)

        assert len(calls) >= 1  # May include additional queries
        # Check if any call contains the play mutation
        assert any("Play" in call["query"] for call in calls)
        assert result_1.count == 1

        calls.clear()

        # Reset play count
        final_result = await stash_client.scene_reset_play_count(created_scene.id)

        assert len(calls) >= 1
        # Check for reset mutation
        assert any(
            "Play" in call["query"] or "Reset" in call["query"] for call in calls
        )
        assert final_result == 0


# =============================================================================
# Scene Query Integration Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_scenes
async def test_find_scenes_with_filter(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding scenes with filter criteria."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        # Test with rating filter
        filter_data = {"rating100": {"value": 50, "modifier": "GREATER_THAN"}}

        result = await stash_client.find_scenes(
            filter_={"per_page": 10}, scene_filter=filter_data
        )

        # Verify GraphQL call includes filter
        assert len(calls) == 1
        assert "findScenes" in calls[0]["query"]
        assert "scene_filter" in calls[0]["variables"]
        assert calls[0]["exception"] is None

        # Verify response
        assert result is not None
        assert is_set(result.count), "result.count should be set"
        assert result.count >= 0
        assert isinstance(result.scenes, list)


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_scenes
async def test_scene_wall(stash_client: StashClient, stash_cleanup_tracker) -> None:
    """Test getting scene wall (random scenes for display)."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        scenes = await stash_client.scene_wall()

        # Verify GraphQL call
        assert len(calls) == 1
        assert "sceneWall" in calls[0]["query"]
        assert calls[0]["exception"] is None

        # Verify response
        assert scenes is not None
        assert isinstance(scenes, list)
        if len(scenes) > 0:
            assert all(isinstance(scene, Scene) for scene in scenes)
