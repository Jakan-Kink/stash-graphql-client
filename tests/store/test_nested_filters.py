"""Tests for nested field filtering in StashEntityStore.

Tests the Django-style double-underscore syntax for nested field specifications:
- _parse_nested_field(): Parse 'files__path' → ['files', 'path']
- _check_nested_field_present(): Recursively check if nested path is populated
- missing_fields_nested(): Check which nested field specs are missing
- populate(): Recursively populate nested fields
- All filter methods: Support nested field specs

Following TESTING_REQUIREMENTS.md:
- Mock only at HTTP boundary using respx
- Use FactoryBoy factories for test objects
- Verify both request and response in GraphQL mocks
"""

import logging

import httpx
import pytest
import respx

from stash_graphql_client import Image, StashEntityStore
from stash_graphql_client.types import Gallery, GalleryChapter, Scene
from stash_graphql_client.types.unset import UNSET
from tests.fixtures.stash import (
    ImageFactory,
    ImageFileFactory,
    SceneFactory,
    StudioFactory,
    create_graphql_response,
)


# =============================================================================
# Unit Tests - Nested Field Parsing
# =============================================================================


class TestNestedFieldParsing:
    """Tests for _parse_nested_field() static method."""

    def test_parse_single_field(self, respx_entity_store: StashEntityStore) -> None:
        """Test parsing a single field (no nesting)."""
        store = respx_entity_store
        result = store._parse_nested_field("rating100")
        assert result == ["rating100"]

    def test_parse_two_level_nesting(
        self, respx_entity_store: StashEntityStore
    ) -> None:
        """Test parsing two-level nested field."""
        store = respx_entity_store
        result = store._parse_nested_field("files__path")
        assert result == ["files", "path"]

    def test_parse_three_level_nesting(
        self, respx_entity_store: StashEntityStore
    ) -> None:
        """Test parsing three-level nested field."""
        store = respx_entity_store
        result = store._parse_nested_field("studio__parent__name")
        assert result == ["studio", "parent", "name"]


# =============================================================================
# Unit Tests - Nested Field Presence Checking
# =============================================================================


class TestNestedFieldPresenceChecking:
    """Tests for _check_nested_field_present() method."""

    def test_check_single_field_present(
        self, respx_entity_store: StashEntityStore
    ) -> None:
        """Test checking single field that is present."""
        store = respx_entity_store

        studio = StudioFactory.build(id="1", name="Acme", rating100=90)
        object.__setattr__(studio, "_received_fields", {"id", "name", "rating100"})
        store._cache_entity(studio)

        assert store._check_nested_field_present(studio, ["rating100"]) is True

    def test_check_single_field_unset(
        self, respx_entity_store: StashEntityStore
    ) -> None:
        """Test checking single field that is UNSET."""
        store = respx_entity_store

        # Build without rating100, then it will be UNSET by default
        studio = StudioFactory.build(id="1", name="Acme")
        object.__setattr__(studio, "_received_fields", {"id", "name"})
        # Explicitly set rating100 to UNSET after construction
        object.__setattr__(studio, "rating100", UNSET)
        store._cache_entity(studio)

        assert store._check_nested_field_present(studio, ["rating100"]) is False

    def test_check_nested_field_both_present(
        self, respx_entity_store: StashEntityStore
    ) -> None:
        """Test checking nested field where both levels are present."""
        store = respx_entity_store

        # Create parent studio with name populated
        parent = StudioFactory.build(id="parent-1", name="Parent Studio")
        object.__setattr__(parent, "_received_fields", {"id", "name"})
        store._cache_entity(parent)

        # Create child studio with parent populated
        child = StudioFactory.build(id="child-1", name="Child Studio", parent=parent)
        object.__setattr__(child, "_received_fields", {"id", "name", "parent"})
        store._cache_entity(child)

        # Check nested path: studio -> parent -> name
        assert store._check_nested_field_present(child, ["parent", "name"]) is True

    def test_check_nested_field_root_unset(
        self, respx_entity_store: StashEntityStore
    ) -> None:
        """Test checking nested field where root relationship is UNSET."""
        store = respx_entity_store

        # Studio with parent=UNSET
        studio = StudioFactory.build(id="1", name="Acme", parent=UNSET)
        object.__setattr__(studio, "_received_fields", {"id", "name"})
        store._cache_entity(studio)

        assert store._check_nested_field_present(studio, ["parent", "name"]) is False

    def test_check_nested_field_root_none(
        self, respx_entity_store: StashEntityStore
    ) -> None:
        """Test checking nested field where root relationship is None (no parent)."""
        store = respx_entity_store

        # Studio with parent=None (actually has no parent)
        studio = StudioFactory.build(id="1", name="Acme", parent=None)
        object.__setattr__(studio, "_received_fields", {"id", "name", "parent"})
        store._cache_entity(studio)

        # Should return True because parent is populated (it's just null)
        assert store._check_nested_field_present(studio, ["parent", "name"]) is True

    def test_check_nested_field_leaf_unset(
        self, respx_entity_store: StashEntityStore
    ) -> None:
        """Test checking nested field where leaf field is UNSET."""
        store = respx_entity_store

        # Parent with name=UNSET
        parent = StudioFactory.build(id="parent-1", name=UNSET)
        object.__setattr__(parent, "_received_fields", {"id"})
        store._cache_entity(parent)

        # Child with parent populated
        child = StudioFactory.build(id="child-1", name="Child", parent=parent)
        object.__setattr__(child, "_received_fields", {"id", "name", "parent"})
        store._cache_entity(child)

        # Nested path should fail because parent.name is UNSET
        assert store._check_nested_field_present(child, ["parent", "name"]) is False

    def test_check_nested_field_list_all_present(
        self, respx_entity_store: StashEntityStore
    ) -> None:
        """Test checking nested field on list where all items have the field."""
        store = respx_entity_store

        # Create files with path populated
        file1 = ImageFileFactory.build(id="f1", path="/path/to/image1.jpg")
        file2 = ImageFileFactory.build(id="f2", path="/path/to/image2.jpg")

        for f in [file1, file2]:
            object.__setattr__(f, "_received_fields", {"id", "path"})
            store._cache_entity(f)

        # Create image with files populated
        image = ImageFactory.build(id="img1", title="Test", files=[file1, file2])
        object.__setattr__(image, "_received_fields", {"id", "title", "files"})
        store._cache_entity(image)

        # Check nested path: image -> files -> path
        assert store._check_nested_field_present(image, ["files", "path"]) is True

    def test_check_nested_field_list_one_missing(
        self, respx_entity_store: StashEntityStore
    ) -> None:
        """Test checking nested field on list where one item is missing the field."""
        store = respx_entity_store

        # file1 has path, file2 has path=UNSET
        file1 = ImageFileFactory.build(id="f1", path="/path/to/image1.jpg")
        object.__setattr__(file1, "_received_fields", {"id", "path"})
        store._cache_entity(file1)

        file2 = ImageFileFactory.build(id="f2", path=UNSET)
        object.__setattr__(file2, "_received_fields", {"id"})
        store._cache_entity(file2)

        # Image with both files
        image = ImageFactory.build(id="img1", title="Test", files=[file1, file2])
        object.__setattr__(image, "_received_fields", {"id", "title", "files"})
        store._cache_entity(image)

        # Should fail because file2.path is UNSET
        assert store._check_nested_field_present(image, ["files", "path"]) is False


class TestMissingFieldsNested:
    """Tests for missing_fields_nested() method."""

    def test_missing_fields_nested_all_present(
        self, respx_entity_store: StashEntityStore
    ) -> None:
        """Test missing_fields_nested when all fields are present."""
        store = respx_entity_store

        studio = StudioFactory.build(id="1", name="Acme", rating100=90)
        object.__setattr__(studio, "_received_fields", {"id", "name", "rating100"})
        store._cache_entity(studio)

        missing = store.missing_fields_nested(studio, "name", "rating100")
        assert missing == set()

    def test_missing_fields_nested_some_missing(
        self, respx_entity_store: StashEntityStore
    ) -> None:
        """Test missing_fields_nested when some fields are missing."""
        store = respx_entity_store

        # Build without rating100, then explicitly set to UNSET
        studio = StudioFactory.build(id="1", name="Acme")
        object.__setattr__(studio, "_received_fields", {"id", "name"})
        object.__setattr__(studio, "rating100", UNSET)
        store._cache_entity(studio)

        missing = store.missing_fields_nested(studio, "name", "rating100")
        assert missing == {"rating100"}

    def test_missing_fields_nested_with_nested_spec(
        self, respx_entity_store: StashEntityStore
    ) -> None:
        """Test missing_fields_nested with nested field specification."""
        store = respx_entity_store

        # Parent with name=UNSET
        parent = StudioFactory.build(id="parent-1", name=UNSET)
        object.__setattr__(parent, "_received_fields", {"id"})
        store._cache_entity(parent)

        # Child with parent populated
        child = StudioFactory.build(id="child-1", name="Child", parent=parent)
        object.__setattr__(child, "_received_fields", {"id", "name", "parent"})
        store._cache_entity(child)

        # Check for 'parent__name' - should be missing
        missing = store.missing_fields_nested(child, "parent__name")
        assert missing == {"parent__name"}

    def test_missing_fields_nested_mixed_regular_and_nested(
        self, respx_entity_store: StashEntityStore
    ) -> None:
        """Test missing_fields_nested with mix of regular and nested specs."""
        store = respx_entity_store

        parent = StudioFactory.build(id="parent-1", name="Parent")
        object.__setattr__(parent, "_received_fields", {"id", "name"})
        store._cache_entity(parent)

        # Build without rating100, then explicitly set to UNSET
        child = StudioFactory.build(id="child-1", name="Child", parent=parent)
        object.__setattr__(child, "_received_fields", {"id", "name", "parent"})
        object.__setattr__(child, "rating100", UNSET)
        store._cache_entity(child)

        # Check mix: 'rating100' (regular), 'parent__name' (nested)
        missing = store.missing_fields_nested(child, "rating100", "parent__name")

        # Only rating100 should be missing, parent__name is present
        assert missing == {"rating100"}


# =============================================================================
# Integration Tests - populate() with Nested Fields
# =============================================================================


class TestPopulateWithNestedFields:
    """Tests for populate() method with nested field specifications.

    Note: Full populate() integration tests are in test_advanced_filters.py.
    These tests focus on nested field parsing and specification handling.
    """

    def test_populate_parses_nested_field_specs(
        self, respx_entity_store: StashEntityStore
    ) -> None:
        """Test that populate() correctly separates nested field specs from regular fields."""
        store = respx_entity_store

        # This is a unit test that verifies the parsing logic
        # The actual population is tested in integration tests

        # Create a simple studio for testing
        studio = StudioFactory.build(id="1", name="Test")
        object.__setattr__(studio, "_received_fields", {"id", "name"})
        store._cache_entity(studio)

        # Verify the nested field parsing works
        assert store._parse_nested_field("parent__name") == ["parent", "name"]
        assert store._parse_nested_field("parent__parent__name") == [
            "parent",
            "parent",
            "name",
        ]

    def test_populate_handles_mixed_field_specs(
        self, respx_entity_store: StashEntityStore
    ) -> None:
        """Test that populate() can handle mix of regular and nested specs."""
        store = respx_entity_store

        # Verify missing_fields_nested works with mixed specs
        studio = StudioFactory.build(id="1", name="Test")
        object.__setattr__(studio, "_received_fields", {"id", "name"})
        object.__setattr__(studio, "rating100", UNSET)
        object.__setattr__(studio, "parent", UNSET)
        store._cache_entity(studio)

        # Check that both regular and nested missing fields are detected
        missing = store.missing_fields_nested(studio, "rating100", "parent__name")
        # Both should be missing (rating100 is UNSET, parent is UNSET)
        assert "rating100" in missing
        assert "parent__name" in missing


# =============================================================================
# Integration Tests - Filter Methods with Nested Fields
# =============================================================================


class TestFilterStrictWithNestedFields:
    """Tests for filter_strict() with nested field specifications."""

    def test_filter_strict_nested_all_present(
        self, respx_entity_store: StashEntityStore
    ) -> None:
        """Test filter_strict with nested fields when all are present."""
        store = respx_entity_store

        # Create files with path populated
        file1 = ImageFileFactory.build(id="f1", path="/path1.jpg", size=1024)
        file2 = ImageFileFactory.build(id="f2", path="/path2.jpg", size=2048)
        for f in [file1, file2]:
            object.__setattr__(f, "_received_fields", {"id", "path", "size"})
            store._cache_entity(f)

        # Image with files populated
        image = ImageFactory.build(id="img1", title="Test", files=[file1, file2])
        object.__setattr__(image, "_received_fields", {"id", "title", "files"})
        store._cache_entity(image)

        # Should succeed because files__path is fully populated
        results = store.filter_strict(
            Image,
            required_fields=["files__path", "files__size"],
            predicate=lambda i: any(f.size > 1500 for f in i.files),
        )

        assert len(results) == 1
        assert results[0].id == "img1"

    def test_filter_strict_nested_missing_raises(
        self, respx_entity_store: StashEntityStore
    ) -> None:
        """Test filter_strict raises when nested field is missing."""
        store = respx_entity_store

        # File with path=UNSET
        file1 = ImageFileFactory.build(id="f1", path=UNSET, size=1024)
        object.__setattr__(file1, "_received_fields", {"id", "size"})
        store._cache_entity(file1)

        # Image with files populated
        image = ImageFactory.build(id="img1", title="Test", files=[file1])
        object.__setattr__(image, "_received_fields", {"id", "title", "files"})
        store._cache_entity(image)

        # Should raise because file1.path is UNSET
        with pytest.raises(ValueError, match="missing required fields"):
            store.filter_strict(
                Image,
                required_fields=["files__path"],
                predicate=lambda i: True,
            )


class TestFilterAndPopulateWithNestedFields:
    """Tests for filter_and_populate() with nested field specifications."""

    @pytest.mark.asyncio
    async def test_filter_and_populate_nested_auto_fetches(
        self, respx_mock, respx_entity_store: StashEntityStore
    ) -> None:
        """Test filter_and_populate auto-fetches missing nested fields."""
        store = respx_entity_store

        # File with path=UNSET
        file1 = ImageFileFactory.build(id="f1", path=UNSET, size=UNSET)
        object.__setattr__(file1, "_received_fields", {"id"})
        store._cache_entity(file1)

        # Image with files populated
        image = ImageFactory.build(id="img1", title="Test", files=[file1])
        object.__setattr__(image, "_received_fields", {"id", "title", "files"})
        store._cache_entity(image)

        # Mock GraphQL: Two file fetches (populate calls each nested field separately)
        # Each fetch returns the complete file data (GraphQL returns all fields queried)
        file_response_complete = {
            "__typename": "ImageFile",
            "id": "f1",
            "path": "/large.jpg",
            "size": 5_000_000,
            "width": 1920,
            "height": 1080,
            "format": "jpg",
        }

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                # First populate call for 'path' field
                httpx.Response(
                    200,
                    json=create_graphql_response("findFile", file_response_complete),
                ),
                # Second populate call for 'size' field
                httpx.Response(
                    200,
                    json=create_graphql_response("findFile", file_response_complete),
                ),
            ]
        )

        # Filter with nested field - should auto-populate
        results = await store.filter_and_populate(
            Image,
            required_fields=["files__path", "files__size"],
            predicate=lambda i: any(
                f.size > 1_000_000 for f in i.files if f.size is not UNSET
            ),
        )

        # Should make GraphQL calls to populate missing nested fields
        assert len(graphql_route.calls) >= 1

        # Should find the match
        assert len(results) == 1
        assert results[0].files[0].size == 5_000_000


# =============================================================================
# Edge Cases
# =============================================================================


class TestNestedFieldEdgeCases:
    """Tests for edge cases in nested field handling."""

    def test_nested_field_with_empty_list(
        self, respx_entity_store: StashEntityStore
    ) -> None:
        """Test nested field check on empty list."""
        store = respx_entity_store

        # Image with empty files list
        image = ImageFactory.build(id="img1", title="Test", files=[])
        object.__setattr__(image, "_received_fields", {"id", "title", "files"})
        store._cache_entity(image)

        # Should return True (list is populated, just empty)
        assert store._check_nested_field_present(image, ["files", "path"]) is True

    def test_nested_field_three_levels(
        self, respx_entity_store: StashEntityStore
    ) -> None:
        """Test nested field with three levels of nesting."""
        store = respx_entity_store

        # Grandparent
        grandparent = StudioFactory.build(id="gp", name="Grandparent", parent=None)
        object.__setattr__(grandparent, "_received_fields", {"id", "name", "parent"})
        store._cache_entity(grandparent)

        # Parent
        parent = StudioFactory.build(id="p", name="Parent", parent=grandparent)
        object.__setattr__(parent, "_received_fields", {"id", "name", "parent"})
        store._cache_entity(parent)

        # Child
        child = StudioFactory.build(id="c", name="Child", parent=parent)
        object.__setattr__(child, "_received_fields", {"id", "name", "parent"})
        store._cache_entity(child)

        # Check three-level path: child -> parent -> parent -> name
        # This checks: child.parent.parent.name
        assert (
            store._check_nested_field_present(child, ["parent", "parent", "name"])
            is True
        )

    def test_check_nested_field_empty_path(
        self, respx_entity_store: StashEntityStore
    ) -> None:
        """Test checking nested field with empty path (edge case)."""
        store = respx_entity_store

        studio = StudioFactory.build(id="1", name="Test")
        store._cache_entity(studio)

        # Empty path should return True (nothing to check)
        assert store._check_nested_field_present(studio, []) is True

    def test_check_nested_field_object_missing_field(
        self, respx_entity_store: StashEntityStore
    ) -> None:
        """Test checking nested field when object doesn't have the field at all."""
        store = respx_entity_store

        studio = StudioFactory.build(id="1", name="Test")
        object.__setattr__(studio, "_received_fields", {"id", "name"})
        store._cache_entity(studio)

        # Try to check a field that doesn't exist on Studio type
        # This simulates a typo or API version mismatch
        assert store._check_nested_field_present(studio, ["nonexistent_field"]) is False

    def test_check_nested_field_in_received_but_missing_attr(
        self, respx_entity_store: StashEntityStore
    ) -> None:
        """Test edge case: field in _received_fields but object doesn't have it."""
        store = respx_entity_store

        studio = StudioFactory.build(id="1", name="Test")
        # Corrupt state: claim we have rating100 in received_fields but don't
        object.__setattr__(studio, "_received_fields", {"id", "name", "rating100"})
        # Delete the attribute to simulate corruption
        if hasattr(studio, "rating100"):
            delattr(studio, "rating100")
        store._cache_entity(studio)

        # Should return False (defensive check for data corruption)
        assert store._check_nested_field_present(studio, ["rating100"]) is False

    def test_check_nested_field_in_received_but_value_unset(
        self, respx_entity_store: StashEntityStore
    ) -> None:
        """Test edge case: field in _received_fields but value is UNSET."""
        store = respx_entity_store

        studio = StudioFactory.build(id="1", name="Test")
        # Corrupt state: claim we have rating100 in received_fields but it's UNSET
        object.__setattr__(studio, "_received_fields", {"id", "name", "rating100"})
        object.__setattr__(studio, "rating100", UNSET)
        store._cache_entity(studio)

        # Should return False (defensive check for data corruption)
        assert store._check_nested_field_present(studio, ["rating100"]) is False

    def test_check_nested_field_scalar_with_remaining_path(
        self, respx_entity_store: StashEntityStore
    ) -> None:
        """Test checking nested field where value is scalar but path continues."""
        store = respx_entity_store

        studio = StudioFactory.build(id="1", name="Test Studio")
        object.__setattr__(studio, "_received_fields", {"id", "name"})
        store._cache_entity(studio)

        # name is a string, can't traverse further
        # Path ['name', 'something'] should return False
        assert store._check_nested_field_present(studio, ["name", "something"]) is False

    @pytest.mark.asyncio
    async def test_populate_nested_field_nonexistent(
        self, respx_mock, respx_entity_store: StashEntityStore, caplog
    ) -> None:
        """Test populate() with nested field spec for non-existent field."""
        store = respx_entity_store

        studio = StudioFactory.build(id="1", name="Test")
        object.__setattr__(studio, "_received_fields", {"id", "name"})
        store._cache_entity(studio)

        # Try to populate a field that doesn't exist
        with caplog.at_level(logging.WARNING):
            await store.populate(studio, fields=["nonexistent__field"])

        # Should log a warning
        assert "has no field" in caplog.text

    @pytest.mark.asyncio
    async def test_populate_nested_field_value_is_none(
        self, respx_mock, respx_entity_store: StashEntityStore
    ) -> None:
        """Test populate() where nested field root value is None."""
        store = respx_entity_store

        # Studio with parent=None (actually has no parent)
        studio = StudioFactory.build(id="1", name="Test", parent=None)
        object.__setattr__(studio, "_received_fields", {"id", "name", "parent"})
        store._cache_entity(studio)

        # No GraphQL call should be made since parent is None
        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            return_value=httpx.Response(500, text="Should not be called")
        )

        # Populate with nested spec - should skip because parent is None
        await store.populate(studio, fields=["parent__name"])

        # Verify no GraphQL calls
        assert len(graphql_route.calls) == 0

    @pytest.mark.asyncio
    async def test_populate_nested_single_object(
        self, respx_mock, respx_entity_store: StashEntityStore
    ) -> None:
        """Test populate() with nested field on single object (not list)."""
        store = respx_entity_store

        # Parent with name=UNSET
        parent = StudioFactory.build(id="p1")
        object.__setattr__(parent, "_received_fields", {"id"})
        object.__setattr__(parent, "name", UNSET)
        store._cache_entity(parent)

        # Child with parent populated
        child = StudioFactory.build(id="c1", name="Child", parent=parent)
        object.__setattr__(child, "_received_fields", {"id", "name", "parent"})
        store._cache_entity(child)

        # Mock GraphQL response for fetching parent.name
        parent_response = {"id": "p1", "name": "Parent Name"}

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                # First call: populate child (root field 'parent')
                httpx.Response(
                    200,
                    json=create_graphql_response(
                        "findStudio",
                        {"id": "c1", "name": "Child", "parent": parent_response},
                    ),
                ),
                # Second call: populate parent with 'name'
                httpx.Response(
                    200,
                    json=create_graphql_response("findStudio", parent_response),
                ),
            ]
        )

        # Populate with nested field on single object
        await store.populate(child, fields=["parent__name"])

        # Should make at least 1 GraphQL call
        assert len(graphql_route.calls) >= 1

    @pytest.mark.asyncio
    async def test_populate_nested_list_with_non_stashobject_items(
        self, respx_mock, respx_entity_store: StashEntityStore
    ) -> None:
        """Test populate() where list contains non-StashObject items (edge case)."""
        store = respx_entity_store

        # Create an image with a files list that contains a mix (shouldn't happen in practice)
        image = ImageFactory.build(id="img1", title="Test")
        # Manually set files to include a non-StashObject (simulates data corruption)
        files_list = [
            ImageFileFactory.build(id="f1"),
            {"id": "f2", "not_a_stashobject": True},  # This shouldn't happen normally
        ]
        object.__setattr__(image, "files", files_list)
        object.__setattr__(image, "_received_fields", {"id", "title", "files"})
        store._cache_entity(image)

        # Mock GraphQL response (may or may not be called)
        respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json=create_graphql_response(
                        "findImage",
                        {
                            "id": "img1",
                            "title": "Test",
                            "files": [{"id": "f1", "path": "/test.jpg"}],
                        },
                    ),
                )
            ]
        )

        # Populate - should skip non-StashObject items gracefully
        result = await store.populate(image, fields=["files__path"])

        # Should not crash, just skip the non-StashObject item
        assert result is not None

    def test_get_fetchable_type_with_non_class(
        self, respx_entity_store: StashEntityStore
    ) -> None:
        """Test _get_fetchable_type handles non-class types gracefully."""
        store = respx_entity_store

        # Test with non-class types (should return None without crashing)
        # This covers the isinstance(entity_type, type) check
        assert store._get_fetchable_type("not a class") is None  # type: ignore[arg-type]
        assert store._get_fetchable_type(123) is None  # type: ignore[arg-type]
        assert store._get_fetchable_type(None) is None  # type: ignore[arg-type]

    def test_get_fetchable_type_no_typename_attr(
        self, respx_entity_store: StashEntityStore
    ) -> None:
        """Test _get_fetchable_type with class missing __type_name__."""
        store = respx_entity_store

        # Create a class without __type_name__ attribute
        class FakeClass:
            pass

        # Should handle AttributeError and return None (lines 856-857)
        assert store._get_fetchable_type(FakeClass) is None  # type: ignore[arg-type]

    def test_get_concrete_type_unknown_typename(
        self, respx_entity_store: StashEntityStore
    ) -> None:
        """Test _get_concrete_type with unrecognized __typename."""
        store = respx_entity_store

        # Data with unknown __typename
        data = {"__typename": "UnknownType", "id": "123"}

        # Should log warning and fall back to requested type (lines 906-910)
        result = store._get_concrete_type(data, Scene)
        assert result is Scene

    async def test_populate_single_nested_object(
        self, respx_mock, respx_entity_store: StashEntityStore
    ) -> None:
        """Test populate with single nested object with multiple nested field specs.

        This test ensures that when we have multiple nested field specs on a single
        object (not a list), the for loop iterates correctly, triggering the elif
        branch multiple times (line 1249->1227).
        """

        store = respx_entity_store

        # Studio with minimal data
        studio = StudioFactory.build(id="s1", name="Test")
        object.__setattr__(studio, "_received_fields", {"id", "name"})
        store._cache_entity(studio)

        # Scene with studio reference
        scene = SceneFactory.build(id="sc1", title="Test", studio=studio)
        object.__setattr__(scene, "_received_fields", {"id", "title", "studio"})
        store._cache_entity(scene)

        # Mock GraphQL responses - ONE fetch that returns both fields
        # This is realistic - GraphQL returns whatever fields you query for
        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json=create_graphql_response(
                        "findStudio",
                        {
                            "id": "s1",
                            "name": "Test",
                            "urls": ["http://test.com"],
                            "details": "Test details",
                        },
                    ),
                )
            ]
        )

        # Populate TWO nested field specs - creates nested_specs = {"studio": {("urls",), ("details",)}}
        # The for loop on line 1227 iterates twice for the two tuples
        # Each iteration takes the elif on line 1249 for single object
        # After first iteration, loop branches back to 1227 for second (line 1249->1227)
        result = await store.populate(scene, fields=["studio__urls", "studio__details"])

        # Should make exactly 1 call (both fields fetched together)
        assert len(graphql_route.calls) == 1
        assert result is not None
        assert result.studio.urls is not UNSET
        assert result.studio.details is not UNSET

    async def test_populate_non_fetchable_single_object_continues_loop(
        self, respx_mock, respx_entity_store: StashEntityStore
    ) -> None:
        """Test branch 1249->1227: loop continues when elif is False.

        When we have multiple nested field specs on a non-fetchable single
        StashObject, the for loop at line 1227 iterates, but the elif at
        line 1249 is False (not independently fetchable), so execution
        continues to the next iteration (branch 1249->1227).
        """
        store = respx_entity_store

        # Create a GalleryChapter (not independently fetchable) as a SINGLE object
        chapter = GalleryChapter.from_dict(
            {"id": "ch1", "title": "Chapter 1", "image_index": 5}
        )
        object.__setattr__(chapter, "_received_fields", {"id"})
        store._cache_entity(chapter)

        # Create a Gallery with a single chapter field (not a list for this test)
        # We'll manually set a field to be a single chapter using object.__setattr__
        # to bypass Pydantic validation
        gallery = Gallery.from_dict({"id": "gal1", "title": "Test Gallery"})
        # Use object.__setattr__ to bypass Pydantic validation
        object.__setattr__(gallery, "test_field", chapter)  # Custom field for testing
        object.__setattr__(gallery, "_received_fields", {"id", "title", "test_field"})
        store._cache_entity(gallery)

        # Populate with TWO nested field specs on non-fetchable single object
        # nested_specs = {"test_field": {("title",), ("image_index",)}}
        # Iteration 1: value=chapter, not list, not fetchable -> elif False -> continue to 1227
        # Iteration 2: value=chapter, not list, not fetchable -> elif False -> continue to 1227
        # The 1249->1227 branch is taken on iteration 1
        result = await store.populate(
            gallery, fields=["test_field__title", "test_field__image_index"]
        )

        # Should complete without errors (GalleryChapter not fetchable, just skipped)
        assert result is not None
        assert result.id == "gal1"

    async def test_populate_skips_non_fetchable_nested_items(
        self, respx_mock, respx_entity_store: StashEntityStore
    ) -> None:
        """Test that populate skips non-independently-fetchable items in lists."""
        store = respx_entity_store

        # Create a GalleryChapter with partial fields (not independently fetchable)
        chapter_data = {"id": "ch1", "title": "Chapter 1", "image_index": 0}
        chapter = GalleryChapter.from_dict(chapter_data)
        object.__setattr__(chapter, "_received_fields", {"id"})  # Only id fetched
        store._cache_entity(chapter)

        # Create a Gallery with chapters
        gallery = Gallery.from_dict(
            {"id": "gal1", "title": "Test Gallery", "chapters": [chapter]}
        )
        object.__setattr__(gallery, "_received_fields", {"id", "title", "chapters"})
        store._cache_entity(gallery)

        # No mock needed - populate should skip non-fetchable GalleryChapter
        # Since Gallery already has 'chapters' in _received_fields,
        # no re-fetch is triggered

        # Try to populate nested field on non-fetchable type
        # Should skip GalleryChapter (not independently fetchable) without crashing
        result = await store.populate(gallery, fields=["chapters__title"])

        # Should complete successfully without GraphQL calls
        # (Gallery already has chapters, GalleryChapter is not fetchable)
        assert result is not None
        assert result.id == "gal1"
