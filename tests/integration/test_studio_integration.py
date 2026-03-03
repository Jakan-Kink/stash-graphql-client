"""Integration tests for studio mixin functionality.

Tests studio operations against a real Stash instance.
"""

import pytest

from stash_graphql_client import StashClient
from stash_graphql_client.types import BulkStudioUpdateInput, Studio
from stash_graphql_client.types.unset import is_set
from tests.fixtures import capture_graphql_calls


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_studios_returns_results(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding studios returns results (may be empty)."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        result = await stash_client.find_studios()

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_studios"
        assert "findStudios" in calls[0]["query"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Result should be valid even if empty
        assert is_set(result.count)
        assert result.count is not None
        assert result.count >= 0
        assert is_set(result.studios)
        assert result.studios is not None
        assert isinstance(result.studios, list)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_studios_with_pagination(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test studio pagination works correctly."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        result = await stash_client.find_studios(filter_={"per_page": 10, "page": 1})

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_studios"
        assert "findStudios" in calls[0]["query"]
        assert calls[0]["variables"]["filter"]["per_page"] == 10
        assert calls[0]["variables"]["filter"]["page"] == 1
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify response
        assert is_set(result.studios)
        assert result.studios is not None
        assert len(result.studios) <= 10


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_nonexistent_studio_returns_none(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding a nonexistent studio returns None."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        studio = await stash_client.find_studio("99999999")

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_studio"
        assert "findStudio" in calls[0]["query"]
        assert calls[0]["variables"]["id"] == "99999999"
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify response
        assert studio is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_studios_with_q_parameter(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding studios using q search parameter."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        result = await stash_client.find_studios(q="test")

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_studios"
        assert "findStudios" in calls[0]["query"]
        assert calls[0]["variables"]["filter"]["q"] == "test"
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Should return valid result (may or may not have matches)
        assert is_set(result.count)
        assert result.count is not None
        assert result.count >= 0
        assert is_set(result.studios)
        assert result.studios is not None
        assert isinstance(result.studios, list)


# =============================================================================
# Studio mutation lifecycle tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="studio_mutations")
async def test_create_and_find_studio(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test creating a studio and retrieving it by ID."""
    async with (
        stash_cleanup_tracker(stash_client) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        studio = await stash_client.create_studio(
            Studio(name="SGC Inttest Create Studio")
        )
        cleanup["studios"].append(studio.id)

        assert len(calls) == 1, "Expected 1 GraphQL call for create_studio"
        assert "studioCreate" in calls[0]["query"]
        assert calls[0]["exception"] is None

        assert studio.id is not None
        assert is_set(studio.name)
        assert studio.name == "SGC Inttest Create Studio"

        calls.clear()

        found = await stash_client.find_studio(studio.id)

        assert len(calls) == 1, "Expected 1 GraphQL call for find_studio"
        assert "findStudio" in calls[0]["query"]
        assert calls[0]["exception"] is None

        assert found is not None
        assert found.id == studio.id
        assert found.name == "SGC Inttest Create Studio"


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="studio_mutations")
async def test_update_studio(stash_client: StashClient, stash_cleanup_tracker) -> None:
    """Test creating a studio and updating its details."""
    async with (
        stash_cleanup_tracker(stash_client) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        studio = await stash_client.create_studio(
            Studio(name="SGC Inttest Update Studio")
        )
        cleanup["studios"].append(studio.id)
        assert studio.id is not None

        calls.clear()

        studio.details = "integration test details"
        updated = await stash_client.update_studio(studio)

        assert len(calls) == 1, "Expected 1 GraphQL call for update_studio"
        assert "studioUpdate" in calls[0]["query"]
        assert calls[0]["exception"] is None

        assert updated.id == studio.id
        assert is_set(updated.details)
        assert updated.details == "integration test details"


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="studio_mutations")
async def test_studio_destroy(stash_client: StashClient, stash_cleanup_tracker) -> None:
    """Test creating a studio and then destroying it."""
    async with (
        stash_cleanup_tracker(stash_client) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        studio = await stash_client.create_studio(
            Studio(name="SGC Inttest Destroy Studio")
        )
        cleanup["studios"].append(studio.id)
        assert studio.id is not None

        calls.clear()

        result = await stash_client.studio_destroy({"id": studio.id})

        assert len(calls) == 1, "Expected 1 GraphQL call for studio_destroy"
        assert "studioDestroy" in calls[0]["query"]
        assert calls[0]["exception"] is None
        assert result is True

        # Already destroyed — remove from cleanup to avoid double-delete
        cleanup["studios"].remove(studio.id)

        calls.clear()

        gone = await stash_client.find_studio(studio.id)
        assert gone is None


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="studio_mutations")
async def test_studios_destroy_bulk(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test bulk-destroying multiple studios in a single call."""
    async with (
        stash_cleanup_tracker(stash_client) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        studio_a = await stash_client.create_studio(
            Studio(name="SGC Inttest Bulk Destroy Studio A")
        )
        studio_b = await stash_client.create_studio(
            Studio(name="SGC Inttest Bulk Destroy Studio B")
        )
        cleanup["studios"].append(studio_a.id)
        cleanup["studios"].append(studio_b.id)
        assert studio_a.id is not None
        assert studio_b.id is not None

        calls.clear()

        result = await stash_client.studios_destroy([studio_a.id, studio_b.id])

        assert len(calls) == 1, "Expected 1 GraphQL call for studios_destroy"
        assert "studiosDestroy" in calls[0]["query"]
        assert calls[0]["exception"] is None
        assert result is True

        cleanup["studios"].remove(studio_a.id)
        cleanup["studios"].remove(studio_b.id)


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="studio_mutations")
async def test_bulk_studio_update(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test bulk updating multiple studios' rating in a single call.

    Requires has_bulk_studio_update capability (bulkStudioUpdate mutation).
    """
    if not stash_client._capabilities.has_bulk_studio_update:
        pytest.skip("Server does not support bulkStudioUpdate")

    async with (
        stash_cleanup_tracker(stash_client) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        studio_a = await stash_client.create_studio(
            Studio(name="SGC Inttest Bulk Update Studio A")
        )
        studio_b = await stash_client.create_studio(
            Studio(name="SGC Inttest Bulk Update Studio B")
        )
        cleanup["studios"].append(studio_a.id)
        cleanup["studios"].append(studio_b.id)
        assert studio_a.id is not None
        assert studio_b.id is not None

        calls.clear()

        updated = await stash_client.bulk_studio_update(
            BulkStudioUpdateInput(ids=[studio_a.id, studio_b.id], rating100=75)
        )

        assert len(calls) == 1, "Expected 1 GraphQL call for bulk_studio_update"
        assert "bulkStudioUpdate" in calls[0]["query"]
        assert calls[0]["exception"] is None

        assert len(updated) == 2
        for s in updated:
            assert is_set(s.rating100)
            assert s.rating100 == 75
