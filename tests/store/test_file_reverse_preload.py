"""Tests for bulk/preload of files via find_iter(BaseFile, ...) (stashapp/stash #6938).

The preload use case warms the identity map with every file as its concrete
polymorphic subtype (VideoFile/ImageFile/GalleryFile), each carrying the
resolver-backed reverse relationships (scenes/images/galleries). This routes
through StashEntityStore._execute_find_query against the findFiles query.

Follows TESTING_REQUIREMENTS.md: mock only at the HTTP boundary via respx,
execute the real store code, assert request query AND response usage.
"""

import json

import httpx
import pytest
import respx

from stash_graphql_client import Scene
from stash_graphql_client.fragments import FragmentStore
from stash_graphql_client.types.files import (
    BaseFile,
    BasicFile,
    GalleryFile,
    ImageFile,
    VideoFile,
)
from stash_graphql_client.types.unset import UnsetType, is_set
from tests.fixtures import (
    assert_query_fragments_resolve,
    dump_graphql_calls,
    make_server_capabilities,
)


_SCENE_ITEM = {
    "__typename": "Scene",
    "id": "1",
    "title": "S1",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
}

_FIND_FILES_RESPONSE = {
    "findFiles": {
        "count": 1,
        "files": [
            {
                "__typename": "VideoFile",
                "id": "500",
                "path": "/media/v.mp4",
                "scenes": [_SCENE_ITEM],
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        ],
    }
}


class TestFindIterBaseFilePreload:
    """find_iter(BaseFile, ...) issues findFiles and yields concrete subtypes."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_find_iter_basefile_yields_concrete_videofile(
        self, respx_entity_store_with_file_reverse_caps
    ) -> None:
        """find_iter(BaseFile, path__contains=...) yields a VideoFile (not BaseFile).

        The bulk path must route BaseFile through the findFiles query and
        deserialize each item to its concrete __typename subtype, so a preload
        warms the identity map with VideoFile/ImageFile/GalleryFile instances.
        """
        store = respx_entity_store_with_file_reverse_caps

        def responder(request: httpx.Request) -> httpx.Response:
            query = json.loads(request.content).get("query", "")
            if "findFiles" in query:
                return httpx.Response(200, json={"data": _FIND_FILES_RESPONSE})
            return httpx.Response(200, json={"data": {}})

        route = respx.post("http://localhost:9999/graphql").mock(side_effect=responder)

        try:
            results = [
                f async for f in store.find_iter(BaseFile, path__contains="/media/")
            ]
        finally:
            dump_graphql_calls(route.calls)

        # Request: a findFiles query filtered by path was issued.
        find_files = [
            json.loads(c.request.content)
            for c in route.calls
            if "findFiles" in json.loads(c.request.content).get("query", "")
        ]
        assert find_files, "expected a findFiles query"
        assert (
            find_files[0]
            .get("variables", {})
            .get("file_filter", {})
            .get("path", {})
            .get("value")
            == "/media/"
        )

        # The production query must actually SELECT the reverse field (otherwise a
        # live capable server returns scenes=UNSET and only the mock makes this
        # pass). Full ...SceneFragment, narrowed to the VideoFile subtype.
        find_files_query = find_files[0]["query"]
        assert "... on VideoFile" in find_files_query
        assert "scenes" in find_files_query
        assert "...SceneFragment" in find_files_query

        # Response: yielded the concrete subtype with its reverse list populated.
        assert len(results) == 1
        video_file = results[0]
        assert isinstance(video_file, VideoFile)
        reverse_scenes = video_file.scenes
        assert is_set(reverse_scenes)
        assert reverse_scenes is not None
        assert isinstance(reverse_scenes[0], Scene)
        assert reverse_scenes[0].id == "1"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_find_iter_basefile_yields_all_concrete_subtypes(
        self, respx_entity_store_with_file_reverse_caps
    ) -> None:
        """A mixed findFiles page deserializes each item to its concrete subtype.

        Every BaseFile implementation — VideoFile/ImageFile/GalleryFile and the
        fieldless BasicFile (e.g. a zip_file) — must be resolved via __typename so
        a preload warms the identity map with the right polymorphic class for
        every file, not a uniform BaseFile.
        """
        store = respx_entity_store_with_file_reverse_caps

        mixed = {
            "findFiles": {
                "count": 4,
                "files": [
                    {
                        "__typename": "VideoFile",
                        "id": "500",
                        "path": "/v.mp4",
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T00:00:00Z",
                    },
                    {
                        "__typename": "ImageFile",
                        "id": "600",
                        "path": "/i.jpg",
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T00:00:00Z",
                    },
                    {
                        "__typename": "GalleryFile",
                        "id": "700",
                        "path": "/g.zip",
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T00:00:00Z",
                    },
                    {
                        "__typename": "BasicFile",
                        "id": "800",
                        "path": "/archive.zip",
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T00:00:00Z",
                    },
                ],
            }
        }

        def responder(request: httpx.Request) -> httpx.Response:
            query = json.loads(request.content).get("query", "")
            if "findFiles" in query:
                return httpx.Response(200, json={"data": mixed})
            return httpx.Response(200, json={"data": {}})

        route = respx.post("http://localhost:9999/graphql").mock(side_effect=responder)

        try:
            results = [f async for f in store.find_iter(BaseFile)]
        finally:
            dump_graphql_calls(route.calls)

        by_type = {type(f).__name__: f for f in results}
        assert isinstance(by_type["VideoFile"], VideoFile)
        assert isinstance(by_type["ImageFile"], ImageFile)
        assert isinstance(by_type["GalleryFile"], GalleryFile)
        assert isinstance(by_type["BasicFile"], BasicFile)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_reverse_scene_carries_files_resolving_to_owning_file(
        self, respx_entity_store_with_file_reverse_caps
    ) -> None:
        """The full ...SceneFragment delivers each reverse scene's ``files``, and
        the nested file (same id as the owner) resolves to the owning file.

        This is the contract the full-fragment choice was made for — downstream
        callers use ``next(s for s in file.scenes if is_set(s.files) and s.files
        and file == s.files[0])``. Verifies (a) scene.files is populated (not
        UNSET), and (b) the identity map collapses the nested same-id file onto
        the owning file instance.
        """
        store = respx_entity_store_with_file_reverse_caps

        scene_with_owning_file = {
            "__typename": "Scene",
            "id": "1",
            "title": "S1",
            "files": [
                {
                    "__typename": "VideoFile",
                    "id": "500",
                    "path": "/v.mp4",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                }
            ],
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        }
        response = {
            "findFiles": {
                "count": 1,
                "files": [
                    {
                        "__typename": "VideoFile",
                        "id": "500",
                        "path": "/v.mp4",
                        "scenes": [scene_with_owning_file],
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T00:00:00Z",
                    }
                ],
            }
        }

        def responder(request: httpx.Request) -> httpx.Response:
            if "findFiles" in json.loads(request.content).get("query", ""):
                return httpx.Response(200, json={"data": response})
            return httpx.Response(200, json={"data": {}})

        route = respx.post("http://localhost:9999/graphql").mock(side_effect=responder)

        try:
            results = [f async for f in store.find_iter(BaseFile)]
        finally:
            dump_graphql_calls(route.calls)

        file = results[0]
        scene = file.scenes[0]
        # (a) the reverse scene's files came back populated (full fragment).
        assert not isinstance(scene.files, UnsetType)
        assert scene.files
        # (b) the caller's literal pattern: the nested same-id file IS the owner.
        assert scene.files[0] == file
        assert scene.files[0] is file

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_find_iter_basefile_uncapable_yields_files_without_reverse(
        self, respx_entity_store
    ) -> None:
        """On a server without #6938, bulk preload still works: findFiles selects
        no reverse fields, files come back as concrete subtypes, and the reverse
        relationship is left UNSET (no per-file fallback in the bulk path)."""
        store = respx_entity_store

        response = {
            "findFiles": {
                "count": 1,
                "files": [
                    {
                        "__typename": "VideoFile",
                        "id": "500",
                        "path": "/v.mp4",
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T00:00:00Z",
                    }
                ],
            }
        }

        def responder(request: httpx.Request) -> httpx.Response:
            if "findFiles" in json.loads(request.content).get("query", ""):
                return httpx.Response(200, json={"data": response})
            return httpx.Response(200, json={"data": {}})

        route = respx.post("http://localhost:9999/graphql").mock(side_effect=responder)

        try:
            results = [f async for f in store.find_iter(BaseFile)]
        finally:
            dump_graphql_calls(route.calls)

        query = json.loads(route.calls[0].request.content)["query"]
        assert "...SceneFragment" not in query
        assert "scenes {" not in query

        assert isinstance(results[0], VideoFile)
        assert isinstance(results[0].scenes, UnsetType)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_find_iter_basefile_translates_basename_filter(
        self, respx_entity_store_with_file_reverse_caps
    ) -> None:
        """find_iter(BaseFile, basename__equals=...) builds a FileFilterType
        criterion on ``basename`` (a StringCriterionInput field)."""
        store = respx_entity_store_with_file_reverse_caps

        captured: dict = {}

        def responder(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content)
            if "findFiles" in body.get("query", ""):
                captured.update(body.get("variables", {}))
                return httpx.Response(
                    200, json={"data": {"findFiles": {"count": 0, "files": []}}}
                )
            return httpx.Response(200, json={"data": {}})

        route = respx.post("http://localhost:9999/graphql").mock(side_effect=responder)

        try:
            _ = [f async for f in store.find_iter(BaseFile, basename__equals="v.mp4")]
        finally:
            dump_graphql_calls(route.calls)

        assert captured.get("file_filter", {}).get("basename") == {
            "value": "v.mp4",
            "modifier": "EQUALS",
        }


class TestEagerFileQueryAssembly:
    """The capability-gated findFile(s) queries must be valid, self-contained
    GraphQL — the full-fragment reverse selection assembles many fragments and
    must not duplicate or drop any definition."""

    @pytest.mark.unit
    def test_capable_file_queries_have_no_duplicate_or_unresolved_fragments(
        self,
    ) -> None:
        """FIND_FILE(S)_QUERY parse cleanly with every fragment declared exactly
        once and every spread resolvable.

        An isolated FragmentStore is rebuilt with the reverse-relationship
        capability so the queries embed full ...SceneFragment/ImageFragment/
        GalleryFragment alongside the file fragments. Naive concatenation would
        declare FileFields/VideoFileFields multiple times — invalid GraphQL.
        """
        store = FragmentStore()
        store.rebuild(
            make_server_capabilities(
                app_schema=85,
                type_fields={
                    "VideoFile": frozenset({"scenes"}),
                    "ImageFile": frozenset({"images"}),
                    "GalleryFile": frozenset({"galleries"}),
                },
            )
        )

        assert_query_fragments_resolve(store.FIND_FILES_QUERY)
        assert_query_fragments_resolve(store.FIND_FILE_QUERY)
        assert "...SceneFragment" in store.FIND_FILES_QUERY
        assert "...ImageFragment" in store.FIND_FILES_QUERY
        assert "...GalleryFragment" in store.FIND_FILES_QUERY

    @pytest.mark.unit
    def test_uncapable_file_queries_omit_reverse_fields(self) -> None:
        """Without the resolver capability, the base findFile(s) queries are still
        valid and select no reverse fields (so the server is never asked for them).
        """
        store = FragmentStore()  # no capabilities -> base queries

        assert_query_fragments_resolve(store.FIND_FILES_QUERY)
        assert "...SceneFragment" not in store.FIND_FILES_QUERY
        assert "scenes {" not in store.FIND_FILES_QUERY
