"""Unit tests for JobsClientMixin.

These tests mock at the HTTP boundary using respx, allowing real code execution
through the entire GraphQL client stack including serialization/deserialization.
"""

import json

import httpx
import pytest
import respx

from stash_graphql_client import StashClient
from stash_graphql_client.types import JobStatus
from tests.fixtures import create_graphql_response


# =============================================================================
# find_job tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_job_success(respx_stash_client: StashClient) -> None:
    """Test finding a job by ID successfully."""
    job_data = {
        "id": "job-123",
        "status": "RUNNING",
        "description": "Test job",
        "progress": 50.0,
        "subTasks": [],
        "addTime": "2024-01-01T00:00:00Z",
    }

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        return_value=httpx.Response(
            200, json=create_graphql_response("findJob", job_data)
        )
    )

    job = await respx_stash_client.find_job("job-123")

    assert job is not None
    assert job.id == "job-123"
    assert job.status == JobStatus.RUNNING
    assert job.progress == 50.0
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "findJob" in req["query"]
    assert req["variables"]["input"]["id"] == "job-123"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_job_empty_id(respx_stash_client: StashClient) -> None:
    """Test find_job returns None for empty job_id."""
    # Should not make any HTTP calls
    job = await respx_stash_client.find_job("")

    assert job is None


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_job_not_found(respx_stash_client: StashClient) -> None:
    """Test find_job returns None when job doesn't exist."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(200, json=create_graphql_response("findJob", None))]
    )

    job = await respx_stash_client.find_job("nonexistent")

    assert job is None
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_job_graphql_error(respx_stash_client: StashClient) -> None:
    """Test find_job handles GraphQL errors gracefully."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "data": {"findJob": None},
                    "errors": [{"message": "Job not found", "path": ["findJob"]}],
                },
            )
        ]
    )

    job = await respx_stash_client.find_job("error-job")

    assert job is None
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_job_result_with_errors_key(respx_stash_client: StashClient) -> None:
    """Test find_job returns None when result contains 'errors' key."""
    # Return a response where the data dict itself contains "errors"
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json={"data": {"errors": [{"message": "Some error"}], "findJob": None}},
            )
        ]
    )

    job = await respx_stash_client.find_job("error-job")

    assert job is None
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_job_exception(respx_stash_client: StashClient) -> None:
    """Test find_job handles exceptions gracefully."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=Exception("Network error")
    )

    job = await respx_stash_client.find_job("exception-job")

    assert job is None


# =============================================================================
# wait_for_job tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_wait_for_job_empty_id(respx_stash_client: StashClient) -> None:
    """Test wait_for_job returns None for empty job_id."""
    result = await respx_stash_client.wait_for_job("")

    assert result is None


@pytest.mark.asyncio
@pytest.mark.unit
async def test_wait_for_job_not_found(respx_stash_client: StashClient) -> None:
    """Test wait_for_job raises ValueError when job not found."""
    respx.post("http://localhost:9999/graphql").mock(
        return_value=httpx.Response(200, json=create_graphql_response("findJob", None))
    )

    with pytest.raises(ValueError, match="Job nonexistent not found"):
        await respx_stash_client.wait_for_job("nonexistent", timeout=1.0)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_wait_for_job_success(respx_stash_client: StashClient) -> None:
    """Test wait_for_job returns True when job reaches desired status."""
    job_data = {
        "id": "job-123",
        "status": "FINISHED",
        "description": "Test job",
        "progress": 100.0,
        "subTasks": [],
        "addTime": "2024-01-01T00:00:00Z",
    }

    respx.post("http://localhost:9999/graphql").mock(
        return_value=httpx.Response(
            200, json=create_graphql_response("findJob", job_data)
        )
    )

    result = await respx_stash_client.wait_for_job(
        "job-123", status=JobStatus.FINISHED, period=0.1
    )

    assert result is True


@pytest.mark.asyncio
@pytest.mark.unit
async def test_wait_for_job_finished_with_different_status(
    respx_stash_client: StashClient,
) -> None:
    """Test wait_for_job returns False when job finishes with different status."""
    job_data = {
        "id": "job-123",
        "status": "CANCELLED",
        "description": "Test job",
        "progress": 50.0,
        "subTasks": [],
        "addTime": "2024-01-01T00:00:00Z",
    }

    respx.post("http://localhost:9999/graphql").mock(
        return_value=httpx.Response(
            200, json=create_graphql_response("findJob", job_data)
        )
    )

    result = await respx_stash_client.wait_for_job(
        "job-123", status=JobStatus.FINISHED, period=0.1
    )

    assert result is False


@pytest.mark.asyncio
@pytest.mark.unit
async def test_wait_for_job_timeout(respx_stash_client: StashClient) -> None:
    """Test wait_for_job raises TimeoutError on timeout."""
    job_data = {
        "id": "job-123",
        "status": "RUNNING",
        "description": "Test job",
        "progress": 50.0,
        "subTasks": [],
        "addTime": "2024-01-01T00:00:00Z",
    }

    respx.post("http://localhost:9999/graphql").mock(
        return_value=httpx.Response(
            200, json=create_graphql_response("findJob", job_data)
        )
    )

    with pytest.raises(
        TimeoutError, match="Timeout waiting for job job-123 to reach status"
    ):
        await respx_stash_client.wait_for_job(
            "job-123", status=JobStatus.FINISHED, period=0.1, timeout=0.5
        )


# =============================================================================
# stop_job tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_stop_job_success(respx_stash_client: StashClient) -> None:
    """Test stopping a job successfully."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        return_value=httpx.Response(200, json=create_graphql_response("stopJob", True))
    )

    result = await respx_stash_client.stop_job("job-123")

    assert result is True
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "stopJob" in req["query"]
    assert req["variables"]["job_id"] == "job-123"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_stop_job_false_response(respx_stash_client: StashClient) -> None:
    """Test stop_job returns False when server returns false."""
    respx.post("http://localhost:9999/graphql").mock(
        return_value=httpx.Response(200, json=create_graphql_response("stopJob", False))
    )

    result = await respx_stash_client.stop_job("job-123")

    assert result is False


@pytest.mark.asyncio
@pytest.mark.unit
async def test_stop_job_exception(respx_stash_client: StashClient) -> None:
    """Test stop_job handles exceptions gracefully."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=Exception("Network error")
    )

    result = await respx_stash_client.stop_job("job-123")

    assert result is False


# =============================================================================
# stop_all_jobs tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_stop_all_jobs_success(respx_stash_client: StashClient) -> None:
    """Test stopping all jobs successfully."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        return_value=httpx.Response(
            200, json=create_graphql_response("stopAllJobs", True)
        )
    )

    result = await respx_stash_client.stop_all_jobs()

    assert result is True
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "stopAllJobs" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_stop_all_jobs_false_response(respx_stash_client: StashClient) -> None:
    """Test stop_all_jobs returns False when server returns false."""
    respx.post("http://localhost:9999/graphql").mock(
        return_value=httpx.Response(
            200, json=create_graphql_response("stopAllJobs", False)
        )
    )

    result = await respx_stash_client.stop_all_jobs()

    assert result is False


@pytest.mark.asyncio
@pytest.mark.unit
async def test_stop_all_jobs_exception(respx_stash_client: StashClient) -> None:
    """Test stop_all_jobs handles exceptions gracefully."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=Exception("Network error")
    )

    result = await respx_stash_client.stop_all_jobs()

    assert result is False


# =============================================================================
# job_queue tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_job_queue_success(respx_stash_client: StashClient) -> None:
    """Test getting job queue successfully."""
    jobs_data = [
        {
            "id": "job-1",
            "status": "RUNNING",
            "description": "Job 1",
            "progress": 50.0,
            "subTasks": [],
            "addTime": "2024-01-01T00:00:00Z",
        },
        {
            "id": "job-2",
            "status": "FINISHED",
            "description": "Job 2",
            "progress": 100.0,
            "subTasks": [],
            "addTime": "2024-01-01T00:01:00Z",
        },
    ]

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        return_value=httpx.Response(
            200, json=create_graphql_response("jobQueue", jobs_data)
        )
    )

    jobs = await respx_stash_client.job_queue()

    assert len(jobs) == 2
    assert jobs[0].id == "job-1"
    assert jobs[0].status == JobStatus.RUNNING
    assert jobs[1].id == "job-2"
    assert jobs[1].status == JobStatus.FINISHED
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "jobQueue" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_job_queue_empty(respx_stash_client: StashClient) -> None:
    """Test getting empty job queue."""
    respx.post("http://localhost:9999/graphql").mock(
        return_value=httpx.Response(200, json=create_graphql_response("jobQueue", []))
    )

    jobs = await respx_stash_client.job_queue()

    assert len(jobs) == 0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_job_queue_exception(respx_stash_client: StashClient) -> None:
    """Test job_queue handles exceptions gracefully."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=Exception("Network error")
    )

    jobs = await respx_stash_client.job_queue()

    assert len(jobs) == 0
