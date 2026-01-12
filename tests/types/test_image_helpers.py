"""Tests for Image helper methods.

These tests verify that the helper methods:
1. Modify relationships in-memory only (DON'T call save())
2. Are asynchronous (async)
"""

import inspect

import pytest

from stash_graphql_client.types import UNSET, UnsetType, is_set
from stash_graphql_client.types.gallery import Gallery
from stash_graphql_client.types.image import Image
from stash_graphql_client.types.performer import Performer
from stash_graphql_client.types.tag import Tag


@pytest.mark.usefixtures("mock_entity_store")
class TestImageHelperMethods:
    """Test Image convenience helper methods."""

    @pytest.mark.asyncio
    async def test_add_performer(self):
        """Test that add_performer adds performer to image.performers list."""
        image = Image(id="1", title="Image 1", performers=[], urls=[])
        performer = Performer(id="2", name="Performer 1")

        # Add performer (async method now, uses generic machinery)
        await image.add_performer(performer)

        # Verify performer was added
        assert is_set(image.performers)
        assert performer in image.performers

    @pytest.mark.asyncio
    async def test_add_performer_deduplication(self):
        """Test that add_performer doesn't create duplicates."""
        image = Image(id="1", title="Image 1", performers=[], urls=[])
        performer = Performer(id="2", name="Performer 1")

        # Add same performer twice
        await image.add_performer(performer)
        await image.add_performer(performer)

        # Should only have one entry
        assert is_set(image.performers)
        assert len(image.performers) == 1

    @pytest.mark.asyncio
    async def test_remove_performer(self):
        """Test that remove_performer removes performer from image.performers list."""
        performer = Performer(id="2", name="Performer 1")
        image = Image(id="1", title="Image 1", performers=[performer], urls=[])

        # Remove performer (async method now, uses generic machinery)
        await image.remove_performer(performer)

        # Verify performer was removed
        assert is_set(image.performers)
        assert performer not in image.performers

    @pytest.mark.asyncio
    async def test_remove_performer_noop_if_not_present(self):
        """Test that remove_performer is no-op if performer not in list."""
        image = Image(id="1", title="Image 1", performers=[], urls=[])
        performer = Performer(id="2", name="Performer 1")

        # Remove performer that's not in the list - should be no-op
        await image.remove_performer(performer)

        assert is_set(image.performers)
        assert performer not in image.performers

    @pytest.mark.asyncio
    async def test_add_performer_when_performers_is_unset(self):
        """Test that add_performer initializes performers list when UNSET."""
        image = Image.model_construct(id="1", title="Image 1", performers=UNSET)
        performer = Performer(id="2", name="Performer 1")

        # Verify performers is UNSET before adding
        assert isinstance(image.performers, UnsetType)

        # Add performer - should initialize list first
        await image.add_performer(performer)

        # Verify performers was initialized and performer was added
        assert is_set(image.performers)
        assert isinstance(image.performers, list)
        assert performer in image.performers

    @pytest.mark.asyncio
    async def test_remove_performer_when_performers_is_unset(self):
        """Test that remove_performer is no-op when performers is UNSET."""
        image = Image.model_construct(id="1", title="Image 1", performers=UNSET)
        performer = Performer(id="2", name="Performer 1")

        # Remove should be no-op when UNSET
        await image.remove_performer(performer)

        # performers should still be UNSET
        assert isinstance(image.performers, UnsetType)

    @pytest.mark.asyncio
    async def test_add_to_gallery(self):
        """Test that add_to_gallery adds gallery to image.galleries list."""
        image = Image(id="1", title="Image 1", galleries=[], urls=[])
        gallery = Gallery(id="2", title="Gallery 1")

        # Add gallery (async method now, uses generic machinery)
        await image.add_to_gallery(gallery)

        # Verify gallery was added
        assert is_set(image.galleries)
        assert gallery in image.galleries

    @pytest.mark.asyncio
    async def test_add_to_gallery_deduplication(self):
        """Test that add_to_gallery doesn't create duplicates."""
        image = Image(id="1", title="Image 1", galleries=[], urls=[])
        gallery = Gallery(id="2", title="Gallery 1")

        # Add same gallery twice
        await image.add_to_gallery(gallery)
        await image.add_to_gallery(gallery)

        # Should only have one entry
        assert is_set(image.galleries)
        assert len(image.galleries) == 1

    @pytest.mark.asyncio
    async def test_remove_from_gallery(self):
        """Test that remove_from_gallery removes gallery from image.galleries list."""
        gallery = Gallery(id="2", title="Gallery 1")
        image = Image(id="1", title="Image 1", galleries=[gallery], urls=[])

        # Remove gallery (async method now, uses generic machinery)
        await image.remove_from_gallery(gallery)

        # Verify gallery was removed
        assert is_set(image.galleries)
        assert gallery not in image.galleries

    @pytest.mark.asyncio
    async def test_remove_from_gallery_noop_if_not_present(self):
        """Test that remove_from_gallery is no-op if gallery not in list."""
        image = Image(id="1", title="Image 1", galleries=[], urls=[])
        gallery = Gallery(id="2", title="Gallery 1")

        # Remove gallery that's not in the list - should be no-op
        await image.remove_from_gallery(gallery)

        assert is_set(image.galleries)
        assert gallery not in image.galleries

    @pytest.mark.asyncio
    async def test_add_to_gallery_when_galleries_is_unset(self):
        """Test that add_to_gallery initializes galleries list when UNSET."""
        image = Image.model_construct(id="1", title="Image 1", galleries=UNSET)
        gallery = Gallery(id="2", title="Gallery 1")

        # Verify galleries is UNSET before adding
        assert isinstance(image.galleries, UnsetType)

        # Add gallery - should initialize list first
        await image.add_to_gallery(gallery)

        # Verify galleries was initialized and gallery was added
        assert is_set(image.galleries)
        assert isinstance(image.galleries, list)
        assert gallery in image.galleries

    @pytest.mark.asyncio
    async def test_remove_from_gallery_when_galleries_is_unset(self):
        """Test that remove_from_gallery is no-op when galleries is UNSET."""
        image = Image.model_construct(id="1", title="Image 1", galleries=UNSET)
        gallery = Gallery(id="2", title="Gallery 1")

        # Remove should be no-op when UNSET
        await image.remove_from_gallery(gallery)

        # galleries should still be UNSET
        assert isinstance(image.galleries, UnsetType)

    @pytest.mark.asyncio
    async def test_add_tag(self):
        """Test that add_tag adds tag to tags list."""
        image = Image(id="1", title="Image 1", tags=[], urls=[])
        tag = Tag(id="2", name="Tag 1", parents=[], children=[])

        # Add tag
        await image.add_tag(tag)

        # Verify tag was added
        assert is_set(image.tags)
        assert tag in image.tags

    @pytest.mark.asyncio
    async def test_remove_tag(self):
        """Test that remove_tag removes tag from tags list."""
        tag = Tag(id="2", name="Tag 1", parents=[], children=[])
        image = Image(id="1", title="Image 1", tags=[tag], urls=[])

        # Remove tag
        await image.remove_tag(tag)

        # Verify tag was removed
        assert is_set(image.tags)
        assert tag not in image.tags

    def test_helpers_are_async_not_sync(self):
        """Test that helper methods are now async coroutines (use generic machinery)."""

        image = Image(id="1", title="Image 1", performers=[], galleries=[], urls=[])

        # These should all be coroutine functions (async methods)
        assert inspect.iscoroutinefunction(image.add_performer)
        assert inspect.iscoroutinefunction(image.remove_performer)
        assert inspect.iscoroutinefunction(image.add_to_gallery)
        assert inspect.iscoroutinefunction(image.remove_from_gallery)
        assert inspect.iscoroutinefunction(image.add_tag)
        assert inspect.iscoroutinefunction(image.remove_tag)
