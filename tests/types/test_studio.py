"""Tests for stash_graphql_client.types.studio module.

Tests studio types including Studio, StudioCreateInput, StudioUpdateInput and related types.
"""

import pytest
from pydantic import BaseModel

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

    # Test specific relationship mappings
    parent_studio_mapping = Studio.__relationships__["parent_studio"]
    assert parent_studio_mapping[0] == "parent_id"  # target field
    assert parent_studio_mapping[1] is False  # is_list

    tags_mapping = Studio.__relationships__["tags"]
    assert tags_mapping[0] == "tag_ids"  # target field
    assert tags_mapping[1] is True  # is_list


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
    assert studio.aliases == []  # default factory
    assert studio.tags == []  # default factory
    assert studio.stash_ids == []  # default factory


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
def test_studio_from_account() -> None:
    """Test Studio.from_account class method exists."""
    # Test that the from_account method exists
    assert hasattr(Studio, "from_account")
    assert callable(Studio.from_account)


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
    assert stash_ids_mapping[0] == "stash_ids"  # target field
    assert stash_ids_mapping[1] is True  # is_list
    assert stash_ids_mapping[2] is not None  # has transformation function


# @pytest.mark.unit
# async def test_studio_from_account_method() -> None:
#     """Test Studio.from_account method creates studio from account."""

#     # Create mock account
# !!!!!    mock_account = Mock()
# !!!!!    mock_account.display_name = "Test Display Name"
# !!!!!    mock_account.username = "testuser"
# !!!!!    mock_account.bio = "Test bio description"
# !!!!!    mock_account.site_url = "https://example.mymember.site"
# !!!!!    mock_account.studio_name = "ExampleStudio"  # This should come from site config

#     # Call the method
#     studio = await Studio.from_account(mock_account)

#     # Verify the result
#     assert studio.id == "new"
#     assert studio.name == "ExampleStudio"  # Should use studio_name from site config
#     assert studio.url == "https://example.mymember.site"
#     assert studio.details == "Test bio description"


# @pytest.mark.unit
# async def test_studio_from_account_fallback_name() -> None:
#     """Test Studio.from_account handles missing display_name."""

#     # Create mock account with no display_name
# !!!!!    mock_account = Mock(spec=["display_name", "username", "bio", "site_url"])
# !!!!!    mock_account.display_name = None
# !!!!!    mock_account.username = "testuser"
# !!!!!    mock_account.bio = "Test bio"
# !!!!!    mock_account.site_url = None  # Explicitly set site_url to None
#     # No studio_name attribute, should fall back to username

#     # Call the method
#     studio = await Studio.from_account(mock_account)

#     # Should fallback to username
#     assert studio.name == "testuser"

#     # Test with no username either
#     mock_account.username = None
#     studio = await Studio.from_account(mock_account)

#     # Should fallback to "Unknown"
#     assert studio.name == "Unknown"
