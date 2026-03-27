"""Unit tests for StudioClientMixin.

These tests mock at the HTTP boundary using respx, allowing real code execution
through the entire GraphQL client stack including serialization/deserialization.
"""

import json
from typing import Any
from unittest.mock import patch

import httpx
import pytest
import respx

from stash_graphql_client import StashClient
from stash_graphql_client.errors import StashGraphQLError
from stash_graphql_client.types import (
    BulkStudioUpdateInput,
    BulkUpdateIdMode,
    BulkUpdateIds,
    Studio,
    StudioDestroyInput,
)
from stash_graphql_client.types.unset import UNSET, is_set
from tests.fixtures import (
    create_find_studios_result,
    create_graphql_response,
    create_studio_dict,
    dump_graphql_calls,
)


# =============================================================================
# find_studio tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_studio_by_id(respx_stash_client: StashClient) -> None:
    """Test finding a studio by ID."""
    studio_data = create_studio_dict(id="123", name="Test Studio")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("findStudio", studio_data))
        ]
    )

    try:
        studio = await respx_stash_client.find_studio("123")
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert studio is not None
    assert studio.id == "123"
    assert studio.name == "Test Studio"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "findStudio" in req["query"]
    assert req["variables"]["id"] == "123"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_studio_not_found(respx_stash_client: StashClient) -> None:
    """Test finding a studio that doesn't exist."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("findStudio", None))
        ]
    )

    try:
        studio = await respx_stash_client.find_studio("999")
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert studio is None
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_studio_error_returns_none(respx_stash_client: StashClient) -> None:
    """Test that find_studio returns None on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    try:
        studio = await respx_stash_client.find_studio("error_id")
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert studio is None
    assert len(graphql_route.calls) == 1


# =============================================================================
# find_studios tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_studios(respx_stash_client: StashClient) -> None:
    """Test finding studios."""
    studio_data = create_studio_dict(id="123", name="Test Studio")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findStudios",
                    create_find_studios_result(count=1, studios=[studio_data]),
                ),
            )
        ]
    )

    try:
        result = await respx_stash_client.find_studios()
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert result.count == 1
    assert is_set(result.studios)
    assert result.studios is not None
    assert len(result.studios) == 1
    assert result.studios[0].id == "123"

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_studios_with_q_parameter(respx_stash_client: StashClient) -> None:
    """Test finding studios with q parameter."""
    studio_data = create_studio_dict(id="123", name="Search Result")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findStudios",
                    create_find_studios_result(count=1, studios=[studio_data]),
                ),
            )
        ]
    )

    try:
        result = await respx_stash_client.find_studios(q="Search Result")
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert result.count == 1
    assert is_set(result.studios)
    assert result.studios is not None
    assert result.studios[0].name == "Search Result"

    # Verify q was passed in filter
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["filter"]["q"] == "Search Result"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_studios_with_custom_filter(respx_stash_client: StashClient) -> None:
    """Test finding studios with custom filter_ parameter."""
    studio_data = create_studio_dict(id="123", name="Paginated Result")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findStudios",
                    create_find_studios_result(count=1, studios=[studio_data]),
                ),
            )
        ]
    )

    try:
        result = await respx_stash_client.find_studios(
            filter_={"page": 2, "per_page": 10, "sort": "name", "direction": "ASC"}
        )
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert result.count == 1
    assert is_set(result.studios)
    assert result.studios is not None
    assert result.studios[0].name == "Paginated Result"

    # Verify the custom filter was passed
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["filter"]["page"] == 2
    assert req["variables"]["filter"]["per_page"] == 10


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_studios_error_returns_empty(
    respx_stash_client: StashClient,
) -> None:
    """Test that find_studios returns empty result on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    try:
        result = await respx_stash_client.find_studios()
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert result.count == 0
    assert is_set(result.studios)
    assert result.studios is not None
    assert len(result.studios) == 0

    assert len(graphql_route.calls) == 1


# =============================================================================
# create_studio tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_studio(respx_stash_client: StashClient) -> None:
    """Test creating a studio.

    This covers lines 96-103: successful creation.
    """
    created_studio_data = create_studio_dict(
        id="9001",
        name="New Studio",
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("studioCreate", created_studio_data)
            )
        ]
    )

    studio = Studio(id="9999", name="New Studio")
    try:
        result = await respx_stash_client.create_studio(studio)
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert result is not None
    assert result.id == "9001"
    assert result.name == "New Studio"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "studioCreate" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_studio_error_raises(respx_stash_client: StashClient) -> None:
    """Test that create_studio raises on error.

    This covers lines 104-106: exception handling.
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    studio = Studio(id="9999", name="Will Fail")

    try:
        with pytest.raises(StashGraphQLError):
            await respx_stash_client.create_studio(studio)
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert len(graphql_route.calls) == 1


# =============================================================================
# update_studio tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_studio(respx_stash_client: StashClient) -> None:
    """Test updating a studio.

    This covers lines 124-131: successful update.
    """
    updated_studio_data = create_studio_dict(
        id="123",
        name="Updated Studio",
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("studioUpdate", updated_studio_data)
            )
        ]
    )

    studio = Studio(id="123", name="Original Name")
    studio.name = "Updated Studio"

    try:
        result = await respx_stash_client.update_studio(studio)
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert result is not None
    assert result.id == "123"
    assert result.name == "Updated Studio"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "studioUpdate" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_studio_error_raises(respx_stash_client: StashClient) -> None:
    """Test that update_studio raises on error.

    This covers lines 132-134: exception handling.
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    studio = Studio(id="123", name="Will Fail")

    try:
        with pytest.raises(StashGraphQLError):
            await respx_stash_client.update_studio(studio)
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert len(graphql_route.calls) == 1


# =============================================================================
# studio_destroy tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_studio_destroy_with_dict(respx_stash_client: StashClient) -> None:
    """Test destroying a studio with dict input."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("studioDestroy", True))
        ]
    )

    try:
        result = await respx_stash_client.studio_destroy({"id": "123"})
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert result is True

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "studioDestroy" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_studio_destroy_with_input_type(respx_stash_client: StashClient) -> None:
    """Test destroying a studio with StudioDestroyInput.

    This covers line 154-155: if isinstance(input_data, StudioDestroyInput).
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("studioDestroy", True))
        ]
    )

    input_data = StudioDestroyInput(id="123")
    try:
        result = await respx_stash_client.studio_destroy(input_data)
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert result is True

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "studioDestroy" in req["query"]
    assert req["variables"]["input"]["id"] == "123"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_studio_destroy_error_raises(respx_stash_client: StashClient) -> None:
    """Test that studio_destroy raises on error.

    This covers lines 165-167: exception handling.
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    try:
        with pytest.raises(StashGraphQLError):
            await respx_stash_client.studio_destroy({"id": "123"})
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert len(graphql_route.calls) == 1


# =============================================================================
# studios_destroy tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_studios_destroy(respx_stash_client: StashClient) -> None:
    """Test destroying multiple studios."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("studiosDestroy", True))
        ]
    )

    try:
        result = await respx_stash_client.studios_destroy(["123", "456", "789"])
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert result is True

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "studiosDestroy" in req["query"]
    assert req["variables"]["ids"] == ["123", "456", "789"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_studios_destroy_error_raises(respx_stash_client: StashClient) -> None:
    """Test that studios_destroy raises on error.

    This covers lines 189-191: exception handling.
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    try:
        with pytest.raises(StashGraphQLError):
            await respx_stash_client.studios_destroy(["123", "456"])
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert len(graphql_route.calls) == 1


# =============================================================================
# bulk_studio_update tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_bulk_studio_update_with_dict(respx_stash_client: StashClient) -> None:
    """Test bulk updating studios with dict input.

    This covers lines 231-232: else branch when input_data is a dict.
    """
    updated_studios_data = [
        create_studio_dict(id="1", name="Studio 1"),
        create_studio_dict(id="2", name="Studio 2"),
        create_studio_dict(id="3", name="Studio 3"),
    ]

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response("bulkStudioUpdate", updated_studios_data),
            )
        ]
    )

    input_dict = {
        "ids": ["1", "2", "3"],
        "rating100": 80,
    }

    try:
        result = await respx_stash_client.bulk_studio_update(input_dict)
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert len(result) == 3
    assert result[0].id == "1"
    assert result[1].id == "2"
    assert result[2].id == "3"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "bulkStudioUpdate" in req["query"]
    assert req["variables"]["input"]["ids"] == ["1", "2", "3"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_bulk_studio_update_with_input_type(
    respx_stash_client: StashClient,
) -> None:
    """Test bulk updating studios with BulkStudioUpdateInput.

    This covers lines 229-230: if isinstance(input_data, BulkStudioUpdateInput).
    """
    updated_studios_data = [
        create_studio_dict(id="1", name="Studio 1"),
        create_studio_dict(id="2", name="Studio 2"),
    ]

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response("bulkStudioUpdate", updated_studios_data),
            )
        ]
    )

    input_data = BulkStudioUpdateInput(
        ids=["1", "2"],
        tag_ids=BulkUpdateIds(ids=["tag1", "tag2"], mode=BulkUpdateIdMode.ADD),
    )

    try:
        result = await respx_stash_client.bulk_studio_update(input_data)
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert len(result) == 2
    assert result[0].id == "1"
    assert result[1].id == "2"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "bulkStudioUpdate" in req["query"]
    assert req["variables"]["input"]["ids"] == ["1", "2"]
    # Schema uses snake_case for this field
    assert req["variables"]["input"]["tag_ids"]["ids"] == ["tag1", "tag2"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_bulk_studio_update_error_raises(respx_stash_client: StashClient) -> None:
    """Test that bulk_studio_update raises on error.

    This covers lines 241-243: exception handling.
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    input_data = BulkStudioUpdateInput(
        ids=["1", "2"],
        rating100=80,
    )

    try:
        with pytest.raises(StashGraphQLError):
            await respx_stash_client.bulk_studio_update(input_data)
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert len(graphql_route.calls) == 1


# =============================================================================
# find_studio_hierarchy tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_studio_hierarchy_multi_level(
    respx_stash_client: StashClient,
) -> None:
    """Test finding studio hierarchy with multiple levels.

    Structure: Root > Parent > Child
    This covers lines 267-283: the full hierarchy traversal.
    """
    # Create nested studio hierarchy
    root_studio = create_studio_dict(id="10", name="Root Studio", parent_studio=None)
    parent_studio = create_studio_dict(
        id="11", name="Parent Studio", parent_studio=root_studio
    )
    child_studio = create_studio_dict(
        id="12", name="Child Studio", parent_studio=parent_studio
    )

    # Mock responses for each level of traversal
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            # First call: find child studio
            httpx.Response(
                200, json=create_graphql_response("findStudio", child_studio)
            ),
        ]
    )

    try:
        hierarchy = await respx_stash_client.find_studio_hierarchy("12")
    finally:
        dump_graphql_calls(graphql_route.calls)

    # Verify hierarchy is ordered from root to child
    assert len(hierarchy) == 3
    assert hierarchy[0].id == "10"
    assert hierarchy[0].name == "Root Studio"
    assert hierarchy[1].id == "11"
    assert hierarchy[1].name == "Parent Studio"
    assert hierarchy[2].id == "12"
    assert hierarchy[2].name == "Child Studio"

    # Verify request
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "findStudio" in req["query"]
    assert req["variables"]["id"] == "12"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_studio_hierarchy_single_studio(
    respx_stash_client: StashClient,
) -> None:
    """Test finding hierarchy for a studio with no parent.

    This covers line 277-280: checking if parent_studio exists.
    """
    # Studio with no parent
    studio_data = create_studio_dict(id="13", name="Solo Studio", parent_studio=None)

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("findStudio", studio_data))
        ]
    )

    try:
        hierarchy = await respx_stash_client.find_studio_hierarchy("13")
    finally:
        dump_graphql_calls(graphql_route.calls)

    # Should return single studio
    assert len(hierarchy) == 1
    assert hierarchy[0].id == "13"
    assert hierarchy[0].name == "Solo Studio"

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_studio_hierarchy_not_found(respx_stash_client: StashClient) -> None:
    """Test finding hierarchy for a non-existent studio.

    This covers lines 270-271: handling studio not found.
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("findStudio", None))
        ]
    )

    try:
        hierarchy = await respx_stash_client.find_studio_hierarchy("nonexistent")
    finally:
        dump_graphql_calls(graphql_route.calls)

    # Should return empty list
    assert len(hierarchy) == 0

    assert len(graphql_route.calls) == 1


# =============================================================================
# find_studio_root tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_studio_root_from_child(respx_stash_client: StashClient) -> None:
    """Test finding root studio from a child studio.

    This covers lines 315-316: returning hierarchy[0].
    """
    # Create nested hierarchy
    root_studio = create_studio_dict(id="10", name="Root Studio", parent_studio=None)
    parent_studio = create_studio_dict(
        id="11", name="Parent Studio", parent_studio=root_studio
    )
    child_studio = create_studio_dict(
        id="12", name="Child Studio", parent_studio=parent_studio
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("findStudio", child_studio)
            ),
        ]
    )

    try:
        root = await respx_stash_client.find_studio_root("12")
    finally:
        dump_graphql_calls(graphql_route.calls)

    # Should return the root studio
    assert root is not None
    assert root.id == "10"
    assert root.name == "Root Studio"

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_studio_root_already_root(respx_stash_client: StashClient) -> None:
    """Test finding root when the studio is already a root.

    This covers lines 315-316: same studio returned when no parent.
    """
    # Studio with no parent
    studio_data = create_studio_dict(id="14", name="Already Root", parent_studio=None)

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("findStudio", studio_data))
        ]
    )

    try:
        root = await respx_stash_client.find_studio_root("14")
    finally:
        dump_graphql_calls(graphql_route.calls)

    # Should return itself
    assert root is not None
    assert root.id == "14"
    assert root.name == "Already Root"

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_studio_root_not_found(respx_stash_client: StashClient) -> None:
    """Test finding root for a non-existent studio.

    This covers lines 315-316: returning None when hierarchy is empty.
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("findStudio", None))
        ]
    )

    try:
        root = await respx_stash_client.find_studio_root("nonexistent")
    finally:
        dump_graphql_calls(graphql_route.calls)

    # Should return None
    assert root is None

    assert len(graphql_route.calls) == 1


# =============================================================================
# map_studio_ids tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_map_studio_ids_string_input(respx_stash_client: StashClient) -> None:
    """Test mapping studio names to IDs.

    This covers lines 386-403: string input handling.
    """
    studio1 = create_studio_dict(id="1", name="Studio One")
    studio2 = create_studio_dict(id="2", name="Studio Two")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            # First search: "Studio One"
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findStudios",
                    create_find_studios_result(count=1, studios=[studio1]),
                ),
            ),
            # Second search: "Studio Two"
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findStudios",
                    create_find_studios_result(count=1, studios=[studio2]),
                ),
            ),
        ]
    )

    try:
        studio_ids = await respx_stash_client.map_studio_ids(
            ["Studio One", "Studio Two"]
        )
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert len(studio_ids) == 2
    assert studio_ids[0] == "1"
    assert studio_ids[1] == "2"

    # Verify both queries were made
    assert len(graphql_route.calls) == 2
    req1 = json.loads(graphql_route.calls[0].request.content)
    assert req1["variables"]["studio_filter"]["name"]["value"] == "Studio One"
    req2 = json.loads(graphql_route.calls[1].request.content)
    assert req2["variables"]["studio_filter"]["name"]["value"] == "Studio Two"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_map_studio_ids_dict_input(respx_stash_client: StashClient) -> None:
    """Test mapping studio dicts to IDs.

    This covers lines 406-423: dict input handling.
    """
    studio_data = create_studio_dict(id="1", name="Dict Studio")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findStudios",
                    create_find_studios_result(count=1, studios=[studio_data]),
                ),
            ),
        ]
    )

    try:
        studio_ids = await respx_stash_client.map_studio_ids([{"name": "Dict Studio"}])
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert len(studio_ids) == 1
    assert studio_ids[0] == "1"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["studio_filter"]["name"]["value"] == "Dict Studio"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_map_studio_ids_studio_object_with_id(
    respx_stash_client: StashClient,
) -> None:
    """Test mapping Studio objects with ID to IDs.

    This covers lines 377-381: Studio object with ID.
    """
    # No GraphQL calls needed - just extract ID
    studio_obj = Studio(id="17", name="Test Studio")

    studio_ids = await respx_stash_client.map_studio_ids([studio_obj])

    assert len(studio_ids) == 1
    assert studio_ids[0] == "17"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_map_studio_ids_studio_object_new_searches_by_name(
    respx_stash_client: StashClient,
) -> None:
    """Test mapping new Studio objects (with auto-generated UUID) searches by name.

    This covers lines 380-384: Studio object with is_new() True falls through to name search.
    """
    studio_data = create_studio_dict(id="18", name="Test Studio")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findStudios",
                    create_find_studios_result(count=1, studios=[studio_data]),
                ),
            ),
        ]
    )

    # New studio object (auto-generates UUID, is_new() == True)
    studio_obj = Studio(name="Test Studio")
    try:
        studio_ids = await respx_stash_client.map_studio_ids([studio_obj])
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert len(studio_ids) == 1
    assert studio_ids[0] == "18"

    # Should search by name
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["studio_filter"]["name"]["value"] == "Test Studio"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_map_studio_ids_create_missing(respx_stash_client: StashClient) -> None:
    """Test auto-creating missing studios when create=True.

    This covers lines 395-399, 417-419: auto-creation paths.
    """
    created_studio = create_studio_dict(id="19", name="New Studio")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            # First: search returns empty
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findStudios", create_find_studios_result(count=0, studios=[])
                ),
            ),
            # Second: create studio
            httpx.Response(
                200, json=create_graphql_response("studioCreate", created_studio)
            ),
        ]
    )

    try:
        studio_ids = await respx_stash_client.map_studio_ids(
            ["New Studio"], create=True
        )
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert len(studio_ids) == 1
    assert studio_ids[0] == "19"

    # Verify search and create were both called
    assert len(graphql_route.calls) == 2
    req1 = json.loads(graphql_route.calls[0].request.content)
    assert "findStudios" in req1["query"]
    req2 = json.loads(graphql_route.calls[1].request.content)
    assert "studioCreate" in req2["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_map_studio_ids_not_found_no_create(
    respx_stash_client: StashClient,
) -> None:
    """Test skipping studios not found when create=False.

    This covers lines 400-403, 420-423: warning when not found.
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            # Search returns empty
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findStudios", create_find_studios_result(count=0, studios=[])
                ),
            ),
        ]
    )

    try:
        studio_ids = await respx_stash_client.map_studio_ids(
            ["Missing Studio"], create=False
        )
    finally:
        dump_graphql_calls(graphql_route.calls)

    # Should skip missing studio
    assert len(studio_ids) == 0

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_map_studio_ids_mixed_types(respx_stash_client: StashClient) -> None:
    """Test mapping mixed input types.

    This covers all input type branches together.
    """
    studio_from_name = create_studio_dict(id="1", name="String Studio")
    studio_from_dict = create_studio_dict(id="2", name="Dict Studio")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            # Search for string input
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findStudios",
                    create_find_studios_result(count=1, studios=[studio_from_name]),
                ),
            ),
            # Search for dict input
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findStudios",
                    create_find_studios_result(count=1, studios=[studio_from_dict]),
                ),
            ),
        ]
    )

    # Mix of Studio object with ID, string, and dict
    studio_obj = Studio(id="15", name="Object Studio")
    try:
        studio_ids = await respx_stash_client.map_studio_ids(
            [studio_obj, "String Studio", {"name": "Dict Studio"}]
        )
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert len(studio_ids) == 3
    assert studio_ids[0] == "15"  # Direct from object
    assert studio_ids[1] == "1"  # From search
    assert studio_ids[2] == "2"  # From search

    # Only 2 GraphQL calls (object didn't need search)
    assert len(graphql_route.calls) == 2


@pytest.mark.asyncio
@pytest.mark.unit
async def test_map_studio_ids_error_handling(respx_stash_client: StashClient) -> None:
    """Test that errors are caught and logged, continuing with other studios.

    This covers lines 425-427: exception handling.
    """
    studio_ok = create_studio_dict(id="16", name="OK Studio")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            # First studio: error
            httpx.Response(500, json={"errors": [{"message": "Server error"}]}),
            # Second studio: success
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findStudios",
                    create_find_studios_result(count=1, studios=[studio_ok]),
                ),
            ),
        ]
    )

    try:
        studio_ids = await respx_stash_client.map_studio_ids(
            ["Error Studio", "OK Studio"]
        )
    finally:
        dump_graphql_calls(graphql_route.calls)

    # Should skip error studio and continue
    assert len(studio_ids) == 1
    assert studio_ids[0] == "16"

    assert len(graphql_route.calls) == 2


@pytest.mark.asyncio
@pytest.mark.unit
async def test_map_studio_ids_create_from_dict(respx_stash_client: StashClient) -> None:
    """Test auto-creating missing studios from dict input.

    This covers lines 417-419: create from dict branch.
    """
    created_studio = create_studio_dict(id="20", name="New Dict Studio")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            # Search returns empty
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findStudios", create_find_studios_result(count=0, studios=[])
                ),
            ),
            # Create studio
            httpx.Response(
                200, json=create_graphql_response("studioCreate", created_studio)
            ),
        ]
    )

    try:
        studio_ids = await respx_stash_client.map_studio_ids(
            [{"name": "New Dict Studio"}], create=True
        )
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert len(studio_ids) == 1
    assert studio_ids[0] == "20"

    assert len(graphql_route.calls) == 2


@pytest.mark.asyncio
@pytest.mark.unit
async def test_map_studio_ids_dict_not_found_no_create(
    respx_stash_client: StashClient,
) -> None:
    """Test skipping studios from dict input not found when create=False.

    This covers lines 425-427: warning path for dict input.
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            # Search returns empty
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findStudios", create_find_studios_result(count=0, studios=[])
                ),
            ),
        ]
    )

    try:
        studio_ids = await respx_stash_client.map_studio_ids(
            [{"name": "Missing Dict Studio"}], create=False
        )
    finally:
        dump_graphql_calls(graphql_route.calls)

    # Should skip missing studio
    assert len(studio_ids) == 0

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_map_studio_ids_invalid_input_type(
    respx_stash_client: StashClient,
) -> None:
    """Test map_studio_ids with invalid input type (not Studio, str, or dict).

    This covers lines 410->374 FALSE: when studio_input doesn't match any isinstance checks.
    Invalid types are silently skipped.
    """
    # Pass invalid types that don't match any isinstance checks
    invalid_inputs: list[Any] = [123, None, [], object()]
    result = await respx_stash_client.map_studio_ids(invalid_inputs)

    # All invalid inputs should be skipped
    assert result == []


@pytest.mark.asyncio
@pytest.mark.unit
async def test_map_studio_ids_dict_without_name(
    respx_stash_client: StashClient,
) -> None:
    """Test map_studio_ids with dict input that has no 'name' key.

    This covers lines 412->374 FALSE: when dict doesn't have name key or name is empty.
    """
    # No HTTP calls should be made
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(200, json={})]
    )

    try:
        result = await respx_stash_client.map_studio_ids(
            [
                {"other_field": "value"},
                {"name": ""},
            ]  # Dict without name, dict with empty name
        )
    finally:
        dump_graphql_calls(graphql_route.calls)

    # Dicts without valid name are skipped
    assert len(result) == 0
    assert len(graphql_route.calls) == 0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_map_studio_ids_exception_handling_patched(
    respx_stash_client: StashClient,
) -> None:
    """Test map_studio_ids exception handling - error logged and continues.

    This covers lines 429-431: exception caught, logged, continue processing.
    Uses patch to bypass find_studios' internal exception handler.
    """
    studio_data = create_studio_dict(id="21", name="GoodStudio")

    # Mock find_studios to raise exception for first call, succeed for second
    original_find_studios = respx_stash_client.find_studios
    call_count = 0

    async def mock_find_studios(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # First call raises exception (bypasses find_studios internal handler)
            raise RuntimeError("Unexpected error during studio lookup")
        # Second call succeeds
        return await original_find_studios(*args, **kwargs)

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            # Second call - for "GoodStudio"
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findStudios",
                    create_find_studios_result(count=1, studios=[studio_data]),
                ),
            ),
        ]
    )

    with patch.object(
        respx_stash_client, "find_studios", side_effect=mock_find_studios
    ):
        try:
            result = await respx_stash_client.map_studio_ids(
                ["FailStudio", "GoodStudio"]
            )
        finally:
            dump_graphql_calls(graphql_route.calls)

    # First studio failed (exception caught at lines 429-431), second succeeded
    assert len(result) == 1
    assert result[0] == "21"

    assert call_count == 2  # Both calls were attempted

    # Verify the HTTP route was called
    assert len(graphql_route.calls) == 1  # Only one HTTP call (second studio)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_map_studio_ids_studio_object_with_id_but_name_unset(
    respx_stash_client: StashClient,
) -> None:
    """Test map_studio_ids with NEW Studio object that has name=UNSET.

    This covers lines 389->393 FALSE: when Studio is new (not from server) and name is UNSET,
    the is_set(studio_input.name) check is False, so studio_name remains None and
    the code skips name-based lookup entirely, skipping this studio.
    """
    # Create NEW Studio with name=UNSET using model_construct
    # The _is_new flag makes is_new() return True
    studio = Studio.model_construct(name=UNSET, _is_new=True)

    # No HTTP calls should be made - name lookup is skipped for UNSET name
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(200, json={})]
    )

    try:
        result = await respx_stash_client.map_studio_ids([studio])
    finally:
        dump_graphql_calls(graphql_route.calls)

    # Studio with UNSET name is skipped - no ID added
    assert len(result) == 0

    # Verify NO HTTP calls were made (name lookup was skipped)
    assert len(graphql_route.calls) == 0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_bulk_studio_update_with_return_fields(
    respx_stash_client: StashClient,
) -> None:
    """Test bulk_studio_update with return_fields uses minimal mutation."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "bulkStudioUpdate",
                    [{"id": "1"}, {"id": "2"}],
                ),
            )
        ]
    )

    try:
        result = await respx_stash_client.bulk_studio_update(
            {"ids": ["1", "2"], "rating100": 80},
            return_fields="id",
        )
    finally:
        dump_graphql_calls(graphql_route.calls)

    # Returns raw dicts, not Studio objects
    assert result == [{"id": "1"}, {"id": "2"}]

    # Verify the minimal mutation was used (no full fragment)
    req = json.loads(graphql_route.calls[0].request.content)
    assert "bulkStudioUpdate" in req["query"]
    # Should NOT contain full studio fields like "image_path" or "child_studios"
    assert "child_studios" not in req["query"]
