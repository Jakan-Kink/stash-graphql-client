"""Integration tests for file reverse-relationship navigation (stashapp/stash #6938).

Validated against a real Stash instance, for VideoFile/ImageFile/GalleryFile:

1. The path-as-join-key assumption holds — ``find{Scenes,Images,Galleries}``
   filtered by a file's path returns the entity that owns it. This is what the
   fallback relies on for servers without the #6938 resolvers.
2. The adaptive ``store.populate(file, [reverse_field])`` yields the owning
   entity via whichever path the server supports (direct_field resolver or path
   fallback).

Each case skips gracefully when the test Stash has no entity of that type with a
matching file + path (a ``GalleryFile`` is a compressed archive — zip/cbz by
default — so a gallery not backed by one has no ``GalleryFile``).
"""

from dataclasses import dataclass

import pytest

from stash_graphql_client import StashClient
from stash_graphql_client.types.files import GalleryFile, ImageFile, VideoFile
from stash_graphql_client.types.unset import is_set
from tests.fixtures import capture_graphql_calls, dump_graphql_calls


@dataclass(frozen=True)
class _ReverseCase:
    """Per-entity wiring for a file reverse relationship."""

    finder: str  # client method, e.g. "find_scenes"
    result_attr: str  # result list attr, e.g. "scenes"
    file_accessor: str  # entity attr holding the file list, e.g. "files"
    file_type: type  # concrete file subtype carrying the reverse field
    reverse_field: str  # field on the file pointing back, e.g. "scenes"
    filter_key: str  # entity filter kwarg, e.g. "scene_filter"


_CASES = [
    pytest.param(
        _ReverseCase(
            "find_scenes", "scenes", "files", VideoFile, "scenes", "scene_filter"
        ),
        marks=pytest.mark.requires_scenes,
        id="scene",
    ),
    pytest.param(
        _ReverseCase(
            "find_images",
            "images",
            "visual_files",
            ImageFile,
            "images",
            "image_filter",
        ),
        marks=pytest.mark.requires_images,
        id="image",
    ),
    pytest.param(
        _ReverseCase(
            "find_galleries",
            "galleries",
            "files",
            GalleryFile,
            "galleries",
            "gallery_filter",
        ),
        marks=pytest.mark.requires_galleries,
        id="gallery",
    ),
]


def _first_with_file(entities, accessor, file_type):
    """First (entity, file-of-type-with-path) pair, or (None, None)."""
    for entity in entities if is_set(entities) else []:
        files = getattr(entity, accessor, None)
        for file in (files if is_set(files) else None) or []:
            if (
                isinstance(file, file_type)
                and is_set(getattr(file, "path", None))
                and file.path
            ):
                return entity, file
    return None, None


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize("case", _CASES)
async def test_path_is_valid_join_key_for_file_reverse(
    case: _ReverseCase, stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """find{Type} filtered by a file's path returns the entity that owns it.

    This is the join key the reverse-relationship fallback relies on for servers
    that predate the #6938 resolvers.
    """
    finder = getattr(stash_client, case.finder)
    async with (
        stash_cleanup_tracker(stash_client),
        capture_graphql_calls(stash_client) as calls,
    ):
        try:
            result = await finder(filter_={"per_page": 25})
        finally:
            dump_graphql_calls(calls, case.finder)
        assert is_set(result.count)
        assert result.count > 0

        entity, file = _first_with_file(
            getattr(result, case.result_attr), case.file_accessor, case.file_type
        )
        if entity is None:
            pytest.skip(
                f"No {case.result_attr} with a {case.file_type.__name__} + path "
                "in test Stash instance"
            )

        calls.clear()
        try:
            by_path = await finder(
                **{
                    case.filter_key: {
                        "path": {"value": file.path, "modifier": "EQUALS"}
                    }
                }
            )
        finally:
            dump_graphql_calls(calls, f"{case.finder}_by_path")

        found = getattr(by_path, case.result_attr)
        assert is_set(found)
        assert entity.id in {e.id for e in found}, (
            "path EQUALS filter did not return the owning entity"
        )


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize("case", _CASES)
async def test_adaptive_populate_file_reverse(
    case: _ReverseCase, stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """store.populate(file, [reverse_field]) yields the owning entity via the
    direct_field resolver or the path-filter fallback, whichever the server
    supports."""
    finder = getattr(stash_client, case.finder)
    async with stash_cleanup_tracker(stash_client):
        result = await finder(filter_={"per_page": 25})
        entity, file = _first_with_file(
            getattr(result, case.result_attr), case.file_accessor, case.file_type
        )
        if entity is None:
            pytest.skip(
                f"No {case.result_attr} with a {case.file_type.__name__} + path "
                "in test Stash instance"
            )

        store = file._store
        assert store is not None, "store should be initialized on the client"

        # The reverse field is unqueried (UNSET) on the file from the entity
        # fragment; the adaptive populate must fill it via resolver or fallback.
        populated = await store.populate(file, fields=[case.reverse_field])

        reverse = getattr(populated, case.reverse_field)
        assert is_set(reverse)
        assert reverse is not None
        assert entity.id in {e.id for e in reverse}, (
            "adaptive populate did not return the owning entity"
        )
