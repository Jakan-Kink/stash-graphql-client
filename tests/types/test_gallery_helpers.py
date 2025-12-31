"""Tests for Gallery helper methods.

These tests verify that the helper methods:
1. Modify relationships in-memory only (DON'T call save())
2. Are asynchronous (async)
"""

import inspect

import pytest

from stash_graphql_client.types import UNSET, Scene, UnsetType, is_set
from stash_graphql_client.types.gallery import Gallery
from stash_graphql_client.types.performer import Performer


@pytest.mark.usefixtures("mock_entity_store")
class TestGalleryHelperMethods:
    """Test Gallery convenience helper methods."""

    @pytest.mark.asyncio
    async def test_add_performer(self):
        """Test that add_performer adds performer to gallery.performers list."""
        gallery = Gallery(id="1", title="Gallery 1", performers=[], urls=[])
        performer = Performer(id="2", name="Performer 1")

        # Add performer (async method now, uses generic machinery)
        await gallery.add_performer(performer)

        # Verify performer was added
        assert is_set(gallery.performers)
        assert performer in gallery.performers

    @pytest.mark.asyncio
    async def test_add_performer_deduplication(self):
        """Test that add_performer doesn't create duplicates."""
        gallery = Gallery(id="1", title="Gallery 1", performers=[], urls=[])
        performer = Performer(id="2", name="Performer 1")

        # Add same performer twice
        await gallery.add_performer(performer)
        await gallery.add_performer(performer)

        # Should only have one entry
        assert is_set(gallery.performers)
        assert len(gallery.performers) == 1

    @pytest.mark.asyncio
    async def test_remove_performer(self):
        """Test that remove_performer removes performer from gallery.performers list."""
        performer = Performer(id="2", name="Performer 1")
        gallery = Gallery(id="1", title="Gallery 1", performers=[performer], urls=[])

        # Remove performer (async method now, uses generic machinery)
        await gallery.remove_performer(performer)

        # Verify performer was removed
        assert is_set(gallery.performers)
        assert performer not in gallery.performers

    @pytest.mark.asyncio
    async def test_remove_performer_noop_if_not_present(self):
        """Test that remove_performer is no-op if performer not in list."""
        gallery = Gallery(id="1", title="Gallery 1", performers=[], urls=[])
        performer = Performer(id="2", name="Performer 1")

        # Remove performer that's not in the list - should be no-op
        await gallery.remove_performer(performer)

        assert is_set(gallery.performers)
        assert performer not in gallery.performers

    @pytest.mark.asyncio
    async def test_add_performer_when_performers_is_unset(self):
        """Test that add_performer initializes performers list when UNSET."""
        gallery = Gallery.model_construct(id="1", title="Gallery 1", performers=UNSET)
        performer = Performer(id="2", name="Performer 1")

        # Verify performers is UNSET before adding
        assert isinstance(gallery.performers, UnsetType)

        # Add performer - should initialize list first
        await gallery.add_performer(performer)

        # Verify performers was initialized and performer was added
        assert is_set(gallery.performers)
        assert isinstance(gallery.performers, list)
        assert performer in gallery.performers

    @pytest.mark.asyncio
    async def test_remove_performer_when_performers_is_unset(self):
        """Test that remove_performer is no-op when performers is UNSET."""
        gallery = Gallery.model_construct(id="1", title="Gallery 1", performers=UNSET)
        performer = Performer(id="2", name="Performer 1")

        # Remove should be no-op when UNSET
        await gallery.remove_performer(performer)

        # performers should still be UNSET
        assert isinstance(gallery.performers, UnsetType)

    @pytest.mark.asyncio
    async def test_add_scene(self):
        """Test that add_scene adds scene to gallery.scenes list."""
        gallery = Gallery(id="1", title="Gallery 1", scenes=[], urls=[])
        scene = Scene(id="2", title="Scene 1", organized=False, urls=[])

        # Add scene (async method now, uses generic machinery)
        await gallery.add_scene(scene)

        # Verify scene was added
        assert is_set(gallery.scenes)
        assert scene in gallery.scenes

    @pytest.mark.asyncio
    async def test_add_scene_deduplication(self):
        """Test that add_scene doesn't create duplicates."""
        gallery = Gallery(id="1", title="Gallery 1", scenes=[], urls=[])
        scene = Scene(id="2", title="Scene 1", organized=False, urls=[])

        # Add same scene twice
        await gallery.add_scene(scene)
        await gallery.add_scene(scene)

        # Should only have one entry
        assert is_set(gallery.scenes)
        assert len(gallery.scenes) == 1

    @pytest.mark.asyncio
    async def test_remove_scene(self):
        """Test that remove_scene removes scene from gallery.scenes list."""
        scene = Scene(id="2", title="Scene 1", organized=False, urls=[])
        gallery = Gallery(id="1", title="Gallery 1", scenes=[scene], urls=[])

        # Remove scene (async method now, uses generic machinery)
        await gallery.remove_scene(scene)

        # Verify scene was removed
        assert is_set(gallery.scenes)
        assert scene not in gallery.scenes

    @pytest.mark.asyncio
    async def test_remove_scene_noop_if_not_present(self):
        """Test that remove_scene is no-op if scene not in list."""
        gallery = Gallery(id="1", title="Gallery 1", scenes=[], urls=[])
        scene = Scene(id="2", title="Scene 1", organized=False, urls=[])

        # Remove scene that's not in the list - should be no-op
        await gallery.remove_scene(scene)

        assert is_set(gallery.scenes)
        assert scene not in gallery.scenes

    @pytest.mark.asyncio
    async def test_add_scene_when_scenes_is_unset(self):
        """Test that add_scene initializes scenes list when UNSET."""
        gallery = Gallery.model_construct(id="1", title="Gallery 1", scenes=UNSET)
        scene = Scene(id="2", title="Scene 1", organized=False, urls=[])

        # Verify scenes is UNSET before adding
        assert isinstance(gallery.scenes, UnsetType)

        # Add scene - should initialize list first
        await gallery.add_scene(scene)

        # Verify scenes was initialized and scene was added
        assert is_set(gallery.scenes)
        assert isinstance(gallery.scenes, list)
        assert scene in gallery.scenes

    @pytest.mark.asyncio
    async def test_remove_scene_when_scenes_is_unset(self):
        """Test that remove_scene is no-op when scenes is UNSET."""
        gallery = Gallery.model_construct(id="1", title="Gallery 1", scenes=UNSET)
        scene = Scene(id="2", title="Scene 1", organized=False, urls=[])

        # Remove should be no-op when UNSET
        await gallery.remove_scene(scene)

        # scenes should still be UNSET
        assert isinstance(gallery.scenes, UnsetType)

    @pytest.mark.asyncio
    async def test_add_tag(self):
        """Test that add_tag adds tag to tags list."""
        from stash_graphql_client.types import Tag

        gallery = Gallery(id="1", title="Gallery 1", tags=[], urls=[])
        tag = Tag(id="2", name="Tag 1", parents=[], children=[])

        # Add tag
        await gallery.add_tag(tag)

        # Verify tag was added
        assert is_set(gallery.tags)
        assert tag in gallery.tags

    @pytest.mark.asyncio
    async def test_remove_tag(self):
        """Test that remove_tag removes tag from tags list."""
        from stash_graphql_client.types import Tag

        tag = Tag(id="2", name="Tag 1", parents=[], children=[])
        gallery = Gallery(id="1", title="Gallery 1", tags=[tag], urls=[])

        # Remove tag
        await gallery.remove_tag(tag)

        # Verify tag was removed
        assert is_set(gallery.tags)
        assert tag not in gallery.tags

    def test_helpers_are_async_not_sync(self):
        """Test that helper methods are now async coroutines (use generic machinery)."""
        gallery = Gallery(id="1", title="Gallery 1", performers=[], scenes=[], urls=[])

        # These should all be coroutine functions (async methods)
        assert inspect.iscoroutinefunction(gallery.add_performer)
        assert inspect.iscoroutinefunction(gallery.remove_performer)
        assert inspect.iscoroutinefunction(gallery.add_scene)
        assert inspect.iscoroutinefunction(gallery.remove_scene)
        assert inspect.iscoroutinefunction(gallery.add_tag)
        assert inspect.iscoroutinefunction(gallery.remove_tag)
