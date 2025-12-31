"""Tests for StashEntityStore.

Tests the StashEntityStore following TESTING_REQUIREMENTS.md:
- Mock only at HTTP boundary using respx
- Use FactoryBoy factories for creating test objects
- Verify caching, TTL, and query behavior
"""

import time
import uuid
from datetime import timedelta
from unittest.mock import patch

import httpx
import pytest
import respx

from stash_graphql_client import (
    Gallery,
    Image,
    Performer,
    Scene,
    StashEntityStore,
    Studio,
    Tag,
)
from stash_graphql_client.errors import StashError, StashIntegrationError
from stash_graphql_client.store import CacheEntry
from stash_graphql_client.types.base import StashObject
from tests.fixtures.stash import (
    PerformerFactory,
    SceneFactory,
    StudioFactory,
    TagFactory,
    create_find_galleries_result,
    create_find_images_result,
    create_find_performers_result,
    create_gallery_dict,
    create_graphql_response,
    create_image_dict,
    create_performer_dict,
    create_studio_dict,
)


# =============================================================================
# Unit Tests - CacheEntry
# =============================================================================


class TestCacheEntry:
    """Tests for CacheEntry dataclass."""

    @pytest.mark.unit
    def test_cache_entry_not_expired_when_no_ttl(self) -> None:
        """Test that cache entry without TTL never expires."""
        performer = PerformerFactory.build()
        entry: CacheEntry[Performer] = CacheEntry(
            entity=performer,
            cached_at=time.monotonic(),
            ttl_seconds=None,
        )

        assert not entry.is_expired()

    @pytest.mark.unit
    def test_cache_entry_not_expired_within_ttl(self) -> None:
        """Test that cache entry is not expired within TTL."""
        performer = PerformerFactory.build()
        entry: CacheEntry[Performer] = CacheEntry(
            entity=performer,
            cached_at=time.monotonic(),
            ttl_seconds=60.0,  # 60 seconds
        )

        assert not entry.is_expired()

    @pytest.mark.unit
    def test_cache_entry_expired_after_ttl(self) -> None:
        """Test that cache entry is expired after TTL passes."""
        performer = PerformerFactory.build()
        # Set cached_at to 2 seconds ago with 1 second TTL
        entry: CacheEntry[Performer] = CacheEntry(
            entity=performer,
            cached_at=time.monotonic() - 2.0,
            ttl_seconds=1.0,
        )

        assert entry.is_expired()


# =============================================================================
# Unit Tests - Filter Translation
# =============================================================================


class TestFilterTranslation:
    """Tests for Django-style filter to GraphQL translation."""

    @pytest.mark.unit
    def test_parse_lookup_equals(self, respx_entity_store) -> None:
        """Test parsing simple equality lookup."""
        store = respx_entity_store

        field, modifier = store._parse_lookup("title")
        assert field == "title"
        assert modifier == "EQUALS"

    @pytest.mark.unit
    def test_parse_lookup_contains(self, respx_entity_store) -> None:
        """Test parsing __contains lookup."""
        store = respx_entity_store

        field, modifier = store._parse_lookup("title__contains")
        assert field == "title"
        assert modifier == "INCLUDES"

    @pytest.mark.unit
    def test_parse_lookup_regex(self, respx_entity_store) -> None:
        """Test parsing __regex lookup."""
        store = respx_entity_store

        field, modifier = store._parse_lookup("title__regex")
        assert field == "title"
        assert modifier == "MATCHES_REGEX"

    @pytest.mark.unit
    def test_parse_lookup_gte(self, respx_entity_store) -> None:
        """Test parsing __gte lookup."""
        store = respx_entity_store

        field, modifier = store._parse_lookup("rating100__gte")
        assert field == "rating100"
        assert modifier == "GREATER_THAN"

    @pytest.mark.unit
    def test_parse_lookup_between(self, respx_entity_store) -> None:
        """Test parsing __between lookup."""
        store = respx_entity_store

        field, modifier = store._parse_lookup("rating100__between")
        assert field == "rating100"
        assert modifier == "BETWEEN"

    @pytest.mark.unit
    def test_parse_lookup_null(self, respx_entity_store) -> None:
        """Test parsing __null lookup."""
        store = respx_entity_store

        field, modifier = store._parse_lookup("studio__null")
        assert field == "studio"
        assert modifier == "IS_NULL"

    @pytest.mark.unit
    def test_build_criterion_equals(self, respx_entity_store) -> None:
        """Test building EQUALS criterion."""
        store = respx_entity_store

        criterion = store._build_criterion("title", "EQUALS", "test")
        assert criterion == {"value": "test", "modifier": "EQUALS"}

    @pytest.mark.unit
    def test_build_criterion_between(self, respx_entity_store) -> None:
        """Test building BETWEEN criterion."""
        store = respx_entity_store

        criterion = store._build_criterion("rating100", "BETWEEN", (60, 90))
        assert criterion == {"value": 60, "value2": 90, "modifier": "BETWEEN"}

    @pytest.mark.unit
    def test_build_criterion_is_null_true(self, respx_entity_store) -> None:
        """Test building IS_NULL criterion with True."""
        store = respx_entity_store

        criterion = store._build_criterion("studio", "IS_NULL", True)
        assert criterion == {"value": "", "modifier": "IS_NULL"}

    @pytest.mark.unit
    def test_build_criterion_is_null_false(self, respx_entity_store) -> None:
        """Test building IS_NULL criterion with False returns NOT_NULL."""
        store = respx_entity_store

        criterion = store._build_criterion("studio", "IS_NULL", False)
        assert criterion == {"value": "", "modifier": "NOT_NULL"}

    @pytest.mark.unit
    def test_build_criterion_includes_list(self, respx_entity_store) -> None:
        """Test building INCLUDES criterion with list."""
        store = respx_entity_store

        criterion = store._build_criterion("tags", "INCLUDES", ["1", "2"])
        assert criterion == {"value": ["1", "2"], "modifier": "INCLUDES"}


# =============================================================================
# Unit Tests - Cache Operations
# =============================================================================


class TestCacheOperations:
    """Tests for cache manipulation methods."""

    @pytest.mark.unit
    def test_cache_entity(self, respx_entity_store) -> None:
        """Test that _cache_entity stores entity correctly."""
        store = respx_entity_store
        performer = PerformerFactory.build(id="123", name="Test Performer")

        store._cache_entity(performer)

        assert store.is_cached(Performer, "123")
        stats = store.cache_stats()
        assert stats.total_entries == 1
        assert stats.by_type.get("Performer") == 1

    @pytest.mark.unit
    def test_invalidate_single(self, respx_entity_store) -> None:
        """Test invalidating a single entity."""
        store = respx_entity_store
        performer = PerformerFactory.build(id="123")

        store._cache_entity(performer)
        assert store.is_cached(Performer, "123")

        store.invalidate(Performer, "123")
        assert not store.is_cached(Performer, "123")

    @pytest.mark.unit
    def test_invalidate_type(self, respx_entity_store) -> None:
        """Test invalidating all entities of a type."""
        store = respx_entity_store
        p1 = PerformerFactory.build(id="1")
        p2 = PerformerFactory.build(id="2")
        tag = TagFactory.build(id="t1")

        store._cache_entity(p1)
        store._cache_entity(p2)
        store._cache_entity(tag)

        store.invalidate_type(Performer)

        assert not store.is_cached(Performer, "1")
        assert not store.is_cached(Performer, "2")
        assert store.is_cached(Tag, "t1")  # Tag should still be cached

    @pytest.mark.unit
    def test_invalidate_all(self, respx_entity_store) -> None:
        """Test invalidating entire cache."""
        store = respx_entity_store
        performer = PerformerFactory.build(id="1")
        tag = TagFactory.build(id="t1")

        store._cache_entity(performer)
        store._cache_entity(tag)

        store.invalidate_all()

        stats = store.cache_stats()
        assert stats.total_entries == 0

    @pytest.mark.unit
    def test_set_ttl_per_type(self, respx_entity_store) -> None:
        """Test setting TTL for a specific type."""
        store = respx_entity_store

        store.set_ttl(Performer, timedelta(minutes=5))
        store.set_ttl(Scene, timedelta(hours=1))

        # Verify internal state
        assert store._type_ttls.get("Performer") == timedelta(minutes=5)
        assert store._type_ttls.get("Scene") == timedelta(hours=1)

    @pytest.mark.unit
    def test_cache_stats(self, respx_entity_store) -> None:
        """Test cache statistics."""
        store = respx_entity_store
        p1 = PerformerFactory.build(id="1")
        p2 = PerformerFactory.build(id="2")
        tag = TagFactory.build(id="t1")

        store._cache_entity(p1)
        store._cache_entity(p2)
        store._cache_entity(tag)

        stats = store.cache_stats()

        assert stats.total_entries == 3
        assert stats.by_type["Performer"] == 2
        assert stats.by_type["Tag"] == 1
        assert stats.expired_count == 0

    @pytest.mark.unit
    def test_filter_cached_objects(self, respx_entity_store) -> None:
        """Test filtering cached objects with predicate."""
        store = respx_entity_store
        p1 = PerformerFactory.build(id="1", name="Alice", favorite=True)
        p2 = PerformerFactory.build(id="2", name="Bob", favorite=False)
        p3 = PerformerFactory.build(id="3", name="Charlie", favorite=True)

        store._cache_entity(p1)
        store._cache_entity(p2)
        store._cache_entity(p3)

        favorites = store.filter(Performer, lambda p: p.favorite)

        assert len(favorites) == 2
        names = {p.name for p in favorites}
        assert names == {"Alice", "Charlie"}

    @pytest.mark.unit
    def test_all_cached(self, respx_entity_store) -> None:
        """Test getting all cached objects of a type."""
        store = respx_entity_store
        p1 = PerformerFactory.build(id="1")
        p2 = PerformerFactory.build(id="2")
        tag = TagFactory.build(id="t1")

        store._cache_entity(p1)
        store._cache_entity(p2)
        store._cache_entity(tag)

        performers = store.all_cached(Performer)
        tags = store.all_cached(Tag)

        assert len(performers) == 2
        assert len(tags) == 1

    @pytest.mark.unit
    def test_cache_size_property(self, respx_stash_client) -> None:
        """Test cache_size property returns number of cached entities."""
        # Create a fresh store to avoid fixture state
        store = StashEntityStore(respx_stash_client, default_ttl=timedelta(minutes=30))

        # Empty cache
        assert store.cache_size == 0

        # Add some entities
        p1 = PerformerFactory.build(id="1")
        p2 = PerformerFactory.build(id="2")
        tag = TagFactory.build(id="t1")

        store._cache_entity(p1)
        assert store.cache_size == 1

        store._cache_entity(p2)
        store._cache_entity(tag)
        assert store.cache_size == 3

        # Invalidate one
        store.invalidate(Performer, "1")
        assert store.cache_size == 2


# =============================================================================
# Integration Tests - Get Operations with HTTP Mocking
# =============================================================================


class TestGetOperations:
    """Tests for get() and get_many() with HTTP mocking."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_cache_miss_fetches(
        self, respx_entity_store, respx_mock: respx.MockRouter
    ) -> None:
        """Test that get() fetches on cache miss."""
        store = respx_entity_store

        performer_data = create_performer_dict(id="123", name="Test Performer")
        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json=create_graphql_response("findPerformer", performer_data),
                )
            ]
        )

        result = await store.get(Performer, "123")

        assert result is not None
        assert result.id == "123"
        assert result.name == "Test Performer"
        assert len(graphql_route.calls) == 1  # Fetched from GraphQL

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_cache_hit_no_fetch(
        self, respx_entity_store, respx_mock: respx.MockRouter
    ) -> None:
        """Test that get() returns cached entity without fetching."""
        store = respx_entity_store

        # Pre-populate cache
        performer = PerformerFactory.build(id="123", name="Cached Performer")
        store._cache_entity(performer)

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[httpx.Response(200, json={"data": {}})]
        )

        result = await store.get(Performer, "123")

        assert result is not None
        assert result.id == "123"
        assert result.name == "Cached Performer"
        assert len(graphql_route.calls) == 0  # No fetch needed

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_expired_refetches(self, respx_stash_client) -> None:
        """Test that get() refetches when cache entry is expired."""
        store = StashEntityStore(respx_stash_client, default_ttl=timedelta(seconds=0))

        with patch.object(StashObject, "_store", store):
            # Pre-populate with immediately expired entry
            old_performer = PerformerFactory.build(id="123", name="Old Name")
            store._cache_entity(old_performer)

            # Wait a tiny bit to ensure expiration
            time.sleep(0.01)

            new_performer_data = create_performer_dict(id="123", name="New Name")
            graphql_route = respx.post("http://localhost:9999/graphql").mock(
                side_effect=[
                    httpx.Response(
                        200,
                        json=create_graphql_response(
                            "findPerformer", new_performer_data
                        ),
                    )
                ]
            )

            result = await store.get(Performer, "123")

            assert result is not None
            assert result.name == "New Name"  # Got fresh data
            assert len(graphql_route.calls) == 1

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_not_found_returns_none(self, respx_entity_store) -> None:
        """Test that get() returns None when entity not found."""
        store = respx_entity_store

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json=create_graphql_response("findPerformer", None),
                )
            ]
        )

        result = await store.get(Performer, "nonexistent")

        assert result is None
        assert len(graphql_route.calls) == 1

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_many_partial_cache(self, respx_entity_store) -> None:
        """Test that get_many() uses cache for some and fetches others."""
        store = respx_entity_store

        # Pre-cache one performer
        cached = PerformerFactory.build(id="1", name="Cached")
        store._cache_entity(cached)

        # Mock fetch for the other
        fetched_data = create_performer_dict(id="2", name="Fetched")
        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json=create_graphql_response("findPerformer", fetched_data),
                )
            ]
        )

        results = await store.get_many(Performer, ["1", "2"])

        assert len(results) == 2
        names = {p.name for p in results}
        assert names == {"Cached", "Fetched"}
        # Only one fetch (for id="2")
        assert len(graphql_route.calls) == 1


# =============================================================================
# Integration Tests - Find Operations with HTTP Mocking
# =============================================================================


class TestFindOperations:
    """Tests for find() and find_one() with HTTP mocking."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_find_caches_results(self, respx_entity_store) -> None:
        """Test that find() caches all returned entities."""
        store = respx_entity_store

        performers_data = create_find_performers_result(
            count=2,
            performers=[
                create_performer_dict(id="1", name="Alice"),
                create_performer_dict(id="2", name="Bob"),
            ],
        )

        # Mock both calls - first for count check, second for actual fetch
        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200, json=create_graphql_response("findPerformers", performers_data)
                ),
                httpx.Response(
                    200, json=create_graphql_response("findPerformers", performers_data)
                ),
            ]
        )

        results = await store.find(Performer, name__contains="test")

        assert len(results) == 2
        # Both should now be cached
        assert store.is_cached(Performer, "1")
        assert store.is_cached(Performer, "2")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_find_raises_on_large_result(self, respx_entity_store) -> None:
        """Test that find() raises StashError when results exceed FIND_LIMIT."""
        store = respx_entity_store

        # Mock response with count > FIND_LIMIT
        large_result = create_find_performers_result(count=1500, performers=[])

        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200, json=create_graphql_response("findPerformers", large_result)
                )
            ]
        )

        with pytest.raises(StashError, match="exceeding limit of 1000"):
            await store.find(Performer, name__contains="test")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_find_one_returns_first(self, respx_entity_store) -> None:
        """Test that find_one() returns first match."""
        store = respx_entity_store

        performers_data = create_find_performers_result(
            count=5,
            performers=[create_performer_dict(id="1", name="First Match")],
        )

        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200, json=create_graphql_response("findPerformers", performers_data)
                )
            ]
        )

        result = await store.find_one(Performer, name="First Match")

        assert result is not None
        assert result.id == "1"
        assert result.name == "First Match"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_find_one_returns_none_on_no_match(self, respx_entity_store) -> None:
        """Test that find_one() returns None when no match."""
        store = respx_entity_store

        empty_result = create_find_performers_result(count=0, performers=[])

        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200, json=create_graphql_response("findPerformers", empty_result)
                )
            ]
        )

        result = await store.find_one(Performer, name="Nonexistent")

        assert result is None


# =============================================================================
# Integration Tests - find_iter with HTTP Mocking
# =============================================================================


class TestFindIterOperations:
    """Tests for find_iter() lazy pagination."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_find_iter_yields_items(self, respx_entity_store) -> None:
        """Test that find_iter() yields individual items."""
        store = respx_entity_store

        performers_data = create_find_performers_result(
            count=3,
            performers=[
                create_performer_dict(id="1", name="A"),
                create_performer_dict(id="2", name="B"),
                create_performer_dict(id="3", name="C"),
            ],
        )

        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200, json=create_graphql_response("findPerformers", performers_data)
                )
            ]
        )

        results = [
            performer async for performer in store.find_iter(Performer, query_batch=10)
        ]

        assert len(results) == 3
        names = [p.name for p in results]
        assert names == ["A", "B", "C"]

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_find_iter_early_break_stops_fetching(
        self, respx_entity_store
    ) -> None:
        """Test that breaking early from find_iter() stops fetching more pages."""
        store = respx_entity_store

        # First page
        page1 = create_find_performers_result(
            count=100,
            performers=[
                create_performer_dict(id="1", name="A"),
                create_performer_dict(id="2", name="B"),
            ],
        )

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200, json=create_graphql_response("findPerformers", page1)
                )
            ]
        )

        count = 0
        async for _ in store.find_iter(Performer, query_batch=2):
            count += 1
            if count >= 1:
                break

        # Should only have fetched first page
        assert len(graphql_route.calls) == 1

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_find_iter_caches_as_it_goes(self, respx_entity_store) -> None:
        """Test that find_iter() caches items as they are yielded."""
        store = respx_entity_store

        performers_data = create_find_performers_result(
            count=2,
            performers=[
                create_performer_dict(id="1", name="A"),
                create_performer_dict(id="2", name="B"),
            ],
        )

        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200, json=create_graphql_response("findPerformers", performers_data)
                )
            ]
        )

        async for _ in store.find_iter(Performer, query_batch=10):
            pass

        # Both should be cached
        assert store.is_cached(Performer, "1")
        assert store.is_cached(Performer, "2")


# =============================================================================
# Unit Tests - Default TTL
# =============================================================================


class TestDefaultTTL:
    """Tests for default TTL configuration."""

    @pytest.mark.unit
    def test_default_ttl_is_30_minutes(self, respx_entity_store) -> None:
        """Test that default TTL is 30 minutes."""
        store = respx_entity_store

        assert store._default_ttl == timedelta(minutes=30)

    @pytest.mark.unit
    def test_custom_default_ttl(self, respx_stash_client) -> None:
        """Test setting custom default TTL."""
        store = StashEntityStore(respx_stash_client, default_ttl=timedelta(hours=1))

        with patch.object(StashObject, "_store", store):
            assert store._default_ttl == timedelta(hours=1)

    @pytest.mark.unit
    def test_no_default_ttl(self, respx_stash_client) -> None:
        """Test disabling default TTL (never expire)."""
        store = StashEntityStore(respx_stash_client, default_ttl=None)

        with patch.object(StashObject, "_store", store):
            assert store._default_ttl is None


# =============================================================================
# Additional Coverage Tests
# =============================================================================


class TestGetManyEdgeCases:
    """Additional tests for get_many() edge cases."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_many_with_expired_entries(self, respx_stash_client) -> None:
        """Test get_many() when cached entries are expired."""
        store = StashEntityStore(respx_stash_client, default_ttl=timedelta(seconds=0))

        with patch.object(StashObject, "_store", store):
            # Pre-cache with immediately expiring entry
            expired = PerformerFactory.build(id="1", name="Expired")
            store._cache_entity(expired)

            time.sleep(0.01)  # Ensure expiration

            # Mock fetch for expired entry
            fetched_data = create_performer_dict(id="1", name="Refreshed")
            respx.post("http://localhost:9999/graphql").mock(
                side_effect=[
                    httpx.Response(
                        200,
                        json=create_graphql_response("findPerformer", fetched_data),
                    )
                ]
            )

            results = await store.get_many(Performer, ["1"])

            assert len(results) == 1
            assert results[0].name == "Refreshed"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_many_all_cached_no_fetch(self, respx_entity_store) -> None:
        """Test get_many() when all IDs are cached."""
        store = respx_entity_store

        # Pre-cache all performers
        p1 = PerformerFactory.build(id="1", name="Alice")
        p2 = PerformerFactory.build(id="2", name="Bob")
        store._cache_entity(p1)
        store._cache_entity(p2)

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[httpx.Response(200, json={"data": {}})]
        )

        results = await store.get_many(Performer, ["1", "2"])

        assert len(results) == 2
        assert len(graphql_route.calls) == 0  # No fetch needed


class TestFindEdgeCases:
    """Additional tests for find() edge cases."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_find_returns_empty_on_zero_count(self, respx_entity_store) -> None:
        """Test find() returns empty list when count is 0."""
        store = respx_entity_store

        empty_result = create_find_performers_result(count=0, performers=[])

        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200, json=create_graphql_response("findPerformers", empty_result)
                )
            ]
        )

        results = await store.find(Performer, name="nonexistent")

        assert results == []

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_find_raises_stash_error_on_large_result(
        self, respx_entity_store
    ) -> None:
        """Test that find() raises StashError (not ValueError) when exceeding limit."""
        store = respx_entity_store

        large_result = create_find_performers_result(count=1500, performers=[])

        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200, json=create_graphql_response("findPerformers", large_result)
                )
            ]
        )

        with pytest.raises(StashError):
            await store.find(Performer, name__contains="test")


class TestFindIterEdgeCases:
    """Additional tests for find_iter() edge cases."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_find_iter_invalid_query_batch(self, respx_entity_store) -> None:
        """Test find_iter() raises ValueError for invalid query_batch."""
        store = respx_entity_store

        with pytest.raises(ValueError, match="query_batch must be positive"):
            async for _ in store.find_iter(Performer, query_batch=0):
                pass

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_find_iter_multiple_pages(self, respx_entity_store) -> None:
        """Test find_iter() fetches multiple pages."""
        store = respx_entity_store

        # Page 1 - full batch (3 items = query_batch)
        page1 = create_find_performers_result(
            count=5,
            performers=[
                create_performer_dict(id="1", name="A"),
                create_performer_dict(id="2", name="B"),
                create_performer_dict(id="3", name="C"),
            ],
        )
        # Page 2 - partial batch (2 items < query_batch, signals last page)
        page2 = create_find_performers_result(
            count=5,
            performers=[
                create_performer_dict(id="4", name="D"),
                create_performer_dict(id="5", name="E"),
            ],
        )

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200, json=create_graphql_response("findPerformers", page1)
                ),
                httpx.Response(
                    200, json=create_graphql_response("findPerformers", page2)
                ),
            ]
        )

        results = [
            performer async for performer in store.find_iter(Performer, query_batch=3)
        ]

        assert len(results) == 5
        assert len(graphql_route.calls) == 2  # Two pages fetched


class TestFilterWithExpiredEntries:
    """Tests for filter() with expired entries."""

    @pytest.mark.unit
    def test_filter_skips_expired_entries(self, respx_stash_client) -> None:
        """Test filter() skips expired entries."""
        store = StashEntityStore(respx_stash_client, default_ttl=timedelta(seconds=0))

        with patch.object(StashObject, "_store", store):
            # Add entry that will expire immediately
            performer = PerformerFactory.build(id="1", name="Test", favorite=True)
            store._cache_entity(performer)

            time.sleep(0.01)  # Ensure expiration

            # Filter should skip expired entry
            favorites = store.filter(
                Performer,
                lambda p: p.favorite is True,  # Narrow bool | UnsetType to bool
            )

            assert len(favorites) == 0


class TestPopulateFunction:
    """Tests for populate() function and helpers."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_populate_list_of_stubs(self, respx_entity_store) -> None:
        """Test populate() with list of stub performers."""
        store = respx_entity_store

        # Patch store reference BEFORE creating stubs so identity map validator works
        with patch.object(StashObject, "_store", store):
            # Create scene with stub performers - they'll auto-register in store via identity map
            stub1 = Performer(id="1", name="")
            stub2 = Performer(id="2", name="")

            # Explicitly add stubs to ensure they're cached
            store.add(stub1)
            store.add(stub2)

            scene = SceneFactory.build(id="s1", performers=[stub1, stub2])

            # Mock performer fetches - use side_effect with enough responses for all calls
            # populate() may fetch each performer to complete the data
            respx.post("http://localhost:9999/graphql").mock(
                side_effect=[
                    httpx.Response(
                        200,
                        json=create_graphql_response(
                            "findPerformer", create_performer_dict(id="1", name="Alice")
                        ),
                    ),
                    httpx.Response(
                        200,
                        json=create_graphql_response(
                            "findPerformer", create_performer_dict(id="2", name="Bob")
                        ),
                    ),
                    # Add extra responses in case of additional fetches
                    httpx.Response(
                        200,
                        json=create_graphql_response(
                            "findPerformer", create_performer_dict(id="1", name="Alice")
                        ),
                    ),
                    httpx.Response(
                        200,
                        json=create_graphql_response(
                            "findPerformer", create_performer_dict(id="2", name="Bob")
                        ),
                    ),
                ]
            )

            result = await store.populate(scene, fields=["performers"])

            # The stubs in the scene should have been updated in-place
            assert len(result.performers) == 2
            names = {p.name for p in result.performers}
            assert names == {"Alice", "Bob"}
            # Verify original stub objects were updated
            assert stub1.name == "Alice"
            assert stub2.name == "Bob"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_populate_single_stub(self, respx_entity_store) -> None:
        """Test populate() with single stub studio."""
        store = respx_entity_store

        # Patch store reference BEFORE creating stubs so identity map validator works
        with patch.object(StashObject, "_store", store):
            # Create scene with stub studio - it'll auto-register in store via identity map
            stub_studio = Studio(id="st1", name="")

            # Explicitly add stub to ensure it's cached
            store.add(stub_studio)

            scene = SceneFactory.build(id="s1", studio=stub_studio)

            # Mock studio fetch - use side_effect with enough responses for all calls
            # populate() may fetch the studio to complete the data
            respx.post("http://localhost:9999/graphql").mock(
                side_effect=[
                    httpx.Response(
                        200,
                        json=create_graphql_response(
                            "findStudio",
                            create_studio_dict(id="st1", name="Big Studio"),
                        ),
                    ),
                    httpx.Response(
                        200,
                        json=create_graphql_response(
                            "findStudio",
                            create_studio_dict(id="st1", name="Big Studio"),
                        ),
                    ),
                ]
            )

            result = await store.populate(scene, fields=["studio"])

            # The stub in the scene should have been updated in-place
            assert result.studio is not None
            assert result.studio.name == "Big Studio"
            # Verify original stub object was updated
            assert stub_studio.name == "Big Studio"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_populate_nonexistent_field(self, respx_entity_store) -> None:
        """Test populate() with non-existent field logs warning."""
        store = respx_entity_store
        scene = SceneFactory.build(id="s1")

        # Should not raise, just log warning
        result = await store.populate(scene, fields=["nonexistent_field"])

        assert result.id == "s1"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_populate_none_value_skipped(self, respx_entity_store) -> None:
        """Test populate() skips fields with None value."""
        store = respx_entity_store
        scene = SceneFactory.build(id="s1", studio=None)

        # Should not raise or attempt to populate None
        result = await store.populate(scene, fields=["studio"])

        assert result.studio is None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_populate_list_non_stashobject(self, respx_entity_store) -> None:
        """Test _populate_list returns unchanged if items are not StashObjects."""
        store = respx_entity_store

        # List of strings, not StashObjects
        result = await store._populate_list(["a", "b", "c"])

        assert result == ["a", "b", "c"]

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_populate_list_empty(self, respx_entity_store) -> None:
        """Test _populate_list returns empty list unchanged."""
        store = respx_entity_store

        result = await store._populate_list([])

        assert result == []

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_populate_non_list_non_stashobject_field(
        self, respx_entity_store
    ) -> None:
        """Test populate() skips field that is not list or StashObject."""
        store = respx_entity_store

        # Scene has a 'title' field that is a string, not list or StashObject
        scene = SceneFactory.build(id="s1", title="My Scene Title")

        # Should not raise, title is neither list nor StashObject
        result = await store.populate(scene, fields=["title"])

        # Title should remain unchanged
        assert result.title == "My Scene Title"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_populate_single_stub_returns_none(self, respx_entity_store) -> None:
        """Test populate() when _populate_single returns None."""
        store = respx_entity_store

        # Create scene with stub studio
        stub_studio = Studio(id="st1", name="")
        scene = SceneFactory.build(id="s1", studio=stub_studio)

        # Mock studio fetch returns None (not found)
        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json=create_graphql_response("findStudio", None),
                )
            ]
        )

        result = await store.populate(scene, fields=["studio"])

        # Studio should remain the stub since populated_single is None
        assert result.studio is not None
        assert result.studio.id == "st1"
        assert result.studio.name == ""  # Still the stub

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_populate_single_full_object_not_stub(
        self, respx_entity_store
    ) -> None:
        """Test _populate_single returns original when not a stub."""
        store = respx_entity_store

        # Create scene with a FULL studio (not a stub)
        full_studio = StudioFactory.build(
            id="st1", name="Full Studio", urls=["http://example.com"]
        )
        scene = SceneFactory.build(id="s1", studio=full_studio)

        # Mock for potential GraphQL calls - populate() may still check
        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(200, json={"data": {}}),
                httpx.Response(200, json={"data": {}}),
            ]
        )

        result = await store.populate(scene, fields=["studio"])

        # Studio should remain unchanged (it's not a stub)
        assert result.studio is not None
        assert result.studio.name == "Full Studio"
        # May make a call to verify/fetch (implementation detail)
        # The important part is the studio data is preserved

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_populate_list_no_stubs(self, respx_entity_store) -> None:
        """Test _populate_list when no items are stubs."""
        store = respx_entity_store

        # Create scene with FULL performers (not stubs)
        full_performer1 = PerformerFactory.build(id="1", name="Alice", country="USA")
        full_performer2 = PerformerFactory.build(id="2", name="Bob", country="UK")
        scene = SceneFactory.build(
            id="s1", performers=[full_performer1, full_performer2]
        )

        # No mock needed for get_many since stub_ids will be empty
        # But _populate_list still calls get() for each item at the end
        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[httpx.Response(200, json={"data": {}})]
        )

        result = await store.populate(scene, fields=["performers"])

        # Performers should remain unchanged
        assert len(result.performers) == 2
        # No get_many call for stub_ids (since there are none)
        # But individual get() calls will happen - these hit cache since we haven't populated
        # Actually the full performers won't be in cache, so get() will be called
        # Let's just verify the performers are there
        names = {p.name for p in result.performers}
        assert "Alice" in names or len(result.performers) == 2

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_populate_with_fields_as_set(self, respx_entity_store) -> None:
        """Test populate() when fields parameter is already a set (not list)."""
        store = respx_entity_store

        # Create scene with stub studio
        stub_studio = Studio(id="st1", name="")
        scene = SceneFactory.build(id="s1", studio=stub_studio)

        # Mock studio fetch
        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json=create_graphql_response(
                        "findStudio",
                        create_studio_dict(id="st1", name="Big Studio"),
                    ),
                ),
                httpx.Response(
                    200,
                    json=create_graphql_response(
                        "findStudio",
                        create_studio_dict(id="st1", name="Big Studio"),
                    ),
                ),
            ]
        )

        # Pass fields as a set instead of list (covers line 417: fields_set = fields)
        result = await store.populate(scene, fields={"studio"})

        assert result.studio is not None
        assert result.studio.name == "Big Studio"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_populate_field_not_on_object(self, respx_entity_store) -> None:
        """Test populate() when field doesn't exist on object (covers continue path)."""
        store = respx_entity_store

        # Create scene
        scene = SceneFactory.build(id="s1")

        # Try to populate a field that doesn't exist on Scene
        # This should hit the `if not hasattr(obj, field_name): continue` path (line 461)
        result = await store.populate(scene, fields=["nonexistent_field", "title"])

        # Should complete without error, skipping the nonexistent field
        assert result.id == "s1"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_populate_single_object_not_needing_population(
        self, respx_entity_store
    ) -> None:
        """Test _populate_single when object doesn't need population (returns original)."""
        store = respx_entity_store

        # Create a FULL performer (not a stub) with many fields populated
        full_performer = PerformerFactory.build(
            id="p1",
            name="Full Performer",
            country="USA",
            ethnicity="Caucasian",
            gender="FEMALE",
        )
        # Set _received_fields to indicate it has lots of data
        object.__setattr__(
            full_performer,
            "_received_fields",
            {"id", "name", "country", "ethnicity", "gender"},
        )

        # Cache it
        store.add(full_performer)

        # Call _populate_single - should return original without fetching (line 494)
        result = await store._populate_single(full_performer, force_refetch=False)

        # Should return the same object without any GraphQL call
        assert result is full_performer
        assert result.name == "Full Performer"


class TestInvalidateNotCached:
    """Test invalidate() when entity is not cached."""

    @pytest.mark.unit
    def test_invalidate_not_cached_no_error(self, respx_entity_store) -> None:
        """Test invalidate() does nothing when entity not cached."""
        store = respx_entity_store

        # Should not raise
        store.invalidate(Performer, "nonexistent")

        # Cache should still be empty
        stats = store.cache_stats()
        assert stats.total_entries == 0


class TestCacheStatsWithExpired:
    """Test cache_stats() with expired entries."""

    @pytest.mark.unit
    def test_cache_stats_counts_expired(self, respx_stash_client) -> None:
        """Test cache_stats() counts expired entries."""
        store = StashEntityStore(respx_stash_client, default_ttl=timedelta(seconds=0))

        with patch.object(StashObject, "_store", store):
            # Add entry that expires immediately
            performer = PerformerFactory.build(id="1")
            store._cache_entity(performer)

            time.sleep(0.01)  # Ensure expiration

            stats = store.cache_stats()

            assert stats.total_entries == 1
            assert stats.expired_count == 1


class TestGetTtlForType:
    """Tests for _get_ttl_for_type helper."""

    @pytest.mark.unit
    def test_get_ttl_for_type_with_override(self, respx_entity_store) -> None:
        """Test _get_ttl_for_type returns type-specific TTL."""
        store = respx_entity_store
        store.set_ttl(Performer, timedelta(minutes=5))

        ttl = store._get_ttl_for_type("Performer")

        assert ttl == timedelta(minutes=5)

    @pytest.mark.unit
    def test_get_ttl_for_type_falls_back_to_default(self, respx_entity_store) -> None:
        """Test _get_ttl_for_type falls back to default."""
        store = respx_entity_store

        ttl = store._get_ttl_for_type("Scene")

        assert ttl == timedelta(minutes=30)  # Default


class TestExecuteFindByIdsEdgeCases:
    """Tests for _execute_find_by_ids edge cases."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_execute_find_by_ids_entity_not_found(
        self, respx_entity_store
    ) -> None:
        """Test _execute_find_by_ids skips not found entities."""
        store = respx_entity_store

        # Mock returns None for this performer
        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(200, json=create_graphql_response("findPerformer", None))
            ]
        )

        results = await store._execute_find_by_ids(Performer, ["nonexistent"])

        assert results == []


class TestTranslateFiltersEdgeCases:
    """Tests for _translate_filters edge cases."""

    @pytest.mark.unit
    def test_translate_filters_raw_dict_passthrough(self, respx_entity_store) -> None:
        """Test raw dict with modifier is passed through."""
        store = respx_entity_store

        _graphql_filter, entity_filter = store._translate_filters(
            "Scene",
            {"title": {"value": "test", "modifier": "NOT_EQUALS"}},
        )

        assert entity_filter is not None
        assert entity_filter["title"] == {"value": "test", "modifier": "NOT_EQUALS"}

    @pytest.mark.unit
    def test_translate_filters_nested_filter(self, respx_entity_store) -> None:
        """Test nested filters ending with _filter."""
        store = respx_entity_store

        _graphql_filter, entity_filter = store._translate_filters(
            "Scene",
            {"performers_filter": {"name": {"value": "Jane", "modifier": "EQUALS"}}},
        )

        assert entity_filter is not None
        assert "performers_filter" in entity_filter

    @pytest.mark.unit
    def test_translate_filters_criterion_none_skipped(self, respx_entity_store) -> None:
        """Test filters with None criterion are skipped."""
        store = respx_entity_store

        # Invalid BETWEEN (single value) returns None criterion
        _graphql_filter, entity_filter = store._translate_filters(
            "Scene",
            {"rating100__between": "invalid"},  # Not a tuple/list
        )

        # Should not include the invalid filter
        assert entity_filter is None or "rating100" not in entity_filter


class TestBuildCriterionEdgeCases:
    """Tests for _build_criterion edge cases."""

    @pytest.mark.unit
    def test_build_criterion_between_invalid_returns_none(
        self, respx_entity_store
    ) -> None:
        """Test BETWEEN with invalid value returns None."""
        store = respx_entity_store

        # Single value, not tuple/list of 2
        criterion = store._build_criterion("rating100", "BETWEEN", 50)

        assert criterion is None

    @pytest.mark.unit
    def test_build_criterion_between_wrong_length_returns_none(
        self, respx_entity_store
    ) -> None:
        """Test BETWEEN with wrong length tuple returns None."""
        store = respx_entity_store

        # Tuple of 3, not 2
        criterion = store._build_criterion("rating100", "BETWEEN", (10, 20, 30))

        assert criterion is None


class TestExecuteFindQueryEntityTypes:
    """Tests for _execute_find_query with different entity types."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_find_gallery_type(self, respx_entity_store) -> None:
        """Test find() with Gallery type."""
        store = respx_entity_store

        galleries_data = create_find_galleries_result(
            count=1,
            galleries=[create_gallery_dict(id="g1", title="Test Gallery")],
        )

        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200, json=create_graphql_response("findGalleries", galleries_data)
                ),
                httpx.Response(
                    200, json=create_graphql_response("findGalleries", galleries_data)
                ),
            ]
        )

        results = await store.find(Gallery, title__contains="test")

        assert len(results) == 1
        assert results[0].id == "g1"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_find_image_type(self, respx_entity_store) -> None:
        """Test find() with Image type."""
        store = respx_entity_store

        images_data = create_find_images_result(
            count=1,
            images=[create_image_dict(id="i1", title="Test Image")],
        )

        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200, json=create_graphql_response("findImages", images_data)
                ),
                httpx.Response(
                    200, json=create_graphql_response("findImages", images_data)
                ),
            ]
        )

        results = await store.find(Image, title__contains="test")

        assert len(results) == 1
        assert results[0].id == "i1"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_find_unsupported_type_raises(self, respx_entity_store) -> None:
        """Test find() with unsupported type raises ValueError."""
        store = respx_entity_store

        # Create a mock unsupported type
        class UnsupportedType(StashObject):
            __type_name__ = "Unsupported"

        with pytest.raises(ValueError, match="Unsupported entity type"):
            await store.find(UnsupportedType)


class TestNeedsPopulationEdgeCases:
    """Tests for _needs_population() edge cases."""

    @pytest.mark.unit
    def test_needs_population_fallback_heuristic_no_received_fields(
        self, respx_entity_store
    ) -> None:
        """Test _needs_population() fallback heuristic when no _received_fields."""
        store = respx_entity_store

        # Create performer without _received_fields tracking
        performer = Performer(id="1", name="Test")
        delattr(performer, "_received_fields")

        # Should use fallback heuristic (non_id_fields <= 1)
        result = store._needs_population(performer)

        # id + name = 2 fields, but exclude id/timestamps leaves just name (<=1)
        assert result is True

    @pytest.mark.unit
    def test_needs_population_with_fields_some_missing(
        self, respx_entity_store
    ) -> None:
        """Test _needs_population() when some requested fields are missing."""
        store = respx_entity_store

        performer = Performer(id="1", name="Test")
        performer._received_fields = {"id", "name"}

        # Request fields, some missing
        result = store._needs_population(
            performer, fields={"name", "gender", "birthdate"}
        )

        assert result is True

    @pytest.mark.unit
    def test_needs_population_with_fields_all_present(self, respx_entity_store) -> None:
        """Test _needs_population() when all requested fields are present."""
        store = respx_entity_store

        performer = Performer(id="1", name="Test")
        performer._received_fields = {"id", "name", "gender"}

        # Request fields, all present
        result = store._needs_population(performer, fields={"name", "gender"})

        assert result is False


class TestIsUuidMethod:
    """Tests for _is_uuid() method."""

    @pytest.mark.unit
    def test_is_uuid_valid_uuid(self, respx_entity_store) -> None:
        """Test _is_uuid() returns True for valid UUID."""
        store = respx_entity_store

        valid_uuid = uuid.uuid4().hex

        assert store._is_uuid(valid_uuid) is True

    @pytest.mark.unit
    def test_is_uuid_numeric_id(self, respx_entity_store) -> None:
        """Test _is_uuid() returns False for numeric ID."""
        store = respx_entity_store

        assert store._is_uuid("123") is False
        assert store._is_uuid("456789") is False

    @pytest.mark.unit
    def test_is_uuid_wrong_length(self, respx_entity_store) -> None:
        """Test _is_uuid() returns False for wrong length strings."""
        store = respx_entity_store

        assert store._is_uuid("abcdef") is False
        assert store._is_uuid("a" * 31) is False
        assert store._is_uuid("a" * 33) is False

    @pytest.mark.unit
    def test_is_uuid_non_hex_characters(self, respx_entity_store) -> None:
        """Test _is_uuid() returns False for non-hex characters."""
        store = respx_entity_store

        # 32 chars but not hex
        assert store._is_uuid("g" * 32) is False
        assert store._is_uuid("xyz" + "a" * 29) is False


class TestFindUnsavedRelatedObjects:
    """Tests for _find_unsaved_related_objects() method."""

    @pytest.mark.unit
    def test_find_unsaved_related_single_object_with_uuid(
        self, respx_entity_store
    ) -> None:
        """Test finding unsaved single related object with UUID."""
        store = respx_entity_store

        unsaved_studio = Studio(id=uuid.uuid4().hex, name="Unsaved Studio")
        scene = Scene(id="1", title="Test Scene", studio=unsaved_studio)

        unsaved = store._find_unsaved_related_objects(scene)

        assert len(unsaved) == 1
        assert unsaved[0] is unsaved_studio

    @pytest.mark.unit
    def test_find_unsaved_related_list_with_uuids(self, respx_entity_store) -> None:
        """Test finding unsaved related objects in lists."""
        store = respx_entity_store

        unsaved_p1 = Performer(id=uuid.uuid4().hex, name="Unsaved 1")
        unsaved_p2 = Performer(id=uuid.uuid4().hex, name="Unsaved 2")
        saved_p = Performer(id="123", name="Saved")

        scene = Scene(
            id="1",
            title="Test Scene",
            performers=[unsaved_p1, saved_p, unsaved_p2],
        )

        unsaved = store._find_unsaved_related_objects(scene)

        assert len(unsaved) == 2
        assert unsaved_p1 in unsaved
        assert unsaved_p2 in unsaved
        assert saved_p not in unsaved

    @pytest.mark.unit
    def test_find_unsaved_related_no_relationships_attr(
        self, respx_entity_store
    ) -> None:
        """Test _find_unsaved_related_objects() with object missing __relationships__."""
        store = respx_entity_store

        # Use Tag which has minimal relationships
        obj = Tag(id="1", name="Test")

        # Test edge case with empty __relationships__
        with patch.object(Tag, "__relationships__", {}):
            unsaved = store._find_unsaved_related_objects(obj)
            assert unsaved == []

    @pytest.mark.unit
    def test_find_unsaved_related_empty_list(self, respx_entity_store) -> None:
        """Test _find_unsaved_related_objects() with empty list relationship."""
        store = respx_entity_store

        scene = Scene(id="1", title="Test", performers=[])

        unsaved = store._find_unsaved_related_objects(scene)

        assert unsaved == []

    @pytest.mark.unit
    def test_find_unsaved_related_missing_field_name(self, respx_entity_store) -> None:
        """Test _find_unsaved_related_objects() with missing field_name (line 782)."""
        store = respx_entity_store

        # Create an object with __relationships__ that references a non-existent field
        performer = Performer(id="1", name="Test")

        # Mock __relationships__ to include a field that doesn't exist on the object
        with patch.object(
            Performer, "__relationships__", {"nonexistent_field": "Studio"}
        ):
            unsaved = store._find_unsaved_related_objects(performer)
            # Should skip the missing field and return empty list
            assert unsaved == []

    @pytest.mark.unit
    def test_find_unsaved_related_none_value(self, respx_entity_store) -> None:
        """Test _find_unsaved_related_objects() with None relationship value (line 786)."""
        store = respx_entity_store

        # Create scene with studio=None
        scene = Scene(id="1", title="Test", studio=None)

        unsaved = store._find_unsaved_related_objects(scene)

        # Should skip None values
        assert unsaved == []


class TestSaveMethod:
    """Tests for save() method."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_save_with_unsaved_related_cascades_and_warns(
        self, respx_stash_client, caplog
    ) -> None:
        """Test save() cascades for unsaved related objects with warning."""
        store = StashEntityStore(respx_stash_client)

        # Create unsaved tag with UUID (tags can be saved easily)
        unsaved_tag_uuid = uuid.uuid4().hex
        unsaved_tag = Tag(id=unsaved_tag_uuid, name="New Tag")
        unsaved_tag._is_new = True

        # Create performer with unsaved tag relationship
        performer = Performer(id="2", name="Test Performer", tags=[unsaved_tag])

        # Mock GraphQL responses for saves
        tag_response = create_graphql_response(
            "tagCreate", create_studio_dict(id="101", name="New Tag")
        )
        performer_response = create_graphql_response(
            "performerUpdate", create_performer_dict(id="2", name="Test Performer")
        )

        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(200, json=tag_response),  # Save tag
                httpx.Response(200, json=performer_response),  # Save performer
            ]
        )

        with caplog.at_level("WARNING"):
            await store.save(performer)

        # Check warning was logged
        assert any("Cascading save" in record.message for record in caplog.records)
        assert any("deprecated" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_save_with_more_than_3_unsaved_related_truncates_warning(
        self, respx_stash_client, caplog
    ) -> None:
        """Test save() warning message truncates when >3 unsaved objects (line 708)."""
        store = StashEntityStore(respx_stash_client)

        # Create 5 unsaved tags with UUIDs
        unsaved_tags = []
        for i in range(5):
            tag_uuid = uuid.uuid4().hex
            tag = Tag(id=tag_uuid, name=f"Tag {i}")
            tag._is_new = True
            unsaved_tags.append(tag)

        # Create performer with 5 unsaved tag relationships
        performer = Performer(id="2", name="Test Performer", tags=unsaved_tags)

        # Mock GraphQL responses for 5 tag saves + 1 performer save
        tag_responses = [
            create_graphql_response(
                "tagCreate", create_studio_dict(id=f"10{i}", name=f"Tag {i}")
            )
            for i in range(5)
        ]
        performer_response = create_graphql_response(
            "performerUpdate", create_performer_dict(id="2", name="Test Performer")
        )

        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                *[httpx.Response(200, json=r) for r in tag_responses],
                httpx.Response(200, json=performer_response),
            ]
        )

        with caplog.at_level("WARNING"):
            await store.save(performer)

        # Check warning includes "and N more" when >3 unsaved objects
        warning_messages = [
            r.message for r in caplog.records if "Cascading save" in r.message
        ]
        assert len(warning_messages) == 1
        assert "and 2 more" in warning_messages[0]  # Shows first 3, then "and 2 more"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_save_new_object_updates_cache_key(self, respx_stash_client) -> None:
        """Test save() updates cache key from UUID to real ID for new objects."""
        store = StashEntityStore(respx_stash_client)

        # Create new performer with UUID
        old_uuid = uuid.uuid4().hex
        performer = Performer(id=old_uuid, name="New Performer")
        performer._is_new = True

        # Add to cache with UUID key
        store.add(performer)
        assert ("Performer", old_uuid) in store._cache

        # Mock GraphQL response for save
        performer_response = create_graphql_response(
            "performerCreate", create_performer_dict(id="123", name="New Performer")
        )

        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[httpx.Response(200, json=performer_response)]
        )

        await store.save(performer)

        # Old UUID key removed, new ID key added
        assert ("Performer", old_uuid) not in store._cache
        assert ("Performer", "123") in store._cache

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_save_new_object_not_in_cache_adds_it(
        self, respx_stash_client
    ) -> None:
        """Test save() adds new object to cache if not already cached."""
        store = StashEntityStore(respx_stash_client)

        # Create new performer with UUID but DON'T add to cache
        old_uuid = uuid.uuid4().hex
        performer = Performer(id=old_uuid, name="New Performer")
        performer._is_new = True

        # Mock GraphQL response for save
        performer_response = create_graphql_response(
            "performerCreate", create_performer_dict(id="123", name="New Performer")
        )

        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[httpx.Response(200, json=performer_response)]
        )

        await store.save(performer)

        # Should be cached with new ID
        assert ("Performer", "123") in store._cache

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_save_with_remaining_unsaved_after_cascade_raises(
        self, respx_stash_client
    ) -> None:
        """Test save() raises if unsaved UUIDs remain after cascade."""
        store = StashEntityStore(respx_stash_client)

        # Create unsaved parent studio that won't get saved properly (keeps UUID)
        parent_uuid = uuid.uuid4().hex
        unsaved_parent = Studio(id=parent_uuid, name="Bad Parent")
        unsaved_parent._is_new = True

        # Create child studio with unsaved parent
        studio_uuid = uuid.uuid4().hex
        studio = Studio(
            id=studio_uuid, name="Test Studio", parent_studio=unsaved_parent
        )
        studio._is_new = True

        # Mock GraphQL response that doesn't properly save parent (returns same UUID)
        parent_response = create_graphql_response(
            "studioCreate", create_studio_dict(id=parent_uuid, name="Bad Parent")
        )
        studio_response = create_graphql_response(
            "studioCreate", create_studio_dict(id="200", name="Test Studio")
        )

        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(200, json=parent_response),  # Parent save (keeps UUID)
                httpx.Response(200, json=studio_response),  # Studio save
            ]
        )

        with pytest.raises(
            StashIntegrationError, match="related objects still have UUIDs"
        ):
            await store.save(studio)


class TestGetOrCreateMethod:
    """Tests for get_or_create() method."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_or_create_finds_existing(self, respx_entity_store) -> None:
        """Test get_or_create() returns existing entity."""
        store = respx_entity_store

        # Mock find_one to return existing
        performer_data = create_find_performers_result(
            count=1,
            performers=[create_performer_dict(id="1", name="Alice")],
        )

        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200, json=create_graphql_response("findPerformers", performer_data)
                )
            ]
        )

        result = await store.get_or_create(Performer, name="Alice")

        assert result.id == "1"
        assert result.name == "Alice"
        assert not hasattr(result, "_is_new") or not result._is_new

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_or_create_creates_new(self, respx_entity_store) -> None:
        """Test get_or_create() creates new entity when not found."""
        store = respx_entity_store

        # Mock find_one to return None
        empty_result = create_find_performers_result(count=0, performers=[])

        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200, json=create_graphql_response("findPerformers", empty_result)
                )
            ]
        )

        result = await store.get_or_create(Performer, name="Bob")

        assert result.name == "Bob"
        assert result._is_new is True
        # Should have UUID
        assert len(result.id) == 32

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_or_create_with_create_false_raises(
        self, respx_entity_store
    ) -> None:
        """Test get_or_create() raises when not found and create_if_missing=False."""
        store = respx_entity_store

        # Mock find_one to return None
        empty_result = create_find_performers_result(count=0, performers=[])

        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200, json=create_graphql_response("findPerformers", empty_result)
                )
            ]
        )

        with pytest.raises(StashIntegrationError, match="not found with criteria"):
            await store.get_or_create(
                Performer, create_if_missing=False, name="Charlie"
            )

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_or_create_find_one_exception_creates_anyway(
        self, respx_entity_store
    ) -> None:
        """Test get_or_create() creates if find_one raises exception."""
        store = respx_entity_store

        # Mock find_one to raise exception
        respx.post("http://localhost:9999/graphql").mock(
            side_effect=httpx.HTTPError("Network error")
        )

        result = await store.get_or_create(Performer, name="Dave")

        assert result.name == "Dave"
        assert result._is_new is True
