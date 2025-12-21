"""Unit tests for TagClientMixin.

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
from stash_graphql_client.types import Tag, TagDestroyInput
from tests.fixtures import (
    create_find_tags_result,
    create_graphql_response,
    create_tag_dict,
)


# =============================================================================
# find_tag tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_tag_by_id(respx_stash_client: StashClient) -> None:
    """Test finding a tag by ID."""
    tag_data = create_tag_dict(id="123", name="Test Tag")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("findTag", tag_data))
        ]
    )

    tag = await respx_stash_client.find_tag("123")

    assert tag is not None
    assert tag.id == "123"
    assert tag.name == "Test Tag"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "findTag" in req["query"]
    assert req["variables"]["id"] == "123"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_tag_not_found(respx_stash_client: StashClient) -> None:
    """Test finding a tag that doesn't exist."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(200, json=create_graphql_response("findTag", None))]
    )

    tag = await respx_stash_client.find_tag("999")

    assert tag is None
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_tag_error_returns_none(respx_stash_client: StashClient) -> None:
    """Test that find_tag returns None on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    tag = await respx_stash_client.find_tag("error_id")

    assert tag is None
    assert len(graphql_route.calls) == 1


# =============================================================================
# find_tags tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_tags(respx_stash_client: StashClient) -> None:
    """Test finding tags."""
    tag_data = create_tag_dict(id="123", name="Test Tag")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findTags",
                    create_find_tags_result(count=1, tags=[tag_data]),
                ),
            )
        ]
    )

    result = await respx_stash_client.find_tags()

    assert result.count == 1
    assert len(result.tags) == 1
    assert result.tags[0].id == "123"

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_tags_with_q_parameter(respx_stash_client: StashClient) -> None:
    """Test finding tags with q parameter.

    This covers lines 64-66: if q is not None.
    """
    tag_data = create_tag_dict(id="123", name="Search Result")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findTags",
                    create_find_tags_result(count=1, tags=[tag_data]),
                ),
            )
        ]
    )

    result = await respx_stash_client.find_tags(q="Search Result")

    assert result.count == 1
    assert result.tags[0].name == "Search Result"

    # Verify q was passed in filter
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["filter"]["q"] == "Search Result"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_tags_with_custom_filter(respx_stash_client: StashClient) -> None:
    """Test finding tags with custom filter_ parameter."""
    tag_data = create_tag_dict(id="123", name="Paginated Result")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findTags",
                    create_find_tags_result(count=1, tags=[tag_data]),
                ),
            )
        ]
    )

    result = await respx_stash_client.find_tags(
        filter_={"page": 2, "per_page": 10, "sort": "name", "direction": "ASC"}
    )

    assert result.count == 1
    assert result.tags[0].name == "Paginated Result"

    # Verify the custom filter was passed
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["filter"]["page"] == 2
    assert req["variables"]["filter"]["per_page"] == 10


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_tags_error_returns_empty(respx_stash_client: StashClient) -> None:
    """Test that find_tags returns empty result on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    result = await respx_stash_client.find_tags()

    assert result.count == 0
    assert len(result.tags) == 0

    assert len(graphql_route.calls) == 1


# =============================================================================
# create_tag tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_tag(respx_stash_client: StashClient) -> None:
    """Test creating a tag.

    This covers lines 91-97: successful creation.
    """
    created_tag_data = create_tag_dict(
        id="new_tag_123",
        name="New Tag",
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("tagCreate", created_tag_data)
            )
        ]
    )

    tag = Tag(id="new", name="New Tag")
    result = await respx_stash_client.create_tag(tag)

    assert result is not None
    assert result.id == "new_tag_123"
    assert result.name == "New Tag"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "tagCreate" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_tag_already_exists_fallback(
    respx_stash_client: StashClient,
) -> None:
    """Test create_tag falls back to finding existing tag.

    This covers lines 98-111: when tag already exists error.
    """
    existing_tag_data = create_tag_dict(
        id="existing_123",
        name="Existing Tag",
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
                        {"message": "tag with name 'Existing Tag' already exists"}
                    ],
                },
            )
        # Second call - find existing tag
        return httpx.Response(
            200,
            json=create_graphql_response(
                "findTags",
                create_find_tags_result(count=1, tags=[existing_tag_data]),
            ),
        )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=mock_response
    )

    tag = Tag(id="new", name="Existing Tag")
    result = await respx_stash_client.create_tag(tag)

    assert result is not None
    assert result.id == "existing_123"
    assert result.name == "Existing Tag"

    # Should have made 2 calls - create then find
    assert len(graphql_route.calls) == 2


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_tag_already_exists_but_not_found_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test create_tag re-raises when tag 'already exists' but can't be found.

    This covers line 111: raise when results.count == 0 after "already exists" error.
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
                    "errors": [{"message": "tag with name 'Ghost Tag' already exists"}],
                },
            )
        # Second call - but tag is NOT found (count=0)
        return httpx.Response(
            200,
            json=create_graphql_response(
                "findTags",
                create_find_tags_result(count=0, tags=[]),
            ),
        )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=mock_response
    )

    tag = Tag(id="new", name="Ghost Tag")

    with pytest.raises(StashGraphQLError):
        await respx_stash_client.create_tag(tag)

    # Should have made 2 calls - create then find (which returned empty)
    assert len(graphql_route.calls) == 2


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_tag_error_raises(respx_stash_client: StashClient) -> None:
    """Test that create_tag raises on error.

    This covers lines 112-113: re-raise when error is not "already exists".
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    tag = Tag(id="new", name="Will Fail")

    with pytest.raises(StashGraphQLError):
        await respx_stash_client.create_tag(tag)

    assert len(graphql_route.calls) == 1


# =============================================================================
# tags_merge tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_tags_merge(respx_stash_client: StashClient) -> None:
    """Test merging tags.

    This covers lines 133-138: successful merge.
    """
    merged_tag_data = create_tag_dict(id="dest_tag", name="Merged Tag")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("tagsMerge", merged_tag_data)
            )
        ]
    )

    result = await respx_stash_client.tags_merge(
        source=["tag1", "tag2", "tag3"],
        destination="dest_tag",
    )

    assert result is not None
    assert result.id == "dest_tag"
    assert result.name == "Merged Tag"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "tagsMerge" in req["query"]
    assert req["variables"]["input"]["source"] == ["tag1", "tag2", "tag3"]
    assert req["variables"]["input"]["destination"] == "dest_tag"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_tags_merge_error_raises(respx_stash_client: StashClient) -> None:
    """Test that tags_merge raises on error.

    This covers lines 139-141: exception handling.
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    with pytest.raises(StashGraphQLError):
        await respx_stash_client.tags_merge(source=["tag1"], destination="dest")

    assert len(graphql_route.calls) == 1


# =============================================================================
# bulk_tag_update tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_bulk_tag_update(respx_stash_client: StashClient) -> None:
    """Test bulk updating tags.

    This covers lines 169-187: successful bulk update.
    """
    updated_tags_data = [
        create_tag_dict(id="t1", name="Tag 1"),
        create_tag_dict(id="t2", name="Tag 2"),
        create_tag_dict(id="t3", name="Tag 3"),
    ]

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("bulkTagUpdate", updated_tags_data)
            )
        ]
    )

    result = await respx_stash_client.bulk_tag_update(
        ids=["t1", "t2", "t3"],
        description="Updated description",
        aliases=["alias1", "alias2"],
        favorite=True,
        parent_ids=["parent1"],
        child_ids=["child1"],
    )

    assert len(result) == 3
    assert result[0].id == "t1"
    assert result[1].id == "t2"
    assert result[2].id == "t3"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "bulkTagUpdate" in req["query"]
    assert req["variables"]["input"]["ids"] == ["t1", "t2", "t3"]
    assert req["variables"]["input"]["description"] == "Updated description"
    assert req["variables"]["input"]["aliases"] == ["alias1", "alias2"]
    assert req["variables"]["input"]["favorite"] is True
    assert req["variables"]["input"]["parent_ids"] == ["parent1"]
    assert req["variables"]["input"]["child_ids"] == ["child1"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_bulk_tag_update_minimal(respx_stash_client: StashClient) -> None:
    """Test bulk updating tags with only required fields."""
    updated_tags_data = [
        create_tag_dict(id="t1", name="Tag 1"),
    ]

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("bulkTagUpdate", updated_tags_data)
            )
        ]
    )

    result = await respx_stash_client.bulk_tag_update(ids=["t1"])

    assert len(result) == 1
    assert result[0].id == "t1"

    # Verify only ids was passed
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["input"] == {"ids": ["t1"]}


@pytest.mark.asyncio
@pytest.mark.unit
async def test_bulk_tag_update_error_raises(respx_stash_client: StashClient) -> None:
    """Test that bulk_tag_update raises on error.

    This covers lines 188-190: exception handling.
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    with pytest.raises(StashGraphQLError):
        await respx_stash_client.bulk_tag_update(ids=["t1", "t2"])

    assert len(graphql_route.calls) == 1


# =============================================================================
# update_tag tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_tag(respx_stash_client: StashClient) -> None:
    """Test updating a tag.

    This covers lines 208-214: successful update.
    """
    updated_tag_data = create_tag_dict(
        id="123",
        name="Updated Tag",
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("tagUpdate", updated_tag_data)
            )
        ]
    )

    tag = Tag(id="123", name="Original Name")
    tag.name = "Updated Tag"

    result = await respx_stash_client.update_tag(tag)

    assert result is not None
    assert result.id == "123"
    assert result.name == "Updated Tag"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "tagUpdate" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_tag_error_raises(respx_stash_client: StashClient) -> None:
    """Test that update_tag raises on error.

    This covers lines 215-217: exception handling.
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    tag = Tag(id="123", name="Will Fail")

    with pytest.raises(StashGraphQLError):
        await respx_stash_client.update_tag(tag)

    assert len(graphql_route.calls) == 1


# =============================================================================
# tag_destroy tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_tag_destroy_with_dict(respx_stash_client: StashClient) -> None:
    """Test destroying a tag with dict input."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("tagDestroy", True))
        ]
    )

    result = await respx_stash_client.tag_destroy({"id": "123"})

    assert result is True

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "tagDestroy" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_tag_destroy_with_input_type(respx_stash_client: StashClient) -> None:
    """Test destroying a tag with TagDestroyInput.

    This covers line 237-238: if isinstance(input_data, TagDestroyInput).
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("tagDestroy", True))
        ]
    )

    input_data = TagDestroyInput(id="123")
    result = await respx_stash_client.tag_destroy(input_data)

    assert result is True

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "tagDestroy" in req["query"]
    assert req["variables"]["input"]["id"] == "123"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_tag_destroy_error_raises(respx_stash_client: StashClient) -> None:
    """Test that tag_destroy raises on error.

    This covers lines 248-250: exception handling.
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    with pytest.raises(StashGraphQLError):
        await respx_stash_client.tag_destroy({"id": "123"})

    assert len(graphql_route.calls) == 1


# =============================================================================
# tags_destroy tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_tags_destroy(respx_stash_client: StashClient) -> None:
    """Test destroying multiple tags."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("tagsDestroy", True))
        ]
    )

    result = await respx_stash_client.tags_destroy(["123", "456", "789"])

    assert result is True

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "tagsDestroy" in req["query"]
    assert req["variables"]["ids"] == ["123", "456", "789"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_tags_destroy_error_raises(respx_stash_client: StashClient) -> None:
    """Test that tags_destroy raises on error.

    This covers lines 272-274: exception handling.
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    with pytest.raises(StashGraphQLError):
        await respx_stash_client.tags_destroy(["123", "456"])

    assert len(graphql_route.calls) == 1


# =============================================================================
# map_tag_ids tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_map_tag_ids_string_input_found(respx_stash_client: StashClient) -> None:
    """Test map_tag_ids with string input - tag found.

    This covers lines 349-350, 352-358: string input, tag found.
    """
    tag_data = create_tag_dict(id="tag123", name="Action")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findTags",
                    create_find_tags_result(count=1, tags=[tag_data]),
                ),
            )
        ]
    )

    result = await respx_stash_client.map_tag_ids(["Action"])

    assert len(result) == 1
    assert result[0] == "tag123"

    # Verify request
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["tag_filter"]["name"]["value"] == "Action"
    assert req["variables"]["tag_filter"]["name"]["modifier"] == "EQUALS"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_map_tag_ids_string_input_not_found_no_create(
    respx_stash_client: StashClient,
) -> None:
    """Test map_tag_ids with string input - tag not found, create=False.

    This covers lines 349-350, 352-357, 364-367: string input, not found, warning logged.
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findTags",
                    create_find_tags_result(count=0, tags=[]),
                ),
            )
        ]
    )

    result = await respx_stash_client.map_tag_ids(["MissingTag"], create=False)

    # Tag not found and create=False, so empty list
    assert len(result) == 0

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_map_tag_ids_string_input_not_found_with_create(
    respx_stash_client: StashClient,
) -> None:
    """Test map_tag_ids with string input - tag not found, create=True.

    This covers lines 349-350, 352-363: string input, not found, create new tag.
    """
    created_tag_data = create_tag_dict(id="new_tag_456", name="NewTag")

    call_count = 0

    def mock_response(request):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # First call - search returns empty
            return httpx.Response(
                200,
                json=create_graphql_response(
                    "findTags",
                    create_find_tags_result(count=0, tags=[]),
                ),
            )
        # Second call - create tag
        return httpx.Response(
            200, json=create_graphql_response("tagCreate", created_tag_data)
        )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=mock_response
    )

    result = await respx_stash_client.map_tag_ids(["NewTag"], create=True)

    assert len(result) == 1
    assert result[0] == "new_tag_456"

    # Should have made 2 calls - find then create
    assert len(graphql_route.calls) == 2


@pytest.mark.asyncio
@pytest.mark.unit
async def test_map_tag_ids_tag_object_with_id(respx_stash_client: StashClient) -> None:
    """Test map_tag_ids with Tag object that has an ID.

    This covers lines 340-344: Tag object with ID, use directly.
    """
    tag = Tag(id="existing123", name="Action")

    # No HTTP calls should be made since tag has ID
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(200, json={})]
    )

    result = await respx_stash_client.map_tag_ids([tag])

    assert len(result) == 1
    assert result[0] == "existing123"

    # Verify NO HTTP calls were made
    assert len(graphql_route.calls) == 0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_map_tag_ids_tag_object_without_id(
    respx_stash_client: StashClient,
) -> None:
    """Test map_tag_ids with Tag object without ID - search by name.

    This covers lines 340-346, 352-358: Tag object without ID, search by name.
    """
    found_tag_data = create_tag_dict(id="drama789", name="Drama")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findTags",
                    create_find_tags_result(count=1, tags=[found_tag_data]),
                ),
            )
        ]
    )

    # Create Tag object without ID using model_construct to avoid auto-generated ID
    tag = Tag.model_construct(name="Drama", id=None)
    result = await respx_stash_client.map_tag_ids([tag])

    assert len(result) == 1
    assert result[0] == "drama789"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["tag_filter"]["name"]["value"] == "Drama"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_map_tag_ids_dict_input_found(respx_stash_client: StashClient) -> None:
    """Test map_tag_ids with dict input containing name - tag found.

    This covers lines 370-377: dict input with name, tag found.
    """
    tag_data = create_tag_dict(id="comedy555", name="Comedy")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findTags",
                    create_find_tags_result(count=1, tags=[tag_data]),
                ),
            )
        ]
    )

    result = await respx_stash_client.map_tag_ids([{"name": "Comedy"}])

    assert len(result) == 1
    assert result[0] == "comedy555"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["tag_filter"]["name"]["value"] == "Comedy"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_map_tag_ids_dict_input_with_create(
    respx_stash_client: StashClient,
) -> None:
    """Test map_tag_ids with dict input - tag not found, create=True.

    This covers lines 370-381: dict input, not found, create new tag.
    """
    created_tag_data = create_tag_dict(id="thriller999", name="Thriller")

    call_count = 0

    def mock_response(request):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # First call - search returns empty
            return httpx.Response(
                200,
                json=create_graphql_response(
                    "findTags",
                    create_find_tags_result(count=0, tags=[]),
                ),
            )
        # Second call - create tag
        return httpx.Response(
            200, json=create_graphql_response("tagCreate", created_tag_data)
        )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=mock_response
    )

    result = await respx_stash_client.map_tag_ids([{"name": "Thriller"}], create=True)

    assert len(result) == 1
    assert result[0] == "thriller999"

    assert len(graphql_route.calls) == 2


@pytest.mark.asyncio
@pytest.mark.unit
async def test_map_tag_ids_dict_input_without_name(
    respx_stash_client: StashClient,
) -> None:
    """Test map_tag_ids with dict input that has no 'name' key.

    This covers line 371: dict without name is skipped.
    """
    # No HTTP calls should be made
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(200, json={})]
    )

    result = await respx_stash_client.map_tag_ids([{"other_field": "value"}])

    # Dict without name is skipped
    assert len(result) == 0
    assert len(graphql_route.calls) == 0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_map_tag_ids_mixed_input_types(respx_stash_client: StashClient) -> None:
    """Test map_tag_ids with mixed input types (string, Tag, dict).

    This tests the full integration across all input types.
    """
    tag_with_id = Tag(id="id1", name="Action")
    tag_without_id = Tag.model_construct(name="Drama", id=None)

    tag_data_drama = create_tag_dict(id="drama123", name="Drama")
    tag_data_comedy = create_tag_dict(id="comedy456", name="Comedy")

    call_count = 0

    def mock_response(request):
        nonlocal call_count
        call_count += 1
        req_data = json.loads(request.content)

        # Check which tag we're searching for
        tag_name = req_data["variables"]["tag_filter"]["name"]["value"]

        if tag_name == "Drama":
            return httpx.Response(
                200,
                json=create_graphql_response(
                    "findTags",
                    create_find_tags_result(count=1, tags=[tag_data_drama]),
                ),
            )
        if tag_name == "Comedy":
            return httpx.Response(
                200,
                json=create_graphql_response(
                    "findTags",
                    create_find_tags_result(count=1, tags=[tag_data_comedy]),
                ),
            )
        # Fallback for unexpected tag names
        return httpx.Response(
            200,
            json=create_graphql_response(
                "findTags",
                create_find_tags_result(count=0, tags=[]),
            ),
        )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=mock_response
    )

    result = await respx_stash_client.map_tag_ids(
        [
            tag_with_id,  # Has ID - no lookup
            tag_without_id,  # No ID - lookup by name
            {"name": "Comedy"},  # Dict - lookup by name
        ]
    )

    assert len(result) == 3
    assert result[0] == "id1"  # Direct from Tag with ID
    assert result[1] == "drama123"  # Found by name search
    assert result[2] == "comedy456"  # Found by dict name search

    # 2 HTTP calls (tag_without_id and dict lookup)
    assert len(graphql_route.calls) == 2


@pytest.mark.asyncio
@pytest.mark.unit
async def test_map_tag_ids_exception_handling(respx_stash_client: StashClient) -> None:
    """Test map_tag_ids exception handling - error logged and continues.

    This covers lines 383-385: exception caught, logged, continue processing.
    """
    tag_data = create_tag_dict(id="good_tag", name="GoodTag")

    # Mock find_tags to raise exception for first call, succeed for second
    original_find_tags = respx_stash_client.find_tags
    call_count = 0

    async def mock_find_tags(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # First call raises exception (bypasses find_tags internal handler)
            raise RuntimeError("Unexpected error during tag lookup")
        # Second call succeeds
        return await original_find_tags(*args, **kwargs)

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            # Second call - for "GoodTag"
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findTags",
                    create_find_tags_result(count=1, tags=[tag_data]),
                ),
            ),
        ]
    )

    with patch.object(respx_stash_client, "find_tags", side_effect=mock_find_tags):
        result = await respx_stash_client.map_tag_ids(["FailTag", "GoodTag"])

    # First tag failed (exception caught at lines 383-385), second succeeded
    assert len(result) == 1
    assert result[0] == "good_tag"

    assert call_count == 2  # Both calls were attempted

    # Verify the HTTP route was called
    assert len(graphql_route.calls) == 1  # Only one HTTP call (second tag)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_map_tag_ids_empty_list(respx_stash_client: StashClient) -> None:
    """Test map_tag_ids with empty input list.

    This covers the base case - empty input returns empty output.
    """
    # No HTTP calls should be made
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(200, json={})]
    )

    result = await respx_stash_client.map_tag_ids([])

    assert len(result) == 0
    assert len(graphql_route.calls) == 0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_map_tag_ids_tag_object_with_empty_name(
    respx_stash_client: StashClient,
) -> None:
    """Test map_tag_ids with Tag object that has empty/None name and no ID.

    This covers line 346: tag_name = tag_input.name or "" - edge case.
    """
    # Create Tag with empty name and explicitly NO id to avoid identity map
    tag = Tag.model_construct(name="", id=None)

    # No HTTP calls should be made since tag_name is empty
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(200, json={})]
    )

    result = await respx_stash_client.map_tag_ids([tag])

    # Empty name tag is skipped
    assert len(result) == 0
    assert len(graphql_route.calls) == 0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_map_tag_ids_dict_not_found_no_create(
    respx_stash_client: StashClient,
) -> None:
    """Test map_tag_ids with dict input - tag not found, create=False.

    This covers lines 382-383: dict input, not found, warning logged.
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findTags",
                    create_find_tags_result(count=0, tags=[]),
                ),
            )
        ]
    )

    result = await respx_stash_client.map_tag_ids(
        [{"name": "MissingTag"}], create=False
    )

    # Tag not found and create=False, so empty list
    assert len(result) == 0

    assert len(graphql_route.calls) == 1
