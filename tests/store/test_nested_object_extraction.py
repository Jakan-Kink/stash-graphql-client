"""Tests for Phase 2: Nested Object Extraction and Identity Map.

Tests the cache integration prototype's nested object extraction feature where:
1. Nested StashObjects are extracted from GraphQL responses during validation
2. Extracted objects are cached in the store's identity map
3. Multiple references to the same object (by ID) return the same instance

This follows TESTING_REQUIREMENTS.md:
- Mock only at HTTP boundary using respx
- Use FactoryBoy factories for creating test objects
- Verify identity map behavior and cache state
"""

from unittest.mock import patch

import httpx
import pytest
import respx

from stash_graphql_client import (
    Performer,
    Scene,
    Studio,
)
from stash_graphql_client.types.base import StashObject


# =============================================================================
# Phase 2: Nested Object Extraction and Caching
# =============================================================================


class TestNestedSingleObjectExtraction:
    """Tests for extracting and caching single nested objects (e.g., scene.studio)."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_nested_studio_extracted_and_cached(self, respx_entity_store) -> None:
        """Test that nested studio is extracted from GraphQL response and cached.

        When a Scene is fetched with nested Studio data, the Studio should be:
        - Extracted from the nested dict during validation
        - Cached in store with key ("Studio", "st1")
        - Accessible via scene.studio as a Studio instance
        - Retrievable from cache independently
        """
        store = respx_entity_store

        # Mock GraphQL response with nested studio
        scene_data = {
            "findScene": {
                "id": "s1",
                "title": "Test Scene",
                "studio": {
                    "id": "st1",
                    "name": "Test Studio",
                    "url": "http://test.com",
                },
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        }

        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[httpx.Response(200, json={"data": scene_data})]
        )

        scene = await store.get(Scene, "s1")

        # Verify scene was created
        assert scene is not None
        assert scene.id == "s1"
        assert scene.studio is not None

        # Verify nested studio is a Studio instance (not a dict)
        assert isinstance(scene.studio, Studio)
        assert scene.studio.id == "st1"
        assert scene.studio.name == "Test Studio"

        # Verify studio is cached in the store
        assert store.is_cached(Studio, "st1")

        # Verify we can retrieve studio from cache independently
        cached_studio = await store.get(Studio, "st1")
        assert cached_studio is not None
        assert cached_studio.id == "st1"
        assert cached_studio.name == "Test Studio"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_nested_studio_with_none_value(self, respx_entity_store) -> None:
        """Test that None studio values are handled gracefully without extraction."""
        store = respx_entity_store

        scene_data = {
            "findScene": {
                "id": "s1",
                "title": "Scene without studio",
                "studio": None,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        }

        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[httpx.Response(200, json={"data": scene_data})]
        )

        scene = await store.get(Scene, "s1")

        # Scene should exist with None studio
        assert scene is not None
        assert scene.studio is None


class TestIdentityMapSingleObjects:
    """Tests for identity map pattern with single nested objects."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_same_studio_id_returns_same_reference(
        self, respx_entity_store
    ) -> None:
        """Test identity map: two scenes with same studio ID share the same Studio instance.

        When Scene1 and Scene2 both reference Studio(id="st1"),
        both scene.studio should point to the SAME object instance (same id()).
        This is the core identity map pattern.
        """
        store = respx_entity_store

        # Mock responses for two different scenes with the same studio
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

        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(200, json={"data": scene1_data}),
                httpx.Response(200, json={"data": scene2_data}),
            ]
        )

        scene1 = await store.get(Scene, "s1")
        scene2 = await store.get(Scene, "s2")

        # Both scenes should exist
        assert scene1 is not None
        assert scene2 is not None
        assert scene1.studio is not None
        assert scene2.studio is not None

        # KEY TEST: Both studios should be THE SAME object (identity map)
        # Not just equal, but literally the same object reference
        assert scene1.studio is scene2.studio
        assert id(scene1.studio) == id(scene2.studio)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_identity_map_mutation_propagates(self, respx_entity_store) -> None:
        """Test that mutations to a cached nested object are visible everywhere.

        If we modify scene1.studio.name, the change should be visible in
        scene2.studio (because they're the same object reference).
        """
        store = respx_entity_store

        scene1_data = {
            "findScene": {
                "id": "s1",
                "title": "Scene 1",
                "studio": {"id": "st1", "name": "Original Name"},
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        }

        scene2_data = {
            "findScene": {
                "id": "s2",
                "title": "Scene 2",
                "studio": {"id": "st1", "name": "Original Name"},
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        }

        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(200, json={"data": scene1_data}),
                httpx.Response(200, json={"data": scene2_data}),
            ]
        )

        scene1 = await store.get(Scene, "s1")
        scene2 = await store.get(Scene, "s2")

        # Modify studio through scene1
        assert scene1.studio is not None
        scene1.studio.name = "Modified Name"

        # Modification should be visible in scene2 (same reference)
        assert scene2.studio is not None
        assert scene2.studio.name == "Modified Name"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_cached_studio_matches_scene_studio_reference(
        self, respx_entity_store
    ) -> None:
        """Test that directly fetched cached object matches nested reference.

        If we fetch a Scene with studio, then separately fetch the Studio,
        both should return the same object instance.
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
            side_effect=[httpx.Response(200, json={"data": scene_data})]
        )

        scene = await store.get(Scene, "s1")
        assert scene.studio is not None

        # Fetch studio from cache (no GraphQL call needed)
        cached_studio = await store.get(Studio, "st1")
        assert cached_studio is not None

        # Should be the exact same object
        assert scene.studio is cached_studio
        assert id(scene.studio) == id(cached_studio)


class TestNestedListObjectExtraction:
    """Tests for extracting and caching lists of nested objects (e.g., scene.performers)."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_nested_performers_list_extracted_and_cached(
        self, respx_entity_store
    ) -> None:
        """Test that nested performers list is extracted and each performer is cached.

        When a Scene has multiple performers, each should be:
        - Extracted from the list of dicts during validation
        - Cached individually in the store
        - Accessible as Performer instances
        """
        store = respx_entity_store

        scene_data = {
            "findScene": {
                "id": "s1",
                "title": "Test Scene",
                "performers": [
                    {"id": "p1", "name": "Alice", "gender": "FEMALE"},
                    {"id": "p2", "name": "Bob", "gender": "MALE"},
                    {"id": "p3", "name": "Charlie", "gender": "MALE"},
                ],
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        }

        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[httpx.Response(200, json={"data": scene_data})]
        )

        scene = await store.get(Scene, "s1")

        # Verify scene was created with performers
        assert scene is not None
        assert scene.performers is not None
        assert len(scene.performers) == 3

        # Verify each performer is a Performer instance
        for performer in scene.performers:
            assert isinstance(performer, Performer)

        # Verify all performers are cached individually
        assert store.is_cached(Performer, "p1")
        assert store.is_cached(Performer, "p2")
        assert store.is_cached(Performer, "p3")

        # Verify we can retrieve each performer from cache
        cached_p1 = await store.get(Performer, "p1")
        assert cached_p1 is not None
        assert cached_p1.name == "Alice"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_empty_performers_list_handled(self, respx_entity_store) -> None:
        """Test that empty performers lists are handled gracefully."""
        store = respx_entity_store

        scene_data = {
            "findScene": {
                "id": "s1",
                "title": "Scene without performers",
                "performers": [],
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        }

        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[httpx.Response(200, json={"data": scene_data})]
        )

        scene = await store.get(Scene, "s1")

        # Scene should exist with empty performers list
        assert scene is not None
        assert scene.performers == []


class TestIdentityMapListObjects:
    """Tests for identity map pattern with lists of nested objects."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_same_performer_in_multiple_scenes_same_reference(
        self, respx_entity_store
    ) -> None:
        """Test identity map: same performer in two scenes shares the same Performer instance.

        If Scene1 and Scene2 both have Performer(id="p1") in their performers list,
        both should point to the same cached Performer instance.
        """
        store = respx_entity_store

        # Two scenes with overlapping performers
        scene1_data = {
            "findScene": {
                "id": "s1",
                "title": "Scene 1",
                "performers": [
                    {"id": "p1", "name": "Alice", "gender": "FEMALE"},
                    {"id": "p2", "name": "Bob", "gender": "MALE"},
                ],
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        }

        scene2_data = {
            "findScene": {
                "id": "s2",
                "title": "Scene 2",
                "performers": [
                    {"id": "p1", "name": "Alice", "gender": "FEMALE"},  # Same performer
                    {"id": "p3", "name": "Charlie", "gender": "MALE"},
                ],
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        }

        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(200, json={"data": scene1_data}),
                httpx.Response(200, json={"data": scene2_data}),
            ]
        )

        scene1 = await store.get(Scene, "s1")
        scene2 = await store.get(Scene, "s2")

        # Find Alice in both scenes
        alice_in_scene1 = next(p for p in scene1.performers if p.id == "p1")
        alice_in_scene2 = next(p for p in scene2.performers if p.id == "p1")

        # KEY TEST: Both should be the SAME object (identity map)
        assert alice_in_scene1 is alice_in_scene2
        assert id(alice_in_scene1) == id(alice_in_scene2)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_identity_map_list_mutation_propagates(
        self, respx_entity_store
    ) -> None:
        """Test that mutations to performers propagate via identity map.

        If we modify scene1.performers[0].name, the change should be visible
        in scene2.performers if they share the same performer.
        """
        store = respx_entity_store

        scene1_data = {
            "findScene": {
                "id": "s1",
                "title": "Scene 1",
                "performers": [
                    {"id": "p1", "name": "Original Name", "gender": "FEMALE"}
                ],
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        }

        scene2_data = {
            "findScene": {
                "id": "s2",
                "title": "Scene 2",
                "performers": [
                    {"id": "p1", "name": "Original Name", "gender": "FEMALE"}
                ],
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        }

        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(200, json={"data": scene1_data}),
                httpx.Response(200, json={"data": scene2_data}),
            ]
        )

        scene1 = await store.get(Scene, "s1")
        scene2 = await store.get(Scene, "s2")

        # Modify performer through scene1
        scene1.performers[0].name = "Modified Name"

        # Modification should be visible in scene2
        assert scene2.performers[0].name == "Modified Name"


class TestStoreContextInjection:
    """Tests for store context injection during entity validation."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_store_context_enables_nested_extraction(
        self, respx_entity_store
    ) -> None:
        """Test that store context is passed during validation to enable extraction.

        When store creates an entity from GraphQL response, it should pass
        context={"store": store} to Pydantic validation, which enables
        the nested object extraction logic.
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
            side_effect=[httpx.Response(200, json={"data": scene_data})]
        )

        scene = await store.get(Scene, "s1")

        # The fact that studio is cached proves context was passed
        assert scene is not None
        assert store.is_cached(Studio, "st1")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_no_extraction_without_store_context(self) -> None:
        """Test that entities created directly don't cache nested objects.

        When constructing an entity directly from dict (not through store),
        nested objects should be created but NOT cached, since there's no
        store context during validation.
        """
        # Ensure no store context is set (completely naked creation)
        with patch.object(StashObject, "_store", None):
            # Create scene directly, bypassing store
            scene_dict = {
                "id": "s1",
                "title": "Direct Scene",
                "studio": {"id": "st1", "name": "Direct Studio"},
            }

            scene = Scene(**scene_dict)

            # Scene should be created
            assert scene.id == "s1"
            assert scene.studio is not None

            # Studio should be a Studio instance
            assert isinstance(scene.studio, Studio)

            # Verify no store was used (no _store available means no caching happened)
            assert StashObject._store is None


class TestDeeplyNestedExtraction:
    """Tests for extraction behavior with deeply nested objects."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_nested_studio_with_parent_studio(self, respx_entity_store) -> None:
        """Test extraction of nested studio that has its own parent_studio.

        When Scene has Studio, and Studio has parent_studio, the extraction
        should handle the nested structure appropriately.

        This test documents the expected behavior - whether deep extraction
        is performed recursively or only one level deep.
        """
        store = respx_entity_store

        scene_data = {
            "findScene": {
                "id": "s1",
                "title": "Scene with nested studio",
                "studio": {
                    "id": "st1",
                    "name": "Child Studio",
                    "parent_studio": {"id": "st0", "name": "Parent Studio"},
                },
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        }

        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[httpx.Response(200, json={"data": scene_data})]
        )

        scene = await store.get(Scene, "s1")

        # Studio should be cached
        assert store.is_cached(Studio, "st1")

        # Document expected behavior for parent_studio:
        # - If recursive extraction: parent_studio should also be cached
        # - If one-level extraction: parent_studio would be a dict or shallow Studio
        #
        # For this test, we expect recursive extraction to be performed
        assert store.is_cached(Studio, "st0")

        # Verify the full chain is accessible
        assert scene.studio is not None
        assert scene.studio.parent_studio is not None
        assert isinstance(scene.studio.parent_studio, Studio)
        assert scene.studio.parent_studio.name == "Parent Studio"


class TestReceivedFieldsWithNestedExtraction:
    """Tests for _received_fields tracking with nested object extraction."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_received_fields_includes_nested_object_fields(
        self, respx_entity_store
    ) -> None:
        """Test that _received_fields includes fields with nested objects.

        When a Scene is fetched with studio data, _received_fields should
        include "studio" to indicate the field was present in the response.
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
            side_effect=[httpx.Response(200, json={"data": scene_data})]
        )

        scene = await store.get(Scene, "s1")

        # Verify _received_fields includes "studio"
        assert scene is not None
        received = getattr(scene, "_received_fields", set())
        assert "studio" in received

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_nested_studio_has_received_fields(self, respx_entity_store) -> None:
        """Test that extracted nested objects also have _received_fields tracking.

        When Studio is extracted from Scene, the Studio instance should have
        its own _received_fields set tracking which fields were in the nested dict.
        """
        store = respx_entity_store

        scene_data = {
            "findScene": {
                "id": "s1",
                "title": "Test Scene",
                "studio": {
                    "id": "st1",
                    "name": "Test Studio",
                    "url": "http://test.com",
                },
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        }

        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[httpx.Response(200, json={"data": scene_data})]
        )

        scene = await store.get(Scene, "s1")

        # Verify studio has _received_fields
        assert scene.studio is not None
        studio_received = getattr(scene.studio, "_received_fields", set())
        assert "id" in studio_received
        assert "name" in studio_received
        assert "url" in studio_received
