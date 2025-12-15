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


@pytest.mark.integration
@pytest.mark.requires_scenes
@pytest.mark.asyncio
async def test_find_scenes_returns_expected_count(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test that find_scenes returns consistent count and scenes list length."""
    async with stash_cleanup_tracker(stash_client, auto_capture=False):
        result = await stash_client.find_scenes()

        # Dynamic assertion: count should match scenes list length
        assert result.count == len(result.scenes)
        # Sanity check: should have at least some scenes
        assert result.count > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_scenes_with_pagination(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test that pagination works correctly."""
    async with stash_cleanup_tracker(stash_client, auto_capture=False):
        # First query without pagination to get total count
        full_result = await stash_client.find_scenes()
        total_count = full_result.count

        # Now test pagination
        paginated_result = await stash_client.find_scenes(
            filter_={"per_page": 10, "page": 1}
        )

        # Pagination should report same total count
        assert paginated_result.count == total_count
        # But only return requested page size (or less if fewer scenes exist)
        assert len(paginated_result.scenes) == min(10, total_count)


@pytest.mark.integration
@pytest.mark.requires_scenes
@pytest.mark.asyncio
async def test_find_scene_by_id(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding a single scene by ID."""
    async with stash_cleanup_tracker(stash_client, auto_capture=False):
        result = await stash_client.find_scenes(filter_={"per_page": 1})
        assert len(result.scenes) > 0

        scene_id = result.scenes[0].id
        scene = await stash_client.find_scene(scene_id)

        assert scene is not None
        assert scene.id == scene_id


@pytest.mark.integration
@pytest.mark.requires_images
@pytest.mark.asyncio
async def test_find_images_returns_expected_count(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test that find_images returns consistent count and images list length."""
    async with stash_cleanup_tracker(stash_client, auto_capture=False):
        result = await stash_client.find_images()

        # Dynamic assertion: count should match images list length
        assert result.count == len(result.images)
        # Sanity check: should have at least some images
        assert result.count > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_images_with_pagination(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test that image pagination works correctly."""
    async with stash_cleanup_tracker(stash_client, auto_capture=False):
        # First query without pagination to get total count
        full_result = await stash_client.find_images()
        total_count = full_result.count

        # Now test pagination
        paginated_result = await stash_client.find_images(
            filter_={"per_page": 50, "page": 1}
        )

        # Pagination should report same total count
        assert paginated_result.count == total_count
        # But only return requested page size (or less if fewer images exist)
        assert len(paginated_result.images) == min(50, total_count)


@pytest.mark.integration
@pytest.mark.requires_images
@pytest.mark.asyncio
async def test_find_image_by_id(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding a single image by ID."""
    async with stash_cleanup_tracker(stash_client, auto_capture=False):
        result = await stash_client.find_images(filter_={"per_page": 1})
        assert len(result.images) > 0

        image_id = result.images[0].id
        image = await stash_client.find_image(image_id)

        assert image is not None
        assert image.id == image_id


@pytest.mark.integration
@pytest.mark.requires_galleries
@pytest.mark.asyncio
async def test_find_galleries_returns_expected_count(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test that find_galleries returns the 1 gallery from test Stash."""
    async with stash_cleanup_tracker(stash_client, auto_capture=False):
        result = await stash_client.find_galleries()

        assert result.count == 1
        assert len(result.galleries) == 1


@pytest.mark.integration
@pytest.mark.requires_galleries
@pytest.mark.asyncio
async def test_find_gallery_by_id(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding a single gallery by ID."""
    async with stash_cleanup_tracker(stash_client, auto_capture=False):
        result = await stash_client.find_galleries()
        assert len(result.galleries) > 0

        gallery_id = result.galleries[0].id
        gallery = await stash_client.find_gallery(gallery_id)

        assert gallery is not None
        assert gallery.id == gallery_id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_gallery_is_organized(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test that the gallery has organized=True."""
    async with stash_cleanup_tracker(stash_client, auto_capture=False):
        result = await stash_client.find_galleries()

        assert result.galleries[0].organized is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_nonexistent_scene_returns_none(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test that finding a nonexistent scene returns None."""
    async with stash_cleanup_tracker(stash_client, auto_capture=False):
        scene = await stash_client.find_scene("99999999")

        assert scene is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_nonexistent_image_returns_none(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test that finding a nonexistent image returns None."""
    async with stash_cleanup_tracker(stash_client, auto_capture=False):
        image = await stash_client.find_image("99999999")

        assert image is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_nonexistent_gallery_returns_none(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test that finding a nonexistent gallery returns None."""
    async with stash_cleanup_tracker(stash_client, auto_capture=False):
        gallery = await stash_client.find_gallery("99999999")

        assert gallery is None
