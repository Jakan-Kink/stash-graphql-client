"""Integration tests for StashClient base functionality.

Tests core client methods like execute, system status, and job management.
"""

import pytest

from stash_graphql_client import StashClient
from stash_graphql_client.types import SystemStatus
from tests.fixtures import capture_graphql_calls


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_system_status(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test getting system status from Stash."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        status = await stash_client.get_system_status()

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for get_system_status"
        assert "systemStatus" in calls[0]["query"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify response
        assert status is not None
        assert isinstance(status, SystemStatus)
        assert status.status in ("OK", "NEEDS_MIGRATION", "SETUP")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_execute_raw_query(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test executing a raw GraphQL query."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        query = """
            query {
                systemStatus {
                    status
                    appSchema
                    configPath
                    databasePath
                }
            }
        """
        result = await stash_client.execute(query)

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for execute"
        assert "systemStatus" in calls[0]["query"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify response
        assert result is not None
        assert "systemStatus" in result
        assert result["systemStatus"]["status"] in ("OK", "NEEDS_MIGRATION", "SETUP")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_job_nonexistent(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding a job with invalid ID format returns None.

    Job IDs must be numeric. Passing a string causes a GraphQL parsing error
    which is caught by the client and returns None.
    """
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        job = await stash_client.find_job("nonexistent-job-id")

        # Verify GraphQL call was attempted
        assert len(calls) == 1, "Expected 1 GraphQL call for find_job"
        assert "findJob" in calls[0]["query"]
        # find_job wraps ID in input object
        assert calls[0]["variables"]["input"]["id"] == "nonexistent-job-id"
        # GraphQL error: job IDs must be integers, not strings
        assert calls[0]["exception"] is not None
        assert "parsing" in str(calls[0]["exception"]) or "invalid syntax" in str(
            calls[0]["exception"]
        )

        # Verify response (exception caught, None returned)
        assert job is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_client_is_initialized(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test that client is properly initialized."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        # This test doesn't make GraphQL calls - just checks client state
        assert stash_client._initialized is True
        assert stash_client.gql_client is not None

        # Verify no GraphQL calls made
        assert len(calls) == 0, (
            "Expected 0 GraphQL calls for client initialization check"
        )
