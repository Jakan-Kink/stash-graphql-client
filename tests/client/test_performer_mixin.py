"""Unit tests for PerformerClientMixin.

These tests mock at the HTTP boundary using respx, allowing real code execution
through the entire GraphQL client stack including serialization/deserialization.
"""

import json
from unittest.mock import patch

import httpx
import pytest
import respx

from stash_graphql_client import StashClient
from stash_graphql_client.errors import StashGraphQLError
from stash_graphql_client.types import (
    BulkPerformerUpdateInput,
    BulkUpdateIds,
    OnMultipleMatch,
    Performer,
    PerformerDestroyInput,
)
from tests.fixtures import (
    create_find_performers_result,
    create_graphql_response,
    create_performer_dict,
)


# =============================================================================
# find_performer tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_performer_by_id(respx_stash_client: StashClient) -> None:
    """Test finding a performer by ID."""
    performer_data = create_performer_dict(id="123", name="Test Performer")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("findPerformer", performer_data)
            )
        ]
    )

    performer = await respx_stash_client.find_performer("123")

    assert performer is not None
    assert performer.id == "123"
    assert performer.name == "Test Performer"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "findPerformer" in req["query"]
    assert req["variables"]["id"] == "123"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_performer_not_found(respx_stash_client: StashClient) -> None:
    """Test finding a performer that doesn't exist."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("findPerformer", None))
        ]
    )

    performer = await respx_stash_client.find_performer("999")

    assert performer is None
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_performer_error_returns_none(
    respx_stash_client: StashClient,
) -> None:
    """Test that find_performer returns None on error.

    Uses a numeric string ID so it takes the direct ID lookup path (1 call).
    Non-numeric strings get parsed as names and trigger name+alias searches.
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    # Use numeric ID to take the direct lookup path (not name search)
    performer = await respx_stash_client.find_performer("999")

    assert performer is None
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_performer_by_name_dict_filter(
    respx_stash_client: StashClient,
) -> None:
    """Test finding a performer by name using dict filter.

    This covers lines 75-124: if isinstance(parsed_input, dict) branch.
    """
    performer_data = create_performer_dict(id="123", name="Performer Name")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findPerformers",
                    create_find_performers_result(count=1, performers=[performer_data]),
                ),
            )
        ]
    )

    # Pass a dict with "name" to trigger the dict branch
    performer = await respx_stash_client.find_performer({"name": "Performer Name"})

    assert performer is not None
    assert performer.id == "123"
    assert performer.name == "Performer Name"

    # Should use findPerformers query
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "findPerformers" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_performer_by_name_falls_back_to_alias(
    respx_stash_client: StashClient,
) -> None:
    """Test finding a performer by name falls back to alias search.

    This covers the alias fallback in lines 100-124.
    """
    performer_data = create_performer_dict(id="456", name="Performer Real Name")

    # First call (by name) returns empty, second call (by alias) returns performer
    call_count = 0

    def mock_response(request):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # First call - name search returns empty
            return httpx.Response(
                200,
                json=create_graphql_response(
                    "findPerformers",
                    create_find_performers_result(count=0, performers=[]),
                ),
            )
        # Second call - alias search returns the performer
        return httpx.Response(
            200,
            json=create_graphql_response(
                "findPerformers",
                create_find_performers_result(count=1, performers=[performer_data]),
            ),
        )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=mock_response
    )

    performer = await respx_stash_client.find_performer({"name": "Alias Name"})

    assert performer is not None
    assert performer.id == "456"
    assert performer.name == "Performer Real Name"

    # Should have made 2 calls - name then alias
    assert len(graphql_route.calls) == 2


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_performer_by_name_not_found(
    respx_stash_client: StashClient,
) -> None:
    """Test finding a performer by name when not found by name or alias.

    This covers lines 75-124 when both searches return empty.
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findPerformers",
                    create_find_performers_result(count=0, performers=[]),
                ),
            ),
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findPerformers",
                    create_find_performers_result(count=0, performers=[]),
                ),
            ),
        ]
    )

    performer = await respx_stash_client.find_performer({"name": "Nonexistent"})

    assert performer is None
    # Called twice - once for name, once for alias
    assert len(graphql_route.calls) == 2


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_performer_dict_without_name_key(
    respx_stash_client: StashClient,
) -> None:
    """Test finding a performer with dict input that has no 'name' key.

    This covers line 77->101: when dict has no name key, it skips the name/alias
    search entirely and falls through to check result (which is None), returning None.
    No HTTP calls are made because the name search is skipped.
    """
    # Pass a dict without "name" key - skips the name/alias search entirely
    performer = await respx_stash_client.find_performer({"other_field": "value"})

    # Returns None without making any HTTP calls
    assert performer is None


# =============================================================================
# find_performers tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_performers(respx_stash_client: StashClient) -> None:
    """Test finding performers."""
    performer_data = create_performer_dict(id="123", name="Test Performer")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findPerformers",
                    create_find_performers_result(count=1, performers=[performer_data]),
                ),
            )
        ]
    )

    result = await respx_stash_client.find_performers()

    assert result.count == 1
    assert len(result.performers) == 1
    assert result.performers[0].id == "123"

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_performers_with_q_parameter(
    respx_stash_client: StashClient,
) -> None:
    """Test finding performers with q parameter.

    This covers lines 235-236: if q is not None.
    """
    performer_data = create_performer_dict(id="123", name="Search Result")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findPerformers",
                    create_find_performers_result(count=1, performers=[performer_data]),
                ),
            )
        ]
    )

    result = await respx_stash_client.find_performers(q="Search Result")

    assert result.count == 1
    assert result.performers[0].name == "Search Result"

    # Verify q was passed in filter
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["filter"]["q"] == "Search Result"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_performers_with_custom_filter(
    respx_stash_client: StashClient,
) -> None:
    """Test finding performers with custom filter_ parameter.

    This covers line 200->202: when filter_ is not None.
    """
    performer_data = create_performer_dict(id="123", name="Paginated Result")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findPerformers",
                    create_find_performers_result(count=1, performers=[performer_data]),
                ),
            )
        ]
    )

    # Provide a custom filter_ to skip the default {"per_page": -1}
    result = await respx_stash_client.find_performers(
        filter_={"page": 2, "per_page": 10, "sort": "name", "direction": "ASC"}
    )

    assert result.count == 1
    assert result.performers[0].name == "Paginated Result"

    # Verify the custom filter was passed
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["filter"]["page"] == 2
    assert req["variables"]["filter"]["per_page"] == 10
    assert req["variables"]["filter"]["sort"] == "name"
    assert req["variables"]["filter"]["direction"] == "ASC"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_performers_error_returns_empty(
    respx_stash_client: StashClient,
) -> None:
    """Test that find_performers returns empty result on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    result = await respx_stash_client.find_performers()

    assert result.count == 0
    assert len(result.performers) == 0

    assert len(graphql_route.calls) == 1


# =============================================================================
# create_performer tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_performer(respx_stash_client: StashClient) -> None:
    """Test creating a performer.

    This covers lines 307-313: successful creation.
    """
    created_performer_data = create_performer_dict(
        id="new_performer_123",
        name="New Performer",
        gender="FEMALE",
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response("performerCreate", created_performer_data),
            )
        ]
    )

    performer = Performer(id="new", name="New Performer", gender="FEMALE")
    result = await respx_stash_client.create_performer(performer)

    assert result is not None
    assert result.id == "new_performer_123"
    assert result.name == "New Performer"
    assert result.gender == "FEMALE"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "performerCreate" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_performer_already_exists_fallback(
    respx_stash_client: StashClient,
) -> None:
    """Test create_performer falls back to finding existing performer.

    This covers lines 316-351: when performer already exists error.
    """
    existing_performer_data = create_performer_dict(
        id="existing_123",
        name="Existing Performer",
    )

    call_count = 0

    def mock_response(request):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # First call - create fails with "already exists"
            return httpx.Response(
                200,
                json={
                    "data": None,
                    "errors": [
                        {
                            "message": "performer with name 'Existing Performer' already exists"
                        }
                    ],
                },
            )
        # Second call - find existing performer
        return httpx.Response(
            200,
            json=create_graphql_response(
                "findPerformers",
                create_find_performers_result(
                    count=1, performers=[existing_performer_data]
                ),
            ),
        )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=mock_response
    )

    performer = Performer(id="new", name="Existing Performer")
    result = await respx_stash_client.create_performer(performer)

    assert result is not None
    assert result.id == "existing_123"
    assert result.name == "Existing Performer"

    # Should have made 2 calls - create then find
    assert len(graphql_route.calls) == 2


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_performer_error_raises(respx_stash_client: StashClient) -> None:
    """Test that create_performer raises on error.

    This covers lines 350-351: re-raise when error is not "already exists".
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    performer = Performer(id="new", name="Will Fail")

    with pytest.raises(StashGraphQLError):
        await respx_stash_client.create_performer(performer)

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_performer_already_exists_but_not_found_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test create_performer re-raises when performer 'already exists' but can't be found.

    This covers line 301: raise when result.count == 0 after "already exists" error.
    This is an edge case where the error says performer exists but we can't find it.
    """
    call_count = 0

    def mock_response(request):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # First call - create fails with "already exists"
            return httpx.Response(
                200,
                json={
                    "data": None,
                    "errors": [
                        {
                            "message": "performer with name 'Ghost Performer' already exists"
                        }
                    ],
                },
            )
        # Second call - but performer is NOT found (count=0)
        return httpx.Response(
            200,
            json=create_graphql_response(
                "findPerformers",
                create_find_performers_result(count=0, performers=[]),
            ),
        )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=mock_response
    )

    performer = Performer(id="new", name="Ghost Performer")

    # Should re-raise the original exception since performer wasn't found
    with pytest.raises(StashGraphQLError):
        await respx_stash_client.create_performer(performer)

    # Should have made 2 calls - create then find (which returned empty)
    assert len(graphql_route.calls) == 2


# =============================================================================
# update_performer tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_performer(respx_stash_client: StashClient) -> None:
    """Test updating a performer.

    This covers lines 414-420: successful update.
    """
    updated_performer_data = create_performer_dict(
        id="123",
        name="Updated Performer",
        gender="MALE",
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response("performerUpdate", updated_performer_data),
            )
        ]
    )

    performer = Performer(id="123", name="Original Name")
    performer.name = "Updated Performer"
    performer.gender = "MALE"

    result = await respx_stash_client.update_performer(performer)

    assert result is not None
    assert result.id == "123"
    assert result.name == "Updated Performer"
    assert result.gender == "MALE"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "performerUpdate" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_performer_error_raises(respx_stash_client: StashClient) -> None:
    """Test that update_performer raises on error.

    This covers lines 421-423: exception handling.
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    performer = Performer(id="123", name="Will Fail")

    with pytest.raises(StashGraphQLError):
        await respx_stash_client.update_performer(performer)

    assert len(graphql_route.calls) == 1


# =============================================================================
# update_performer_image tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_performer_image(respx_stash_client: StashClient) -> None:
    """Test updating a performer's image.

    This covers lines 459-467: successful image update.
    """
    updated_performer_data = create_performer_dict(
        id="123",
        name="Performer",
        image_path="/performer/123/image.jpg",
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response("performerUpdate", updated_performer_data),
            )
        ]
    )

    performer = Performer(id="123", name="Performer")
    image_url = "data:image/jpeg;base64,/9j/4AAQSkZJRg=="

    result = await respx_stash_client.update_performer_image(performer, image_url)

    assert result is not None
    assert result.id == "123"

    # Verify the input only contains id and image
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "performerUpdate" in req["query"]
    assert req["variables"]["input"]["id"] == "123"
    assert req["variables"]["input"]["image"] == image_url


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_performer_image_error_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test that update_performer_image raises on error.

    This covers lines 468-470: exception handling.
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    performer = Performer(id="123", name="Performer")

    with pytest.raises(StashGraphQLError):
        await respx_stash_client.update_performer_image(
            performer, "data:image/jpeg;base64,xxx"
        )

    assert len(graphql_route.calls) == 1


# =============================================================================
# performer_destroy tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_performer_destroy_with_dict(respx_stash_client: StashClient) -> None:
    """Test destroying a performer with dict input."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("performerDestroy", True))
        ]
    )

    result = await respx_stash_client.performer_destroy({"id": "123"})

    assert result is True

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "performerDestroy" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_performer_destroy_with_input_type(
    respx_stash_client: StashClient,
) -> None:
    """Test destroying a performer with PerformerDestroyInput.

    This covers line 507: if isinstance(input_data, PerformerDestroyInput).
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("performerDestroy", True))
        ]
    )

    input_data = PerformerDestroyInput(id="123")
    result = await respx_stash_client.performer_destroy(input_data)

    assert result is True

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "performerDestroy" in req["query"]
    assert req["variables"]["input"]["id"] == "123"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_performer_destroy_error_raises(respx_stash_client: StashClient) -> None:
    """Test that performer_destroy raises on error.

    This covers lines 517-519: exception handling.
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    with pytest.raises(StashGraphQLError):
        await respx_stash_client.performer_destroy({"id": "123"})

    assert len(graphql_route.calls) == 1


# =============================================================================
# performers_destroy tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_performers_destroy(respx_stash_client: StashClient) -> None:
    """Test destroying multiple performers."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("performersDestroy", True))
        ]
    )

    result = await respx_stash_client.performers_destroy(["123", "456", "789"])

    assert result is True

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "performersDestroy" in req["query"]
    assert req["variables"]["ids"] == ["123", "456", "789"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_performers_destroy_error_raises(respx_stash_client: StashClient) -> None:
    """Test that performers_destroy raises on error.

    This covers lines 548-550: exception handling.
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    with pytest.raises(StashGraphQLError):
        await respx_stash_client.performers_destroy(["123", "456"])

    assert len(graphql_route.calls) == 1


# =============================================================================
# bulk_performer_update tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_bulk_performer_update_with_dict(respx_stash_client: StashClient) -> None:
    """Test bulk updating performers with dict input.

    This covers lines 590-591: else branch when input_data is a dict.
    """
    updated_performers_data = [
        create_performer_dict(id="p1", name="Performer 1", gender="FEMALE"),
        create_performer_dict(id="p2", name="Performer 2", gender="FEMALE"),
        create_performer_dict(id="p3", name="Performer 3", gender="FEMALE"),
    ]

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "bulkPerformerUpdate", updated_performers_data
                ),
            )
        ]
    )

    input_dict = {
        "ids": ["p1", "p2", "p3"],
        "gender": "FEMALE",
    }

    result = await respx_stash_client.bulk_performer_update(input_dict)

    assert len(result) == 3
    assert result[0].id == "p1"
    assert result[1].id == "p2"
    assert result[2].id == "p3"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "bulkPerformerUpdate" in req["query"]
    assert req["variables"]["input"]["ids"] == ["p1", "p2", "p3"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_bulk_performer_update_with_input_type(
    respx_stash_client: StashClient,
) -> None:
    """Test bulk updating performers with BulkPerformerUpdateInput.

    This covers lines 588-589: if isinstance(input_data, BulkPerformerUpdateInput).
    """
    updated_performers_data = [
        create_performer_dict(id="p1", name="Performer 1"),
        create_performer_dict(id="p2", name="Performer 2"),
    ]

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "bulkPerformerUpdate", updated_performers_data
                ),
            )
        ]
    )

    input_data = BulkPerformerUpdateInput(
        ids=["p1", "p2"],
        tag_ids=BulkUpdateIds(ids=["tag1", "tag2"], mode="ADD"),
    )

    result = await respx_stash_client.bulk_performer_update(input_data)

    assert len(result) == 2
    assert result[0].id == "p1"
    assert result[1].id == "p2"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "bulkPerformerUpdate" in req["query"]
    assert req["variables"]["input"]["ids"] == ["p1", "p2"]
    assert req["variables"]["input"]["tag_ids"]["ids"] == [
        "tag1",
        "tag2",
    ]  # Schema uses snake_case


@pytest.mark.asyncio
@pytest.mark.unit
async def test_bulk_performer_update_error_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test that bulk_performer_update raises on error.

    This covers lines 600-602: exception handling.
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    input_data = BulkPerformerUpdateInput(
        ids=["p1", "p2"],
        gender="FEMALE",
    )

    with pytest.raises(StashGraphQLError):
        await respx_stash_client.bulk_performer_update(input_data)

    assert len(graphql_route.calls) == 1


# =============================================================================
# all_performers tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_all_performers(respx_stash_client: StashClient) -> None:
    """Test getting all performers.

    This covers lines 506-512: successful retrieval.
    """
    performers_data = [
        create_performer_dict(id="p1", name="Performer 1"),
        create_performer_dict(id="p2", name="Performer 2"),
        create_performer_dict(id="p3", name="Performer 3"),
    ]

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response("allPerformers", performers_data),
            )
        ]
    )

    result = await respx_stash_client.all_performers()

    assert len(result) == 3
    assert result[0].id == "p1"
    assert result[0].name == "Performer 1"
    assert result[1].id == "p2"
    assert result[2].id == "p3"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "allPerformers" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_all_performers_error_returns_empty(
    respx_stash_client: StashClient,
) -> None:
    """Test that all_performers returns empty list on error.

    This covers lines 510-512: exception handling.
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    result = await respx_stash_client.all_performers()

    assert result == []
    assert len(graphql_route.calls) == 1


# =============================================================================
# map_performer_ids tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_map_performer_ids_string_input_found_by_name(
    respx_stash_client: StashClient,
) -> None:
    """Test map_performer_ids with string input found by name.

    This covers lines 640-646: string input, name search successful.
    """
    performer_data = create_performer_dict(id="p1", name="John Doe")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findPerformers",
                    create_find_performers_result(count=1, performers=[performer_data]),
                ),
            )
        ]
    )

    result = await respx_stash_client.map_performer_ids(["John Doe"])

    assert result == ["p1"]
    assert len(graphql_route.calls) == 1

    # Verify request searched by name
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["performer_filter"]["name"]["value"] == "John Doe"
    assert req["variables"]["performer_filter"]["name"]["modifier"] == "EQUALS"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_map_performer_ids_string_input_found_by_alias(
    respx_stash_client: StashClient,
) -> None:
    """Test map_performer_ids with string input found by alias fallback.

    This covers lines 648-657: name search fails, alias search succeeds.
    """
    performer_data = create_performer_dict(id="p2", name="Jane Smith")

    call_count = 0

    def mock_response(request):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # First call - name search returns empty
            return httpx.Response(
                200,
                json=create_graphql_response(
                    "findPerformers",
                    create_find_performers_result(count=0, performers=[]),
                ),
            )
        # Second call - alias search returns the performer
        return httpx.Response(
            200,
            json=create_graphql_response(
                "findPerformers",
                create_find_performers_result(count=1, performers=[performer_data]),
            ),
        )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=mock_response
    )

    result = await respx_stash_client.map_performer_ids(["Jane Alias"])

    assert result == ["p2"]
    assert len(graphql_route.calls) == 2

    # Verify first request searched by name
    req1 = json.loads(graphql_route.calls[0].request.content)
    assert req1["variables"]["performer_filter"]["name"]["value"] == "Jane Alias"

    # Verify second request searched by alias
    req2 = json.loads(graphql_route.calls[1].request.content)
    assert req2["variables"]["performer_filter"]["aliases"]["value"] == "Jane Alias"
    assert req2["variables"]["performer_filter"]["aliases"]["modifier"] == "INCLUDES"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_map_performer_ids_string_input_multiple_matches_return_first(
    respx_stash_client: StashClient,
) -> None:
    """Test map_performer_ids with multiple matches using RETURN_FIRST strategy.

    This covers lines 666-670: multiple matches with on_multiple=RETURN_FIRST.
    """
    performer1_data = create_performer_dict(id="p1", name="Common Name")
    performer2_data = create_performer_dict(id="p2", name="Common Name")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findPerformers",
                    create_find_performers_result(
                        count=2, performers=[performer1_data, performer2_data]
                    ),
                ),
            )
        ]
    )

    result = await respx_stash_client.map_performer_ids(
        ["Common Name"], on_multiple=OnMultipleMatch.RETURN_FIRST
    )

    assert result == ["p1"]  # Returns first match
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_map_performer_ids_string_input_multiple_matches_return_none(
    respx_stash_client: StashClient,
) -> None:
    """Test map_performer_ids with multiple matches using RETURN_NONE strategy.

    This covers lines 661-665: multiple matches with on_multiple=RETURN_NONE.
    """
    performer1_data = create_performer_dict(id="p1", name="Ambiguous Name")
    performer2_data = create_performer_dict(id="p2", name="Ambiguous Name")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findPerformers",
                    create_find_performers_result(
                        count=2, performers=[performer1_data, performer2_data]
                    ),
                ),
            )
        ]
    )

    result = await respx_stash_client.map_performer_ids(
        ["Ambiguous Name"], on_multiple=OnMultipleMatch.RETURN_NONE
    )

    assert result == []  # Returns empty - skipped the performer
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_map_performer_ids_string_input_multiple_matches_default_fallback(
    respx_stash_client: StashClient,
) -> None:
    """Test map_performer_ids with multiple matches using default fallback.

    This covers lines 672-676: else branch (default fallback to first match).
    """
    performer1_data = create_performer_dict(id="p1", name="Multiple Name")
    performer2_data = create_performer_dict(id="p2", name="Multiple Name")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findPerformers",
                    create_find_performers_result(
                        count=2, performers=[performer1_data, performer2_data]
                    ),
                ),
            )
        ]
    )

    # Use RETURN_LIST (which falls through to else branch)
    result = await respx_stash_client.map_performer_ids(
        ["Multiple Name"], on_multiple=OnMultipleMatch.RETURN_LIST
    )

    assert result == ["p1"]  # Falls back to first match
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_map_performer_ids_string_input_single_match(
    respx_stash_client: StashClient,
) -> None:
    """Test map_performer_ids with string input returning single match.

    This covers lines 678-679: single match, append ID.
    """
    performer_data = create_performer_dict(id="p1", name="Single Match")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findPerformers",
                    create_find_performers_result(count=1, performers=[performer_data]),
                ),
            )
        ]
    )

    result = await respx_stash_client.map_performer_ids(["Single Match"])

    assert result == ["p1"]
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_map_performer_ids_string_input_not_found_create_false(
    respx_stash_client: StashClient,
) -> None:
    """Test map_performer_ids with string input not found and create=False.

    This covers lines 689-692: not found, create=False, log warning and skip.
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            # Name search returns empty
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findPerformers",
                    create_find_performers_result(count=0, performers=[]),
                ),
            ),
            # Alias search returns empty
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findPerformers",
                    create_find_performers_result(count=0, performers=[]),
                ),
            ),
        ]
    )

    result = await respx_stash_client.map_performer_ids(["Nonexistent"], create=False)

    assert result == []
    assert len(graphql_route.calls) == 2


@pytest.mark.asyncio
@pytest.mark.unit
async def test_map_performer_ids_string_input_not_found_create_true(
    respx_stash_client: StashClient,
) -> None:
    """Test map_performer_ids with string input not found and create=True.

    This covers lines 680-688: not found, create=True, create new performer.
    """
    new_performer_data = create_performer_dict(id="new_p1", name="New Performer")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            # Name search returns empty
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findPerformers",
                    create_find_performers_result(count=0, performers=[]),
                ),
            ),
            # Alias search returns empty
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findPerformers",
                    create_find_performers_result(count=0, performers=[]),
                ),
            ),
            # Create performer
            httpx.Response(
                200,
                json=create_graphql_response("performerCreate", new_performer_data),
            ),
        ]
    )

    result = await respx_stash_client.map_performer_ids(["New Performer"], create=True)

    assert result == ["new_p1"]
    assert len(graphql_route.calls) == 3

    # Verify create request
    req = json.loads(graphql_route.calls[2].request.content)
    assert "performerCreate" in req["query"]
    assert req["variables"]["input"]["name"] == "New Performer"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_map_performer_ids_dict_input_found(
    respx_stash_client: StashClient,
) -> None:
    """Test map_performer_ids with dict input containing name key.

    This covers lines 694-716: dict input with name, single match.
    """
    performer_data = create_performer_dict(id="p1", name="Dict Performer")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findPerformers",
                    create_find_performers_result(count=1, performers=[performer_data]),
                ),
            )
        ]
    )

    result = await respx_stash_client.map_performer_ids([{"name": "Dict Performer"}])

    assert result == ["p1"]
    assert len(graphql_route.calls) == 1

    # Verify request
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["performer_filter"]["name"]["value"] == "Dict Performer"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_map_performer_ids_dict_input_multiple_matches_return_none(
    respx_stash_client: StashClient,
) -> None:
    """Test map_performer_ids with dict input and multiple matches using RETURN_NONE.

    This covers lines 704-709: dict input, multiple matches, RETURN_NONE.
    """
    performer1_data = create_performer_dict(id="p1", name="Dict Multiple")
    performer2_data = create_performer_dict(id="p2", name="Dict Multiple")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findPerformers",
                    create_find_performers_result(
                        count=2, performers=[performer1_data, performer2_data]
                    ),
                ),
            )
        ]
    )

    result = await respx_stash_client.map_performer_ids(
        [{"name": "Dict Multiple"}], on_multiple=OnMultipleMatch.RETURN_NONE
    )

    assert result == []
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_map_performer_ids_dict_input_multiple_matches_return_first(
    respx_stash_client: StashClient,
) -> None:
    """Test map_performer_ids with dict input and multiple matches using RETURN_FIRST.

    This covers lines 710-714: dict input, multiple matches, RETURN_FIRST.
    """
    performer1_data = create_performer_dict(id="p1", name="Dict First")
    performer2_data = create_performer_dict(id="p2", name="Dict First")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findPerformers",
                    create_find_performers_result(
                        count=2, performers=[performer1_data, performer2_data]
                    ),
                ),
            )
        ]
    )

    result = await respx_stash_client.map_performer_ids(
        [{"name": "Dict First"}], on_multiple=OnMultipleMatch.RETURN_FIRST
    )

    assert result == ["p1"]
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_map_performer_ids_dict_input_not_found_create_true(
    respx_stash_client: StashClient,
) -> None:
    """Test map_performer_ids with dict input not found and create=True.

    This covers lines 717-722: dict input, not found, create=True.
    """
    new_performer_data = create_performer_dict(id="new_p1", name="New Dict")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            # Search returns empty
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findPerformers",
                    create_find_performers_result(count=0, performers=[]),
                ),
            ),
            # Create performer
            httpx.Response(
                200,
                json=create_graphql_response("performerCreate", new_performer_data),
            ),
        ]
    )

    result = await respx_stash_client.map_performer_ids(
        [{"name": "New Dict"}], create=True
    )

    assert result == ["new_p1"]
    assert len(graphql_route.calls) == 2


@pytest.mark.asyncio
@pytest.mark.unit
async def test_map_performer_ids_dict_input_not_found_create_false(
    respx_stash_client: StashClient,
) -> None:
    """Test map_performer_ids with dict input not found and create=False.

    This covers lines 723-726: dict input, not found, create=False.
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findPerformers",
                    create_find_performers_result(count=0, performers=[]),
                ),
            )
        ]
    )

    result = await respx_stash_client.map_performer_ids(
        [{"name": "Missing Dict"}], create=False
    )

    assert result == []
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_map_performer_ids_performer_object_with_id(
    respx_stash_client: StashClient,
) -> None:
    """Test map_performer_ids with Performer object that has an ID.

    This covers lines 631-635: Performer object with ID, use directly.
    """
    performer = Performer(id="p1", name="Has ID")

    # No HTTP calls should be made - ID is used directly
    result = await respx_stash_client.map_performer_ids([performer])

    assert result == ["p1"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_map_performer_ids_performer_object_without_id(
    respx_stash_client: StashClient,
) -> None:
    """Test map_performer_ids with Performer object without an ID.

    This covers lines 638-644: Performer object without ID, search by name.
    """
    performer = Performer(name="No ID Performer")
    performer_data = create_performer_dict(id="p1", name="No ID Performer")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findPerformers",
                    create_find_performers_result(count=1, performers=[performer_data]),
                ),
            )
        ]
    )

    result = await respx_stash_client.map_performer_ids([performer])

    assert result == ["p1"]
    assert len(graphql_route.calls) == 1

    # Verify it searched by name
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["performer_filter"]["name"]["value"] == "No ID Performer"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_map_performer_ids_error_handling_continues(
    respx_stash_client: StashClient,
) -> None:
    """Test map_performer_ids handles errors gracefully and continues processing.

    This covers lines 732-734: exception handling, log and continue.

    Note: When a string performer errors, both name and alias searches fail (2 calls),
    then the exception handler catches it and continues to the next performer.
    """
    performer1_data = create_performer_dict(id="p1", name="Good Performer")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            # First performer - name search fails
            httpx.Response(500, json={"errors": [{"message": "Server error"}]}),
            # First performer - alias search also fails (caught by exception handler)
            httpx.Response(500, json={"errors": [{"message": "Server error"}]}),
            # Second performer - name search succeeds
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findPerformers",
                    create_find_performers_result(
                        count=1, performers=[performer1_data]
                    ),
                ),
            ),
        ]
    )

    # First performer will error (caught and continued), second will succeed
    result = await respx_stash_client.map_performer_ids(
        ["Error Performer", "Good Performer"]
    )

    # Should have one ID from successful performer (error was caught and continued)
    assert result == ["p1"]
    assert len(graphql_route.calls) == 3  # 2 failed calls + 1 success


@pytest.mark.asyncio
@pytest.mark.unit
async def test_map_performer_ids_mixed_input_types(
    respx_stash_client: StashClient,
) -> None:
    """Test map_performer_ids with mixed input types in a single call.

    This covers the full loop processing different input types.
    """
    performer1_data = create_performer_dict(id="p1", name="String Input")
    performer2_data = create_performer_dict(id="p2", name="Dict Input")
    performer_with_id = Performer(id="p3", name="Has ID")

    call_count = 0

    def mock_response(request):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # First call - string search
            return httpx.Response(
                200,
                json=create_graphql_response(
                    "findPerformers",
                    create_find_performers_result(
                        count=1, performers=[performer1_data]
                    ),
                ),
            )
        # Second call - dict search
        return httpx.Response(
            200,
            json=create_graphql_response(
                "findPerformers",
                create_find_performers_result(count=1, performers=[performer2_data]),
            ),
        )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=mock_response
    )

    result = await respx_stash_client.map_performer_ids(
        ["String Input", {"name": "Dict Input"}, performer_with_id]
    )

    assert result == ["p1", "p2", "p3"]
    assert len(graphql_route.calls) == 2


@pytest.mark.asyncio
@pytest.mark.unit
async def test_map_performer_ids_empty_list(respx_stash_client: StashClient) -> None:
    """Test map_performer_ids with empty input list.

    This covers the loop with no iterations.
    """
    result = await respx_stash_client.map_performer_ids([])

    assert result == []


@pytest.mark.asyncio
@pytest.mark.unit
async def test_map_performer_ids_dict_input_without_name_key(
    respx_stash_client: StashClient,
) -> None:
    """Test map_performer_ids with dict input that has no 'name' key.

    This covers line 701 false branch (when name is None/missing).
    Dict inputs without a 'name' key are skipped.
    """
    # No HTTP calls should be made - dict without name is skipped
    result = await respx_stash_client.map_performer_ids([{"other_field": "value"}])

    assert result == []


@pytest.mark.asyncio
@pytest.mark.unit
async def test_map_performer_ids_dict_input_multiple_matches_else_default(
    respx_stash_client: StashClient,
) -> None:
    """Test map_performer_ids with dict input and multiple matches using else default.

    This covers lines 719-724: else branch (default behavior for dict input multiple matches).
    When results.count > 1 and on_multiple is neither RETURN_NONE nor RETURN_FIRST,
    the else branch defaults to using the first match.
    """
    performer1_data = create_performer_dict(id="p1", name="Dict Multiple")
    performer2_data = create_performer_dict(id="p2", name="Dict Multiple")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findPerformers",
                    create_find_performers_result(
                        count=2, performers=[performer1_data, performer2_data]
                    ),
                ),
            )
        ]
    )

    # Use RETURN_LIST - falls through to else branch which defaults to first match
    result = await respx_stash_client.map_performer_ids(
        [{"name": "Dict Multiple"}], on_multiple=OnMultipleMatch.RETURN_LIST
    )

    # Else branch defaults to first match (lines 719-724)
    assert result == ["p1"]
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_map_performer_ids_invalid_input_type(
    respx_stash_client: StashClient,
) -> None:
    """Test map_performer_ids with invalid input type (not Performer, str, or dict).

    This covers the else path when performer_input doesn't match any isinstance checks.
    Invalid types (int, None, etc.) are silently skipped and don't raise exceptions.
    """
    # Pass invalid types that don't match any isinstance checks
    # These should be skipped silently (lines 697 false -> loop back to 628)
    result = await respx_stash_client.map_performer_ids(
        [123, None, [], object()]  # type: ignore[list-item]
    )

    # All invalid inputs should be skipped
    assert result == []


@pytest.mark.asyncio
@pytest.mark.unit
async def test_map_performer_ids_exception_handling(
    respx_stash_client: StashClient,
) -> None:
    """Test map_performer_ids exception handling inside the loop.

    This covers lines 736-738: exception handler when any error occurs during processing.
    We trigger an exception by returning malformed data that causes an AttributeError
    when accessing .id on the performer object.
    """
    performer_data = create_performer_dict(id="p1", name="Valid Performer")

    # Mock find_performers to raise an exception for the first call
    original_find_performers = respx_stash_client.find_performers
    call_count = 0

    async def mock_find_performers(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # First call raises an exception (simulates unexpected error during processing)
            raise RuntimeError("Unexpected error during performer lookup")
        # Second call succeeds
        return await original_find_performers(*args, **kwargs)

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            # Second call - for "Valid Performer"
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findPerformers",
                    create_find_performers_result(count=1, performers=[performer_data]),
                ),
            ),
        ]
    )

    with patch.object(
        respx_stash_client, "find_performers", side_effect=mock_find_performers
    ):
        # First performer causes exception, second succeeds
        result = await respx_stash_client.map_performer_ids(
            ["Error Performer", "Valid Performer"]
        )

    # First performer was skipped due to exception (caught at lines 736-738)
    # Second performer succeeded
    assert result == ["p1"]
    assert call_count == 2  # Both calls were attempted

    # Verify the HTTP route was called
    assert len(graphql_route.calls) == 1  # Only one HTTP call (second performer)
