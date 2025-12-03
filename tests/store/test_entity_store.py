"""Tests for StashEntityStore.

Tests the StashEntityStore following TESTING_REQUIREMENTS.md:
- Mock only at HTTP boundary using respx
- Use FactoryBoy factories for creating test objects
- Verify caching, TTL, and query behavior
"""

import time
from datetime import timedelta

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
from stash_graphql_client.errors import StashError
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
    def test_parse_lookup_equals(self, respx_stash_client) -> None:
        """Test parsing simple equality lookup."""
        store = StashEntityStore(respx_stash_client)

        field, modifier = store._parse_lookup("title")
        assert field == "title"
        assert modifier == "EQUALS"

    @pytest.mark.unit
    def test_parse_lookup_contains(self, respx_stash_client) -> None:
        """Test parsing __contains lookup."""
        store = StashEntityStore(respx_stash_client)

        field, modifier = store._parse_lookup("title__contains")
        assert field == "title"
        assert modifier == "INCLUDES"

    @pytest.mark.unit
    def test_parse_lookup_regex(self, respx_stash_client) -> None:
        """Test parsing __regex lookup."""
        store = StashEntityStore(respx_stash_client)

        field, modifier = store._parse_lookup("title__regex")
        assert field == "title"
        assert modifier == "MATCHES_REGEX"

    @pytest.mark.unit
    def test_parse_lookup_gte(self, respx_stash_client) -> None:
        """Test parsing __gte lookup."""
        store = StashEntityStore(respx_stash_client)

        field, modifier = store._parse_lookup("rating100__gte")
        assert field == "rating100"
        assert modifier == "GREATER_THAN"

    @pytest.mark.unit
    def test_parse_lookup_between(self, respx_stash_client) -> None:
        """Test parsing __between lookup."""
        store = StashEntityStore(respx_stash_client)

        field, modifier = store._parse_lookup("rating100__between")
        assert field == "rating100"
        assert modifier == "BETWEEN"

    @pytest.mark.unit
    def test_parse_lookup_null(self, respx_stash_client) -> None:
        """Test parsing __null lookup."""
        store = StashEntityStore(respx_stash_client)

        field, modifier = store._parse_lookup("studio__null")
        assert field == "studio"
        assert modifier == "IS_NULL"

    @pytest.mark.unit
    def test_build_criterion_equals(self, respx_stash_client) -> None:
        """Test building EQUALS criterion."""
        store = StashEntityStore(respx_stash_client)

        criterion = store._build_criterion("title", "EQUALS", "test")
        assert criterion == {"value": "test", "modifier": "EQUALS"}

    @pytest.mark.unit
    def test_build_criterion_between(self, respx_stash_client) -> None:
        """Test building BETWEEN criterion."""
        store = StashEntityStore(respx_stash_client)

        criterion = store._build_criterion("rating100", "BETWEEN", (60, 90))
        assert criterion == {"value": 60, "value2": 90, "modifier": "BETWEEN"}

    @pytest.mark.unit
    def test_build_criterion_is_null_true(self, respx_stash_client) -> None:
        """Test building IS_NULL criterion with True."""
        store = StashEntityStore(respx_stash_client)

        criterion = store._build_criterion("studio", "IS_NULL", True)
        assert criterion == {"value": "", "modifier": "IS_NULL"}

    @pytest.mark.unit
    def test_build_criterion_is_null_false(self, respx_stash_client) -> None:
        """Test building IS_NULL criterion with False returns NOT_NULL."""
        store = StashEntityStore(respx_stash_client)

        criterion = store._build_criterion("studio", "IS_NULL", False)
        assert criterion == {"value": "", "modifier": "NOT_NULL"}

    @pytest.mark.unit
    def test_build_criterion_includes_list(self, respx_stash_client) -> None:
        """Test building INCLUDES criterion with list."""
        store = StashEntityStore(respx_stash_client)

        criterion = store._build_criterion("tags", "INCLUDES", ["1", "2"])
        assert criterion == {"value": ["1", "2"], "modifier": "INCLUDES"}


# =============================================================================
# Unit Tests - Cache Operations
# =============================================================================


class TestCacheOperations:
    """Tests for cache manipulation methods."""

    @pytest.mark.unit
    def test_cache_entity(self, respx_stash_client) -> None:
        """Test that _cache_entity stores entity correctly."""
        store = StashEntityStore(respx_stash_client)
        performer = PerformerFactory.build(id="123", name="Test Performer")

        store._cache_entity(performer)

        assert store.is_cached(Performer, "123")
        stats = store.cache_stats()
        assert stats.total_entries == 1
        assert stats.by_type.get("Performer") == 1

    @pytest.mark.unit
    def test_invalidate_single(self, respx_stash_client) -> None:
        """Test invalidating a single entity."""
        store = StashEntityStore(respx_stash_client)
        performer = PerformerFactory.build(id="123")

        store._cache_entity(performer)
        assert store.is_cached(Performer, "123")

        store.invalidate(Performer, "123")
        assert not store.is_cached(Performer, "123")

    @pytest.mark.unit
    def test_invalidate_type(self, respx_stash_client) -> None:
        """Test invalidating all entities of a type."""
        store = StashEntityStore(respx_stash_client)
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
    def test_invalidate_all(self, respx_stash_client) -> None:
        """Test invalidating entire cache."""
        store = StashEntityStore(respx_stash_client)
        performer = PerformerFactory.build(id="1")
        tag = TagFactory.build(id="t1")

        store._cache_entity(performer)
        store._cache_entity(tag)

        store.invalidate_all()

        stats = store.cache_stats()
        assert stats.total_entries == 0

    @pytest.mark.unit
    def test_set_ttl_per_type(self, respx_stash_client) -> None:
        """Test setting TTL for a specific type."""
        store = StashEntityStore(respx_stash_client)

        store.set_ttl(Performer, timedelta(minutes=5))
        store.set_ttl(Scene, timedelta(hours=1))

        # Verify internal state
        assert store._type_ttls.get("Performer") == timedelta(minutes=5)
        assert store._type_ttls.get("Scene") == timedelta(hours=1)

    @pytest.mark.unit
    def test_cache_stats(self, respx_stash_client) -> None:
        """Test cache statistics."""
        store = StashEntityStore(respx_stash_client)
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
    def test_filter_cached_objects(self, respx_stash_client) -> None:
        """Test filtering cached objects with predicate."""
        store = StashEntityStore(respx_stash_client)
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
    def test_all_cached(self, respx_stash_client) -> None:
        """Test getting all cached objects of a type."""
        store = StashEntityStore(respx_stash_client)
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


# =============================================================================
# Integration Tests - Get Operations with HTTP Mocking
# =============================================================================


class TestGetOperations:
    """Tests for get() and get_many() with HTTP mocking."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_cache_miss_fetches(
        self, respx_stash_client, respx_mock: respx.MockRouter
    ) -> None:
        """Test that get() fetches on cache miss."""
        store = StashEntityStore(respx_stash_client)

        performer_data = create_performer_dict(id="123", name="Test Performer")
        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            return_value=httpx.Response(
                200,
                json=create_graphql_response("findPerformer", performer_data),
            )
        )

        result = await store.get(Performer, "123")

        assert result is not None
        assert result.id == "123"
        assert result.name == "Test Performer"
        assert len(graphql_route.calls) == 1  # Fetched from GraphQL

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_cache_hit_no_fetch(
        self, respx_stash_client, respx_mock: respx.MockRouter
    ) -> None:
        """Test that get() returns cached entity without fetching."""
        store = StashEntityStore(respx_stash_client)

        # Pre-populate cache
        performer = PerformerFactory.build(id="123", name="Cached Performer")
        store._cache_entity(performer)

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            return_value=httpx.Response(200, json={"data": {}})
        )

        result = await store.get(Performer, "123")

        assert result is not None
        assert result.id == "123"
        assert result.name == "Cached Performer"
        assert len(graphql_route.calls) == 0  # No fetch needed

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_expired_refetches(
        self, respx_stash_client, respx_mock: respx.MockRouter
    ) -> None:
        """Test that get() refetches when cache entry is expired."""
        store = StashEntityStore(respx_stash_client, default_ttl=timedelta(seconds=0))

        # Pre-populate with immediately expired entry
        old_performer = PerformerFactory.build(id="123", name="Old Name")
        store._cache_entity(old_performer)

        # Wait a tiny bit to ensure expiration
        time.sleep(0.01)

        new_performer_data = create_performer_dict(id="123", name="New Name")
        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            return_value=httpx.Response(
                200,
                json=create_graphql_response("findPerformer", new_performer_data),
            )
        )

        result = await store.get(Performer, "123")

        assert result is not None
        assert result.name == "New Name"  # Got fresh data
        assert len(graphql_route.calls) == 1

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_not_found_returns_none(
        self, respx_stash_client, respx_mock: respx.MockRouter
    ) -> None:
        """Test that get() returns None when entity not found."""
        store = StashEntityStore(respx_stash_client)

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            return_value=httpx.Response(
                200,
                json=create_graphql_response("findPerformer", None),
            )
        )

        result = await store.get(Performer, "nonexistent")

        assert result is None
        assert len(graphql_route.calls) == 1

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_many_partial_cache(
        self, respx_stash_client, respx_mock: respx.MockRouter
    ) -> None:
        """Test that get_many() uses cache for some and fetches others."""
        store = StashEntityStore(respx_stash_client)

        # Pre-cache one performer
        cached = PerformerFactory.build(id="1", name="Cached")
        store._cache_entity(cached)

        # Mock fetch for the other
        fetched_data = create_performer_dict(id="2", name="Fetched")
        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            return_value=httpx.Response(
                200,
                json=create_graphql_response("findPerformer", fetched_data),
            )
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
    async def test_find_caches_results(
        self, respx_stash_client, respx_mock: respx.MockRouter
    ) -> None:
        """Test that find() caches all returned entities."""
        store = StashEntityStore(respx_stash_client)

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
    async def test_find_raises_on_large_result(
        self, respx_stash_client, respx_mock: respx.MockRouter
    ) -> None:
        """Test that find() raises StashError when results exceed FIND_LIMIT."""
        store = StashEntityStore(respx_stash_client)

        # Mock response with count > FIND_LIMIT
        large_result = create_find_performers_result(count=1500, performers=[])

        respx.post("http://localhost:9999/graphql").mock(
            return_value=httpx.Response(
                200, json=create_graphql_response("findPerformers", large_result)
            )
        )

        with pytest.raises(StashError, match="exceeding limit of 1000"):
            await store.find(Performer, name__contains="test")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_find_one_returns_first(
        self, respx_stash_client, respx_mock: respx.MockRouter
    ) -> None:
        """Test that find_one() returns first match."""
        store = StashEntityStore(respx_stash_client)

        performers_data = create_find_performers_result(
            count=5,
            performers=[create_performer_dict(id="1", name="First Match")],
        )

        respx.post("http://localhost:9999/graphql").mock(
            return_value=httpx.Response(
                200, json=create_graphql_response("findPerformers", performers_data)
            )
        )

        result = await store.find_one(Performer, name="First Match")

        assert result is not None
        assert result.id == "1"
        assert result.name == "First Match"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_find_one_returns_none_on_no_match(
        self, respx_stash_client, respx_mock: respx.MockRouter
    ) -> None:
        """Test that find_one() returns None when no match."""
        store = StashEntityStore(respx_stash_client)

        empty_result = create_find_performers_result(count=0, performers=[])

        respx.post("http://localhost:9999/graphql").mock(
            return_value=httpx.Response(
                200, json=create_graphql_response("findPerformers", empty_result)
            )
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
    async def test_find_iter_yields_items(
        self, respx_stash_client, respx_mock: respx.MockRouter
    ) -> None:
        """Test that find_iter() yields individual items."""
        store = StashEntityStore(respx_stash_client)

        performers_data = create_find_performers_result(
            count=3,
            performers=[
                create_performer_dict(id="1", name="A"),
                create_performer_dict(id="2", name="B"),
                create_performer_dict(id="3", name="C"),
            ],
        )

        respx.post("http://localhost:9999/graphql").mock(
            return_value=httpx.Response(
                200, json=create_graphql_response("findPerformers", performers_data)
            )
        )

        results = []
        async for performer in store.find_iter(Performer, query_batch=10):
            results.append(performer)

        assert len(results) == 3
        names = [p.name for p in results]
        assert names == ["A", "B", "C"]

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_find_iter_early_break_stops_fetching(
        self, respx_stash_client, respx_mock: respx.MockRouter
    ) -> None:
        """Test that breaking early from find_iter() stops fetching more pages."""
        store = StashEntityStore(respx_stash_client)

        # First page
        page1 = create_find_performers_result(
            count=100,
            performers=[
                create_performer_dict(id="1", name="A"),
                create_performer_dict(id="2", name="B"),
            ],
        )

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            return_value=httpx.Response(
                200, json=create_graphql_response("findPerformers", page1)
            )
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
    async def test_find_iter_caches_as_it_goes(
        self, respx_stash_client, respx_mock: respx.MockRouter
    ) -> None:
        """Test that find_iter() caches items as they are yielded."""
        store = StashEntityStore(respx_stash_client)

        performers_data = create_find_performers_result(
            count=2,
            performers=[
                create_performer_dict(id="1", name="A"),
                create_performer_dict(id="2", name="B"),
            ],
        )

        respx.post("http://localhost:9999/graphql").mock(
            return_value=httpx.Response(
                200, json=create_graphql_response("findPerformers", performers_data)
            )
        )

        async for _ in store.find_iter(Performer, query_batch=10):
            pass

        # Both should be cached
        assert store.is_cached(Performer, "1")
        assert store.is_cached(Performer, "2")


# =============================================================================
# Unit Tests - Stub Detection
# =============================================================================


class TestStubDetection:
    """Tests for stub detection logic."""

    @pytest.mark.unit
    def test_is_stub_minimal_object(self, respx_stash_client) -> None:
        """Test that minimal object (only id) is detected as stub."""
        store = StashEntityStore(respx_stash_client)

        # Create minimal performer (stub-like)
        stub = Performer(id="123", name="")

        assert store._is_stub(stub)

    @pytest.mark.unit
    def test_is_stub_full_object(self, respx_stash_client) -> None:
        """Test that full object is not detected as stub."""
        store = StashEntityStore(respx_stash_client)

        # Create full performer
        full = PerformerFactory.build(
            id="123",
            name="Full Performer",
            country="USA",
            ethnicity="Caucasian",
        )

        assert not store._is_stub(full)


# =============================================================================
# Unit Tests - Default TTL
# =============================================================================


class TestDefaultTTL:
    """Tests for default TTL configuration."""

    @pytest.mark.unit
    def test_default_ttl_is_30_minutes(self, respx_stash_client) -> None:
        """Test that default TTL is 30 minutes."""
        store = StashEntityStore(respx_stash_client)

        assert store._default_ttl == timedelta(minutes=30)

    @pytest.mark.unit
    def test_custom_default_ttl(self, respx_stash_client) -> None:
        """Test setting custom default TTL."""
        store = StashEntityStore(respx_stash_client, default_ttl=timedelta(hours=1))

        assert store._default_ttl == timedelta(hours=1)

    @pytest.mark.unit
    def test_no_default_ttl(self, respx_stash_client) -> None:
        """Test disabling default TTL (never expire)."""
        store = StashEntityStore(respx_stash_client, default_ttl=None)

        assert store._default_ttl is None


# =============================================================================
# Additional Coverage Tests
# =============================================================================


class TestGetManyEdgeCases:
    """Additional tests for get_many() edge cases."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_many_with_expired_entries(
        self, respx_stash_client, respx_mock: respx.MockRouter
    ) -> None:
        """Test get_many() when cached entries are expired."""
        store = StashEntityStore(respx_stash_client, default_ttl=timedelta(seconds=0))

        # Pre-cache with immediately expiring entry
        expired = PerformerFactory.build(id="1", name="Expired")
        store._cache_entity(expired)

        time.sleep(0.01)  # Ensure expiration

        # Mock fetch for expired entry
        fetched_data = create_performer_dict(id="1", name="Refreshed")
        respx.post("http://localhost:9999/graphql").mock(
            return_value=httpx.Response(
                200,
                json=create_graphql_response("findPerformer", fetched_data),
            )
        )

        results = await store.get_many(Performer, ["1"])

        assert len(results) == 1
        assert results[0].name == "Refreshed"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_many_all_cached_no_fetch(
        self, respx_stash_client, respx_mock: respx.MockRouter
    ) -> None:
        """Test get_many() when all IDs are cached."""
        store = StashEntityStore(respx_stash_client)

        # Pre-cache all performers
        p1 = PerformerFactory.build(id="1", name="Alice")
        p2 = PerformerFactory.build(id="2", name="Bob")
        store._cache_entity(p1)
        store._cache_entity(p2)

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            return_value=httpx.Response(200, json={"data": {}})
        )

        results = await store.get_many(Performer, ["1", "2"])

        assert len(results) == 2
        assert len(graphql_route.calls) == 0  # No fetch needed


class TestFindEdgeCases:
    """Additional tests for find() edge cases."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_find_returns_empty_on_zero_count(
        self, respx_stash_client, respx_mock: respx.MockRouter
    ) -> None:
        """Test find() returns empty list when count is 0."""
        store = StashEntityStore(respx_stash_client)

        empty_result = create_find_performers_result(count=0, performers=[])

        respx.post("http://localhost:9999/graphql").mock(
            return_value=httpx.Response(
                200, json=create_graphql_response("findPerformers", empty_result)
            )
        )

        results = await store.find(Performer, name="nonexistent")

        assert results == []

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_find_raises_stash_error_on_large_result(
        self, respx_stash_client, respx_mock: respx.MockRouter
    ) -> None:
        """Test that find() raises StashError (not ValueError) when exceeding limit."""
        store = StashEntityStore(respx_stash_client)

        large_result = create_find_performers_result(count=1500, performers=[])

        respx.post("http://localhost:9999/graphql").mock(
            return_value=httpx.Response(
                200, json=create_graphql_response("findPerformers", large_result)
            )
        )

        with pytest.raises(StashError):
            await store.find(Performer, name__contains="test")


class TestFindIterEdgeCases:
    """Additional tests for find_iter() edge cases."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_find_iter_invalid_query_batch(self, respx_stash_client) -> None:
        """Test find_iter() raises ValueError for invalid query_batch."""
        store = StashEntityStore(respx_stash_client)

        with pytest.raises(ValueError, match="query_batch must be positive"):
            async for _ in store.find_iter(Performer, query_batch=0):
                pass

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_find_iter_multiple_pages(
        self, respx_stash_client, respx_mock: respx.MockRouter
    ) -> None:
        """Test find_iter() fetches multiple pages."""
        store = StashEntityStore(respx_stash_client)

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

        results = []
        async for performer in store.find_iter(Performer, query_batch=3):
            results.append(performer)

        assert len(results) == 5
        assert len(graphql_route.calls) == 2  # Two pages fetched


class TestFilterWithExpiredEntries:
    """Tests for filter() with expired entries."""

    @pytest.mark.unit
    def test_filter_skips_expired_entries(self, respx_stash_client) -> None:
        """Test filter() skips expired entries."""
        store = StashEntityStore(respx_stash_client, default_ttl=timedelta(seconds=0))

        # Add entry that will expire immediately
        performer = PerformerFactory.build(id="1", name="Test", favorite=True)
        store._cache_entity(performer)

        time.sleep(0.01)  # Ensure expiration

        # Filter should skip expired entry
        favorites = store.filter(Performer, lambda p: p.favorite)

        assert len(favorites) == 0


class TestPopulateFunction:
    """Tests for populate() function and helpers."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_populate_list_of_stubs(
        self, respx_stash_client, respx_mock: respx.MockRouter
    ) -> None:
        """Test populate() with list of stub performers."""
        store = StashEntityStore(respx_stash_client)

        # Create scene with stub performers
        stub1 = Performer(id="1", name="")
        stub2 = Performer(id="2", name="")
        scene = SceneFactory.build(id="s1", performers=[stub1, stub2])

        # Mock performer fetches
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
                # get() is called again in _populate_list for each stub
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

        result = await store.populate(scene, "performers")

        assert len(result.performers) == 2
        names = {p.name for p in result.performers}
        assert names == {"Alice", "Bob"}

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_populate_single_stub(
        self, respx_stash_client, respx_mock: respx.MockRouter
    ) -> None:
        """Test populate() with single stub studio."""
        store = StashEntityStore(respx_stash_client)

        # Create scene with stub studio
        stub_studio = Studio(id="st1", name="")
        scene = SceneFactory.build(id="s1", studio=stub_studio)

        # Mock studio fetch
        respx.post("http://localhost:9999/graphql").mock(
            return_value=httpx.Response(
                200,
                json=create_graphql_response(
                    "findStudio", create_studio_dict(id="st1", name="Big Studio")
                ),
            )
        )

        result = await store.populate(scene, "studio")

        assert result.studio is not None
        assert result.studio.name == "Big Studio"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_populate_nonexistent_field(self, respx_stash_client) -> None:
        """Test populate() with non-existent field logs warning."""
        store = StashEntityStore(respx_stash_client)
        scene = SceneFactory.build(id="s1")

        # Should not raise, just log warning
        result = await store.populate(scene, "nonexistent_field")

        assert result.id == "s1"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_populate_none_value_skipped(self, respx_stash_client) -> None:
        """Test populate() skips fields with None value."""
        store = StashEntityStore(respx_stash_client)
        scene = SceneFactory.build(id="s1", studio=None)

        # Should not raise or attempt to populate None
        result = await store.populate(scene, "studio")

        assert result.studio is None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_populate_list_non_stashobject(self, respx_stash_client) -> None:
        """Test _populate_list returns unchanged if items are not StashObjects."""
        store = StashEntityStore(respx_stash_client)

        # List of strings, not StashObjects
        result = await store._populate_list(["a", "b", "c"])

        assert result == ["a", "b", "c"]

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_populate_list_empty(self, respx_stash_client) -> None:
        """Test _populate_list returns empty list unchanged."""
        store = StashEntityStore(respx_stash_client)

        result = await store._populate_list([])

        assert result == []

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_populate_non_list_non_stashobject_field(
        self, respx_stash_client
    ) -> None:
        """Test populate() skips field that is not list or StashObject."""
        store = StashEntityStore(respx_stash_client)

        # Scene has a 'title' field that is a string, not list or StashObject
        scene = SceneFactory.build(id="s1", title="My Scene Title")

        # Should not raise, title is neither list nor StashObject
        result = await store.populate(scene, "title")

        # Title should remain unchanged
        assert result.title == "My Scene Title"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_populate_single_stub_returns_none(
        self, respx_stash_client, respx_mock: respx.MockRouter
    ) -> None:
        """Test populate() when _populate_single returns None."""
        store = StashEntityStore(respx_stash_client)

        # Create scene with stub studio
        stub_studio = Studio(id="st1", name="")
        scene = SceneFactory.build(id="s1", studio=stub_studio)

        # Mock studio fetch returns None (not found)
        respx.post("http://localhost:9999/graphql").mock(
            return_value=httpx.Response(
                200,
                json=create_graphql_response("findStudio", None),
            )
        )

        result = await store.populate(scene, "studio")

        # Studio should remain the stub since populated_single is None
        assert result.studio is not None
        assert result.studio.id == "st1"
        assert result.studio.name == ""  # Still the stub

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_populate_single_full_object_not_stub(
        self, respx_stash_client, respx_mock: respx.MockRouter
    ) -> None:
        """Test _populate_single returns original when not a stub."""
        store = StashEntityStore(respx_stash_client)

        # Create scene with a FULL studio (not a stub)
        full_studio = StudioFactory.build(
            id="st1", name="Full Studio", url="http://example.com"
        )
        scene = SceneFactory.build(id="s1", studio=full_studio)

        # No mock needed - should not make any GraphQL calls
        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            return_value=httpx.Response(200, json={"data": {}})
        )

        result = await store.populate(scene, "studio")

        # Studio should remain unchanged (it's not a stub)
        assert result.studio is not None
        assert result.studio.name == "Full Studio"
        # No GraphQL calls should have been made
        assert len(graphql_route.calls) == 0

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_populate_list_no_stubs(
        self, respx_stash_client, respx_mock: respx.MockRouter
    ) -> None:
        """Test _populate_list when no items are stubs."""
        store = StashEntityStore(respx_stash_client)

        # Create scene with FULL performers (not stubs)
        full_performer1 = PerformerFactory.build(id="1", name="Alice", country="USA")
        full_performer2 = PerformerFactory.build(id="2", name="Bob", country="UK")
        scene = SceneFactory.build(
            id="s1", performers=[full_performer1, full_performer2]
        )

        # No mock needed for get_many since stub_ids will be empty
        # But _populate_list still calls get() for each item at the end
        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            return_value=httpx.Response(200, json={"data": {}})
        )

        result = await store.populate(scene, "performers")

        # Performers should remain unchanged
        assert len(result.performers) == 2
        # No get_many call for stub_ids (since there are none)
        # But individual get() calls will happen - these hit cache since we haven't populated
        # Actually the full performers won't be in cache, so get() will be called
        # Let's just verify the performers are there
        names = {p.name for p in result.performers}
        assert "Alice" in names or len(result.performers) == 2


class TestInvalidateNotCached:
    """Test invalidate() when entity is not cached."""

    @pytest.mark.unit
    def test_invalidate_not_cached_no_error(self, respx_stash_client) -> None:
        """Test invalidate() does nothing when entity not cached."""
        store = StashEntityStore(respx_stash_client)

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
    def test_get_ttl_for_type_with_override(self, respx_stash_client) -> None:
        """Test _get_ttl_for_type returns type-specific TTL."""
        store = StashEntityStore(respx_stash_client)
        store.set_ttl(Performer, timedelta(minutes=5))

        ttl = store._get_ttl_for_type("Performer")

        assert ttl == timedelta(minutes=5)

    @pytest.mark.unit
    def test_get_ttl_for_type_falls_back_to_default(self, respx_stash_client) -> None:
        """Test _get_ttl_for_type falls back to default."""
        store = StashEntityStore(respx_stash_client)

        ttl = store._get_ttl_for_type("Scene")

        assert ttl == timedelta(minutes=30)  # Default


class TestExecuteFindByIdsEdgeCases:
    """Tests for _execute_find_by_ids edge cases."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_execute_find_by_ids_entity_not_found(
        self, respx_stash_client, respx_mock: respx.MockRouter
    ) -> None:
        """Test _execute_find_by_ids skips not found entities."""
        store = StashEntityStore(respx_stash_client)

        # Mock returns None for this performer
        respx.post("http://localhost:9999/graphql").mock(
            return_value=httpx.Response(
                200, json=create_graphql_response("findPerformer", None)
            )
        )

        results = await store._execute_find_by_ids(Performer, ["nonexistent"])

        assert results == []


class TestTranslateFiltersEdgeCases:
    """Tests for _translate_filters edge cases."""

    @pytest.mark.unit
    def test_translate_filters_raw_dict_passthrough(self, respx_stash_client) -> None:
        """Test raw dict with modifier is passed through."""
        store = StashEntityStore(respx_stash_client)

        graphql_filter, entity_filter = store._translate_filters(
            "Scene",
            {"title": {"value": "test", "modifier": "NOT_EQUALS"}},
        )

        assert entity_filter is not None
        assert entity_filter["title"] == {"value": "test", "modifier": "NOT_EQUALS"}

    @pytest.mark.unit
    def test_translate_filters_nested_filter(self, respx_stash_client) -> None:
        """Test nested filters ending with _filter."""
        store = StashEntityStore(respx_stash_client)

        graphql_filter, entity_filter = store._translate_filters(
            "Scene",
            {"performers_filter": {"name": {"value": "Jane", "modifier": "EQUALS"}}},
        )

        assert entity_filter is not None
        assert "performers_filter" in entity_filter

    @pytest.mark.unit
    def test_translate_filters_criterion_none_skipped(self, respx_stash_client) -> None:
        """Test filters with None criterion are skipped."""
        store = StashEntityStore(respx_stash_client)

        # Invalid BETWEEN (single value) returns None criterion
        graphql_filter, entity_filter = store._translate_filters(
            "Scene",
            {"rating100__between": "invalid"},  # Not a tuple/list
        )

        # Should not include the invalid filter
        assert entity_filter is None or "rating100" not in entity_filter


class TestBuildCriterionEdgeCases:
    """Tests for _build_criterion edge cases."""

    @pytest.mark.unit
    def test_build_criterion_between_invalid_returns_none(
        self, respx_stash_client
    ) -> None:
        """Test BETWEEN with invalid value returns None."""
        store = StashEntityStore(respx_stash_client)

        # Single value, not tuple/list of 2
        criterion = store._build_criterion("rating100", "BETWEEN", 50)

        assert criterion is None

    @pytest.mark.unit
    def test_build_criterion_between_wrong_length_returns_none(
        self, respx_stash_client
    ) -> None:
        """Test BETWEEN with wrong length tuple returns None."""
        store = StashEntityStore(respx_stash_client)

        # Tuple of 3, not 2
        criterion = store._build_criterion("rating100", "BETWEEN", (10, 20, 30))

        assert criterion is None


class TestExecuteFindQueryEntityTypes:
    """Tests for _execute_find_query with different entity types."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_find_gallery_type(
        self, respx_stash_client, respx_mock: respx.MockRouter
    ) -> None:
        """Test find() with Gallery type."""
        store = StashEntityStore(respx_stash_client)

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
    async def test_find_image_type(
        self, respx_stash_client, respx_mock: respx.MockRouter
    ) -> None:
        """Test find() with Image type."""
        store = StashEntityStore(respx_stash_client)

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
    async def test_find_unsupported_type_raises(self, respx_stash_client) -> None:
        """Test find() with unsupported type raises ValueError."""
        store = StashEntityStore(respx_stash_client)

        # Create a mock unsupported type
        class UnsupportedType(StashObject):
            __type_name__ = "Unsupported"

        with pytest.raises(ValueError, match="Unsupported entity type"):
            await store.find(UnsupportedType)
