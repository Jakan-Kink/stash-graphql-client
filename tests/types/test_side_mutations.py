"""Tests for __side_mutations__ and _pending_side_ops support.

Tests cover:
- Field-based side mutations (Gallery.cover, Gallery.images, Scene activity/play/o, Image o_counter)
- Queued side operations (_pending_side_ops)
- Handler deduplication for multi-field → single handler
- Edge cases (failure recovery, new object ID preservation)
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest
import respx

from stash_graphql_client.types.base import StashObject
from stash_graphql_client.types.gallery import Gallery
from stash_graphql_client.types.image import Image
from stash_graphql_client.types.scene import Scene
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
            create_gallery_dict(id="g1", title="Test", cover=None)
        )
        gallery.mark_clean()
        assert not gallery.is_dirty()

        # Set cover to an image
        gallery.cover = Image(id="img-1")
        assert gallery.is_dirty()
        assert "cover" in gallery.get_changed_fields()

    def test_clearing_cover_makes_gallery_dirty(self, respx_entity_store) -> None:
        """Setting cover to None (reset) marks the gallery as dirty."""
        gallery = Gallery.from_graphql(
            create_gallery_dict(
                id="g2", title="Test", cover={"id": "img-1", "__typename": "Image"}
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
            create_gallery_dict(id="g3", title="Test", cover=None)
        )
        gallery.mark_clean()

        # Make cover dirty AND a regular field dirty
        gallery.cover = Image(id="img-1")
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
        gallery.cover = Image(id="img-1")

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
            create_gallery_dict(id="g4", title="Test", cover=None)
        )
        gallery.mark_clean()

        # Set cover
        gallery.cover = Image(id="img-42")

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
        assert req["variables"]["input"]["gallery_id"] == "g4"
        assert req["variables"]["input"]["cover_image_id"] == "img-42"

        # Object should be clean after save
        assert not gallery.is_dirty()

    @pytest.mark.asyncio
    async def test_save_fires_reset_cover_mutation(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """save() should fire resetGalleryCover when cover is set to None."""
        gallery = Gallery.from_graphql(
            create_gallery_dict(
                id="g5", title="Test", cover={"id": "img-1", "__typename": "Image"}
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
        assert req["variables"]["input"]["gallery_id"] == "g5"

        assert not gallery.is_dirty()

    @pytest.mark.asyncio
    async def test_save_fires_both_main_and_side_mutations(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """When both regular fields and cover are dirty, both mutations fire."""
        gallery = Gallery.from_graphql(
            create_gallery_dict(id="g6", title="Old Title", cover=None)
        )
        gallery.mark_clean()

        gallery.title = "New Title"
        gallery.cover = Image(id="img-99")

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                # Main galleryUpdate
                httpx.Response(
                    200,
                    json=create_graphql_response("galleryUpdate", {"id": "g6"}),
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
        assert req2["variables"]["input"]["cover_image_id"] == "img-99"

        assert not gallery.is_dirty()

    # ── New object edge case ───────────────────────────────────────

    @pytest.mark.asyncio
    async def test_save_new_gallery_fires_side_mutation_after_create(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """For new galleries, side mutations fire AFTER create (using real ID)."""
        gallery = Gallery(title="Brand New")
        gallery.cover = Image(id="img-cover")
        assert gallery.is_new()

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                # galleryCreate returns real server ID
                httpx.Response(
                    200,
                    json=create_graphql_response(
                        "galleryCreate", {"id": "server-gallery-id"}
                    ),
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
        assert req2["variables"]["input"]["gallery_id"] == "server-gallery-id"

        assert gallery.id == "server-gallery-id"
        assert not gallery.is_new()
        assert not gallery.is_dirty()

    # ── No side mutations by default ───────────────────────────────

    def test_stash_object_has_empty_side_mutations(self) -> None:
        """Base StashObject has no side mutations by default."""
        assert StashObject.__side_mutations__ == {}

    def test_tag_has_no_side_mutations(self) -> None:
        """Tag (a simple entity) inherits empty side mutations."""
        assert Tag.__side_mutations__ == {}

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
                    "tagCreate", {"id": "t-1", "name": "Plain Tag"}
                ),
            )
        )

        try:
            await tag.save(respx_stash_client)
        finally:
            dump_graphql_calls(graphql_route.calls)

        assert len(graphql_route.calls) == 1
        assert tag.id == "t-1"
        assert not tag.is_dirty()

    # ── Queued side operations ─────────────────────────────────────

    @pytest.mark.asyncio
    async def test_queue_side_op_prevents_save_skip(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """save() should NOT skip when _pending_side_ops is non-empty."""
        tag = Tag.from_graphql({"id": "t-1", "name": "Test"})
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
        gallery = Gallery.from_graphql(create_gallery_dict(id="g1", title="Test"))
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
                    json=create_graphql_response("galleryUpdate", {"id": "g1"}),
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
        tag = Tag.from_graphql({"id": "t-1", "name": "Test"})
        tag.mark_clean()

        tag._queue_side_op(AsyncMock())
        assert len(tag._pending_side_ops) == 1

        await tag.save(respx_stash_client)
        assert len(tag._pending_side_ops) == 0

    def test_queued_ops_cleared_on_mark_clean(self, respx_entity_store) -> None:
        """mark_clean() also clears the queue."""
        tag = Tag.from_graphql({"id": "t-1", "name": "Test"})
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
            create_gallery_dict(id="g1", title="Test", cover=None)
        )
        gallery.mark_clean()

        # Field-based side mutation
        gallery.cover = Image(id="img-1")

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
            create_gallery_dict(id="g1", title="Test", cover=None)
        )
        gallery.mark_clean()
        gallery.cover = Image(id="img-1")

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
        gallery.cover = Image(id="img-1")
        assert gallery.is_new()

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                # Create succeeds
                httpx.Response(
                    200,
                    json=create_graphql_response("galleryCreate", {"id": "real-id"}),
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
        assert gallery.id == "real-id"
        assert not gallery.is_new()

    # ── Handler deduplication ──────────────────────────────────────

    @pytest.mark.asyncio
    async def test_side_mutation_handler_deduplication(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """Multi-field side mutations sharing a handler fire only once."""
        scene = Scene.from_graphql(
            {"id": "s1", "title": "Test", "resume_time": 10.0, "play_duration": 100.0}
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
        gallery = Gallery.from_graphql(create_gallery_dict(id="g1", title="Test"))
        gallery.images = []
        gallery.mark_clean()

        gallery.images.append(Image(id="img-1"))
        gallery.images.append(Image(id="img-2"))

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
        assert req["variables"]["input"]["gallery_id"] == "g1"
        assert set(req["variables"]["input"]["image_ids"]) == {"img-1", "img-2"}

    @pytest.mark.asyncio
    async def test_images_diff_fires_remove_mutation(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """Removing images from gallery fires removeGalleryImages."""
        img1 = Image(id="img-1")
        gallery = Gallery.from_graphql(create_gallery_dict(id="g2", title="Test"))
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
        assert req["variables"]["input"]["image_ids"] == ["img-1"]

    @pytest.mark.asyncio
    async def test_images_both_add_and_remove(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """Adding and removing images fires both mutations."""
        img_keep = Image(id="keep")
        img_remove = Image(id="remove")
        gallery = Gallery.from_graphql(create_gallery_dict(id="g3", title="Test"))
        gallery.images = [img_keep, img_remove]
        gallery.mark_clean()

        gallery.images.remove(img_remove)
        gallery.images.append(Image(id="new"))

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
        image = Image.from_graphql({"id": "i1", "o_counter": 2, "organized": False})
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
        image = Image.from_graphql({"id": "i2", "o_counter": 5, "organized": False})
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
        scene = Scene.from_graphql({"id": "s1", "title": "Test", "play_count": 5})
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
            {"id": "s1", "title": "T", "o_history": ["2026-01-01T00:00:00Z"]}
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
                "id": "s2",
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
            {"id": "s3", "title": "T", "play_history": [], "play_count": 0}
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
                "id": "s4",
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
        scene = Scene.from_graphql({"id": "s5", "title": "T", "o_counter": 3})
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
                "id": "s6",
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
        scene = Scene.from_graphql({"id": "s7", "title": "T"})
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
        image = Image.from_graphql({"id": "i3", "o_counter": 5, "organized": False})
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
        image = Image.from_graphql({"id": "i4", "organized": False})
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
        image = Image.from_graphql({"id": "i5", "o_counter": 3, "organized": False})
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
        gallery = Gallery.from_graphql(create_gallery_dict(id="g10", title="Test"))
        gallery.images = []
        gallery.mark_clean()

        img = Image(id="img-new")
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
        img = Image(id="img-existing")
        img.galleries = []  # Pre-set to avoid store.populate() for inverse
        gallery = Gallery.from_graphql(create_gallery_dict(id="g11", title="Test"))
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
        image = Image.from_graphql({"id": "i6", "o_counter": 3, "organized": False})
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
                "id": "s8",
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
                "id": "s9",
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
