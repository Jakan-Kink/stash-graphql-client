"""Integration tests for StashClient against a real Stash instance.

These tests require a running Stash instance at localhost:9999.
The tests are designed to work with any Stash instance that has:
- At least some scenes (for scene tests)
- At least some images (for image tests)
- At least one organized gallery (for gallery tests)

Run with: pytest tests/integration/ -m integration
Skip with: pytest -m "not integration"
"""

import pytest

from stash_graphql_client import StashClient
from stash_graphql_client.types.unset import is_set
from tests.fixtures import capture_graphql_calls, dump_graphql_calls


@pytest.mark.integration
@pytest.mark.requires_scenes
@pytest.mark.asyncio
async def test_find_scenes_returns_expected_count(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test that find_scenes returns consistent count and scenes list length."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        try:
            result = await stash_client.find_scenes()
        finally:
            dump_graphql_calls(calls)

        # Verify GraphQL calls
        assert len(calls) == 1, "Expected 1 GraphQL call for find_scenes"
        assert "findScenes" in calls[0]["query"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Dynamic assertion: count should match scenes list length
        assert is_set(result.scenes)
        assert result.count == len(result.scenes)
        # Sanity check: should have at least some scenes
        assert is_set(result.count)
        assert result.count > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_scenes_with_pagination(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test that pagination works correctly."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        # First query without pagination to get total count
        try:
            full_result = await stash_client.find_scenes()
        finally:
            dump_graphql_calls(calls, "find_scenes (full)")
        assert is_set(full_result.count)
        total_count = full_result.count

        # Verify first call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_scenes (full)"
        assert "findScenes" in calls[0]["query"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        calls.clear()

        # Now test pagination
        try:
            paginated_result = await stash_client.find_scenes(
                filter_={"per_page": 10, "page": 1}
            )
        finally:
            dump_graphql_calls(calls, "find_scenes (paginated)")

        # Verify paginated call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_scenes (paginated)"
        assert "findScenes" in calls[0]["query"]
        assert calls[0]["variables"]["filter"]["per_page"] == 10
        assert calls[0]["variables"]["filter"]["page"] == 1
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Pagination should report same total count (allow +/- 1 for concurrent test activity)
        # Note: Other tests running in parallel may create scenes between queries
        assert is_set(paginated_result.count)
        assert abs(paginated_result.count - total_count) <= 1, (
            f"Count changed significantly between queries: {total_count} -> {paginated_result.count}"
        )
        # But only return requested page size (or less if fewer scenes exist)
        assert is_set(paginated_result.scenes)
        assert len(paginated_result.scenes) <= 10, (
            f"Expected at most 10 scenes, got {len(paginated_result.scenes)}"
        )


@pytest.mark.integration
@pytest.mark.requires_scenes
@pytest.mark.asyncio
async def test_find_scene_by_id(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding a single scene by ID."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        try:
            result = await stash_client.find_scenes(filter_={"per_page": 1})
        finally:
            dump_graphql_calls(calls, "find_scenes")
        assert is_set(result.scenes)
        assert len(result.scenes) > 0

        scene_id = result.scenes[0].id

        # Verify find_scenes call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_scenes"
        assert "findScenes" in calls[0]["query"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        calls.clear()

        try:
            scene = await stash_client.find_scene(scene_id)
        finally:
            dump_graphql_calls(calls, "find_scene")

        # Verify find_scene call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_scene"
        assert "findScene" in calls[0]["query"]
        assert calls[0]["variables"]["id"] == scene_id
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        assert scene is not None
        assert scene.id == scene_id


@pytest.mark.integration
@pytest.mark.requires_images
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="gallery_image")
async def test_find_images_returns_expected_count(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test that find_images returns consistent count and images list length."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        try:
            result = await stash_client.find_images()
        finally:
            dump_graphql_calls(calls)

        # Verify GraphQL calls
        assert len(calls) == 1, "Expected 1 GraphQL call for find_images"
        assert "findImages" in calls[0]["query"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Dynamic assertion: count should match images list length
        assert is_set(result.images)
        assert result.count == len(result.images)
        # Sanity check: should have at least some images
        assert is_set(result.count)
        assert result.count > 0


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="gallery_image")
async def test_find_images_with_pagination(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test that image pagination works correctly."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        # First query without pagination to get total count
        try:
            full_result = await stash_client.find_images()
        finally:
            dump_graphql_calls(calls, "find_images (full)")
        assert is_set(full_result.count)
        total_count = full_result.count

        # Verify first call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_images (full)"
        assert "findImages" in calls[0]["query"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        calls.clear()

        # Now test pagination
        try:
            paginated_result = await stash_client.find_images(
                filter_={"per_page": 50, "page": 1}
            )
        finally:
            dump_graphql_calls(calls, "find_images (paginated)")

        # Verify paginated call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_images (paginated)"
        assert "findImages" in calls[0]["query"]
        assert calls[0]["variables"]["filter"]["per_page"] == 50
        assert calls[0]["variables"]["filter"]["page"] == 1
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Pagination should report same total count
        assert paginated_result.count == total_count
        # But only return requested page size (or less if fewer images exist)
        assert is_set(paginated_result.images)
        assert is_set(paginated_result.count)
        assert len(paginated_result.images) == min(50, paginated_result.count)


@pytest.mark.integration
@pytest.mark.requires_images
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="gallery_image")
async def test_find_image_by_id(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding a single image by ID."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        try:
            result = await stash_client.find_images(filter_={"per_page": 1})
        finally:
            dump_graphql_calls(calls, "find_images")
        assert is_set(result.images)
        assert len(result.images) > 0

        image_id = result.images[0].id

        # Verify find_images call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_images"
        assert "findImages" in calls[0]["query"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        calls.clear()

        try:
            image = await stash_client.find_image(image_id)
        finally:
            dump_graphql_calls(calls, "find_image")

        # Verify find_image call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_image"
        assert "findImage" in calls[0]["query"]
        assert calls[0]["variables"]["id"] == image_id
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        assert image is not None
        assert image.id == image_id


@pytest.mark.integration
@pytest.mark.requires_galleries
@pytest.mark.asyncio
async def test_find_galleries_returns_expected_count(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test that find_galleries returns consistent count and galleries list length."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        try:
            result = await stash_client.find_galleries()
        finally:
            dump_graphql_calls(calls)

        # Verify GraphQL calls
        assert len(calls) == 1, "Expected 1 GraphQL call for find_galleries"
        assert "findGalleries" in calls[0]["query"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Dynamic assertion: count should match galleries list length
        assert is_set(result.galleries)
        assert result.count == len(result.galleries)
        # Sanity check: should have at least some galleries
        assert is_set(result.count)
        assert result.count > 0


@pytest.mark.integration
@pytest.mark.requires_galleries
@pytest.mark.asyncio
async def test_find_gallery_by_id(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding a single gallery by ID."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        try:
            result = await stash_client.find_galleries()
        finally:
            dump_graphql_calls(calls, "find_galleries")
        assert len(result.galleries) > 0

        gallery_id = result.galleries[0].id

        # Verify find_galleries call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_galleries"
        assert "findGalleries" in calls[0]["query"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        calls.clear()

        try:
            gallery = await stash_client.find_gallery(gallery_id)
        finally:
            dump_graphql_calls(calls, "find_gallery")

        # Verify find_gallery call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_gallery"
        assert "findGallery" in calls[0]["query"]
        assert calls[0]["variables"]["id"] == gallery_id
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        assert gallery is not None
        assert gallery.id == gallery_id


@pytest.mark.integration
@pytest.mark.requires_galleries
@pytest.mark.asyncio
async def test_gallery_is_organized(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test that at least one gallery has organized=True."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        try:
            result = await stash_client.find_galleries()
        finally:
            dump_graphql_calls(calls)

        # Verify GraphQL calls
        assert len(calls) == 1, "Expected 1 GraphQL call for find_galleries"
        assert "findGalleries" in calls[0]["query"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # At least one gallery should be organized
        assert is_set(result.galleries)
        assert len(result.galleries) > 0, "Expected at least one gallery"
        organized_galleries = [g for g in result.galleries if g.organized is True]
        assert len(organized_galleries) > 0, "Expected at least one organized gallery"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_nonexistent_scene_returns_none(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test that finding a nonexistent scene returns None."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        try:
            scene = await stash_client.find_scene("99999999")
        finally:
            dump_graphql_calls(calls)

        # Verify GraphQL calls
        assert len(calls) == 1, "Expected 1 GraphQL call for find_scene"
        assert "findScene" in calls[0]["query"]
        assert calls[0]["variables"]["id"] == "99999999"
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        assert scene is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_nonexistent_image_returns_none(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test that finding a nonexistent image returns None."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        try:
            image = await stash_client.find_image("99999999")
        finally:
            dump_graphql_calls(calls)

        # Verify GraphQL calls
        assert len(calls) == 1, "Expected 1 GraphQL call for find_image"
        assert "findImage" in calls[0]["query"]
        assert calls[0]["variables"]["id"] == "99999999"
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        assert image is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_nonexistent_gallery_returns_none(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test that finding a nonexistent gallery returns None."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        try:
            gallery = await stash_client.find_gallery("99999999")
        finally:
            dump_graphql_calls(calls)

        # Verify GraphQL calls
        assert len(calls) == 1, "Expected 1 GraphQL call for find_gallery"
        assert "findGallery" in calls[0]["query"]
        assert calls[0]["variables"]["id"] == "99999999"
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        assert gallery is None
