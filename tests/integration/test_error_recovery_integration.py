"""Integration tests for error recovery and data validation.

These tests require a running Stash instance.
Migrated from fansly-downloader-ng (tests/stash/integration/test_error_recovery.py).
"""

import asyncio

import pytest

from stash_graphql_client import StashClient
from stash_graphql_client.types import (
    Gallery,
    GenderEnum,
    Performer,
    Scene,
    Studio,
    Tag,
)
from tests.fixtures import capture_graphql_calls, dump_graphql_calls


# Integration tests with metadata generation and error recovery need longer timeouts
pytestmark = [pytest.mark.asyncio, pytest.mark.timeout(180)]


def get_id(obj):
    """Get ID from Pydantic model."""
    return obj.id


def get_ids(objects):
    """Get set of IDs from list of Pydantic models."""
    return {obj.id for obj in objects}


def get_attribute(obj, attr_name):
    """Get attribute from Pydantic model."""
    return getattr(obj, attr_name, None)


def get_attribute_list(obj, attr_name):
    """Get attribute list from Pydantic model."""
    attr = getattr(obj, attr_name, None)
    if attr is None:
        return []
    return attr


@pytest.mark.asyncio
async def test_concurrent_error_recovery(
    stash_client: StashClient, enable_scene_creation, stash_cleanup_tracker
) -> None:
    """Test concurrent error recovery.

    This test:
    1. Attempts multiple operations concurrently
    2. Handles errors in parallel
    3. Recovers from failures
    4. Verifies final state
    """
    try:
        async with (
            stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
            capture_graphql_calls(stash_client) as calls,
        ):
            # Create base data
            try:
                performer = Performer(
                    name="[TEST] Concurrent Error - Test Performer",
                    gender=GenderEnum.FEMALE,
                )
                performer = await stash_client.create_performer(performer)
                cleanup["performers"].append(performer.id)

                studio = Studio(
                    name="[TEST] Concurrent Error - Test Studio",
                )
                studio = await stash_client.create_studio(studio)
                cleanup["studios"].append(studio.id)
            finally:
                dump_graphql_calls(calls, "create base data")

            # Create an invalid performer for testing
            invalid_performer = Performer(
                id="999999",  # Non-existent ID
                name="Invalid",
            )

            # Attempt concurrent scene creation with some invalid data
            async def create_scene(i: int, should_fail: bool = False) -> Scene | None:
                try:
                    scene = Scene(
                        title=f"[TEST] Concurrent Error - Scene {i}",
                        details=f"Created by concurrent error recovery test - Scene {i}",
                        date="2024-01-01",
                        urls=[f"https://example.com/scene_{i}"],
                        organized=True,
                        performers=[invalid_performer if should_fail else performer],
                        studio=studio,
                    )
                    created = await stash_client.create_scene(scene)
                    cleanup["scenes"].append(
                        created.id
                    )  # Use attribute notation instead of dictionary access
                except Exception as e:
                    print(f"Scene {i} creation failed: {e}")
                    if should_fail:
                        # Expected failure with invalid performer
                        return None
                    raise  # Unexpected failure
                else:
                    return created

            calls.clear()

            # Create 5 scenes, 2 with invalid performers
            try:
                scene_tasks = [
                    create_scene(i, should_fail=(i % 2 == 0)) for i in range(5)
                ]
                scenes = await asyncio.gather(*scene_tasks)
            finally:
                dump_graphql_calls(calls, "concurrent scene creation")

            valid_scenes = [s for s in scenes if s is not None]
            assert (
                len(valid_scenes) == 2
            )  # Exactly the scenes with valid performers (odd indices)

            # Attempt concurrent gallery creation with some invalid data
            async def create_gallery(
                i: int, should_fail: bool = False
            ) -> Gallery | None:
                try:
                    gallery = Gallery(
                        title=f"[TEST] Concurrent Error - Gallery {i}",
                        details=f"Created by concurrent error recovery test - Gallery {i}",
                        date="2024-01-01",
                        urls=[f"https://example.com/gallery_{i}"],
                        organized=True,
                        performers=[invalid_performer if should_fail else performer],
                        studio=studio,
                    )
                    created = await stash_client.create_gallery(gallery)
                    cleanup["galleries"].append(created.id)
                except Exception as e:
                    print(f"Gallery {i} creation failed: {e}")
                    if should_fail:
                        # Expected failure with invalid performer
                        return None
                    raise  # Unexpected failure
                else:
                    return created

            calls.clear()

            # Create 5 galleries, 2 with invalid performers
            try:
                gallery_tasks = [
                    create_gallery(i, should_fail=(i % 2 == 0)) for i in range(5)
                ]
                galleries = await asyncio.gather(*gallery_tasks)
            finally:
                dump_graphql_calls(calls, "concurrent gallery creation")

            valid_galleries = [g for g in galleries if g is not None]
            assert (
                len(valid_galleries) == 2
            )  # Exactly the galleries with valid performers (odd indices)

            calls.clear()

            # Verify final state
            found_scenes: list[Scene | None] = []
            found_galleries: list[Gallery | None] = []
            try:
                for scene in valid_scenes:
                    found_scenes.append(await stash_client.find_scene(scene.id))
                for gallery in valid_galleries:
                    found_galleries.append(await stash_client.find_gallery(gallery.id))
            finally:
                dump_graphql_calls(calls, "verify final state")

            for found_scene in found_scenes:
                assert found_scene is not None
                assert performer.id in get_ids(found_scene.performers)
                assert get_id(found_scene.studio) == studio.id

            for found_gallery in found_galleries:
                assert found_gallery is not None
                assert performer.id in get_ids(found_gallery.performers)
                assert get_id(found_gallery.studio) == studio.id

    except RuntimeError as e:
        if "Stash instance" in str(e):
            pytest.skip(f"Test requires running Stash instance: {e}")
        else:
            raise


@pytest.mark.asyncio
async def test_relationship_error_recovery(
    stash_client: StashClient, enable_scene_creation, stash_cleanup_tracker
) -> None:
    """Test relationship error recovery.

    This test:
    1. Creates test content with relationships
    2. Attempts invalid relationship updates
    3. Recovers from failures
    4. Verifies relationship integrity
    """
    try:
        async with (
            stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
            capture_graphql_calls(stash_client) as calls,
        ):
            # Create test data with unique names to avoid conflicts
            try:
                performer = Performer(
                    name="[TEST] Relationship Error - Performer",  # Unique name
                    gender=GenderEnum.FEMALE,
                )
                performer = await stash_client.create_performer(performer)
                cleanup["performers"].append(performer.id)

                studio = Studio(
                    name="[TEST] Relationship Error - Studio",  # Unique name
                )
                studio = await stash_client.create_studio(studio)
                cleanup["studios"].append(studio.id)

                tag = Tag(
                    name="[TEST] relationship_error_tag",  # Unique name
                )
                tag = await stash_client.create_tag(tag)
                cleanup["tags"].append(tag.id)

                # Create scene with relationships
                scene = Scene(
                    title="[TEST] Relationship Error - Scene",  # Unique name
                    details="Test details",
                    date="2024-01-01",
                    urls=["https://example.com/scene"],
                    organized=True,
                    performers=[performer],
                    studio=studio,
                    tags=[tag],
                )
                scene = await stash_client.create_scene(scene)
                cleanup["scenes"].append(scene.id)
            finally:
                dump_graphql_calls(calls, "create test data with relationships")

            assert performer is not None, "Performer creation failed"
            assert performer.id, "Performer ID is missing"
            performer_id = get_id(performer)
            assert studio is not None, "Studio creation failed"
            assert studio.id, "Studio ID is missing"
            studio_id = get_id(studio)
            assert tag is not None, "Tag creation failed"
            assert tag.id, "Tag ID is missing"
            tag_id = get_id(tag)
            assert scene is not None, "Scene creation failed"
            assert scene.id, "Scene ID is missing"
            scene_id = get_id(scene)

            calls.clear()

            # Attempt invalid relationship updates, recovering after each
            try:
                # Test invalid performer relationship
                try:
                    invalid_performer = Performer(
                        id="999999",
                        name="Invalid",
                    )
                    scene.performers = [invalid_performer]
                    await stash_client.update_scene(scene)
                    pytest.fail("Should have failed with invalid performer")
                except Exception as e:
                    print(f"Expected failure with invalid performer: {e}")
                    # Restore valid performer
                    scene.performers = [performer]
                    scene = await stash_client.update_scene(scene)

                # Test invalid studio relationship
                try:
                    invalid_studio = Studio(
                        id="999999",
                        name="Invalid",
                    )
                    scene.studio = invalid_studio
                    await stash_client.update_scene(scene)
                    pytest.fail("Should have failed with invalid studio")
                except Exception as e:
                    print(f"Expected failure with invalid studio: {e}")
                    # Restore valid studio
                    scene.studio = studio
                    scene = await stash_client.update_scene(scene)

                # Test invalid tag relationship
                try:
                    invalid_tag = Tag(
                        id="999999",
                        name="invalid",
                    )
                    scene.tags = [invalid_tag]
                    await stash_client.update_scene(scene)
                    pytest.fail("Should have failed with invalid tag")
                except Exception as e:
                    print(f"Expected failure with invalid tag: {e}")
                    # Restore valid tag
                    scene.tags = [tag]
                    scene = await stash_client.update_scene(scene)
            finally:
                dump_graphql_calls(calls, "invalid relationship updates and recovery")

            calls.clear()

            # Verify final state
            try:
                found_scene = await stash_client.find_scene(scene_id)
            finally:
                dump_graphql_calls(calls, "verify relationship integrity")

            assert found_scene is not None

            performers = get_attribute_list(found_scene, "performers")
            assert len(performers) == 1
            assert performer_id in get_ids(performers)

            scene_studio = get_attribute(found_scene, "studio")
            assert get_id(scene_studio) == studio_id

            tags = get_attribute_list(found_scene, "tags")
            assert len(tags) == 1
            assert tag_id in get_ids(tags)

    except RuntimeError as e:
        if "Stash instance" in str(e):
            pytest.skip(f"Test requires running Stash instance: {e}")
        else:
            raise
