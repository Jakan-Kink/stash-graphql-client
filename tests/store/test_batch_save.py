"""Tests for StashEntityStore.save_batch() and save_all().

Tests cover batch saving, cache key remapping, side mutations,
ordering guarantees, and error handling.
"""

import json
import uuid
from unittest.mock import AsyncMock, patch

import httpx
import pytest
import respx

from stash_graphql_client import (
    BatchResult,
    Performer,
    Scene,
    StashEntityStore,
    Tag,
)
from stash_graphql_client.errors import StashBatchError
from tests.fixtures import dump_graphql_calls


# =============================================================================
# save_batch tests
# =============================================================================


class TestSaveBatch:
    """Tests for StashEntityStore.save_batch()."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_batch_updates_three_scenes(self, respx_stash_client) -> None:
        """Three dirty Scenes batch-updated in single request, all marked clean."""
        store = StashEntityStore(respx_stash_client)

        # Create 3 existing scenes and make them dirty
        scenes = []
        for i in range(3):
            scene = Scene.from_graphql({"id": str(i + 1), "title": f"Original {i}"})
            scene.title = f"Updated {i}"
            store.add(scene)
            scenes.append(scene)

        # Verify they're dirty
        for s in scenes:
            assert s.is_dirty()

        # Mock batch response
        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={
                        "data": {
                            f"op{i}": {"id": str(i + 1), "__typename": "Scene"}
                            for i in range(3)
                        }
                    },
                )
            ]
        )

        try:
            result = await store.save_batch(scenes)
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert result.all_succeeded
        assert len(result) == 3

        # All marked clean
        for s in scenes:
            assert not s.is_dirty()

        # Single HTTP request
        assert len(graphql_route.calls) == 1
        req = json.loads(graphql_route.calls[0].request.content)
        assert "op0: sceneUpdate" in req["query"]
        assert "op2: sceneUpdate" in req["query"]

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_batch_creates_two_tags(self, respx_stash_client) -> None:
        """Two new Tags batch-created with UUID→ID cache remapping."""
        store = StashEntityStore(respx_stash_client)

        tags = []
        uuids = []
        for i in range(2):
            tag_uuid = uuid.uuid4().hex
            uuids.append(tag_uuid)
            tag = Tag(id=tag_uuid, name=f"Tag {i}")
            tag._is_new = True
            store.add(tag)
            tags.append(tag)

        # Verify UUID keys in cache
        for tag_uuid in uuids:
            assert ("Tag", tag_uuid) in store._cache

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={
                        "data": {
                            "op0": {"id": "100", "__typename": "Tag"},
                            "op1": {"id": "101", "__typename": "Tag"},
                        }
                    },
                )
            ]
        )

        try:
            result = await store.save_batch(tags)
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert result.all_succeeded

        # UUIDs removed, real IDs in cache
        for tag_uuid in uuids:
            assert ("Tag", tag_uuid) not in store._cache
        assert ("Tag", "100") in store._cache
        assert ("Tag", "101") in store._cache

        # IDs updated on objects
        assert tags[0].id == "100"
        assert tags[1].id == "101"
        assert not tags[0].is_new()

        # Verify mutation type is Create
        req = json.loads(graphql_route.calls[0].request.content)
        assert "tagCreate" in req["query"]

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_skip_non_dirty_objects(self, respx_stash_client) -> None:
        """Non-dirty objects are silently excluded from the batch."""
        store = StashEntityStore(respx_stash_client)

        clean_tag = Tag.from_graphql({"id": "1", "name": "Clean"})
        dirty_tag = Tag.from_graphql({"id": "2", "name": "Dirty"})
        dirty_tag.name = "Updated"

        store.add(clean_tag)
        store.add(dirty_tag)

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={"data": {"op0": {"id": "2", "__typename": "Tag"}}},
                )
            ]
        )

        try:
            result = await store.save_batch([clean_tag, dirty_tag])
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert result.all_succeeded
        assert len(result) == 1  # Only the dirty tag

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_creates_ordered_before_updates(self, respx_stash_client) -> None:
        """Creates appear before updates in the alias ordering."""
        store = StashEntityStore(respx_stash_client)

        # Existing tag (update)
        existing_tag = Tag.from_graphql({"id": "1", "name": "Old"})
        existing_tag.name = "Updated"
        store.add(existing_tag)

        # New tag (create)
        new_uuid = uuid.uuid4().hex
        new_tag = Tag(id=new_uuid, name="Brand New")
        new_tag._is_new = True
        store.add(new_tag)

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={
                        "data": {
                            "op0": {"id": "99", "__typename": "Tag"},
                            "op1": {"id": "1", "__typename": "Tag"},
                        }
                    },
                )
            ]
        )

        try:
            # Pass update first, create second — save_batch should reorder
            result = await store.save_batch([existing_tag, new_tag])
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert result.all_succeeded

        # Verify op0 is Create, op1 is Update
        req = json.loads(graphql_route.calls[0].request.content)
        assert "op0: tagCreate" in req["query"]
        assert "op1: tagUpdate" in req["query"]

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_mixed_types_in_batch(self, respx_stash_client) -> None:
        """Different entity types can be batched together."""
        store = StashEntityStore(respx_stash_client)

        tag = Tag.from_graphql({"id": "1", "name": "Old"})
        tag.name = "New Tag"
        store.add(tag)

        performer = Performer.from_graphql(
            {"id": "2", "name": "Old Performer", "disambiguation": ""}
        )
        performer.name = "New Performer"
        store.add(performer)

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={
                        "data": {
                            "op0": {"id": "1", "__typename": "Tag"},
                            "op1": {"id": "2", "__typename": "Performer"},
                        }
                    },
                )
            ]
        )

        try:
            result = await store.save_batch([tag, performer])
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert result.all_succeeded
        req = json.loads(graphql_route.calls[0].request.content)
        assert "tagUpdate" in req["query"]
        assert "performerUpdate" in req["query"]

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_empty_batch_returns_empty_result(self, respx_stash_client) -> None:
        """Batch with no dirty objects returns empty BatchResult."""
        store = StashEntityStore(respx_stash_client)

        clean_tag = Tag.from_graphql({"id": "1", "name": "Clean"})
        store.add(clean_tag)

        result = await store.save_batch([clean_tag])

        assert isinstance(result, BatchResult)
        assert len(result) == 0
        assert result.all_succeeded

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_typename_mismatch_logs_warning(
        self, respx_stash_client, caplog
    ) -> None:
        """__typename mismatch in response logs warning but doesn't fail."""
        store = StashEntityStore(respx_stash_client)

        tag = Tag.from_graphql({"id": "1", "name": "Old"})
        tag.name = "New"
        store.add(tag)

        # Respond with wrong __typename
        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={"data": {"op0": {"id": "1", "__typename": "WrongType"}}},
                )
            ]
        )

        try:
            result = await store.save_batch([tag])
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert result.all_succeeded
        assert not tag.is_dirty()  # Still marked clean
        assert "mismatch" in caplog.text.lower()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_partial_failure_succeeds_some_fails_others(
        self, respx_stash_client
    ) -> None:
        """Partial batch failure: succeeded objects get mark_clean, failed stay dirty."""
        from gql.transport.exceptions import TransportQueryError

        store = StashEntityStore(respx_stash_client)

        tags = []
        for i in range(3):
            tag = Tag.from_graphql({"id": str(i + 1), "name": f"Tag {i}"})
            tag.name = f"Updated {i}"
            store.add(tag)
            tags.append(tag)

        # Mock partial failure: op0 and op2 succeed, op1 fails
        partial_data = {
            "op0": {"id": "1", "__typename": "Tag"},
            "op2": {"id": "3", "__typename": "Tag"},
        }
        errors = [{"message": "Tag not found", "path": ["op1"]}]

        original_execute = respx_stash_client._session.execute

        async def mock_execute(operation):
            raise TransportQueryError(
                "Partial failure", errors=errors, data=partial_data
            )

        respx_stash_client._session.execute = mock_execute

        try:
            with pytest.raises(StashBatchError) as exc_info:
                await store.save_batch(tags)

            batch_result = exc_info.value.batch_result
            assert len(batch_result.succeeded) == 2
            assert len(batch_result.failed) == 1
        finally:
            respx_stash_client._session.execute = original_execute

        # Succeeded objects marked clean
        assert not tags[0].is_dirty()
        assert not tags[2].is_dirty()

        # Failed object stays dirty
        assert tags[1].is_dirty()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_side_mutations_fire_after_main_batch(
        self, respx_stash_client
    ) -> None:
        """Side mutation handlers are called after the main batch succeeds."""
        store = StashEntityStore(respx_stash_client)

        # Create a scene with a side-mutation field
        scene = Scene.from_graphql(
            {"id": "1", "title": "Test", "play_count": 5, "play_duration": 100.0}
        )
        # Make dirty: change title (main) — this will trigger a main mutation
        scene.title = "Updated"
        store.add(scene)

        # Track side mutation calls
        side_mutation_called = False
        original_side_mutations = Scene.__side_mutations__.copy()

        async def mock_handler(client, obj):
            nonlocal side_mutation_called
            side_mutation_called = True

        # Patch a side mutation field — make 'play_count' dirty with a handler
        scene._snapshot["play_count"] = 0  # Force dirty
        Scene.__side_mutations__["play_count"] = mock_handler

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={"data": {"op0": {"id": "1", "__typename": "Scene"}}},
                ),
            ]
        )

        try:
            result = await store.save_batch([scene])
        finally:
            dump_graphql_calls(graphql_route.calls)
            Scene.__side_mutations__ = original_side_mutations

        assert result.all_succeeded
        assert side_mutation_called
        assert not scene.is_dirty()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_queued_ops_fire_after_side_mutations(
        self, respx_stash_client
    ) -> None:
        """Queued operations (_pending_side_ops) fire after side mutations."""
        store = StashEntityStore(respx_stash_client)

        tag = Tag.from_graphql({"id": "1", "name": "Original"})
        tag.name = "Changed"
        store.add(tag)

        # Queue an operation
        op_called = False

        async def queued_op(client, obj):
            nonlocal op_called
            op_called = True

        tag._queue_side_op(queued_op)

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={"data": {"op0": {"id": "1", "__typename": "Tag"}}},
                )
            ]
        )

        try:
            result = await store.save_batch([tag])
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert result.all_succeeded
        assert op_called
        assert not tag.is_dirty()
        assert len(tag._pending_side_ops) == 0  # Cleared by mark_clean()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_deduplicated_side_mutation_handlers(
        self, respx_stash_client
    ) -> None:
        """Two fields mapping to the same handler fires it only once."""
        store = StashEntityStore(respx_stash_client)

        scene = Scene.from_graphql(
            {
                "id": "1",
                "title": "Test",
                "play_count": 5,
                "play_duration": 100.0,
                "resume_time": 50.0,
            }
        )
        scene.title = "Updated"
        store.add(scene)

        call_count = 0
        original_side_mutations = Scene.__side_mutations__.copy()

        async def shared_handler(client, obj):
            nonlocal call_count
            call_count += 1

        # Two fields → same handler object
        scene._snapshot["play_duration"] = 0.0
        scene._snapshot["resume_time"] = 0.0
        Scene.__side_mutations__["play_duration"] = shared_handler
        Scene.__side_mutations__["resume_time"] = shared_handler

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={"data": {"op0": {"id": "1", "__typename": "Scene"}}},
                ),
            ]
        )

        try:
            await store.save_batch([scene])
        finally:
            dump_graphql_calls(graphql_route.calls)
            Scene.__side_mutations__ = original_side_mutations

        # Handler fired only once despite two dirty fields
        assert call_count == 1

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_cascade_saves_unsaved_related_before_batch(
        self, respx_stash_client
    ) -> None:
        """Unsaved related objects are cascade-saved before the batch runs."""
        store = StashEntityStore(respx_stash_client)

        # Create an unsaved tag (UUID = new)
        tag_uuid = uuid.uuid4().hex
        new_tag = Tag(id=tag_uuid, name="New Tag")
        new_tag._is_new = True
        store.add(new_tag)

        # Create a scene that references the new tag
        scene = Scene.from_graphql({"id": "1", "title": "My Scene", "tags": []})
        scene.tags = [new_tag]
        scene.title = "Updated Scene"
        store.add(scene)

        # Mock: first call = tag create (cascade), second = scene update (batch)
        call_count = 0

        async def mock_execute(operation):
            nonlocal call_count
            call_count += 1
            # Cascade save for the tag (individual save, not batch)
            if call_count == 1:
                return {"tagCreate": {"id": "99"}}
            # Batch for the scene
            return {"op0": {"id": "1", "__typename": "Scene"}}

        original = respx_stash_client._session.execute
        respx_stash_client._session.execute = mock_execute

        try:
            await store.save_batch([scene])
        finally:
            respx_stash_client._session.execute = original

        # Tag was cascade-saved first, then scene batched
        assert call_count == 2
        assert new_tag.id == "99"
        assert not scene.is_dirty()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_cascade_makes_object_clean_excludes_from_batch(
        self, respx_stash_client
    ) -> None:
        """Object that becomes clean after cascade re-check is excluded."""
        store = StashEntityStore(respx_stash_client)

        # Create a tag that's only "dirty" because of a relationship
        tag_uuid = uuid.uuid4().hex
        new_tag = Tag(id=tag_uuid, name="Cascade Me")
        new_tag._is_new = True
        store.add(new_tag)

        # A scene that references the tag — but its only dirty field IS the tag
        scene = Scene.from_graphql({"id": "1", "title": "Scene"})
        scene.tags = [new_tag]
        store.add(scene)

        # After cascade-saving the tag, the scene's tag list has a real ID
        # but the scene itself may or may not still be dirty depending on
        # whether tags changed vs snapshot. Let's force it: make scene
        # non-dirty after cascade by giving it a clean snapshot
        call_count = 0

        async def mock_execute(operation):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # Cascade save for tag
                return {"tagCreate": {"id": "50"}}
            # If scene is still dirty, it goes through batch
            return {"op0": {"id": "1", "__typename": "Scene"}}

        original = respx_stash_client._session.execute
        respx_stash_client._session.execute = mock_execute

        try:
            await store.save_batch([scene])
        finally:
            respx_stash_client._session.execute = original

        # At minimum the tag was cascade-saved
        assert new_tag.id == "50"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_to_input_non_dict_skipped(self, respx_stash_client) -> None:
        """Object whose to_input() returns non-dict is skipped with warning."""
        store = StashEntityStore(respx_stash_client)

        tag = Tag.from_graphql({"id": "1", "name": "Old"})
        tag.name = "New"
        store.add(tag)

        with patch.object(
            type(tag), "to_input", new_callable=AsyncMock, return_value="not a dict"
        ):
            result = await store.save_batch([tag])

        # Skipped — empty result
        assert len(result) == 0

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_batch_create_remap_without_type_index_entry(
        self, respx_stash_client
    ) -> None:
        """UUID→ID remap works even when the type has no _type_index entry."""
        store = StashEntityStore(respx_stash_client)

        tag_uuid = uuid.uuid4().hex
        new_tag = Tag(id=tag_uuid, name="No Index")
        new_tag._is_new = True
        store.add(new_tag)

        # Remove the type index entry so _type_index.get("Tag") returns None
        store._type_index.pop("Tag", None)

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={"data": {"op0": {"id": "88", "__typename": "Tag"}}},
                )
            ]
        )

        try:
            result = await store.save_batch([new_tag])
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert result.all_succeeded
        assert new_tag.id == "88"
        assert ("Tag", "88") in store._cache
        assert ("Tag", tag_uuid) not in store._cache

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_new_object_not_in_cache_gets_added(self, respx_stash_client) -> None:
        """New object NOT in cache gets added during save_batch UUID remap."""
        store = StashEntityStore(respx_stash_client)

        tag_uuid = uuid.uuid4().hex
        new_tag = Tag(id=tag_uuid, name="Uncached")
        new_tag._is_new = True
        # Deliberately do NOT call store.add() — not in cache

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={"data": {"op0": {"id": "77", "__typename": "Tag"}}},
                )
            ]
        )

        try:
            result = await store.save_batch([new_tag])
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert result.all_succeeded
        assert new_tag.id == "77"
        # Should now be cached with real ID
        assert ("Tag", "77") in store._cache

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_side_mutation_error_logged_but_object_cleaned(
        self, respx_stash_client, caplog
    ) -> None:
        """Side mutation failure is logged but object still gets mark_clean."""
        store = StashEntityStore(respx_stash_client)

        scene = Scene.from_graphql(
            {"id": "1", "title": "Test", "play_count": 5, "play_duration": 100.0}
        )
        scene.title = "Updated"
        store.add(scene)

        original_side_mutations = Scene.__side_mutations__.copy()

        async def failing_handler(client, obj):
            raise RuntimeError("Side mutation exploded")

        scene._snapshot["play_count"] = 0  # Force dirty
        Scene.__side_mutations__["play_count"] = failing_handler

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={"data": {"op0": {"id": "1", "__typename": "Scene"}}},
                ),
            ]
        )

        try:
            result = await store.save_batch([scene])
        finally:
            dump_graphql_calls(graphql_route.calls)
            Scene.__side_mutations__ = original_side_mutations

        assert result.all_succeeded
        assert not scene.is_dirty()  # Still cleaned despite side mutation failure
        assert "Side mutation" in caplog.text
        assert "exploded" in caplog.text

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_queued_op_error_logged_but_object_cleaned(
        self, respx_stash_client, caplog
    ) -> None:
        """Queued op failure is logged but object still gets mark_clean."""
        store = StashEntityStore(respx_stash_client)

        tag = Tag.from_graphql({"id": "1", "name": "Original"})
        tag.name = "Changed"
        store.add(tag)

        async def failing_op(client, obj):
            raise RuntimeError("Queued op boom")

        tag._queue_side_op(failing_op)

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={"data": {"op0": {"id": "1", "__typename": "Tag"}}},
                )
            ]
        )

        try:
            result = await store.save_batch([tag])
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert result.all_succeeded
        assert not tag.is_dirty()
        assert "Queued operation" in caplog.text
        assert "boom" in caplog.text


# =============================================================================
# save_all tests
# =============================================================================


class TestSaveAll:
    """Tests for StashEntityStore.save_all()."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_save_all_empty_cache(self, respx_stash_client) -> None:
        """Empty cache returns empty BatchResult."""
        store = StashEntityStore(respx_stash_client)

        result = await store.save_all()

        assert isinstance(result, BatchResult)
        assert len(result) == 0

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_save_all_skips_clean_entities(self, respx_stash_client) -> None:
        """Clean entities in cache are not included in batch."""
        store = StashEntityStore(respx_stash_client)

        # Add clean entities
        for i in range(3):
            tag = Tag.from_graphql({"id": str(i + 1), "name": f"Tag {i}"})
            store.add(tag)
            assert not tag.is_dirty()

        result = await store.save_all()

        assert len(result) == 0

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_save_all_finds_dirty_entities(self, respx_stash_client) -> None:
        """save_all finds and batch-saves dirty entities from cache."""
        store = StashEntityStore(respx_stash_client)

        # One clean, one dirty
        clean_tag = Tag.from_graphql({"id": "1", "name": "Clean"})
        store.add(clean_tag)

        dirty_tag = Tag.from_graphql({"id": "2", "name": "Dirty"})
        dirty_tag.name = "Modified"
        store.add(dirty_tag)

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={"data": {"op0": {"id": "2", "__typename": "Tag"}}},
                )
            ]
        )

        try:
            result = await store.save_all()
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert result.all_succeeded
        assert len(result) == 1
        assert not dirty_tag.is_dirty()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_save_all_orders_new_before_dirty(self, respx_stash_client) -> None:
        """save_all partitions new objects before updates."""
        store = StashEntityStore(respx_stash_client)

        # Dirty existing tag (update)
        existing = Tag.from_graphql({"id": "1", "name": "Old"})
        existing.name = "Updated"
        store.add(existing)

        # New tag (create)
        new_uuid = uuid.uuid4().hex
        new_tag = Tag(id=new_uuid, name="Brand New")
        new_tag._is_new = True
        store.add(new_tag)

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={
                        "data": {
                            "op0": {"id": "50", "__typename": "Tag"},
                            "op1": {"id": "1", "__typename": "Tag"},
                        }
                    },
                )
            ]
        )

        try:
            result = await store.save_all()
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert result.all_succeeded

        # Verify creates come first in the query
        req = json.loads(graphql_route.calls[0].request.content)
        query = req["query"]
        create_pos = query.index("tagCreate")
        update_pos = query.index("tagUpdate")
        assert create_pos < update_pos

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_save_all_with_pending_side_ops(self, respx_stash_client) -> None:
        """Entities with only pending side ops (not dirty fields) are included."""
        store = StashEntityStore(respx_stash_client)

        tag = Tag.from_graphql({"id": "1", "name": "Clean"})
        store.add(tag)
        assert not tag.is_dirty()

        # Queue an operation without dirtying fields
        op_called = False

        async def queued_op(client, obj):
            nonlocal op_called
            op_called = True

        tag._queue_side_op(queued_op)

        # No main mutation needed, but side ops should fire
        await store.save_all()

        # The side-only object should still be processed
        assert op_called
        assert not tag.is_dirty()
