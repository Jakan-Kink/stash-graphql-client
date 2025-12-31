"""Integration tests for group mixin functionality.

Tests group operations against a real Stash instance.

These tests are written BEFORE the implementation exists (TDD approach).
Tests will fail with AttributeError until GroupClientMixin is implemented.

NOTE: Tests use the stash_cleanup_tracker to ensure proper cleanup of
created objects. CRUD tests manually register created groups with
`cleanup['groups'].append(group.id)` to enable proper cleanup tracking.
Once tests are verified to properly clean up, they may qualify for
auto_capture=False optimization (requires manual verification).
"""

import pytest

from stash_graphql_client import StashClient
from stash_graphql_client.types import Group
from stash_graphql_client.types.unset import is_set
from tests.fixtures import capture_graphql_calls


# =============================================================================
# Read-only group tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_groups_returns_results(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding groups returns results (may be empty)."""
    async with (
        stash_cleanup_tracker(stash_client),
        capture_graphql_calls(stash_client) as calls,
    ):
        result = await stash_client.find_groups()

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_groups"
        assert "findGroups" in calls[0]["query"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Result should be valid even if empty
        assert is_set(result.count)
        assert result.count >= 0
        assert isinstance(result.groups, list)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_groups_with_pagination(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test group pagination works correctly."""
    async with (
        stash_cleanup_tracker(stash_client),
        capture_graphql_calls(stash_client) as calls,
    ):
        result = await stash_client.find_groups(filter_={"per_page": 10, "page": 1})

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_groups"
        assert "findGroups" in calls[0]["query"]
        assert calls[0]["variables"]["filter"]["per_page"] == 10
        assert calls[0]["variables"]["filter"]["page"] == 1
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        assert is_set(result.groups)
        assert len(result.groups) <= 10


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_nonexistent_group_returns_none(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding a nonexistent group returns None."""
    async with (
        stash_cleanup_tracker(stash_client),
        capture_graphql_calls(stash_client) as calls,
    ):
        group = await stash_client.find_group("99999999")

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_group"
        assert "findGroup" in calls[0]["query"]
        assert calls[0]["variables"]["id"] == "99999999"
        assert calls[0]["exception"] is None

        assert group is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_groups_with_q_parameter(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding groups using q search parameter."""
    async with (
        stash_cleanup_tracker(stash_client),
        capture_graphql_calls(stash_client) as calls,
    ):
        result = await stash_client.find_groups(q="test")

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_groups"
        assert "findGroups" in calls[0]["query"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Should return valid result (may or may not have matches)
        assert is_set(result.count)
        assert result.count >= 0
        assert isinstance(result.groups, list)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_groups_with_filter(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding groups using group_filter."""
    async with (
        stash_cleanup_tracker(stash_client),
        capture_graphql_calls(stash_client) as calls,
    ):
        # Search for a group that likely doesn't exist
        result = await stash_client.find_groups(
            group_filter={
                "name": {"value": "NonexistentGroup12345", "modifier": "EQUALS"}
            }
        )

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_groups"
        assert "findGroups" in calls[0]["query"]
        assert "group_filter" in calls[0]["variables"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        assert result.count == 0
        assert is_set(result.groups)
        assert len(result.groups) == 0


# =============================================================================
# CRUD tests (create groups - cleanup tracker handles deletion)
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_and_find_group(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test creating a group and finding it by ID."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        # Create a new group
        group = Group.new(
            name="Integration Test Group",
            director="Test Director",
            synopsis="A test group for integration testing",
        )
        created_group = await stash_client.create_group(group)
        cleanup["groups"].append(created_group.id)  # Manual cleanup registration

        # Verify creation call
        assert len(calls) == 1, "Expected 1 GraphQL call for create_group"
        assert "groupCreate" in calls[0]["query"]
        assert calls[0]["variables"]["input"]["name"] == "Integration Test Group"
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        assert created_group is not None
        assert created_group.id is not None
        assert created_group.name == "Integration Test Group"
        assert created_group.director == "Test Director"

        # Find the group by ID
        calls.clear()
        found_group = await stash_client.find_group(created_group.id)

        # Verify find call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_group"
        assert "findGroup" in calls[0]["query"]
        assert calls[0]["variables"]["id"] == created_group.id
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        assert found_group is not None
        assert found_group.id == created_group.id
        assert found_group.name == "Integration Test Group"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_and_update_group(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test creating and updating a group."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        # Create a new group
        group = Group.new(
            name="Group To Update",
            director="Original Director",
        )
        created_group = await stash_client.create_group(group)
        cleanup["groups"].append(created_group.id)  # Manual cleanup registration

        # Verify creation call
        assert len(calls) == 1, "Expected 1 GraphQL call for create_group"
        assert "groupCreate" in calls[0]["query"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        assert created_group.director == "Original Director"

        # Update the group
        calls.clear()
        created_group.director = "Updated Director"
        created_group.synopsis = "Added synopsis"
        updated_group = await stash_client.update_group(created_group)

        # Verify update call
        assert len(calls) == 1, "Expected 1 GraphQL call for update_group"
        assert "groupUpdate" in calls[0]["query"]
        assert calls[0]["variables"]["input"]["id"] == created_group.id
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        assert updated_group.director == "Updated Director"
        assert updated_group.synopsis == "Added synopsis"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_and_destroy_group(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test creating and destroying a group."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        # Does not require cleanup as we are destroying the group immediately after creation
        # Create a new group
        group = Group.new(name="Group To Destroy")
        created_group = await stash_client.create_group(group)

        # Verify creation call
        assert len(calls) == 1, "Expected 1 GraphQL call for create_group"
        assert "groupCreate" in calls[0]["query"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        assert created_group.id is not None

        # Destroy the group
        calls.clear()
        result = await stash_client.group_destroy({"id": created_group.id})

        # Verify destroy call
        assert len(calls) == 1, "Expected 1 GraphQL call for group_destroy"
        assert "groupDestroy" in calls[0]["query"]
        assert calls[0]["variables"]["input"]["id"] == created_group.id
        assert calls[0]["exception"] is None

        assert result is True

        # Verify it's gone
        calls.clear()
        found_group = await stash_client.find_group(created_group.id)

        assert len(calls) == 1, "Expected 1 GraphQL call for find_group"
        assert "findGroup" in calls[0]["query"]
        assert calls[0]["exception"] is None

        assert found_group is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_multiple_and_destroy_groups(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test creating multiple groups and destroying them in bulk."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        # Does not require cleanup as we are destroying the groups immediately after creation
        # Create multiple groups
        group1 = await stash_client.create_group(Group.new(name="Bulk Destroy Group 1"))
        group2 = await stash_client.create_group(Group.new(name="Bulk Destroy Group 2"))
        group3 = await stash_client.create_group(Group.new(name="Bulk Destroy Group 3"))

        # Verify 3 creation calls
        assert len(calls) == 3, "Expected 3 GraphQL calls for creating groups"
        for call in calls:
            assert "groupCreate" in call["query"]
            assert call["result"] is not None
            assert call["exception"] is None

        group_ids = [group1.id, group2.id, group3.id]

        # Destroy all groups at once
        calls.clear()
        result = await stash_client.groups_destroy(group_ids)

        # Verify destroy call
        assert len(calls) == 1, "Expected 1 GraphQL call for groups_destroy"
        assert "groupsDestroy" in calls[0]["query"]
        assert calls[0]["exception"] is None

        assert result is True

        # Verify they're all gone
        calls.clear()
        for group_id in group_ids:
            found = await stash_client.find_group(group_id)
            assert found is None

        # Verify find calls
        assert len(calls) == 3, "Expected 3 GraphQL calls for finding groups"
        for call in calls:
            assert "findGroup" in call["query"]
            assert call["exception"] is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_group_with_duration_and_date(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test creating a group with duration and date fields."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        group = Group.new(
            name="Group With Metadata",
            duration=7200,  # 2 hours in seconds
            date="2024-01-15",
            rating100=85,
        )
        created_group = await stash_client.create_group(group)
        cleanup["groups"].append(created_group.id)  # Manual cleanup registration

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for create_group"
        assert "groupCreate" in calls[0]["query"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        assert created_group.duration == 7200
        assert created_group.date == "2024-01-15"
        assert created_group.rating100 == 85


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_group_with_urls(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test creating a group with URLs."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        group = Group.new(
            name="Group With URLs",
            urls=["https://example.com/group1", "https://example.com/group2"],
        )
        created_group = await stash_client.create_group(group)
        cleanup["groups"].append(created_group.id)  # Manual cleanup registration

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for create_group"
        assert "groupCreate" in calls[0]["query"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        assert is_set(created_group.urls)
        assert len(created_group.urls) == 2
        assert "https://example.com/group1" in created_group.urls


# =============================================================================
# Bulk update tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_bulk_group_update(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test bulk updating multiple groups."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        # Create multiple groups
        created_groups = []
        for i in range(3):
            group = await stash_client.create_group(
                Group.new(name=f"Bulk Update Group {i}")
            )
            created_groups.append(group)
            cleanup["groups"].append(group.id)  # Manual cleanup registration

        # Verify creation calls
        assert len(calls) == 3, "Expected 3 GraphQL calls for creating groups"
        for call in calls:
            assert "groupCreate" in call["query"]
            assert call["result"] is not None
            assert call["exception"] is None

        group_ids = [g.id for g in created_groups]

        # Bulk update all groups
        calls.clear()
        updated = await stash_client.bulk_group_update(
            {"ids": group_ids, "rating100": 75}
        )

        # Verify bulk update call
        assert len(calls) == 1, "Expected 1 GraphQL call for bulk_group_update"
        assert "bulkGroupUpdate" in calls[0]["query"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        assert len(updated) == 3
        for group in updated:
            assert group.rating100 == 75


# =============================================================================
# Sub-group relationship tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_add_and_remove_sub_groups(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test adding and removing sub-groups from a parent group."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        # Create parent and child groups
        parent_group = await stash_client.create_group(Group.new(name="Parent Group"))
        cleanup["groups"].append(parent_group.id)  # Manual cleanup registration

        child_group1 = await stash_client.create_group(Group.new(name="Child Group 1"))
        cleanup["groups"].append(child_group1.id)  # Manual cleanup registration

        child_group2 = await stash_client.create_group(Group.new(name="Child Group 2"))
        cleanup["groups"].append(child_group2.id)  # Manual cleanup registration

        # Verify creation calls
        assert len(calls) == 3, "Expected 3 GraphQL calls for creating groups"
        for call in calls:
            assert "groupCreate" in call["query"]
            assert call["result"] is not None
            assert call["exception"] is None

        # Add sub-groups
        calls.clear()
        result = await stash_client.add_group_sub_groups(
            {
                "containing_group_id": parent_group.id,
                "sub_groups": [
                    {"group_id": child_group1.id},
                    {"group_id": child_group2.id},
                ],
            }
        )

        # Verify add call
        assert len(calls) == 1, "Expected 1 GraphQL call for add_group_sub_groups"
        assert "addGroupSubGroups" in calls[0]["query"]
        assert calls[0]["exception"] is None

        assert result is True

        # Verify sub-groups were added
        calls.clear()
        updated_parent = await stash_client.find_group(parent_group.id)

        assert len(calls) == 1, "Expected 1 GraphQL call for find_group"
        assert "findGroup" in calls[0]["query"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        assert updated_parent is not None
        assert is_set(updated_parent.sub_groups)
        assert len(updated_parent.sub_groups) == 2

        # Remove one sub-group
        calls.clear()
        result = await stash_client.remove_group_sub_groups(
            {
                "containing_group_id": parent_group.id,
                "sub_group_ids": [child_group1.id],
            }
        )

        # Verify remove call
        assert len(calls) == 1, "Expected 1 GraphQL call for remove_group_sub_groups"
        assert "removeGroupSubGroups" in calls[0]["query"]
        assert calls[0]["exception"] is None

        assert result is True

        # Verify sub-group was removed
        calls.clear()
        updated_parent = await stash_client.find_group(parent_group.id)

        assert len(calls) == 1, "Expected 1 GraphQL call for find_group"
        assert "findGroup" in calls[0]["query"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        assert updated_parent is not None
        assert is_set(updated_parent.sub_groups)
        assert len(updated_parent.sub_groups) == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_reorder_sub_groups(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test reordering sub-groups within a parent group."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        # Create parent and multiple child groups
        parent_group = await stash_client.create_group(
            Group.new(name="Parent For Reorder")
        )
        cleanup["groups"].append(parent_group.id)  # Manual cleanup registration

        child_groups = []
        for i in range(3):
            child = await stash_client.create_group(
                Group.new(name=f"Reorder Child {i}")
            )
            child_groups.append(child)
            cleanup["groups"].append(child.id)  # Manual cleanup registration

        # Verify creation calls (4 total: 1 parent + 3 children)
        assert len(calls) == 4, "Expected 4 GraphQL calls for creating groups"
        for call in calls:
            assert "groupCreate" in call["query"]
            assert call["result"] is not None
            assert call["exception"] is None

        # Add all sub-groups
        calls.clear()
        await stash_client.add_group_sub_groups(
            {
                "containing_group_id": parent_group.id,
                "sub_groups": [{"group_id": c.id} for c in child_groups],
            }
        )

        # Verify add call
        assert len(calls) == 1, "Expected 1 GraphQL call for add_group_sub_groups"
        assert "addGroupSubGroups" in calls[0]["query"]
        assert calls[0]["exception"] is None

        # Reorder: move first child to after second
        calls.clear()
        result = await stash_client.reorder_sub_groups(
            {
                "group_id": parent_group.id,
                "sub_group_ids": [child_groups[0].id],
                "insert_at_id": child_groups[1].id,
                "insert_after": True,
            }
        )

        # Verify reorder call
        assert len(calls) == 1, "Expected 1 GraphQL call for reorder_sub_groups"
        assert "reorderSubGroups" in calls[0]["query"]
        assert calls[0]["exception"] is None

        assert result is True


# =============================================================================
# Find group by ID after creation (verifies round-trip)
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_group_by_id_returns_complete_data(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test that find_group returns all expected fields."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        # Create a group with all optional fields
        group = Group.new(
            name="Complete Group",
            aliases="complete, test, full",
            duration=3600,
            date="2024-06-15",
            rating100=90,
            director="Test Director",
            synopsis="A complete test group with all fields",
            urls=["https://example.com/complete"],
        )
        created_group = await stash_client.create_group(group)
        cleanup["groups"].append(created_group.id)  # Manual cleanup registration

        # Verify creation call
        assert len(calls) == 1, "Expected 1 GraphQL call for create_group"
        assert "groupCreate" in calls[0]["query"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Find the group and verify all fields
        calls.clear()
        found = await stash_client.find_group(created_group.id)

        # Verify find call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_group"
        assert "findGroup" in calls[0]["query"]
        assert calls[0]["variables"]["id"] == created_group.id
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        assert found is not None
        assert found.name == "Complete Group"
        assert found.aliases == "complete, test, full"
        assert found.duration == 3600
        assert found.date == "2024-06-15"
        assert found.rating100 == 90
        assert found.director == "Test Director"
        assert found.synopsis == "A complete test group with all fields"
        assert is_set(found.urls)
        assert len(found.urls) == 1
