"""Unit tests for stash_cleanup_tracker auto-capture of created object IDs.

The tracker spies on ``client._session.execute`` to record created object IDs
for teardown. ``store.save_all`` routes through ``execute_batch``, which aliases
every operation (``op0``/``op1``/...) and keys the response by those aliases, so
the tracker must recover each mutation's field name from the request document to
know which cleanup bucket the payload belongs to.
"""

import uuid

import httpx
import pytest
import respx

from stash_graphql_client import Performer, StashEntityStore, Tag
from tests.fixtures import dump_graphql_calls


@pytest.mark.asyncio
@pytest.mark.unit
async def test_auto_capture_records_save_all_batched_aliases(
    respx_entity_store: StashEntityStore,
    respx_stash_client,
    stash_cleanup_tracker,
) -> None:
    """save_all's op-aliased batch creates land in the right cleanup buckets."""
    store = respx_entity_store

    tag = Tag(id=uuid.uuid4().hex, name="Cleanup Tag")
    tag._is_new = True
    store.add(tag)

    performer = Performer(id=uuid.uuid4().hex, name="Cleanup Performer")
    performer._is_new = True
    store.add(performer)

    # save_all orders creates in cache-insertion order: op0=tagCreate, op1=performerCreate.
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "data": {
                        "op0": {"id": "100", "__typename": "Tag"},
                        "op1": {"id": "200", "__typename": "Performer"},
                    }
                },
            )
        ]
    )

    async with stash_cleanup_tracker(respx_stash_client) as cleanup:
        try:
            result = await store.save_all()
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert result.all_succeeded
        assert cleanup["tags"] == ["100"]
        assert cleanup["performers"] == ["200"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_auto_capture_records_single_unaliased_create(
    respx_entity_store: StashEntityStore,
    respx_stash_client,
    stash_cleanup_tracker,
) -> None:
    """An unaliased single create (response keyed by field name) is captured."""
    store = respx_entity_store

    tag = Tag(id=uuid.uuid4().hex, name="Solo Tag")
    tag._is_new = True
    store.add(tag)

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json={"data": {"tagCreate": {"id": "300", "__typename": "Tag"}}}
            )
        ]
    )

    async with stash_cleanup_tracker(respx_stash_client) as cleanup:
        try:
            await store.save(tag)
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert cleanup["tags"] == ["300"]
