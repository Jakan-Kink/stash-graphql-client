"""Tests for stash_graphql_client.types.tag module.

Tests Tag.find_by_name() method with exact match and case-insensitive fallback.

Following TESTING_REQUIREMENTS.md:
- Mock at HTTP boundary only with respx
- Test real code paths (no AsyncMock of client methods)
- Verify GraphQL requests and responses
"""

import httpx
import pytest
import respx

from stash_graphql_client.types.tag import Tag
from tests.fixtures import create_find_tags_result, create_tag_dict


@pytest.mark.unit
@pytest.mark.asyncio
async def test_tag_find_by_name_exact_match(respx_stash_client) -> None:
    """Test Tag.find_by_name() with exact match found.

    This covers lines 162-173 in tag.py - the exact match path.
    """
    # Create mock response data
    tag_data = create_tag_dict(id="789", name="Action")
    find_result = create_find_tags_result(count=1, tags=[tag_data])

    with respx.mock:
        route = respx.post("http://localhost:9999/graphql").mock(
            return_value=httpx.Response(200, json={"data": {"findTags": find_result}})
        )

        # Call find_by_name with real client
        result = await Tag.find_by_name(respx_stash_client, "Action")

        # Verify GraphQL call was made with EQUALS modifier
        assert len(route.calls) == 1

        # Verify query and variables
        import json

        body = json.loads(route.calls[0].request.content)
        assert "findTags" in body["query"]
        assert body["variables"]["tag_filter"]["name"]["value"] == "Action"
        assert body["variables"]["tag_filter"]["name"]["modifier"] == "EQUALS"

        # Verify result
        assert isinstance(result, Tag)
        assert result.id == "789"
        assert result.name == "Action"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_tag_find_by_name_case_insensitive_match(respx_stash_client) -> None:
    """Test Tag.find_by_name() falls back to case-insensitive search.

    This covers lines 175-193 in tag.py - the case-insensitive fallback.
    """
    # Create mock response data
    tag_data = create_tag_dict(id="123", name="diva")
    empty_result = create_find_tags_result(count=0, tags=[])
    insensitive_result = create_find_tags_result(count=1, tags=[tag_data])

    with respx.mock:
        # First call (EQUALS) returns empty, second call (INCLUDES) finds it
        route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(200, json={"data": {"findTags": empty_result}}),
                httpx.Response(200, json={"data": {"findTags": insensitive_result}}),
            ]
        )

        # Call find_by_name with "Diva" (different case)
        result = await Tag.find_by_name(respx_stash_client, "Diva")

        # Should have made 2 calls
        assert len(route.calls) == 2

        # Verify first call: exact match with EQUALS
        import json

        body1 = json.loads(route.calls[0].request.content)
        assert body1["variables"]["tag_filter"]["name"]["modifier"] == "EQUALS"

        # Verify second call: case-insensitive with INCLUDES
        body2 = json.loads(route.calls[1].request.content)
        assert body2["variables"]["tag_filter"]["name"]["modifier"] == "INCLUDES"

        # Verify result matches (case-insensitive)
        assert isinstance(result, Tag)
        assert result.id == "123"
        assert result.name == "diva"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_tag_find_by_name_case_insensitive_filters_results(
    respx_stash_client,
) -> None:
    """Test Tag.find_by_name() filters case-insensitive results correctly.

    This covers lines 187-193 in tag.py - the filtering loop for case-insensitive match.
    """
    # Create mock response data with multiple results that need filtering
    tag1 = create_tag_dict(id="1", name="divine")
    tag2 = create_tag_dict(id="2", name="Diva")
    tag3 = create_tag_dict(id="3", name="dividend")

    empty_result = create_find_tags_result(count=0, tags=[])
    insensitive_result = create_find_tags_result(count=3, tags=[tag1, tag2, tag3])

    with respx.mock:
        # First call (EQUALS) returns empty, second call (INCLUDES) returns multiple
        route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(200, json={"data": {"findTags": empty_result}}),
                httpx.Response(200, json={"data": {"findTags": insensitive_result}}),
            ]
        )

        # Call find_by_name
        result = await Tag.find_by_name(respx_stash_client, "diva")

        # Should have made 2 calls
        assert len(route.calls) == 2

        # Should return the exact case-insensitive match
        assert isinstance(result, Tag)
        assert result.id == "2"
        assert result.name == "Diva"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_tag_find_by_name_not_found(respx_stash_client) -> None:
    """Test Tag.find_by_name() returns None when tag not found.

    This covers lines 195-196 in tag.py - the None return when not found.
    """
    # Mock empty results for both calls
    empty_result = create_find_tags_result(count=0, tags=[])

    with respx.mock:
        route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(200, json={"data": {"findTags": empty_result}}),
                httpx.Response(200, json={"data": {"findTags": empty_result}}),
            ]
        )

        # Call find_by_name
        result = await Tag.find_by_name(respx_stash_client, "NonExistent")

        # Should have made 2 calls (exact then case-insensitive)
        assert len(route.calls) == 2

        # Should return None
        assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_tag_find_by_name_exception(respx_stash_client) -> None:
    """Test Tag.find_by_name() returns None on exception.

    This covers lines 197-199 in tag.py - the exception handling.
    """
    # Mock HTTP error
    with respx.mock:
        route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=httpx.ConnectError("Connection failed")
        )

        # Call find_by_name
        result = await Tag.find_by_name(respx_stash_client, "Action")

        # Verify GraphQL call was attempted
        assert len(route.calls) == 1

        # Should return None (not raise)
        assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_tag_find_by_name_case_insensitive_no_exact_match(
    respx_stash_client,
) -> None:
    """Test Tag.find_by_name() when INCLUDES finds results but none match exactly.

    This covers the path where INCLUDES returns results but filtering finds no exact match.
    """
    # Create mock response data where INCLUDES returns results but none match exactly
    tag1 = create_tag_dict(id="1", name="active")
    tag2 = create_tag_dict(id="2", name="react")

    empty_result = create_find_tags_result(count=0, tags=[])
    insensitive_result = create_find_tags_result(count=2, tags=[tag1, tag2])

    with respx.mock:
        # First call (EQUALS) returns empty, second call (INCLUDES) returns non-matching results
        route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(200, json={"data": {"findTags": empty_result}}),
                httpx.Response(200, json={"data": {"findTags": insensitive_result}}),
            ]
        )

        # Call find_by_name with "action"
        result = await Tag.find_by_name(respx_stash_client, "action")

        # Should have made 2 calls
        assert len(route.calls) == 2

        # Should return None (no case-insensitive exact match)
        assert result is None
