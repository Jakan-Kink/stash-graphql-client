"""Tests for Gallery helper methods.

These tests verify that the helper methods:
1. Modify relationships in-memory only (DON'T call save())
2. Are synchronous (not async)
"""

from stash_graphql_client.types import UNSET, Scene
from stash_graphql_client.types.gallery import Gallery
from stash_graphql_client.types.performer import Performer


class TestGalleryHelperMethods:
    """Test Gallery convenience helper methods."""

    def test_add_performer(self):
        """Test that add_performer adds performer to gallery.performers list."""
        gallery = Gallery(id="1", title="Gallery 1", performers=[], urls=[])
        performer = Performer(id="2", name="Performer 1")

        # Add performer (sync method, not async)
        gallery.add_performer(performer)

        # Verify performer was added
        assert performer in gallery.performers

    def test_add_performer_deduplication(self):
        """Test that add_performer doesn't create duplicates."""
        gallery = Gallery(id="1", title="Gallery 1", performers=[], urls=[])
        performer = Performer(id="2", name="Performer 1")

        # Add same performer twice
        gallery.add_performer(performer)
        gallery.add_performer(performer)

        # Should only have one entry
        assert len(gallery.performers) == 1

    def test_remove_performer(self):
        """Test that remove_performer removes performer from gallery.performers list."""
        performer = Performer(id="2", name="Performer 1")
        gallery = Gallery(id="1", title="Gallery 1", performers=[performer], urls=[])

        # Remove performer (sync method, not async)
        gallery.remove_performer(performer)

        # Verify performer was removed
        assert performer not in gallery.performers

    def test_remove_performer_noop_if_not_present(self):
        """Test that remove_performer is no-op if performer not in list."""
        gallery = Gallery(id="1", title="Gallery 1", performers=[], urls=[])
        performer = Performer(id="2", name="Performer 1")

        # Remove performer that's not in the list - should be no-op
        gallery.remove_performer(performer)

        assert performer not in gallery.performers

    def test_add_performer_when_performers_is_unset(self):
        """Test that add_performer initializes performers list when UNSET."""
        gallery = Gallery.model_construct(id="1", title="Gallery 1", performers=UNSET)
        performer = Performer(id="2", name="Performer 1")

        # Verify performers is UNSET before adding
        assert gallery.performers is UNSET

        # Add performer - should initialize list first
        gallery.add_performer(performer)

        # Verify performers was initialized and performer was added
        assert gallery.performers is not UNSET
        assert isinstance(gallery.performers, list)
        assert performer in gallery.performers

    def test_remove_performer_when_performers_is_unset(self):
        """Test that remove_performer is no-op when performers is UNSET."""
        gallery = Gallery.model_construct(id="1", title="Gallery 1", performers=UNSET)
        performer = Performer(id="2", name="Performer 1")

        # Remove should be no-op when UNSET
        gallery.remove_performer(performer)

        # performers should still be UNSET
        assert gallery.performers is UNSET

    def test_add_scene(self):
        """Test that add_scene adds scene to gallery.scenes list."""
        gallery = Gallery(id="1", title="Gallery 1", scenes=[], urls=[])
        scene = Scene(id="2", title="Scene 1", organized=False, urls=[])

        # Add scene (sync method, not async)
        gallery.add_scene(scene)

        # Verify scene was added
        assert scene in gallery.scenes

    def test_add_scene_deduplication(self):
        """Test that add_scene doesn't create duplicates."""
        gallery = Gallery(id="1", title="Gallery 1", scenes=[], urls=[])
        scene = Scene(id="2", title="Scene 1", organized=False, urls=[])

        # Add same scene twice
        gallery.add_scene(scene)
        gallery.add_scene(scene)

        # Should only have one entry
        assert len(gallery.scenes) == 1

    def test_remove_scene(self):
        """Test that remove_scene removes scene from gallery.scenes list."""
        scene = Scene(id="2", title="Scene 1", organized=False, urls=[])
        gallery = Gallery(id="1", title="Gallery 1", scenes=[scene], urls=[])

        # Remove scene (sync method, not async)
        gallery.remove_scene(scene)

        # Verify scene was removed
        assert scene not in gallery.scenes

    def test_remove_scene_noop_if_not_present(self):
        """Test that remove_scene is no-op if scene not in list."""
        gallery = Gallery(id="1", title="Gallery 1", scenes=[], urls=[])
        scene = Scene(id="2", title="Scene 1", organized=False, urls=[])

        # Remove scene that's not in the list - should be no-op
        gallery.remove_scene(scene)

        assert scene not in gallery.scenes

    def test_add_scene_when_scenes_is_unset(self):
        """Test that add_scene initializes scenes list when UNSET."""
        gallery = Gallery.model_construct(id="1", title="Gallery 1", scenes=UNSET)
        scene = Scene(id="2", title="Scene 1", organized=False, urls=[])

        # Verify scenes is UNSET before adding
        assert gallery.scenes is UNSET

        # Add scene - should initialize list first
        gallery.add_scene(scene)

        # Verify scenes was initialized and scene was added
        assert gallery.scenes is not UNSET
        assert isinstance(gallery.scenes, list)
        assert scene in gallery.scenes

    def test_remove_scene_when_scenes_is_unset(self):
        """Test that remove_scene is no-op when scenes is UNSET."""
        gallery = Gallery.model_construct(id="1", title="Gallery 1", scenes=UNSET)
        scene = Scene(id="2", title="Scene 1", organized=False, urls=[])

        # Remove should be no-op when UNSET
        gallery.remove_scene(scene)

        # scenes should still be UNSET
        assert gallery.scenes is UNSET

    def test_helpers_are_sync_not_async(self):
        """Test that helper methods are synchronous (not coroutines)."""
        import inspect

        gallery = Gallery(id="1", title="Gallery 1", performers=[], scenes=[], urls=[])
        performer = Performer(id="2", name="Performer 1")
        scene = Scene(id="3", title="Scene 1", organized=False, urls=[])

        # These should all be regular methods, not coroutines
        assert not inspect.iscoroutinefunction(gallery.add_performer)
        assert not inspect.iscoroutinefunction(gallery.remove_performer)
        assert not inspect.iscoroutinefunction(gallery.add_scene)
        assert not inspect.iscoroutinefunction(gallery.remove_scene)

        # Calling them should not return coroutines
        assert gallery.add_performer(performer) is None
        assert gallery.add_scene(scene) is None
