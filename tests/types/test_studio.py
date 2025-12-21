"""Tests for stash_graphql_client.types.studio module.

Tests studio types including Studio, StudioCreateInput, StudioUpdateInput and related types.
"""

import pytest
from pydantic import BaseModel

from stash_graphql_client.types import UNSET
from stash_graphql_client.types.base import RelationshipMetadata
from stash_graphql_client.types.studio import (
    FindStudiosResultType,
    Studio,
    StudioCreateInput,
    StudioDestroyInput,
    StudioUpdateInput,
)


@pytest.mark.unit
def test_studio_create_input() -> None:
    """Test StudioCreateInput input type."""
    assert issubclass(StudioCreateInput, BaseModel)

    # Test field types
    fields = StudioCreateInput.model_fields
    expected_fields = [
        "name",
        "urls",
        "parent_id",
        "details",
        "aliases",
        "tag_ids",
        "stash_ids",
    ]
    for field in expected_fields:
        assert field in fields, f"Field {field} not found in StudioCreateInput"


@pytest.mark.unit
def test_studio_update_input() -> None:
    """Test StudioUpdateInput input type."""
    assert issubclass(StudioUpdateInput, BaseModel)

    # Test field types
    fields = StudioUpdateInput.model_fields
    expected_fields = [
        "id",
        "name",
        "urls",
        "parent_id",
        "details",
        "aliases",
        "tag_ids",
        "stash_ids",
    ]

    for field in expected_fields:
        assert field in fields, f"Field {field} not found in StudioUpdateInput"


@pytest.mark.unit
def test_studio() -> None:
    """Test Studio type."""
    assert issubclass(Studio, BaseModel)

    # Test that it extends StashObject
    fields = Studio.model_fields
    assert "id" in fields  # From StashObject

    # Test studio-specific fields
    expected_fields = [
        "name",
        "aliases",
        "tags",
        "stash_ids",
        "urls",
        "parent_studio",
        "details",
        "image_path",
    ]

    for field in expected_fields:
        assert field in fields, f"Field {field} not found in Studio"


@pytest.mark.unit
def test_studio_class_variables() -> None:
    """Test Studio class variables."""
    assert hasattr(Studio, "__type_name__")
    assert Studio.__type_name__ == "Studio"

    assert hasattr(Studio, "__update_input_type__")
    assert Studio.__update_input_type__ == StudioUpdateInput

    assert hasattr(Studio, "__create_input_type__")
    assert Studio.__create_input_type__ == StudioCreateInput

    assert hasattr(Studio, "__tracked_fields__")
    expected_tracked_fields = {
        "name",
        "aliases",
        "tags",
        "stash_ids",
        "urls",
        "parent_studio",
        "details",
        "rating100",
        "favorite",
        "ignore_auto_tag",
    }
    assert Studio.__tracked_fields__ == expected_tracked_fields


@pytest.mark.unit
def test_studio_field_conversions() -> None:
    """Test Studio field conversions."""
    assert hasattr(Studio, "__field_conversions__")

    expected_conversions = {
        "name": str,
        "urls": list,
        "aliases": list,
        "details": str,
    }

    for field, conversion in expected_conversions.items():
        assert field in Studio.__field_conversions__
        assert Studio.__field_conversions__[field] == conversion


@pytest.mark.unit
def test_studio_relationships() -> None:
    """Test Studio relationships."""
    assert hasattr(Studio, "__relationships__")

    # Test key relationships exist
    expected_relationships = ["parent_studio", "tags", "stash_ids"]

    for field in expected_relationships:
        assert field in Studio.__relationships__, (
            f"Relationship {field} not found in Studio"
        )

    # Test specific relationship mappings (using RelationshipMetadata attributes)
    parent_studio_mapping = Studio.__relationships__["parent_studio"]
    assert isinstance(parent_studio_mapping, RelationshipMetadata)
    assert parent_studio_mapping.target_field == "parent_id"
    assert parent_studio_mapping.is_list is False

    tags_mapping = Studio.__relationships__["tags"]
    assert isinstance(tags_mapping, RelationshipMetadata)
    assert tags_mapping.target_field == "tag_ids"
    assert tags_mapping.is_list is True


@pytest.mark.unit
def test_studio_destroy_input() -> None:
    """Test StudioDestroyInput input type."""
    assert issubclass(StudioDestroyInput, BaseModel)

    # Test field types
    fields = StudioDestroyInput.model_fields
    expected_fields = ["id"]

    for field in expected_fields:
        assert field in fields, f"Field {field} not found in StudioDestroyInput"


@pytest.mark.unit
def test_find_studios_result_type() -> None:
    """Test FindStudiosResultType result type."""
    assert issubclass(FindStudiosResultType, BaseModel)

    # Test field types
    fields = FindStudiosResultType.model_fields
    expected_fields = ["count", "studios"]

    for field in expected_fields:
        assert field in fields, f"Field {field} not found in FindStudiosResultType"


@pytest.mark.unit
def test_studio_instantiation() -> None:
    """Test Studio instantiation."""
    studio = Studio(id="123", name="Test Studio")

    assert studio.id == "123"
    assert studio.name == "Test Studio"
    # Studio list fields default to UNSET (not [] or None) for fragment-based loading
    assert studio.aliases is UNSET
    assert studio.tags is UNSET
    assert studio.stash_ids is UNSET


@pytest.mark.unit
def test_studio_create_input_instantiation() -> None:
    """Test StudioCreateInput instantiation."""
    studio_input = StudioCreateInput(
        name="New Studio", urls=["https://example.com"], details="A new studio"
    )

    assert studio_input.name == "New Studio"
    assert studio_input.urls == ["https://example.com"]
    assert studio_input.details == "A new studio"


@pytest.mark.unit
def test_studio_update_input_instantiation() -> None:
    """Test StudioUpdateInput instantiation."""
    studio_input = StudioUpdateInput(
        id="123", name="Updated Studio", urls=["https://updated.com"]
    )

    assert studio_input.id == "123"
    assert studio_input.name == "Updated Studio"
    assert studio_input.urls == ["https://updated.com"]


@pytest.mark.unit
def test_strawberry_decorations() -> None:
    """Test that all types are properly decorated with strawberry."""
    types_to_test = [
        StudioCreateInput,
        StudioUpdateInput,
        Studio,
        StudioDestroyInput,
        FindStudiosResultType,
    ]
    for type_class in types_to_test:
        assert issubclass(type_class, BaseModel), (
            f"{type_class.__name__} should be a Pydantic BaseModel"
        )


@pytest.mark.unit
def test_studio_inheritance() -> None:
    """Test that Studio properly inherits from StashObject."""

    # Test that Studio follows the StashObject interface pattern
    assert hasattr(Studio, "__type_name__")
    assert hasattr(Studio, "__tracked_fields__")
    assert hasattr(Studio, "__field_conversions__")
    assert hasattr(Studio, "__relationships__")


@pytest.mark.unit
def test_studio_stash_id_relationship() -> None:
    """Test Studio's stash_ids relationship transformation."""
    # Test that stash_ids relationship has a transformation function
    stash_ids_mapping = Studio.__relationships__["stash_ids"]
    assert isinstance(stash_ids_mapping, RelationshipMetadata)
    assert stash_ids_mapping.target_field == "stash_ids"
    assert stash_ids_mapping.is_list is True
    assert stash_ids_mapping.transform is not None  # has transformation function


@pytest.mark.unit
def test_studio_handle_deprecated_url_migration() -> None:
    """Test Studio.handle_deprecated_url() migrates url to urls.

    This covers lines 131-137 in studio.py - url migration logic.
    """
    # Test migrating single url to urls array via Studio instantiation
    studio = Studio(id="1", url="https://example.com", name="Test Studio")

    # url should be migrated to urls
    assert studio.urls == ["https://example.com"]


@pytest.mark.unit
def test_studio_handle_deprecated_url_merge() -> None:
    """Test Studio.handle_deprecated_url() merges url into existing urls.

    This covers lines 135-137 in studio.py - ensuring url is in urls array.
    """
    # Test merging url into existing urls if not present
    studio = Studio(
        id="1",
        url="https://example.com",
        urls=["https://other.com"],
        name="Test Studio",
    )

    # url should be prepended to urls
    assert studio.urls == ["https://example.com", "https://other.com"]


@pytest.mark.unit
def test_studio_handle_deprecated_url_already_in_urls() -> None:
    """Test Studio.handle_deprecated_url() when url already in urls.

    This covers line 135 branch where url is already in urls.
    """
    # Test when url is already in urls
    studio = Studio(
        id="1",
        url="https://example.com",
        urls=["https://example.com", "https://other.com"],
        name="Test Studio",
    )

    # Should not duplicate
    assert studio.urls == ["https://example.com", "https://other.com"]


@pytest.mark.unit
def test_studio_handle_deprecated_url_empty_string() -> None:
    """Test Studio.handle_deprecated_url() removes empty string url.

    This covers line 133 in studio.py - removing empty url.
    """
    # Test with empty string url
    studio = Studio(id="1", name="Test Studio", url="")

    # Empty url should be removed, urls should be UNSET
    assert studio.urls is UNSET


@pytest.mark.unit
def test_studio_handle_deprecated_url_none() -> None:
    """Test Studio.handle_deprecated_url() removes None url.

    This covers lines 131-133 in studio.py - removing None url.
    """
    # Can't actually pass url=None since it's a string field
    # But the validator handles the case defensively
    studio = Studio(id="1", name="Test Studio")

    # Should have UNSET urls (no url field provided)
    assert studio.urls is UNSET
