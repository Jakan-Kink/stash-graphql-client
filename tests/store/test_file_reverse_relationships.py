"""Tests for file reverse-relationship navigation (stashapp/stash #6938).

VideoFile.scenes, ImageFile.images, and GalleryFile.galleries are read-only
resolvers that let a file navigate back to the entities using it. They are
introspection-gated (no appSchema bump) and resolved via ``findFile`` — which
returns the ``BaseFile`` interface, so the subtype-only reverse fields must be
selected through an inline fragment (``... on VideoFile { scenes { ... } }``).

Follows TESTING_REQUIREMENTS.md: mock only at the HTTP boundary via respx,
execute the real store/populate code, assert request query AND response usage.
"""

import json

import httpx
import pytest
import respx

from stash_graphql_client import Scene
from stash_graphql_client.types.files import VideoFile
from stash_graphql_client.types.unset import UnsetType
from tests.fixtures import dump_graphql_calls


_SCENE_ITEM = {
    "__typename": "Scene",
    "id": "1",
    "title": "S1",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
}

_FIND_FILE_RESPONSE = {
    "findFile": {
        "__typename": "VideoFile",
        "id": "500",
        "path": "/v.mp4",
        "scenes": [_SCENE_ITEM],
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }
}


def _dispatch_by_query(request: httpx.Request) -> httpx.Response:
    """Route findFile / findScene so nested population doesn't exhaust the mock."""
    query = json.loads(request.content).get("query", "")
    if "findFile" in query:
        return httpx.Response(200, json={"data": _FIND_FILE_RESPONSE})
    if "findScene" in query:
        return httpx.Response(200, json={"data": {"findScene": _SCENE_ITEM}})
    return httpx.Response(200, json={"data": {}})


class TestFileReverseRelationshipQueryBuilding:
    """The findFile populate must select reverse fields via an inline fragment."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_populate_video_file_scenes_uses_inline_fragment(
        self, respx_entity_store_with_file_reverse_caps
    ) -> None:
        """Populating VideoFile.scenes emits ``... on VideoFile { scenes }``.

        ``scenes`` is not a field on the ``BaseFile`` interface that ``findFile``
        returns, so a bare ``scenes { ... }`` selection is invalid GraphQL. The
        query builder must narrow with an inline fragment on the concrete subtype.
        """
        store = respx_entity_store_with_file_reverse_caps

        route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=_dispatch_by_query
        )

        video_file = VideoFile(id="500", path="/v.mp4")

        try:
            populated = await store.populate(video_file, fields=["scenes"])
        finally:
            dump_graphql_calls(route.calls)

        find_file_calls = [
            c
            for c in route.calls
            if "findFile" in json.loads(c.request.content).get("query", "")
        ]
        assert len(find_file_calls) == 1, "expected exactly one findFile query"
        find_file_query = json.loads(find_file_calls[0].request.content)["query"]
        assert "... on VideoFile" in find_file_query
        assert "scenes" in find_file_query

        # Response used: the reverse list is attached and identity-map resolved.
        assert populated.scenes is not None
        assert populated.scenes[0].id == "1"
        assert isinstance(populated.scenes[0], Scene)


class TestFileReverseRelationshipFallback:
    """On servers without #6938, populate falls back to a path-filtered query."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_populate_video_file_scenes_falls_back_to_path_filter(
        self, respx_entity_store
    ) -> None:
        """Without the resolver capability, VideoFile.scenes is populated via
        findScenes filtered by the file's path — not via a findFile selection.

        ``respx_entity_store`` advertises capabilities that do NOT include the
        reverse-relationship resolvers, so ``has_file_reverse_relationships`` is
        False and the adaptive populate must take the filter-query branch.
        """
        store = respx_entity_store

        def responder(request: httpx.Request) -> httpx.Response:
            query = json.loads(request.content).get("query", "")
            if "findScenes" in query:
                return httpx.Response(
                    200,
                    json={
                        "data": {"findScenes": {"count": 1, "scenes": [_SCENE_ITEM]}}
                    },
                )
            return httpx.Response(200, json={"data": {}})

        route = respx.post("http://localhost:9999/graphql").mock(side_effect=responder)

        video_file = VideoFile(id="500", path="/v.mp4")

        try:
            populated = await store.populate(video_file, fields=["scenes"])
        finally:
            dump_graphql_calls(route.calls)

        calls = [json.loads(c.request.content) for c in route.calls]

        # Uncapable server: never attempt the findFile inline-fragment selection.
        assert not any("findFile" in c.get("query", "") for c in calls)

        # Instead, a findScenes filtered by the file's path was issued.
        find_scenes = [c for c in calls if "findScenes" in c.get("query", "")]
        assert find_scenes, "expected a findScenes fallback query"
        assert any(
            c.get("variables", {}).get("scene_filter", {}).get("path", {}).get("value")
            == "/v.mp4"
            for c in find_scenes
        )

        # Reverse list populated equivalently to the direct_field path.
        assert populated.scenes is not None
        assert populated.scenes[0].id == "1"
        assert isinstance(populated.scenes[0], Scene)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_fallback_refetches_path_when_file_path_unknown(
        self, respx_entity_store
    ) -> None:
        """When the file has no local path, the fallback fetches it via findFile
        (base fragment) before issuing the path-filtered query."""
        store = respx_entity_store

        def responder(request: httpx.Request) -> httpx.Response:
            query = json.loads(request.content).get("query", "")
            if "findFile" in query:
                return httpx.Response(
                    200,
                    json={
                        "data": {
                            "findFile": {
                                "__typename": "VideoFile",
                                "id": "500",
                                "path": "/v.mp4",
                                "created_at": "2024-01-01T00:00:00Z",
                                "updated_at": "2024-01-01T00:00:00Z",
                            }
                        }
                    },
                )
            if "findScenes" in query:
                return httpx.Response(
                    200,
                    json={
                        "data": {"findScenes": {"count": 1, "scenes": [_SCENE_ITEM]}}
                    },
                )
            return httpx.Response(200, json={"data": {}})

        route = respx.post("http://localhost:9999/graphql").mock(side_effect=responder)

        video_file = VideoFile(id="500")  # no path known locally

        try:
            populated = await store.populate(video_file, fields=["scenes"])
        finally:
            dump_graphql_calls(route.calls)

        calls = [json.loads(c.request.content) for c in route.calls]
        # The path was refetched via findFile, then used in the findScenes filter.
        assert any("findFile" in c.get("query", "") for c in calls)
        find_scenes = [c for c in calls if "findScenes" in c.get("query", "")]
        assert any(
            c.get("variables", {}).get("scene_filter", {}).get("path", {}).get("value")
            == "/v.mp4"
            for c in find_scenes
        )
        assert populated.scenes is not None
        assert populated.scenes[0].id == "1"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_fallback_leaves_field_unset_when_path_unavailable(
        self, respx_entity_store
    ) -> None:
        """If the file's path can't be resolved, the fallback skips gracefully:
        no findScenes is issued and the field is left UNSET (not falsely marked
        as received)."""
        store = respx_entity_store

        def responder(request: httpx.Request) -> httpx.Response:
            query = json.loads(request.content).get("query", "")
            if "findFile" in query:
                # File comes back without a path (partial/edge data).
                return httpx.Response(
                    200,
                    json={
                        "data": {
                            "findFile": {
                                "__typename": "VideoFile",
                                "id": "500",
                                "created_at": "2024-01-01T00:00:00Z",
                                "updated_at": "2024-01-01T00:00:00Z",
                            }
                        }
                    },
                )
            return httpx.Response(200, json={"data": {}})

        route = respx.post("http://localhost:9999/graphql").mock(side_effect=responder)

        video_file = VideoFile(id="500")  # no path known locally

        try:
            populated = await store.populate(video_file, fields=["scenes"])
        finally:
            dump_graphql_calls(route.calls)

        calls = [json.loads(c.request.content) for c in route.calls]
        # No findScenes attempted without a join key.
        assert not any("findScenes" in c.get("query", "") for c in calls)
        # Field left UNSET, and not falsely recorded as received.
        assert isinstance(populated.scenes, UnsetType)
        assert "scenes" not in getattr(populated, "_received_fields", set())
