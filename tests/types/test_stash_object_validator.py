"""Tests for StashObject identity map validator and caching behavior.

This test suite covers the wrap validator in StashObject that implements:
- Identity map pattern (same ID → same object reference)
- Cache expiration and eviction
- Field merging on cached objects
- Nested object cache lookups
"""

from __future__ import annotations

from unittest.mock import patch

import httpx
import pytest
import respx
from pydantic import BaseModel

from stash_graphql_client.types.base import FromGraphQLMixin, StashObject
from stash_graphql_client.types.files import ImageFile
from stash_graphql_client.types.image import Image
from stash_graphql_client.types.scene import Scene
from stash_graphql_client.types.studio import Studio
from stash_graphql_client.types.tag import Tag
from stash_graphql_client.types.unset import UNSET, UnsetType


# Test model for from_graphql union type testing
class _ModelMultiUnion(FromGraphQLMixin, BaseModel):
    """Test model with multi-type union field."""

    id: str
    mixed_field: str | int | None | UnsetType = UNSET  # 4-way union!


class TestIdValidator:
    """Tests for StashObject._validate_id field validator."""

    @pytest.mark.unit
    def test_rejects_non_numeric_non_uuid_id(self) -> None:
        """Test that non-numeric, non-UUID4 ids are rejected."""
        with (
            patch.object(StashObject, "_store", None),
            pytest.raises(ValueError, match="Invalid StashObject id 'bad-id'"),
        ):
            Tag(id="bad-id", name="Test")

    @pytest.mark.unit
    def test_rejects_prefixed_numeric_id(self) -> None:
        """Test that prefixed IDs like 'scene-123' are rejected."""
        with (
            patch.object(StashObject, "_store", None),
            pytest.raises(ValueError, match="Invalid StashObject id 'scene-123'"),
        ):
            Scene(id="scene-123", title="Test")

    @pytest.mark.unit
    def test_rejects_uuid_shaped_string_that_is_not_uuid4(self) -> None:
        """Test that a UUID-shaped string coerced by uuid.UUID(version=4) is rejected.

        uuid.UUID('...', version=4) overwrites the version nibble, so the
        parsed hex won't round-trip back to the input. The validator catches
        this via the `parsed.hex == value.replace('-', '')` check.
        """
        # Version-1 UUID: uuid.UUID() accepts it with version=4 but silently
        # rewrites the version nibble, so the hex no longer matches the input.
        coercible_id = "12345678-1234-1234-8234-123456789abc"
        with (
            patch.object(StashObject, "_store", None),
            pytest.raises(ValueError, match="Invalid StashObject id"),
        ):
            Tag(id=coercible_id, name="Test")

    @pytest.mark.unit
    def test_accepts_numeric_id(self) -> None:
        """Test that numeric string IDs are accepted."""
        with patch.object(StashObject, "_store", None):
            tag = Tag(id="42", name="Test")
            assert tag.id == "42"

    @pytest.mark.unit
    def test_accepts_uuid4_hex_id(self) -> None:
        """Test that UUID4 hex IDs (from _inject_uuid) are accepted."""
        import uuid

        hex_id = uuid.uuid4().hex
        with patch.object(StashObject, "_store", None):
            tag = Tag(id=hex_id, name="Test")
            assert tag.id == hex_id


class TestIdentityMapValidator:
    """Test identity map validator behavior in StashObject."""

    @pytest.mark.asyncio
    async def test_validator_evicts_expired_cache_entry(
        self, respx_entity_store
    ) -> None:
        """Test that validator evicts expired cache entries during from_graphql().

        This tests lines 507-508 in types/base.py:
        - Validator checks if cached entry is expired
        - Expired entries are removed from cache
        - New instance is constructed after eviction

        This is different from store.get() which checks expiration before
        calling the validator. This test exercises the validator's own
        expiration handling.
        """
        # Ensure store is initialized by fixture (type narrowing for Pylance)
        assert Scene._store is not None

        # Set up mock GraphQL response (not actually called in this test)
        respx.post("http://localhost:9999/graphql").mock(
            return_value=httpx.Response(200, json={"data": {}})
        )

        # Step 1: Create initial scene via from_graphql to populate cache
        scene_data = {
            "id": "401",
            "title": "Original Scene",
            "urls": [],
            "organized": False,
            "files": [],
            "tags": [],
            "performers": [],
            "galleries": [],
            "groups": [],
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        }

        scene1 = Scene.from_graphql(scene_data)
        assert scene1.id == "401"
        assert scene1.title == "Original Scene"

        # Verify it was cached
        cache_key = ("Scene", "401")
        assert cache_key in Scene._store._cache

        # Step 2: Force the cache entry to expire
        # Set TTL to negative value - guaranteed expired since age is always positive
        # (time.monotonic() - cached_at) > -1 is always True
        cached_entry = Scene._store._cache[cache_key]
        cached_entry.ttl_seconds = -1

        # Step 3: Call from_graphql again with same ID
        # This should trigger the validator's expiration path (lines 507-508)
        scene2 = Scene.from_graphql(scene_data)

        # Step 4: Verify behavior
        # The expired entry should have been evicted and a new instance created
        assert scene2.id == "401"
        assert scene2.title == "Original Scene"

        # The cache should now contain a NEW entry (not the expired one)
        new_cached_entry = Scene._store._cache[cache_key]
        assert new_cached_entry is not cached_entry  # Different cache entry object
        assert new_cached_entry.cached_at > cached_entry.cached_at  # Fresh timestamp
        assert not new_cached_entry.is_expired()  # Not expired

        # scene2 should be a different instance than scene1 (because cache was evicted)
        assert scene2 is not scene1


class TestFromGraphQLMixin:
    """Test FromGraphQLMixin._process_nested_graphql behavior."""

    def test_process_nested_graphql_with_multi_type_union(self) -> None:
        """Test _process_nested_graphql with Union of multiple non-None types - hits branch 138->145.

        When a field is annotated as Type1 | Type2 | None | UnsetType (multiple non-None types),
        the _process_nested_graphql method's branch at line 138 should be False,
        skipping unwrapping logic and jumping to line 145.

        After filtering out None and UnsetType, non_none_args = [str, int] (length 2),
        so len(non_none_args) == 1 is False, triggering branch 138->145.
        """

        # Test data with string value for mixed_field
        data = {"id": "402", "mixed_field": "string-value"}

        # Known mypy limitation with @classmethod + TypeVar (see base.py:from_graphql)
        result = _ModelMultiUnion.from_graphql(data)  # type: ignore[misc]

        # Verify the field wasn't unwrapped (branch 138->145 taken)
        assert result.id == "402"
        assert result.mixed_field == "string-value"

    def test_from_dict_alias_calls_from_graphql(self) -> None:
        """Test from_dict() is a working alias for from_graphql() - covers line 182."""
        scene_data = {
            "id": "403",
            "title": "Test Scene",
            "urls": [],
            "organized": False,
            "files": [],
            "tags": [],
            "performers": [],
            "galleries": [],
            "groups": [],
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        }

        # Call from_dict (line 182)
        scene = Scene.from_dict(scene_data)

        assert scene.id == "403"
        assert scene.title == "Test Scene"


class TestStashObjectInit:
    """Test StashObject.__init__() behavior."""

    def test_init_without_id_sets_is_new_flag(self) -> None:
        """Test __init__() sets _is_new=True for new objects - covers line 374."""
        # Create object without providing an ID
        tag = Tag(name="New Tag", description="A fresh tag")

        # Verify _is_new flag was set (line 374)
        assert tag.is_new() is True
        # Verify UUID was auto-generated
        assert len(tag.id) == 32
        assert not tag.id.isdigit()  # UUID hex, not a numeric ID

    def test_validator_with_data_without_id_field(self, respx_entity_store) -> None:
        """Test validator handles data without 'id' field - hits branch 474->517.

        When model_validate() is called with dict data lacking an 'id' field,
        the validator skips cache lookup (branch 474->517), processes nested
        objects, then calls handler which invokes __init__ to auto-generate UUID.

        Requires entity store to be active so validator doesn't return early.
        """
        # Validate data without 'id' field
        # Branch 474->517: skips cache lookup since no id
        tag = Tag.model_validate({"name": "No ID Tag"})

        # Verify UUID was auto-generated by __init__
        assert tag.is_new() is True
        assert len(tag.id) == 32
        assert not tag.id.isdigit()
        assert tag.name == "No ID Tag"

    def test_process_nested_cache_lookups_without_store(self) -> None:
        """Test _process_nested_cache_lookups returns data unchanged when no store - covers line 549."""
        # Use patch.object to temporarily set store to None (thread-safe for parallel tests)
        with patch.object(Tag, "_store", None):
            # Call the method - should return data unchanged
            test_data = {"id": "123", "name": "Test"}
            result = Tag._process_nested_cache_lookups(test_data)

            # Should return the same dict unchanged
            assert result is test_data

    def test_process_nested_cache_lookups_with_list_field(
        self, respx_entity_store
    ) -> None:
        """Test _process_nested_cache_lookups replaces cached items in lists - covers lines 579-604."""
        # Ensure store is initialized by fixture (type narrowing for Pylance)
        assert Tag._store is not None
        assert Scene._store is not None

        # Clear cache to ensure test isolation
        Tag._store._cache.clear()
        Scene._store._cache.clear()

        # Pre-populate cache with a tag
        tag_data = {"id": "301", "name": "Cached Tag"}
        cached_tag = Tag.from_graphql(tag_data)

        # Verify tag was cached
        cache_key = ("Tag", "301")
        assert cache_key in Tag._store._cache
        assert Tag._store._cache[cache_key].entity is cached_tag

        # Create scene data with tags list containing the cached tag
        scene_data = {
            "id": "403",
            "title": "Test Scene",
            "tags": [
                {"id": "301", "name": "Cached Tag"},  # Should use cached instance
                {"id": "302", "name": "New Tag"},  # Not cached
            ],
        }

        # Process the nested data
        processed = Scene._process_nested_cache_lookups(scene_data)

        # Verify the cached tag was reused (same object reference)
        assert processed["tags"][0] is cached_tag
        # New tag should still be a dict (not yet constructed)
        assert isinstance(processed["tags"][1], dict)
        assert processed["tags"][1]["id"] == "302"

        # Clean up
        Tag._store._cache.clear()
        Scene._store._cache.clear()

    def test_process_nested_cache_lookups_multi_type_union(
        self, respx_entity_store
    ) -> None:
        """Test _process_nested_cache_lookups with multi-type Union - covers branch 571->575."""

        # Create a test model with a field that has multiple non-None types in Union
        class TestModel(StashObject):
            __type_name__ = "TestModel"
            __update_input_type__ = BaseModel
            multi_field: str | int | None | UnsetType = UNSET  # Multiple types

        # Process data - Union won't be unwrapped since len(non_none_args) != 1
        data = {"id": "402", "multi_field": "value"}
        processed = TestModel._process_nested_cache_lookups(data)

        # Data should pass through unchanged (no StashObject to cache)
        assert processed == data

    def test_process_nested_cache_lookups_list_field_non_list_value(
        self, respx_entity_store
    ) -> None:
        """Test _process_nested_cache_lookups with list field but non-list value - covers branch 594->615."""
        # Scene has a tags field that's list[Tag], but we'll provide a non-list value
        scene_data = {
            "id": "404",
            "title": "Test Scene",
            "tags": "not-a-list",  # Wrong type - should be a list
        }

        # Process the data - should handle gracefully
        processed = Scene._process_nested_cache_lookups(scene_data)

        # Non-list value should pass through unchanged
        assert processed["tags"] == "not-a-list"

    def test_process_nested_cache_lookups_expired_list_item(
        self, respx_entity_store
    ) -> None:
        """Test _process_nested_cache_lookups with expired cached list item - covers branch 607->613."""
        # Ensure store is initialized by fixture (type narrowing for Pylance)
        assert Tag._store is not None

        # Clear any existing cache to ensure test isolation
        Tag._store._cache.clear()

        # Pre-populate cache with a tag
        tag_data = {"id": "303", "name": "Expired Tag"}
        cached_tag = Tag.from_graphql(tag_data)

        # Verify tag was cached
        cache_key = ("Tag", "303")
        assert cache_key in Tag._store._cache
        assert Tag._store._cache[cache_key].entity is cached_tag

        # Force the cache entry to expire
        Tag._store._cache[cache_key].ttl_seconds = -1  # Guaranteed expired

        # Create scene data with tags list containing the expired cached tag
        scene_data = {
            "id": "405",
            "title": "Test Scene",
            "tags": [
                {"id": "303", "name": "Expired Tag"},  # Cached but expired
            ],
        }

        # Process the nested data
        processed = Scene._process_nested_cache_lookups(scene_data)

        # Expired tag should NOT be reused (stays as dict)
        assert isinstance(processed["tags"][0], dict)
        assert processed["tags"][0]["id"] == "303"

        # Clean up
        Tag._store._cache.clear()

    def test_process_nested_cache_lookups_expired_single_object(
        self, respx_entity_store
    ) -> None:
        """Test _process_nested_cache_lookups with expired cached single object - covers branch 628->550."""
        # Ensure store is initialized by fixture (type narrowing for Pylance)
        assert Studio._store is not None

        # Clear any existing cache to ensure test isolation
        Studio._store._cache.clear()

        # Pre-populate cache with a studio
        studio_data = {"id": "201", "name": "Test Studio"}
        cached_studio = Studio.from_graphql(studio_data)

        # Verify studio was cached
        cache_key = ("Studio", "201")
        assert cache_key in Studio._store._cache
        assert Studio._store._cache[cache_key].entity is cached_studio

        # Force the cache entry to expire
        Studio._store._cache[cache_key].ttl_seconds = -1  # Guaranteed expired

        # Create scene data with studio field containing the expired cached studio
        scene_data = {
            "id": "406",
            "title": "Test Scene",
            "studio": {"id": "201", "name": "Test Studio"},  # Cached but expired
        }

        # Process the nested data
        processed = Scene._process_nested_cache_lookups(scene_data)

        # Expired studio should NOT be reused (stays as dict)
        assert isinstance(processed["studio"], dict)
        assert processed["studio"]["id"] == "201"

        # Clean up
        Studio._store._cache.clear()

    def test_process_nested_cache_lookups_with_valid_cached_single_object(
        self, respx_entity_store
    ) -> None:
        """Test _process_nested_cache_lookups reuses valid cached single object - covers lines 799-806.

        This is the "happy path" complement to test_process_nested_cache_lookups_expired_single_object.
        When a single nested StashObject field references a cached entity that has NOT expired,
        the cached instance should be reused instead of constructing a new object.

        This covers:
        - Line 800: if cache_key in cls._store._cache (TRUE branch)
        - Line 802: if not cached_entry.is_expired() (TRUE branch)
        - Line 803-805: log.debug statement
        - Line 806: processed[field_name] = cached_entry.entity
        """
        # Ensure store is initialized by fixture (type narrowing for Pylance)
        assert Studio._store is not None
        assert Scene._store is not None

        # Clear any existing cache to ensure test isolation
        Studio._store._cache.clear()
        Scene._store._cache.clear()

        # Pre-populate cache with a studio
        studio_data = {"id": "202", "name": "Cached Studio"}
        cached_studio = Studio.from_graphql(studio_data)

        # Verify studio was cached and NOT expired
        cache_key = ("Studio", "202")
        assert cache_key in Studio._store._cache
        assert Studio._store._cache[cache_key].entity is cached_studio
        assert not Studio._store._cache[cache_key].is_expired()  # Confirm not expired

        # Create scene data with studio field containing a dict reference to the cached studio
        scene_data = {
            "id": "407",
            "title": "Test Scene with Cached Studio",
            "studio": {
                "id": "202",
                "name": "Cached Studio",
            },  # Should reuse cached
        }

        # Process the nested data - this should hit lines 799-806
        processed = Scene._process_nested_cache_lookups(scene_data)

        # Verify the cached studio instance was reused (same object reference)
        assert processed["studio"] is cached_studio
        assert not isinstance(processed["studio"], dict)  # Not a dict anymore
        assert processed["studio"].id == "202"
        assert processed["studio"].name == "Cached Studio"

        # Clean up
        Studio._store._cache.clear()
        Scene._store._cache.clear()

    def test_process_nested_cache_lookups_single_object_not_in_cache(
        self, respx_entity_store
    ) -> None:
        """Test _process_nested_cache_lookups with uncached single object - covers line 800 FALSE branch.

        When a single nested StashObject field references an entity that is NOT in the cache,
        the dict should be left unchanged (not replaced with a cached instance).

        This covers:
        - Line 800: if cache_key in cls._store._cache (FALSE branch)
        """
        # Ensure store is initialized by fixture (type narrowing for Pylance)
        assert Studio._store is not None
        assert Scene._store is not None

        # Clear any existing cache to ensure test isolation
        Studio._store._cache.clear()
        Scene._store._cache.clear()

        # Create scene data with studio field containing a dict reference
        # This studio is NOT pre-cached, so the dict should remain unchanged
        scene_data = {
            "id": "408",
            "title": "Test Scene with Uncached Studio",
            "studio": {
                "id": "203",
                "name": "Uncached Studio",
            },  # NOT in cache
        }

        # Verify the studio is NOT in cache before processing
        cache_key = ("Studio", "203")
        assert cache_key not in Studio._store._cache

        # Process the nested data - should take FALSE branch at line 800
        processed = Scene._process_nested_cache_lookups(scene_data)

        # Verify the studio dict was NOT replaced (stays as dict)
        assert isinstance(processed["studio"], dict)
        assert processed["studio"]["id"] == "203"
        assert processed["studio"]["name"] == "Uncached Studio"

        # Verify it's still not cached after processing
        assert cache_key not in Studio._store._cache

        # Clean up
        Studio._store._cache.clear()
        Scene._store._cache.clear()


class TestMergePathUnionTypeDiscrimination:
    """Regression tests for union-typed list field corruption on merge path.

    Pydantic v2's model_validate() post-processes the returned instance for
    union-typed list fields, overwriting __dict__ with raw input data.  The
    merge path must inoculate the input dict with validated values to prevent
    this corruption.
    """

    @pytest.mark.unit
    def test_visual_files_not_corrupted_on_merge(self, respx_entity_store) -> None:
        """visual_files should contain ImageFile objects after a merge, not raw dicts."""
        raw_data = {
            "id": "900",
            "title": "Merge Test",
            "visual_files": [
                {"__typename": "ImageFile", "id": "901", "path": "/test.jpg"},
            ],
        }

        # First construction — caches the Image
        img1 = Image.from_graphql(raw_data.copy())
        assert isinstance(img1.visual_files[0], ImageFile)

        # Second construction — triggers merge path
        img2 = Image.from_graphql(raw_data.copy())
        assert img2 is img1, "Identity map must return same object"
        assert isinstance(img2.visual_files[0], ImageFile), (
            "visual_files[0] should be ImageFile after merge, not dict"
        )

    @pytest.mark.unit
    def test_identity_preserved_across_merge(self, respx_entity_store) -> None:
        """Merge path must return the same cached instance (identity map contract)."""
        data = {
            "id": "910",
            "title": "Identity Test",
            "visual_files": [
                {"__typename": "ImageFile", "id": "911", "path": "/a.jpg"},
            ],
        }

        img1 = Image.from_graphql(data.copy())
        img2 = Image.from_graphql(data.copy())
        assert img1 is img2

    @pytest.mark.unit
    def test_merge_preserves_fields_absent_from_new_data(
        self, respx_entity_store
    ) -> None:
        """Fields present in cached but absent from new data must survive the merge."""
        full_data = {
            "id": "920",
            "title": "Full Data",
            "rating100": 75,
            "visual_files": [
                {"__typename": "ImageFile", "id": "921", "path": "/b.jpg"},
            ],
        }
        partial_data = {
            "id": "920",
            "title": "Updated Title",
            "visual_files": [
                {"__typename": "ImageFile", "id": "921", "path": "/b.jpg"},
            ],
        }

        img = Image.from_graphql(full_data)
        assert img.rating100 == 75

        merged = Image.from_graphql(partial_data)
        assert merged is img
        assert merged.title == "Updated Title"
        assert merged.rating100 == 75, (
            "rating100 should survive merge when absent from new data"
        )
