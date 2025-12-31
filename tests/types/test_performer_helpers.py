"""Tests for Performer helper methods.

These tests verify that the helper methods:
1. Modify relationships in-memory only (DON'T call save())
2. Are asynchronous (async)
"""

import inspect

import pytest

from stash_graphql_client.types import UNSET, UnsetType, is_set
from stash_graphql_client.types.performer import Performer
from stash_graphql_client.types.tag import Tag


@pytest.mark.usefixtures("mock_entity_store")
class TestPerformerHelperMethods:
    """Test Performer convenience helper methods."""

    @pytest.mark.asyncio
    async def test_add_tag(self):
        """Test that add_tag adds tag to performer.tags list."""
        performer = Performer(id="1", name="Performer 1", tags=[])
        tag = Tag(id="2", name="Tag 1", parents=[], children=[])

        # Add tag (async method now, uses generic machinery)
        await performer.add_tag(tag)

        # Verify tag was added
        assert is_set(performer.tags)
        assert tag in performer.tags

    @pytest.mark.asyncio
    async def test_add_tag_deduplication(self):
        """Test that add_tag doesn't create duplicates."""
        performer = Performer(id="1", name="Performer 1", tags=[])
        tag = Tag(id="2", name="Tag 1", parents=[], children=[])

        # Add same tag twice
        await performer.add_tag(tag)
        await performer.add_tag(tag)

        # Should only have one entry
        assert is_set(performer.tags)
        assert len(performer.tags) == 1

    @pytest.mark.asyncio
    async def test_remove_tag(self):
        """Test that remove_tag removes tag from performer.tags list."""
        tag = Tag(id="2", name="Tag 1", parents=[], children=[])
        performer = Performer(id="1", name="Performer 1", tags=[tag])

        # Remove tag (async method now, uses generic machinery)
        await performer.remove_tag(tag)

        # Verify tag was removed
        assert is_set(performer.tags)
        assert tag not in performer.tags

    @pytest.mark.asyncio
    async def test_remove_tag_noop_if_not_present(self):
        """Test that remove_tag is no-op if tag not in list."""
        performer = Performer(id="1", name="Performer 1", tags=[])
        tag = Tag(id="2", name="Tag 1", parents=[], children=[])

        # Remove tag that's not in the list - should be no-op
        await performer.remove_tag(tag)

        assert is_set(performer.tags)
        assert tag not in performer.tags

    @pytest.mark.asyncio
    async def test_add_tag_when_tags_is_unset(self):
        """Test that add_tag initializes tags list when UNSET."""
        # Create performer with UNSET tags using model_construct
        performer = Performer.model_construct(id="1", name="Performer 1", tags=UNSET)
        tag = Tag(id="2", name="Tag 1", parents=[], children=[])

        # Verify tags is UNSET before adding
        assert isinstance(performer.tags, UnsetType)

        # Add tag - should initialize list first
        await performer.add_tag(tag)

        # Verify tags was initialized and tag was added
        assert is_set(performer.tags)
        assert isinstance(performer.tags, list)
        assert tag in performer.tags

    @pytest.mark.asyncio
    async def test_remove_tag_when_tags_is_unset(self):
        """Test that remove_tag is no-op when tags is UNSET."""
        # Create performer with UNSET tags
        performer = Performer.model_construct(id="1", name="Performer 1", tags=UNSET)
        tag = Tag(id="2", name="Tag 1", parents=[], children=[])

        # Remove should be no-op when UNSET
        await performer.remove_tag(tag)

        # tags should still be UNSET
        assert isinstance(performer.tags, UnsetType)

    def test_helpers_are_async_not_sync(self):
        """Test that helper methods are now async coroutines (use generic machinery)."""
        performer = Performer(id="1", name="Performer 1", tags=[])

        # These should all be coroutine functions (async methods)
        assert inspect.iscoroutinefunction(performer.add_tag)
        assert inspect.iscoroutinefunction(performer.remove_tag)
