"""Tests for Scene helper methods.

These tests verify that the helper methods:
1. Modify relationships in-memory only (DON'T call save())
2. Are synchronous (not async)
"""

from stash_graphql_client.types import Scene
from stash_graphql_client.types.gallery import Gallery
from stash_graphql_client.types.performer import Performer
from stash_graphql_client.types.studio import Studio
from stash_graphql_client.types.tag import Tag


class TestSceneHelperMethods:
    """Test Scene convenience helper methods."""

    def test_add_to_gallery(self):
        """Test that add_to_gallery adds gallery to scene.galleries list."""
        scene = Scene(id="1", title="Scene 1", galleries=[], organized=False, urls=[])
        gallery = Gallery(id="2", title="Gallery 1")

        # Add gallery (sync method, not async)
        scene.add_to_gallery(gallery)

        # Verify gallery was added
        assert gallery in scene.galleries

    def test_add_to_gallery_deduplication(self):
        """Test that add_to_gallery doesn't create duplicates."""
        scene = Scene(id="1", title="Scene 1", galleries=[], organized=False, urls=[])
        gallery = Gallery(id="2", title="Gallery 1")

        # Add same gallery twice
        scene.add_to_gallery(gallery)
        scene.add_to_gallery(gallery)

        # Should only have one entry
        assert len(scene.galleries) == 1

    def test_remove_from_gallery(self):
        """Test that remove_from_gallery removes gallery from scene.galleries list."""
        gallery = Gallery(id="2", title="Gallery 1")
        scene = Scene(
            id="1", title="Scene 1", galleries=[gallery], organized=False, urls=[]
        )

        # Remove gallery (sync method, not async)
        scene.remove_from_gallery(gallery)

        # Verify gallery was removed
        assert gallery not in scene.galleries

    def test_remove_from_gallery_noop_if_not_present(self):
        """Test that remove_from_gallery is no-op if gallery not in list."""
        scene = Scene(id="1", title="Scene 1", galleries=[], organized=False, urls=[])
        gallery = Gallery(id="2", title="Gallery 1")

        # Remove gallery that's not in the list - should be no-op
        scene.remove_from_gallery(gallery)

        assert gallery not in scene.galleries

    def test_add_performer(self):
        """Test that add_performer adds performer to scene.performers list."""
        scene = Scene(id="1", title="Scene 1", performers=[], organized=False, urls=[])
        performer = Performer(id="2", name="Performer 1")

        # Add performer (sync method, not async)
        scene.add_performer(performer)

        # Verify performer was added
        assert performer in scene.performers

    def test_add_performer_deduplication(self):
        """Test that add_performer doesn't create duplicates."""
        scene = Scene(id="1", title="Scene 1", performers=[], organized=False, urls=[])
        performer = Performer(id="2", name="Performer 1")

        # Add same performer twice
        scene.add_performer(performer)
        scene.add_performer(performer)

        # Should only have one entry
        assert len(scene.performers) == 1

    def test_remove_performer(self):
        """Test that remove_performer removes performer from scene.performers list."""
        performer = Performer(id="2", name="Performer 1")
        scene = Scene(
            id="1", title="Scene 1", performers=[performer], organized=False, urls=[]
        )

        # Remove performer (sync method, not async)
        scene.remove_performer(performer)

        # Verify performer was removed
        assert performer not in scene.performers

    def test_remove_performer_noop_if_not_present(self):
        """Test that remove_performer is no-op if performer not in list."""
        scene = Scene(id="1", title="Scene 1", performers=[], organized=False, urls=[])
        performer = Performer(id="2", name="Performer 1")

        # Remove performer that's not in the list - should be no-op
        scene.remove_performer(performer)

        assert performer not in scene.performers

    def test_add_tag(self):
        """Test that add_tag adds tag to scene.tags list."""
        scene = Scene(id="1", title="Scene 1", tags=[], organized=False, urls=[])
        tag = Tag(id="2", name="Tag 1", parents=[], children=[])

        # Add tag (sync method, not async)
        scene.add_tag(tag)

        # Verify tag was added
        assert tag in scene.tags

    def test_add_tag_deduplication(self):
        """Test that add_tag doesn't create duplicates."""
        scene = Scene(id="1", title="Scene 1", tags=[], organized=False, urls=[])
        tag = Tag(id="2", name="Tag 1", parents=[], children=[])

        # Add same tag twice
        scene.add_tag(tag)
        scene.add_tag(tag)

        # Should only have one entry
        assert len(scene.tags) == 1

    def test_remove_tag(self):
        """Test that remove_tag removes tag from scene.tags list."""
        tag = Tag(id="2", name="Tag 1", parents=[], children=[])
        scene = Scene(id="1", title="Scene 1", tags=[tag], organized=False, urls=[])

        # Remove tag (sync method, not async)
        scene.remove_tag(tag)

        # Verify tag was removed
        assert tag not in scene.tags

    def test_remove_tag_noop_if_not_present(self):
        """Test that remove_tag is no-op if tag not in list."""
        scene = Scene(id="1", title="Scene 1", tags=[], organized=False, urls=[])
        tag = Tag(id="2", name="Tag 1", parents=[], children=[])

        # Remove tag that's not in the list - should be no-op
        scene.remove_tag(tag)

        assert tag not in scene.tags

    def test_set_studio(self):
        """Test that set_studio sets the studio field."""
        scene = Scene(id="1", title="Scene 1", organized=False, urls=[])
        studio = Studio(id="2", name="Studio 1")

        # Set studio (sync method, not async)
        scene.set_studio(studio)

        # Verify studio was set
        assert scene.studio == studio

    def test_set_studio_to_none(self):
        """Test that set_studio can set studio to None."""
        studio = Studio(id="2", name="Studio 1")
        scene = Scene(id="1", title="Scene 1", studio=studio, organized=False, urls=[])

        # Set studio to None (sync method, not async)
        scene.set_studio(None)

        # Verify studio was set to None
        assert scene.studio is None

    def test_helpers_are_sync_not_async(self):
        """Test that helper methods are synchronous (not coroutines)."""
        import inspect

        scene = Scene(id="1", title="Scene 1", organized=False, urls=[])
        gallery = Gallery(id="2", title="Gallery 1")
        performer = Performer(id="3", name="Performer 1")
        tag = Tag(id="4", name="Tag 1", parents=[], children=[])
        studio = Studio(id="5", name="Studio 1")

        # These should all be regular methods, not coroutines
        assert not inspect.iscoroutinefunction(scene.add_to_gallery)
        assert not inspect.iscoroutinefunction(scene.remove_from_gallery)
        assert not inspect.iscoroutinefunction(scene.add_performer)
        assert not inspect.iscoroutinefunction(scene.remove_performer)
        assert not inspect.iscoroutinefunction(scene.add_tag)
        assert not inspect.iscoroutinefunction(scene.remove_tag)
        assert not inspect.iscoroutinefunction(scene.set_studio)

        # Calling them should not return coroutines - test all helpers
        assert scene.add_to_gallery(gallery) is None
        assert scene.add_performer(performer) is None
        assert scene.add_tag(tag) is None
        assert scene.set_studio(studio) is None

    def test_add_performer_when_performers_is_unset(self):
        """Test that add_performer initializes performers list when UNSET.

        This covers line 351: if self.performers is UNSET
        """
        from stash_graphql_client.types import UNSET

        # Create scene with UNSET performers using model_construct
        scene = Scene.model_construct(
            id="1", title="Scene 1", performers=UNSET, organized=False, urls=[]
        )
        performer = Performer(id="2", name="Performer 1")

        # Verify performers is UNSET before adding
        assert scene.performers is UNSET

        # Add performer - should initialize list first
        scene.add_performer(performer)

        # Verify performers was initialized and performer was added
        assert scene.performers is not UNSET
        assert isinstance(scene.performers, list)
        assert performer in scene.performers

    def test_add_tag_when_tags_is_unset(self):
        """Test that add_tag initializes tags list when UNSET.

        This covers line 386: if tag not in self.tags (after initializing from UNSET)
        """
        from stash_graphql_client.types import UNSET

        # Create scene with UNSET tags using model_construct
        scene = Scene.model_construct(
            id="1", title="Scene 1", tags=UNSET, organized=False, urls=[]
        )
        tag = Tag(id="2", name="Tag 1", parents=[], children=[])

        # Verify tags is UNSET before adding
        assert scene.tags is UNSET

        # Add tag - should initialize list first
        scene.add_tag(tag)

        # Verify tags was initialized and tag was added
        assert scene.tags is not UNSET
        assert isinstance(scene.tags, list)
        assert tag in scene.tags
