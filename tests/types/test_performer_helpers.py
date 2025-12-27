"""Tests for Performer helper methods.

These tests verify that the helper methods:
1. Modify relationships in-memory only (DON'T call save())
2. Are synchronous (not async)
"""

from stash_graphql_client.types import UNSET, UnsetType, is_set
from stash_graphql_client.types.performer import Performer
from stash_graphql_client.types.tag import Tag


class TestPerformerHelperMethods:
    """Test Performer convenience helper methods."""

    def test_add_tag(self):
        """Test that add_tag adds tag to performer.tags list."""
        performer = Performer(id="1", name="Performer 1", tags=[])
        tag = Tag(id="2", name="Tag 1", parents=[], children=[])

        # Add tag (sync method, not async)
        performer.add_tag(tag)

        # Verify tag was added
        assert is_set(performer.tags)
        assert tag in performer.tags

    def test_add_tag_deduplication(self):
        """Test that add_tag doesn't create duplicates."""
        performer = Performer(id="1", name="Performer 1", tags=[])
        tag = Tag(id="2", name="Tag 1", parents=[], children=[])

        # Add same tag twice
        performer.add_tag(tag)
        performer.add_tag(tag)

        # Should only have one entry
        assert is_set(performer.tags)
        assert len(performer.tags) == 1

    def test_remove_tag(self):
        """Test that remove_tag removes tag from performer.tags list."""
        tag = Tag(id="2", name="Tag 1", parents=[], children=[])
        performer = Performer(id="1", name="Performer 1", tags=[tag])

        # Remove tag (sync method, not async)
        performer.remove_tag(tag)

        # Verify tag was removed
        assert is_set(performer.tags)
        assert tag not in performer.tags

    def test_remove_tag_noop_if_not_present(self):
        """Test that remove_tag is no-op if tag not in list."""
        performer = Performer(id="1", name="Performer 1", tags=[])
        tag = Tag(id="2", name="Tag 1", parents=[], children=[])

        # Remove tag that's not in the list - should be no-op
        performer.remove_tag(tag)

        assert is_set(performer.tags)
        assert tag not in performer.tags

    def test_add_tag_when_tags_is_unset(self):
        """Test that add_tag initializes tags list when UNSET."""
        # Create performer with UNSET tags using model_construct
        performer = Performer.model_construct(id="1", name="Performer 1", tags=UNSET)
        tag = Tag(id="2", name="Tag 1", parents=[], children=[])

        # Verify tags is UNSET before adding
        assert isinstance(performer.tags, UnsetType)

        # Add tag - should initialize list first
        performer.add_tag(tag)

        # Verify tags was initialized and tag was added
        assert is_set(performer.tags)
        assert isinstance(performer.tags, list)
        assert tag in performer.tags

    def test_remove_tag_when_tags_is_unset(self):
        """Test that remove_tag is no-op when tags is UNSET."""
        # Create performer with UNSET tags
        performer = Performer.model_construct(id="1", name="Performer 1", tags=UNSET)
        tag = Tag(id="2", name="Tag 1", parents=[], children=[])

        # Remove should be no-op when UNSET
        performer.remove_tag(tag)

        # tags should still be UNSET
        assert isinstance(performer.tags, UnsetType)

    def test_helpers_are_sync_not_async(self):
        """Test that helper methods are synchronous (not coroutines)."""
        import inspect

        performer = Performer(id="1", name="Performer 1", tags=[])
        tag = Tag(id="2", name="Tag 1", parents=[], children=[])

        # These should all be regular methods, not coroutines
        assert not inspect.iscoroutinefunction(performer.add_tag)
        assert not inspect.iscoroutinefunction(performer.remove_tag)

        # Calling them should not return coroutines
        assert performer.add_tag(tag) is None
        assert performer.remove_tag(tag) is None
