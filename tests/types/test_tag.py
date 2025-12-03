"""Tests for stash_graphql_client.types.tag module."""

import httpx
import pytest
import respx

from stash_graphql_client import StashClient
from stash_graphql_client.types.tag import Tag
from tests.fixtures import create_graphql_response, create_tag_dict


class TestTagFindByName:
    """Tests for Tag.find_by_name() classmethod."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_find_by_name_exact_match(
        self, respx_stash_client: StashClient
    ) -> None:
        """Test find_by_name returns tag when exact name match is found."""
        tag_data = create_tag_dict(id="123", name="TestTag")

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json=create_graphql_response(
                        "findTags", {"count": 1, "tags": [tag_data]}
                    ),
                )
            ]
        )

        result = await Tag.find_by_name(respx_stash_client, "TestTag")

        assert result is not None
        assert result.id == "123"
        assert result.name == "TestTag"
        assert len(graphql_route.calls) == 1

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_find_by_name_case_insensitive_match(
        self, respx_stash_client: StashClient
    ) -> None:
        """Test find_by_name falls back to case-insensitive search.

        When exact match (EQUALS) fails, it tries INCLUDES and filters
        for case-insensitive exact match.
        """
        tag_data = create_tag_dict(id="456", name="testtag")

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                # First call: exact match returns nothing
                httpx.Response(
                    200,
                    json=create_graphql_response("findTags", {"count": 0, "tags": []}),
                ),
                # Second call: INCLUDES search returns the tag
                httpx.Response(
                    200,
                    json=create_graphql_response(
                        "findTags", {"count": 1, "tags": [tag_data]}
                    ),
                ),
            ]
        )

        # Search with different case
        result = await Tag.find_by_name(respx_stash_client, "TestTag")

        assert result is not None
        assert result.id == "456"
        assert result.name == "testtag"
        # Should have made 2 calls: EQUALS first, then INCLUDES
        assert len(graphql_route.calls) == 2

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_find_by_name_no_match(self, respx_stash_client: StashClient) -> None:
        """Test find_by_name returns None when no match is found."""
        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                # First call: exact match returns nothing
                httpx.Response(
                    200,
                    json=create_graphql_response("findTags", {"count": 0, "tags": []}),
                ),
                # Second call: INCLUDES search also returns nothing
                httpx.Response(
                    200,
                    json=create_graphql_response("findTags", {"count": 0, "tags": []}),
                ),
            ]
        )

        result = await Tag.find_by_name(respx_stash_client, "NonExistentTag")

        assert result is None
        assert len(graphql_route.calls) == 2

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_find_by_name_includes_returns_partial_match_only(
        self, respx_stash_client: StashClient
    ) -> None:
        """Test find_by_name returns None when INCLUDES only finds partial matches.

        INCLUDES might return tags that contain the search term but aren't
        exact matches (even case-insensitively).
        """
        # These tags contain "Test" but aren't "Test" exactly
        partial_tags = [
            create_tag_dict(id="1", name="Testing"),
            create_tag_dict(id="2", name="AnotherTest"),
        ]

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                # First call: exact match returns nothing
                httpx.Response(
                    200,
                    json=create_graphql_response("findTags", {"count": 0, "tags": []}),
                ),
                # Second call: INCLUDES returns partial matches only
                httpx.Response(
                    200,
                    json=create_graphql_response(
                        "findTags", {"count": 2, "tags": partial_tags}
                    ),
                ),
            ]
        )

        result = await Tag.find_by_name(respx_stash_client, "Test")

        # Should return None because none of the partial matches are exact
        assert result is None
        assert len(graphql_route.calls) == 2

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_find_by_name_error_handling(
        self, respx_stash_client: StashClient
    ) -> None:
        """Test find_by_name returns None on exception."""
        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    500, json={"errors": [{"message": "Internal server error"}]}
                )
            ]
        )

        result = await Tag.find_by_name(respx_stash_client, "ErrorTag")

        assert result is None
        assert len(graphql_route.calls) == 1

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_find_by_name_case_insensitive_exact_match_filtering(
        self, respx_stash_client: StashClient
    ) -> None:
        """Test that case-insensitive matching correctly filters results.

        When searching for "Diva", and INCLUDES returns multiple tags,
        it should find the one where name.lower() == "diva".
        """
        # Multiple tags returned by INCLUDES, only one is exact match
        tags_data = [
            create_tag_dict(id="1", name="diva"),  # This is the exact match
            create_tag_dict(id="2", name="Diva Queen"),  # Contains but not exact
            create_tag_dict(id="3", name="The Diva"),  # Contains but not exact
        ]

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                # First call: exact match (case-sensitive) returns nothing
                httpx.Response(
                    200,
                    json=create_graphql_response("findTags", {"count": 0, "tags": []}),
                ),
                # Second call: INCLUDES returns all matching tags
                httpx.Response(
                    200,
                    json=create_graphql_response(
                        "findTags", {"count": 3, "tags": tags_data}
                    ),
                ),
            ]
        )

        result = await Tag.find_by_name(respx_stash_client, "Diva")

        assert result is not None
        assert result.id == "1"
        assert result.name == "diva"
        assert len(graphql_route.calls) == 2
