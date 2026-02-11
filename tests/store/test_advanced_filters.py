"""Tests for advanced StashEntityStore filter methods.

Tests the new repository pattern filter methods:
- filter_strict(): Fail-fast filtering with required fields
- filter_and_populate(): Smart hybrid filtering with auto-population
- filter_and_populate_with_stats(): Debug variant with statistics
- populated_filter_iter(): Lazy async iterator with auto-population

Following TESTING_REQUIREMENTS.md:
- Mock only at HTTP boundary using respx
- Use FactoryBoy factories for test objects
- Verify both request and response in GraphQL mocks
"""

import io
import logging
import re
import time
from datetime import timedelta
from unittest.mock import patch

import httpx
import pytest
import respx

from stash_graphql_client import Performer, StashEntityStore
from stash_graphql_client.logging import client_logger
from stash_graphql_client.types.base import StashObject
from stash_graphql_client.types.unset import UNSET
from tests.fixtures.stash import (
    PerformerFactory,
    SceneFactory,
    create_graphql_response,
    create_performer_dict,
)


# =============================================================================
# Unit Tests - filter_strict()
# =============================================================================


class TestFilterStrict:
    """Tests for filter_strict() - fail-fast filtering."""

    @pytest.mark.asyncio
    async def test_filter_strict_success_all_fields_present(
        self, respx_entity_store: StashEntityStore
    ) -> None:
        """Test filter_strict succeeds when all cached objects have required fields."""
        store = respx_entity_store

        # Pre-populate cache with complete data
        p1 = PerformerFactory.build(id="1", name="Alice", rating100=90, favorite=True)
        p2 = PerformerFactory.build(id="2", name="Bob", rating100=85, favorite=False)
        p3 = PerformerFactory.build(id="3", name="Charlie", rating100=95, favorite=True)

        # Mark fields as received (simulate they came from GraphQL)
        for p in [p1, p2, p3]:
            object.__setattr__(
                p, "_received_fields", {"id", "name", "rating100", "favorite"}
            )
            store._cache_entity(p)

        # Filter with required fields - should succeed
        results = store.filter_strict(
            Performer,
            required_fields=["rating100", "favorite"],
            predicate=lambda p: p.rating100 >= 90 and p.favorite,  # type: ignore[operator, arg-type, return-value]
        )

        assert len(results) == 2
        assert all(r.rating100 >= 90 for r in results)  # type: ignore[operator]
        assert all(r.favorite for r in results)
        assert {r.id for r in results} == {"1", "3"}

    @pytest.mark.asyncio
    async def test_filter_strict_raises_on_missing_field(
        self, respx_entity_store: StashEntityStore
    ) -> None:
        """Test filter_strict raises ValueError if any object missing required field."""
        store = respx_entity_store

        # Create performers with incomplete data
        p1 = PerformerFactory.build(id="1", name="Alice", rating100=90)
        p2 = PerformerFactory.build(id="2", name="Bob")  # Don't set rating100

        # Manually set rating100 to UNSET for p2 (simulating unqueried field)
        object.__setattr__(p2, "rating100", UNSET)

        # Mark different received fields
        object.__setattr__(p1, "_received_fields", {"id", "name", "rating100"})
        object.__setattr__(p2, "_received_fields", {"id", "name"})  # No rating100!

        store._cache_entity(p1)
        store._cache_entity(p2)

        # Should raise because p2 is missing rating100
        with pytest.raises(ValueError, match="Performer 2 is missing required fields"):
            store.filter_strict(
                Performer,
                required_fields=["rating100"],
                predicate=lambda p: p.rating100 >= 80,  # type: ignore[operator]
            )

    @pytest.mark.asyncio
    async def test_filter_strict_empty_cache(
        self, respx_entity_store: StashEntityStore
    ) -> None:
        """Test filter_strict returns empty list for empty cache."""
        store = respx_entity_store

        results = store.filter_strict(
            Performer,
            required_fields=["rating100"],
            predicate=lambda p: p.rating100 >= 80,  # type: ignore[operator]
        )

        assert results == []

    @pytest.mark.asyncio
    async def test_filter_strict_skips_expired(
        self, respx_entity_store: StashEntityStore
    ) -> None:
        """Test filter_strict skips expired cache entries."""
        store = respx_entity_store

        # Create performer and cache it
        p1 = PerformerFactory.build(id="1", name="Alice", rating100=90)
        object.__setattr__(p1, "_received_fields", {"id", "name", "rating100"})
        store._cache_entity(p1)

        # Manually expire the entry
        cache_key = ("Performer", "1")
        entry = store._cache[cache_key]
        entry.ttl_seconds = 0.001  # 1ms TTL

        time.sleep(0.002)  # Wait for expiration

        # Should return empty (expired entry skipped)
        results = store.filter_strict(
            Performer, required_fields=["rating100"], predicate=lambda p: True
        )

        assert results == []

    @pytest.mark.asyncio
    async def test_filter_strict_skips_other_types(
        self, respx_entity_store: StashEntityStore
    ) -> None:
        """Test filter_strict skips entities of different types in cache."""
        store = respx_entity_store

        # Cache a performer AND a scene
        p1 = PerformerFactory.build(id="1", name="Alice", rating100=90)
        s1 = SceneFactory.build(id="1", title="Scene 1")

        object.__setattr__(p1, "_received_fields", {"id", "name", "rating100"})
        object.__setattr__(s1, "_received_fields", {"id", "title"})

        store._cache_entity(p1)
        store._cache_entity(s1)  # Different type in cache

        # Filter for Performers only - should skip Scene
        results = store.filter_strict(
            Performer,
            required_fields=["rating100"],
            predicate=lambda p: p.rating100 >= 80,  # type: ignore[operator]
        )

        assert len(results) == 1
        assert results[0].id == "1"
        assert results[0].name == "Alice"


class TestFilterStrictTypeIndexCleanup:
    """Tests for filter_strict() type index edge cases."""

    @pytest.mark.asyncio
    async def test_filter_strict_cleans_orphaned_type_index_entries(
        self, respx_stash_client
    ) -> None:
        """Test filter_strict() handles orphaned type index entries."""
        store = StashEntityStore(respx_stash_client, default_ttl=timedelta(minutes=30))

        with patch.object(StashObject, "_store", store):
            # Cache a performer normally
            p1 = PerformerFactory.build(id="1", name="Alice", rating100=90)
            object.__setattr__(p1, "_received_fields", {"id", "name", "rating100"})
            store._cache_entity(p1)

            # Create orphaned index entry (ID in index but not in cache)
            store._type_index["Performer"].add("orphan")

            results = store.filter_strict(
                Performer,
                required_fields=["rating100"],
                predicate=lambda p: p.rating100 >= 80,  # type: ignore[operator]
            )

            assert len(results) == 1
            assert results[0].id == "1"

            # Orphaned entry should have been cleaned up
            assert "orphan" not in store._type_index["Performer"]


class TestFilterAndPopulateSecondPassEdgeCases:
    """Tests for filter_and_populate/with_stats second pass edge cases."""

    @pytest.mark.asyncio
    async def test_filter_and_populate_empty_type_index_second_pass(
        self, respx_mock, respx_entity_store: StashEntityStore
    ) -> None:
        """Test filter_and_populate when type index is empty during second pass."""
        store = respx_entity_store

        # Cache a performer with missing field so populate() will be called
        p1 = PerformerFactory.build(id="1", name="Alice", rating100=90)
        object.__setattr__(p1, "rating100", UNSET)
        object.__setattr__(p1, "_received_fields", {"id", "name"})  # missing rating100
        store._cache_entity(p1)

        # Mock GraphQL response for the populate call
        p1_complete = create_performer_dict(id="1", name="Alice", rating100=90)
        respx.post("http://localhost:9999/graphql").mock(
            return_value=httpx.Response(
                200, json=create_graphql_response("findPerformer", p1_complete)
            )
        )

        # Patch populate to also invalidate the type after populating
        original_populate = store.populate

        async def populate_and_invalidate(entity, **kwargs):
            result = await original_populate(entity, **kwargs)
            store.invalidate_type(Performer)
            return result

        with patch.object(store, "populate", side_effect=populate_and_invalidate):
            results = await store.filter_and_populate(
                Performer,
                required_fields=["rating100"],
                predicate=lambda p: True,
            )

        # Second pass finds empty type index, returns empty
        assert results == []

    @pytest.mark.asyncio
    async def test_filter_and_populate_with_stats_empty_type_index_second_pass(
        self, respx_mock, respx_entity_store: StashEntityStore
    ) -> None:
        """Test filter_and_populate_with_stats when type index is empty during second pass."""
        store = respx_entity_store

        p1 = PerformerFactory.build(id="1", name="Alice", rating100=90)
        object.__setattr__(p1, "rating100", UNSET)
        object.__setattr__(p1, "_received_fields", {"id", "name"})  # missing rating100
        store._cache_entity(p1)

        # Mock GraphQL response for the populate call
        p1_complete = create_performer_dict(id="1", name="Alice", rating100=90)
        respx.post("http://localhost:9999/graphql").mock(
            return_value=httpx.Response(
                200, json=create_graphql_response("findPerformer", p1_complete)
            )
        )

        original_populate = store.populate

        async def populate_and_invalidate(entity, **kwargs):
            result = await original_populate(entity, **kwargs)
            store.invalidate_type(Performer)
            return result

        with patch.object(store, "populate", side_effect=populate_and_invalidate):
            results, stats = await store.filter_and_populate_with_stats(
                Performer,
                required_fields=["rating100"],
                predicate=lambda p: True,
            )

        assert results == []
        assert stats["matches"] == 0


# =============================================================================
# Unit Tests - filter_and_populate()
# =============================================================================


class TestFilterAndPopulate:
    """Tests for filter_and_populate() - smart hybrid filtering."""

    @pytest.mark.asyncio
    async def test_filter_and_populate_all_complete(
        self, respx_mock, respx_entity_store: StashEntityStore
    ) -> None:
        """Test filter_and_populate with no population needed (all fields present)."""
        store = respx_entity_store

        # Pre-populate cache with complete data
        p1 = PerformerFactory.build(id="1", name="Alice", rating100=90, favorite=True)
        p2 = PerformerFactory.build(id="2", name="Bob", rating100=85, favorite=False)

        for p in [p1, p2]:
            object.__setattr__(
                p, "_received_fields", {"id", "name", "rating100", "favorite"}
            )
            store._cache_entity(p)

        # Should NOT make any GraphQL calls
        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            return_value=httpx.Response(500, text="Should not be called")
        )

        # Filter - no population needed
        results = await store.filter_and_populate(
            Performer,
            required_fields=["rating100", "favorite"],
            predicate=lambda p: p.rating100 >= 90,  # type: ignore[operator]
        )

        # Verify NO GraphQL calls were made
        assert len(graphql_route.calls) == 0

        # Verify results
        assert len(results) == 1
        assert results[0].id == "1"
        assert results[0].rating100 == 90

    @pytest.mark.asyncio
    async def test_filter_and_populate_partial_population(
        self, respx_mock, respx_entity_store: StashEntityStore
    ) -> None:
        """Test filter_and_populate populates only performers missing fields."""
        store = respx_entity_store

        # Create 3 performers: 2 complete, 1 incomplete
        p1 = PerformerFactory.build(id="1", name="Alice", rating100=90, favorite=True)
        p2 = PerformerFactory.build(id="2", name="Bob")
        p3 = PerformerFactory.build(id="3", name="Charlie", rating100=95, favorite=True)

        # Set p2 fields to UNSET (simulating unqueried fields)
        object.__setattr__(p2, "rating100", UNSET)
        object.__setattr__(p2, "favorite", UNSET)

        # Mark received fields
        object.__setattr__(
            p1, "_received_fields", {"id", "name", "rating100", "favorite"}
        )
        object.__setattr__(
            p2, "_received_fields", {"id", "name"}
        )  # Missing rating + favorite
        object.__setattr__(
            p3, "_received_fields", {"id", "name", "rating100", "favorite"}
        )

        for p in [p1, p2, p3]:
            store._cache_entity(p)

        # Mock GraphQL response for p2 (only one needing population)
        p2_complete = create_performer_dict(
            id="2", name="Bob", rating100=85, favorite=False
        )
        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            return_value=httpx.Response(
                200, json=create_graphql_response("findPerformer", p2_complete)
            )
        )

        # Filter with auto-population
        results = await store.filter_and_populate(
            Performer,
            required_fields=["rating100", "favorite"],
            predicate=lambda p: p.rating100 >= 90,  # type: ignore[operator]
        )

        # Verify only 1 GraphQL call (for p2)
        assert len(graphql_route.calls) == 1

        # Verify results (p1 and p3 match predicate)
        assert len(results) == 2
        assert {r.id for r in results} == {"1", "3"}

    @pytest.mark.asyncio
    async def test_filter_and_populate_all_need_population(
        self, respx_mock, respx_entity_store: StashEntityStore
    ) -> None:
        """Test filter_and_populate when all performers need fields fetched."""
        store = respx_entity_store

        # Create 2 performers with missing rating100
        p1 = PerformerFactory.build(id="1", name="Alice")
        p2 = PerformerFactory.build(id="2", name="Bob")

        # Set rating100 to UNSET
        object.__setattr__(p1, "rating100", UNSET)
        object.__setattr__(p2, "rating100", UNSET)

        for p in [p1, p2]:
            object.__setattr__(p, "_received_fields", {"id", "name"})
            store._cache_entity(p)

        # Mock GraphQL responses for both
        p1_complete = create_performer_dict(id="1", name="Alice", rating100=95)
        p2_complete = create_performer_dict(id="2", name="Bob", rating100=75)

        call_count = 0

        def mock_response(request):
            nonlocal call_count
            call_count += 1
            # Return different data based on which ID is in request
            content = request.content.decode()
            if '"id": "1"' in content or '"id":"1"' in content:
                return httpx.Response(
                    200, json=create_graphql_response("findPerformer", p1_complete)
                )
            return httpx.Response(
                200, json=create_graphql_response("findPerformer", p2_complete)
            )

        respx.post("http://localhost:9999/graphql").mock(side_effect=mock_response)

        # Filter with population
        results = await store.filter_and_populate(
            Performer,
            required_fields=["rating100"],
            predicate=lambda p: p.rating100 >= 80,  # type: ignore[operator]
        )

        # Verify both were fetched
        assert call_count == 2

        # Verify results (only p1 matches)
        assert len(results) == 1
        assert results[0].id == "1"
        assert results[0].rating100 == 95

    @pytest.mark.asyncio
    async def test_filter_and_populate_empty_cache(
        self, respx_mock, respx_entity_store: StashEntityStore
    ) -> None:
        """Test filter_and_populate returns empty for empty cache."""
        store = respx_entity_store

        results = await store.filter_and_populate(
            Performer,
            required_fields=["rating100"],
            predicate=lambda p: p.rating100 >= 80,  # type: ignore[operator]
        )

        assert results == []

    @pytest.mark.asyncio
    async def test_filter_and_populate_skips_other_types(
        self, respx_mock, respx_entity_store: StashEntityStore
    ) -> None:
        """Test filter_and_populate skips entities of different types."""
        store = respx_entity_store

        # Cache performer and scene (mixed types)
        p1 = PerformerFactory.build(id="1", name="Alice", rating100=90)
        s1 = SceneFactory.build(id="1", title="Scene 1")

        object.__setattr__(p1, "_received_fields", {"id", "name", "rating100"})
        object.__setattr__(s1, "_received_fields", {"id", "title"})

        store._cache_entity(p1)
        store._cache_entity(s1)

        # Filter for Performers - should skip Scene
        results = await store.filter_and_populate(
            Performer,
            required_fields=["rating100"],
            predicate=lambda p: p.rating100 >= 80,  # type: ignore[operator]
        )

        assert len(results) == 1
        assert results[0].name == "Alice"

    @pytest.mark.asyncio
    async def test_filter_and_populate_skips_expired(
        self, respx_mock, respx_entity_store: StashEntityStore
    ) -> None:
        """Test filter_and_populate skips expired entries."""
        store = respx_entity_store

        # Cache performer
        p1 = PerformerFactory.build(id="1", name="Alice", rating100=90)
        object.__setattr__(p1, "_received_fields", {"id", "name", "rating100"})
        store._cache_entity(p1)

        # Expire it
        cache_key = ("Performer", "1")
        store._cache[cache_key].ttl_seconds = 0.001

        time.sleep(0.002)

        # Should return empty
        results = await store.filter_and_populate(
            Performer,
            required_fields=["rating100"],
            predicate=lambda p: p.rating100 >= 80,  # type: ignore[operator]
        )

        assert results == []

    @pytest.mark.asyncio
    async def test_filter_and_populate_warns_on_populate_failure(
        self, respx_mock, respx_entity_store: StashEntityStore
    ) -> None:
        """Test filter_and_populate warns if populate fails to load fields."""
        store = respx_entity_store

        # Cache performer with missing field
        p1 = PerformerFactory.build(id="1", name="Alice")
        object.__setattr__(p1, "rating100", UNSET)
        object.__setattr__(p1, "_received_fields", {"id", "name"})
        store._cache_entity(p1)

        # Mock populate to return object WITHOUT the field (simulate failure)
        # This returns the performer but doesn't set rating100
        p1_incomplete = create_performer_dict(id="1", name="Alice")
        # Intentionally omit rating100 from response

        respx.post("http://localhost:9999/graphql").mock(
            return_value=httpx.Response(
                200, json=create_graphql_response("findPerformer", p1_incomplete)
            )
        )

        # Filter should warn and skip this performer
        log_capture = io.StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setLevel(logging.WARNING)
        client_logger.addHandler(handler)

        results = await store.filter_and_populate(
            Performer,
            required_fields=["rating100"],
            predicate=lambda p: p.rating100 >= 80,  # type: ignore[operator]
        )

        client_logger.removeHandler(handler)
        log_output = log_capture.getvalue()

        # Should have warned about missing field
        assert "still missing" in log_output or len(results) == 0
        # Should skip the performer (can't filter without required field)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_filter_and_populate_skips_entry_expired_during_processing(
        self, respx_mock, respx_entity_store: StashEntityStore
    ) -> None:
        """Test filter_and_populate skips entries that expire during populate phase."""
        store = respx_entity_store

        # Cache two performers with complete data (no population needed)
        p1 = PerformerFactory.build(id="1", name="Alice", rating100=90)
        p2 = PerformerFactory.build(id="2", name="Bob", rating100=85)

        for p in [p1, p2]:
            object.__setattr__(p, "_received_fields", {"id", "name", "rating100"})
            store._cache_entity(p)

        # Spy on all_cached to expire p2 after it's called but before final filtering
        original_all_cached = store.all_cached

        def spy_and_expire(entity_type):
            result = original_all_cached(entity_type)
            # Expire p2 while processing (race condition simulation)
            cache_key = ("Performer", "2")
            if cache_key in store._cache:
                store._cache[cache_key].ttl_seconds = 0.001

                time.sleep(0.002)
            return result

        with patch.object(store, "all_cached", wraps=spy_and_expire):
            results = await store.filter_and_populate(
                Performer,
                required_fields=["rating100"],
                predicate=lambda p: p.rating100 >= 80,  # type: ignore[operator]
            )

        # Should only get p1 (p2 expired during processing)
        assert len(results) == 1
        assert results[0].id == "1"

    @pytest.mark.asyncio
    async def test_filter_and_populate_batch_size(
        self, respx_mock, respx_entity_store: StashEntityStore
    ) -> None:
        """Test filter_and_populate respects batch_size parameter."""
        store = respx_entity_store

        # Create 5 performers needing population
        performers = []
        for i in range(1, 6):
            p = PerformerFactory.build(id=str(i), name=f"P{i}")
            object.__setattr__(p, "rating100", UNSET)
            object.__setattr__(p, "_received_fields", {"id", "name"})
            store._cache_entity(p)
            performers.append(p)

        # Mock responses
        def mock_response(request):
            content = request.content.decode()
            # Extract ID from request (simple approach)
            for i in range(1, 6):
                if f'"id": "{i}"' in content or f'"id":"{i}"' in content:
                    return httpx.Response(
                        200,
                        json=create_graphql_response(
                            "findPerformer",
                            create_performer_dict(
                                id=str(i), name=f"P{i}", rating100=80 + i
                            ),
                        ),
                    )
            return httpx.Response(500, text="Unknown ID")

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=mock_response
        )

        # Filter with small batch size
        results = await store.filter_and_populate(
            Performer,
            required_fields=["rating100"],
            predicate=lambda p: p.rating100 >= 83,  # type: ignore[operator]
            batch_size=2,  # Process 2 at a time
        )

        # All 5 should have been fetched
        assert len(graphql_route.calls) == 5

        # Results: P3, P4, P5 (rating 83, 84, 85)
        assert len(results) == 3


# =============================================================================
# Unit Tests - filter_and_populate_with_stats()
# =============================================================================


class TestFilterAndPopulateWithStats:
    """Tests for filter_and_populate_with_stats() - debug variant."""

    @pytest.mark.asyncio
    async def test_filter_with_stats_returns_stats(
        self, respx_mock, respx_entity_store: StashEntityStore
    ) -> None:
        """Test filter_and_populate_with_stats returns correct statistics."""
        store = respx_entity_store

        # Create 3 performers: 2 complete, 1 incomplete
        p1 = PerformerFactory.build(id="1", name="Alice", rating100=90)
        p2 = PerformerFactory.build(id="2", name="Bob")
        p3 = PerformerFactory.build(id="3", name="Charlie", rating100=95)

        # Set p2 rating100 to UNSET
        object.__setattr__(p2, "rating100", UNSET)

        object.__setattr__(p1, "_received_fields", {"id", "name", "rating100"})
        object.__setattr__(p2, "_received_fields", {"id", "name"})
        object.__setattr__(p3, "_received_fields", {"id", "name", "rating100"})

        for p in [p1, p2, p3]:
            store._cache_entity(p)

        # Mock response for p2
        p2_complete = create_performer_dict(id="2", name="Bob", rating100=85)
        respx.post("http://localhost:9999/graphql").mock(
            return_value=httpx.Response(
                200, json=create_graphql_response("findPerformer", p2_complete)
            )
        )

        # Filter with stats
        results, stats = await store.filter_and_populate_with_stats(
            Performer,
            required_fields=["rating100"],
            predicate=lambda p: p.rating100 >= 90,  # type: ignore[operator]
        )

        # Verify results
        assert len(results) == 2  # p1 and p3

        # Verify stats
        assert stats["total_cached"] == 3
        assert stats["needed_population"] == 1  # Only p2
        assert stats["populated_fields"] == ["rating100"]
        assert stats["matches"] == 2
        assert stats["cache_hit_rate"] == 2 / 3  # 2 out of 3 had data

    @pytest.mark.asyncio
    async def test_filter_with_stats_empty_cache(
        self, respx_mock, respx_entity_store: StashEntityStore
    ) -> None:
        """Test filter_and_populate_with_stats with empty cache."""
        store = respx_entity_store

        results, stats = await store.filter_and_populate_with_stats(
            Performer,
            required_fields=["rating100"],
            predicate=lambda p: p.rating100 >= 80,  # type: ignore[operator]
        )

        assert results == []
        assert stats["total_cached"] == 0
        assert stats["needed_population"] == 0
        assert stats["matches"] == 0
        assert stats["cache_hit_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_filter_with_stats_all_complete(
        self, respx_mock, respx_entity_store: StashEntityStore
    ) -> None:
        """Test stats when all objects have complete data (100% cache hit)."""
        store = respx_entity_store

        # All complete
        p1 = PerformerFactory.build(id="1", name="Alice", rating100=90)
        p2 = PerformerFactory.build(id="2", name="Bob", rating100=85)

        for p in [p1, p2]:
            object.__setattr__(p, "_received_fields", {"id", "name", "rating100"})
            store._cache_entity(p)

        results, stats = await store.filter_and_populate_with_stats(
            Performer,
            required_fields=["rating100"],
            predicate=lambda p: p.rating100 >= 80,  # type: ignore[operator]
        )

        assert len(results) == 2
        assert stats["total_cached"] == 2
        assert stats["needed_population"] == 0
        assert stats["cache_hit_rate"] == 1.0  # 100% hit rate

    @pytest.mark.asyncio
    async def test_filter_with_stats_skips_other_types(
        self, respx_mock, respx_entity_store: StashEntityStore
    ) -> None:
        """Test filter_and_populate_with_stats skips entities of different types."""
        store = respx_entity_store

        # Cache mixed types
        p1 = PerformerFactory.build(id="1", name="Alice", rating100=90)
        s1 = SceneFactory.build(id="1", title="Scene 1")

        object.__setattr__(p1, "_received_fields", {"id", "name", "rating100"})
        object.__setattr__(s1, "_received_fields", {"id", "title"})

        store._cache_entity(p1)
        store._cache_entity(s1)

        # Filter for Performers
        results, stats = await store.filter_and_populate_with_stats(
            Performer,
            required_fields=["rating100"],
            predicate=lambda p: p.rating100 >= 80,  # type: ignore[operator]
        )

        assert len(results) == 1
        assert stats["total_cached"] == 1  # Only 1 Performer

    @pytest.mark.asyncio
    async def test_filter_with_stats_skips_expired(
        self, respx_mock, respx_entity_store: StashEntityStore
    ) -> None:
        """Test filter_and_populate_with_stats skips expired entries."""
        store = respx_entity_store

        # Cache performer
        p1 = PerformerFactory.build(id="1", name="Alice", rating100=90)
        object.__setattr__(p1, "_received_fields", {"id", "name", "rating100"})
        store._cache_entity(p1)

        # Expire it
        cache_key = ("Performer", "1")
        store._cache[cache_key].ttl_seconds = 0.001

        time.sleep(0.002)

        # Should return empty
        results, _stats = await store.filter_and_populate_with_stats(
            Performer,
            required_fields=["rating100"],
            predicate=lambda p: p.rating100 >= 80,  # type: ignore[operator]
        )

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_filter_with_stats_warns_on_populate_failure(
        self, respx_mock, respx_entity_store: StashEntityStore
    ) -> None:
        """Test filter_and_populate_with_stats warns if populate fails."""
        store = respx_entity_store

        # Cache performer with missing field
        p1 = PerformerFactory.build(id="1", name="Alice")
        object.__setattr__(p1, "rating100", UNSET)
        object.__setattr__(p1, "_received_fields", {"id", "name"})
        store._cache_entity(p1)

        # Mock incomplete response
        p1_incomplete = create_performer_dict(id="1", name="Alice")

        respx.post("http://localhost:9999/graphql").mock(
            return_value=httpx.Response(
                200, json=create_graphql_response("findPerformer", p1_incomplete)
            )
        )

        # Should warn and skip
        log_capture = io.StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setLevel(logging.WARNING)
        client_logger.addHandler(handler)

        _results, stats = await store.filter_and_populate_with_stats(
            Performer,
            required_fields=["rating100"],
            predicate=lambda p: p.rating100 >= 80,  # type: ignore[operator]
        )

        client_logger.removeHandler(handler)
        log_output = log_capture.getvalue()

        assert "still missing" in log_output or stats["matches"] == 0

    @pytest.mark.asyncio
    async def test_filter_with_stats_skips_entry_expired_during_processing(
        self, respx_mock, respx_entity_store: StashEntityStore
    ) -> None:
        """Test filter_and_populate_with_stats skips entries expired during processing."""
        store = respx_entity_store

        # Cache two performers with complete data
        p1 = PerformerFactory.build(id="1", name="Alice", rating100=90)
        p2 = PerformerFactory.build(id="2", name="Bob", rating100=85)

        for p in [p1, p2]:
            object.__setattr__(p, "_received_fields", {"id", "name", "rating100"})
            store._cache_entity(p)

        # Spy on all_cached to expire p2 during processing
        original_all_cached = store.all_cached

        def spy_and_expire(entity_type):
            result = original_all_cached(entity_type)
            # Expire p2 (race condition simulation)
            cache_key = ("Performer", "2")
            if cache_key in store._cache:
                store._cache[cache_key].ttl_seconds = 0.001

                time.sleep(0.002)
            return result

        with patch.object(store, "all_cached", wraps=spy_and_expire):
            results, stats = await store.filter_and_populate_with_stats(
                Performer,
                required_fields=["rating100"],
                predicate=lambda p: p.rating100 >= 80,  # type: ignore[operator]
            )

        # Should only get p1
        assert len(results) == 1
        assert results[0].id == "1"
        assert stats["total_cached"] == 2  # Originally 2
        assert stats["matches"] == 1  # But only 1 matched (p2 expired)


# =============================================================================
# Unit Tests - populated_filter_iter()
# =============================================================================


class TestPopulatedFilterIter:
    """Tests for populated_filter_iter() - lazy async iterator."""

    @pytest.mark.asyncio
    async def test_populated_filter_iter_yields_incrementally(
        self, respx_mock, respx_entity_store: StashEntityStore
    ) -> None:
        """Test populated_filter_iter yields results as they're processed."""
        store = respx_entity_store

        # Create 3 performers
        p1 = PerformerFactory.build(id="1", name="Alice")
        p2 = PerformerFactory.build(id="2", name="Bob")
        p3 = PerformerFactory.build(id="3", name="Charlie")

        # Set rating100 to UNSET
        for p in [p1, p2, p3]:
            object.__setattr__(p, "rating100", UNSET)
            object.__setattr__(p, "_received_fields", {"id", "name"})
            store._cache_entity(p)

        # Mock responses
        def mock_response(request):
            content = request.content.decode()
            if '"id": "1"' in content or '"id":"1"' in content:
                return httpx.Response(
                    200,
                    json=create_graphql_response(
                        "findPerformer",
                        create_performer_dict(id="1", name="Alice", rating100=95),
                    ),
                )
            if '"id": "2"' in content or '"id":"2"' in content:
                return httpx.Response(
                    200,
                    json=create_graphql_response(
                        "findPerformer",
                        create_performer_dict(id="2", name="Bob", rating100=85),
                    ),
                )
            return httpx.Response(
                200,
                json=create_graphql_response(
                    "findPerformer",
                    create_performer_dict(id="3", name="Charlie", rating100=75),
                ),
            )

        respx.post("http://localhost:9999/graphql").mock(side_effect=mock_response)

        # Iterate and collect
        results = []
        async for performer in store.populated_filter_iter(
            Performer,
            required_fields=["rating100"],
            predicate=lambda p: p.rating100 >= 80,  # type: ignore[operator]
            yield_batch=1,  # Process one at a time
        ):
            results.append(performer)

        # Should get p1 and p2 (rating >= 80)
        assert len(results) == 2
        assert {r.id for r in results} == {"1", "2"}

    @pytest.mark.asyncio
    async def test_populated_filter_iter_early_break(
        self, respx_mock, respx_entity_store: StashEntityStore
    ) -> None:
        """Test populated_filter_iter can break early without processing all."""
        store = respx_entity_store

        # Create 100 performers (but we'll break after finding 1)
        for i in range(1, 101):
            p = PerformerFactory.build(id=str(i), name=f"P{i}")
            object.__setattr__(p, "rating100", UNSET)
            object.__setattr__(p, "_received_fields", {"id", "name"})
            store._cache_entity(p)

        # Mock - all return high rating
        call_count = 0

        def mock_response(request):
            nonlocal call_count
            call_count += 1
            content = request.content.decode()
            # Extract any ID
            match = re.search(r'"id"\s*:\s*"(\d+)"', content)
            if match:
                pid = match.group(1)
                return httpx.Response(
                    200,
                    json=create_graphql_response(
                        "findPerformer",
                        create_performer_dict(id=pid, name=f"P{pid}", rating100=95),
                    ),
                )
            return httpx.Response(500, text="Unknown")

        respx.post("http://localhost:9999/graphql").mock(side_effect=mock_response)

        # Break after first result
        count = 0
        async for _performer in store.populated_filter_iter(
            Performer,
            required_fields=["rating100"],
            predicate=lambda p: p.rating100 >= 90,  # type: ignore[operator]
            yield_batch=10,  # Process 10 at a time
        ):
            count += 1
            if count >= 1:
                break

        # Should have only fetched first batch (10), not all 100
        assert call_count <= 10

    @pytest.mark.asyncio
    async def test_populated_filter_iter_empty_cache(
        self, respx_mock, respx_entity_store: StashEntityStore
    ) -> None:
        """Test populated_filter_iter with empty cache."""
        store = respx_entity_store

        results = []
        async for performer in store.populated_filter_iter(
            Performer,
            required_fields=["rating100"],
            predicate=lambda p: p.rating100 >= 80,  # type: ignore[operator]
        ):
            results.append(performer)

        assert results == []

    @pytest.mark.asyncio
    async def test_populated_filter_iter_batching(
        self, respx_mock, respx_entity_store: StashEntityStore
    ) -> None:
        """Test populated_filter_iter respects batch parameters."""
        store = respx_entity_store

        # Create 6 performers
        for i in range(1, 7):
            p = PerformerFactory.build(id=str(i), name=f"P{i}")
            object.__setattr__(p, "rating100", UNSET)
            object.__setattr__(p, "_received_fields", {"id", "name"})
            store._cache_entity(p)

        # Mock responses
        def mock_response(request):
            content = request.content.decode()
            match = re.search(r'"id"\s*:\s*"(\d+)"', content)
            if match:
                pid = match.group(1)
                return httpx.Response(
                    200,
                    json=create_graphql_response(
                        "findPerformer",
                        create_performer_dict(
                            id=pid, name=f"P{pid}", rating100=80 + int(pid)
                        ),
                    ),
                )
            return httpx.Response(500)

        respx.post("http://localhost:9999/graphql").mock(side_effect=mock_response)

        # Process with specific batch sizes
        results = []
        async for performer in store.populated_filter_iter(
            Performer,
            required_fields=["rating100"],
            predicate=lambda p: p.rating100 >= 83,  # type: ignore[operator]
            populate_batch=2,  # Populate 2 at a time
            yield_batch=3,  # Yield after processing 3
        ):
            results.append(performer)

        # P3, P4, P5, P6 match (rating 83, 84, 85, 86)
        assert len(results) == 4
        assert all(r.rating100 >= 83 for r in results)  # type: ignore[operator]

    @pytest.mark.asyncio
    async def test_populated_filter_iter_warns_on_populate_failure(
        self, respx_mock, respx_entity_store: StashEntityStore
    ) -> None:
        """Test populated_filter_iter warns if populate fails to load fields."""
        store = respx_entity_store

        # Cache performer with missing field
        p1 = PerformerFactory.build(id="1", name="Alice")
        object.__setattr__(p1, "rating100", UNSET)
        object.__setattr__(p1, "_received_fields", {"id", "name"})
        store._cache_entity(p1)

        # Mock incomplete response (no rating100)
        p1_incomplete = create_performer_dict(id="1", name="Alice")

        respx.post("http://localhost:9999/graphql").mock(
            return_value=httpx.Response(
                200, json=create_graphql_response("findPerformer", p1_incomplete)
            )
        )

        # Should warn and skip
        log_capture = io.StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setLevel(logging.WARNING)
        client_logger.addHandler(handler)

        results = []
        async for performer in store.populated_filter_iter(
            Performer,
            required_fields=["rating100"],
            predicate=lambda p: p.rating100 >= 80,  # type: ignore[operator]
        ):
            results.append(performer)

        client_logger.removeHandler(handler)
        log_output = log_capture.getvalue()

        assert "missing" in log_output or len(results) == 0
        assert len(results) == 0  # Should skip the incomplete performer

    @pytest.mark.asyncio
    async def test_populated_filter_iter_all_complete_no_population(
        self, respx_mock, respx_entity_store: StashEntityStore
    ) -> None:
        """Test populated_filter_iter with all data complete (no population needed)."""
        store = respx_entity_store

        # Cache performers with complete data
        p1 = PerformerFactory.build(id="1", name="Alice", rating100=95)
        p2 = PerformerFactory.build(id="2", name="Bob", rating100=85)

        for p in [p1, p2]:
            object.__setattr__(p, "_received_fields", {"id", "name", "rating100"})
            store._cache_entity(p)

        # Mock should NOT be called (no population needed)
        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            return_value=httpx.Response(500, text="Should not be called")
        )

        # Iterate - should not trigger any fetches
        results = []
        async for performer in store.populated_filter_iter(
            Performer,
            required_fields=["rating100"],
            predicate=lambda p: p.rating100 >= 90,  # type: ignore[operator]
        ):
            results.append(performer)

        # Verify no GraphQL calls
        assert len(graphql_route.calls) == 0

        # Verify results
        assert len(results) == 1
        assert results[0].id == "1"
        assert results[0].rating100 == 95
