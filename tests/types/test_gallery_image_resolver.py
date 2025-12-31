"""Tests for Gallery.image(index) resolver method."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from stash_graphql_client.types import UNSET
from stash_graphql_client.types.gallery import Gallery
from stash_graphql_client.types.image import Image


@pytest.mark.unit
class TestGalleryImageResolver:
    """Test Gallery.image(index) GraphQL resolver method."""

    @pytest.mark.asyncio
    async def test_image_success(self):
        """Test successful image retrieval by index."""
        # Create gallery with store configured
        gallery = Gallery(id="gallery-123", title="Test Gallery", urls=[])

        # Mock the store and client
        mock_client = AsyncMock()
        mock_store = MagicMock()
        mock_store._client = mock_client

        # Configure Gallery._store class variable
        Gallery._store = mock_store

        # Mock GraphQL response
        mock_client.execute.return_value = {
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

        # Call image resolver
        result = await gallery.image(0)

        # Verify result
        assert isinstance(result, Image)
        assert result.id == "image-456"
        assert result.title == "Test Image"

        # Verify GraphQL query was called
        mock_client.execute.assert_called_once()
        call_args = mock_client.execute.call_args
        assert "GalleryImage" in call_args[0][0]
        assert call_args[0][1] == {"galleryId": "gallery-123", "index": 0}

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
        gallery = Gallery(id="gallery-123", title="Test", urls=[])

        # Ensure no store is configured
        Gallery._store = None

        with pytest.raises(
            RuntimeError, match="Cannot get image: no StashEntityStore configured"
        ):
            await gallery.image(0)

    @pytest.mark.asyncio
    async def test_image_graphql_execution_fails(self):
        """Test that image() raises ValueError when GraphQL execution fails."""
        gallery = Gallery(id="gallery-123", title="Test", urls=[])

        # Mock store with failing client
        mock_client = AsyncMock()
        mock_store = MagicMock()
        mock_store._client = mock_client
        Gallery._store = mock_store

        # Mock GraphQL failure
        mock_client.execute.side_effect = Exception("GraphQL error")

        with pytest.raises(
            ValueError,
            match="Failed to fetch image at index 0 from gallery gallery-123",
        ):
            await gallery.image(0)

    @pytest.mark.asyncio
    async def test_image_gallery_not_found(self):
        """Test that image() raises ValueError when gallery is not found."""
        gallery = Gallery(id="gallery-123", title="Test", urls=[])

        # Mock store and client
        mock_client = AsyncMock()
        mock_store = MagicMock()
        mock_store._client = mock_client
        Gallery._store = mock_store

        # Mock empty GraphQL response (gallery not found)
        mock_client.execute.return_value = {}

        with pytest.raises(ValueError, match="Gallery gallery-123 not found"):
            await gallery.image(0)

    @pytest.mark.asyncio
    async def test_image_not_found_at_index(self):
        """Test that image() raises ValueError when image not found at index."""
        gallery = Gallery(id="gallery-123", title="Test", urls=[])

        # Mock store and client
        mock_client = AsyncMock()
        mock_store = MagicMock()
        mock_store._client = mock_client
        Gallery._store = mock_store

        # Mock GraphQL response with findGallery present but no image
        mock_client.execute.return_value = {
            "findGallery": {"id": "gallery-123"}  # Has gallery but no 'image' key
        }

        with pytest.raises(
            ValueError, match="No image found at index 5 in gallery gallery-123"
        ):
            await gallery.image(5)

    @pytest.mark.asyncio
    async def test_image_with_image_count_in_error_message(self):
        """Test that error message includes image_count when available."""
        gallery = Gallery(id="gallery-123", title="Test", urls=[], image_count=10)

        # Mock store and client
        mock_client = AsyncMock()
        mock_store = MagicMock()
        mock_store._client = mock_client
        Gallery._store = mock_store

        # Mock GraphQL response with findGallery present but no image
        mock_client.execute.return_value = {
            "findGallery": {"id": "gallery-123"}  # Has gallery but no 'image' key
        }

        with pytest.raises(ValueError, match="Gallery has 10 images"):
            await gallery.image(15)

    @pytest.mark.asyncio
    async def test_image_leverages_identity_map(self):
        """Test that image() uses from_graphql() for identity map integration."""
        gallery = Gallery(id="gallery-123", title="Test", urls=[])

        # Mock store and client
        mock_client = AsyncMock()
        mock_store = MagicMock()
        mock_store._client = mock_client
        Gallery._store = mock_store

        # Mock GraphQL response with same image twice
        mock_client.execute.return_value = {
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

        # Call image resolver twice with same index
        result1 = await gallery.image(0)

        # Reset mock to simulate second call
        mock_client.execute.return_value = {
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

        result2 = await gallery.image(0)

        # Both should be valid Image objects
        assert isinstance(result1, Image)
        assert isinstance(result2, Image)
        assert result1.id == result2.id == "image-456"
