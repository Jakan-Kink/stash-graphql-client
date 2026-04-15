"""Tests for __side_mutations__ and _pending_side_ops support.

Tests cover:
- Field-based side mutations (Gallery.cover, Gallery.images, Scene activity/play/o, Image o_counter)
- Queued side operations (_pending_side_ops)
- Handler deduplication for multi-field → single handler
- Edge cases (failure recovery, new object ID preservation)
- Bulk relationship handlers (Performer, Studio, Tag)
- Batch-size limiting for large relationship sets
- Bidirectional sync for fixed relationships
- Scene.groups serialization via __relationships__
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest
import respx

from stash_graphql_client.types.base import StashObject
from stash_graphql_client.types.gallery import Gallery
from stash_graphql_client.types.group import Group
from stash_graphql_client.types.image import Image
from stash_graphql_client.types.performer import Performer
from stash_graphql_client.types.scene import Scene, SceneGroupInput
from stash_graphql_client.types.studio import Studio
from stash_graphql_client.types.tag import Tag
from tests.fixtures import (
    create_gallery_dict,
    create_graphql_response,
    dump_graphql_calls,
)


class TestSideMutations:
    """Test __side_mutations__ support in save() and to_input()."""

    # ── Dirty tracking integration ─────────────────────────────────

    def test_cover_tracked_in_gallery(self, respx_entity_store) -> None:
        """Cover field is in Gallery.__tracked_fields__."""
        assert "cover" in Gallery.__tracked_fields__

    def test_cover_is_side_mutation(self) -> None:
        """Cover field is registered as a side mutation."""
        assert "cover" in Gallery.__side_mutations__

    def test_setting_cover_makes_gallery_dirty(self, respx_entity_store) -> None:
        """Changing cover marks the gallery as dirty."""
        gallery = Gallery.from_graphql(
            create_gallery_dict(id="100", title="Test", cover=None)
        )
        gallery.mark_clean()
        assert not gallery.is_dirty()

        # Set cover to an image
        gallery.cover = Image(id="200")
        assert gallery.is_dirty()
        assert "cover" in gallery.get_changed_fields()

    def test_clearing_cover_makes_gallery_dirty(self, respx_entity_store) -> None:
        """Setting cover to None (reset) marks the gallery as dirty."""
        gallery = Gallery.from_graphql(
            create_gallery_dict(
                id="101", title="Test", cover={"id": "200", "__typename": "Image"}
            )
        )
        gallery.mark_clean()
        assert not gallery.is_dirty()

        gallery.cover = None
        assert gallery.is_dirty()

    # ── to_input() exclusion ───────────────────────────────────────

    @pytest.mark.asyncio
    async def test_to_input_excludes_cover_for_dirty_existing(
        self, respx_entity_store
    ) -> None:
        """to_input() should NOT include cover in the update input dict."""
        gallery = Gallery.from_graphql(
            create_gallery_dict(id="102", title="Test", cover=None)
        )
        gallery.mark_clean()

        # Make cover dirty AND a regular field dirty
        gallery.cover = Image(id="200")
        gallery.title = "Updated"

        input_data = await gallery.to_input()

        # title should be in the input, cover should NOT
        assert "title" in input_data
        assert "cover" not in input_data
        assert "cover_image_id" not in input_data

    @pytest.mark.asyncio
    async def test_to_input_excludes_cover_for_new_object(
        self, respx_entity_store
    ) -> None:
        """to_input() for a new Gallery should also exclude cover."""
        gallery = Gallery(title="New Gallery")
        gallery.cover = Image(id="200")

        input_data = await gallery.to_input()

        assert "title" in input_data
        assert "cover" not in input_data

    # ── save() fires side mutation ─────────────────────────────────

    @pytest.mark.asyncio
    async def test_save_fires_set_cover_mutation(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """save() should fire setGalleryCover when cover is set to an Image."""
        gallery = Gallery.from_graphql(
            create_gallery_dict(id="103", title="Test", cover=None)
        )
        gallery.mark_clean()

        # Set cover
        gallery.cover = Image(id="202")

        # Mock: main update (only-id, skipped) + setGalleryCover
        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                # setGalleryCover response
                httpx.Response(
                    200, json=create_graphql_response("setGalleryCover", True)
                ),
            ]
        )

        try:
            await gallery.save(respx_stash_client)
        finally:
            dump_graphql_calls(graphql_route.calls)

        # Only one call: setGalleryCover (main mutation skipped — no non-side fields dirty)
        assert len(graphql_route.calls) == 1
        req = json.loads(graphql_route.calls[0].request.content)
        assert "setGalleryCover" in req["query"]
        assert req["variables"]["input"]["gallery_id"] == "103"
        assert req["variables"]["input"]["cover_image_id"] == "202"

        # Object should be clean after save
        assert not gallery.is_dirty()

    @pytest.mark.asyncio
    async def test_save_fires_reset_cover_mutation(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """save() should fire resetGalleryCover when cover is set to None."""
        gallery = Gallery.from_graphql(
            create_gallery_dict(
                id="104", title="Test", cover={"id": "200", "__typename": "Image"}
            )
        )
        gallery.mark_clean()

        # Reset cover
        gallery.cover = None

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200, json=create_graphql_response("resetGalleryCover", True)
                ),
            ]
        )

        try:
            await gallery.save(respx_stash_client)
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert len(graphql_route.calls) == 1
        req = json.loads(graphql_route.calls[0].request.content)
        assert "resetGalleryCover" in req["query"]
        assert req["variables"]["input"]["gallery_id"] == "104"

        assert not gallery.is_dirty()

    @pytest.mark.asyncio
    async def test_save_fires_both_main_and_side_mutations(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """When both regular fields and cover are dirty, both mutations fire."""
        gallery = Gallery.from_graphql(
            create_gallery_dict(id="105", title="Old Title", cover=None)
        )
        gallery.mark_clean()

        gallery.title = "New Title"
        gallery.cover = Image(id="203")

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                # Main galleryUpdate
                httpx.Response(
                    200,
                    json=create_graphql_response("galleryUpdate", {"id": "105"}),
                ),
                # setGalleryCover
                httpx.Response(
                    200, json=create_graphql_response("setGalleryCover", True)
                ),
            ]
        )

        try:
            await gallery.save(respx_stash_client)
        finally:
            dump_graphql_calls(graphql_route.calls)

        # Two calls: main update + side mutation
        assert len(graphql_route.calls) == 2

        # First call: galleryUpdate with title, no cover
        req1 = json.loads(graphql_route.calls[0].request.content)
        assert "galleryUpdate" in req1["query"]
        assert req1["variables"]["input"]["title"] == "New Title"
        assert "cover" not in req1["variables"]["input"]

        # Second call: setGalleryCover
        req2 = json.loads(graphql_route.calls[1].request.content)
        assert "setGalleryCover" in req2["query"]
        assert req2["variables"]["input"]["cover_image_id"] == "203"

        assert not gallery.is_dirty()

    # ── New object edge case ───────────────────────────────────────

    @pytest.mark.asyncio
    async def test_save_new_gallery_fires_side_mutation_after_create(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """For new galleries, side mutations fire AFTER create (using real ID)."""
        gallery = Gallery(title="Brand New")
        gallery.cover = Image(id="204")
        assert gallery.is_new()

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                # galleryCreate returns real server ID
                httpx.Response(
                    200,
                    json=create_graphql_response("galleryCreate", {"id": "500"}),
                ),
                # setGalleryCover uses the real ID
                httpx.Response(
                    200, json=create_graphql_response("setGalleryCover", True)
                ),
            ]
        )

        try:
            await gallery.save(respx_stash_client)
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert len(graphql_route.calls) == 2

        # Create mutation
        req1 = json.loads(graphql_route.calls[0].request.content)
        assert "galleryCreate" in req1["query"]
        assert "cover" not in req1["variables"]["input"]

        # Side mutation uses real server ID, not UUID
        req2 = json.loads(graphql_route.calls[1].request.content)
        assert "setGalleryCover" in req2["query"]
        assert req2["variables"]["input"]["gallery_id"] == "500"

        assert gallery.id == "500"
        assert not gallery.is_new()
        assert not gallery.is_dirty()

    # ── No side mutations by default ───────────────────────────────

    def test_stash_object_has_empty_side_mutations(self) -> None:
        """Base StashObject has no side mutations by default."""
        assert StashObject.__side_mutations__ == {}

    def test_tag_has_side_mutations(self) -> None:
        """Tag has side mutations for all content types."""
        assert set(Tag.__side_mutations__.keys()) == {
            "scenes",
            "images",
            "galleries",
            "performers",
            "groups",
            "scene_markers",
        }

    @pytest.mark.asyncio
    async def test_save_without_side_mutations_unchanged(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """save() for entities without side mutations works as before."""
        tag = Tag.new(name="Plain Tag")

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            return_value=httpx.Response(
                200,
                json=create_graphql_response(
                    "tagCreate", {"id": "400", "name": "Plain Tag"}
                ),
            )
        )

        try:
            await tag.save(respx_stash_client)
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert len(graphql_route.calls) == 1
        assert tag.id == "400"
        assert not tag.is_dirty()

    # ── Queued side operations ─────────────────────────────────────

    @pytest.mark.asyncio
    async def test_queue_side_op_prevents_save_skip(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """save() should NOT skip when _pending_side_ops is non-empty."""
        tag = Tag.from_graphql({"id": "400", "name": "Test"})
        tag.mark_clean()
        assert not tag.is_dirty()
        assert not tag.is_new()

        # Queue an op
        called = False

        async def _op(client, obj):
            nonlocal called
            called = True

        tag._queue_side_op(_op)

        # save() should fire the op even though tag is not dirty
        await tag.save(respx_stash_client)
        assert called

    @pytest.mark.asyncio
    async def test_queued_ops_fire_after_main_mutation(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """Queued ops fire AFTER the main mutation."""
        gallery = Gallery.from_graphql(create_gallery_dict(id="100", title="Test"))
        gallery.mark_clean()
        gallery.title = "Updated"

        call_order = []

        async def _op(client, obj):
            call_order.append("queued_op")

        gallery._queue_side_op(_op)

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json=create_graphql_response("galleryUpdate", {"id": "100"}),
                ),
            ]
        )

        try:
            # Intercept to track main mutation order
            original_execute = respx_stash_client.execute

            async def tracking_execute(query, variables=None):
                call_order.append("main_mutation")
                return await original_execute(query, variables)

            with patch.object(
                respx_stash_client, "execute", side_effect=tracking_execute
            ):
                await gallery.save(respx_stash_client)
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert call_order == ["main_mutation", "queued_op"]

    @pytest.mark.asyncio
    async def test_queued_ops_cleared_after_save(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """Queue is empty after successful save."""
        tag = Tag.from_graphql({"id": "400", "name": "Test"})
        tag.mark_clean()

        tag._queue_side_op(AsyncMock())
        assert len(tag._pending_side_ops) == 1

        await tag.save(respx_stash_client)
        assert len(tag._pending_side_ops) == 0

    def test_queued_ops_cleared_on_mark_clean(self, respx_entity_store) -> None:
        """mark_clean() also clears the queue."""
        tag = Tag.from_graphql({"id": "400", "name": "Test"})
        tag._queue_side_op(AsyncMock())
        assert len(tag._pending_side_ops) == 1

        tag.mark_clean()
        assert len(tag._pending_side_ops) == 0

    @pytest.mark.asyncio
    async def test_field_and_queued_side_mutations_both_fire(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """When both cover (field-based) and a queued op exist, both fire."""
        gallery = Gallery.from_graphql(
            create_gallery_dict(id="100", title="Test", cover=None)
        )
        gallery.mark_clean()

        # Field-based side mutation
        gallery.cover = Image(id="200")

        # Queued op
        queued_called = False

        async def _op(client, obj):
            nonlocal queued_called
            queued_called = True

        gallery._queue_side_op(_op)

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200, json=create_graphql_response("setGalleryCover", True)
                ),
            ]
        )

        try:
            await gallery.save(respx_stash_client)
        finally:
            dump_graphql_calls(graphql_route.calls)

        # setGalleryCover fired
        assert len(graphql_route.calls) == 1
        req = json.loads(graphql_route.calls[0].request.content)
        assert "setGalleryCover" in req["query"]

        # Queued op also fired
        assert queued_called

    @pytest.mark.asyncio
    async def test_side_mutation_failure_leaves_object_dirty(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """If side mutation fails, object stays dirty (mark_clean not reached)."""
        gallery = Gallery.from_graphql(
            create_gallery_dict(id="100", title="Test", cover=None)
        )
        gallery.mark_clean()
        gallery.cover = Image(id="200")

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=Exception("Network error")
        )

        try:
            with pytest.raises(ValueError, match="Failed to save"):
                await gallery.save(respx_stash_client)
        finally:
            dump_graphql_calls(graphql_route.calls)

        # Object should still be dirty
        assert gallery.is_dirty()

    @pytest.mark.asyncio
    async def test_side_mutation_failure_preserves_server_id(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """If create succeeds but side mutation fails, server ID is kept."""
        gallery = Gallery(title="New")
        gallery.cover = Image(id="200")
        assert gallery.is_new()

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                # Create succeeds
                httpx.Response(
                    200,
                    json=create_graphql_response("galleryCreate", {"id": "501"}),
                ),
                # Side mutation fails
                Exception("Cover mutation failed"),
            ]
        )

        try:
            with pytest.raises(ValueError, match="Failed to save"):
                await gallery.save(respx_stash_client)
        finally:
            dump_graphql_calls(graphql_route.calls)

        # Server ID is preserved even though save failed overall
        assert gallery.id == "501"
        assert not gallery.is_new()

    # ── Handler deduplication ──────────────────────────────────────

    @pytest.mark.asyncio
    async def test_side_mutation_handler_deduplication(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """Multi-field side mutations sharing a handler fire only once."""
        scene = Scene.from_graphql(
            {"id": "300", "title": "Test", "resume_time": 10.0, "play_duration": 100.0}
        )
        scene.mark_clean()

        # Dirty both fields that share _save_activity handler
        scene.resume_time = 20.0
        scene.play_duration = 200.0
        assert "resume_time" in scene.get_changed_fields()
        assert "play_duration" in scene.get_changed_fields()

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json=create_graphql_response("sceneSaveActivity", True),
                ),
            ]
        )

        try:
            await scene.save(respx_stash_client)
        finally:
            dump_graphql_calls(graphql_route.calls)

        # Only ONE sceneSaveActivity call despite two dirty fields
        assert len(graphql_route.calls) == 1
        req = json.loads(graphql_route.calls[0].request.content)
        assert "sceneSaveActivity" in req["query"]

    # ── Gallery.images side mutation ───────────────────────────────

    @pytest.mark.asyncio
    async def test_images_diff_fires_add_mutation(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """Adding images to gallery fires addGalleryImages."""
        gallery = Gallery.from_graphql(create_gallery_dict(id="100", title="Test"))
        gallery.images = []
        gallery.mark_clean()

        gallery.images.append(Image(id="200"))
        gallery.images.append(Image(id="201"))

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200, json=create_graphql_response("addGalleryImages", True)
                ),
            ]
        )

        try:
            await gallery.save(respx_stash_client)
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert len(graphql_route.calls) == 1
        req = json.loads(graphql_route.calls[0].request.content)
        assert "addGalleryImages" in req["query"]
        assert req["variables"]["input"]["gallery_id"] == "100"
        assert set(req["variables"]["input"]["image_ids"]) == {"200", "201"}

    @pytest.mark.asyncio
    async def test_images_diff_fires_remove_mutation(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """Removing images from gallery fires removeGalleryImages."""
        img1 = Image(id="200")
        gallery = Gallery.from_graphql(create_gallery_dict(id="101", title="Test"))
        gallery.images = [img1]
        gallery.mark_clean()

        gallery.images.remove(img1)

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200, json=create_graphql_response("removeGalleryImages", True)
                ),
            ]
        )

        try:
            await gallery.save(respx_stash_client)
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert len(graphql_route.calls) == 1
        req = json.loads(graphql_route.calls[0].request.content)
        assert "removeGalleryImages" in req["query"]
        assert req["variables"]["input"]["image_ids"] == ["200"]

    @pytest.mark.asyncio
    async def test_images_both_add_and_remove(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """Adding and removing images fires both mutations."""
        img_keep = Image(id="220")
        img_remove = Image(id="221")
        gallery = Gallery.from_graphql(create_gallery_dict(id="102", title="Test"))
        gallery.images = [img_keep, img_remove]
        gallery.mark_clean()

        gallery.images.remove(img_remove)
        gallery.images.append(Image(id="222"))

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200, json=create_graphql_response("addGalleryImages", True)
                ),
                httpx.Response(
                    200,
                    json=create_graphql_response("removeGalleryImages", True),
                ),
            ]
        )

        try:
            await gallery.save(respx_stash_client)
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert len(graphql_route.calls) == 2

    # ── Image.o_counter side mutation ──────────────────────────────

    @pytest.mark.asyncio
    async def test_o_counter_increment_fires_mutation(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """Incrementing o_counter fires imageIncrementO."""
        image = Image.from_graphql({"id": "207", "o_counter": 2, "organized": False})
        image.mark_clean()
        image.o_counter = 4  # delta = +2

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(200, json=create_graphql_response("imageIncrementO", 3)),
                httpx.Response(200, json=create_graphql_response("imageIncrementO", 4)),
            ]
        )

        try:
            await image.save(respx_stash_client)
        finally:
            dump_graphql_calls(graphql_route.calls)

        # Two increment calls for delta of 2
        assert len(graphql_route.calls) == 2
        assert image.o_counter == 4

    @pytest.mark.asyncio
    async def test_o_counter_reset_fires_mutation(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """Setting o_counter to 0 fires imageResetO."""
        image = Image.from_graphql({"id": "208", "o_counter": 5, "organized": False})
        image.mark_clean()
        image.o_counter = 0

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(200, json=create_graphql_response("imageResetO", 0)),
            ]
        )

        try:
            await image.save(respx_stash_client)
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert len(graphql_route.calls) == 1
        req = json.loads(graphql_route.calls[0].request.content)
        assert "imageResetO" in req["query"]
        assert image.o_counter == 0

    # ── Scene queued operations ────────────────────────────────────

    @pytest.mark.asyncio
    async def test_scene_reset_play_count_queues_and_fires(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """reset_play_count() queues op that fires sceneResetPlayCount."""
        scene = Scene.from_graphql({"id": "300", "title": "Test", "play_count": 5})
        scene.mark_clean()
        scene.reset_play_count()

        assert len(scene._pending_side_ops) == 1

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json=create_graphql_response("sceneResetPlayCount", 0),
                ),
            ]
        )

        try:
            await scene.save(respx_stash_client)
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert len(graphql_route.calls) == 1
        req = json.loads(graphql_route.calls[0].request.content)
        assert "sceneResetPlayCount" in req["query"]
        assert scene.play_count == 0

    # ── Scene._save_o (o_history diff) ─────────────────────────────

    @pytest.mark.asyncio
    async def test_save_o_add_history_entries(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """Adding o_history entries fires sceneAddO."""
        scene = Scene.from_graphql(
            {"id": "300", "title": "T", "o_history": ["2026-01-01T00:00:00Z"]}
        )
        scene.mark_clean()
        scene.o_history.append("2026-02-01T00:00:00Z")

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json=create_graphql_response(
                        "sceneAddO",
                        {
                            "count": 2,
                            "history": [
                                "2026-01-01T00:00:00Z",
                                "2026-02-01T00:00:00Z",
                            ],
                        },
                    ),
                ),
            ]
        )

        try:
            await scene.save(respx_stash_client)
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert len(graphql_route.calls) == 1
        req = json.loads(graphql_route.calls[0].request.content)
        assert "sceneAddO" in req["query"]
        assert scene.o_counter == 2

    @pytest.mark.asyncio
    async def test_save_o_remove_history_entries(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """Removing o_history entries fires sceneDeleteO."""
        scene = Scene.from_graphql(
            {
                "id": "301",
                "title": "T",
                "o_history": ["2026-01-01T00:00:00Z", "2026-02-01T00:00:00Z"],
                "o_counter": 2,
            }
        )
        scene.mark_clean()
        # Time scalar converts strings to datetime, so pop by index
        scene.o_history.pop(1)

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json=create_graphql_response(
                        "sceneDeleteO",
                        {"count": 1, "history": ["2026-01-01T00:00:00Z"]},
                    ),
                ),
            ]
        )

        try:
            await scene.save(respx_stash_client)
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert len(graphql_route.calls) == 1
        req = json.loads(graphql_route.calls[0].request.content)
        assert "sceneDeleteO" in req["query"]
        assert scene.o_counter == 1

    # ── Scene._save_play (play_history diff) ───────────────────────

    @pytest.mark.asyncio
    async def test_save_play_add_history_entries(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """Adding play_history entries fires sceneAddPlay."""
        scene = Scene.from_graphql(
            {"id": "302", "title": "T", "play_history": [], "play_count": 0}
        )
        scene.mark_clean()
        scene.play_history.append("2026-03-01T12:00:00Z")

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json=create_graphql_response(
                        "sceneAddPlay",
                        {"count": 1, "history": ["2026-03-01T12:00:00Z"]},
                    ),
                ),
            ]
        )

        try:
            await scene.save(respx_stash_client)
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert len(graphql_route.calls) == 1
        req = json.loads(graphql_route.calls[0].request.content)
        assert "sceneAddPlay" in req["query"]
        assert scene.play_count == 1

    @pytest.mark.asyncio
    async def test_save_play_remove_history_entries(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """Removing play_history entries fires sceneDeletePlay."""
        scene = Scene.from_graphql(
            {
                "id": "303",
                "title": "T",
                "play_history": ["2026-01-01T00:00:00Z"],
                "play_count": 1,
            }
        )
        scene.mark_clean()
        # Time scalar converts strings to datetime, so pop by index
        scene.play_history.pop(0)

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json=create_graphql_response(
                        "sceneDeletePlay", {"count": 0, "history": []}
                    ),
                ),
            ]
        )

        try:
            await scene.save(respx_stash_client)
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert len(graphql_route.calls) == 1
        assert scene.play_count == 0

    # ── Scene queued ops: reset_o, reset_activity, generate_screenshot ──

    @pytest.mark.asyncio
    async def test_scene_reset_o_queues_and_fires(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """reset_o() queues op that fires sceneResetO."""
        scene = Scene.from_graphql({"id": "304", "title": "T", "o_counter": 3})
        scene.mark_clean()
        scene.reset_o()

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(200, json=create_graphql_response("sceneResetO", 0)),
            ]
        )

        try:
            await scene.save(respx_stash_client)
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert len(graphql_route.calls) == 1
        assert scene.o_counter == 0
        assert scene.o_history == []

    @pytest.mark.asyncio
    async def test_scene_reset_activity_queues_and_fires(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """reset_activity() queues op that fires sceneResetActivity."""
        scene = Scene.from_graphql(
            {
                "id": "305",
                "title": "T",
                "resume_time": 42.5,
                "play_duration": 120.0,
            }
        )
        scene.mark_clean()
        scene.reset_activity(reset_resume=True, reset_duration=True)

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json=create_graphql_response("sceneResetActivity", True),
                ),
            ]
        )

        try:
            await scene.save(respx_stash_client)
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert len(graphql_route.calls) == 1
        req = json.loads(graphql_route.calls[0].request.content)
        assert "sceneResetActivity" in req["query"]
        assert scene.resume_time is None
        assert scene.play_duration is None

    @pytest.mark.asyncio
    async def test_scene_generate_screenshot_queues_and_fires(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """generate_screenshot() queues op that fires sceneGenerateScreenshot."""
        scene = Scene.from_graphql({"id": "306", "title": "T"})
        scene.mark_clean()
        scene.generate_screenshot(at=30.5)

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json=create_graphql_response(
                        "sceneGenerateScreenshot", "/path/to/screenshot.jpg"
                    ),
                ),
            ]
        )

        try:
            await scene.save(respx_stash_client)
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert len(graphql_route.calls) == 1
        req = json.loads(graphql_route.calls[0].request.content)
        assert "sceneGenerateScreenshot" in req["query"]
        assert req["variables"]["at"] == 30.5

    # ── Image._save_o_counter edge cases ───────────────────────────

    @pytest.mark.asyncio
    async def test_o_counter_decrement_fires_mutation(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """Decrementing o_counter fires imageDecrementO."""
        image = Image.from_graphql({"id": "209", "o_counter": 5, "organized": False})
        image.mark_clean()
        image.o_counter = 3  # delta = -2

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(200, json=create_graphql_response("imageDecrementO", 4)),
                httpx.Response(200, json=create_graphql_response("imageDecrementO", 3)),
            ]
        )

        try:
            await image.save(respx_stash_client)
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert len(graphql_route.calls) == 2
        assert image.o_counter == 3

    @pytest.mark.asyncio
    async def test_o_counter_non_int_snapshot_treated_as_zero(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """Non-int snapshot (e.g., UNSET) is treated as 0."""
        image = Image.from_graphql({"id": "210", "organized": False})
        # o_counter is UNSET, snapshot is also UNSET
        image.mark_clean()
        image.o_counter = 2  # delta from 0 → 2

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(200, json=create_graphql_response("imageIncrementO", 1)),
                httpx.Response(200, json=create_graphql_response("imageIncrementO", 2)),
            ]
        )

        try:
            await image.save(respx_stash_client)
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert len(graphql_route.calls) == 2
        assert image.o_counter == 2

    @pytest.mark.asyncio
    async def test_o_counter_non_int_current_treated_as_zero(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """Non-int current value (e.g., None) treated as 0 → fires reset."""
        image = Image.from_graphql({"id": "211", "o_counter": 3, "organized": False})
        image.mark_clean()
        image.o_counter = None  # non-int current → treated as 0, snapshot=3 → reset

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(200, json=create_graphql_response("imageResetO", 0)),
            ]
        )

        try:
            await image.save(respx_stash_client)
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert len(graphql_route.calls) == 1
        req = json.loads(graphql_route.calls[0].request.content)
        assert "imageResetO" in req["query"]
        assert image.o_counter == 0

    # ── Gallery.add_image / remove_image convenience methods ───────

    @pytest.mark.asyncio
    async def test_gallery_add_image_convenience(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """add_image() adds to images list and can be saved."""
        gallery = Gallery.from_graphql(create_gallery_dict(id="106", title="Test"))
        gallery.images = []
        gallery.mark_clean()

        img = Image(id="205")
        img.galleries = []  # Pre-set to avoid store.populate() for inverse
        await gallery.add_image(img)

        assert img in gallery.images
        assert gallery.is_dirty()

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200, json=create_graphql_response("addGalleryImages", True)
                ),
            ]
        )

        try:
            await gallery.save(respx_stash_client)
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert len(graphql_route.calls) == 1

    @pytest.mark.asyncio
    async def test_gallery_remove_image_convenience(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """remove_image() removes from images list and can be saved."""
        img = Image(id="206")
        img.galleries = []  # Pre-set to avoid store.populate() for inverse
        gallery = Gallery.from_graphql(create_gallery_dict(id="107", title="Test"))
        gallery.images = [img]
        gallery.mark_clean()

        await gallery.remove_image(img)

        assert img not in gallery.images
        assert gallery.is_dirty()

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json=create_graphql_response("removeGalleryImages", True),
                ),
            ]
        )

        try:
            await gallery.save(respx_stash_client)
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert len(graphql_route.calls) == 1

    # ── Branch coverage: delta == 0 and partial reset flags ────────

    @pytest.mark.asyncio
    async def test_o_counter_no_delta_no_mutation(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """When o_counter delta is 0, handler is a no-op."""
        image = Image.from_graphql({"id": "212", "o_counter": 3, "organized": False})
        image.mark_clean()
        # Call handler directly with unchanged value to cover elif->exit branch
        await Image._save_o_counter(respx_stash_client, image)
        assert image.o_counter == 3

    @pytest.mark.asyncio
    async def test_scene_reset_activity_resume_only(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """reset_activity(reset_resume=True, reset_duration=False) only resets resume."""
        scene = Scene.from_graphql(
            {
                "id": "307",
                "title": "T",
                "resume_time": 42.5,
                "play_duration": 120.0,
            }
        )
        scene.mark_clean()
        scene.reset_activity(reset_resume=True, reset_duration=False)

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json=create_graphql_response("sceneResetActivity", True),
                ),
            ]
        )

        try:
            await scene.save(respx_stash_client)
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert scene.resume_time is None
        assert scene.play_duration == 120.0

    @pytest.mark.asyncio
    async def test_scene_reset_activity_duration_only(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """reset_activity(reset_resume=False, reset_duration=True) only resets duration."""
        scene = Scene.from_graphql(
            {
                "id": "308",
                "title": "T",
                "resume_time": 42.5,
                "play_duration": 120.0,
            }
        )
        scene.mark_clean()
        scene.reset_activity(reset_resume=False, reset_duration=True)

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json=create_graphql_response("sceneResetActivity", True),
                ),
            ]
        )

        try:
            await scene.save(respx_stash_client)
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert scene.resume_time == 42.5
        assert scene.play_duration is None


class TestBulkRelationshipHandler:
    """Tests for _make_bulk_relationship_handler and bulk-update side mutations."""

    # ── Metadata registration ────────────────────────────────────────

    def test_performer_has_side_mutations(self) -> None:
        """Performer has side mutations for scenes, galleries, images."""
        assert set(Performer.__side_mutations__.keys()) == {
            "scenes",
            "galleries",
            "images",
        }

    def test_studio_has_side_mutations(self) -> None:
        """Studio has side mutations for scenes, images, galleries, groups."""
        assert set(Studio.__side_mutations__.keys()) == {
            "scenes",
            "images",
            "galleries",
            "groups",
        }

    def test_performer_groups_not_in_side_mutations(self) -> None:
        """Performer.groups is read-only (derived via scenes), not a side mutation."""
        assert "groups" not in Performer.__side_mutations__

    def test_performer_groups_in_relationships(self) -> None:
        """Performer.groups has RelationshipMetadata for queryability."""
        from stash_graphql_client.types.base import RelationshipMetadata

        rel = Performer.__relationships__["groups"]
        assert isinstance(rel, RelationshipMetadata)
        assert rel.target_field == ""  # Read-only
        assert rel.query_strategy == "filter_query"

    # ── Performer.scenes side mutation (BulkUpdateIds pattern) ───────

    @pytest.mark.asyncio
    async def test_performer_add_scenes_fires_bulk_update(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """Adding scenes to performer fires bulkSceneUpdate with ADD mode."""
        performer = Performer.from_graphql({"id": "1001", "name": "Test"})
        performer.scenes = []
        performer.mark_clean()

        performer.scenes.append(Scene(id="2001"))
        performer.scenes.append(Scene(id="2002"))

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json=create_graphql_response(
                        "bulkSceneUpdate",
                        [{"id": "2001"}, {"id": "2002"}],
                    ),
                ),
            ]
        )

        try:
            await performer.save(respx_stash_client)
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert len(graphql_route.calls) == 1
        req = json.loads(graphql_route.calls[0].request.content)
        assert "bulkSceneUpdate" in req["query"]
        assert set(req["variables"]["input"]["ids"]) == {"2001", "2002"}
        assert req["variables"]["input"]["performer_ids"]["mode"] == "ADD"
        assert req["variables"]["input"]["performer_ids"]["ids"] == ["1001"]

    @pytest.mark.asyncio
    async def test_performer_remove_scenes_fires_bulk_update(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """Removing scenes from performer fires bulkSceneUpdate with REMOVE mode."""
        s1 = Scene(id="2001")
        performer = Performer.from_graphql({"id": "1001", "name": "Test"})
        performer.scenes = [s1]
        performer.mark_clean()

        performer.scenes.remove(s1)

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json=create_graphql_response("bulkSceneUpdate", [{"id": "2001"}]),
                ),
            ]
        )

        try:
            await performer.save(respx_stash_client)
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert len(graphql_route.calls) == 1
        req = json.loads(graphql_route.calls[0].request.content)
        assert req["variables"]["input"]["performer_ids"]["mode"] == "REMOVE"
        assert req["variables"]["input"]["performer_ids"]["ids"] == ["1001"]

    # ── Studio.scenes side mutation (scalar FK pattern) ──────────────

    @pytest.mark.asyncio
    async def test_studio_add_scenes_fires_bulk_update(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """Adding scenes to studio fires bulkSceneUpdate with studio_id set."""
        studio = Studio.from_graphql({"id": "3001", "name": "Acme"})
        studio.scenes = []
        studio.mark_clean()

        studio.scenes.append(Scene(id="2001"))

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json=create_graphql_response("bulkSceneUpdate", [{"id": "2001"}]),
                ),
            ]
        )

        try:
            await studio.save(respx_stash_client)
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert len(graphql_route.calls) == 1
        req = json.loads(graphql_route.calls[0].request.content)
        assert "bulkSceneUpdate" in req["query"]
        assert req["variables"]["input"]["ids"] == ["2001"]
        assert req["variables"]["input"]["studio_id"] == "3001"

    @pytest.mark.asyncio
    async def test_studio_remove_scenes_clears_studio_id(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """Removing scenes from studio fires bulkSceneUpdate with studio_id=null."""
        s1 = Scene(id="2001")
        studio = Studio.from_graphql({"id": "3001", "name": "Acme"})
        studio.scenes = [s1]
        studio.mark_clean()

        studio.scenes.remove(s1)

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json=create_graphql_response("bulkSceneUpdate", [{"id": "2001"}]),
                ),
            ]
        )

        try:
            await studio.save(respx_stash_client)
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert len(graphql_route.calls) == 1
        req = json.loads(graphql_route.calls[0].request.content)
        assert req["variables"]["input"]["studio_id"] is None

    @pytest.mark.asyncio
    async def test_studio_images_side_mutation(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """Studio.images fires bulkImageUpdate with studio_id."""
        studio = Studio.from_graphql({"id": "3001", "name": "Acme"})
        studio.images = []
        studio.mark_clean()

        studio.images.append(Image(id="6001"))

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json=create_graphql_response("bulkImageUpdate", [{"id": "6001"}]),
                ),
            ]
        )

        try:
            await studio.save(respx_stash_client)
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert len(graphql_route.calls) == 1
        req = json.loads(graphql_route.calls[0].request.content)
        assert "bulkImageUpdate" in req["query"]
        assert req["variables"]["input"]["studio_id"] == "3001"

    @pytest.mark.asyncio
    async def test_studio_galleries_side_mutation(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """Studio.galleries fires bulkGalleryUpdate with studio_id."""
        studio = Studio.from_graphql({"id": "3001", "name": "Acme"})
        studio.galleries = []
        studio.mark_clean()

        studio.galleries.append(Gallery(id="7001"))

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json=create_graphql_response("bulkGalleryUpdate", [{"id": "7001"}]),
                ),
            ]
        )

        try:
            await studio.save(respx_stash_client)
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert len(graphql_route.calls) == 1
        req = json.loads(graphql_route.calls[0].request.content)
        assert "bulkGalleryUpdate" in req["query"]
        assert req["variables"]["input"]["studio_id"] == "3001"

    @pytest.mark.asyncio
    async def test_studio_groups_side_mutation(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """Studio.groups fires bulkGroupUpdate with studio_id."""
        studio = Studio.from_graphql({"id": "3001", "name": "Acme"})
        studio.groups = []
        studio.mark_clean()

        studio.groups.append(Group(id="5001"))

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json=create_graphql_response("bulkGroupUpdate", [{"id": "5001"}]),
                ),
            ]
        )

        try:
            await studio.save(respx_stash_client)
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert len(graphql_route.calls) == 1
        req = json.loads(graphql_route.calls[0].request.content)
        assert "bulkGroupUpdate" in req["query"]
        assert req["variables"]["input"]["studio_id"] == "3001"

    # ── Tag side mutations ───────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_tag_add_scenes_fires_bulk_update(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """Adding scenes to tag fires bulkSceneUpdate with tag_ids ADD."""
        tag = Tag.from_graphql({"id": "4001", "name": "Action"})
        tag.scenes = []
        tag.mark_clean()

        tag.scenes.append(Scene(id="2001"))

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json=create_graphql_response("bulkSceneUpdate", [{"id": "2001"}]),
                ),
            ]
        )

        try:
            await tag.save(respx_stash_client)
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert len(graphql_route.calls) == 1
        req = json.loads(graphql_route.calls[0].request.content)
        assert "bulkSceneUpdate" in req["query"]
        assert req["variables"]["input"]["tag_ids"]["mode"] == "ADD"
        assert req["variables"]["input"]["tag_ids"]["ids"] == ["4001"]

    @pytest.mark.asyncio
    async def test_tag_add_performers_fires_bulk_update(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """Adding performers to tag fires bulkPerformerUpdate with tag_ids ADD."""
        tag = Tag.from_graphql({"id": "4001", "name": "Blonde"})
        tag.performers = []
        tag.mark_clean()

        tag.performers.append(Performer(id="1001", name="Test"))

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json=create_graphql_response(
                        "bulkPerformerUpdate", [{"id": "1001"}]
                    ),
                ),
            ]
        )

        try:
            await tag.save(respx_stash_client)
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert len(graphql_route.calls) == 1
        req = json.loads(graphql_route.calls[0].request.content)
        assert "bulkPerformerUpdate" in req["query"]
        assert req["variables"]["input"]["tag_ids"]["mode"] == "ADD"

    @pytest.mark.asyncio
    async def test_tag_remove_groups_fires_bulk_update(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """Removing groups from tag fires bulkGroupUpdate with tag_ids REMOVE."""
        g1 = Group(id="5001")
        tag = Tag.from_graphql({"id": "4001", "name": "Series"})
        tag.groups = [g1]
        tag.mark_clean()

        tag.groups.remove(g1)

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json=create_graphql_response("bulkGroupUpdate", [{"id": "5001"}]),
                ),
            ]
        )

        try:
            await tag.save(respx_stash_client)
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert len(graphql_route.calls) == 1
        req = json.loads(graphql_route.calls[0].request.content)
        assert req["variables"]["input"]["tag_ids"]["mode"] == "REMOVE"

    # ── to_input() exclusion for side-mutation fields ────────────────

    @pytest.mark.asyncio
    async def test_performer_to_input_excludes_side_mutation_fields(
        self, respx_entity_store
    ) -> None:
        """Performer.to_input() excludes scenes/galleries/images."""
        performer = Performer.from_graphql({"id": "1001", "name": "Test"})
        performer.scenes = [Scene(id="2001")]
        performer.galleries = [Gallery(id="7001")]
        performer.images = [Image(id="6001")]
        performer.mark_clean()

        # Make a non-side field dirty too
        performer.name = "Updated"

        input_data = await performer.to_input()
        assert "name" in input_data
        assert "scenes" not in input_data
        assert "scene_ids" not in input_data
        assert "galleries" not in input_data
        assert "gallery_ids" not in input_data
        assert "images" not in input_data
        assert "image_ids" not in input_data

    @pytest.mark.asyncio
    async def test_studio_to_input_excludes_side_mutation_fields(
        self, respx_entity_store
    ) -> None:
        """Studio.to_input() excludes scenes/images/galleries/groups."""
        studio = Studio.from_graphql({"id": "3001", "name": "Acme"})
        studio.mark_clean()

        studio.name = "Updated Acme"

        input_data = await studio.to_input()
        assert "name" in input_data
        for field in ("scenes", "images", "galleries", "groups"):
            assert field not in input_data

    # ── Batching ─────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_bulk_handler_batches_large_sets(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """Large relationship diffs are batched (batch_size=3 for test)."""
        # Create a handler with tiny batch size for testing
        handler = StashObject._make_bulk_relationship_handler(
            "scenes",
            "bulk_scene_update",
            "performer_ids",
            batch_size=3,
        )

        performer = Performer.from_graphql({"id": "1001", "name": "Test"})
        performer.scenes = []
        performer.mark_clean()

        # Add 7 scenes — should result in 3 batches (3 + 3 + 1)
        for i in range(7):
            performer.scenes.append(Scene(id=f"{2001 + i}"))

        responses = [
            httpx.Response(
                200,
                json=create_graphql_response(
                    "bulkSceneUpdate", [{"id": f"{2001 + i}"} for i in range(3)]
                ),
            )
            for _ in range(3)
        ]

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=responses
        )

        try:
            await handler(respx_stash_client, performer)
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert len(graphql_route.calls) == 3

        # Verify each batch has correct mode
        for call in graphql_route.calls:
            req = json.loads(call.request.content)
            assert req["variables"]["input"]["performer_ids"]["mode"] == "ADD"

        # Total IDs across all batches should be 7
        all_ids = set()
        for call in graphql_route.calls:
            req = json.loads(call.request.content)
            all_ids.update(req["variables"]["input"]["ids"])
        assert len(all_ids) == 7


class TestBidirectionalSync:
    """Tests for fixed bidirectional relationship sync."""

    # ── Image.galleries ↔ Gallery.images ─────────────────────────────

    @pytest.mark.asyncio
    async def test_image_add_to_gallery_syncs_gallery_images(
        self, respx_entity_store
    ) -> None:
        """image.add_to_gallery(gallery) syncs gallery.images."""
        image = Image.from_graphql({"id": "6001", "title": "Photo"})
        image.galleries = []
        gallery = Gallery.from_graphql(create_gallery_dict(id="7001", title="Album"))
        gallery.images = []

        await image.add_to_gallery(gallery)

        assert gallery in image.galleries
        assert image in gallery.images

    @pytest.mark.asyncio
    async def test_gallery_add_image_syncs_image_galleries(
        self, respx_entity_store
    ) -> None:
        """gallery.add_image(image) syncs image.galleries."""
        gallery = Gallery.from_graphql(create_gallery_dict(id="7001", title="Album"))
        gallery.images = []
        image = Image.from_graphql({"id": "6001", "title": "Photo"})
        image.galleries = []

        await gallery.add_image(image)

        assert image in gallery.images
        assert gallery in image.galleries

    # ── Group.studio ↔ Studio.groups ─────────────────────────────────

    def test_setting_group_studio_syncs_studio_groups(self, respx_entity_store) -> None:
        """Setting group.studio syncs studio.groups."""
        studio = Studio.from_graphql({"id": "3001", "name": "Acme"})
        studio.groups = []
        group = Group.from_graphql({"id": "5001", "name": "Series A"})

        group.studio = studio

        assert studio in [group.studio]
        assert group in studio.groups


class TestSceneGroupsSerialization:
    """Tests for Scene.groups __relationships__ entry and serialization."""

    def test_scene_groups_in_relationships(self) -> None:
        """Scene.__relationships__ includes groups with complex_object strategy."""
        from stash_graphql_client.types.base import RelationshipMetadata

        assert "groups" in Scene.__relationships__
        rel = Scene.__relationships__["groups"]
        assert isinstance(rel, RelationshipMetadata)
        assert rel.query_strategy == "complex_object"
        assert rel.inverse_type == "Group"
        assert rel.inverse_query_field == "scenes"
        assert rel.transform is not None

    def test_scene_groups_transform(self, respx_entity_store) -> None:
        """Scene.groups transform converts SceneGroup to SceneGroupInput."""
        rel = Scene.__relationships__["groups"]

        # SceneGroup can't be constructed directly due to forward-ref resolution
        # (Group is under TYPE_CHECKING in scene.py), so we use a simple stand-in.
        class MockSceneGroup:
            def __init__(self, group: Group, scene_index: int) -> None:
                self.group = group
                self.scene_index = scene_index

        group = Group(id="5001")
        scene_group = MockSceneGroup(group=group, scene_index=3)

        result = rel.transform(scene_group)

        assert isinstance(result, SceneGroupInput)
        assert result.group_id == "5001"
        assert result.scene_index == 3

    @pytest.mark.asyncio
    async def test_scene_groups_serialized_in_to_input(
        self, respx_entity_store
    ) -> None:
        """Scene.groups changes are serialized via to_input()."""
        scene = Scene.from_graphql(
            {
                "id": "2001",
                "title": "Test",
                "groups": [
                    {"group": {"id": "5001"}, "scene_index": 0},
                ],
            }
        )
        scene.mark_clean()

        # Create a second scene that has a different group list to force dirty
        scene2 = Scene.from_graphql(
            {
                "id": "2002",
                "title": "Test2",
                "groups": [
                    {"group": {"id": "5001"}, "scene_index": 0},
                    {"group": {"id": "5002"}, "scene_index": 1},
                ],
            }
        )

        # Copy groups from scene2 to scene (avoids SceneGroup.model_validate)
        scene.groups = scene2.groups

        input_data = await scene.to_input()

        assert "groups" in input_data
        assert len(input_data["groups"]) == 2
        group_ids = {g["group_id"] for g in input_data["groups"]}
        assert group_ids == {"5001", "5002"}


class TestConvenienceMethods:
    """Tests for add_*/remove_* convenience methods on entities with side mutations."""

    @pytest.mark.asyncio
    async def test_performer_add_scene(self, respx_entity_store) -> None:
        """performer.add_scene() adds to scenes list."""
        performer = Performer.from_graphql({"id": "1001", "name": "Test"})
        performer.scenes = []
        scene = Scene(id="2001")

        await performer.add_scene(scene)

        assert scene in performer.scenes
        assert performer.is_dirty()

    @pytest.mark.asyncio
    async def test_performer_remove_scene(self, respx_entity_store) -> None:
        """performer.remove_scene() removes from scenes list."""
        scene = Scene(id="2001")
        performer = Performer.from_graphql({"id": "1001", "name": "Test"})
        performer.scenes = [scene]
        performer.mark_clean()

        await performer.remove_scene(scene)

        assert scene not in performer.scenes
        assert performer.is_dirty()

    @pytest.mark.asyncio
    async def test_performer_add_gallery(self, respx_entity_store) -> None:
        """performer.add_gallery() adds to galleries list."""
        performer = Performer.from_graphql({"id": "1001", "name": "Test"})
        performer.galleries = []
        gallery = Gallery(id="7001")

        await performer.add_gallery(gallery)

        assert gallery in performer.galleries

    @pytest.mark.asyncio
    async def test_performer_add_image(self, respx_entity_store) -> None:
        """performer.add_image() adds to images list."""
        performer = Performer.from_graphql({"id": "1001", "name": "Test"})
        performer.images = []
        image = Image(id="6001")

        await performer.add_image(image)

        assert image in performer.images

    @pytest.mark.asyncio
    async def test_studio_add_scene(self, respx_entity_store) -> None:
        """studio.add_scene() adds to scenes list."""
        studio = Studio.from_graphql({"id": "3001", "name": "Acme"})
        studio.scenes = []
        scene = Scene(id="2001")

        await studio.add_scene(scene)

        assert scene in studio.scenes

    @pytest.mark.asyncio
    async def test_studio_add_group(self, respx_entity_store) -> None:
        """studio.add_group() adds to groups list."""
        studio = Studio.from_graphql({"id": "3001", "name": "Acme"})
        studio.groups = []
        group = Group(id="5001")

        await studio.add_group(group)

        assert group in studio.groups

    @pytest.mark.asyncio
    async def test_tag_add_scene(self, respx_entity_store) -> None:
        """tag.add_scene() adds to scenes list."""
        tag = Tag.from_graphql({"id": "4001", "name": "Action"})
        tag.scenes = []
        scene = Scene(id="2001")

        await tag.add_scene(scene)

        assert scene in tag.scenes

    @pytest.mark.asyncio
    async def test_tag_add_performer(self, respx_entity_store) -> None:
        """tag.add_performer() adds to performers list."""
        tag = Tag.from_graphql({"id": "4001", "name": "Blonde"})
        tag.performers = []
        performer = Performer(id="1001", name="Test")

        await tag.add_performer(performer)

        assert performer in tag.performers

    @pytest.mark.asyncio
    async def test_tag_add_gallery(self, respx_entity_store) -> None:
        """tag.add_gallery() adds to galleries list."""
        tag = Tag.from_graphql({"id": "4001", "name": "HD"})
        tag.galleries = []
        gallery = Gallery(id="7001")

        await tag.add_gallery(gallery)

        assert gallery in tag.galleries

    @pytest.mark.asyncio
    async def test_tag_add_group(self, respx_entity_store) -> None:
        """tag.add_group() adds to groups list."""
        tag = Tag.from_graphql({"id": "4001", "name": "Series"})
        tag.groups = []
        group = Group(id="5001")

        await tag.add_group(group)

        assert group in tag.groups

    # ── remove_* methods ─────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_performer_remove_gallery(self, respx_entity_store) -> None:
        """performer.remove_gallery() removes from galleries list."""
        gallery = Gallery(id="7001")
        performer = Performer.from_graphql({"id": "1001", "name": "Test"})
        performer.galleries = [gallery]
        performer.mark_clean()

        await performer.remove_gallery(gallery)
        assert gallery not in performer.galleries
        assert performer.is_dirty()

    @pytest.mark.asyncio
    async def test_performer_remove_image(self, respx_entity_store) -> None:
        """performer.remove_image() removes from images list."""
        image = Image(id="6001")
        performer = Performer.from_graphql({"id": "1001", "name": "Test"})
        performer.images = [image]
        performer.mark_clean()

        await performer.remove_image(image)
        assert image not in performer.images

    @pytest.mark.asyncio
    async def test_studio_remove_scene(self, respx_entity_store) -> None:
        """studio.remove_scene() removes from scenes list."""
        scene = Scene(id="2001")
        studio = Studio.from_graphql({"id": "3001", "name": "Acme"})
        studio.scenes = [scene]
        studio.mark_clean()

        await studio.remove_scene(scene)
        assert scene not in studio.scenes
        assert studio.is_dirty()

    @pytest.mark.asyncio
    async def test_studio_remove_image(self, respx_entity_store) -> None:
        """studio.remove_image() removes from images list."""
        image = Image(id="6001")
        studio = Studio.from_graphql({"id": "3001", "name": "Acme"})
        studio.images = [image]
        studio.mark_clean()

        await studio.remove_image(image)
        assert image not in studio.images

    @pytest.mark.asyncio
    async def test_studio_remove_gallery(self, respx_entity_store) -> None:
        """studio.remove_gallery() removes from galleries list."""
        gallery = Gallery(id="7001")
        studio = Studio.from_graphql({"id": "3001", "name": "Acme"})
        studio.galleries = [gallery]
        studio.mark_clean()

        await studio.remove_gallery(gallery)
        assert gallery not in studio.galleries

    @pytest.mark.asyncio
    async def test_studio_remove_group(self, respx_entity_store) -> None:
        """studio.remove_group() removes from groups list."""
        group = Group(id="5001")
        studio = Studio.from_graphql({"id": "3001", "name": "Acme"})
        studio.groups = [group]
        studio.mark_clean()

        await studio.remove_group(group)
        assert group not in studio.groups

    @pytest.mark.asyncio
    async def test_tag_remove_scene(self, respx_entity_store) -> None:
        """tag.remove_scene() removes from scenes list."""
        scene = Scene(id="2001")
        tag = Tag.from_graphql({"id": "4001", "name": "Action"})
        tag.scenes = [scene]
        tag.mark_clean()

        await tag.remove_scene(scene)
        assert scene not in tag.scenes

    @pytest.mark.asyncio
    async def test_tag_remove_image(self, respx_entity_store) -> None:
        """tag.remove_image() removes from images list."""
        image = Image(id="6001")
        tag = Tag.from_graphql({"id": "4001", "name": "HD"})
        tag.images = [image]
        tag.mark_clean()

        await tag.remove_image(image)
        assert image not in tag.images

    @pytest.mark.asyncio
    async def test_tag_remove_gallery(self, respx_entity_store) -> None:
        """tag.remove_gallery() removes from galleries list."""
        gallery = Gallery(id="7001")
        tag = Tag.from_graphql({"id": "4001", "name": "HD"})
        tag.galleries = [gallery]
        tag.mark_clean()

        await tag.remove_gallery(gallery)
        assert gallery not in tag.galleries

    @pytest.mark.asyncio
    async def test_tag_remove_performer(self, respx_entity_store) -> None:
        """tag.remove_performer() removes from performers list."""
        performer = Performer(id="1001", name="Test")
        tag = Tag.from_graphql({"id": "4001", "name": "Blonde"})
        tag.performers = [performer]
        tag.mark_clean()

        await tag.remove_performer(performer)
        assert performer not in tag.performers

    @pytest.mark.asyncio
    async def test_tag_remove_group(self, respx_entity_store) -> None:
        """tag.remove_group() removes from groups list."""
        group = Group(id="5001")
        tag = Tag.from_graphql({"id": "4001", "name": "Series"})
        tag.groups = [group]
        tag.mark_clean()

        await tag.remove_group(group)
        assert group not in tag.groups

    # ── Missing convenience method coverage ──────────────────────────

    @pytest.mark.asyncio
    async def test_studio_add_image(self, respx_entity_store) -> None:
        """studio.add_image() adds to images list."""
        studio = Studio.from_graphql({"id": "3001", "name": "Acme"})
        studio.images = []
        image = Image(id="6001")

        await studio.add_image(image)
        assert image in studio.images

    @pytest.mark.asyncio
    async def test_studio_add_gallery(self, respx_entity_store) -> None:
        """studio.add_gallery() adds to galleries list."""
        studio = Studio.from_graphql({"id": "3001", "name": "Acme"})
        studio.galleries = []
        gallery = Gallery(id="7001")

        await studio.add_gallery(gallery)
        assert gallery in studio.galleries

    @pytest.mark.asyncio
    async def test_tag_add_image(self, respx_entity_store) -> None:
        """tag.add_image() adds to images list."""
        tag = Tag.from_graphql({"id": "4001", "name": "HD"})
        tag.images = []
        image = Image(id="6001")

        await tag.add_image(image)
        assert image in tag.images

    @pytest.mark.asyncio
    async def test_tag_add_scene_marker(self, respx_entity_store) -> None:
        """tag.add_scene_marker() adds to scene_markers list."""
        from stash_graphql_client.types.markers import SceneMarker

        tag = Tag.from_graphql({"id": "4001", "name": "Action"})
        tag.scene_markers = []
        marker = SceneMarker(id="8001")

        await tag.add_scene_marker(marker)
        assert marker in tag.scene_markers

    @pytest.mark.asyncio
    async def test_tag_remove_scene_marker(self, respx_entity_store) -> None:
        """tag.remove_scene_marker() removes from scene_markers list."""
        from stash_graphql_client.types.markers import SceneMarker

        marker = SceneMarker(id="8001")
        tag = Tag.from_graphql({"id": "4001", "name": "Action"})
        tag.scene_markers = [marker]
        tag.mark_clean()

        await tag.remove_scene_marker(marker)
        assert marker not in tag.scene_markers


class TestUnsetGuards:
    """Tests for UNSET guards in _add_to_relationship."""

    @pytest.mark.asyncio
    async def test_filter_query_field_unset_no_store_raises(self) -> None:
        """Adding to a filter_query field with UNSET value and no store raises."""
        from unittest.mock import patch

        from stash_graphql_client.errors import StashIntegrationError

        performer = Performer.from_graphql({"id": "1001", "name": "Test"})
        scene = Scene(id="2001")

        # Performer.scenes is UNSET (not provided in from_graphql)
        # Patch store to None to simulate disconnected mode
        with (
            patch.object(type(performer), "_store", None),
            pytest.raises(
                StashIntegrationError,
                match="filter_query strategy",
            ),
        ):
            await performer.add_scene(scene)

    @pytest.mark.asyncio
    async def test_filter_query_field_populated_via_filter_query_hint(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """populate() for a filter_query field uses _fetch_filter_query_relationship
        to resolve the field via the filter_query_hint, enabling add_scene to succeed."""

        performer = Performer.from_graphql({"id": "1001", "name": "Test"})
        # performer.scenes is UNSET (not in the from_graphql dict)
        scene = Scene.from_graphql({"id": "2001", "title": "Test Scene"})

        # Mock: populate now fires findScenes via filter_query_hint
        # (not findPerformer), returning an empty scenes list
        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={"data": {"findScenes": {"count": 0, "scenes": []}}},
                ),
            ]
        )

        # With filter_query support, populate successfully initializes
        # performer.scenes to [], so add_scene can proceed
        await performer.add_scene(scene)
        assert scene in performer.scenes

    @pytest.mark.asyncio
    async def test_filter_query_field_still_unset_after_populate_raises(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """If _fetch_filter_query_relationship silently fails to set the field,
        the UNSET guard in _add_to_relationship still fires."""
        from stash_graphql_client.errors import StashIntegrationError

        performer = Performer.from_graphql({"id": "1001", "name": "Test"})
        scene = Scene(id="2001")

        # Patch _fetch_filter_query_relationship to be a no-op — populate()
        # runs but leaves performer.scenes as UNSET
        with (
            patch.object(
                respx_entity_store,
                "_fetch_filter_query_relationship",
                new_callable=AsyncMock,
            ),
            pytest.raises(
                StashIntegrationError,
                match="filter_query strategy and could not be populated",
            ),
        ):
            await performer.add_scene(scene)

    @pytest.mark.asyncio
    async def test_direct_field_unset_after_populate_raises(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """populate() returns data without a direct_field → still UNSET → raises."""
        from stash_graphql_client.errors import StashIntegrationError

        scene = Scene.from_graphql({"id": "2001", "title": "Test"})
        # scene.galleries is UNSET (not in the from_graphql dict)
        gallery = Gallery(id="7001")

        # Mock: populate fires findScene, response has no "galleries" key
        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json=create_graphql_response(
                        "findScene", {"id": "2001", "title": "Test"}
                    ),
                ),
            ]
        )

        with pytest.raises(
            StashIntegrationError,
            match="field is still UNSET after populate",
        ):
            await scene.add_to_gallery(gallery)

    @pytest.mark.asyncio
    async def test_filter_query_inverse_unset_no_store_raises(self) -> None:
        """Syncing inverse filter_query field with no store raises."""
        from unittest.mock import patch

        from stash_graphql_client.errors import StashIntegrationError

        # Image.galleries has inverse_query_field="images" on Gallery
        # Gallery.images uses filter_query strategy
        image = Image.from_graphql({"id": "6001", "title": "Photo"})
        image.galleries = []
        gallery = Gallery(id="7001")
        # gallery.images is UNSET, and we remove the store

        with (
            patch.object(type(gallery), "_store", None),
            pytest.raises(
                StashIntegrationError,
                match="filter_query strategy",
            ),
        ):
            await image.add_to_gallery(gallery)
