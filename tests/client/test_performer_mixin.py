"""Unit tests for PerformerClientMixin.

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
    BulkPerformerUpdateInput,
    BulkUpdateIds,
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
    assert req["variables"]["input"]["tag_ids"]["ids"] == ["tag1", "tag2"]


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
