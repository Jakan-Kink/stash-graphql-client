"""Tests for Image helper methods.

These tests verify that the helper methods:
1. Modify relationships in-memory only (DON'T call save())
2. Are synchronous (not async)
"""

from stash_graphql_client.types import UNSET
from stash_graphql_client.types.gallery import Gallery
from stash_graphql_client.types.image import Image
from stash_graphql_client.types.performer import Performer


class TestImageHelperMethods:
    """Test Image convenience helper methods."""

    def test_add_performer(self):
        """Test that add_performer adds performer to image.performers list."""
        image = Image(id="1", title="Image 1", performers=[], urls=[])
        performer = Performer(id="2", name="Performer 1")

        # Add performer (sync method, not async)
        image.add_performer(performer)

        # Verify performer was added
        assert performer in image.performers

    def test_add_performer_deduplication(self):
        """Test that add_performer doesn't create duplicates."""
        image = Image(id="1", title="Image 1", performers=[], urls=[])
        performer = Performer(id="2", name="Performer 1")

        # Add same performer twice
        image.add_performer(performer)
        image.add_performer(performer)

        # Should only have one entry
        assert len(image.performers) == 1

    def test_remove_performer(self):
        """Test that remove_performer removes performer from image.performers list."""
        performer = Performer(id="2", name="Performer 1")
        image = Image(id="1", title="Image 1", performers=[performer], urls=[])

        # Remove performer (sync method, not async)
        image.remove_performer(performer)

        # Verify performer was removed
        assert performer not in image.performers

    def test_remove_performer_noop_if_not_present(self):
        """Test that remove_performer is no-op if performer not in list."""
        image = Image(id="1", title="Image 1", performers=[], urls=[])
        performer = Performer(id="2", name="Performer 1")

        # Remove performer that's not in the list - should be no-op
        image.remove_performer(performer)

        assert performer not in image.performers

    def test_add_performer_when_performers_is_unset(self):
        """Test that add_performer initializes performers list when UNSET."""
        image = Image.model_construct(id="1", title="Image 1", performers=UNSET)
        performer = Performer(id="2", name="Performer 1")

        # Verify performers is UNSET before adding
        assert image.performers is UNSET

        # Add performer - should initialize list first
        image.add_performer(performer)

        # Verify performers was initialized and performer was added
        assert image.performers is not UNSET
        assert isinstance(image.performers, list)
        assert performer in image.performers

    def test_remove_performer_when_performers_is_unset(self):
        """Test that remove_performer is no-op when performers is UNSET."""
        image = Image.model_construct(id="1", title="Image 1", performers=UNSET)
        performer = Performer(id="2", name="Performer 1")

        # Remove should be no-op when UNSET
        image.remove_performer(performer)

        # performers should still be UNSET
        assert image.performers is UNSET

    def test_add_to_gallery(self):
        """Test that add_to_gallery adds gallery to image.galleries list."""
        image = Image(id="1", title="Image 1", galleries=[], urls=[])
        gallery = Gallery(id="2", title="Gallery 1")

        # Add gallery (sync method, not async)
        image.add_to_gallery(gallery)

        # Verify gallery was added
        assert gallery in image.galleries

    def test_add_to_gallery_deduplication(self):
        """Test that add_to_gallery doesn't create duplicates."""
        image = Image(id="1", title="Image 1", galleries=[], urls=[])
        gallery = Gallery(id="2", title="Gallery 1")

        # Add same gallery twice
        image.add_to_gallery(gallery)
        image.add_to_gallery(gallery)

        # Should only have one entry
        assert len(image.galleries) == 1

    def test_remove_from_gallery(self):
        """Test that remove_from_gallery removes gallery from image.galleries list."""
        gallery = Gallery(id="2", title="Gallery 1")
        image = Image(id="1", title="Image 1", galleries=[gallery], urls=[])

        # Remove gallery (sync method, not async)
        image.remove_from_gallery(gallery)

        # Verify gallery was removed
        assert gallery not in image.galleries

    def test_remove_from_gallery_noop_if_not_present(self):
        """Test that remove_from_gallery is no-op if gallery not in list."""
        image = Image(id="1", title="Image 1", galleries=[], urls=[])
        gallery = Gallery(id="2", title="Gallery 1")

        # Remove gallery that's not in the list - should be no-op
        image.remove_from_gallery(gallery)

        assert gallery not in image.galleries

    def test_add_to_gallery_when_galleries_is_unset(self):
        """Test that add_to_gallery initializes galleries list when UNSET."""
        image = Image.model_construct(id="1", title="Image 1", galleries=UNSET)
        gallery = Gallery(id="2", title="Gallery 1")

        # Verify galleries is UNSET before adding
        assert image.galleries is UNSET

        # Add gallery - should initialize list first
        image.add_to_gallery(gallery)

        # Verify galleries was initialized and gallery was added
        assert image.galleries is not UNSET
        assert isinstance(image.galleries, list)
        assert gallery in image.galleries

    def test_remove_from_gallery_when_galleries_is_unset(self):
        """Test that remove_from_gallery is no-op when galleries is UNSET."""
        image = Image.model_construct(id="1", title="Image 1", galleries=UNSET)
        gallery = Gallery(id="2", title="Gallery 1")

        # Remove should be no-op when UNSET
        image.remove_from_gallery(gallery)

        # galleries should still be UNSET
        assert image.galleries is UNSET

    def test_helpers_are_sync_not_async(self):
        """Test that helper methods are synchronous (not coroutines)."""
        import inspect

        image = Image(id="1", title="Image 1", performers=[], galleries=[], urls=[])
        performer = Performer(id="2", name="Performer 1")
        gallery = Gallery(id="3", title="Gallery 1")

        # These should all be regular methods, not coroutines
        assert not inspect.iscoroutinefunction(image.add_performer)
        assert not inspect.iscoroutinefunction(image.remove_performer)
        assert not inspect.iscoroutinefunction(image.add_to_gallery)
        assert not inspect.iscoroutinefunction(image.remove_from_gallery)

        # Calling them should not return coroutines
        assert image.add_performer(performer) is None
        assert image.add_to_gallery(gallery) is None
