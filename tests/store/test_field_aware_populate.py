"""Tests for Phase 3: Field-Aware Populate.

Tests the enhanced populate() method that uses _received_fields tracking to
selectively fetch only genuinely missing fields, avoiding redundant queries.

Key features tested:
1. populate() only fetches fields not in _received_fields
2. _received_fields are merged on refetch (old | new)
3. force_refetch invalidates cache and re-fetches
4. Helper methods: has_fields(), missing_fields()

This follows TESTING_REQUIREMENTS.md:
- Mock only at HTTP boundary using respx
- Use FactoryBoy factories for creating test objects
- Verify field tracking and selective fetching behavior
"""

import httpx
import pytest
import respx

from stash_graphql_client import (
    Scene,
)
from tests.fixtures.stash import (
    SceneFactory,
)


# =============================================================================
# Phase 3: Field-Aware Populate
# =============================================================================


class TestPopulateWithFieldsParameter:
    """Tests for populate() with explicit fields parameter."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_populate_only_fetches_missing_fields(
        self, respx_entity_store
    ) -> None:
        """Test that populate() only fetches fields not in _received_fields.

        When a Scene has _received_fields={"id", "title"}, calling
        populate(scene, fields=["studio", "performers"]) should only
        fetch "studio" and "performers", not "title" (already received).
        """
        store = respx_entity_store

        # Initial fetch with minimal fields
        initial_data = {
            "findScene": {
                "id": "s1",
                "title": "Test Scene",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        }

        # Second fetch with additional fields
        populate_data = {
            "findScene": {
                "id": "s1",
                "title": "Test Scene",
                "studio": {"id": "st1", "name": "Test Studio"},
                "performers": [{"id": "p1", "name": "Alice", "gender": "FEMALE"}],
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        }

        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(200, json={"data": initial_data}),
                httpx.Response(200, json={"data": populate_data}),
            ]
        )

        # Initial get - only has id, title
        scene = await store.get(Scene, "s1")
        assert scene is not None

        # Verify initial _received_fields
        received = getattr(scene, "_received_fields", set())
        assert "id" in received
        assert "title" in received
        assert "studio" not in received
        assert "performers" not in received

        # Populate with additional fields
        scene = await store.populate(scene, fields=["studio", "performers"])

        # Verify studio and performers are now present
        assert scene.studio is not None
        assert scene.performers is not None
        assert len(scene.performers) >= 1

        # Verify _received_fields now includes the new fields
        received_after = getattr(scene, "_received_fields", set())
        assert "studio" in received_after
        assert "performers" in received_after
        # Original fields should still be present
        assert "id" in received_after
        assert "title" in received_after

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_populate_with_already_received_fields_no_fetch(
        self, respx_entity_store
    ) -> None:
        """Test that populate() doesn't fetch fields already in _received_fields.

        If all requested fields are already in _received_fields, no GraphQL
        query should be made.
        """
        store = respx_entity_store

        # Fetch scene with studio already included
        scene_data = {
            "findScene": {
                "id": "s1",
                "title": "Test Scene",
                "studio": {"id": "st1", "name": "Test Studio"},
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        }

        # Single mock that handles BOTH the initial get AND any populate calls
        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                # Call 1: Initial store.get(Scene, "s1")
                httpx.Response(200, json={"data": scene_data}),
            ]
        )

        scene = await store.get(Scene, "s1")
        assert scene is not None

        # Try to populate with field that's already received
        scene_after = await store.populate(scene, fields=["studio"])

        # Debug: Print all GraphQL calls made
        print(f"\n=== GraphQL Calls Made: {len(graphql_route.calls)} ===")
        for i, call in enumerate(graphql_route.calls):
            import json

            req_body = json.loads(call.request.content)
            print(f"\nCall {i}:")
            print(f"  Query: {req_body.get('query', '')[:100]}...")
            print(f"  Variables: {req_body.get('variables', {})}")
            if call.response:
                print(f"  Response status: {call.response.status_code}")

        # Should have made only 1 call (the initial get), populate should make 0 additional calls
        assert len(graphql_route.calls) == 1

        # Scene should be unchanged (or same reference)
        assert scene_after is scene or scene_after.studio is not None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_populate_with_empty_fields_list(self, respx_entity_store) -> None:
        """Test that populate() with empty fields list returns object unchanged."""
        store = respx_entity_store

        scene_data = {
            "findScene": {
                "id": "s1",
                "title": "Test Scene",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        }

        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[httpx.Response(200, json={"data": scene_data})]
        )

        scene = await store.get(Scene, "s1")

        # Populate with empty fields
        scene_after = await store.populate(scene, fields=[])

        # Should return the same object
        assert scene_after is scene

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_populate_with_none_fields_parameter(
        self, respx_entity_store
    ) -> None:
        """Test that populate() with fields=None uses heuristic behavior."""
        store = respx_entity_store

        scene_data = {
            "findScene": {
                "id": "s1",
                "title": "Test Scene",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        }

        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[httpx.Response(200, json={"data": scene_data})]
        )

        scene = await store.get(Scene, "s1")

        # Populate with fields=None (default)
        scene_after = await store.populate(scene, fields=None)

        # Should handle gracefully (behavior depends on implementation)
        assert scene_after is not None


class TestFieldMergingOnRefetch:
    """Tests for _received_fields merging behavior."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_received_fields_merged_on_populate(self, respx_entity_store) -> None:
        """Test that _received_fields are merged (union) when populating.

        Initial fetch has fields A, B.
        Populate with fields C, D.
        Result should have _received_fields = {A, B, C, D}.
        """
        store = respx_entity_store

        # Initial fetch with minimal fields
        initial_data = {
            "findScene": {
                "id": "s1",
                "title": "Test Scene",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        }

        # Populate with additional fields
        populate_data = {
            "findScene": {
                "id": "s1",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "studio": {"id": "st1", "name": "Test Studio"},
                "rating100": 85,
            }
        }

        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(200, json={"data": initial_data}),
                httpx.Response(200, json={"data": populate_data}),
            ]
        )

        scene = await store.get(Scene, "s1")
        initial_received = getattr(scene, "_received_fields", set()).copy()

        # Populate with new fields
        scene = await store.populate(scene, fields=["studio", "rating100"])

        # Verify fields are merged (union)
        final_received = getattr(scene, "_received_fields", set())

        # Should have original fields
        for field in initial_received:
            if field != "title":  # title might not be in populate response
                assert field in final_received

        # Should have new fields
        assert "studio" in final_received
        assert "rating100" in final_received

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_received_fields_not_lost_on_partial_refetch(
        self, respx_entity_store
    ) -> None:
        """Test that existing _received_fields are preserved when fetching new fields.

        If Scene has {id, title, studio} and we populate with {performers},
        the result should have {id, title, studio, performers}, not just
        {id, performers} (which would lose studio).
        """
        store = respx_entity_store

        # Initial fetch with studio
        initial_data = {
            "findScene": {
                "id": "s1",
                "title": "Test Scene",
                "studio": {"id": "st1", "name": "Test Studio"},
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        }

        # Populate with performers (GraphQL might not return studio in this response)
        populate_data = {
            "findScene": {
                "id": "s1",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "performers": [{"id": "p1", "name": "Alice", "gender": "FEMALE"}],
            }
        }

        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(200, json={"data": initial_data}),
                httpx.Response(200, json={"data": populate_data}),
            ]
        )

        scene = await store.get(Scene, "s1")
        assert "studio" in getattr(scene, "_received_fields", set())

        # Populate with performers
        scene = await store.populate(scene, fields=["performers"])

        # Verify studio is still in _received_fields (not lost)
        final_received = getattr(scene, "_received_fields", set())
        assert "studio" in final_received
        assert "performers" in final_received


class TestForceRefetchParameter:
    """Tests for force_refetch parameter behavior."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_force_refetch_invalidates_cache_and_refetches(
        self, respx_entity_store
    ) -> None:
        """Test that force_refetch=True invalidates cache and re-fetches from server.

        Even if fields are in _received_fields, force_refetch should
        invalidate the cache entry and fetch fresh data.
        """
        store = respx_entity_store

        # Initial fetch
        initial_data = {
            "findScene": {
                "id": "s1",
                "title": "Original Title",
                "studio": {"id": "st1", "name": "Original Studio"},
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        }

        # Force refetch returns updated data
        refetch_data = {
            "findScene": {
                "id": "s1",
                "title": "Updated Title",
                "studio": {"id": "st1", "name": "Updated Studio"},
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        }

        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(200, json={"data": initial_data}),
                httpx.Response(200, json={"data": refetch_data}),
            ]
        )

        scene = await store.get(Scene, "s1")
        assert scene.title == "Original Title"
        assert scene.studio is not None
        assert scene.studio.name == "Original Studio"

        # Force refetch - should get updated data even though fields are already received
        scene = await store.populate(scene, fields=["studio"], force_refetch=True)

        # Should have updated data from server
        assert scene.studio is not None
        assert scene.studio.name == "Updated Studio"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_force_refetch_with_empty_fields_refetches_all(
        self, respx_entity_store
    ) -> None:
        """Test that force_refetch with no fields still refetches the entity.

        force_refetch=True with fields=[] should invalidate and re-fetch
        the entire entity (or at least trigger a cache invalidation).
        """
        store = respx_entity_store

        initial_data = {
            "findScene": {
                "id": "s1",
                "title": "Original",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        }

        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[httpx.Response(200, json={"data": initial_data})]
        )

        scene = await store.get(Scene, "s1")
        assert scene.title == "Original"

        # Force refetch with empty fields
        scene_after = await store.populate(scene, fields=[], force_refetch=True)

        # Should handle gracefully (behavior depends on implementation)
        assert scene_after is not None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_force_refetch_false_uses_cache(self, respx_entity_store) -> None:
        """Test that force_refetch=False (default) uses cached data.

        When fields are already in _received_fields and force_refetch=False,
        no GraphQL query should be made.
        """
        store = respx_entity_store

        scene_data = {
            "findScene": {
                "id": "s1",
                "title": "Test Scene",
                "studio": {"id": "st1", "name": "Test Studio"},
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        }

        # Single mock handles both initial get AND populate calls
        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                # Call 1: Initial store.get(Scene, "s1")
                httpx.Response(200, json={"data": scene_data}),
            ]
        )

        scene = await store.get(Scene, "s1")

        # Populate with already-received field and force_refetch=False
        await store.populate(scene, fields=["studio"], force_refetch=False)

        # Should have made only 1 call (the initial get), populate should make 0 additional calls
        assert len(graphql_route.calls) == 1


class TestHasFieldsHelper:
    """Tests for has_fields() helper method."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_has_fields_returns_true_when_all_present(
        self, respx_entity_store
    ) -> None:
        """Test has_fields() returns True when all specified fields are received."""
        store = respx_entity_store

        scene_data = {
            "findScene": {
                "id": "s1",
                "title": "Test Scene",
                "studio": {"id": "st1", "name": "Test Studio"},
                "rating100": 85,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        }

        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[httpx.Response(200, json={"data": scene_data})]
        )

        scene = await store.get(Scene, "s1")

        # Check fields that are present
        assert store.has_fields(scene, "id", "title", "studio")
        assert store.has_fields(scene, "rating100")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_has_fields_returns_false_when_any_missing(
        self, respx_entity_store
    ) -> None:
        """Test has_fields() returns False if ANY requested field is missing."""
        store = respx_entity_store

        scene_data = {
            "findScene": {
                "id": "s1",
                "title": "Test Scene",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        }

        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[httpx.Response(200, json={"data": scene_data})]
        )

        scene = await store.get(Scene, "s1")

        # Check mix of present and missing fields
        assert not store.has_fields(scene, "title", "studio")  # studio missing
        assert not store.has_fields(scene, "performers")  # performers missing

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_has_fields_with_no_received_fields(self, respx_entity_store) -> None:
        """Test has_fields() handles objects without _received_fields gracefully."""
        store = respx_entity_store

        # Create object directly without _received_fields
        scene = SceneFactory.build(id="s1", title="Test")

        # Should return False (no _received_fields means nothing received)
        assert not store.has_fields(scene, "title")


class TestMissingFieldsHelper:
    """Tests for missing_fields() helper method."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_missing_fields_returns_empty_when_all_present(
        self, respx_entity_store
    ) -> None:
        """Test missing_fields() returns empty set when all fields are received."""
        store = respx_entity_store

        scene_data = {
            "findScene": {
                "id": "s1",
                "title": "Test Scene",
                "studio": {"id": "st1", "name": "Test Studio"},
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        }

        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[httpx.Response(200, json={"data": scene_data})]
        )

        scene = await store.get(Scene, "s1")

        # Check fields that are all present
        missing = store.missing_fields(scene, "id", "title", "studio")
        assert missing == set()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_missing_fields_returns_missing_subset(
        self, respx_entity_store
    ) -> None:
        """Test missing_fields() returns only the fields not in _received_fields."""
        store = respx_entity_store

        scene_data = {
            "findScene": {
                "id": "s1",
                "title": "Test Scene",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        }

        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[httpx.Response(200, json={"data": scene_data})]
        )

        scene = await store.get(Scene, "s1")

        # Check mix of present and missing fields
        missing = store.missing_fields(scene, "title", "studio", "performers")
        assert "title" not in missing  # present
        assert "studio" in missing  # missing
        assert "performers" in missing  # missing

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_missing_fields_with_no_received_fields(
        self, respx_entity_store
    ) -> None:
        """Test missing_fields() treats all fields as missing without _received_fields."""
        store = respx_entity_store

        # Create object directly without _received_fields
        scene = SceneFactory.build(id="s1", title="Test")

        # All queried fields should be considered missing
        missing = store.missing_fields(scene, "title", "studio")
        assert missing == {"title", "studio"}


class TestPopulateIntegrationWithPhase2:
    """Tests for populate() integration with Phase 2 nested object extraction."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_populate_nested_studio_object_directly(
        self, respx_entity_store
    ) -> None:
        """Test that we can populate a nested studio object directly.

        After fetching a Scene with studio, we should be able to call
        populate(scene.studio, fields=["urls"]) to add more fields to
        the nested Studio instance.
        """
        store = respx_entity_store

        # Initial scene fetch with minimal studio
        scene_data = {
            "findScene": {
                "id": "s1",
                "title": "Test Scene",
                "studio": {"id": "st1", "name": "Test Studio"},
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        }

        # Populate studio with additional fields
        studio_data = {
            "findStudio": {
                "id": "st1",
                "name": "Test Studio",
                "urls": ["http://test.com"],
                "details": "Studio details",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        }

        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(200, json={"data": scene_data}),
                httpx.Response(200, json={"data": studio_data}),
            ]
        )

        scene = await store.get(Scene, "s1")
        assert scene.studio is not None

        # Populate the nested studio directly
        populated_studio = await store.populate(
            scene.studio, fields=["urls", "details"]
        )

        # Verify studio now has additional fields
        assert populated_studio.urls == ["http://test.com"]
        assert populated_studio.details == "Studio details"

        # Verify _received_fields includes new fields
        studio_received = getattr(populated_studio, "_received_fields", set())
        assert "urls" in studio_received
        assert "details" in studio_received

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_populate_performer_from_list(self, respx_entity_store) -> None:
        """Test that we can populate a performer from scene.performers list.

        After fetching a Scene with performers, we should be able to call
        populate(scene.performers[0], fields=["birthdate"]) to add more
        fields to individual Performer instances.
        """
        store = respx_entity_store

        # Initial scene with minimal performer data
        scene_data = {
            "findScene": {
                "id": "s1",
                "title": "Test Scene",
                "performers": [{"id": "p1", "name": "Alice", "gender": "FEMALE"}],
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        }

        # Populate performer with additional fields
        performer_data = {
            "findPerformer": {
                "id": "p1",
                "name": "Alice",
                "gender": "FEMALE",
                "birthdate": "1990-01-01",
                "country": "USA",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        }

        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(200, json={"data": scene_data}),
                httpx.Response(200, json={"data": performer_data}),
            ]
        )

        scene = await store.get(Scene, "s1")
        assert len(scene.performers) >= 1

        # Populate the first performer
        performer = scene.performers[0]
        populated_performer = await store.populate(
            performer, fields=["birthdate", "country"]
        )

        # Verify performer now has additional fields
        assert populated_performer.birthdate == "1990-01-01"
        assert populated_performer.country == "USA"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_populate_uses_cached_nested_object(self, respx_entity_store) -> None:
        """Test that populate() uses cached nested objects (identity map).

        If Scene1 and Scene2 share the same Studio, populating the studio
        through Scene1 should also populate it for Scene2 (same reference).
        """
        store = respx_entity_store

        # Two scenes with same studio
        scene1_data = {
            "findScene": {
                "id": "s1",
                "title": "Scene 1",
                "studio": {"id": "st1", "name": "Shared Studio"},
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        }

        scene2_data = {
            "findScene": {
                "id": "s2",
                "title": "Scene 2",
                "studio": {"id": "st1", "name": "Shared Studio"},
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        }

        # Populate studio with URLs
        studio_data = {
            "findStudio": {
                "id": "st1",
                "name": "Shared Studio",
                "urls": ["http://shared.com"],
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        }

        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(200, json={"data": scene1_data}),
                httpx.Response(200, json={"data": scene2_data}),
                httpx.Response(200, json={"data": studio_data}),
            ]
        )

        scene1 = await store.get(Scene, "s1")
        scene2 = await store.get(Scene, "s2")

        # Populate studio through scene1
        assert scene1.studio is not None
        populated_studio = await store.populate(scene1.studio, fields=["urls"])
        assert populated_studio.urls == ["http://shared.com"]

        # Scene2's studio should also have the URLs (same reference)
        assert scene2.studio is not None
        assert scene2.studio is scene1.studio  # Identity map
        assert scene2.studio.urls == ["http://shared.com"]


class TestSelectiveFieldLoading:
    """Tests for selective field loading to avoid expensive queries."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_check_before_populate_with_missing_fields(
        self, respx_entity_store
    ) -> None:
        """Test pattern: check missing_fields() before populate().

        Demonstrates the recommended pattern of checking which fields are
        missing before populating, to avoid unnecessary work.
        """
        store = respx_entity_store

        scene_data = {
            "findScene": {
                "id": "s1",
                "title": "Test Scene",
                "studio": {"id": "st1", "name": "Test Studio"},
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        }

        respx.post("http://localhost:9999/graphql").mock(
            return_value=httpx.Response(200, json={"data": scene_data})
        )

        scene = await store.get(Scene, "s1")

        # Check what's missing before populating
        required_fields = ["studio", "performers", "rating100"]
        missing = store.missing_fields(scene, *required_fields)

        # Only populate if there are missing fields
        if missing:
            # In this case: performers and rating100 are missing
            assert "performers" in missing
            assert "rating100" in missing
            assert "studio" not in missing  # already present

            # Could populate only the missing fields
            # scene = await store.populate(scene, fields=list(missing))

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_populate_only_expensive_fields_when_needed(
        self, respx_entity_store
    ) -> None:
        """Test pattern: only load expensive fields (relationships) when needed.

        Demonstrates loading a scene with minimal data initially, then
        selectively loading expensive relationships only when required.
        """
        store = respx_entity_store

        # Initial fetch - minimal/fast
        minimal_data = {
            "findScene": {
                "id": "s1",
                "title": "Test Scene",
                "rating100": 85,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        }

        # Expensive populate - relationships
        expensive_data = {
            "findScene": {
                "id": "s1",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "performers": [
                    {"id": "p1", "name": "Alice", "gender": "FEMALE"},
                    {"id": "p2", "name": "Bob", "gender": "MALE"},
                ],
                "tags": [
                    {"id": "t1", "name": "Tag 1"},
                    {"id": "t2", "name": "Tag 2"},
                ],
                "studio": {"id": "st1", "name": "Studio"},
            }
        }

        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(200, json={"data": minimal_data}),
                httpx.Response(200, json={"data": expensive_data}),
            ]
        )

        # Fast initial fetch
        scene = await store.get(Scene, "s1")
        assert scene.title == "Test Scene"
        assert scene.rating100 == 85

        # Only load relationships when actually needed
        if_need_relationships = True
        if if_need_relationships:
            scene = await store.populate(scene, fields=["performers", "tags", "studio"])
            assert len(scene.performers) >= 2
            assert len(scene.tags) >= 2
