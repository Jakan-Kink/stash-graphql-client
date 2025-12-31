"""Unit tests for GroupClientMixin.

These tests are written BEFORE the implementation exists (TDD approach).
Tests will fail with ImportError or AttributeError until GroupClientMixin
is implemented in stash_graphql_client/client/mixins/group.py.

Tests mock at the HTTP boundary using respx, allowing real code execution
through the entire GraphQL client stack including serialization/deserialization.
"""

import json

import httpx
import pytest
import respx

from stash_graphql_client import StashClient
from stash_graphql_client.errors import StashGraphQLError
from stash_graphql_client.types import (
    BulkGroupUpdateInput,
    BulkUpdateIdMode,
    BulkUpdateIds,
    Group,
    GroupDescriptionInput,
    GroupDestroyInput,
    GroupSubGroupAddInput,
    GroupSubGroupRemoveInput,
    ReorderSubGroupsInput,
)
from stash_graphql_client.types.unset import is_set
from tests.fixtures import (
    create_find_groups_result,
    create_graphql_response,
    create_group_dict,
    create_tag_dict,
)


# =============================================================================
# find_group tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_group_by_id(respx_stash_client: StashClient) -> None:
    """Test finding a group by ID."""
    group_data = create_group_dict(
        id="123",
        name="Test Group",
        duration=3600,
        director="Test Director",
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("findGroup", group_data))
        ]
    )

    group = await respx_stash_client.find_group("123")

    assert group is not None
    assert group.id == "123"
    assert group.name == "Test Group"
    assert group.duration == 3600
    assert group.director == "Test Director"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "findGroup" in req["query"]
    assert req["variables"]["id"] == "123"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_group_not_found(respx_stash_client: StashClient) -> None:
    """Test finding a group that doesn't exist."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("findGroup", None))
        ]
    )

    group = await respx_stash_client.find_group("999")

    assert group is None
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_group_error_returns_none(respx_stash_client: StashClient) -> None:
    """Test that find_group returns None on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    group = await respx_stash_client.find_group("error_id")

    assert group is None
    assert len(graphql_route.calls) == 1


# =============================================================================
# find_groups tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_groups(respx_stash_client: StashClient) -> None:
    """Test finding groups."""
    group_data = create_group_dict(id="123", name="Test Group")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findGroups",
                    create_find_groups_result(count=1, groups=[group_data]),
                ),
            )
        ]
    )

    result = await respx_stash_client.find_groups()

    assert result.count == 1
    assert is_set(result.groups)
    assert len(result.groups) == 1
    assert result.groups[0].name == "Test Group"

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_groups_with_filter(respx_stash_client: StashClient) -> None:
    """Test finding groups with filter."""
    group_data = create_group_dict(id="123", name="Action Movie")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findGroups",
                    create_find_groups_result(count=1, groups=[group_data]),
                ),
            )
        ]
    )

    result = await respx_stash_client.find_groups(
        filter_={"per_page": 10, "page": 1},
        group_filter={"name": {"value": "Action", "modifier": "INCLUDES"}},
    )

    assert result.count == 1
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_groups_with_query(respx_stash_client: StashClient) -> None:
    """Test finding groups with search query."""
    group_data = create_group_dict(id="123", name="Test Series")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findGroups",
                    create_find_groups_result(count=1, groups=[group_data]),
                ),
            )
        ]
    )

    result = await respx_stash_client.find_groups(q="Test")

    assert result.count == 1
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["filter"]["q"] == "Test"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_groups_empty(respx_stash_client: StashClient) -> None:
    """Test finding groups when none exist."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findGroups", create_find_groups_result(count=0, groups=[])
                ),
            )
        ]
    )

    result = await respx_stash_client.find_groups()

    assert result.count == 0
    assert is_set(result.groups)
    assert len(result.groups) == 0
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_groups_error_returns_empty(
    respx_stash_client: StashClient,
) -> None:
    """Test that find_groups returns empty result on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    result = await respx_stash_client.find_groups()

    assert result.count == 0
    assert is_set(result.groups)
    assert len(result.groups) == 0
    assert len(graphql_route.calls) == 1


# =============================================================================
# create_group tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_group(respx_stash_client: StashClient) -> None:
    """Test creating a group."""
    group_data = create_group_dict(
        id="123",
        name="New Group",
        duration=7200,
        director="Test Director",
        synopsis="A test group",
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("groupCreate", group_data))
        ]
    )

    group = Group(id="new", name="New Group", duration=7200, director="Test Director")
    created = await respx_stash_client.create_group(group)

    assert created.id == "123"
    assert created.name == "New Group"
    assert created.duration == 7200
    assert created.director == "Test Director"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "groupCreate" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_group_with_tags(respx_stash_client: StashClient) -> None:
    """Test creating a group with tags."""
    tag_data = create_tag_dict(id="tag1", name="Action")
    group_data = create_group_dict(
        id="123",
        name="Action Movie",
        tags=[tag_data],
    )

    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("groupCreate", group_data))
        ]
    )

    group = Group(id="new", name="Action Movie")
    created = await respx_stash_client.create_group(group)

    assert created.id == "123"
    assert is_set(created.tags)
    assert len(created.tags) == 1
    assert created.tags[0].name == "Action"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_group_error_raises(respx_stash_client: StashClient) -> None:
    """Test that create_group raises on error when id is incorrectly included."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "errors": [
                        {
                            "message": "unknown field",
                            "path": ["variable", "input", "id"],
                            "extensions": {"code": "GRAPHQL_VALIDATION_FAILED"},
                        }
                    ]
                },
            )
        ]
    )

    group = Group(id="temp", name="New Group")

    with pytest.raises(StashGraphQLError, match="unknown field"):
        await respx_stash_client.create_group(group)

    assert len(graphql_route.calls) == 1


# =============================================================================
# update_group tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_group(respx_stash_client: StashClient) -> None:
    """Test updating a group."""
    group_data = create_group_dict(
        id="123",
        name="Updated Group",
        director="New Director",
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("groupUpdate", group_data))
        ]
    )

    group = Group(id="123", name="Updated Group", director="New Director")
    updated = await respx_stash_client.update_group(group)

    assert updated.id == "123"
    assert updated.name == "Updated Group"
    assert updated.director == "New Director"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "groupUpdate" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_group_error_raises(respx_stash_client: StashClient) -> None:
    """Test that update_group raises on error."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    group = Group(id="123", name="Test")

    with pytest.raises(StashGraphQLError, match="Server error"):
        await respx_stash_client.update_group(group)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_group_without_id_raises(respx_stash_client: StashClient) -> None:
    """Test that update_group raises ValueError when group has no ID."""
    group = Group(id="", name="Test")  # Group with empty ID
    group.id = ""  # Ensure ID is empty

    with pytest.raises(ValueError, match="Group must have an ID to update"):
        await respx_stash_client.update_group(group)


# =============================================================================
# group_destroy tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_group_destroy_with_dict(respx_stash_client: StashClient) -> None:
    """Test deleting a group with dict input."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("groupDestroy", True))
        ]
    )

    result = await respx_stash_client.group_destroy({"id": "123"})

    assert result is True
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "groupDestroy" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_group_destroy_with_input_type(respx_stash_client: StashClient) -> None:
    """Test deleting a group with GroupDestroyInput."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("groupDestroy", True))
        ]
    )

    input_data = GroupDestroyInput(id="123")
    result = await respx_stash_client.group_destroy(input_data)

    assert result is True
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_group_destroy_error_raises(respx_stash_client: StashClient) -> None:
    """Test that group_destroy raises on error."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    with pytest.raises(StashGraphQLError, match="Server error"):
        await respx_stash_client.group_destroy({"id": "123"})


# =============================================================================
# groups_destroy tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_groups_destroy(respx_stash_client: StashClient) -> None:
    """Test deleting multiple groups."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("groupsDestroy", True))
        ]
    )

    result = await respx_stash_client.groups_destroy(["123", "456", "789"])

    assert result is True
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "groupsDestroy" in req["query"]
    assert req["variables"]["ids"] == ["123", "456", "789"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_groups_destroy_error_raises(respx_stash_client: StashClient) -> None:
    """Test that groups_destroy raises on error."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    with pytest.raises(StashGraphQLError, match="Server error"):
        await respx_stash_client.groups_destroy(["123", "456"])


# =============================================================================
# bulk_group_update tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_bulk_group_update_with_dict(respx_stash_client: StashClient) -> None:
    """Test bulk updating groups with dict input."""
    group_data = [
        create_group_dict(id="1", name="Group 1", rating100=80),
        create_group_dict(id="2", name="Group 2", rating100=80),
    ]

    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("bulkGroupUpdate", group_data)
            )
        ]
    )

    result = await respx_stash_client.bulk_group_update(
        {"ids": ["1", "2"], "rating100": 80}
    )

    assert len(result) == 2
    assert result[0].rating100 == 80
    assert result[1].rating100 == 80


@pytest.mark.asyncio
@pytest.mark.unit
async def test_bulk_group_update_with_input_type(
    respx_stash_client: StashClient,
) -> None:
    """Test bulk updating groups with BulkGroupUpdateInput."""
    group_data = [
        create_group_dict(id="1", name="Group 1"),
        create_group_dict(id="2", name="Group 2"),
    ]

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("bulkGroupUpdate", group_data)
            )
        ]
    )

    input_data = BulkGroupUpdateInput(
        ids=["1", "2"],
        tag_ids=BulkUpdateIds(ids=["tag1", "tag2"], mode=BulkUpdateIdMode.ADD),
    )
    result = await respx_stash_client.bulk_group_update(input_data)

    assert len(result) == 2
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_bulk_group_update_error_raises(respx_stash_client: StashClient) -> None:
    """Test that bulk_group_update raises on error."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    input_data = BulkGroupUpdateInput(ids=["1", "2"], rating100=80)

    with pytest.raises(StashGraphQLError, match="Server error"):
        await respx_stash_client.bulk_group_update(input_data)


# =============================================================================
# add_group_sub_groups tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_add_group_sub_groups_with_dict(respx_stash_client: StashClient) -> None:
    """Test adding sub groups with dict input."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("addGroupSubGroups", True))
        ]
    )

    result = await respx_stash_client.add_group_sub_groups(
        {
            "containing_group_id": "parent_123",
            "sub_groups": [{"group_id": "child_456"}],
        }
    )

    assert result is True
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_add_group_sub_groups_with_input_type(
    respx_stash_client: StashClient,
) -> None:
    """Test adding sub groups with GroupSubGroupAddInput."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("addGroupSubGroups", True))
        ]
    )

    input_data = GroupSubGroupAddInput(
        containing_group_id="parent_123",
        sub_groups=[GroupDescriptionInput(group_id="child_456")],
        insert_index=0,
    )
    result = await respx_stash_client.add_group_sub_groups(input_data)

    assert result is True


@pytest.mark.asyncio
@pytest.mark.unit
async def test_add_group_sub_groups_error_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test that add_group_sub_groups raises on error."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    with pytest.raises(StashGraphQLError, match="Server error"):
        await respx_stash_client.add_group_sub_groups(
            {"containing_group_id": "123", "sub_groups": [{"group_id": "456"}]}
        )


# =============================================================================
# remove_group_sub_groups tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_remove_group_sub_groups_with_dict(
    respx_stash_client: StashClient,
) -> None:
    """Test removing sub groups with dict input."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("removeGroupSubGroups", True)
            )
        ]
    )

    result = await respx_stash_client.remove_group_sub_groups(
        {
            "containing_group_id": "parent_123",
            "sub_group_ids": ["child_456", "child_789"],
        }
    )

    assert result is True
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_remove_group_sub_groups_with_input_type(
    respx_stash_client: StashClient,
) -> None:
    """Test removing sub groups with GroupSubGroupRemoveInput."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("removeGroupSubGroups", True)
            )
        ]
    )

    input_data = GroupSubGroupRemoveInput(
        containing_group_id="parent_123",
        sub_group_ids=["child_456", "child_789"],
    )
    result = await respx_stash_client.remove_group_sub_groups(input_data)

    assert result is True


@pytest.mark.asyncio
@pytest.mark.unit
async def test_remove_group_sub_groups_error_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test that remove_group_sub_groups raises on error."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    with pytest.raises(StashGraphQLError, match="Server error"):
        await respx_stash_client.remove_group_sub_groups(
            {"containing_group_id": "123", "sub_group_ids": ["456"]}
        )


# =============================================================================
# reorder_sub_groups tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_reorder_sub_groups_with_dict(respx_stash_client: StashClient) -> None:
    """Test reordering sub groups with dict input."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("reorderSubGroups", True))
        ]
    )

    result = await respx_stash_client.reorder_sub_groups(
        {
            "group_id": "parent_123",
            "sub_group_ids": ["child_1", "child_2", "child_3"],
            "insert_at_id": "child_1",
            "insert_after": True,
        }
    )

    assert result is True
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_reorder_sub_groups_with_input_type(
    respx_stash_client: StashClient,
) -> None:
    """Test reordering sub groups with ReorderSubGroupsInput."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("reorderSubGroups", True))
        ]
    )

    input_data = ReorderSubGroupsInput(
        group_id="parent_123",
        sub_group_ids=["child_1", "child_2"],
        insert_at_id="child_1",
        insert_after=False,
    )
    result = await respx_stash_client.reorder_sub_groups(input_data)

    assert result is True


@pytest.mark.asyncio
@pytest.mark.unit
async def test_reorder_sub_groups_error_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test that reorder_sub_groups raises on error."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    with pytest.raises(StashGraphQLError, match="Server error"):
        await respx_stash_client.reorder_sub_groups(
            {
                "group_id": "123",
                "sub_group_ids": ["1", "2"],
                "insert_at_id": "1",
                "insert_after": True,
            }
        )
