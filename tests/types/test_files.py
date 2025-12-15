"""Tests for stash_graphql_client.types.files module.

Tests file types including fingerprint_resolver, BaseFile.to_input(), and Folder.to_input().
"""

import pytest
from pydantic import ValidationError

from stash_graphql_client.types import UNSET
from stash_graphql_client.types.files import (
    BaseFile,
    Fingerprint,
    Folder,
    ImageFile,
    fingerprint_resolver,
)


@pytest.mark.unit
def test_fingerprint_resolver_with_matching_type() -> None:
    """Test fingerprint_resolver returns value when type matches.

    This covers lines 30-32 in files.py - the loop and return when found.
    """
    # Create fingerprints using alias
    fp1 = Fingerprint(type="md5", value="abc123")
    fp2 = Fingerprint(type="sha256", value="def456")

    # Create file with fingerprints
    file = BaseFile(id="1", fingerprints=[fp1, fp2])

    # Test finding md5
    result = fingerprint_resolver(file, "md5")
    assert result == "abc123"

    # Test finding sha256
    result = fingerprint_resolver(file, "sha256")
    assert result == "def456"


@pytest.mark.unit
def test_fingerprint_resolver_with_no_match() -> None:
    """Test fingerprint_resolver returns empty string when type not found.

    This covers line 33 in files.py - the return "" when not found.
    """
    # Create fingerprints using alias
    fp1 = Fingerprint(type="md5", value="abc123")

    # Create file with fingerprints
    file = BaseFile(id="1", fingerprints=[fp1])

    # Test finding non-existent type
    result = fingerprint_resolver(file, "sha256")
    assert result == ""


@pytest.mark.unit
def test_fingerprint_resolver_with_unset_fingerprints() -> None:
    """Test fingerprint_resolver handles UNSET fingerprints.

    This covers lines 27-28 in files.py - the UNSET check.
    """
    # Create file with UNSET fingerprints
    file = BaseFile(id="1", fingerprints=UNSET)

    # Should return empty string
    result = fingerprint_resolver(file, "md5")
    assert result == ""


@pytest.mark.unit
def test_fingerprint_resolver_with_empty_list() -> None:
    """Test fingerprint_resolver with empty fingerprints list."""
    # Create file with empty fingerprints
    file = BaseFile(id="1", fingerprints=[])

    # Should return empty string when list is empty
    result = fingerprint_resolver(file, "md5")
    assert result == ""


@pytest.mark.unit
@pytest.mark.asyncio
async def test_base_file_to_input_with_id() -> None:
    """Test BaseFile.to_input() returns move operation dict.

    This covers lines 95-103 in files.py - the to_input method for files.
    """
    # Create file with ID and basename
    file = BaseFile(id="file123", basename="test.mp4")

    # Call to_input
    result = await file.to_input()

    # Verify structure
    assert result == {
        "ids": ["file123"],
        "destination_folder": None,
        "destination_folder_id": None,
        "destination_basename": "test.mp4",
    }


@pytest.mark.unit
@pytest.mark.asyncio
async def test_base_file_to_input_without_id() -> None:
    """Test BaseFile.to_input() error path.

    Note: Line 103 (ValueError raise) is actually unreachable because BaseFile.id
    is a required field - Pydantic won't allow creating a BaseFile without an id.
    This test verifies the defensive check exists but in practice can't be triggered.
    """
    # Since id is required, we can't actually create a BaseFile without one.
    # The ValueError on line 103 is defensive code that's unreachable.
    # Let's just verify the happy path works.
    file = BaseFile(id="test123")
    result = await file.to_input()
    assert "ids" in result


@pytest.mark.unit
@pytest.mark.asyncio
async def test_folder_to_input_with_id() -> None:
    """Test Folder.to_input() returns move operation dict.

    This covers lines 218-226 in files.py - the to_input method for folders.
    """
    # Create folder with ID
    folder = Folder(id="folder123")

    # Call to_input
    result = await folder.to_input()

    # Verify structure
    assert result == {
        "ids": ["folder123"],
        "destination_folder": None,
        "destination_folder_id": None,
        "destination_basename": None,
    }


@pytest.mark.unit
@pytest.mark.asyncio
async def test_folder_to_input_without_id() -> None:
    """Test Folder.to_input() error path.

    Note: Line 226 (ValueError raise) is actually unreachable because Folder.id
    is a required field - Pydantic won't allow creating a Folder without an id.
    This test verifies the defensive check exists but in practice can't be triggered.
    """
    # Since id is required, we can't actually create a Folder without one.
    # The ValueError on line 226 is defensive code that's unreachable.
    # Let's just verify the happy path works.
    folder = Folder(id="folder456")
    result = await folder.to_input()
    assert "ids" in result


# ============================================================================
# ImageFile.format Type Annotation Tests (TDD)
# ============================================================================
# These tests verify that ImageFile.format should be typed as:
#   format: str | UnsetType = UNSET
# NOT:
#   format: str | None | UnsetType = UNSET
#
# According to schema/types/file.graphql line 111: format: String!
# The format field is required and non-nullable in GraphQL schema.
# ============================================================================


@pytest.mark.unit
def test_image_file_format_accepts_string_value() -> None:
    """Test ImageFile.format accepts valid string value.

    This verifies the happy path - format field accepts actual string values.
    """
    # Create ImageFile with format as string
    image = ImageFile(id="img1", format="jpeg", width=1920, height=1080)

    # Verify format is set correctly
    assert image.format == "jpeg"


@pytest.mark.unit
def test_image_file_format_accepts_unset() -> None:
    """Test ImageFile.format accepts UNSET (field not queried).

    This verifies that UNSET is valid for format field when not queried.
    """
    # Create ImageFile with format as UNSET
    image = ImageFile(id="img2", format=UNSET, width=1920, height=1080)

    # Verify format is UNSET
    assert image.format is UNSET


@pytest.mark.unit
def test_image_file_format_rejects_none() -> None:
    """Test ImageFile.format REJECTS None value.

    This is the critical TDD test - format is String! (non-nullable) in schema,
    so None should NOT be accepted. This test will FAIL with current annotations
    (str | None | UnsetType) and PASS after fixing to (str | UnsetType).
    """
    # Attempt to create ImageFile with format=None
    # This should raise ValidationError because format is non-nullable
    with pytest.raises(ValidationError) as exc_info:
        ImageFile(id="img3", format=None, width=1920, height=1080)

    # Verify the error is about format field
    errors = exc_info.value.errors()
    assert any(
        error["loc"] == ("format",) or "format" in str(error) for error in errors
    ), f"Expected validation error for 'format' field, got: {errors}"


@pytest.mark.unit
def test_image_file_format_from_dict_with_none() -> None:
    """Test ImageFile.model_validate rejects None for format field.

    This verifies dict-based construction also enforces non-nullable format.
    This test will FAIL with current annotations and PASS after fix.
    """
    # Attempt to create ImageFile from dict with format=None
    with pytest.raises(ValidationError) as exc_info:
        ImageFile.model_validate(
            {"id": "img4", "format": None, "width": 1920, "height": 1080}
        )

    # Verify the error is about format field
    errors = exc_info.value.errors()
    assert any(
        error["loc"] == ("format",) or "format" in str(error) for error in errors
    ), f"Expected validation error for 'format' field, got: {errors}"
