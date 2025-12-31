"""Tests for SceneMarker helper methods.

These tests verify that the helper methods:
1. Modify relationships in-memory only (DON'T call save())
2. Are asynchronous (async)
"""

import inspect

import pytest

from stash_graphql_client.types import UNSET, UnsetType, is_set
from stash_graphql_client.types.markers import SceneMarker
from stash_graphql_client.types.tag import Tag


@pytest.mark.usefixtures("mock_entity_store")
class TestSceneMarkerHelperMethods:
    """Test SceneMarker convenience helper methods."""

    @pytest.mark.asyncio
    async def test_add_tag(self):
        """Test that add_tag adds tag to scene_marker.tags list."""
        marker = SceneMarker(id="1", title="Intro", seconds=10.0, tags=[])
        tag = Tag(id="2", name="Action", parents=[], children=[])

        # Add tag (async method now, uses generic machinery)
        await marker.add_tag(tag)

        # Verify tag was added
        assert is_set(marker.tags)
        assert tag in marker.tags

    @pytest.mark.asyncio
    async def test_add_tag_deduplication(self):
        """Test that add_tag doesn't create duplicates."""
        marker = SceneMarker(id="1", title="Intro", seconds=10.0, tags=[])
        tag = Tag(id="2", name="Action", parents=[], children=[])

        # Add same tag twice
        await marker.add_tag(tag)
        await marker.add_tag(tag)

        # Should only have one entry
        assert is_set(marker.tags)
        assert len(marker.tags) == 1

    @pytest.mark.asyncio
    async def test_remove_tag(self):
        """Test that remove_tag removes tag from scene_marker.tags list."""
        tag = Tag(id="2", name="Action", parents=[], children=[])
        marker = SceneMarker(id="1", title="Intro", seconds=10.0, tags=[tag])

        # Remove tag (async method now, uses generic machinery)
        await marker.remove_tag(tag)

        # Verify tag was removed
        assert is_set(marker.tags)
        assert tag not in marker.tags

    @pytest.mark.asyncio
    async def test_remove_tag_noop_if_not_present(self):
        """Test that remove_tag is no-op if tag not in list."""
        marker = SceneMarker(id="1", title="Intro", seconds=10.0, tags=[])
        tag = Tag(id="2", name="Action", parents=[], children=[])

        # Remove tag that's not in the list - should be no-op
        await marker.remove_tag(tag)

        assert is_set(marker.tags)
        assert tag not in marker.tags

    @pytest.mark.asyncio
    async def test_add_tag_when_tags_is_unset(self):
        """Test that add_tag initializes tags list when UNSET."""
        # Create marker with UNSET tags using model_construct
        marker = SceneMarker.model_construct(
            id="1", title="Intro", seconds=10.0, tags=UNSET
        )
        tag = Tag(id="2", name="Action", parents=[], children=[])

        # Verify tags is UNSET before adding
        assert isinstance(marker.tags, UnsetType)

        # Add tag - should initialize list first
        await marker.add_tag(tag)

        # Verify tags was initialized and tag was added
        assert is_set(marker.tags)
        assert isinstance(marker.tags, list)
        assert tag in marker.tags

    @pytest.mark.asyncio
    async def test_remove_tag_when_tags_is_unset(self):
        """Test that remove_tag is no-op when tags is UNSET."""
        # Create marker with UNSET tags
        marker = SceneMarker.model_construct(
            id="1", title="Intro", seconds=10.0, tags=UNSET
        )
        tag = Tag(id="2", name="Action", parents=[], children=[])

        # Remove should be no-op when UNSET
        await marker.remove_tag(tag)

        # tags should still be UNSET
        assert isinstance(marker.tags, UnsetType)

    def test_helpers_are_async_not_sync(self):
        """Test that helper methods are now async coroutines (use generic machinery)."""
        marker = SceneMarker(id="1", title="Intro", seconds=10.0, tags=[])

        # These should all be coroutine functions (async methods)
        assert inspect.iscoroutinefunction(marker.add_tag)
        assert inspect.iscoroutinefunction(marker.remove_tag)
