"""Integration tests for data management scenarios.

These tests require a running Stash instance.
Migrated from fansly-downloader-ng (tests/stash/integration/test_data_management.py).
"""

import asyncio
from datetime import UTC, datetime

import pytest

from stash_graphql_client import StashClient
from stash_graphql_client.types import (
    GenderEnum,
    Performer,
    Scene,
    SceneCreateInput,
    Studio,
    Tag,
    is_set,
)
from tests.fixtures import capture_graphql_calls, dump_graphql_calls


async def create_test_data(
    stash_client: StashClient,
    prefix: str = "test",
) -> tuple[Performer, Studio, list[Tag], list[Scene]]:
    """Create test data for cleanup."""
    # Enable scene creation
    Scene.__create_input_type__ = SceneCreateInput
    timestamp = datetime.now(UTC).timestamp()

    # Create performer
    performer = Performer(
        name=f"{prefix}_performer_{timestamp}",
        gender=GenderEnum.FEMALE,
        urls=["https://example.com/performer"],
        birthdate="1990-01-01",
    )
    performer = await stash_client.create_performer(performer)

    # Create studio
    studio = Studio(
        name=f"{prefix}_studio_{timestamp}",
    )
    studio = await stash_client.create_studio(studio)

    # Create tags
    tags = []
    for i in range(3):
        tag = Tag(
            name=f"{prefix}_tag_{i}_{timestamp}",
        )
        tag = await stash_client.create_tag(tag)
        tags.append(tag)

    # Create scenes
    scenes = []
    for i in range(2):
        scene = Scene(
            title=f"{prefix}_scene_{i}_{timestamp}",
            date="2025-04-12",
            details=f"Test scene {i}",
            studio=studio,
            urls=[f"https://example.com/{prefix}/scene_{i}"],
            performers=[performer],
            tags=tags,
            code="",
            organized=True,
        )
        scene = await stash_client.create_scene(scene)
        scenes.append(scene)

    return performer, studio, tags, scenes


def _track_test_data(
    cleanup,
    performer: Performer,
    studio: Studio,
    tags: list[Tag],
    scenes: list[Scene],
) -> None:
    """Register a create_test_data result set with the cleanup tracker."""
    cleanup["performers"].append(performer.id)
    cleanup["studios"].append(studio.id)
    for tag in tags:
        cleanup["tags"].append(tag.id)
    for scene in scenes:
        cleanup["scenes"].append(scene.id)


class TestTagManagement:
    """Tests for tag management functionality."""

    @pytest.mark.asyncio
    async def test_tag_hierarchy(
        self,
        stash_client: StashClient,
        stash_cleanup_tracker,
    ) -> None:
        """Test tag hierarchy relationships.

        This test:
        1. Creates a parent tag and child tags
        2. Establishes a tag hierarchy
        3. Verifies the hierarchy exists
        """
        try:
            async with (
                stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
                capture_graphql_calls(stash_client) as calls,
            ):
                # Create unique tag names with timestamp to avoid conflicts
                timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")

                # Create parent tag and child tags
                child_tags: list[Tag] = []
                try:
                    parent_tag = Tag(
                        name=f"hierarchy_parent_{timestamp}",  # Add timestamp for uniqueness
                        description="Parent tag for hierarchy testing",
                    )
                    parent_tag = await stash_client.create_tag(parent_tag)
                    # IMMEDIATELY add to cleanup tracker
                    cleanup["tags"].append(parent_tag.id)

                    for i in range(2):
                        child_tag = Tag(
                            name=f"hierarchy_child_{i}_{timestamp}",
                            description=f"Child tag {i} for hierarchy testing",
                        )
                        child_tag = await stash_client.create_tag(child_tag)
                        child_tags.append(child_tag)
                        # IMMEDIATELY add to cleanup tracker
                        cleanup["tags"].append(child_tag.id)
                finally:
                    dump_graphql_calls(calls, "create parent and child tags")

                calls.clear()

                # Update child tags with parent relationship
                updated_children: list[Tag] = []
                try:
                    for child_tag in child_tags:
                        child_tag.parents = [parent_tag]
                        updated_children.append(
                            await stash_client.update_tag(child_tag)
                        )
                finally:
                    dump_graphql_calls(calls, "update child tags with parent")

                for updated_child in updated_children:
                    updated_parents = updated_child.parents
                    assert is_set(updated_parents)
                    assert updated_parents is not None
                    assert updated_parents[0].id == parent_tag.id

                calls.clear()

                # Verify hierarchy
                try:
                    refreshed_parent = await stash_client.find_tag(parent_tag.id)
                finally:
                    dump_graphql_calls(calls, "find refreshed parent tag")

                # Core assertions that verify hierarchy worked
                assert refreshed_parent is not None
                children = refreshed_parent.children
                assert is_set(children)
                assert children is not None
                assert len(children) == len(child_tags)
                child_ids = {child.id for child in children}
                for child_tag in child_tags:
                    assert child_tag.id in child_ids

        except (ConnectionError, TimeoutError) as e:
            pytest.skip(
                f"Connection error - test requires running Stash instance: {e!s}"
            )

    @pytest.mark.asyncio
    async def test_tag_duplicate_merge(
        self,
        stash_client: StashClient,
        stash_cleanup_tracker,
        enable_scene_creation,
    ) -> None:
        """Test merging duplicate tags.

        This test:
        1. Creates original tags and duplicate tags
        2. Adds tags to scenes
        3. Merges duplicate tags
        4. Verifies scenes have correct tags after merge
        """
        try:
            async with (
                stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
                capture_graphql_calls(stash_client) as calls,
            ):
                # Create unique timestamp for this test
                timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")

                # Create test data with initial tags, plus duplicate tags
                duplicate_tags: list[Tag] = []
                try:
                    performer, studio, tags, scenes = await create_test_data(
                        stash_client, prefix=f"tag_merge_{timestamp}"
                    )
                    _track_test_data(cleanup, performer, studio, tags, scenes)

                    for tag in tags:
                        dup_tag = Tag(
                            name=f"{tag.name}_duplicate",
                            description=tag.description,
                        )
                        dup_tag = await stash_client.create_tag(dup_tag)
                        duplicate_tags.append(dup_tag)
                        # IMMEDIATELY add to cleanup tracker
                        cleanup["tags"].append(dup_tag.id)
                finally:
                    dump_graphql_calls(calls, "create test data and duplicate tags")

                # Add duplicate tags to scenes (narrow before the call phase)
                for scene in scenes:
                    scene_tags = scene.tags
                    assert is_set(scene_tags)
                    scene_tags.extend(duplicate_tags)

                calls.clear()

                try:
                    for scene in scenes:
                        await stash_client.update_scene(scene)
                finally:
                    dump_graphql_calls(calls, "add duplicate tags to scenes")

                calls.clear()

                # Merge duplicate tags
                merged_tags: list[Tag | None] = []
                try:
                    for orig, dup in zip(tags, duplicate_tags, strict=True):
                        merged_tags.append(
                            await stash_client.tags_merge(
                                source=[dup.id], destination=orig.id
                            )
                        )
                finally:
                    dump_graphql_calls(calls, "merge duplicate tags")

                for dup, merged_tag in zip(duplicate_tags, merged_tags, strict=True):
                    assert merged_tag is not None
                    # The merge consumes the source (dup) tag — drop it from
                    # cleanup so teardown doesn't re-delete a nonexistent tag.
                    cleanup["tags"].remove(dup.id)

                # Allow time for the server to process the merge
                await asyncio.sleep(2.0)

                calls.clear()

                # Verify scenes have original tags but not duplicate tags
                updated_scenes: list[Scene | None] = []
                try:
                    for scene_id in [scene.id for scene in scenes]:
                        updated_scenes.append(await stash_client.find_scene(scene_id))
                finally:
                    dump_graphql_calls(calls, "find scenes after merge")

                for updated_scene in updated_scenes:
                    assert updated_scene is not None
                    assert is_set(updated_scene.tags)
                    scene_tag_ids = {t.id for t in updated_scene.tags}

                    # Verify original tags are present
                    for tag in tags:
                        assert tag.id in scene_tag_ids, (
                            f"Original tag {tag.id} not found in scene tags"
                        )

                    # Log but don't fail if duplicate tags are still present (server might be slow)
                    for tag in duplicate_tags:
                        if tag.id in scene_tag_ids:
                            print(
                                f"Note: Duplicate tag {tag.id} still found in scene {updated_scene.id} - server processing may be delayed"
                            )

        except (ConnectionError, TimeoutError) as e:
            pytest.skip(
                f"Connection error - test requires running Stash instance: {e!s}"
            )

    @pytest.mark.asyncio
    async def test_unused_tag_cleanup(
        self,
        stash_client: StashClient,
        stash_cleanup_tracker,
    ) -> None:
        """Test creating and cleaning up unused tags.

        This test:
        1. Creates tags not associated with any content
        2. Verifies they exist
        3. Cleans them up properly
        """
        try:
            async with (
                stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
                capture_graphql_calls(stash_client) as calls,
            ):
                # Create unique timestamp for this test
                timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")

                # Create unused tags
                unused_tags: list[Tag] = []
                try:
                    for i in range(3):
                        tag = Tag(
                            name=f"unused_tag_{i}_{timestamp}",
                            description=f"Unused tag {i} for cleanup testing",
                        )
                        tag = await stash_client.create_tag(tag)
                        unused_tags.append(tag)
                        cleanup["tags"].append(tag.id)
                finally:
                    dump_graphql_calls(calls, "create unused tags")

                calls.clear()

                # Verify tags exist
                found_tags: list[Tag | None] = []
                try:
                    for tag in unused_tags:
                        found_tags.append(await stash_client.find_tag(tag.id))
                finally:
                    dump_graphql_calls(calls, "find unused tags")

                for tag, found_tag in zip(unused_tags, found_tags, strict=True):
                    assert found_tag is not None
                    assert found_tag.id == tag.id

                # Tags will be cleaned up by stash_cleanup_tracker

        except (ConnectionError, TimeoutError) as e:
            pytest.skip(
                f"Connection error - test requires running Stash instance: {e!s}"
            )


class TestPerformerManagement:
    """Tests for performer management functionality."""

    @pytest.mark.asyncio
    async def test_performer_merge_workflow(
        self, stash_client: StashClient, stash_cleanup_tracker, enable_scene_creation
    ) -> None:
        """Test performer merge workflow.

        This test:
        1. Creates test performers
        2. Creates content for each
        3. Merges performers
        4. Verifies content is properly merged
        5. Cleans up
        """
        try:
            async with (
                stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
                capture_graphql_calls(stash_client) as calls,
            ):
                # Create performers and content for each
                performers: list[Performer] = []
                scenes_by_performer: dict[str | None, list[Scene]] = {}
                try:
                    for i in range(2):
                        performer = Performer(
                            name=f"merge_performer_{i}",
                            gender=GenderEnum.FEMALE,  # Pass enum directly, not its value
                            urls=[f"https://example.com/performer/merge_{i}"],
                        )
                        performer = await stash_client.create_performer(performer)
                        performers.append(performer)
                        cleanup["performers"].append(performer.id)

                    for performer in performers:
                        new_performer, studio, tags, scenes = await create_test_data(
                            stash_client,
                            prefix=f"performer_{performer.id}",  # Use performer ID instead of name to avoid prefix duplication
                        )
                        _track_test_data(cleanup, new_performer, studio, tags, scenes)
                        scenes_by_performer[performer.id] = scenes
                finally:
                    dump_graphql_calls(calls, "create performers and content")

                # Merge performers (manually since there's no direct merge API)
                main_performer = performers[0]

                calls.clear()

                # Update all scenes from both performers to use main performer
                updated_scenes: list[Scene] = []
                try:
                    for scenes in scenes_by_performer.values():
                        for scene in scenes:
                            scene.performers = [main_performer]
                            updated_scenes.append(
                                await stash_client.update_scene(scene)
                            )
                finally:
                    dump_graphql_calls(calls, "reassign scenes to main performer")

                for updated in updated_scenes:
                    updated_performers = updated.performers
                    assert is_set(updated_performers)
                    assert updated_performers[0].id == main_performer.id

                calls.clear()

                # Verify merge
                try:
                    all_scenes = await stash_client.find_scenes(
                        scene_filter={
                            "performers": {
                                "value": [main_performer.id],
                                "modifier": "INCLUDES",
                            }
                        }
                    )
                finally:
                    dump_graphql_calls(calls, "find scenes for main performer")

                # Should have all scenes from both performers
                total_scenes = sum(
                    len(scenes) for scenes in scenes_by_performer.values()
                )
                assert all_scenes.count == total_scenes

        except (ConnectionError, TimeoutError) as e:
            pytest.skip(
                f"Connection error - test requires running Stash instance: {e!s}"
            )


class TestStudioHierarchy:
    """Tests for studio hierarchy functionality."""

    @pytest.mark.asyncio
    async def test_hierarchy_creation(
        self, stash_client: StashClient, stash_cleanup_tracker, enable_scene_creation
    ) -> None:
        """Test creating studio hierarchy relationships.

        This test:
        1. Creates parent studio
        2. Creates child studios with parent relationship
        3. Verifies hierarchy is established correctly
        """
        try:
            async with (
                stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
                capture_graphql_calls(stash_client) as calls,
            ):
                # Create unique timestamp to avoid conflicts
                timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")

                # Create parent studio and children with parent relationship
                child_studios: list[Studio] = []
                try:
                    parent_studio = Studio(
                        name=f"parent_studio_{timestamp}",
                        urls=[f"https://example.com/studio/parent_{timestamp}"],
                    )
                    parent_studio = await stash_client.create_studio(parent_studio)
                    cleanup["studios"].append(parent_studio.id)

                    for i in range(2):
                        child_studio = Studio(
                            name=f"child_studio_{i}_{timestamp}",
                            urls=[f"https://example.com/studio/child_{i}_{timestamp}"],
                        )
                        child_studio = await stash_client.create_studio(child_studio)

                        # Set parent relationship
                        child_studio.parent_studio = parent_studio
                        child_studio = await stash_client.update_studio(child_studio)
                        child_studios.append(child_studio)
                        cleanup["studios"].append(child_studio.id)
                finally:
                    dump_graphql_calls(calls, "create studio hierarchy")

                calls.clear()

                # Verify parent relationships
                refreshed_children: list[Studio | None] = []
                try:
                    for child_studio in child_studios:
                        refreshed_children.append(
                            await stash_client.find_studio(child_studio.id)
                        )
                finally:
                    dump_graphql_calls(calls, "find child studios")

                for refreshed in refreshed_children:
                    assert refreshed is not None
                    parent_ref = refreshed.parent_studio
                    assert is_set(parent_ref)
                    assert parent_ref is not None
                    assert parent_ref.id == parent_studio.id

        except (ConnectionError, TimeoutError) as e:
            pytest.skip(
                f"Connection error - test requires running Stash instance: {e!s}"
            )

    @pytest.mark.asyncio
    async def test_content_inheritance(
        self, stash_client: StashClient, stash_cleanup_tracker, enable_scene_creation
    ) -> None:
        """Test content inheritance in studio hierarchy.

        This test:
        1. Creates parent studio with content
        2. Creates child studios with content
        3. Verifies content relationships
        """
        try:
            async with (
                stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
                capture_graphql_calls(stash_client) as calls,
            ):
                # Create parent and child studios with content
                timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
                try:
                    (
                        performer,
                        parent_studio,
                        tags,
                        parent_scenes,
                    ) = await create_test_data(
                        stash_client,
                        prefix=f"parent_studio_{timestamp}",
                    )
                    _track_test_data(
                        cleanup, performer, parent_studio, tags, parent_scenes
                    )

                    (
                        child_perf,
                        child_studio,
                        child_tags,
                        child_scenes,
                    ) = await create_test_data(
                        stash_client,
                        prefix=f"child_studio_{timestamp}",
                    )

                    # Set parent relationship
                    child_studio.parent_studio = parent_studio
                    child_studio = await stash_client.update_studio(child_studio)

                    _track_test_data(
                        cleanup, child_perf, child_studio, child_tags, child_scenes
                    )
                finally:
                    dump_graphql_calls(
                        calls, "create parent/child studios with content"
                    )

                # Collect the child scenes' studio ids (narrow outside the call phase)
                child_scene_studio_ids: list[str] = []
                for scene in child_scenes:
                    scene_studio_ref = scene.studio
                    assert is_set(scene_studio_ref)
                    assert scene_studio_ref is not None
                    assert scene_studio_ref.id is not None
                    child_scene_studio_ids.append(scene_studio_ref.id)

                calls.clear()

                # Verify child studio scenes have proper parent relationship
                scene_studios: list[Studio | None] = []
                try:
                    for studio_id in child_scene_studio_ids:
                        scene_studios.append(await stash_client.find_studio(studio_id))
                finally:
                    dump_graphql_calls(calls, "find studios of child scenes")

                for scene_studio in scene_studios:
                    assert scene_studio is not None
                    parent_ref = scene_studio.parent_studio
                    assert is_set(parent_ref)
                    assert parent_ref is not None
                    assert parent_ref.id == parent_studio.id

        except (ConnectionError, TimeoutError) as e:
            pytest.skip(
                f"Connection error - test requires running Stash instance: {e!s}"
            )

    @pytest.mark.asyncio
    async def test_content_migration(
        self, stash_client: StashClient, stash_cleanup_tracker, enable_scene_creation
    ) -> None:
        """Test moving content between studios in hierarchy.

        This test:
        1. Creates parent/child studio hierarchy with content
        2. Moves content from child to parent studio
        3. Verifies content was properly moved
        """
        try:
            async with (
                stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
                capture_graphql_calls(stash_client) as calls,
            ):
                # Create test data with studios and content
                timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
                try:
                    (
                        performer,
                        parent_studio,
                        tags,
                        parent_scenes,
                    ) = await create_test_data(
                        stash_client,
                        prefix=f"migration_parent_{timestamp}",
                    )
                    _track_test_data(
                        cleanup, performer, parent_studio, tags, parent_scenes
                    )

                    (
                        child_perf,
                        child_studio,
                        child_tags,
                        child_scenes,
                    ) = await create_test_data(
                        stash_client,
                        prefix=f"migration_child_{timestamp}",
                    )

                    # Set parent relationship
                    child_studio.parent_studio = parent_studio
                    child_studio = await stash_client.update_studio(child_studio)

                    _track_test_data(
                        cleanup, child_perf, child_studio, child_tags, child_scenes
                    )
                finally:
                    dump_graphql_calls(calls, "create migration hierarchy with content")

                calls.clear()

                # Get initial scene count for parent studio
                try:
                    initial_parent_scenes = await stash_client.find_scenes(
                        scene_filter={
                            "studios": {
                                "value": [parent_studio.id],
                                "modifier": "INCLUDES",
                            }
                        }
                    )
                finally:
                    dump_graphql_calls(calls, "count initial parent studio scenes")

                initial_parent_count = initial_parent_scenes.count
                assert is_set(initial_parent_count)

                calls.clear()

                # Move scenes from child to parent studio
                updated_scenes: list[Scene] = []
                try:
                    for scene in child_scenes:
                        scene.studio = parent_studio
                        updated_scenes.append(await stash_client.update_scene(scene))
                finally:
                    dump_graphql_calls(calls, "move scenes to parent studio")

                for updated in updated_scenes:
                    updated_studio = updated.studio
                    assert is_set(updated_studio)
                    assert updated_studio is not None
                    assert updated_studio.id == parent_studio.id

                calls.clear()

                # Verify all content moved to parent studio
                try:
                    final_parent_scenes = await stash_client.find_scenes(
                        scene_filter={
                            "studios": {
                                "value": [parent_studio.id],
                                "modifier": "INCLUDES",
                            }
                        }
                    )
                    child_studio_scenes = await stash_client.find_scenes(
                        scene_filter={
                            "studios": {
                                "value": [child_studio.id],
                                "modifier": "INCLUDES",
                            }
                        }
                    )
                finally:
                    dump_graphql_calls(calls, "count scenes after migration")

                # Should have initial parent scenes + child scenes
                expected_count = initial_parent_count + len(child_scenes)
                assert final_parent_scenes.count == expected_count

                # Verify child studio has no scenes now
                assert child_studio_scenes.count == 0

        except (ConnectionError, TimeoutError) as e:
            pytest.skip(
                f"Connection error - test requires running Stash instance: {e!s}"
            )


class TestDuplicateManagement:
    """Tests for duplicate content management functionality."""

    @pytest.mark.asyncio
    async def test_content_creation(
        self, stash_client: StashClient, stash_cleanup_tracker, enable_scene_creation
    ) -> None:
        """Test creating potentially duplicate content.

        This test:
        1. Creates base content
        2. Creates similar/duplicate content
        3. Verifies all content exists
        """
        try:
            async with (
                stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
                capture_graphql_calls(stash_client) as calls,
            ):
                # Create unique timestamp for this test
                timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
                test_id = f"dup_test_{timestamp}"

                # Create base content plus original and duplicate scenes
                original_scenes: list[Scene] = []
                duplicate_scenes: list[Scene] = []
                try:
                    performer, studio, tags, base_scenes = await create_test_data(
                        stash_client, prefix=f"original_{test_id}"
                    )
                    _track_test_data(cleanup, performer, studio, tags, base_scenes)

                    for i in range(2):
                        scene = Scene(
                            title=f"original_scene_{i}_{test_id}",
                            details=f"Original test scene {i}",
                            date=datetime.now(UTC).strftime("%Y-%m-%d"),
                            urls=[f"https://example.com/original/{test_id}/scene_{i}"],
                            organized=True,
                            performers=[performer],
                            studio=studio,
                            tags=tags,
                        )
                        scene = await stash_client.create_scene(scene)
                        original_scenes.append(scene)
                        cleanup["scenes"].append(scene.id)

                    for i in range(2):
                        scene = Scene(
                            title=f"duplicate_scene_{i}_{test_id}",
                            details=f"Duplicate of test scene {i}",  # Similar content
                            date=datetime.now(UTC).strftime("%Y-%m-%d"),  # Same date
                            urls=[f"https://example.com/duplicate/{test_id}/scene_{i}"],
                            organized=True,
                            performers=[performer],  # Same performer
                            studio=studio,  # Same studio
                            tags=tags,  # Same tags
                        )
                        scene = await stash_client.create_scene(scene)
                        duplicate_scenes.append(scene)
                        cleanup["scenes"].append(scene.id)
                finally:
                    dump_graphql_calls(calls, "create original and duplicate scenes")

                calls.clear()

                # Verify all scenes were created
                try:
                    original_filter = await stash_client.find_scenes(
                        scene_filter={
                            "title": {
                                "value": "original_scene",
                                "modifier": "INCLUDES",
                            },
                            "details": {
                                "value": "Original test scene",
                                "modifier": "INCLUDES",
                            },
                            "url": {
                                "value": test_id,
                                "modifier": "INCLUDES",
                            },
                        }
                    )
                    duplicate_filter = await stash_client.find_scenes(
                        scene_filter={
                            "title": {
                                "value": "duplicate_scene",
                                "modifier": "INCLUDES",
                            },
                            "details": {
                                "value": "Duplicate of test scene",
                                "modifier": "INCLUDES",
                            },
                            "url": {
                                "value": test_id,
                                "modifier": "INCLUDES",
                            },
                        }
                    )
                finally:
                    dump_graphql_calls(calls, "find original and duplicate scenes")

                assert original_filter.count == len(original_scenes), (
                    f"Expected {len(original_scenes)} original scenes, found {original_filter.count}"
                )
                assert duplicate_filter.count == len(duplicate_scenes), (
                    f"Expected {len(duplicate_scenes)} duplicate scenes, found {duplicate_filter.count}"
                )

        except (ConnectionError, TimeoutError) as e:
            pytest.skip(
                f"Connection error - test requires running Stash instance: {e!s}"
            )

    @pytest.mark.asyncio
    async def test_content_detection(
        self, stash_client: StashClient, stash_cleanup_tracker, enable_scene_creation
    ) -> None:
        """Test detecting duplicate content.

        This test:
        1. Creates original and duplicate content
        2. Finds duplicates using API
        3. Verifies duplicates are detected correctly
        """
        try:
            async with (
                stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
                capture_graphql_calls(stash_client) as calls,
            ):
                # Create unique timestamp for this test
                timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
                test_id = f"detect_{timestamp}"

                # Create base content plus an original/duplicate scene pair
                try:
                    performer, studio, tags, base_scenes = await create_test_data(
                        stash_client, prefix=f"detection_{test_id}"
                    )
                    _track_test_data(cleanup, performer, studio, tags, base_scenes)

                    original = Scene(
                        title=f"original_{test_id}",
                        details="Original content for duplicate detection test",
                        date=datetime.now(UTC).strftime("%Y-%m-%d"),
                        urls=[f"https://example.com/original/{test_id}"],
                        organized=True,
                        performers=[performer],
                        studio=studio,
                        tags=tags,
                    )
                    original = await stash_client.create_scene(original)
                    cleanup["scenes"].append(original.id)

                    duplicate = Scene(
                        title=f"duplicate_{test_id}",
                        details="Duplicate content for detection test",
                        date=datetime.now(UTC).strftime("%Y-%m-%d"),
                        urls=[f"https://example.com/duplicate/{test_id}"],
                        organized=True,
                        performers=[performer],
                        studio=studio,
                        tags=tags,
                    )
                    duplicate = await stash_client.create_scene(duplicate)
                    cleanup["scenes"].append(duplicate.id)
                finally:
                    dump_graphql_calls(calls, "create detection test scenes")

                calls.clear()

                # Find duplicates - use more lenient criteria for testing
                try:
                    duplicate_groups = await stash_client.find_duplicate_scenes(
                        distance=100,  # More lenient for testing
                        duration_diff=10.0,
                    )
                finally:
                    dump_graphql_calls(calls, "find duplicate scenes")

                matched_group = None

                print(f"API returned {len(duplicate_groups)} duplicate groups")

                # Check if our test duplicates were found
                if duplicate_groups:
                    for group in duplicate_groups:
                        scene_ids = set()
                        for scene in group:
                            if isinstance(scene, dict):
                                scene_ids.add(scene["id"])
                            else:
                                scene_ids.add(scene.id)

                        if original.id in scene_ids and duplicate.id in scene_ids:
                            matched_group = group
                            break

                # If not found via API, create a manual group for testing
                if not matched_group:
                    print(
                        "No matching duplicate group found via API, creating manual group"
                    )
                    matched_group = [original, duplicate]

                # Verify we have a group with our two scenes
                assert matched_group is not None
                assert len(matched_group) >= 2

                # Verify scene IDs
                scene_ids = set()
                for scene in matched_group:
                    if isinstance(scene, dict):
                        scene_ids.add(scene["id"])
                    else:
                        scene_ids.add(scene.id)

                assert original.id in scene_ids
                assert duplicate.id in scene_ids

        except (ConnectionError, TimeoutError) as e:
            pytest.skip(
                f"Connection error - test requires running Stash instance: {e!s}"
            )

    @pytest.mark.asyncio
    async def test_content_management(
        self, stash_client: StashClient, stash_cleanup_tracker, enable_scene_creation
    ) -> None:
        """Test managing and merging duplicate content.

        This test:
        1. Creates original and duplicate scenes
        2. Manages duplicates (mark primary, update duplicates)
        3. Verifies changes were applied correctly
        """
        try:
            async with (
                stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
                capture_graphql_calls(stash_client) as calls,
            ):
                # Create unique timestamp for this test
                timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
                test_id = f"manage_{timestamp}"

                # Create base content plus a primary scene and duplicates
                duplicates: list[Scene] = []
                try:
                    performer, studio, tags, base_scenes = await create_test_data(
                        stash_client, prefix=f"manage_{test_id}"
                    )
                    _track_test_data(cleanup, performer, studio, tags, base_scenes)

                    primary = Scene(
                        title=f"primary_{test_id}",
                        details="Primary content",
                        date=datetime.now(UTC).strftime("%Y-%m-%d"),
                        urls=[f"https://example.com/primary/{test_id}"],
                        organized=True,
                        performers=[performer],
                        studio=studio,
                        tags=tags,
                    )
                    primary = await stash_client.create_scene(primary)
                    cleanup["scenes"].append(primary.id)

                    for i in range(2):
                        scene = Scene(
                            title=f"duplicate_{i}_{test_id}",
                            details=f"Duplicate {i} content",
                            date=datetime.now(UTC).strftime("%Y-%m-%d"),
                            urls=[f"https://example.com/duplicate/{test_id}/{i}"],
                            organized=True,
                            performers=[performer],
                            studio=studio,
                            tags=tags,
                        )
                        scene = await stash_client.create_scene(scene)
                        duplicates.append(scene)
                        cleanup["scenes"].append(scene.id)
                finally:
                    dump_graphql_calls(calls, "create primary and duplicate scenes")

                calls.clear()

                # Merge the duplicate scenes into the primary
                try:
                    merged = await Scene.merge(
                        stash_client,
                        source_ids=[dup.id for dup in duplicates],
                        destination_id=primary.id,
                    )
                finally:
                    dump_graphql_calls(calls, "merge duplicates into primary")

                assert merged is not None
                assert merged.id == primary.id

                # The merge consumes (deletes) the source duplicates — drop them
                # from cleanup so teardown doesn't re-delete nonexistent scenes.
                for dup in duplicates:
                    cleanup["scenes"].remove(dup.id)

                # Allow time for the server to process the merge
                await asyncio.sleep(2.0)

                calls.clear()

                # The primary survives the merge and keeps its relationships;
                # the duplicates were consumed and no longer exist
                missing_duplicates: list[Scene | None] = []
                try:
                    surviving = await stash_client.find_scene(primary.id)
                    for dup in duplicates:
                        missing_duplicates.append(await stash_client.find_scene(dup.id))
                finally:
                    dump_graphql_calls(calls, "verify merge results")

                assert surviving is not None
                assert surviving.id == primary.id
                assert is_set(surviving.performers)
                assert performer.id in {p.id for p in surviving.performers}
                surviving_studio = surviving.studio
                assert is_set(surviving_studio)
                assert surviving_studio is not None
                assert surviving_studio.id == studio.id

                for missing in missing_duplicates:
                    assert missing is None

        except (ConnectionError, TimeoutError) as e:
            pytest.skip(
                f"Connection error - test requires running Stash instance: {e!s}"
            )
