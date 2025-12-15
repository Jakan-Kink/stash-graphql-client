"""Unit tests for FilterClientMixin.

These tests mock at the HTTP boundary using respx, allowing real code execution
through the entire GraphQL client stack including serialization/deserialization.
"""

import json

import httpx
import pytest
import respx

from stash_graphql_client import StashClient
from stash_graphql_client.types import DestroyFilterInput, FilterMode, SaveFilterInput
from tests.fixtures import create_graphql_response


def create_saved_filter_dict(
    id: str = "1",
    mode: str = "SCENES",
    name: str = "Test Filter",
    find_filter: dict | None = None,
    object_filter: dict | None = None,
    ui_options: dict | None = None,
) -> dict:
    """Create a SavedFilter dictionary for testing."""
    return {
        "id": id,
        "mode": mode,
        "name": name,
        "find_filter": find_filter,
        "object_filter": object_filter,
        "ui_options": ui_options,
    }


@pytest.mark.asyncio
@pytest.mark.unit
async def test_save_filter_create_new(respx_stash_client: StashClient) -> None:
    """Test saving a new filter (no ID provided)."""
    filter_data = create_saved_filter_dict(
        id="123",
        mode="SCENES",
        name="My Scenes Filter",
        find_filter={"page": 1, "per_page": 25},
        object_filter={"is_missing": "performers"},
        ui_options={"display_mode": "grid"},
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("saveFilter", filter_data))
        ]
    )

    input_data = SaveFilterInput(
        mode=FilterMode.SCENES,
        name="My Scenes Filter",
        find_filter={"page": 1, "per_page": 25},
        object_filter={"is_missing": "performers"},
        ui_options={"display_mode": "grid"},
    )

    saved_filter = await respx_stash_client.save_filter(input_data)

    # Verify the result
    assert saved_filter is not None
    assert saved_filter.id == "123"
    assert saved_filter.mode == FilterMode.SCENES
    assert saved_filter.name == "My Scenes Filter"

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "saveFilter" in req["query"]
    assert req["variables"]["input"]["mode"] == "SCENES"
    assert req["variables"]["input"]["name"] == "My Scenes Filter"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_save_filter_update_existing(respx_stash_client: StashClient) -> None:
    """Test updating an existing filter (ID provided)."""
    filter_data = create_saved_filter_dict(
        id="456",
        mode="PERFORMERS",
        name="Updated Performers Filter",
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("saveFilter", filter_data))
        ]
    )

    input_data = SaveFilterInput(
        id="456",
        mode=FilterMode.PERFORMERS,
        name="Updated Performers Filter",
    )

    saved_filter = await respx_stash_client.save_filter(input_data)

    # Verify the result
    assert saved_filter is not None
    assert saved_filter.id == "456"
    assert saved_filter.name == "Updated Performers Filter"

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "saveFilter" in req["query"]
    assert req["variables"]["input"]["id"] == "456"
    assert req["variables"]["input"]["mode"] == "PERFORMERS"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_save_filter_with_dict_input(respx_stash_client: StashClient) -> None:
    """Test saving a filter with dictionary input."""
    filter_data = create_saved_filter_dict(
        id="789",
        mode="GALLERIES",
        name="Gallery Filter",
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("saveFilter", filter_data))
        ]
    )

    saved_filter = await respx_stash_client.save_filter(
        {
            "mode": "GALLERIES",
            "name": "Gallery Filter",
        }
    )

    # Verify the result
    assert saved_filter is not None
    assert saved_filter.id == "789"
    assert saved_filter.mode == FilterMode.GALLERIES

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "saveFilter" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_destroy_saved_filter(respx_stash_client: StashClient) -> None:
    """Test deleting a saved filter."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("destroySavedFilter", True)
            )
        ]
    )

    input_data = DestroyFilterInput(id="123")
    result = await respx_stash_client.destroy_saved_filter(input_data)

    # Verify the result
    assert result is True

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "destroySavedFilter" in req["query"]
    assert req["variables"]["input"]["id"] == "123"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_destroy_saved_filter_with_dict(respx_stash_client: StashClient) -> None:
    """Test deleting a saved filter with dictionary input."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("destroySavedFilter", True)
            )
        ]
    )

    result = await respx_stash_client.destroy_saved_filter({"id": "456"})

    # Verify the result
    assert result is True

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["input"]["id"] == "456"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_destroy_saved_filter_failure(respx_stash_client: StashClient) -> None:
    """Test handling when filter deletion fails."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("destroySavedFilter", False)
            )
        ]
    )

    result = await respx_stash_client.destroy_saved_filter({"id": "999"})

    # Verify the result
    assert result is False

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_save_filter_error_raises(respx_stash_client: StashClient) -> None:
    """Test that save_filter raises exception on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(500, json={"errors": [{"message": "Test error"}]})]
    )

    with pytest.raises(Exception, match="error"):
        await respx_stash_client.save_filter({"mode": "SCENES", "name": "Error Filter"})

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_destroy_saved_filter_error_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test that destroy_saved_filter raises exception on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(500, json={"errors": [{"message": "Test error"}]})]
    )

    with pytest.raises(Exception, match="error"):
        await respx_stash_client.destroy_saved_filter({"id": "error"})

    assert len(graphql_route.calls) == 1
