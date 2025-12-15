"""Tests for stash_graphql_client.types.performer module.

Tests Performer.update_avatar() and Performer.find_by_name() methods.

Following TESTING_REQUIREMENTS.md:
- Mock at HTTP boundary only with respx
- Test real code paths (no AsyncMock of client methods)
- Verify GraphQL requests and responses
"""

import base64
import tempfile
from pathlib import Path

import httpx
import pytest
import respx
from pydantic import ValidationError

from stash_graphql_client.types import UNSET
from stash_graphql_client.types.performer import Performer
from tests.fixtures import create_find_performers_result, create_performer_dict


@pytest.mark.unit
@pytest.mark.asyncio
async def test_performer_update_avatar_success(respx_stash_client) -> None:
    """Test Performer.update_avatar() with valid image file.

    This covers lines 248-264 in performer.py - the entire update_avatar method.
    """
    # Create a temporary image file
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp.write(b"fake_image_data")
        tmp_path = tmp.name

    try:
        # Create performer
        performer = Performer(id="123", name="Test Performer")

        # Mock the performerUpdate mutation response
        performer_data = create_performer_dict(id="123", name="Test Performer")

        with respx.mock:
            route = respx.post("http://localhost:9999/graphql").mock(
                return_value=httpx.Response(
                    200, json={"data": {"performerUpdate": performer_data}}
                )
            )

            # Call update_avatar with real client
            result = await performer.update_avatar(respx_stash_client, tmp_path)

            # Verify GraphQL call was made
            assert len(route.calls) == 1
            request = route.calls[0].request

            # Verify mutation and variables
            import json

            body = json.loads(request.content)
            assert "performerUpdate" in body["query"]
            assert body["variables"]["input"]["id"] == "123"

            # Verify image was base64 encoded in data URL
            image_url = body["variables"]["input"]["image"]
            assert image_url.startswith("data:image/jpeg;base64,")

            # Decode and verify content
            encoded_part = image_url.split(",")[1]
            decoded = base64.b64decode(encoded_part)
            assert decoded == b"fake_image_data"

            # Verify result
            assert result.id == "123"
            assert result.name == "Test Performer"

    finally:
        # Clean up temp file
        Path(tmp_path).unlink()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_performer_update_avatar_file_not_found(respx_stash_client) -> None:
    """Test Performer.update_avatar() with non-existent file.

    This covers line 250 in performer.py - the FileNotFoundError raise.
    """
    # Create performer
    performer = Performer(id="123", name="Test Performer")

    # Call with non-existent file (no HTTP mock needed - fails before HTTP call)
    with pytest.raises(FileNotFoundError, match="Image file not found"):
        await performer.update_avatar(respx_stash_client, "/nonexistent/path/image.jpg")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_performer_update_avatar_with_png(respx_stash_client) -> None:
    """Test Performer.update_avatar() with PNG file (different MIME type).

    This covers line 257 in performer.py - the MIME type detection.
    """
    # Create a temporary PNG file
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp.write(b"fake_png_data")
        tmp_path = tmp.name

    try:
        # Create performer
        performer = Performer(id="123", name="Test Performer")

        # Mock the performerUpdate mutation response
        performer_data = create_performer_dict(id="123", name="Test Performer")

        with respx.mock:
            route = respx.post("http://localhost:9999/graphql").mock(
                return_value=httpx.Response(
                    200, json={"data": {"performerUpdate": performer_data}}
                )
            )

            # Call update_avatar
            await performer.update_avatar(respx_stash_client, tmp_path)

            # Verify MIME type is image/png
            assert len(route.calls) == 1
            import json

            body = json.loads(route.calls[0].request.content)
            image_url = body["variables"]["input"]["image"]
            assert image_url.startswith("data:image/png;base64,")

    finally:
        # Clean up temp file
        Path(tmp_path).unlink()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_performer_update_avatar_client_error(respx_stash_client) -> None:
    """Test Performer.update_avatar() when GraphQL mutation fails.

    This covers line 263-264 in performer.py - the exception handling.
    """
    # Create a temporary image file
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp.write(b"fake_image_data")
        tmp_path = tmp.name

    try:
        # Create performer
        performer = Performer(id="123", name="Test Performer")

        # Mock GraphQL error response
        with respx.mock:
            route = respx.post("http://localhost:9999/graphql").mock(
                return_value=httpx.Response(
                    200,
                    json={"errors": [{"message": "GraphQL error"}]},
                )
            )

            # Call should re-raise as ValueError
            with pytest.raises(ValueError, match="Failed to update avatar"):
                await performer.update_avatar(respx_stash_client, tmp_path)

            # Verify GraphQL call was attempted
            assert len(route.calls) == 1

    finally:
        # Clean up temp file
        Path(tmp_path).unlink()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_performer_find_by_name_found(respx_stash_client) -> None:
    """Test Performer.find_by_name() returns performer when found.

    This covers lines 360-375 in performer.py - the find_by_name method.
    """
    # Create mock response data
    performer_data = create_performer_dict(id="456", name="Jane Doe", gender="FEMALE")
    find_result = create_find_performers_result(count=1, performers=[performer_data])

    with respx.mock:
        route = respx.post("http://localhost:9999/graphql").mock(
            return_value=httpx.Response(
                200, json={"data": {"findPerformers": find_result}}
            )
        )

        # Call find_by_name with real client
        result = await Performer.find_by_name(respx_stash_client, "Jane Doe")

        # Verify GraphQL call was made
        assert len(route.calls) == 1

        # Verify query and variables
        import json

        body = json.loads(route.calls[0].request.content)
        assert "findPerformers" in body["query"]
        assert body["variables"]["performer_filter"]["name"]["value"] == "Jane Doe"
        assert body["variables"]["performer_filter"]["name"]["modifier"] == "EQUALS"

        # Verify result
        assert isinstance(result, Performer)
        assert result.id == "456"
        assert result.name == "Jane Doe"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_performer_find_by_name_not_found(respx_stash_client) -> None:
    """Test Performer.find_by_name() returns None when not found.

    This covers line 373 in performer.py - the None return when no performers.
    """
    # Mock empty results
    find_result = create_find_performers_result(count=0, performers=[])

    with respx.mock:
        route = respx.post("http://localhost:9999/graphql").mock(
            return_value=httpx.Response(
                200, json={"data": {"findPerformers": find_result}}
            )
        )

        # Call find_by_name
        result = await Performer.find_by_name(respx_stash_client, "Unknown Person")

        # Verify GraphQL call was made
        assert len(route.calls) == 1

        # Should return None
        assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_performer_find_by_name_exception(respx_stash_client) -> None:
    """Test Performer.find_by_name() returns None on exception.

    This covers line 374-375 in performer.py - the exception handling.
    """
    # Mock HTTP error
    with respx.mock:
        route = respx.post("http://localhost:9999/graphql").mock(
            side_effect=httpx.ConnectError("Connection failed")
        )

        # Call find_by_name
        result = await Performer.find_by_name(respx_stash_client, "Jane Doe")

        # Verify GraphQL call was attempted
        assert len(route.calls) == 1

        # Should return None (not raise)
        assert result is None


# ============================================================================
# Performer.alias_list Type Annotation Tests (TDD)
# ============================================================================
# These tests verify that Performer.alias_list should be typed as:
#   alias_list: list[str] | UnsetType = UNSET
# NOT:
#   alias_list: list[str] | None | UnsetType = UNSET
#
# According to schema/types/performer.graphql line 36: alias_list: [String!]!
# The alias_list field is required and non-nullable list in GraphQL schema.
# ============================================================================


@pytest.mark.unit
def test_performer_alias_list_accepts_string_list() -> None:
    """Test Performer.alias_list accepts valid list of strings.

    This verifies the happy path - alias_list field accepts actual list values.
    """
    # Create Performer with alias_list as list of strings
    performer = Performer(id="p1", name="Jane Doe", alias_list=["Jane D", "JD"])

    # Verify alias_list is set correctly
    assert performer.alias_list == ["Jane D", "JD"]


@pytest.mark.unit
def test_performer_alias_list_accepts_empty_list() -> None:
    """Test Performer.alias_list accepts empty list.

    This verifies that empty list is valid for alias_list field.
    """
    # Create Performer with alias_list as empty list
    performer = Performer(id="p2", name="John Smith", alias_list=[])

    # Verify alias_list is set correctly
    assert performer.alias_list == []


@pytest.mark.unit
def test_performer_alias_list_accepts_unset() -> None:
    """Test Performer.alias_list accepts UNSET (field not queried).

    This verifies that UNSET is valid for alias_list field when not queried.
    """
    # Create Performer with alias_list as UNSET
    performer = Performer(id="p3", name="Test Performer", alias_list=UNSET)

    # Verify alias_list is UNSET
    assert performer.alias_list is UNSET


@pytest.mark.unit
def test_performer_alias_list_rejects_none() -> None:
    """Test Performer.alias_list REJECTS None value.

    This is the critical TDD test - alias_list is [String!]! (non-nullable) in schema,
    so None should NOT be accepted. This test will FAIL with current annotations
    (list[str] | None | UnsetType) and PASS after fixing to (list[str] | UnsetType).
    """
    # Attempt to create Performer with alias_list=None
    # This should raise ValidationError because alias_list is non-nullable
    with pytest.raises(ValidationError) as exc_info:
        Performer(id="p4", name="Test Performer", alias_list=None)

    # Verify the error is about alias_list field
    errors = exc_info.value.errors()
    assert any(
        error["loc"] == ("alias_list",) or "alias_list" in str(error)
        for error in errors
    ), f"Expected validation error for 'alias_list' field, got: {errors}"


@pytest.mark.unit
def test_performer_alias_list_from_dict_with_none() -> None:
    """Test Performer.model_validate rejects None for alias_list field.

    This verifies dict-based construction also enforces non-nullable alias_list.
    This test will FAIL with current annotations and PASS after fix.
    """
    # Attempt to create Performer from dict with alias_list=None
    with pytest.raises(ValidationError) as exc_info:
        Performer.model_validate({"id": "p5", "name": "Test", "alias_list": None})

    # Verify the error is about alias_list field
    errors = exc_info.value.errors()
    assert any(
        error["loc"] == ("alias_list",) or "alias_list" in str(error)
        for error in errors
    ), f"Expected validation error for 'alias_list' field, got: {errors}"
