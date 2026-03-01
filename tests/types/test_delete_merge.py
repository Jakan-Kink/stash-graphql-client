"""Tests for delete(), bulk_destroy(), and merge() on StashObject.

Tests the new entity lifecycle methods following TESTING_REQUIREMENTS.md:
- Mock only at HTTP boundary using respx
- Use FactoryBoy factories for creating test objects
"""

from unittest.mock import patch

import httpx
import pytest
import respx

from stash_graphql_client import (
    Gallery,
    Performer,
    Scene,
    Studio,
    Tag,
)
from stash_graphql_client.types.base import StashObject
from stash_graphql_client.types.markers import SceneMarker
from tests.fixtures.stash import (
    SceneFactory,
    TagFactory,
    create_graphql_response,
    create_tag_dict,
)


# =============================================================================
# delete() Tests
# =============================================================================


class TestEntityDelete:
    """Tests for StashObject.delete() method."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_delete_sends_destroy_mutation(self, respx_stash_client) -> None:
        """Test that delete() sends the correct GraphQL destroy mutation."""
        tag = TagFactory.build(id="123", name="Test Tag")

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json=create_graphql_response("tagDestroy", True),
                )
            ]
        )

        result = await tag.delete(respx_stash_client)

        assert result is True
        assert len(graphql_route.calls) == 1

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_delete_scene_with_kwargs(self, respx_stash_client) -> None:
        """Test that delete() passes kwargs (e.g., delete_file) to destroy input."""
        scene = SceneFactory.build(id="456", title="Test Scene")

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json=create_graphql_response("sceneDestroy", True),
                )
            ]
        )

        result = await scene.delete(respx_stash_client, delete_file=True)

        assert result is True
        # Verify the mutation was called with delete_file in input
        request_body = graphql_route.calls[0].request.content.decode()
        assert "delete_file" in request_body or "deleteFile" in request_body

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_delete_invalidates_cache(
        self, respx_entity_store, respx_stash_client
    ) -> None:
        """Test that delete() invalidates the entity from the store cache."""
        store = respx_entity_store

        tag = TagFactory.build(id="123", name="Test Tag")
        store._cache_entity(tag)
        assert store.get_cached(Tag, "123") is not None

        with patch.object(StashObject, "_store", store):
            respx.post("http://localhost:9999/graphql").mock(
                side_effect=[
                    httpx.Response(
                        200,
                        json=create_graphql_response("tagDestroy", True),
                    )
                ]
            )

            await tag.delete(respx_stash_client)

        assert store.get_cached(Tag, "123") is None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_delete_raises_on_new_object(self, respx_stash_client) -> None:
        """Test that delete() raises ValueError on unsaved (new) objects."""
        tag = Tag(name="Unsaved Tag")  # No server ID, has UUID
        assert tag.is_new()

        with pytest.raises(ValueError, match="Cannot delete unsaved"):
            await tag.delete(respx_stash_client)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_delete_raises_on_unsupported_type(self, respx_stash_client) -> None:
        """Test that delete() raises NotImplementedError for types without __destroy_input_type__."""
        marker = SceneMarker(id="123")

        with pytest.raises(NotImplementedError, match="does not support delete"):
            await marker.delete(respx_stash_client)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_delete_raises_on_failure(self, respx_stash_client) -> None:
        """Test that delete() raises ValueError when server returns False."""
        tag = TagFactory.build(id="123", name="Test Tag")

        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json=create_graphql_response("tagDestroy", False),
                )
            ]
        )

        with pytest.raises(ValueError, match="Failed to delete"):
            await tag.delete(respx_stash_client)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_delete_gallery_uses_ids_field(self, respx_stash_client) -> None:
        """Test that Gallery.delete() uses 'ids' (plural) in destroy input."""
        gallery = Gallery(id="789", title="Test Gallery")
        gallery._is_new = False  # Mark as existing

        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json=create_graphql_response("galleryDestroy", True),
                )
            ]
        )

        result = await gallery.delete(respx_stash_client)
        assert result is True

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_delete_without_store_skips_invalidation(
        self, respx_stash_client
    ) -> None:
        """Test that delete() succeeds when _store is None (no cache to invalidate)."""
        tag = TagFactory.build(id="123", name="Test Tag")

        with patch.object(StashObject, "_store", None):
            respx.post("http://localhost:9999/graphql").mock(
                side_effect=[
                    httpx.Response(
                        200,
                        json=create_graphql_response("tagDestroy", True),
                    )
                ]
            )

            result = await tag.delete(respx_stash_client)
            assert result is True


# =============================================================================
# bulk_destroy() Tests
# =============================================================================


class TestBulkDestroy:
    """Tests for StashObject.bulk_destroy() classmethod."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_bulk_destroy_with_input_type(self, respx_stash_client) -> None:
        """Test bulk_destroy() for types with __bulk_destroy_input_type__ (Scene)."""
        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json=create_graphql_response("scenesDestroy", True),
                )
            ]
        )

        result = await Scene.bulk_destroy(respx_stash_client, ["1", "2", "3"])

        assert result is True
        assert len(graphql_route.calls) == 1

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_bulk_destroy_with_bare_ids(self, respx_stash_client) -> None:
        """Test bulk_destroy() for types using bare ids param (Tag)."""
        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json=create_graphql_response("tagsDestroy", True),
                )
            ]
        )

        result = await Tag.bulk_destroy(respx_stash_client, ["10", "20"])

        assert result is True
        assert len(graphql_route.calls) == 1

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_bulk_destroy_invalidates_cache(
        self, respx_entity_store, respx_stash_client
    ) -> None:
        """Test that bulk_destroy() invalidates all deleted entities from cache."""
        store = respx_entity_store

        tag1 = TagFactory.build(id="10", name="Tag 1")
        tag2 = TagFactory.build(id="20", name="Tag 2")
        store._cache_entity(tag1)
        store._cache_entity(tag2)

        with patch.object(StashObject, "_store", store):
            respx.post("http://localhost:9999/graphql").mock(
                side_effect=[
                    httpx.Response(
                        200,
                        json=create_graphql_response("tagsDestroy", True),
                    )
                ]
            )

            await Tag.bulk_destroy(respx_stash_client, ["10", "20"])

        assert store.get_cached(Tag, "10") is None
        assert store.get_cached(Tag, "20") is None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_bulk_destroy_raises_on_failure(self, respx_stash_client) -> None:
        """Test that bulk_destroy() raises ValueError when server returns False."""
        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json=create_graphql_response("tagsDestroy", False),
                )
            ]
        )

        with pytest.raises(ValueError, match="Failed to bulk delete"):
            await Tag.bulk_destroy(respx_stash_client, ["1", "2"])

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_bulk_destroy_without_store_skips_invalidation(
        self, respx_stash_client
    ) -> None:
        """Test that bulk_destroy() succeeds when _store is None."""
        with patch.object(StashObject, "_store", None):
            respx.post("http://localhost:9999/graphql").mock(
                side_effect=[
                    httpx.Response(
                        200,
                        json=create_graphql_response("tagsDestroy", True),
                    )
                ]
            )

            result = await Tag.bulk_destroy(respx_stash_client, ["1", "2"])
            assert result is True


# =============================================================================
# merge() Tests
# =============================================================================


class TestMerge:
    """Tests for StashObject.merge() classmethod."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_merge_tags(self, respx_stash_client) -> None:
        """Test Tag.merge() sends correct mutation and returns merged entity."""
        merged_tag_data = create_tag_dict(id="3", name="Merged Tag")

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json=create_graphql_response("tagsMerge", merged_tag_data),
                )
            ]
        )

        result = await Tag.merge(
            respx_stash_client, source_ids=["1", "2"], destination_id="3"
        )

        assert result is not None
        assert result.id == "3"
        assert result.name == "Merged Tag"
        assert len(graphql_route.calls) == 1

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_merge_uses_correct_operation_key(self, respx_stash_client) -> None:
        """Test that Tag uses 'tagsMerge' (plural) operation key."""
        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json=create_graphql_response(
                        "tagsMerge", create_tag_dict(id="3", name="Result")
                    ),
                )
            ]
        )

        result = await Tag.merge(
            respx_stash_client, source_ids=["1"], destination_id="3"
        )
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_merge_invalidates_source_entities(
        self, respx_entity_store, respx_stash_client
    ) -> None:
        """Test that merge() invalidates source entities from cache."""
        store = respx_entity_store

        tag1 = TagFactory.build(id="1", name="Source 1")
        tag2 = TagFactory.build(id="2", name="Source 2")
        tag3 = TagFactory.build(id="3", name="Destination")
        store._cache_entity(tag1)
        store._cache_entity(tag2)
        store._cache_entity(tag3)

        with patch.object(StashObject, "_store", store):
            respx.post("http://localhost:9999/graphql").mock(
                side_effect=[
                    httpx.Response(
                        200,
                        json=create_graphql_response(
                            "tagsMerge",
                            create_tag_dict(id="3", name="Destination"),
                        ),
                    )
                ]
            )

            await Tag.merge(
                respx_stash_client, source_ids=["1", "2"], destination_id="3"
            )

        # Source entities should be invalidated
        assert store.get_cached(Tag, "1") is None
        assert store.get_cached(Tag, "2") is None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_merge_returns_none_when_no_data(self, respx_stash_client) -> None:
        """Test that merge() returns None when server returns no entity data."""
        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json=create_graphql_response("tagsMerge", None),
                )
            ]
        )

        result = await Tag.merge(
            respx_stash_client, source_ids=["1"], destination_id="3"
        )
        assert result is None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_merge_raises_on_unsupported_type(self, respx_stash_client) -> None:
        """Test that merge() raises NotImplementedError for types without __merge_input_type__."""
        with pytest.raises(NotImplementedError, match="does not support merge"):
            await Studio.merge(
                respx_stash_client,
                source_ids=["1"],
                destination_id="2",
            )

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_merge_performer_uses_singular_operation_key(
        self, respx_stash_client
    ) -> None:
        """Test that non-Tag merge uses singular operation key (performerMerge)."""
        performer_data = {
            "id": "3",
            "name": "Merged Performer",
        }

        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json=create_graphql_response("performerMerge", performer_data),
                )
            ]
        )

        result = await Performer.merge(
            respx_stash_client, source_ids=["1", "2"], destination_id="3"
        )

        assert result is not None
        assert result.id == "3"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_merge_without_store_skips_invalidation(
        self, respx_stash_client
    ) -> None:
        """Test that merge() succeeds when _store is None (no cache to invalidate)."""
        with patch.object(StashObject, "_store", None):
            respx.post("http://localhost:9999/graphql").mock(
                side_effect=[
                    httpx.Response(
                        200,
                        json=create_graphql_response(
                            "tagsMerge",
                            create_tag_dict(id="3", name="Merged"),
                        ),
                    )
                ]
            )

            result = await Tag.merge(
                respx_stash_client, source_ids=["1"], destination_id="3"
            )
            assert result is not None
            assert result.id == "3"


# =============================================================================
# store.delete() Tests
# =============================================================================


class TestStoreDelete:
    """Tests for StashEntityStore.delete() method."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_store_delete_delegates_and_invalidates(
        self, respx_entity_store, respx_stash_client
    ) -> None:
        """Test that store.delete() calls entity.delete() and invalidates cache."""
        store = respx_entity_store

        tag = TagFactory.build(id="123", name="Test Tag")
        store._cache_entity(tag)

        with patch.object(StashObject, "_store", store):
            respx.post("http://localhost:9999/graphql").mock(
                side_effect=[
                    httpx.Response(
                        200,
                        json=create_graphql_response("tagDestroy", True),
                    )
                ]
            )

            result = await store.delete(tag)

        assert result is True
        assert store.get_cached(Tag, "123") is None


# =============================================================================
# store.invalidate() Overload Tests
# =============================================================================


class TestInvalidateOverload:
    """Tests for the new invalidate(entity) overload."""

    @pytest.mark.unit
    def test_invalidate_with_entity_instance(self, respx_entity_store) -> None:
        """Test invalidate() accepts a StashObject instance."""
        store = respx_entity_store

        tag = TagFactory.build(id="123", name="Test Tag")
        store._cache_entity(tag)
        assert store.get_cached(Tag, "123") is not None

        store.invalidate(tag)
        assert store.get_cached(Tag, "123") is None

    @pytest.mark.unit
    def test_invalidate_with_type_and_id(self, respx_entity_store) -> None:
        """Test invalidate() still works with (type, id) pair."""
        store = respx_entity_store

        tag = TagFactory.build(id="456", name="Test Tag")
        store._cache_entity(tag)

        store.invalidate(Tag, "456")
        assert store.get_cached(Tag, "456") is None


# =============================================================================
# store.get_cached() Tests
# =============================================================================


class TestGetCached:
    """Tests for StashEntityStore.get_cached() method."""

    @pytest.mark.unit
    def test_get_cached_returns_cached_entity(self, respx_entity_store) -> None:
        """Test get_cached() returns entity when in cache."""
        store = respx_entity_store
        tag = TagFactory.build(id="123", name="Cached Tag")
        store._cache_entity(tag)

        result = store.get_cached(Tag, "123")
        assert result is not None
        assert result.id == "123"
        assert result.name == "Cached Tag"

    @pytest.mark.unit
    def test_get_cached_returns_none_on_miss(self, respx_entity_store) -> None:
        """Test get_cached() returns None when not in cache."""
        store = respx_entity_store
        result = store.get_cached(Tag, "nonexistent")
        assert result is None

    @pytest.mark.unit
    def test_get_cached_returns_none_on_expired(self, respx_entity_store) -> None:
        """Test get_cached() returns None for expired cache entries."""
        store = respx_entity_store
        tag = TagFactory.build(id="123", name="Expired Tag")

        # Manually insert expired entry
        import time

        from stash_graphql_client.store import CacheEntry

        store._cache[("Tag", "123")] = CacheEntry(
            entity=tag,
            cached_at=time.monotonic() - 100,
            ttl_seconds=1.0,  # Expired
        )
        store._type_index.setdefault("Tag", set()).add("123")

        result = store.get_cached(Tag, "123")
        assert result is None
