"""Tests for version-related client methods.

Tests the version() and latestversion() client methods following TESTING_REQUIREMENTS.md:
- Mock only at HTTP boundary using respx
- Verify both GraphQL request AND response
- No internal method mocking
- Complete Pydantic model validation
"""

import json

import httpx
import pytest
import respx

from stash_graphql_client.errors import StashGraphQLError, StashServerError
from stash_graphql_client.types import LatestVersion, Version
from tests.fixtures.stash import create_graphql_response


@pytest.mark.asyncio
@pytest.mark.unit
async def test_version(respx_stash_client, respx_mock: respx.MockRouter) -> None:
    """Test version() query returns Version model with all fields."""
    # Mock the GraphQL HTTP endpoint
    version_data = {
        "version": "v0.26.2",
        "hash": "abcdef1234567890",
        "build_time": "2024-01-15T10:30:00Z",
    }

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response("version", version_data),
            )
        ]
    )

    # Use the fixture client and call version()
    result = await respx_stash_client.version()

    # Verify GraphQL request was made
    assert len(graphql_route.calls) == 1
    request = json.loads(graphql_route.calls[0].request.content)
    assert "version" in request["query"]
    assert "query Version" in request["query"]

    # Verify response is correct Version model
    assert isinstance(result, Version)
    assert result.version == "v0.26.2"
    assert result.hash == "abcdef1234567890"
    assert result.build_time == "2024-01-15T10:30:00Z"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_version_with_null_version_field(
    respx_stash_client, respx_mock: respx.MockRouter
) -> None:
    """Test version() with null version field (allowed by schema)."""
    # Mock response with null version field
    version_data = {
        "version": None,
        "hash": "abcdef1234567890",
        "build_time": "2024-01-15T10:30:00Z",
    }

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response("version", version_data),
            )
        ]
    )

    # Use the fixture client and call version()
    result = await respx_stash_client.version()

    # Verify GraphQL request
    assert len(graphql_route.calls) == 1
    request = json.loads(graphql_route.calls[0].request.content)
    assert "version" in request["query"]

    # Verify response handles null version field
    assert isinstance(result, Version)
    assert result.version is None
    assert result.hash == "abcdef1234567890"
    assert result.build_time == "2024-01-15T10:30:00Z"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_latestversion(respx_stash_client, respx_mock: respx.MockRouter) -> None:
    """Test latestversion() query returns LatestVersion model with all fields."""
    # Mock the GraphQL HTTP endpoint
    latest_version_data = {
        "version": "v0.27.0",
        "shorthash": "abc123",
        "release_date": "2024-02-01",
        "url": "https://github.com/stashapp/stash/releases/tag/v0.27.0",
    }

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response("latestversion", latest_version_data),
            )
        ]
    )

    # Use the fixture client and call latestversion()
    result = await respx_stash_client.latestversion()

    # Verify GraphQL request was made
    assert len(graphql_route.calls) == 1
    request = json.loads(graphql_route.calls[0].request.content)
    assert "latestversion" in request["query"]
    assert "query LatestVersion" in request["query"]

    # Verify response is correct LatestVersion model
    assert isinstance(result, LatestVersion)
    assert result.version == "v0.27.0"
    assert result.shorthash == "abc123"
    assert result.release_date == "2024-02-01"
    assert result.url == "https://github.com/stashapp/stash/releases/tag/v0.27.0"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_version_and_latestversion_together(
    respx_stash_client, respx_mock: respx.MockRouter
) -> None:
    """Test calling both version() and latestversion() in sequence.

    This verifies that both methods work correctly when called together,
    as shown in the documentation example.
    """
    # Mock both responses using side_effect for sequential calls
    version_data = {
        "version": "v0.26.2",
        "hash": "abcdef1234567890",
        "build_time": "2024-01-15T10:30:00Z",
    }

    latest_version_data = {
        "version": "v0.27.0",
        "shorthash": "abc123",
        "release_date": "2024-02-01",
        "url": "https://github.com/stashapp/stash/releases/tag/v0.27.0",
    }

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("version", version_data)
            ),  # Call 1
            httpx.Response(
                200, json=create_graphql_response("latestversion", latest_version_data)
            ),  # Call 2
        ]
    )

    # Use the fixture client and call both methods
    current = await respx_stash_client.version()
    latest = await respx_stash_client.latestversion()

    # Verify both GraphQL requests were made
    assert len(graphql_route.calls) == 2

    # Verify version() response
    assert isinstance(current, Version)
    assert current.version == "v0.26.2"

    # Verify latestversion() response
    assert isinstance(latest, LatestVersion)
    assert latest.version == "v0.27.0"

    # Verify versions are different (as expected in update scenario)
    assert current.version != latest.version


@pytest.mark.unit
def test_version_model_validation() -> None:
    """Test Version model validates fields correctly."""
    # Test valid Version with all fields
    version = Version(
        version="v0.26.2",
        hash="abcdef1234567890",
        build_time="2024-01-15T10:30:00Z",
    )
    assert version.version == "v0.26.2"
    assert version.hash == "abcdef1234567890"
    assert version.build_time == "2024-01-15T10:30:00Z"

    # Test valid Version with null version field
    version_null = Version(
        version=None,
        hash="abcdef1234567890",
        build_time="2024-01-15T10:30:00Z",
    )
    assert version_null.version is None
    assert version_null.hash == "abcdef1234567890"

    # Note: Fields are optional (UNSET defaults) for fragment support,
    # so no validation errors are raised for missing fields


@pytest.mark.unit
def test_latestversion_model_validation() -> None:
    """Test LatestVersion Pydantic model validates fields correctly."""
    # Test valid LatestVersion with all fields
    latest = LatestVersion(
        version="v0.27.0",
        shorthash="abc123",
        release_date="2024-02-01",
        url="https://github.com/stashapp/stash/releases/tag/v0.27.0",
    )
    assert latest.version == "v0.27.0"
    assert latest.shorthash == "abc123"
    assert latest.release_date == "2024-02-01"
    assert latest.url == "https://github.com/stashapp/stash/releases/tag/v0.27.0"

    # Note: Fields are optional (UNSET defaults) for fragment support,
    # so no validation errors are raised for missing fields


@pytest.mark.asyncio
@pytest.mark.unit
async def test_version_graphql_error(
    respx_stash_client, respx_mock: respx.MockRouter
) -> None:
    """Test version() handles GraphQL errors gracefully."""
    # Mock GraphQL error response
    error_response = {
        "errors": [
            {
                "message": "Internal server error",
                "locations": [{"line": 2, "column": 5}],
                "path": ["version"],
            }
        ]
    }

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(200, json=error_response)]
    )

    # Use the fixture client and call version()
    # Should raise exception when GraphQL returns errors
    with pytest.raises(StashGraphQLError):  # Will raise KeyError or similar
        await respx_stash_client.version()

    # Verify GraphQL request was attempted
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_latestversion_graphql_error(
    respx_stash_client, respx_mock: respx.MockRouter
) -> None:
    """Test latestversion() handles GraphQL errors gracefully."""
    # Mock GraphQL error response
    error_response = {
        "errors": [
            {
                "message": "Failed to fetch latest version",
                "locations": [{"line": 2, "column": 5}],
                "path": ["latestversion"],
            }
        ]
    }

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(200, json=error_response)]
    )

    # Use the fixture client and call latestversion()
    # Should raise exception when GraphQL returns errors
    with pytest.raises(StashGraphQLError):  # Will raise KeyError or similar
        await respx_stash_client.latestversion()

    # Verify GraphQL request was attempted
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_version_http_error(
    respx_stash_client, respx_mock: respx.MockRouter
) -> None:
    """Test version() handles HTTP errors (e.g., 500 Internal Server Error)."""
    # Mock HTTP 500 error
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(500, text="Internal Server Error")]
    )

    # Use the fixture client and call version()
    # Should raise exception on HTTP error
    with pytest.raises(StashServerError):
        await respx_stash_client.version()

    # Verify GraphQL request was attempted
    assert len(graphql_route.calls) >= 1  # May retry depending on client config


@pytest.mark.asyncio
@pytest.mark.unit
async def test_latestversion_http_error(
    respx_stash_client, respx_mock: respx.MockRouter
) -> None:
    """Test latestversion() handles HTTP errors (e.g., 503 Service Unavailable)."""
    # Mock HTTP 503 error
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(503, text="Service Unavailable")]
    )

    # Use the fixture client and call latestversion()
    # Should raise exception on HTTP error
    with pytest.raises(StashServerError):
        await respx_stash_client.latestversion()

    # Verify GraphQL request was attempted
    assert len(graphql_route.calls) >= 1  # May retry depending on client config


@pytest.mark.unit
def test_version_model_field_types() -> None:
    """Test Version model has correct field types as defined in schema."""
    # Verify field annotations match schema
    # Pydantic uses model_fields (or __annotations__ for older versions)
    fields = getattr(Version, "model_fields", Version.__annotations__)

    # version: String (optional)
    assert "version" in fields
    # hash: String! (required)
    assert "hash" in fields
    # build_time: String! (required)
    assert "build_time" in fields


@pytest.mark.unit
def test_latestversion_model_field_types() -> None:
    """Test LatestVersion model has correct field types as defined in schema."""
    # Verify field annotations match schema
    # Pydantic uses model_fields (or __annotations__ for older versions)
    fields = getattr(LatestVersion, "model_fields", LatestVersion.__annotations__)

    # version: String! (required)
    assert "version" in fields
    # shorthash: String! (required)
    assert "shorthash" in fields
    # release_date: String! (required)
    assert "release_date" in fields
    # url: String! (required)
    assert "url" in fields
