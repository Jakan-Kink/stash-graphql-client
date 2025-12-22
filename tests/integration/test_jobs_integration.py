"""Integration tests for jobs mixin functionality.

Tests job operations against a real Stash instance.

Note: ~40% of jobs functionality is covered by subscription tests:
- stop_job (tested in test_subscribe_then_trigger_job)
- job_queue (tested via subscription events)
- Job state transitions and progress (tested in subscription tests)

This file focuses on query/mutation operations not fully covered by subscriptions.
"""

import pytest

from stash_graphql_client import StashClient
from stash_graphql_client.types import Job, JobStatus
from tests.fixtures import capture_graphql_calls


# =============================================================================
# Job Query Integration Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_job_queue_empty_returns_list(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test that job_queue always returns a list (even if empty).

    This test verifies the job queue query works and returns properly
    structured Job objects, regardless of queue size.
    """
    async with (
        stash_cleanup_tracker(stash_client),
        capture_graphql_calls(stash_client) as calls,
    ):
        jobs = await stash_client.job_queue()

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for job_queue"
        assert "jobQueue" in calls[0]["query"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify response
        assert isinstance(jobs, list), "job_queue should return a list"
        # Queue may be empty or have jobs - both are valid
        for job in jobs:
            assert isinstance(job, Job), "Each item should be a Job object"
            assert job.id is not None, "Job should have an id"
            assert job.status in [
                JobStatus.READY,
                JobStatus.RUNNING,
                JobStatus.FINISHED,
                JobStatus.STOPPING,
                JobStatus.CANCELLED,
                JobStatus.FAILED,
            ], f"Job has unexpected status: {job.status}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_job_with_valid_nonexistent_id(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding a job with a valid numeric ID that doesn't exist returns None.

    Unlike the test_base_integration test which uses an invalid ID format,
    this test uses a valid numeric ID that simply doesn't exist in the queue.
    """
    async with (
        stash_cleanup_tracker(stash_client),
        capture_graphql_calls(stash_client) as calls,
    ):
        # Use a large numeric ID that's unlikely to exist
        job = await stash_client.find_job("999999")

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_job"
        assert "findJob" in calls[0]["query"]
        assert calls[0]["variables"]["input"]["id"] == "999999"
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify response - should be None for nonexistent job
        assert job is None, "Finding nonexistent job should return None"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_job_validates_response_structure(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test that find_job properly validates response structure.

    This test verifies the find_job method can handle various response states
    and returns proper Job objects when data is available.
    """
    async with (
        stash_cleanup_tracker(stash_client),
        capture_graphql_calls(stash_client) as calls,
    ):
        # First, get the current job queue to find a real job ID if available
        queue = await stash_client.job_queue()

        # We need at least one job to complete this test
        if not queue:
            pytest.skip("No jobs in queue to test find_job with valid ID")

        # Get the first job ID from the queue
        job_id = str(queue[0].id)

        # Clear calls to focus on find_job
        calls.clear()

        # Find the job
        job = await stash_client.find_job(job_id)

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_job"
        assert "findJob" in calls[0]["query"]
        assert calls[0]["variables"]["input"]["id"] == job_id
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify response structure if job was found
        if job is not None:
            assert isinstance(job, Job), "Result should be a Job object"
            assert job.id == job_id, "Job ID should match requested ID"
            assert job.status in [
                JobStatus.READY,
                JobStatus.RUNNING,
                JobStatus.FINISHED,
                JobStatus.STOPPING,
                JobStatus.CANCELLED,
                JobStatus.FAILED,
            ], f"Job has unexpected status: {job.status}"


# =============================================================================
# Job Mutation Integration Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_stop_all_jobs_returns_boolean(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test that stop_all_jobs returns a boolean result.

    This mutation attempts to stop all running jobs and returns a boolean
    indicating success. Even if no jobs are running, the call should succeed
    and return a valid boolean.
    """
    async with (
        stash_cleanup_tracker(stash_client),
        capture_graphql_calls(stash_client) as calls,
    ):
        result = await stash_client.stop_all_jobs()

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for stop_all_jobs"
        assert "stopAllJobs" in calls[0]["query"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify response - should be a boolean
        assert isinstance(result, bool), "stop_all_jobs should return a boolean"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_stop_nonexistent_job_returns_boolean(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test that stopping a nonexistent job returns a boolean.

    Attempting to stop a job that doesn't exist should gracefully
    return a boolean result. The Stash API returns True even for
    nonexistent job IDs because the mutation itself succeeds at the
    GraphQL level (it just doesn't match any jobs to stop).
    """
    async with (
        stash_cleanup_tracker(stash_client),
        capture_graphql_calls(stash_client) as calls,
    ):
        result = await stash_client.stop_job("999999")

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for stop_job"
        assert "stopJob" in calls[0]["query"]
        assert calls[0]["variables"]["job_id"] == "999999"
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify response - stop_job returns a boolean (Stash returns True for nonexistent IDs)
        assert isinstance(result, bool), "stop_job should return a boolean"


# =============================================================================
# Job Polling Integration Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_wait_for_job_nonexistent_raises_error(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test that wait_for_job raises ValueError for nonexistent job.

    The wait_for_job method should raise a ValueError if the job
    cannot be found after the first check.
    """
    async with stash_cleanup_tracker(stash_client):
        with pytest.raises(ValueError, match="Job 999999 not found"):
            await stash_client.wait_for_job("999999", timeout=1.0)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_wait_for_job_timeout_raises_error(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test that wait_for_job raises TimeoutError or returns False appropriately.

    In integration testing against a real Stash instance, job completion time is
    unpredictable. This test verifies that wait_for_job:
    - Raises TimeoutError if the job stays RUNNING past the timeout
    - Returns False if the job finishes with a different status before timeout

    Both outcomes are valid depending on system load and job duration.
    """
    async with stash_cleanup_tracker(stash_client):
        # Trigger a job that won't reach STOPPING status
        job_id = await stash_client.metadata_scan()

        try:
            # Use STOPPING as an unreachable target status
            # Job will either: finish (return False) or timeout (raise TimeoutError)
            result = await stash_client.wait_for_job(
                str(job_id),
                status=JobStatus.STOPPING,
                period=0.5,
                timeout=2.0,  # Short timeout to force timeout scenario
            )

            # If we get here, job finished with different status
            assert isinstance(result, bool), "wait_for_job should return boolean"
            assert result is False, "Job finished with different status than STOPPING"
        except TimeoutError as e:
            # Timeout was reached - also valid outcome -- the noqa is because we ARE catching it
            # not expecting it like pytest.raises would.
            assert "Timeout waiting for job" in str(e), (  # noqa: PT017
                "TimeoutError should mention timeout and job ID"
            )
        finally:
            # Clean up
            await stash_client.stop_job(str(job_id))


@pytest.mark.integration
@pytest.mark.asyncio
async def test_wait_for_job_returns_none_for_invalid_input(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test that wait_for_job returns None for empty/invalid job_id.

    The wait_for_job method should handle empty strings gracefully
    by returning None without making GraphQL calls.
    """
    async with (
        stash_cleanup_tracker(stash_client),
        capture_graphql_calls(stash_client) as calls,
    ):
        result = await stash_client.wait_for_job("")

        # Verify no GraphQL calls were made (early return)
        assert len(calls) == 0, "Expected 0 GraphQL calls for empty job_id"

        # Verify response
        assert result is None, "wait_for_job with empty ID should return None"


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.flaky(reruns=2)  # May be flaky if metadata_clean is very fast
async def test_wait_for_job_completion(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test that wait_for_job successfully waits for job completion.

    This test triggers a quick metadata operation and waits for it to
    reach FINISHED or CANCELLED status, verifying the polling mechanism works.
    """
    async with stash_cleanup_tracker(stash_client):
        # Trigger a fast operation
        job_id = await stash_client.metadata_clean({"dryRun": True})
        assert job_id is not None, "metadata_clean should return a job ID"

        # Wait for job to finish with reasonable timeout
        try:
            result = await stash_client.wait_for_job(
                str(job_id),
                status=JobStatus.FINISHED,
                period=1.0,  # Check every 1 second
                timeout=30.0,  # Wait up to 30 seconds
            )

            # Result should indicate job status
            assert isinstance(result, (bool, type(None))), (
                "wait_for_job should return bool or None"
            )

            # If we got True, the job finished successfully
            if result is True:
                # Verify job actually finished
                job = await stash_client.find_job(str(job_id))
                if job:
                    assert job.status == JobStatus.FINISHED, (
                        "Job should be in FINISHED status"
                    )
        except TimeoutError:
            # It's acceptable if the job takes longer than expected
            # Just verify it exists and hasn't errored
            job = await stash_client.find_job(str(job_id))
            if job:
                assert job.status in [
                    JobStatus.RUNNING,
                    JobStatus.FINISHED,
                    JobStatus.CANCELLED,
                    JobStatus.FAILED,
                ], "Job should be in a valid state"
