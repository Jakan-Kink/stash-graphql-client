"""Integration tests for StashClient base functionality.

Tests core client methods like execute, system status, and job management.
"""

import pytest

from stash_graphql_client import StashClient
from stash_graphql_client.types import SystemStatus


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_system_status(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test getting system status from Stash."""
    async with stash_cleanup_tracker(stash_client, auto_capture=False):
        status = await stash_client.get_system_status()

        assert status is not None
        assert isinstance(status, SystemStatus)
        assert status.status in ("OK", "NEEDS_MIGRATION", "SETUP")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_execute_raw_query(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test executing a raw GraphQL query."""
    async with stash_cleanup_tracker(stash_client, auto_capture=False):
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

        assert result is not None
        assert "systemStatus" in result
        assert result["systemStatus"]["status"] in ("OK", "NEEDS_MIGRATION", "SETUP")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_job_nonexistent(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding a job that doesn't exist returns None."""
    async with stash_cleanup_tracker(stash_client, auto_capture=False):
        job = await stash_client.find_job("nonexistent-job-id")

        assert job is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_client_is_initialized(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test that client is properly initialized."""
    async with stash_cleanup_tracker(stash_client, auto_capture=False):
        assert stash_client._initialized is True
        assert stash_client.gql_client is not None
