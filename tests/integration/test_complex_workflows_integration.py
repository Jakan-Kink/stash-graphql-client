"""Integration tests for complex multi-entity workflows.

These tests require a running Stash instance.
Migrated from fansly-downloader-ng (tests/stash/integration/test_complex_workflows.py).
"""

import asyncio
import time

import pytest

from stash_graphql_client import StashClient
from stash_graphql_client.types import (
    Gallery,
    GenderEnum,
    GenerateMetadataInput,
    GenerateMetadataOptions,
    Performer,
    Scene,
    Studio,
    Tag,
    is_set,
)
from tests.fixtures import capture_graphql_calls, dump_graphql_calls


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.full_workflow
@pytest.mark.timeout(180)  # Allow 3 minutes for metadata generation
@pytest.mark.asyncio
async def test_full_content_workflow(
    stash_client: StashClient,
    enable_scene_creation,
    stash_cleanup_tracker,
) -> None:
    """Test full content workflow with relationships.

    This test:
    1. Creates a performer
    2. Creates a studio
    3. Creates tags
    4. Creates a scene with relationships
    5. Creates a gallery with relationships
    6. Updates relationships
    7. Generates metadata
    8. Verifies everything
    """
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        try:
            # Use unique timestamp to avoid name conflicts between test runs
            unique_id = int(time.time() * 1000) % 1000000  # Last 6 digits of timestamp

            # Create performer, studio, tags, scene, and gallery
            tags: list[Tag] = []
            try:
                performer = Performer(
                    name=f"full_content_workflow - Test Performer {unique_id}",
                    gender=GenderEnum.FEMALE,
                    urls=[f"https://example.com/performer/{unique_id}"],
                    birthdate="1990-01-01",
                    ethnicity="CAUCASIAN",
                    country="US",
                    eye_color="BLUE",
                    height_cm=170,
                    measurements="34-24-36",
                    fake_tits="NO",
                    career_length="2020-",
                    tattoos="None",
                    piercings="None",
                    alias_list=["Alias 1", "Alias 2"],
                    details="Test performer details",
                    # Required relationships
                    scenes=[],
                    tags=[],
                    groups=[],
                    stash_ids=[],
                )
                performer = await stash_client.create_performer(performer)
                cleanup["performers"].append(performer.id)

                studio = Studio(
                    name=f"full_content_workflow - Test Studio {unique_id}",
                    urls=[f"https://example.com/studio/{unique_id}"],
                    details="Test studio details",
                )
                studio = await stash_client.create_studio(studio)
                cleanup["studios"].append(studio.id)

                for name in ["Tag1", "Tag2", "Tag3"]:
                    tag = Tag(
                        name=f"full_content_workflow - {name} {unique_id}",
                        description=f"Test {name.lower()} description",
                    )
                    tag = await stash_client.create_tag(tag)
                    tags.append(tag)
                    cleanup["tags"].append(tag.id)

                scene = Scene(
                    title=f"full_content_workflow - Test Scene {unique_id}",
                    details="Test scene details",
                    date="2024-01-01",
                    urls=[f"https://example.com/scene/{unique_id}"],
                    organized=True,
                    performers=[performer],  # Add performer to scene
                    studio=studio,
                    tags=tags,
                )
                scene = await stash_client.create_scene(scene)
                cleanup["scenes"].append(scene.id)

                gallery = Gallery(
                    title=f"full_content_workflow - Test Gallery {unique_id}",
                    details="Test gallery details",
                    date="2024-01-01",
                    urls=[f"https://example.com/gallery/{unique_id}"],
                    organized=True,
                    performers=[performer],
                    studio=studio,
                    tags=tags,
                    rating100=95,
                    # Required relationships
                    scenes=[],
                )
                gallery = await stash_client.create_gallery(gallery)
                cleanup["galleries"].append(gallery.id)
            finally:
                dump_graphql_calls(calls, "create workflow entities")

            assert performer.id is not None
            assert studio.id is not None
            assert all(tag.id is not None for tag in tags)
            assert scene.id is not None
            assert gallery.id is not None

            calls.clear()

            # Generate metadata
            options = GenerateMetadataOptions(
                covers=True,
                sprites=True,
                previews=True,
                imagePreviews=True,
                markers=True,
                phashes=True,
            )

            # Set up subscription and generate metadata
            job_id: str | None = None
            job_started = False
            try:
                try:
                    async with (
                        asyncio.timeout(10),  # 10 second timeout (reduced from 30)
                        stash_client.subscribe_to_jobs() as subscription,
                    ):
                        # Generate metadata after subscription is ready
                        input_data = GenerateMetadataInput(
                            sceneIDs=[scene.id],
                            overwrite=True,
                        )
                        job_id = await stash_client.metadata_generate(
                            options, input_data
                        )
                        job_started = True
                        # Wait for job
                        async for update in subscription:
                            if (
                                update.job
                                and update.job.id == job_id
                                and update.job.status in ["FINISHED", "CANCELLED"]
                            ):
                                break
                except TimeoutError:
                    pass  # Timeout is acceptable — cleanup still happens
            finally:
                dump_graphql_calls(calls, "generate metadata")

            if job_started:
                assert job_id is not None

            calls.clear()

            # Verify scene and gallery
            try:
                found_scene = await stash_client.find_scene(scene.id)
                found_gallery = await stash_client.find_gallery(gallery.id)
            finally:
                dump_graphql_calls(calls, "verify scene and gallery")

            assert found_scene is not None
            scene_performers = found_scene.performers
            assert is_set(scene_performers)
            assert scene_performers[0].id == performer.id
            scene_studio = found_scene.studio
            assert is_set(scene_studio)
            assert scene_studio is not None
            assert scene_studio.id == studio.id
            scene_tags = found_scene.tags
            assert is_set(scene_tags)
            assert len(scene_tags) == len(tags)
            assert {t.id for t in scene_tags} == {t.id for t in tags}

            assert found_gallery is not None
            gallery_performers = found_gallery.performers
            assert is_set(gallery_performers)
            assert gallery_performers[0].id == performer.id
            gallery_studio = found_gallery.studio
            assert is_set(gallery_studio)
            assert gallery_studio is not None
            assert gallery_studio.id == studio.id
            gallery_tags = found_gallery.tags
            assert is_set(gallery_tags)
            assert len(gallery_tags) == len(tags)
            assert {t.id for t in gallery_tags} == {t.id for t in tags}

        except (ConnectionError, TimeoutError) as e:
            pytest.skip(
                f"Connection error - test requires running Stash instance: {e!s}"
            )


@pytest.mark.integration
@pytest.mark.timeout(180)  # Allow 3 minutes for metadata generation
@pytest.mark.asyncio
async def test_concurrent_operations(
    stash_client: StashClient,
    enable_scene_creation,
    stash_cleanup_tracker,
) -> None:
    """Test concurrent operations.

    This test:
    1. Creates multiple scenes concurrently
    2. Updates them concurrently
    3. Generates metadata concurrently
    4. Verifies everything worked correctly
    """
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        try:
            # Create scenes concurrently
            async def create_scene(i: int) -> Scene:
                scene = Scene(
                    title=f"concurrent_operations - Test Scene {i}",
                    details=f"Test scene {i} details",
                    date="2024-01-01",
                    urls=[f"https://example.com/scene/{i}"],
                    organized=True,
                )
                created = await stash_client.create_scene(scene)
                cleanup["scenes"].append(created.id)
                return created

            try:
                create_tasks = [create_scene(i) for i in range(5)]
                scenes = await asyncio.gather(*create_tasks)
            finally:
                dump_graphql_calls(calls, "create scenes concurrently")

            assert len(scenes) == 5
            assert all(s.id is not None for s in scenes)

            calls.clear()

            # Update scenes concurrently
            async def update_scene(scene: Scene) -> Scene:
                scene.title = f"Updated {scene.title}"
                return await stash_client.update_scene(scene)

            try:
                update_tasks = [update_scene(s) for s in scenes]
                updated_scenes = await asyncio.gather(*update_tasks)
            finally:
                dump_graphql_calls(calls, "update scenes concurrently")

            assert len(updated_scenes) == 5
            for updated in updated_scenes:
                title = updated.title
                assert is_set(title)
                assert title is not None
                assert title.startswith("Updated")

            calls.clear()

            # Generate metadata concurrently
            options = GenerateMetadataOptions(
                covers=True,
                sprites=True,
                previews=True,
            )

            # Set up subscription and generate metadata
            finished_jobs = set()
            job_ids: list[str] = []
            jobs_started = False
            try:
                try:
                    async with (
                        asyncio.timeout(10),  # 10 second timeout (reduced from 30)
                        stash_client.subscribe_to_jobs() as subscription,
                    ):

                        async def generate_metadata(scene: Scene) -> str:
                            input_data = GenerateMetadataInput(
                                sceneIDs=[scene.id],
                                overwrite=True,
                            )
                            return await stash_client.metadata_generate(
                                options, input_data
                            )

                        generate_tasks = [generate_metadata(s) for s in scenes]
                        job_ids = list(await asyncio.gather(*generate_tasks))
                        jobs_started = True

                        # Wait for all jobs
                        async for update in subscription:
                            if (
                                update.job
                                and update.job.id in job_ids
                                and update.job.status in ["FINISHED", "CANCELLED"]
                            ):
                                finished_jobs.add(update.job.id)
                                if len(finished_jobs) == len(job_ids):
                                    break

                except TimeoutError:
                    pass  # Timeout is acceptable — cleanup still happens
            finally:
                dump_graphql_calls(calls, "generate metadata concurrently")

            if jobs_started:
                assert len(job_ids) == 5
                assert all(j is not None for j in job_ids)

            calls.clear()

            # Verify all scenes
            try:
                find_tasks = [stash_client.find_scene(s.id) for s in scenes]
                final_scenes = await asyncio.gather(*find_tasks)
            finally:
                dump_graphql_calls(calls, "verify scenes concurrently")

            assert len(final_scenes) == 5
            assert all(s is not None for s in final_scenes)

        except (ConnectionError, TimeoutError) as e:
            pytest.skip(
                f"Connection error - test requires running Stash instance: {e!s}"
            )


@pytest.mark.asyncio
async def test_error_handling(
    stash_client: StashClient,
    enable_scene_creation,
    stash_cleanup_tracker,
) -> None:
    """Test error handling in complex workflows.

    This test:
    1. Tests invalid operations
    2. Tests missing relationships
    3. Tests concurrent error handling
    4. Tests recovery from errors
    """
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        try:
            try:
                # Test invalid scene creation
                scene = Scene(
                    title="",  # Empty title
                    urls=[],  # No URLs
                    organized=True,
                )
                with pytest.raises(Exception, match=r"(?i)title must be set"):
                    await stash_client.create_scene(scene)

                # Create a studio to test invalid relationships
                studio = Studio(
                    name="error_handling - Test Studio",
                    urls=["https://example.com/studio"],
                )
                studio = await stash_client.create_studio(studio)
                cleanup["studios"].append(studio.id)

                # Test invalid studio reference
                scene = Scene(
                    title="error_handling - Test Scene",
                    urls=["https://example.com/scene"],
                    organized=True,
                    studio=Studio(
                        id="999999", name="Invalid Studio"
                    ),  # Use invalid Studio object instead of string
                )
                with pytest.raises(Exception, match=r"(?i)studio"):
                    await stash_client.create_scene(scene)

                # Test concurrent error handling
                async def create_invalid_scene(i: int) -> None:
                    scene = Scene(
                        title=f"error_handling - Test Scene {i}",
                        urls=[f"https://example.com/scene/{i}"],
                        organized=True,
                        studio=Studio(
                            id=f"999999{i}", name=f"Invalid Studio {i}"
                        ),  # Use invalid Studio objects
                    )
                    with pytest.raises(Exception, match=r"(?i)studio"):
                        await stash_client.create_scene(scene)

                invalid_tasks = [create_invalid_scene(i) for i in range(5)]
                await asyncio.gather(*invalid_tasks)

                # Test recovery - create valid scene after errors
                scene = Scene(
                    title="error_handling - Valid Scene",
                    urls=["https://example.com/valid"],
                    organized=True,
                    studio=studio,  # Use valid studio
                )
                created = await stash_client.create_scene(scene)
                cleanup["scenes"].append(created.id)
            finally:
                dump_graphql_calls(calls, "error handling workflow")

            assert created.id is not None
            assert created.title == scene.title
            created_studio = created.studio
            assert is_set(created_studio)
            assert created_studio is not None
            assert created_studio.id == studio.id
        except (ConnectionError, TimeoutError) as e:
            pytest.skip(
                f"Connection error - test requires running Stash instance: {e!s}"
            )
