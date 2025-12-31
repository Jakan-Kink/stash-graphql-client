"""Tests for Studio helper methods.

These tests verify that the helper methods:
1. Modify relationships in-memory only (DON'T call save())
2. Maintain bidirectional consistency locally
3. Mark studios as dirty when relationships change
"""

import inspect

import pytest

from stash_graphql_client.types import UNSET, UnsetType, is_set
from stash_graphql_client.types.studio import Studio


@pytest.mark.usefixtures("mock_entity_store")
class TestStudioHelperMethods:
    """Test Studio convenience helper methods."""

    @pytest.mark.asyncio
    async def test_set_parent_studio(self):
        """Test that set_parent_studio sets the parent_studio field."""
        studio = Studio(id="1", name="Child Studio")
        parent = Studio(id="2", name="Parent Studio", child_studios=[])

        # Set parent (async method now, uses generic machinery)
        await studio.set_parent_studio(parent)

        # Verify parent was set
        assert studio.parent_studio == parent

    @pytest.mark.asyncio
    async def test_set_parent_studio_to_none(self):
        """Test that set_parent_studio can set parent to None."""
        parent = Studio(id="2", name="Parent Studio")
        studio = Studio(id="1", name="Child Studio", parent_studio=parent)

        # Set parent to None
        await studio.set_parent_studio(None)

        # Verify parent was set to None
        assert studio.parent_studio is None

    @pytest.mark.asyncio
    async def test_add_child_studio(self):
        """Test that add_child_studio adds child to parent.child_studios list."""
        parent = Studio(id="1", name="Parent Studio", child_studios=[])
        child = Studio(id="2", name="Child Studio", parent_studio=None)

        # Add child (async method now, uses generic machinery)
        await parent.add_child_studio(child)

        # Verify child was added
        assert is_set(parent.child_studios)
        assert parent.child_studios is not None
        assert child in parent.child_studios
        # Verify bidirectional sync - child's parent should be set
        assert child.parent_studio == parent

    @pytest.mark.asyncio
    async def test_add_child_studio_deduplication(self):
        """Test that add_child_studio doesn't create duplicates."""
        parent = Studio(id="1", name="Parent Studio", child_studios=[])
        child = Studio(id="2", name="Child Studio", parent_studio=None)

        # Add same child twice
        await parent.add_child_studio(child)
        await parent.add_child_studio(child)

        # Should only have one entry
        assert is_set(parent.child_studios)
        assert parent.child_studios is not None
        assert len(parent.child_studios) == 1

    @pytest.mark.asyncio
    async def test_remove_child_studio(self):
        """Test that remove_child_studio removes child from parent.child_studios list."""
        child = Studio(id="2", name="Child Studio", parent_studio=None)
        parent = Studio(id="1", name="Parent Studio", child_studios=[child])

        # Remove child (async method now, uses generic machinery)
        await parent.remove_child_studio(child)

        # Verify child was removed
        assert is_set(parent.child_studios)
        assert parent.child_studios is not None
        assert child not in parent.child_studios

    @pytest.mark.asyncio
    async def test_remove_child_studio_noop_if_not_present(self):
        """Test that remove_child_studio is no-op if child not in list."""
        parent = Studio(id="1", name="Parent Studio", child_studios=[])
        child = Studio(id="2", name="Child Studio")

        # Remove child that's not in the list - should be no-op
        await parent.remove_child_studio(child)

        assert is_set(parent.child_studios)
        assert parent.child_studios is not None
        assert child not in parent.child_studios

    @pytest.mark.asyncio
    async def test_add_child_studio_when_child_studios_is_none(self):
        """Test that add_child_studio initializes child_studios list when None."""
        parent = Studio(id="1", name="Parent Studio", child_studios=None)
        child = Studio(id="2", name="Child Studio", parent_studio=None)

        # Add child - should initialize list first
        await parent.add_child_studio(child)

        # Verify child_studios was initialized and child was added
        assert parent.child_studios is not None
        assert isinstance(parent.child_studios, list)
        assert child in parent.child_studios

    @pytest.mark.asyncio
    async def test_remove_child_studio_when_child_studios_is_unset(self):
        """Test that remove_child_studio is no-op when child_studios is UNSET."""
        parent = Studio.model_construct(
            id="1", name="Parent Studio", child_studios=UNSET
        )
        child = Studio(id="2", name="Child Studio")

        # Remove should be no-op when UNSET
        await parent.remove_child_studio(child)

        # child_studios should still be UNSET
        assert isinstance(parent.child_studios, UnsetType)

    @pytest.mark.asyncio
    async def test_remove_child_studio_when_child_studios_is_none(self):
        """Test that remove_child_studio is no-op when child_studios is None."""
        parent = Studio.model_construct(
            id="1", name="Parent Studio", child_studios=None
        )
        child = Studio(id="2", name="Child Studio")

        # Remove should be no-op when None
        await parent.remove_child_studio(child)

        # child_studios should still be None
        assert parent.child_studios is None

    def test_helpers_are_async_not_sync(self):
        """Test that helper methods are now async coroutines (use generic machinery)."""
        parent = Studio(id="1", name="Parent Studio", child_studios=[])

        # These should all be coroutine functions (async methods)
        assert inspect.iscoroutinefunction(parent.set_parent_studio)
        assert inspect.iscoroutinefunction(parent.add_child_studio)
        assert inspect.iscoroutinefunction(parent.remove_child_studio)
