"""Integration tests for gallery mixin functionality.

Tests gallery operations against a real Stash instance with GraphQL call verification.

These tests cover the core gallery CRUD operations, chapters, image management,
and gallery-specific features like bulk operations and cover image handling.
"""

import pytest

from stash_graphql_client import StashClient
from stash_graphql_client.types import Gallery, GalleryChapter
from tests.fixtures import capture_graphql_calls


# =============================================================================
# Gallery Read Integration Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_galleries_returns_results(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding galleries returns results (may be empty)."""
    async with (
        stash_cleanup_tracker(stash_client),
        capture_graphql_calls(stash_client) as calls,
    ):
        result = await stash_client.find_galleries()

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_galleries"
        assert "findGalleries" in calls[0]["query"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Result should be valid even if empty
        assert result.count >= 0
        assert isinstance(result.galleries, list)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_galleries_with_pagination(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test gallery pagination works correctly."""
    async with (
        stash_cleanup_tracker(stash_client),
        capture_graphql_calls(stash_client) as calls,
    ):
        result = await stash_client.find_galleries(filter_={"per_page": 10, "page": 1})

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_galleries"
        assert "findGalleries" in calls[0]["query"]
        assert calls[0]["variables"]["filter"]["per_page"] == 10
        assert calls[0]["variables"]["filter"]["page"] == 1
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify response
        assert len(result.galleries) <= 10


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_nonexistent_gallery_returns_none(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding a nonexistent gallery returns None."""
    async with (
        stash_cleanup_tracker(stash_client),
        capture_graphql_calls(stash_client) as calls,
    ):
        gallery = await stash_client.find_gallery("99999999")

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_gallery"
        assert "findGallery" in calls[0]["query"]
        assert calls[0]["variables"]["id"] == "99999999"
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify response
        assert gallery is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_galleries_with_q_parameter(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding galleries using q search parameter."""
    async with (
        stash_cleanup_tracker(stash_client),
        capture_graphql_calls(stash_client) as calls,
    ):
        result = await stash_client.find_galleries(q="test")

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_galleries"
        assert "findGalleries" in calls[0]["query"]
        # q parameter is added to filter dict
        assert calls[0]["variables"]["filter"]["q"] == "test"
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Should return valid result (may or may not have matches)
        assert result.count >= 0
        assert isinstance(result.galleries, list)


# =============================================================================
# Gallery CRUD Integration Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_and_find_gallery(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test creating a gallery and finding it."""
    async with (
        stash_cleanup_tracker(stash_client) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        # Create a new gallery
        new_gallery = Gallery.new(
            title="Integration Test Gallery",
        )

        created_gallery = await stash_client.create_gallery(new_gallery)
        cleanup["galleries"].append(created_gallery.id)

        # Verify creation call
        assert len(calls) == 1, "Expected 1 GraphQL call for create_gallery"
        assert "galleryCreate" in calls[0]["query"]
        assert calls[0]["variables"]["input"]["title"] == "Integration Test Gallery"
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify created gallery
        assert created_gallery is not None
        assert isinstance(created_gallery, Gallery)
        assert created_gallery.id is not None
        assert created_gallery.title == "Integration Test Gallery"

        # Clear calls and verify we can find it
        calls.clear()
        found_gallery = await stash_client.find_gallery(created_gallery.id)

        assert len(calls) == 1, "Expected 1 GraphQL call for find_gallery"
        assert "findGallery" in calls[0]["query"]
        assert found_gallery.id == created_gallery.id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_and_update_gallery(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test creating and updating a gallery."""
    async with (
        stash_cleanup_tracker(stash_client) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        # Create gallery
        new_gallery = Gallery.new(
            title="Test Gallery Before Update",
        )

        created_gallery = await stash_client.create_gallery(new_gallery)
        cleanup["galleries"].append(created_gallery.id)

        # Verify creation
        assert len(calls) == 1
        assert "galleryCreate" in calls[0]["query"]
        calls.clear()

        # Update the gallery
        created_gallery.title = "Test Gallery After Update"
        created_gallery.rating100 = 80

        updated_gallery = await stash_client.update_gallery(created_gallery)

        # Verify update call
        assert len(calls) == 1, "Expected 1 GraphQL call for update_gallery"
        assert "galleryUpdate" in calls[0]["query"]
        assert calls[0]["variables"]["input"]["id"] == created_gallery.id
        assert calls[0]["variables"]["input"]["title"] == "Test Gallery After Update"
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify updated gallery
        assert updated_gallery.id == created_gallery.id
        assert updated_gallery.title == "Test Gallery After Update"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_and_destroy_gallery(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test creating and destroying a gallery."""
    async with (
        stash_cleanup_tracker(stash_client) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        # Create gallery
        new_gallery = Gallery.new(title="Gallery to be destroyed")
        created_gallery = await stash_client.create_gallery(new_gallery)
        cleanup["galleries"].append(created_gallery.id)
        gallery_id = created_gallery.id

        # Verify creation
        assert len(calls) == 1
        calls.clear()

        # Destroy the gallery
        success = await stash_client.gallery_destroy(
            [gallery_id],
            delete_file=False,
            delete_generated=False,
        )

        # Verify destroy call
        assert len(calls) == 1, "Expected 1 GraphQL call for gallery_destroy"
        assert "galleryDestroy" in calls[0]["query"]
        assert calls[0]["variables"]["input"]["ids"] == [gallery_id]
        assert calls[0]["variables"]["input"]["delete_file"] is False
        assert calls[0]["exception"] is None

        # Verify destruction
        assert success is True
        cleanup["galleries"].remove(gallery_id)

        # Verify it's gone
        calls.clear()
        found_gallery = await stash_client.find_gallery(gallery_id)
        assert found_gallery is None


# =============================================================================
# Gallery Update Bulk Integration Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_galleries_update_multiple(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test updating multiple galleries individually."""
    async with (
        stash_cleanup_tracker(stash_client) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        # Create multiple test galleries
        gallery1 = Gallery.new(title="Multi Update Test 1")
        gallery2 = Gallery.new(title="Multi Update Test 2")

        created1 = await stash_client.create_gallery(gallery1)
        created2 = await stash_client.create_gallery(gallery2)
        cleanup["galleries"].extend([created1.id, created2.id])

        calls.clear()

        # Update both galleries
        created1.title = "Multi Update Test 1 Updated"
        created1.rating100 = 50
        created2.title = "Multi Update Test 2 Updated"
        created2.rating100 = 75

        updated_galleries = await stash_client.galleries_update([created1, created2])

        # Verify update call
        assert len(calls) == 1, "Expected 1 GraphQL call for galleries_update"
        assert "galleriesUpdate" in calls[0]["query"]
        assert len(calls[0]["variables"]["input"]) == 2
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify result
        assert len(updated_galleries) == 2
        titles = {g.title for g in updated_galleries}
        assert "Multi Update Test 1 Updated" in titles
        assert "Multi Update Test 2 Updated" in titles


# =============================================================================
# Gallery Cover Image Integration Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_images
async def test_set_and_reset_gallery_cover(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test setting and resetting gallery cover image."""
    async with (
        stash_cleanup_tracker(stash_client) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        # Create a test gallery
        new_gallery = Gallery.new(title="Test Gallery for Cover")
        created_gallery = await stash_client.create_gallery(new_gallery)
        cleanup["galleries"].append(created_gallery.id)

        calls.clear()

        # Fetch real images from Stash
        images_result = await stash_client.find_images(filter_={"per_page": 1})
        cover_image_id = images_result.images[0].id if images_result.images else None
        calls.clear()

        if cover_image_id:
            # Set a cover image using a real image ID
            await stash_client.set_gallery_cover(
                created_gallery.id,
                cover_image_id,
            )

            # Verify set cover call
            assert len(calls) == 1, "Expected 1 GraphQL call for set_gallery_cover"
            assert "setGalleryCover" in calls[0]["query"]
            assert calls[0]["variables"]["input"]["gallery_id"] == created_gallery.id
            assert calls[0]["variables"]["input"]["cover_image_id"] == cover_image_id
            assert calls[0]["exception"] is None

            calls.clear()

        # Reset the cover image
        await stash_client.reset_gallery_cover(created_gallery.id)

        # Verify reset cover call
        assert len(calls) == 1, "Expected 1 GraphQL call for reset_gallery_cover"
        assert "resetGalleryCover" in calls[0]["query"]
        assert calls[0]["variables"]["input"]["gallery_id"] == created_gallery.id
        assert calls[0]["exception"] is None


# =============================================================================
# Gallery Image Management Integration Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_images
async def test_add_and_remove_gallery_images(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test adding and removing images from a gallery."""
    async with (
        stash_cleanup_tracker(stash_client) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        # Create a test gallery
        new_gallery = Gallery.new(title="Test Gallery for Images")
        created_gallery = await stash_client.create_gallery(new_gallery)
        cleanup["galleries"].append(created_gallery.id)

        calls.clear()

        # Fetch real images from Stash
        images_result = await stash_client.find_images(filter_={"per_page": 2})
        image_ids = [img.id for img in images_result.images[:2]]
        calls.clear()

        # Add images to gallery
        await stash_client.add_gallery_images(
            created_gallery.id,
            image_ids,
        )

        # Verify add images call
        assert len(calls) == 1, "Expected 1 GraphQL call for add_gallery_images"
        assert "addGalleryImages" in calls[0]["query"]
        assert calls[0]["variables"]["input"]["gallery_id"] == created_gallery.id
        assert calls[0]["variables"]["input"]["image_ids"] == image_ids
        assert calls[0]["exception"] is None

        calls.clear()

        # Remove images from gallery
        await stash_client.remove_gallery_images(
            created_gallery.id,
            [image_ids[0]],
        )

        # Verify remove images call
        assert len(calls) == 1, "Expected 1 GraphQL call for remove_gallery_images"
        assert "removeGalleryImages" in calls[0]["query"]
        assert calls[0]["variables"]["input"]["gallery_id"] == created_gallery.id
        assert calls[0]["variables"]["input"]["image_ids"] == [image_ids[0]]
        assert calls[0]["exception"] is None


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_images
async def test_update_gallery_images_add_mode(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test updating gallery images in ADD mode."""
    async with (
        stash_cleanup_tracker(stash_client) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        # Create a test gallery
        new_gallery = Gallery.new(title="Test Gallery for Image Update ADD")
        created_gallery = await stash_client.create_gallery(new_gallery)
        cleanup["galleries"].append(created_gallery.id)

        calls.clear()

        # Fetch real images from Stash
        images_result = await stash_client.find_images(filter_={"per_page": 1})
        image_ids = [img.id for img in images_result.images[:1]]
        calls.clear()

        # Update gallery images in ADD mode
        await stash_client.update_gallery_images(
            created_gallery.id,
            image_ids,
            mode="ADD",
        )

        # Verify call
        assert len(calls) == 1, "Expected 1 GraphQL call for update_gallery_images"
        assert "addGalleryImages" in calls[0]["query"]
        assert calls[0]["variables"]["input"]["image_ids"] == image_ids
        assert calls[0]["exception"] is None


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_images
async def test_update_gallery_images_remove_mode(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test updating gallery images in REMOVE mode."""
    async with (
        stash_cleanup_tracker(stash_client) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        # Create a test gallery
        new_gallery = Gallery.new(title="Test Gallery for Image Update REMOVE")
        created_gallery = await stash_client.create_gallery(new_gallery)
        cleanup["galleries"].append(created_gallery.id)

        calls.clear()

        # Fetch real images from Stash to add first
        images_result = await stash_client.find_images(filter_={"per_page": 1})
        image_ids = [img.id for img in images_result.images[:1]]
        calls.clear()

        # Update gallery images in REMOVE mode
        await stash_client.update_gallery_images(
            created_gallery.id,
            image_ids,
            mode="REMOVE",
        )

        # Verify call
        assert len(calls) == 1, "Expected 1 GraphQL call for update_gallery_images"
        assert "removeGalleryImages" in calls[0]["query"]
        assert calls[0]["variables"]["input"]["image_ids"] == image_ids
        assert calls[0]["exception"] is None


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_images
async def test_update_gallery_images_set_mode(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test updating gallery images in SET mode (adds via addGalleryImages)."""
    async with (
        stash_cleanup_tracker(stash_client) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        # Create a test gallery
        new_gallery = Gallery.new(title="Test Gallery for Image Update SET")
        created_gallery = await stash_client.create_gallery(new_gallery)
        cleanup["galleries"].append(created_gallery.id)

        calls.clear()

        # Fetch real images from Stash
        images_result = await stash_client.find_images(filter_={"per_page": 2})
        image_ids = [img.id for img in images_result.images[:2]]
        calls.clear()

        # Update gallery images in SET mode
        await stash_client.update_gallery_images(
            created_gallery.id,
            image_ids,
            mode="SET",
        )

        # Verify call (SET mode uses addGalleryImages)
        assert len(calls) == 1, "Expected 1 GraphQL call for update_gallery_images"
        assert "addGalleryImages" in calls[0]["query"]
        assert calls[0]["variables"]["input"]["image_ids"] == image_ids
        assert calls[0]["exception"] is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_gallery_images_invalid_mode(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test updating gallery images with invalid mode raises error."""
    async with (
        stash_cleanup_tracker(stash_client) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        # Create a test gallery
        new_gallery = Gallery.new(title="Test Gallery for Invalid Mode")
        created_gallery = await stash_client.create_gallery(new_gallery)
        cleanup["galleries"].append(created_gallery.id)

        calls.clear()

        # Attempt invalid mode
        with pytest.raises(ValueError, match="mode must be one of"):
            await stash_client.update_gallery_images(
                created_gallery.id,
                ["test_image"],
                mode="INVALID",
            )


# =============================================================================
# Gallery Chapter Integration Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_images
async def test_create_and_destroy_gallery_chapter(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test creating and destroying a gallery chapter."""
    async with (
        stash_cleanup_tracker(stash_client) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        # Create a test gallery
        new_gallery = Gallery.new(title="Test Gallery for Chapters")
        created_gallery = await stash_client.create_gallery(new_gallery)
        cleanup["galleries"].append(created_gallery.id)

        calls.clear()

        # Fetch real images and add to gallery first
        images_result = await stash_client.find_images(filter_={"per_page": 1})
        if images_result.images:
            image_ids = [img.id for img in images_result.images[:1]]
            await stash_client.add_gallery_images(created_gallery.id, image_ids)
            calls.clear()

            # Create a chapter (image_index must be > 0, chapters are 1-indexed)
            chapter = await stash_client.gallery_chapter_create(
                gallery_id=created_gallery.id,
                title="Chapter 1",
                image_index=1,
            )

            # Verify create chapter call
            assert len(calls) == 1, "Expected 1 GraphQL call for gallery_chapter_create"
            assert "galleryChapterCreate" in calls[0]["query"]
            assert calls[0]["variables"]["input"]["gallery_id"] == created_gallery.id
            assert calls[0]["variables"]["input"]["title"] == "Chapter 1"
            assert calls[0]["variables"]["input"]["image_index"] == 1
            assert calls[0]["result"] is not None
            assert calls[0]["exception"] is None

            # Verify chapter
            assert isinstance(chapter, GalleryChapter)
            assert chapter.id is not None
            assert chapter.title == "Chapter 1"

            chapter_id = chapter.id
            calls.clear()

            # Destroy the chapter
            await stash_client.gallery_chapter_destroy(chapter_id)

            # Verify destroy chapter call
            assert len(calls) == 1, (
                "Expected 1 GraphQL call for gallery_chapter_destroy"
            )
            assert "galleryChapterDestroy" in calls[0]["query"]
            assert calls[0]["variables"]["id"] == chapter_id
            assert calls[0]["exception"] is None


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_images
async def test_create_and_update_gallery_chapter(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test creating and updating a gallery chapter."""
    async with (
        stash_cleanup_tracker(stash_client) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        # Create a test gallery
        new_gallery = Gallery.new(title="Test Gallery for Chapter Update")
        created_gallery = await stash_client.create_gallery(new_gallery)
        cleanup["galleries"].append(created_gallery.id)

        calls.clear()

        # Fetch real images and add to gallery first
        images_result = await stash_client.find_images(filter_={"per_page": 5})
        if images_result.images:
            image_ids = [img.id for img in images_result.images[:5]]
            await stash_client.add_gallery_images(created_gallery.id, image_ids)
            calls.clear()

            # Create a chapter (image_index must be > 0, chapters are 1-indexed)
            chapter = await stash_client.gallery_chapter_create(
                gallery_id=created_gallery.id,
                title="Chapter 1",
                image_index=1,
            )

            assert len(calls) == 1
            calls.clear()

            # Update the chapter (use a valid image index from our added images)
            updated_chapter = await stash_client.gallery_chapter_update(
                id=chapter.id,
                title="Chapter 1 Updated",
                image_index=5,
            )

            # Verify update chapter call
            assert len(calls) == 1, "Expected 1 GraphQL call for gallery_chapter_update"
            assert "galleryChapterUpdate" in calls[0]["query"]
            assert calls[0]["variables"]["input"]["id"] == chapter.id
            assert calls[0]["variables"]["input"]["title"] == "Chapter 1 Updated"
            assert calls[0]["variables"]["input"]["image_index"] == "5"
            assert calls[0]["result"] is not None
            assert calls[0]["exception"] is None

            # Verify updates
            assert updated_chapter.id == chapter.id
            assert updated_chapter.title == "Chapter 1 Updated"


# =============================================================================
# Gallery Bulk Operations Integration Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_bulk_gallery_update(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test bulk updating galleries."""
    async with (
        stash_cleanup_tracker(stash_client) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        # Create multiple test galleries
        gallery1 = Gallery.new(title="Bulk Test Gallery 1")
        gallery2 = Gallery.new(title="Bulk Test Gallery 2")

        created1 = await stash_client.create_gallery(gallery1)
        created2 = await stash_client.create_gallery(gallery2)
        cleanup["galleries"].extend([created1.id, created2.id])

        calls.clear()

        # Bulk update both galleries
        updated_galleries = await stash_client.bulk_gallery_update(
            {
                "ids": [created1.id, created2.id],
                "organized": True,
                "rating100": 85,
            }
        )

        # Verify bulk update call
        assert len(calls) == 1, "Expected 1 GraphQL call for bulk_gallery_update"
        assert "bulkGalleryUpdate" in calls[0]["query"]
        assert calls[0]["variables"]["input"]["ids"] == [created1.id, created2.id]
        assert calls[0]["variables"]["input"]["organized"] is True
        assert calls[0]["variables"]["input"]["rating100"] == 85
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify result
        assert len(updated_galleries) == 2
        assert all(g.organized is True for g in updated_galleries)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_gallery_destroy_multiple(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test destroying multiple galleries at once."""
    async with (
        stash_cleanup_tracker(stash_client) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        # Create multiple test galleries
        gallery1 = Gallery.new(title="Multi Destroy Test Gallery 1")
        gallery2 = Gallery.new(title="Multi Destroy Test Gallery 2")

        created1 = await stash_client.create_gallery(gallery1)
        created2 = await stash_client.create_gallery(gallery2)
        gallery_ids = [created1.id, created2.id]
        cleanup["galleries"].extend(gallery_ids)

        calls.clear()

        # Destroy both galleries
        success = await stash_client.gallery_destroy(
            gallery_ids,
            delete_file=False,
            delete_generated=False,
        )

        # Verify destroy call
        assert len(calls) == 1, "Expected 1 GraphQL call for gallery_destroy"
        assert "galleryDestroy" in calls[0]["query"]
        assert calls[0]["variables"]["input"]["ids"] == gallery_ids
        assert calls[0]["variables"]["input"]["delete_file"] is False
        assert calls[0]["exception"] is None

        # Verify destruction
        assert success is True
        for gallery_id in gallery_ids:
            cleanup["galleries"].remove(gallery_id)

        # Verify they're gone
        calls.clear()
        found1 = await stash_client.find_gallery(created1.id)
        found2 = await stash_client.find_gallery(created2.id)
        assert found1 is None
        assert found2 is None
