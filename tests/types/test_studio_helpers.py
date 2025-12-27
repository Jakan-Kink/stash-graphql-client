"""Tests for Studio helper methods.

These tests verify that the helper methods:
1. Modify relationships in-memory only (DON'T call save())
2. Are synchronous (not async)
3. Handle bidirectional parent-child relationships correctly
"""

from stash_graphql_client.types import UNSET
from stash_graphql_client.types.studio import Studio


class TestStudioHelperMethods:
    """Test Studio convenience helper methods."""

    def test_set_parent_studio(self):
        """Test that set_parent_studio sets the parent_studio field."""
        studio = Studio(id="1", name="Child Studio")
        parent = Studio(id="2", name="Parent Studio")

        # Set parent (sync method, not async)
        studio.set_parent_studio(parent)

        # Verify parent was set
        assert studio.parent_studio == parent

    def test_set_parent_studio_to_none(self):
        """Test that set_parent_studio can set parent to None."""
        parent = Studio(id="2", name="Parent Studio")
        studio = Studio(id="1", name="Child Studio", parent_studio=parent)

        # Set parent to None (sync method, not async)
        studio.set_parent_studio(None)

        # Verify parent was set to None
        assert studio.parent_studio is None

    def test_add_child_studio(self):
        """Test that add_child_studio adds child to parent.child_studios list."""
        parent = Studio(id="1", name="Parent Studio", child_studios=[])
        child = Studio(id="2", name="Child Studio")

        # Add child (sync method, not async)
        parent.add_child_studio(child)

        # Verify child was added
        assert child in parent.child_studios
        # Verify bidirectional sync - child's parent should be set
        assert child.parent_studio == parent

    def test_add_child_studio_deduplication(self):
        """Test that add_child_studio doesn't create duplicates."""
        parent = Studio(id="1", name="Parent Studio", child_studios=[])
        child = Studio(id="2", name="Child Studio")

        # Add same child twice
        parent.add_child_studio(child)
        parent.add_child_studio(child)

        # Should only have one entry
        assert len(parent.child_studios) == 1

    def test_remove_child_studio(self):
        """Test that remove_child_studio removes child from parent.child_studios list."""
        child = Studio(id="2", name="Child Studio")
        parent = Studio(id="1", name="Parent Studio", child_studios=[child])

        # Remove child (sync method, not async)
        parent.remove_child_studio(child)

        # Verify child was removed
        assert child not in parent.child_studios
        # Verify bidirectional sync - child's parent should be None
        assert child.parent_studio is None

    def test_remove_child_studio_noop_if_not_present(self):
        """Test that remove_child_studio is no-op if child not in list."""
        parent = Studio(id="1", name="Parent Studio", child_studios=[])
        child = Studio(id="2", name="Child Studio")

        # Remove child that's not in the list - should be no-op
        parent.remove_child_studio(child)

        assert child not in parent.child_studios

    def test_add_child_studio_when_child_studios_is_unset(self):
        """Test that add_child_studio initializes child_studios list when UNSET."""
        parent = Studio.model_construct(
            id="1", name="Parent Studio", child_studios=UNSET
        )
        child = Studio(id="2", name="Child Studio")

        # Verify child_studios is UNSET before adding
        assert parent.child_studios is UNSET

        # Add child - should initialize list first
        parent.add_child_studio(child)

        # Verify child_studios was initialized and child was added
        assert parent.child_studios is not UNSET
        assert isinstance(parent.child_studios, list)
        assert child in parent.child_studios

    def test_add_child_studio_when_child_studios_is_none(self):
        """Test that add_child_studio initializes child_studios list when None."""
        parent = Studio.model_construct(
            id="1", name="Parent Studio", child_studios=None
        )
        child = Studio(id="2", name="Child Studio")

        # Add child - should initialize list first
        parent.add_child_studio(child)

        # Verify child_studios was initialized and child was added
        assert parent.child_studios is not None
        assert isinstance(parent.child_studios, list)
        assert child in parent.child_studios

    def test_remove_child_studio_when_child_studios_is_unset(self):
        """Test that remove_child_studio is no-op when child_studios is UNSET."""
        parent = Studio.model_construct(
            id="1", name="Parent Studio", child_studios=UNSET
        )
        child = Studio(id="2", name="Child Studio")

        # Remove should be no-op when UNSET
        parent.remove_child_studio(child)

        # child_studios should still be UNSET
        assert parent.child_studios is UNSET

    def test_remove_child_studio_when_child_studios_is_none(self):
        """Test that remove_child_studio is no-op when child_studios is None."""
        parent = Studio.model_construct(
            id="1", name="Parent Studio", child_studios=None
        )
        child = Studio(id="2", name="Child Studio")

        # Remove should be no-op when None
        parent.remove_child_studio(child)

        # child_studios should still be None
        assert parent.child_studios is None

    def test_helpers_are_sync_not_async(self):
        """Test that helper methods are synchronous (not coroutines)."""
        import inspect

        parent = Studio(id="1", name="Parent Studio", child_studios=[])
        child = Studio(id="2", name="Child Studio")

        # These should all be regular methods, not coroutines
        assert not inspect.iscoroutinefunction(parent.set_parent_studio)
        assert not inspect.iscoroutinefunction(parent.add_child_studio)
        assert not inspect.iscoroutinefunction(parent.remove_child_studio)

        # Calling them should not return coroutines
        assert parent.set_parent_studio(None) is None
        assert parent.add_child_studio(child) is None
