"""Integration tests for performer mixin functionality.

Tests performer operations against a real Stash instance.
"""

import pytest

from stash_graphql_client import StashClient
from stash_graphql_client.types import BulkPerformerUpdateInput, Performer
from stash_graphql_client.types.unset import is_set
from tests.fixtures import capture_graphql_calls


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_performers_returns_results(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding performers returns results (may be empty)."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        result = await stash_client.find_performers()

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_performers"
        assert "findPerformers" in calls[0]["query"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Result should be valid even if empty
        assert is_set(result.count)
        assert result.count >= 0
        assert isinstance(result.performers, list)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_performers_with_pagination(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test performer pagination works correctly."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        result = await stash_client.find_performers(filter_={"per_page": 10, "page": 1})

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_performers"
        assert "findPerformers" in calls[0]["query"]
        assert calls[0]["variables"]["filter"]["per_page"] == 10
        assert calls[0]["variables"]["filter"]["page"] == 1
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify response
        assert is_set(result.performers)
        assert len(result.performers) <= 10


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_nonexistent_performer_returns_none(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding a nonexistent performer returns None."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        performer = await stash_client.find_performer("99999999")

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_performer"
        assert "findPerformer" in calls[0]["query"]
        assert calls[0]["variables"]["id"] == "99999999"
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify response
        assert performer is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_performer_by_name_filter(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding performer using name filter."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        # Search for a performer that likely doesn't exist
        result = await stash_client.find_performers(
            performer_filter={
                "name": {"value": "NonexistentPerformer12345", "modifier": "EQUALS"}
            }
        )

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_performers"
        assert "findPerformers" in calls[0]["query"]
        assert "performer_filter" in calls[0]["variables"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify response
        assert result.count == 0
        assert is_set(result.performers)
        assert len(result.performers) == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_performers_with_q_parameter(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding performers using q search parameter."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        result = await stash_client.find_performers(q="test")

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_performers"
        assert "findPerformers" in calls[0]["query"]
        # q parameter is added to filter dict
        assert calls[0]["variables"]["filter"]["q"] == "test"
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Should return valid result (may or may not have matches)
        assert is_set(result.count)
        assert result.count >= 0
        assert isinstance(result.performers, list)


# =============================================================================
# Performer mutation lifecycle tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="performer_mutations")
async def test_create_and_find_performer(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test creating a performer and retrieving it by ID."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        performer = await stash_client.create_performer(
            Performer(name="SGC Inttest Create")
        )
        cleanup["performers"].append(performer.id)

        assert len(calls) == 1, "Expected 1 GraphQL call for create_performer"
        assert "performerCreate" in calls[0]["query"]
        assert calls[0]["exception"] is None

        assert performer.id is not None
        assert is_set(performer.name)
        assert performer.name == "SGC Inttest Create"

        calls.clear()

        found = await stash_client.find_performer(performer.id)

        assert len(calls) == 1, "Expected 1 GraphQL call for find_performer"
        assert "findPerformer" in calls[0]["query"]
        assert calls[0]["exception"] is None

        assert found is not None
        assert found.id == performer.id
        assert found.name == "SGC Inttest Create"


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="performer_mutations")
async def test_update_performer(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test creating a performer and updating their details."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        performer = await stash_client.create_performer(
            Performer(name="SGC Inttest Update")
        )
        cleanup["performers"].append(performer.id)
        assert performer.id is not None

        calls.clear()

        performer.details = "integration test details"
        updated = await stash_client.update_performer(performer)

        assert len(calls) == 1, "Expected 1 GraphQL call for update_performer"
        assert "performerUpdate" in calls[0]["query"]
        assert calls[0]["exception"] is None

        assert updated.id == performer.id
        assert is_set(updated.details)
        assert updated.details == "integration test details"


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="performer_mutations")
async def test_performer_destroy(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test creating a performer and then destroying them."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        performer = await stash_client.create_performer(
            Performer(name="SGC Inttest Destroy")
        )
        cleanup["performers"].append(performer.id)
        assert performer.id is not None

        calls.clear()

        result = await stash_client.performer_destroy({"id": performer.id})

        assert len(calls) == 1, "Expected 1 GraphQL call for performer_destroy"
        assert "performerDestroy" in calls[0]["query"]
        assert calls[0]["exception"] is None
        assert result is True

        # Remove from cleanup so the tracker doesn't attempt a double-delete
        cleanup["performers"].remove(performer.id)

        calls.clear()

        # Confirm the performer is gone
        gone = await stash_client.find_performer(performer.id)
        assert gone is None


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="performer_mutations")
async def test_performers_destroy_bulk(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test bulk-destroying multiple performers in a single call."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        perf_a = await stash_client.create_performer(
            Performer(name="SGC Inttest Bulk Destroy A")
        )
        perf_b = await stash_client.create_performer(
            Performer(name="SGC Inttest Bulk Destroy B")
        )
        cleanup["performers"].append(perf_a.id)
        cleanup["performers"].append(perf_b.id)
        assert perf_a.id is not None
        assert perf_b.id is not None

        calls.clear()

        result = await stash_client.performers_destroy([perf_a.id, perf_b.id])

        assert len(calls) == 1, "Expected 1 GraphQL call for performers_destroy"
        assert "performersDestroy" in calls[0]["query"]
        assert calls[0]["exception"] is None
        assert result is True

        # Remove from cleanup — already destroyed
        cleanup["performers"].remove(perf_a.id)
        cleanup["performers"].remove(perf_b.id)


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="performer_mutations")
async def test_bulk_performer_update(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test updating multiple performers' details in a single bulk call."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        perf_a = await stash_client.create_performer(
            Performer(name="SGC Inttest Bulk Update A")
        )
        perf_b = await stash_client.create_performer(
            Performer(name="SGC Inttest Bulk Update B")
        )
        cleanup["performers"].append(perf_a.id)
        cleanup["performers"].append(perf_b.id)
        assert perf_a.id is not None
        assert perf_b.id is not None

        calls.clear()

        updated_performers = await stash_client.bulk_performer_update(
            BulkPerformerUpdateInput(
                ids=[perf_a.id, perf_b.id],
                details="bulk-updated",
            )
        )

        assert len(calls) == 1, "Expected 1 GraphQL call for bulk_performer_update"
        assert "bulkPerformerUpdate" in calls[0]["query"]
        assert calls[0]["exception"] is None

        assert len(updated_performers) == 2
        for p in updated_performers:
            assert is_set(p.details)
            assert p.details == "bulk-updated"


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="performer_mutations")
async def test_performer_merge(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test merging a source performer into a destination performer."""
    if not stash_client._capabilities.has_performer_merge_input:
        pytest.skip(
            "Server does not support performerMerge (PerformerMergeInput not available)"
        )

    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        source = await stash_client.create_performer(
            Performer(name="SGC Inttest Merge Source")
        )
        dest = await stash_client.create_performer(
            Performer(name="SGC Inttest Merge Dest")
        )
        cleanup["performers"].append(source.id)
        cleanup["performers"].append(dest.id)
        assert source.id is not None
        assert dest.id is not None

        calls.clear()

        merged = await stash_client.performer_merge(
            {"source": [source.id], "destination": dest.id}
        )

        assert len(calls) == 1, "Expected 1 GraphQL call for performer_merge"
        assert "performerMerge" in calls[0]["query"]
        assert calls[0]["exception"] is None

        assert merged.id == dest.id

        # The source performer is consumed by the merge — remove from cleanup
        cleanup["performers"].remove(source.id)
