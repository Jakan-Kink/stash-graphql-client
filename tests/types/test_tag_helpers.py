"""Tests for Tag helper methods (add_parent, remove_parent, add_child, remove_child).

These tests verify that the helper methods:
1. Modify relationships in-memory only (DON'T call save())
2. Maintain bidirectional consistency locally
3. Mark tags as dirty when relationships change
"""

import inspect

import pytest

from stash_graphql_client.types import UNSET, Tag


@pytest.mark.usefixtures("mock_entity_store")
class TestTagHelperMethods:
    """Test Tag convenience helper methods."""

    @pytest.mark.asyncio
    async def test_add_parent_maintains_bidirectional_consistency(self):
        """Test that add_parent updates both child.parents and parent.children."""
        parent = Tag(id="1", name="Parent", parents=[], children=[])
        child = Tag(id="2", name="Child", parents=[], children=[])

        # Add parent (async method now, uses generic machinery)
        await child.add_parent(parent)

        # Verify bidirectional consistency
        assert parent in child.parents
        assert child in parent.children

    @pytest.mark.asyncio
    async def test_add_parent_deduplication(self):
        """Test that add_parent doesn't create duplicates."""
        parent = Tag(id="1", name="Parent", parents=[], children=[])
        child = Tag(id="2", name="Child", parents=[], children=[])

        # Add same parent twice
        await child.add_parent(parent)
        await child.add_parent(parent)

        # Should only have one entry on both sides
        assert len(child.parents) == 1
        assert len(parent.children) == 1

    @pytest.mark.asyncio
    async def test_remove_parent_maintains_bidirectional_consistency(self):
        """Test that remove_parent updates both child.parents and parent.children."""
        parent = Tag(id="1", name="Parent", parents=[], children=[])
        child = Tag(id="2", name="Child", parents=[], children=[])

        # Set up relationship
        await child.add_parent(parent)

        # Remove parent (async method now, uses generic machinery)
        await child.remove_parent(parent)

        # Verify bidirectional consistency
        assert parent not in child.parents
        assert child not in parent.children

    @pytest.mark.asyncio
    async def test_remove_parent_noop_if_not_present(self):
        """Test that remove_parent is no-op if parent not in list."""
        parent = Tag(id="1", name="Parent", parents=[], children=[])
        child = Tag(id="2", name="Child", parents=[], children=[])

        # Remove parent that's not in the list - should be no-op
        await child.remove_parent(parent)

        assert parent not in child.parents
        assert child not in parent.children

    @pytest.mark.asyncio
    async def test_add_child_maintains_bidirectional_consistency(self):
        """Test that add_child updates both parent.children and child.parents."""
        parent = Tag(id="1", name="Parent", parents=[], children=[])
        child = Tag(id="2", name="Child", parents=[], children=[])

        # Add child (async method now, uses generic machinery)
        await parent.add_child(child)

        # Verify bidirectional consistency
        assert child in parent.children
        assert parent in child.parents

    @pytest.mark.asyncio
    async def test_add_child_deduplication(self):
        """Test that add_child doesn't create duplicates."""
        parent = Tag(id="1", name="Parent", parents=[], children=[])
        child = Tag(id="2", name="Child", parents=[], children=[])

        # Add same child twice
        await parent.add_child(child)
        await parent.add_child(child)

        # Should only have one entry on both sides
        assert len(parent.children) == 1
        assert len(child.parents) == 1

    @pytest.mark.asyncio
    async def test_remove_child_maintains_bidirectional_consistency(self):
        """Test that remove_child updates both parent.children and child.parents."""
        parent = Tag(id="1", name="Parent", parents=[], children=[])
        child = Tag(id="2", name="Child", parents=[], children=[])

        # Set up relationship
        await parent.add_child(child)

        # Remove child (async method now, uses generic machinery)
        await parent.remove_child(child)

        # Verify bidirectional consistency
        assert child not in parent.children
        assert parent not in child.parents

    @pytest.mark.asyncio
    async def test_remove_child_noop_if_not_present(self):
        """Test that remove_child is no-op if child not in list."""
        parent = Tag(id="1", name="Parent", parents=[], children=[])
        child = Tag(id="2", name="Child", parents=[], children=[])

        # Remove child that's not in the list - should be no-op
        await parent.remove_child(child)

        assert child not in parent.children
        assert parent not in child.parents

    @pytest.mark.asyncio
    async def test_helper_methods_with_multi_level_hierarchy(self):
        """Test that helper methods work correctly in multi-level hierarchies."""
        grandparent = Tag(id="1", name="Grandparent", parents=[], children=[])
        parent = Tag(id="2", name="Parent", parents=[], children=[])
        child = Tag(id="3", name="Child", parents=[], children=[])

        # Build hierarchy using helper methods
        await parent.add_parent(grandparent)
        await child.add_parent(parent)

        # Verify multi-level traversal works
        assert grandparent.children[0].children[0] == child
        assert child.parents[0].parents[0] == grandparent

    def test_helpers_are_async_not_sync(self):
        """Test that helper methods are now async coroutines (use generic machinery)."""
        parent = Tag(id="1", name="Parent", parents=[], children=[])
        child = Tag(id="2", name="Child", parents=[], children=[])

        # These should all be coroutine functions (async methods)
        assert inspect.iscoroutinefunction(child.add_parent)
        assert inspect.iscoroutinefunction(child.remove_parent)
        assert inspect.iscoroutinefunction(parent.add_child)
        assert inspect.iscoroutinefunction(parent.remove_child)

    @pytest.mark.asyncio
    async def test_add_parent_when_inverse_already_exists(self):
        """Test add_parent when parent.children already contains child."""
        parent = Tag(id="1", name="Parent", parents=[], children=[])
        child = Tag(id="2", name="Child", parents=[], children=[])

        # Manually set up inverse relationship first
        parent.children.append(child)

        # Now call add_parent - should only update child.parents
        await child.add_parent(parent)

        # Both sides should be set
        assert parent in child.parents
        assert child in parent.children
        # Should not have duplicates
        assert len(parent.children) == 1

    @pytest.mark.asyncio
    async def test_remove_parent_when_inverse_not_exists(self):
        """Test remove_parent when parent.children doesn't contain child."""
        parent = Tag(id="1", name="Parent", parents=[], children=[])
        child = Tag(id="2", name="Child", parents=[parent], children=[])

        # parent.children is empty (no inverse)
        # Call remove_parent
        await child.remove_parent(parent)

        # Should still remove from child.parents
        assert parent not in child.parents
        assert child not in parent.children

    @pytest.mark.asyncio
    async def test_add_child_when_inverse_already_exists(self):
        """Test add_child when child.parents already contains parent."""
        parent = Tag(id="1", name="Parent", parents=[], children=[])
        child = Tag(id="2", name="Child", parents=[], children=[])

        # Manually set up inverse relationship first
        child.parents.append(parent)

        # Now call add_child - should only update parent.children
        await parent.add_child(child)

        # Both sides should be set
        assert child in parent.children
        assert parent in child.parents
        # Should not have duplicates
        assert len(child.parents) == 1

    @pytest.mark.asyncio
    async def test_remove_child_when_inverse_not_exists(self):
        """Test remove_child when child.parents doesn't contain parent."""
        parent = Tag(id="1", name="Parent", parents=[], children=[])
        child = Tag(id="2", name="Child", parents=[], children=[])

        # Manually set up only parent.children
        parent.children.append(child)

        # child.parents is empty (no inverse)
        # Call remove_child
        await parent.remove_child(child)

        # Should still remove from parent.children
        assert child not in parent.children
        assert parent not in child.parents


@pytest.mark.usefixtures("mock_entity_store")
class TestTagRecursiveMethods:
    """Test Tag recursive hierarchy traversal methods."""

    @pytest.mark.asyncio
    async def test_get_all_descendants_empty(self):
        """Test get_all_descendants with no children."""
        tag = Tag(id="1", name="Root", parents=[], children=[])

        descendants = await tag.get_all_descendants()

        assert descendants == []

    @pytest.mark.asyncio
    async def test_get_all_descendants_single_level(self):
        """Test get_all_descendants with direct children only."""
        parent = Tag(id="1", name="Parent", parents=[], children=[])
        child1 = Tag(id="2", name="Child1", parents=[], children=[])
        child2 = Tag(id="3", name="Child2", parents=[], children=[])

        await parent.add_child(child1)
        await parent.add_child(child2)

        descendants = await parent.get_all_descendants()

        assert len(descendants) == 2
        assert child1 in descendants
        assert child2 in descendants

    @pytest.mark.asyncio
    async def test_get_all_descendants_multi_level(self):
        """Test get_all_descendants with multiple levels (grandchildren)."""
        grandparent = Tag(id="1", name="Grandparent", parents=[], children=[])
        parent = Tag(id="2", name="Parent", parents=[], children=[])
        child = Tag(id="3", name="Child", parents=[], children=[])
        grandchild = Tag(id="4", name="Grandchild", parents=[], children=[])

        await grandparent.add_child(parent)
        await parent.add_child(child)
        await child.add_child(grandchild)

        descendants = await grandparent.get_all_descendants()

        # Should get all 3 descendants
        assert len(descendants) == 3
        assert parent in descendants
        assert child in descendants
        assert grandchild in descendants

    @pytest.mark.asyncio
    async def test_get_all_ancestors_empty(self):
        """Test get_all_ancestors with no parents."""
        tag = Tag(id="1", name="Root", parents=[], children=[])

        ancestors = await tag.get_all_ancestors()

        assert ancestors == []

    @pytest.mark.asyncio
    async def test_get_all_ancestors_single_level(self):
        """Test get_all_ancestors with direct parents only."""
        child = Tag(id="1", name="Child", parents=[], children=[])
        parent1 = Tag(id="2", name="Parent1", parents=[], children=[])
        parent2 = Tag(id="3", name="Parent2", parents=[], children=[])

        await child.add_parent(parent1)
        await child.add_parent(parent2)

        ancestors = await child.get_all_ancestors()

        assert len(ancestors) == 2
        assert parent1 in ancestors
        assert parent2 in ancestors

    @pytest.mark.asyncio
    async def test_get_all_ancestors_multi_level(self):
        """Test get_all_ancestors with multiple levels (grandparents)."""
        grandchild = Tag(id="1", name="Grandchild", parents=[], children=[])
        child = Tag(id="2", name="Child", parents=[], children=[])
        parent = Tag(id="3", name="Parent", parents=[], children=[])
        grandparent = Tag(id="4", name="Grandparent", parents=[], children=[])

        await grandchild.add_parent(child)
        await child.add_parent(parent)
        await parent.add_parent(grandparent)

        ancestors = await grandchild.get_all_ancestors()

        # Should get all 3 ancestors
        assert len(ancestors) == 3
        assert child in ancestors
        assert parent in ancestors
        assert grandparent in ancestors

    @pytest.mark.asyncio
    async def test_get_all_descendants_diamond_pattern(self):
        """Test get_all_descendants with diamond pattern (shared descendants).

        This covers line 260->259 FALSE: when child.id is already in visited set.
        Structure: parent has two children (child1, child2), both have same grandchild.
        """
        parent = Tag(id="1", name="Parent", parents=[], children=[])
        child1 = Tag(id="2", name="Child1", parents=[], children=[])
        child2 = Tag(id="3", name="Child2", parents=[], children=[])
        grandchild = Tag(id="4", name="Grandchild", parents=[], children=[])

        # Build diamond: parent -> child1 -> grandchild
        #                       -> child2 -> grandchild (shared)
        await parent.add_child(child1)
        await parent.add_child(child2)
        await child1.add_child(grandchild)
        await child2.add_child(grandchild)  # Same grandchild from different path

        descendants = await parent.get_all_descendants()

        # Should have all 3 descendants but grandchild only appears once (deduplication)
        assert len(descendants) == 3
        assert child1 in descendants
        assert child2 in descendants
        assert grandchild in descendants
        # Verify grandchild appears only once despite two paths to it
        assert descendants.count(grandchild) == 1

    @pytest.mark.asyncio
    async def test_get_all_ancestors_diamond_pattern(self):
        """Test get_all_ancestors with diamond pattern (shared ancestors).

        This covers line 280->279 FALSE: when parent.id is already in visited set.
        Structure: child has two parents (parent1, parent2), both have same grandparent.
        """
        grandparent = Tag(id="1", name="Grandparent", parents=[], children=[])
        parent1 = Tag(id="2", name="Parent1", parents=[], children=[])
        parent2 = Tag(id="3", name="Parent2", parents=[], children=[])
        child = Tag(id="4", name="Child", parents=[], children=[])

        # Build diamond: child -> parent1 -> grandparent
        #                      -> parent2 -> grandparent (shared)
        await child.add_parent(parent1)
        await child.add_parent(parent2)
        await parent1.add_parent(grandparent)
        await parent2.add_parent(grandparent)  # Same grandparent from different path

        ancestors = await child.get_all_ancestors()

        # Should have all 3 ancestors but grandparent only appears once (deduplication)
        assert len(ancestors) == 3
        assert parent1 in ancestors
        assert parent2 in ancestors
        assert grandparent in ancestors
        # Verify grandparent appears only once despite two paths to it
        assert ancestors.count(grandparent) == 1

    @pytest.mark.asyncio
    async def test_get_all_descendants_with_unset_children(self):
        """Test get_all_descendants when a child tag has UNSET children (early exit).

        This covers the 195->exit branch: when tag.children is UNSET, the recursion
        stops early without trying to iterate.
        """
        # Create child with UNSET children (not loaded from GraphQL)
        child = Tag.model_construct(id="2", name="Child", children=UNSET, parents=[])
        parent = Tag(id="1", name="Parent", children=[child], parents=[])

        # Should not crash, recursion stops at child (early exit)
        descendants = await parent.get_all_descendants()

        # Should only have the one child (recursion stopped)
        assert len(descendants) == 1
        assert descendants[0] == child

    @pytest.mark.asyncio
    async def test_get_all_ancestors_with_unset_parents(self):
        """Test get_all_ancestors when a parent tag has UNSET parents (early exit).

        This covers the 218->exit branch: when tag.parents is UNSET, the recursion
        stops early without trying to iterate.
        """
        # Create parent with UNSET parents (not loaded from GraphQL)
        parent = Tag.model_construct(id="2", name="Parent", parents=UNSET, children=[])
        child = Tag(id="1", name="Child", parents=[parent], children=[])

        # Should not crash, recursion stops at parent (early exit)
        ancestors = await child.get_all_ancestors()

        # Should only have the one parent (recursion stopped)
        assert len(ancestors) == 1
        assert ancestors[0] == parent
