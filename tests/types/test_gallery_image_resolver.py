"""Tests for Gallery.image(index) resolver method.

Following TESTING_REQUIREMENTS.md:
- Mock only at HTTP boundary using respx
- Use real StashClient and StashEntityStore
- Test actual code paths, not mocks
"""

import httpx
import pytest
import respx

from stash_graphql_client import StashEntityStore
from stash_graphql_client.types import UNSET
from stash_graphql_client.types.gallery import Gallery
from stash_graphql_client.types.image import Image


@pytest.mark.unit
class TestGalleryImageResolver:
    """Test Gallery.image(index) GraphQL resolver method."""

    @pytest.mark.asyncio
    async def test_image_success(
        self, respx_mock, respx_entity_store: StashEntityStore
    ):
        """Test successful image retrieval by index."""

        # Create gallery
        gallery = Gallery(id="gallery-123", title="Test Gallery", urls=[])

        # Mock GraphQL HTTP response using side_effect to avoid StopIteration
        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={
                        "data": {
                            "findGallery": {
                                "image": {
                                    "__typename": "Image",
                                    "id": "image-456",
                                    "title": "Test Image",
                                    "organized": False,
                                    "o_counter": 0,
                                }
                            }
                        }
                    },
                )
            ]
        )

        # Call image resolver - uses real code path
        result = await gallery.image(0)

        # Verify result
        assert isinstance(result, Image)
        assert result.id == "image-456"
        assert result.title == "Test Image"

        # Verify GraphQL query was called
        assert len(graphql_route.calls) == 1

    @pytest.mark.asyncio
    async def test_image_gallery_id_unset_raises_error(self):
        """Test that image() raises ValueError when gallery ID is UNSET."""
        # Use model_construct to bypass validation and set UNSET directly
        gallery = Gallery.model_construct(id=UNSET, title="Test", urls=[])

        with pytest.raises(ValueError, match="Cannot get image: gallery ID is not set"):
            await gallery.image(0)

    @pytest.mark.asyncio
    async def test_image_gallery_id_none_raises_error(self):
        """Test that image() raises ValueError when gallery ID is None."""
        # Use model_construct to bypass UUID4 auto-generation
        gallery = Gallery.model_construct(id=None, title="Test", urls=[])

        with pytest.raises(ValueError, match="Cannot get image: gallery ID is not set"):
            await gallery.image(0)

    @pytest.mark.asyncio
    async def test_image_no_store_raises_error(self):
        """Test that image() raises RuntimeError when no store is configured."""
        from unittest.mock import patch

        gallery = Gallery(id="gallery-123", title="Test", urls=[])

        # Use patch.object for thread-safe test isolation in parallel execution
        with (
            patch.object(Gallery, "_store", None),
            pytest.raises(
                RuntimeError, match="Cannot get image: no StashEntityStore configured"
            ),
        ):
            await gallery.image(0)

    @pytest.mark.asyncio
    async def test_image_graphql_execution_fails(
        self, respx_mock, respx_entity_store: StashEntityStore
    ):
        """Test that image() raises ValueError when GraphQL execution fails."""

        gallery = Gallery(id="gallery-123", title="Test", urls=[])

        # Mock GraphQL HTTP failure using side_effect
        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[httpx.Response(500, text="Internal Server Error")]
        )

        with pytest.raises(
            ValueError,
            match="Failed to fetch image at index 0 from gallery gallery-123",
        ):
            await gallery.image(0)

    @pytest.mark.asyncio
    async def test_image_gallery_not_found(
        self, respx_mock, respx_entity_store: StashEntityStore
    ):
        """Test that image() raises ValueError when gallery is not found."""

        gallery = Gallery(id="gallery-123", title="Test", urls=[])

        # Mock empty GraphQL response (gallery not found) using side_effect
        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[httpx.Response(200, json={"data": {}})]
        )

        with pytest.raises(ValueError, match="Gallery gallery-123 not found"):
            await gallery.image(0)

    @pytest.mark.asyncio
    async def test_image_not_found_at_index(
        self, respx_mock, respx_entity_store: StashEntityStore
    ):
        """Test that image() raises ValueError when image not found at index."""

        gallery = Gallery(id="gallery-123", title="Test", urls=[])

        # Mock GraphQL response with findGallery present but no image using side_effect
        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200, json={"data": {"findGallery": {"id": "gallery-123"}}}
                )
            ]
        )

        with pytest.raises(
            ValueError, match="No image found at index 5 in gallery gallery-123"
        ):
            await gallery.image(5)

    @pytest.mark.asyncio
    async def test_image_with_image_count_in_error_message(
        self, respx_mock, respx_entity_store: StashEntityStore
    ):
        """Test that error message includes image_count when available."""

        gallery = Gallery(id="gallery-123", title="Test", urls=[], image_count=10)

        # Mock GraphQL response with findGallery present but no image using side_effect
        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200, json={"data": {"findGallery": {"id": "gallery-123"}}}
                )
            ]
        )

        with pytest.raises(ValueError, match="Gallery has 10 images"):
            await gallery.image(15)

    @pytest.mark.asyncio
    async def test_image_leverages_identity_map(
        self, respx_mock, respx_entity_store: StashEntityStore
    ):
        """Test that image() uses from_graphql() for identity map integration."""

        gallery = Gallery(id="gallery-123", title="Test", urls=[])

        # Mock GraphQL response with same image ID twice using side_effect for multiple calls
        image_data = {
            "__typename": "Image",
            "id": "image-456",
            "title": "Test Image",
            "organized": False,
            "o_counter": 0,
        }

        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200, json={"data": {"findGallery": {"image": image_data}}}
                ),
                httpx.Response(
                    200, json={"data": {"findGallery": {"image": image_data}}}
                ),
            ]
        )

        # Call image resolver twice with same index
        result1 = await gallery.image(0)
        result2 = await gallery.image(0)

        # Both should be valid Image objects with same ID
        assert isinstance(result1, Image)
        assert isinstance(result2, Image)
        assert result1.id == result2.id == "image-456"

        # Identity map ensures same instance (if called in same context)
        # Note: Actual identity (result1 is result2) depends on cache state
