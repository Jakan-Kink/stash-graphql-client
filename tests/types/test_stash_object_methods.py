"""Tests for StashObject utility methods and change tracking.

This test suite covers:
- Change tracking: changed_fields(), mark_dirty(), mark_clean()
- Object comparison: __hash__(), __eq__()
- Field utilities: _get_field_names()
- Save/load: find_by_id(), save()
- Relationship/field processing
"""

from __future__ import annotations

from typing import ClassVar
from unittest.mock import AsyncMock, PropertyMock, patch

import httpx
import pytest
import respx
from pydantic import BaseModel

from stash_graphql_client.types.base import StashObject
from stash_graphql_client.types.performer import Performer
from stash_graphql_client.types.scene import Scene
from stash_graphql_client.types.studio import Studio
from stash_graphql_client.types.tag import Tag


class TestChangeTracking:
    """Test change tracking methods."""

    def test_changed_fields_with_field_not_in_current(self, respx_entity_store) -> None:
        """Test changed_fields() when tracked field not in current state - covers line 669."""
        # Create a tag with tracked fields
        tag = Tag.from_graphql({"id": "tag-1", "name": "Original"})
        tag.mark_clean()  # Take snapshot

        # Manually add a field to __tracked_fields__ that doesn't exist
        with patch.object(Tag, "__tracked_fields__", {"nonexistent_field", "name"}):
            # Get changed fields - should skip nonexistent_field
            changed = tag.get_changed_fields()

            # Only name should be in changed (or nothing if it hasn't changed)
            assert "nonexistent_field" not in changed

    def test_changed_fields_with_new_field_added(self, respx_entity_store) -> None:
        """Test changed_fields() detects field in current but not in snapshot - covers lines 671-672."""
        # Create tag and take snapshot
        tag = Tag.from_graphql({"id": "tag-2", "name": "Test"})
        tag.mark_clean()

        # Set up scenario: field is tracked and in current, but NOT in snapshot
        # This simulates a field that was added after snapshot was taken
        with patch.object(Tag, "__tracked_fields__", {"name", "description"}):
            # Set description value (now in current state)
            tag.description = "New description"

            # Manually remove description from snapshot to simulate it not being there originally
            # This is the scenario that lines 671-672 handle
            if "description" in tag._snapshot:
                del tag._snapshot["description"]

            # Get changed fields
            changed = tag.get_changed_fields()

            # description should be detected as changed (field in current but NOT in snapshot)
            # This hits lines 671-672: field not in snapshot, add to changed and continue
            assert "description" in changed
            assert changed["description"] == "New description"

    def test_mark_dirty_clears_snapshot(self, respx_entity_store) -> None:
        """Test mark_dirty() clears snapshot - covers line 694."""
        tag = Tag.from_graphql({"id": "tag-3", "name": "Test"})
        tag.mark_clean()

        # Verify snapshot exists
        assert tag._snapshot != {}

        # Mark dirty
        tag.mark_dirty()

        # Snapshot should be cleared
        assert tag._snapshot == {}


class TestObjectComparison:
    """Test object comparison methods."""

    def test_hash(self, respx_entity_store) -> None:
        """Test __hash__() method - covers line 1107."""
        # Use from_graphql to avoid validator issues
        tag1 = Tag.from_graphql({"id": "tag-hash", "name": "Test"})
        tag2 = Tag.from_graphql({"id": "tag-hash", "name": "Different Name"})

        # Since they have the same ID, tag2 should be the same cached instance as tag1
        assert tag1 is tag2  # Identity map returns same instance

        # Hash should work
        assert hash(tag1) == hash(tag2)

        # Create a different tag to test hash
        tag3 = Tag.from_graphql({"id": "tag-different", "name": "Other"})
        assert hash(tag1) != hash(tag3)

    def test_eq_with_non_stash_object(self, respx_entity_store) -> None:
        """Test __eq__() returns NotImplemented for non-StashObject - covers line 1119."""
        tag = Tag.from_graphql({"id": "tag-eq", "name": "Test"})

        # Comparison with non-StashObject should return NotImplemented
        result = tag.__eq__("not a stash object")
        assert result is NotImplemented

        # Python falls back to other comparisons
        assert tag != "not a stash object"


class TestFieldNames:
    """Test _get_field_names() method."""

    def test_get_field_names_fallback_empty_fields(self, respx_entity_store) -> None:
        """Test _get_field_names() fallback when model_fields is empty - covers line 709."""

        # Create a minimal test model
        class TestModel(StashObject):
            __type_name__ = "TestModel"
            __update_input_type__ = BaseModel

        # Patch model_fields to return empty dict
        with patch.object(TestModel, "model_fields", {}):
            # Delete __field_names__ if it exists to force computation
            if hasattr(TestModel, "__field_names__"):
                delattr(TestModel, "__field_names__")

            # Call _get_field_names()
            field_names = TestModel._get_field_names()

            # Should fallback to {"id"}
            assert field_names == {"id"}

            # Clean up __field_names__ created during the test
            if hasattr(TestModel, "__field_names__"):
                delattr(TestModel, "__field_names__")

    def test_get_field_names_with_non_empty_fields(self, respx_entity_store) -> None:
        """Test _get_field_names() with non-empty model_fields - covers line 711."""

        # Create a minimal test model
        class TestModel(StashObject):
            __type_name__ = "TestModel"
            __update_input_type__ = BaseModel
            id: str = ""
            name: str | None = None

        # Delete __field_names__ if it exists to force computation
        if hasattr(TestModel, "__field_names__"):
            delattr(TestModel, "__field_names__")

        # Call _get_field_names() - should extract from model_fields
        field_names = TestModel._get_field_names()

        # Should include fields from model
        assert "id" in field_names
        assert "name" in field_names

    def test_get_field_names_fallback_exception(self, respx_entity_store) -> None:
        """Test _get_field_names() fallback on exception - covers lines 714-716."""

        class TestModel(StashObject):
            __type_name__ = "TestModel"
            __update_input_type__ = BaseModel

        # Patch model_fields on the instance's class to raise AttributeError
        with patch.object(
            TestModel,
            "model_fields",
            new_callable=PropertyMock,
            side_effect=AttributeError("Test error"),
        ):
            # Delete __field_names__ if it exists to force computation
            if hasattr(TestModel, "__field_names__"):
                delattr(TestModel, "__field_names__")

            # Call _get_field_names()
            field_names = TestModel._get_field_names()

            # Should fallback to {"id"}
            assert field_names == {"id"}

            # Clean up __field_names__ created during the test
            if hasattr(TestModel, "__field_names__"):
                delattr(TestModel, "__field_names__")


class TestFindById:
    """Test find_by_id() method."""

    @pytest.mark.asyncio
    async def test_find_by_id_exception_returns_none(self, respx_stash_client) -> None:
        """Test find_by_id() returns None on exception - covers lines 765-766."""
        # Mock to raise an exception
        respx.post("http://localhost:9999/graphql").mock(
            side_effect=Exception("Network error")
        )

        # Call find_by_id
        result = await Tag.find_by_id(respx_stash_client, "tag-error")

        # Should return None instead of raising
        assert result is None

    @pytest.mark.asyncio
    async def test_find_by_id_uses_fallback_query_for_unknown_type(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """Test find_by_id() builds fallback query for types not in query_map - covers lines 750-757."""

        # Create a custom type not in the query_map
        class CustomType(StashObject):
            __type_name__: ClassVar[str] = "CustomType"
            __update_input_type__: ClassVar[type[BaseModel]] = BaseModel
            __field_names__: ClassVar[set[str]] = {"id", "name"}

        # Mock response
        response_data = {"data": {"findCustomType": {"id": "custom-1", "name": "Test"}}}
        respx.post("http://localhost:9999/graphql").mock(
            return_value=httpx.Response(200, json=response_data)
        )

        # Call find_by_id - should build fallback query since CustomType not in query_map
        result = await CustomType.find_by_id(respx_stash_client, "custom-1")

        # Should return the object
        assert result is not None
        assert result.id == "custom-1"


class TestSaveMethod:
    """Test save() method and related functionality."""

    @pytest.mark.asyncio
    async def test_save_returns_early_when_not_dirty_and_not_new(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """Test save() returns early when object is clean and not new - covers line 783."""
        # Create and save a tag (so it's not new)
        tag = Tag.from_graphql({"id": "123", "name": "Test"})
        tag.mark_clean()  # Mark as clean

        # Ensure it's not new and not dirty
        assert not tag.is_new()
        assert not tag.is_dirty()

        # Call save - should return early without making any requests
        await tag.save(respx_stash_client)

        # No GraphQL requests should have been made
        # (If any were made, respx would error since we didn't mock anything)

    @pytest.mark.asyncio
    async def test_save_raises_when_to_input_returns_non_dict(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """Test save() raises ValueError when to_input() returns non-dict - covers lines 790-792."""
        # Create a new tag
        tag = Tag.new(name="Test")

        # Patch to_input at class level to return non-dict
        with (
            patch.object(
                Tag, "to_input", new_callable=AsyncMock, return_value="not a dict"
            ),
            pytest.raises(ValueError, match=r"to_input\(\) must return a dict"),
        ):
            await tag.save(respx_stash_client)

    @pytest.mark.asyncio
    async def test_save_returns_when_only_id_in_input_for_existing_object(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """Test save() returns when only ID present for existing object - covers lines 796-798."""
        # Create an existing tag (not new)
        tag = Tag.from_graphql({"id": "456", "name": "Existing"})
        tag.mark_dirty()  # Mark as dirty

        # Patch to_input to return only ID
        with patch.object(
            Tag, "to_input", new_callable=AsyncMock, return_value={"id": "456"}
        ):
            # Save should return early without making GraphQL request
            await tag.save(respx_stash_client)

            # Object should be marked clean
            assert not tag.is_dirty()

    @pytest.mark.asyncio
    async def test_save_raises_when_operation_key_missing_from_response(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """Test save() raises when operation key missing from response - covers lines 818."""
        # Create a new tag
        tag = Tag.new(name="Test")

        # Mock response missing the operation key
        respx.post("http://localhost:9999/graphql").mock(
            return_value=httpx.Response(
                200, json={"data": {"wrong_key": {"id": "123"}}}
            )
        )

        with pytest.raises(ValueError, match="Missing 'tagCreate' in response"):
            await tag.save(respx_stash_client)

    @pytest.mark.asyncio
    async def test_save_raises_when_operation_result_is_none(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """Test save() raises when operation result is None - covers line 822."""
        # Create a new tag
        tag = Tag.new(name="Test")

        # Mock response with None result
        respx.post("http://localhost:9999/graphql").mock(
            return_value=httpx.Response(200, json={"data": {"tagCreate": None}})
        )

        with pytest.raises(ValueError, match="Create operation returned None"):
            await tag.save(respx_stash_client)

    @pytest.mark.asyncio
    async def test_save_wraps_exceptions(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """Test save() wraps exceptions - covers lines 831-832."""
        # Create a new tag
        tag = Tag.new(name="Test")

        # Mock to raise exception
        respx.post("http://localhost:9999/graphql").mock(
            side_effect=Exception("Network error")
        )

        with pytest.raises(ValueError, match="Failed to save Tag"):
            await tag.save(respx_stash_client)

    @pytest.mark.asyncio
    async def test_save_new_object_updates_id_and_marks_clean(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """Test save() updates ID and marks clean for new objects - covers lines 1192-1193."""
        # Create a new tag (will have UUID)
        tag = Tag.new(name="New Tag")
        original_id = tag.id
        assert tag.is_new()

        # Mock successful create response
        respx.post("http://localhost:9999/graphql").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "tagCreate": {
                            "id": "server-assigned-123",
                            "name": "New Tag",
                        }
                    }
                },
            )
        )

        # Save should update ID and mark clean
        await tag.save(respx_stash_client)

        # Verify ID was updated from UUID to server ID
        assert tag.id == "server-assigned-123"
        assert tag.id != original_id
        assert not tag.is_new()

        # Verify object is marked clean
        assert not tag.is_dirty()

    @pytest.mark.asyncio
    async def test_save_existing_object_skips_update_id_and_marks_clean(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """Test save() skips update_id for existing objects - covers lines 1192->1196."""
        # Create an existing tag (not new)
        tag = Tag.from_graphql({"id": "existing-123", "name": "Existing Tag"})
        tag.mark_clean()

        # Modify the tag to make it dirty
        tag.name = "Updated Tag"
        assert tag.is_dirty()
        assert not tag.is_new()

        # Mock successful update response
        respx.post("http://localhost:9999/graphql").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "tagUpdate": {
                            "id": "existing-123",
                            "name": "Updated Tag",
                        }
                    }
                },
            )
        )

        # Save should NOT update ID (already has server ID) but should mark clean
        await tag.save(respx_stash_client)

        # Verify ID was NOT changed
        assert tag.id == "existing-123"

        # Verify object is marked clean
        assert not tag.is_dirty()


class TestGetId:
    """Test _get_id() static method."""

    @pytest.mark.asyncio
    async def test_get_id_with_dict(self) -> None:
        """Test _get_id() with dict input - covers line 845."""
        result = await Tag._get_id({"id": "dict-id", "name": "Test"})
        assert result == "dict-id"

    @pytest.mark.asyncio
    async def test_get_id_with_awaitable_attrs(self, respx_entity_store) -> None:
        """Test _get_id() with object having awaitable_attrs - covers line 847."""

        # Create a simple class that has awaitable_attrs
        class MockAwaitableAttrs:
            async def __getattribute__(self, name):
                # Make attribute access awaitable
                if name == "id":
                    return "awaitable-id"
                return super().__getattribute__(name)

        class MockObj:
            awaitable_attrs = MockAwaitableAttrs()
            id = "regular-id"

        mock_obj = MockObj()

        # Call _get_id - should await awaitable_attrs.id (line 847)
        # then return getattr(obj, "id", None)
        result = await Tag._get_id(mock_obj)

        # Should return the regular id attribute (line 848)
        assert result == "regular-id"


class TestProcessListRelationship:
    """Test _process_list_relationship() method."""

    @pytest.mark.asyncio
    async def test_process_list_relationship_with_sync_transform(
        self, respx_entity_store
    ) -> None:
        """Test _process_list_relationship() with sync (non-async) transform - covers line 881."""

        scene = Scene.new(title="Test")

        # Create test data
        test_items = ["item1", "item2", "item3"]

        # Sync transform function
        def sync_transform(value):
            return f"transformed-{value}"

        # Call the method
        result = await scene._process_list_relationship(test_items, sync_transform)

        # Should have transformed all items using sync function
        assert result == ["transformed-item1", "transformed-item2", "transformed-item3"]

    @pytest.mark.asyncio
    async def test_process_list_relationship_with_falsy_transform_result(
        self, respx_entity_store
    ) -> None:
        """Test _process_list_relationship() skips items when transform returns falsy - covers line 882->875."""

        scene = Scene.new(title="Test")

        # Create test data
        test_items = ["keep", "skip", "keep"]

        # Transform that returns None for "skip"
        def conditional_transform(value):
            if value == "skip":
                return None  # Falsy value
            return value

        # Call the method
        result = await scene._process_list_relationship(
            test_items, conditional_transform
        )

        # Should only include items where transform returned truthy
        assert result == ["keep", "keep"]

    @pytest.mark.asyncio
    async def test_process_list_relationship_with_none_transform(
        self, respx_entity_store
    ) -> None:
        """Test _process_list_relationship() loops but skips processing when transform is None - covers line 876->875."""
        scene = Scene.new(title="Test")

        # Create test data
        test_items = ["item1", "item2"]

        # Call with transform=None - should loop through items but not process them
        result = await scene._process_list_relationship(test_items, None)

        # Should return empty list (items not processed without transform)
        assert result == []


class TestProcessSingleRelationship:
    """Test _process_single_relationship() method."""

    @pytest.mark.asyncio
    async def test_process_single_relationship_with_falsy_value(
        self, respx_entity_store
    ) -> None:
        """Test _process_single_relationship() returns None for falsy value - covers line 863."""
        tag = Tag.new(name="Test")

        # Call with None/falsy value
        result = await tag._process_single_relationship(None, lambda x: x.id)
        assert result is None

    @pytest.mark.asyncio
    async def test_process_single_relationship_with_sync_transform(
        self, respx_entity_store
    ) -> None:
        """Test _process_single_relationship() with sync transform - covers line 869."""
        tag = Tag.new(name="Test")

        # Sync transform function
        def sync_transform(value):
            return f"transformed-{value}"

        result = await tag._process_single_relationship("test", sync_transform)
        assert result == "transformed-test"

    @pytest.mark.asyncio
    async def test_process_single_relationship_returns_none_when_no_transform(
        self, respx_entity_store
    ) -> None:
        """Test _process_single_relationship() returns None when transform is None - covers line 872."""
        tag = Tag.new(name="Test")

        # Call with no transform (None)
        result = await tag._process_single_relationship("value", None)
        assert result is None


class TestProcessRelationships:
    """Test _process_relationships() method."""

    @pytest.mark.asyncio
    async def test_process_relationships_with_list_value(
        self, respx_entity_store
    ) -> None:
        """Test _process_relationships() with list relationship - covers line 942."""

        # Create scene with tags (list relationship)
        scene = Scene.new(title="Test")
        tag1 = Tag.from_graphql({"id": "tag-1", "name": "Tag1"})
        tag2 = Tag.from_graphql({"id": "tag-2", "name": "Tag2"})
        scene.tags = [tag1, tag2]

        # Process relationships
        result = await scene._process_relationships({"tags"})

        # Should have processed the list
        assert "tag_ids" in result
        assert result["tag_ids"] == ["tag-1", "tag-2"]

    @pytest.mark.asyncio
    async def test_process_relationships_with_none_value(
        self, respx_entity_store
    ) -> None:
        """Test _process_relationships() with None value to clear relationship - covers line 940."""

        # Create scene with studio set to None (clearing the relationship)
        scene = Scene.new(title="Test")
        scene.studio = None

        # Process relationships
        result = await scene._process_relationships({"studio"})

        # Should have set studio_id to None
        assert "studio_id" in result
        assert result["studio_id"] is None

    @pytest.mark.asyncio
    async def test_process_relationships_with_falsy_single_transform_result(
        self, respx_entity_store
    ) -> None:
        """Test _process_relationships() when single relationship transform returns falsy - covers line 932->903."""
        # Create scene with studio
        scene = Scene.new(title="Test")
        studio = Studio.new(name="Test Studio")
        scene.studio = studio

        # Patch the __relationships__ to use a transform that returns None
        original_relationships = Scene.__relationships__.copy()

        # Transform that returns None (falsy)
        def falsy_transform(value):
            return None

        # Modify relationships to use our falsy transform
        modified_relationships = original_relationships.copy()
        modified_relationships["studio"] = ("studio_id", False, falsy_transform)

        with patch.object(Scene, "__relationships__", modified_relationships):
            # Process relationships - transform will return None
            result = await scene._process_relationships({"studio"})

            # When transform returns falsy, field should NOT be added to result
            assert "studio_id" not in result


class TestProcessFields:
    """Test _process_fields() method."""

    @pytest.mark.asyncio
    async def test_process_fields_handles_converter_exception(
        self, respx_entity_store
    ) -> None:
        """Test _process_fields() catches converter exceptions - covers line 986."""

        # Create a tag with a field converter that raises
        tag = Tag.new(name="Test")

        # Add a field that will be converted
        tag.rating100 = 50

        # Create a converter that raises ValueError
        def bad_converter(value):
            raise ValueError("Test error")

        # Patch the field conversions dict to add our bad converter
        with patch.dict(Tag.__field_conversions__, {"rating100": bad_converter}):
            # Call _process_fields - should catch the exception
            result = await tag._process_fields({"rating100"})

            # rating100 should not be in result due to exception
            assert "rating100" not in result

    @pytest.mark.asyncio
    async def test_process_fields_when_field_missing_on_object(
        self, respx_entity_store
    ) -> None:
        """Test _process_fields() when field doesn't exist on object - covers line 954->950."""
        tag = Tag.new(name="Test")

        # Add a converter for a field that doesn't exist on the object
        with patch.dict(
            Tag.__field_conversions__, {"nonexistent_field": lambda x: str(x)}
        ):
            # Process fields including the nonexistent one
            result = await tag._process_fields({"nonexistent_field", "name"})

            # nonexistent_field should not be in result (hasattr is False)
            assert "nonexistent_field" not in result

    @pytest.mark.asyncio
    async def test_process_fields_when_converter_is_none(
        self, respx_entity_store
    ) -> None:
        """Test _process_fields() when converter is None - covers line 967->950."""
        tag = Tag.new(name="Test")
        tag.rating100 = 50

        # Set converter to None
        with patch.dict(Tag.__field_conversions__, {"rating100": None}):
            result = await tag._process_fields({"rating100"})

            # rating100 should not be in result (converter is None)
            assert "rating100" not in result

    @pytest.mark.asyncio
    async def test_process_fields_when_converter_not_callable(
        self, respx_entity_store
    ) -> None:
        """Test _process_fields() when converter is not callable - covers line 967->950."""
        tag = Tag.new(name="Test")
        tag.rating100 = 50

        # Set converter to a non-callable value
        with patch.dict(Tag.__field_conversions__, {"rating100": "not callable"}):
            result = await tag._process_fields({"rating100"})

            # rating100 should not be in result (converter is not callable)
            assert "rating100" not in result

    @pytest.mark.asyncio
    async def test_process_fields_when_converter_returns_none(
        self, respx_entity_store
    ) -> None:
        """Test _process_fields() when converter returns None - covers line 969->950."""
        tag = Tag.new(name="Test")
        tag.rating100 = 50

        # Converter that returns None
        def none_converter(value):
            return None

        with patch.dict(Tag.__field_conversions__, {"rating100": none_converter}):
            result = await tag._process_fields({"rating100"})

            # rating100 should not be in result (converter returned None)
            assert "rating100" not in result

    @pytest.mark.asyncio
    async def test_process_fields_skips_field_without_conversion(
        self, respx_entity_store
    ) -> None:
        """Test _process_fields() skips fields not in __field_conversions__ - covers line 1344."""
        # Create a tag
        tag = Tag.from_graphql({"id": "tag-1", "name": "Test", "favorite": False})
        tag.mark_clean()

        # Modify a field that's tracked but NOT in __field_conversions__
        tag.favorite = (
            True  # favorite is in __tracked_fields__ but NOT __field_conversions__
        )

        # Get dirty fields
        dirty_fields = set(tag.get_changed_fields().keys())
        assert "favorite" in dirty_fields

        # Process these fields - favorite should be skipped (not in conversions)
        result = await tag._process_fields(dirty_fields)

        # favorite should not be in result (it was skipped by the continue)
        assert "favorite" not in result


class TestToInputAll:
    """Test _to_input_all() method."""

    @pytest.mark.asyncio
    async def test_to_input_all_raises_when_creation_not_supported(
        self, respx_entity_store
    ) -> None:
        """Test _to_input_all() raises when creation not supported - covers lines 1044."""

        # Create a type that doesn't support creation
        class NoCreateType(StashObject):
            __type_name__ = "NoCreateType"
            __update_input_type__ = BaseModel
            __create_input_type__ = None  # No creation support

        obj = NoCreateType.new()

        # Try to create input for new object
        with pytest.raises(ValueError, match="objects cannot be created, only updated"):
            await obj._to_input_all()


class TestCircularReferenceProtection:
    """Test that dirty checking works with bidirectional relationships."""

    def test_is_dirty_with_circular_reference(self) -> None:
        """Test is_dirty() doesn't fail when bidirectional relationships exist."""
        # Create scene and performer with bidirectional relationship
        scene = Scene.model_construct(
            id="scene-1",
            title="Test Scene",
            urls=[],
            performers=[],
        )
        performer = Performer.model_construct(
            id="perf-1",
            name="Test Performer",
            tags=[],
            parents=[],
            children=[],
            scenes=[],
        )

        # Take initial snapshot
        scene._snapshot = {
            field: getattr(scene, field, None) for field in scene.__tracked_fields__
        }
        performer._snapshot = {
            field: getattr(performer, field, None)
            for field in performer.__tracked_fields__
        }

        # Create bidirectional relationship (this would cause circular ref with model_dump)
        scene.performers = [performer]
        performer.scenes = [scene]

        # is_dirty() should work without ValueError: Circular reference detected
        try:
            scene_dirty = scene.is_dirty()
            perf_dirty = performer.is_dirty()

            # Scene should be dirty (performers is tracked)
            # Performer should NOT be dirty (scenes is NOT tracked - read-only field)
            assert scene_dirty is True
            assert perf_dirty is False  # scenes not in __tracked_fields__
        except ValueError as e:
            if "Circular reference" in str(e):
                pytest.fail(f"is_dirty() raised circular reference error: {e}")
            raise

    def test_get_changed_fields_with_circular_reference(self) -> None:
        """Test get_changed_fields() works with bidirectional relationships."""
        # Create scene with snapshot
        scene = Scene.model_construct(
            id="scene-2",
            title="Original Title",
            urls=[],
            performers=[],
        )
        scene._snapshot = {
            field: getattr(scene, field, None) for field in scene.__tracked_fields__
        }

        # Create performer and link bidirectionally
        performer = Performer.model_construct(
            id="perf-2",
            name="Test Performer",
            tags=[],
            parents=[],
            children=[],
            scenes=[scene],
        )
        scene.performers = [performer]

        # get_changed_fields() should work without circular reference error
        try:
            changed = scene.get_changed_fields()

            # Should detect performers changed
            assert "performers" in changed
            assert changed["performers"] == [performer]
        except ValueError as e:
            if "Circular reference" in str(e):
                pytest.fail(
                    f"get_changed_fields() raised circular reference error: {e}"
                )
            raise

    def test_mark_clean_with_circular_reference(self) -> None:
        """Test mark_clean() works with bidirectional relationships."""
        # Create bidirectional relationship
        scene = Scene.model_construct(
            id="scene-3",
            title="Test",
            urls=[],
            performers=[],
        )
        performer = Performer.model_construct(
            id="perf-3",
            name="Test",
            tags=[],
            parents=[],
            children=[],
            scenes=[scene],
        )
        scene.performers = [performer]

        # mark_clean() should work without circular reference error
        try:
            scene.mark_clean()

            # After marking clean, should not be dirty
            assert scene.is_dirty() is False
        except ValueError as e:
            if "Circular reference" in str(e):
                pytest.fail(f"mark_clean() raised circular reference error: {e}")
            raise
