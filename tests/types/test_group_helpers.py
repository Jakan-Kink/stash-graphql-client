"""Tests for Group helper methods.

These tests verify that the helper methods:
1. Modify relationships in-memory only (DON'T call save())
2. Are synchronous (not async)
3. Handle GroupDescription wrappers correctly
"""

import inspect

from stash_graphql_client.types import UNSET, Group, GroupDescription, UnsetType, is_set


class TestGroupHelperMethods:
    """Test Group convenience helper methods."""

    def test_add_sub_group_with_group_object(self):
        """Test that add_sub_group adds Group to sub_groups list as GroupDescription."""
        parent = Group(id="1", name="Parent Group", sub_groups=[])
        child = Group(id="2", name="Child Group")

        # Add sub-group with description (sync method, not async)
        parent.add_sub_group(child, "Part 2")

        # Verify sub-group was added
        assert is_set(parent.sub_groups)
        assert len(parent.sub_groups) == 1
        assert isinstance(parent.sub_groups[0], GroupDescription)
        assert parent.sub_groups[0].group == child
        assert parent.sub_groups[0].description == "Part 2"

    def test_add_sub_group_with_group_description_object(self):
        """Test that add_sub_group adds GroupDescription to sub_groups list."""
        parent = Group(id="1", name="Parent Group", sub_groups=[])
        child = Group(id="2", name="Child Group")
        child_desc = GroupDescription(group=child, description="Part 2")

        # Add sub-group with GroupDescription (description param ignored)
        parent.add_sub_group(child_desc)

        # Verify sub-group was added
        assert is_set(parent.sub_groups)
        assert len(parent.sub_groups) == 1
        assert parent.sub_groups[0] == child_desc

    def test_add_sub_group_deduplication(self):
        """Test that add_sub_group doesn't create duplicates based on ID."""
        parent = Group(id="1", name="Parent Group", sub_groups=[])
        child = Group(id="2", name="Child Group")

        # Add same sub-group twice
        parent.add_sub_group(child, "Part 1")
        parent.add_sub_group(child, "Part 2")

        # Should only have one entry (deduplicated by ID)
        assert is_set(parent.sub_groups)
        assert len(parent.sub_groups) == 1

    def test_remove_sub_group_with_group_object(self):
        """Test that remove_sub_group removes by Group ID."""
        child = Group(id="2", name="Child Group")
        child_desc = GroupDescription(group=child, description="Part 1")
        parent = Group(id="1", name="Parent Group", sub_groups=[child_desc])

        # Remove sub-group by Group object (sync method, not async)
        parent.remove_sub_group(child)

        # Verify sub-group was removed
        assert is_set(parent.sub_groups)
        assert len(parent.sub_groups) == 0

    def test_remove_sub_group_with_group_description_object(self):
        """Test that remove_sub_group removes by GroupDescription."""
        child = Group(id="2", name="Child Group")
        child_desc = GroupDescription(group=child, description="Part 1")
        parent = Group(id="1", name="Parent Group", sub_groups=[child_desc])

        # Remove sub-group by GroupDescription object
        parent.remove_sub_group(child_desc)

        # Verify sub-group was removed
        assert is_set(parent.sub_groups)
        assert len(parent.sub_groups) == 0

    def test_remove_sub_group_noop_if_not_present(self):
        """Test that remove_sub_group is no-op if sub-group not in list."""
        parent = Group(id="1", name="Parent Group", sub_groups=[])
        child = Group(id="2", name="Child Group")

        # Remove sub-group that's not in the list - should be no-op
        parent.remove_sub_group(child)

        assert is_set(parent.sub_groups)
        assert len(parent.sub_groups) == 0

    def test_add_sub_group_when_sub_groups_is_unset(self):
        """Test that add_sub_group initializes sub_groups list when UNSET."""
        parent = Group.model_construct(id="1", name="Parent Group", sub_groups=UNSET)
        child = Group(id="2", name="Child Group")

        # Verify sub_groups is UNSET before adding
        assert isinstance(parent.sub_groups, UnsetType)

        # Add sub-group - should initialize list first
        parent.add_sub_group(child, "Part 1")

        # Verify sub_groups was initialized and sub-group was added
        assert is_set(parent.sub_groups)
        assert isinstance(parent.sub_groups, list)
        assert is_set(parent.sub_groups)
        assert len(parent.sub_groups) == 1

    def test_remove_sub_group_when_sub_groups_is_unset(self):
        """Test that remove_sub_group is no-op when sub_groups is UNSET."""
        parent = Group.model_construct(id="1", name="Parent Group", sub_groups=UNSET)
        child = Group(id="2", name="Child Group")

        # Remove should be no-op when UNSET
        parent.remove_sub_group(child)

        # sub_groups should still be UNSET
        assert isinstance(parent.sub_groups, UnsetType)

    def test_add_sub_group_without_description(self):
        """Test that add_sub_group works without description parameter."""
        parent = Group(id="1", name="Parent Group", sub_groups=[])
        child = Group(id="2", name="Child Group")

        # Add sub-group without description
        parent.add_sub_group(child)

        # Verify sub-group was added with None description
        assert is_set(parent.sub_groups)
        assert len(parent.sub_groups) == 1
        assert parent.sub_groups[0].group == child
        assert parent.sub_groups[0].description is None

    def test_remove_sub_group_with_unset_group_id(self):
        """Test that remove_sub_group handles GroupDescription with UNSET group.id."""
        # Create GroupDescription with UNSET group.id
        child = Group.model_construct(id=UNSET, name="Child Group")
        child_desc = GroupDescription(group=child, description="Part 1")
        parent = Group(id="1", name="Parent Group", sub_groups=[child_desc])

        other_child = Group(id="2", name="Other Child")

        # Remove should filter out entries with UNSET group.id
        parent.remove_sub_group(other_child)

        # Original entry should still be there (since it has UNSET id)
        assert is_set(parent.sub_groups)
        assert len(parent.sub_groups) == 1

    def test_helpers_are_sync_not_async(self):
        """Test that helper methods are synchronous (not coroutines)."""
        parent = Group(id="1", name="Parent Group", sub_groups=[])
        child = Group(id="2", name="Child Group")

        # These should all be regular methods, not coroutines
        assert not inspect.iscoroutinefunction(parent.add_sub_group)
        assert not inspect.iscoroutinefunction(parent.remove_sub_group)

        # Calling them should not return coroutines
        assert parent.add_sub_group(child) is None
