"""Tests for Group helper methods.

These tests verify that the helper methods:
1. Modify relationships in-memory only (DON'T call save())
2. Are asynchronous (async)
3. Handle GroupDescription wrappers correctly
"""

import inspect
from unittest.mock import patch

import pytest

from stash_graphql_client.errors import StashIntegrationError
from stash_graphql_client.types import UNSET, Group, GroupDescription, UnsetType, is_set


@pytest.mark.usefixtures("mock_entity_store")
class TestGroupHelperMethods:
    """Test Group convenience helper methods."""

    @pytest.mark.asyncio
    async def test_add_sub_group_with_group_object(self):
        """Test that add_sub_group adds Group to sub_groups list as GroupDescription."""
        parent = Group(id="1", name="Parent Group", sub_groups=[])
        child = Group(id="2", name="Child Group")

        # Add sub-group with description (async method now, uses generic machinery)
        await parent.add_sub_group(child, "Part 2")

        # Verify sub-group was added
        assert is_set(parent.sub_groups)
        assert len(parent.sub_groups) == 1
        assert isinstance(parent.sub_groups[0], GroupDescription)
        assert parent.sub_groups[0].group == child
        assert parent.sub_groups[0].description == "Part 2"

    @pytest.mark.asyncio
    async def test_add_sub_group_with_group_description_object(self):
        """Test that add_sub_group adds GroupDescription to sub_groups list."""
        parent = Group(id="1", name="Parent Group", sub_groups=[])
        child = Group(id="2", name="Child Group")
        child_desc = GroupDescription(group=child, description="Part 2")

        # Add sub-group with GroupDescription (description param ignored)
        await parent.add_sub_group(child_desc)

        # Verify sub-group was added
        assert is_set(parent.sub_groups)
        assert len(parent.sub_groups) == 1
        assert parent.sub_groups[0] == child_desc

    @pytest.mark.asyncio
    async def test_add_sub_group_deduplication(self):
        """Test that add_sub_group doesn't create duplicates based on ID."""
        parent = Group(id="1", name="Parent Group", sub_groups=[])
        child = Group(id="2", name="Child Group")

        # Add same sub-group twice
        await parent.add_sub_group(child, "Part 1")
        await parent.add_sub_group(child, "Part 2")

        # Should only have one entry (deduplicated by ID)
        assert is_set(parent.sub_groups)
        assert len(parent.sub_groups) == 1

    @pytest.mark.asyncio
    async def test_remove_sub_group_with_group_object(self):
        """Test that remove_sub_group removes by Group ID."""
        child = Group(id="2", name="Child Group")
        child_desc = GroupDescription(group=child, description="Part 1")
        parent = Group(id="1", name="Parent Group", sub_groups=[child_desc])

        # Remove sub-group by Group object (async method now, uses generic machinery)
        await parent.remove_sub_group(child)

        # Verify sub-group was removed
        assert is_set(parent.sub_groups)
        assert len(parent.sub_groups) == 0

    @pytest.mark.asyncio
    async def test_remove_sub_group_with_group_description_object(self):
        """Test that remove_sub_group removes by GroupDescription."""
        child = Group(id="2", name="Child Group")
        child_desc = GroupDescription(group=child, description="Part 1")
        parent = Group(id="1", name="Parent Group", sub_groups=[child_desc])

        # Remove sub-group by GroupDescription object
        await parent.remove_sub_group(child_desc)

        # Verify sub-group was removed
        assert is_set(parent.sub_groups)
        assert len(parent.sub_groups) == 0

    @pytest.mark.asyncio
    async def test_remove_sub_group_noop_if_not_present(self):
        """Test that remove_sub_group is no-op if sub-group not in list."""
        parent = Group(id="1", name="Parent Group", sub_groups=[])
        child = Group(id="2", name="Child Group")

        # Remove sub-group that's not in the list - should be no-op
        await parent.remove_sub_group(child)

        assert is_set(parent.sub_groups)
        assert len(parent.sub_groups) == 0

    @pytest.mark.asyncio
    async def test_add_sub_group_when_sub_groups_is_unset(self):
        """Test that add_sub_group initializes sub_groups list when UNSET."""
        parent = Group.model_construct(id="1", name="Parent Group", sub_groups=UNSET)
        child = Group(id="2", name="Child Group")

        # Verify sub_groups is UNSET before adding
        assert isinstance(parent.sub_groups, UnsetType)

        # Add sub-group - should initialize list first
        await parent.add_sub_group(child, "Part 1")

        # Verify sub_groups was initialized and sub-group was added
        assert is_set(parent.sub_groups)
        assert isinstance(parent.sub_groups, list)
        assert is_set(parent.sub_groups)
        assert len(parent.sub_groups) == 1

    @pytest.mark.asyncio
    async def test_remove_sub_group_when_sub_groups_is_unset(self):
        """Test that remove_sub_group is no-op when sub_groups is UNSET."""
        parent = Group.model_construct(id="1", name="Parent Group", sub_groups=UNSET)
        child = Group(id="2", name="Child Group")

        # Remove should be no-op when UNSET
        await parent.remove_sub_group(child)

        # sub_groups should still be UNSET
        assert isinstance(parent.sub_groups, UnsetType)

    @pytest.mark.asyncio
    async def test_add_sub_group_without_description(self):
        """Test that add_sub_group works without description parameter."""
        parent = Group(id="1", name="Parent Group", sub_groups=[])
        child = Group(id="2", name="Child Group")

        # Add sub-group without description
        await parent.add_sub_group(child)

        # Verify sub-group was added with None description
        assert is_set(parent.sub_groups)
        assert len(parent.sub_groups) == 1
        assert parent.sub_groups[0].group == child
        assert parent.sub_groups[0].description is None

    @pytest.mark.asyncio
    async def test_remove_sub_group_with_unset_group_id(self):
        """Test that remove_sub_group handles GroupDescription with UNSET group.id."""
        # Create GroupDescription with UNSET group.id
        child = Group.model_construct(id=UNSET, name="Child Group")
        child_desc = GroupDescription(group=child, description="Part 1")
        parent = Group(id="1", name="Parent Group", sub_groups=[child_desc])

        other_child = Group(id="2", name="Other Child")

        # Remove should filter out entries with UNSET group.id
        await parent.remove_sub_group(other_child)

        # Original entry should still be there (since it has UNSET id)
        assert is_set(parent.sub_groups)
        assert len(parent.sub_groups) == 1

    @pytest.mark.asyncio
    async def test_add_containing_group(self):
        """Test that add_containing_group adds containing group to list."""
        child = Group(id="1", name="Child Group", containing_groups=[])
        parent = Group(id="2", name="Parent Group", sub_groups=[])

        # Add containing group
        await child.add_containing_group(parent)

        # Verify containing group was added
        assert is_set(child.containing_groups)
        assert len(child.containing_groups) == 1
        assert isinstance(child.containing_groups[0], GroupDescription)
        assert child.containing_groups[0].group == parent

    @pytest.mark.asyncio
    async def test_add_containing_group_with_description(self):
        """Test adding containing group with GroupDescription object."""
        child = Group(id="1", name="Child Group", containing_groups=[])
        parent = Group(id="2", name="Parent Group")
        parent_desc = GroupDescription(group=parent, description="Main series")

        # Add containing group with description
        await child.add_containing_group(parent_desc)

        # Verify it was added
        assert is_set(child.containing_groups)
        assert len(child.containing_groups) == 1
        assert child.containing_groups[0] == parent_desc

    @pytest.mark.asyncio
    async def test_add_containing_group_deduplication(self):
        """Test that add_containing_group deduplicates by group ID."""
        child = Group(id="1", name="Child Group", containing_groups=[])
        parent = Group(id="2", name="Parent Group")

        # Add same containing group twice
        await child.add_containing_group(parent)
        await child.add_containing_group(parent)

        # Should only have one entry
        assert is_set(child.containing_groups)
        assert len(child.containing_groups) == 1

    @pytest.mark.asyncio
    async def test_add_containing_group_when_unset(self):
        """Test that add_containing_group fetches UNSET field via store."""
        child = Group.model_construct(
            id="1", name="Child Group", containing_groups=UNSET
        )
        parent = Group(id="2", name="Parent Group")

        assert isinstance(child.containing_groups, UnsetType)

        # Add should fetch from store (mocked to return [])
        await child.add_containing_group(parent)

        # Verify list was initialized and group added
        assert is_set(child.containing_groups)
        assert len(child.containing_groups) == 1

    @pytest.mark.asyncio
    async def test_remove_containing_group(self):
        """Test that remove_containing_group removes by group ID."""
        parent = Group(id="2", name="Parent Group")
        parent_desc = GroupDescription(group=parent, description="Main")
        child = Group(id="1", name="Child Group", containing_groups=[parent_desc])

        # Remove by Group object
        await child.remove_containing_group(parent)

        # Verify it was removed
        assert is_set(child.containing_groups)
        assert len(child.containing_groups) == 0

    @pytest.mark.asyncio
    async def test_remove_containing_group_with_description(self):
        """Test that remove_containing_group works with GroupDescription."""
        parent = Group(id="2", name="Parent Group")
        parent_desc = GroupDescription(group=parent, description="Main")
        child = Group(id="1", name="Child Group", containing_groups=[parent_desc])

        # Remove by GroupDescription
        await child.remove_containing_group(parent_desc)

        # Verify it was removed
        assert is_set(child.containing_groups)
        assert len(child.containing_groups) == 0

    @pytest.mark.asyncio
    async def test_remove_containing_group_when_unset(self):
        """Test that remove_containing_group is no-op when UNSET."""
        child = Group.model_construct(id="1", name="Child", containing_groups=UNSET)
        parent = Group(id="2", name="Parent")

        # Should be no-op
        await child.remove_containing_group(parent)

        # Should still be UNSET
        assert isinstance(child.containing_groups, UnsetType)

    @pytest.mark.asyncio
    async def test_add_sub_group_raises_when_store_is_none(self):
        """Test that add_sub_group raises StashIntegrationError when store is None and field is UNSET."""
        # Temporarily set class-level store to None
        with patch.object(Group, "_store", None):
            # Create parent with UNSET sub_groups
            parent = Group.model_construct(id="1", name="Parent", sub_groups=UNSET)
            child = Group(id="2", name="Child")

            # Should raise error
            with pytest.raises(
                StashIntegrationError,
                match="Cannot add sub-group: store not available",
            ):
                await parent.add_sub_group(child)

    @pytest.mark.asyncio
    async def test_add_containing_group_raises_when_store_is_none(self):
        """Test that add_containing_group raises StashIntegrationError when store is None and field is UNSET."""
        # Temporarily set class-level store to None
        with patch.object(Group, "_store", None):
            # Create child with UNSET containing_groups
            child = Group.model_construct(id="1", name="Child", containing_groups=UNSET)
            parent = Group(id="2", name="Parent")

            # Should raise error
            with pytest.raises(
                StashIntegrationError,
                match="Cannot add containing group: store not available",
            ):
                await child.add_containing_group(parent)

    @pytest.mark.asyncio
    async def test_add_sub_group_initializes_none_to_empty_list(self):
        """Test that add_sub_group initializes None field to empty list."""
        parent = Group.model_construct(id="1", name="Parent", sub_groups=None)
        child = Group(id="2", name="Child")

        # Verify field is None before adding
        assert parent.sub_groups is None

        # Add sub-group - should initialize to []
        await parent.add_sub_group(child, "Part 1")

        # Verify field was initialized and child added
        assert isinstance(parent.sub_groups, list)
        assert len(parent.sub_groups) == 1
        assert parent.sub_groups[0].group == child

    @pytest.mark.asyncio
    async def test_add_containing_group_initializes_none_to_empty_list(self):
        """Test that add_containing_group initializes None field to empty list."""
        child = Group.model_construct(id="1", name="Child", containing_groups=None)
        parent = Group(id="2", name="Parent")

        # Verify field is None before adding
        assert child.containing_groups is None

        # Add containing group - should initialize to []
        await child.add_containing_group(parent)

        # Verify field was initialized and parent added
        assert isinstance(child.containing_groups, list)
        assert len(child.containing_groups) == 1
        assert child.containing_groups[0].group == parent

    @pytest.mark.asyncio
    async def test_add_sub_group_without_group_id(self):
        """Test add_sub_group when group has no id (skips deduplication)."""
        parent = Group(id="1", name="Parent", sub_groups=[])
        child = Group.model_construct(id=UNSET, name="Child")  # No ID

        # Add sub-group without ID (should skip deduplication logic)
        await parent.add_sub_group(child, "Part 1")

        # Should still be added
        assert is_set(parent.sub_groups)
        assert len(parent.sub_groups) == 1
        assert parent.sub_groups[0].group == child

    @pytest.mark.asyncio
    async def test_add_containing_group_without_group_id(self):
        """Test add_containing_group when group has no id (skips deduplication)."""
        child = Group(id="1", name="Child", containing_groups=[])
        parent = Group.model_construct(id=UNSET, name="Parent")  # No ID

        # Add containing group without ID (should skip deduplication logic)
        await child.add_containing_group(parent)

        # Should still be added
        assert is_set(child.containing_groups)
        assert len(child.containing_groups) == 1
        assert child.containing_groups[0].group == parent

    @pytest.mark.asyncio
    async def test_remove_sub_group_without_group_id(self):
        """Test remove_sub_group when group has no id (early exit, no-op)."""
        child = Group.model_construct(id=UNSET, name="Child")
        child_desc = GroupDescription(group=child, description="Part 1")
        parent = Group(id="1", name="Parent", sub_groups=[child_desc])

        # Remove sub-group without ID (should be no-op due to early exit)
        other_child = Group.model_construct(id=UNSET, name="Other Child")
        await parent.remove_sub_group(other_child)

        # Original entry should still be there
        assert is_set(parent.sub_groups)
        assert len(parent.sub_groups) == 1

    @pytest.mark.asyncio
    async def test_remove_containing_group_without_group_id(self):
        """Test remove_containing_group when group has no id (early exit, no-op)."""
        parent = Group.model_construct(id=UNSET, name="Parent")
        parent_desc = GroupDescription(group=parent, description="Main")
        child = Group(id="1", name="Child", containing_groups=[parent_desc])

        # Remove containing group without ID (should be no-op due to early exit)
        other_parent = Group.model_construct(id=UNSET, name="Other Parent")
        await child.remove_containing_group(other_parent)

        # Original entry should still be there
        assert is_set(child.containing_groups)
        assert len(child.containing_groups) == 1

    def test_helpers_are_async_not_sync(self):
        """Test that helper methods are now async coroutines (use generic machinery)."""
        parent = Group(id="1", name="Parent Group", sub_groups=[])

        # These should all be coroutine functions (async methods)
        assert inspect.iscoroutinefunction(parent.add_sub_group)
        assert inspect.iscoroutinefunction(parent.remove_sub_group)
        assert inspect.iscoroutinefunction(parent.add_containing_group)
        assert inspect.iscoroutinefunction(parent.remove_containing_group)
