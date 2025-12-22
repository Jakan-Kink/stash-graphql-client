"""Integration tests for image mixin functionality.

Tests image operations against a real Stash instance with GraphQL call verification.

These tests cover the core image CRUD operations, relationships, and
image-specific features like O-counter tracking and bulk operations.
"""

import pytest

from stash_graphql_client import StashClient
from tests.fixtures import capture_graphql_calls


# =============================================================================
# Image Read Integration Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_images_returns_results(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding images returns results (may be empty)."""
    async with (
        stash_cleanup_tracker(stash_client),
        capture_graphql_calls(stash_client) as calls,
    ):
        result = await stash_client.find_images()

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_images"
        assert "findImages" in calls[0]["query"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Result should be valid even if empty
        assert result.count >= 0
        assert isinstance(result.images, list)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_images_with_pagination(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test image pagination works correctly."""
    async with (
        stash_cleanup_tracker(stash_client),
        capture_graphql_calls(stash_client) as calls,
    ):
        result = await stash_client.find_images(filter_={"per_page": 10, "page": 1})

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_images"
        assert "findImages" in calls[0]["query"]
        assert calls[0]["variables"]["filter"]["per_page"] == 10
        assert calls[0]["variables"]["filter"]["page"] == 1
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify response
        assert len(result.images) <= 10


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_nonexistent_image_returns_none(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding a nonexistent image returns None."""
    async with (
        stash_cleanup_tracker(stash_client),
        capture_graphql_calls(stash_client) as calls,
    ):
        image = await stash_client.find_image("99999999")

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_image"
        assert "findImage" in calls[0]["query"]
        assert calls[0]["variables"]["id"] == "99999999"
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify response
        assert image is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_images_with_q_parameter(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding images using q search parameter."""
    async with (
        stash_cleanup_tracker(stash_client),
        capture_graphql_calls(stash_client) as calls,
    ):
        result = await stash_client.find_images(q="test")

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_images"
        assert "findImages" in calls[0]["query"]
        # q parameter is added to filter dict
        assert calls[0]["variables"]["filter"]["q"] == "test"
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Should return valid result (may or may not have matches)
        assert result.count >= 0
        assert isinstance(result.images, list)


# =============================================================================
# NOTE: Image CRUD Integration Tests
# =============================================================================
# Images cannot be created via GraphQL API - there is no ImageCreateInput type.
# Images are added to Stash through folder scanning only. Therefore:
#
# - test_create_and_find_image: REMOVED (creation not supported)
# - test_create_and_update_image: REMOVED (creation not supported)
# - test_create_and_destroy_image: REMOVED (creation not supported)
# - test_update_existing_image: REMOVED (would modify production data)
# - test_bulk_image_update: REMOVED (would modify production data)
# - test_images_destroy_multiple: REMOVED (would delete production data)
#
# Image mutation operations are verified via unit tests in tests/types/ and
# tests/client/ with mocked responses instead.
