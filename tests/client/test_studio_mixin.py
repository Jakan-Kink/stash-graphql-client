"""Unit tests for StudioClientMixin.

These tests mock at the HTTP boundary using respx, allowing real code execution
through the entire GraphQL client stack including serialization/deserialization.
"""

import json

import httpx
import pytest
import respx

from stash_graphql_client import StashClient
from stash_graphql_client.errors import StashGraphQLError
from stash_graphql_client.types import (
    BulkStudioUpdateInput,
    BulkUpdateIds,
    Studio,
    StudioDestroyInput,
)
from tests.fixtures import (
    create_find_studios_result,
    create_graphql_response,
    create_studio_dict,
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

    studio = await respx_stash_client.find_studio("123")

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

    studio = await respx_stash_client.find_studio("999")

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

    studio = await respx_stash_client.find_studio("error_id")

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

    result = await respx_stash_client.find_studios()

    assert result.count == 1
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

    result = await respx_stash_client.find_studios(q="Search Result")

    assert result.count == 1
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

    result = await respx_stash_client.find_studios(
        filter_={"page": 2, "per_page": 10, "sort": "name", "direction": "ASC"}
    )

    assert result.count == 1
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

    result = await respx_stash_client.find_studios()

    assert result.count == 0
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
        id="new_studio_123",
        name="New Studio",
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("studioCreate", created_studio_data)
            )
        ]
    )

    studio = Studio(id="new", name="New Studio")
    result = await respx_stash_client.create_studio(studio)

    assert result is not None
    assert result.id == "new_studio_123"
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

    studio = Studio(id="new", name="Will Fail")

    with pytest.raises(StashGraphQLError):
        await respx_stash_client.create_studio(studio)

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

    result = await respx_stash_client.update_studio(studio)

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

    with pytest.raises(StashGraphQLError):
        await respx_stash_client.update_studio(studio)

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

    result = await respx_stash_client.studio_destroy({"id": "123"})

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
    result = await respx_stash_client.studio_destroy(input_data)

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

    with pytest.raises(StashGraphQLError):
        await respx_stash_client.studio_destroy({"id": "123"})

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

    result = await respx_stash_client.studios_destroy(["123", "456", "789"])

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

    with pytest.raises(StashGraphQLError):
        await respx_stash_client.studios_destroy(["123", "456"])

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
        create_studio_dict(id="s1", name="Studio 1"),
        create_studio_dict(id="s2", name="Studio 2"),
        create_studio_dict(id="s3", name="Studio 3"),
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
        "ids": ["s1", "s2", "s3"],
        "rating100": 80,
    }

    result = await respx_stash_client.bulk_studio_update(input_dict)

    assert len(result) == 3
    assert result[0].id == "s1"
    assert result[1].id == "s2"
    assert result[2].id == "s3"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "bulkStudioUpdate" in req["query"]
    assert req["variables"]["input"]["ids"] == ["s1", "s2", "s3"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_bulk_studio_update_with_input_type(
    respx_stash_client: StashClient,
) -> None:
    """Test bulk updating studios with BulkStudioUpdateInput.

    This covers lines 229-230: if isinstance(input_data, BulkStudioUpdateInput).
    """
    updated_studios_data = [
        create_studio_dict(id="s1", name="Studio 1"),
        create_studio_dict(id="s2", name="Studio 2"),
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
        ids=["s1", "s2"],
        tag_ids=BulkUpdateIds(ids=["tag1", "tag2"], mode="ADD"),
    )

    result = await respx_stash_client.bulk_studio_update(input_data)

    assert len(result) == 2
    assert result[0].id == "s1"
    assert result[1].id == "s2"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "bulkStudioUpdate" in req["query"]
    assert req["variables"]["input"]["ids"] == ["s1", "s2"]
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
        ids=["s1", "s2"],
        rating100=80,
    )

    with pytest.raises(StashGraphQLError):
        await respx_stash_client.bulk_studio_update(input_data)

    assert len(graphql_route.calls) == 1
