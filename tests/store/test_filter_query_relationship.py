"""Tests for _fetch_filter_query_relationship() and populate() integration.

Tests the new filter_query strategy support in populate(), which uses
filter_query_hint from RelationshipMetadata to fetch inverse relationships
(e.g., Tag.scenes) via lightweight { __typename id } queries that resolve
from the identity map cache.

This follows TESTING_REQUIREMENTS.md:
- Mock only at HTTP boundary using respx
- Verify request AND response
- Use real Pydantic models
"""

import json
from unittest.mock import patch

import httpx
import pytest
import respx

from stash_graphql_client import Scene, Tag
from stash_graphql_client.types.base import RelationshipMetadata
from tests.fixtures import dump_graphql_calls


class TestFetchFilterQueryRelationship:
    """Tests for _fetch_filter_query_relationship()."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_fetches_scenes_for_tag(self, respx_entity_store) -> None:
        """Tag.scenes uses filter_query strategy — verify it builds the correct
        query and resolves cached scene instances."""
        store = respx_entity_store

        # Pre-cache a scene via identity map (from_graphql triggers caching)
        scene = Scene.from_graphql(
            {
                "id": "101",
                "title": "Cached Scene",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        )
        store._cache_entity(scene)

        # Pre-cache a tag
        tag = Tag.from_graphql(
            {
                "id": "201",
                "name": "Test Tag",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "parents": [],
                "children": [],
            }
        )
        store._cache_entity(tag)

        # Mock the filter_query response (lightweight — just __typename and id)
        filter_query_response = {
            "findScenes": {
                "count": 1,
                "scenes": [
                    {"__typename": "Scene", "id": "101"},
                ],
            }
        }

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(200, json={"data": filter_query_response}),
            ]
        )

        try:
            result = await store._fetch_filter_query_relationship(tag, "scenes")
        finally:
            dump_graphql_calls(graphql_route.calls)

        # Verify the query was built correctly
        assert len(graphql_route.calls) == 1
        request_body = json.loads(graphql_route.calls[0].request.content)
        query = request_body["query"]
        assert "findScenes" in query
        assert "scene_filter" in query
        assert "tags" in query
        assert "__typename" in query
        assert "201" in query  # entity ID substituted

        # Verify results
        assert len(result) == 1
        assert result[0].id == "101"
        # Identity map should return the same cached instance
        assert result[0] is scene

        # Verify the field was set on the tag
        assert isinstance(tag.scenes, list)
        assert len(tag.scenes) == 1
        assert tag.scenes[0] is scene

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_empty_relationship(self, respx_entity_store) -> None:
        """filter_query with no results should set an empty list."""
        store = respx_entity_store

        tag = Tag.from_graphql(
            {
                "id": "202",
                "name": "Orphan Tag",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "parents": [],
                "children": [],
            }
        )
        store._cache_entity(tag)

        empty_response = {
            "findScenes": {
                "count": 0,
                "scenes": [],
            }
        }

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(200, json={"data": empty_response}),
            ]
        )

        try:
            result = await store._fetch_filter_query_relationship(tag, "scenes")
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert result == []
        assert tag.scenes == []

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_raises_for_non_filter_query_field(self, respx_entity_store) -> None:
        """Should raise ValueError for fields that aren't filter_query strategy."""
        store = respx_entity_store

        tag = Tag.from_graphql(
            {
                "id": "203",
                "name": "Test",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "parents": [],
                "children": [],
            }
        )

        with pytest.raises(ValueError, match="direct_field"):
            await store._fetch_filter_query_relationship(tag, "parents")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_raises_for_non_relationship_field(self, respx_entity_store) -> None:
        """Should raise ValueError for fields that aren't relationships."""
        store = respx_entity_store

        tag = Tag.from_graphql(
            {
                "id": "204",
                "name": "Test",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "parents": [],
                "children": [],
            }
        )

        with pytest.raises(ValueError, match="not a RelationshipMetadata"):
            await store._fetch_filter_query_relationship(tag, "name")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_raises_for_missing_filter_query_hint(
        self, respx_entity_store
    ) -> None:
        """Should raise ValueError when metadata has filter_query strategy but no hint."""
        store = respx_entity_store

        tag = Tag.from_graphql(
            {
                "id": "206",
                "name": "Test",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "parents": [],
                "children": [],
            }
        )

        # Patch scenes metadata to have filter_query strategy but no hint
        patched = RelationshipMetadata(
            target_field="scene_ids",
            is_list=True,
            query_field="scenes",
            inverse_type="Scene",
            query_strategy="filter_query",
            filter_query_hint=None,
        )
        with (
            patch.dict(tag.__relationships__, {"scenes": patched}),
            pytest.raises(ValueError, match="no filter_query_hint"),
        ):
            await store._fetch_filter_query_relationship(tag, "scenes")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_raises_for_unparseable_filter_query_hint(
        self, respx_entity_store
    ) -> None:
        """Should raise ValueError when the hint doesn't match the expected pattern."""
        store = respx_entity_store

        tag = Tag.from_graphql(
            {
                "id": "207",
                "name": "Test",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "parents": [],
                "children": [],
            }
        )

        patched = RelationshipMetadata(
            target_field="scene_ids",
            is_list=True,
            query_field="scenes",
            inverse_type="Scene",
            query_strategy="filter_query",
            filter_query_hint="this is not a valid hint",
        )
        with (
            patch.dict(tag.__relationships__, {"scenes": patched}),
            pytest.raises(ValueError, match="Cannot parse filter_query_hint"),
        ):
            await store._fetch_filter_query_relationship(tag, "scenes")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_multiple_results_resolved_from_cache(
        self, respx_entity_store
    ) -> None:
        """Multiple results should all resolve from identity map cache."""
        store = respx_entity_store

        # Pre-cache multiple scenes
        scenes = []
        for i in range(3):
            s = Scene.from_graphql(
                {
                    "id": f"{100 + i}",
                    "title": f"Scene {i}",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                }
            )
            store._cache_entity(s)
            scenes.append(s)

        tag = Tag.from_graphql(
            {
                "id": "205",
                "name": "Multi",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "parents": [],
                "children": [],
            }
        )
        store._cache_entity(tag)

        response = {
            "findScenes": {
                "count": 3,
                "scenes": [
                    {"__typename": "Scene", "id": f"{100 + i}"} for i in range(3)
                ],
            }
        }

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(200, json={"data": response}),
            ]
        )

        try:
            result = await store._fetch_filter_query_relationship(tag, "scenes")
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert len(result) == 3
        # Each result should be the exact same cached instance
        for i, item in enumerate(result):
            assert item is scenes[i]

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_received_fields_updated_after_fetch(
        self, respx_entity_store
    ) -> None:
        """_received_fields must include the field after _fetch_filter_query_relationship."""
        store = respx_entity_store

        tag = Tag.from_graphql(
            {
                "id": "208",
                "name": "Recv Test",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "parents": [],
                "children": [],
            }
        )
        store._cache_entity(tag)

        # Verify scenes is NOT in _received_fields initially
        assert "scenes" not in tag._received_fields

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={"data": {"findScenes": {"count": 0, "scenes": []}}},
                ),
            ]
        )

        try:
            await store._fetch_filter_query_relationship(tag, "scenes")
        finally:
            dump_graphql_calls(graphql_route.calls)

        # _received_fields must now include "scenes"
        assert "scenes" in tag._received_fields
        # And missing_fields_nested should NOT report it as missing
        assert not store.missing_fields_nested(tag, "scenes")


class TestPopulateFilterQueryIntegration:
    """Tests for populate() routing filter_query fields correctly."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_populate_routes_filter_query_fields(
        self, respx_entity_store
    ) -> None:
        """populate(tag, fields=["scenes"]) should use _fetch_filter_query_relationship."""
        store = respx_entity_store

        # Pre-cache scene
        scene = Scene.from_graphql(
            {
                "id": "110",
                "title": "Pre-cached",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        )
        store._cache_entity(scene)

        # Pre-cache tag
        tag = Tag.from_graphql(
            {
                "id": "210",
                "name": "Pop Tag",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "parents": [],
                "children": [],
            }
        )
        store._cache_entity(tag)

        filter_response = {
            "findScenes": {
                "count": 1,
                "scenes": [{"__typename": "Scene", "id": "110"}],
            }
        }

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(200, json={"data": filter_response}),
            ]
        )

        try:
            tag = await store.populate(tag, fields=["scenes"])
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert isinstance(tag.scenes, list)
        assert len(tag.scenes) == 1
        assert tag.scenes[0] is scene

        # Only 1 call — the filter_query, NOT a direct findTag fetch
        assert len(graphql_route.calls) == 1
        last_query = json.loads(graphql_route.calls[0].request.content)["query"]
        assert "findScenes" in last_query

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_populate_mixes_direct_and_filter_query_fields(
        self, respx_entity_store
    ) -> None:
        """populate() with both direct and filter_query fields should handle both."""
        store = respx_entity_store

        tag = Tag.from_graphql(
            {
                "id": "220",
                "name": "Mixed Tag",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "parents": [],
                "children": [],
            }
        )
        store._cache_entity(tag)

        # filter_query for scenes
        filter_response = {
            "findScenes": {
                "count": 0,
                "scenes": [],
            }
        }
        # direct field fetch for description (re-fetches tag with description)
        direct_response = {
            "findTag": {
                "__typename": "Tag",
                "id": "220",
                "name": "Mixed Tag",
                "description": "A tag with a description",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        }

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(200, json={"data": filter_response}),
                httpx.Response(200, json={"data": direct_response}),
            ]
        )

        try:
            tag = await store.populate(tag, fields=["scenes", "description"])
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert tag.scenes == []
        assert tag.description == "A tag with a description"

        # 2 calls: filter_query for scenes, then direct fetch for description
        assert len(graphql_route.calls) == 2

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_populate_does_not_route_single_value_filter_query(
        self, respx_entity_store
    ) -> None:
        """Scene.studio has filter_query strategy but is_list=False,
        so populate should fetch it as a direct field, NOT via filter_query."""
        store = respx_entity_store

        scene = Scene.from_graphql(
            {
                "id": "130",
                "title": "Studio Test",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        )
        store._cache_entity(scene)

        # Direct field fetch returns studio
        direct_response = {
            "findScene": {
                "__typename": "Scene",
                "id": "130",
                "title": "Studio Test",
                "studio": {"__typename": "Studio", "id": "301", "name": "Acme"},
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        }

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(200, json={"data": direct_response}),
            ]
        )

        try:
            scene = await store.populate(scene, fields=["studio"])
        finally:
            dump_graphql_calls(graphql_route.calls)

        # Should have used a direct findScene query, NOT findScenes filter
        assert len(graphql_route.calls) == 1
        query = json.loads(graphql_route.calls[0].request.content)["query"]
        assert "findScene" in query
        assert "findScenes" not in query


class TestResolveEntityType:
    """Tests for _resolve_entity_type()."""

    @pytest.mark.unit
    def test_resolves_string_type(self, respx_entity_store) -> None:
        store = respx_entity_store
        cls = store._resolve_entity_type("Scene")
        assert cls is Scene

    @pytest.mark.unit
    def test_resolves_class_type(self, respx_entity_store) -> None:
        store = respx_entity_store
        cls = store._resolve_entity_type(Tag)
        assert cls is Tag

    @pytest.mark.unit
    def test_raises_for_none(self, respx_entity_store) -> None:
        store = respx_entity_store
        with pytest.raises(ValueError, match="None"):
            store._resolve_entity_type(None)

    @pytest.mark.unit
    def test_raises_for_unknown_string(self, respx_entity_store) -> None:
        store = respx_entity_store
        with pytest.raises(ValueError, match="Cannot resolve type"):
            store._resolve_entity_type("NonExistentType")

    @pytest.mark.unit
    def test_raises_for_unexpected_type_ref(self, respx_entity_store) -> None:
        store = respx_entity_store
        with pytest.raises(ValueError, match="Unexpected type_ref"):
            store._resolve_entity_type(42)  # type: ignore[arg-type]
