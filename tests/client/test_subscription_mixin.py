"""Unit tests for SubscriptionClientMixin.

These tests mock at the HTTP/WebSocket boundary, allowing real code execution
through the entire GraphQL client stack including subscription handling.

Note: Subscription tests require mocking WebSocket connections since subscriptions
use a different transport mechanism than standard HTTP queries/mutations.

Testing Strategy:
- Mock WebSocket session's subscribe method to return test data
- Avoid MagicMock where possible by using real async iterators
- Use helper functions to create mock WebSocket sessions consistently
"""

import asyncio
import json
from collections.abc import AsyncIterator
from unittest.mock import patch

import httpx
import pytest
import respx

from stash_graphql_client import StashClient
from stash_graphql_client.client.mixins.subscription import AsyncIteratorWrapper
from stash_graphql_client.types import Job, JobStatus, JobStatusUpdate, LogEntry


# =============================================================================
# Helper: Mock async iterator for subscription responses
# =============================================================================


class MockAsyncIterator(AsyncIterator):
    """Mock async iterator that yields predefined values.

    This is a real async iterator implementation, not a mock.
    It's used to simulate WebSocket subscription responses.
    """

    def __init__(self, values: list):
        """Initialize with list of values to yield.

        Args:
            values: List of values to yield from the iterator
        """
        self.values = values
        self.index = 0

    def __aiter__(self):
        """Return self as async iterator."""
        return self

    async def __anext__(self):
        """Get next value or raise StopAsyncIteration."""
        if self.index >= len(self.values):
            raise StopAsyncIteration
        value = self.values[self.index]
        self.index += 1
        return value


# =============================================================================
# Helper: Mock WebSocket session
# =============================================================================


class MockWebSocketSession:
    """Mock WebSocket session for testing subscriptions.

    This is a minimal implementation that provides just the subscribe method
    needed for testing, avoiding MagicMock.
    """

    def __init__(self, responses: list | Exception):
        """Initialize with either a list of responses or an exception to raise.

        Args:
            responses: List of response dicts to yield, or Exception to raise
        """
        self.responses = responses

    def subscribe(self, query):
        """Return an async iterator of responses.

        Args:
            query: GraphQL subscription query (unused in mock)

        Returns:
            Async iterator of responses

        Raises:
            Exception if initialized with an exception
        """
        if isinstance(self.responses, Exception):
            raise self.responses
        return MockAsyncIterator(self.responses)


# =============================================================================
# subscribe_to_jobs Tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_subscribe_to_jobs_yields_updates(
    respx_stash_client: StashClient,
) -> None:
    """Test that subscribe_to_jobs yields JobStatusUpdate objects."""
    # Set up WebSocket session with test responses
    respx_stash_client._ws_session = MockWebSocketSession(
        [
            {
                "jobsSubscribe": {
                    "type": "ADD",
                    "job": {
                        "id": "job_123",
                        "status": "RUNNING",
                        "subTasks": [],
                        "description": "Scanning metadata",
                        "progress": 50.0,
                        "addTime": "2024-01-01T00:00:00Z",
                        "error": None,
                    },
                }
            },
            {
                "jobsSubscribe": {
                    "type": "UPDATE",
                    "job": {
                        "id": "job_123",
                        "status": "RUNNING",
                        "subTasks": [],
                        "description": "Scanning metadata",
                        "progress": 75.0,
                        "addTime": "2024-01-01T00:00:00Z",
                        "error": None,
                    },
                }
            },
            {
                "jobsSubscribe": {
                    "type": "UPDATE",
                    "job": {
                        "id": "job_123",
                        "status": "FINISHED",
                        "subTasks": [],
                        "description": "Scanning metadata",
                        "progress": 100.0,
                        "addTime": "2024-01-01T00:00:00Z",
                        "error": None,
                    },
                }
            },
        ]
    )

    # Subscribe and collect updates
    updates = []
    async with respx_stash_client.subscribe_to_jobs() as subscription:
        async for update in subscription:
            updates.append(update)
            # Break after getting all 3 updates
            if len(updates) == 3:
                break

    # Verify we got all 3 updates
    assert len(updates) == 3

    # Verify first update (ADD, 50% progress)
    assert isinstance(updates[0], JobStatusUpdate)
    assert updates[0].type == "ADD"
    assert isinstance(updates[0].job, Job)
    assert updates[0].job.id == "job_123"
    assert updates[0].job.status == JobStatus.RUNNING
    assert updates[0].job.progress == 50.0

    # Verify second update (UPDATE, 75% progress)
    assert updates[1].type == "UPDATE"
    assert updates[1].job.progress == 75.0

    # Verify third update (UPDATE, finished)
    assert updates[2].type == "UPDATE"
    assert updates[2].job.status == JobStatus.FINISHED
    assert updates[2].job.progress == 100.0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_subscribe_to_jobs_no_ws_session_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test that subscribe_to_jobs raises if WebSocket session is not available."""
    # Ensure _ws_session is None
    respx_stash_client._ws_session = None

    # Should raise exception when trying to subscribe without WebSocket
    with pytest.raises(Exception, match="Failed to connect"):
        async with respx_stash_client.subscribe_to_jobs() as subscription:
            [_ async for _ in subscription]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_subscribe_to_jobs_empty_stream(respx_stash_client: StashClient) -> None:
    """Test that subscribe_to_jobs handles empty subscription stream."""
    # Set up WebSocket session with empty responses
    respx_stash_client._ws_session = MockWebSocketSession([])

    # Subscribe and verify no updates
    updates = []
    async with respx_stash_client.subscribe_to_jobs() as subscription:
        updates.extend([update async for update in subscription])

    assert len(updates) == 0


# =============================================================================
# subscribe_to_logs Tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_subscribe_to_logs_yields_log_entries(
    respx_stash_client: StashClient,
) -> None:
    """Test that subscribe_to_logs yields LogEntry lists."""
    # Set up WebSocket session with log responses
    respx_stash_client._ws_session = MockWebSocketSession(
        [
            {
                "loggingSubscribe": [
                    {
                        "time": "2024-01-01T10:00:00Z",
                        "level": "Info",
                        "message": "Starting scan",
                    },
                    {
                        "time": "2024-01-01T10:00:01Z",
                        "level": "Debug",
                        "message": "Processing file 1",
                    },
                ]
            },
            {
                "loggingSubscribe": [
                    {
                        "time": "2024-01-01T10:00:02Z",
                        "level": "Info",
                        "message": "Scan complete",
                    }
                ]
            },
            {
                "loggingSubscribe": [
                    {
                        "time": "2024-01-01T10:00:03Z",
                        "level": "Error",
                        "message": "Failed to process file",
                    }
                ]
            },
        ]
    )

    # Subscribe and collect log batches
    log_batches = []
    async with respx_stash_client.subscribe_to_logs() as subscription:
        async for logs in subscription:
            log_batches.append(logs)
            if len(log_batches) == 3:
                break

    # Verify we got 3 batches
    assert len(log_batches) == 3

    # Verify first batch (2 entries)
    assert len(log_batches[0]) == 2
    assert isinstance(log_batches[0][0], LogEntry)
    assert log_batches[0][0].level == "Info"
    assert log_batches[0][0].message == "Starting scan"
    assert log_batches[0][1].level == "Debug"

    # Verify second batch (1 entry)
    assert len(log_batches[1]) == 1
    assert log_batches[1][0].message == "Scan complete"

    # Verify third batch (1 error entry)
    assert len(log_batches[2]) == 1
    assert log_batches[2][0].level == "Error"
    assert log_batches[2][0].message == "Failed to process file"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_subscribe_to_logs_no_ws_session_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test that subscribe_to_logs raises if WebSocket session is not available."""
    respx_stash_client._ws_session = None

    with pytest.raises(Exception, match="Failed to connect"):
        async with respx_stash_client.subscribe_to_logs() as subscription:
            [_ async for _ in subscription]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_subscribe_to_logs_empty_batches(respx_stash_client: StashClient) -> None:
    """Test that subscribe_to_logs handles empty log batches."""
    # Set up WebSocket session with empty and non-empty batches
    respx_stash_client._ws_session = MockWebSocketSession(
        [
            {"loggingSubscribe": []},  # Empty batch
            {
                "loggingSubscribe": [
                    {
                        "time": "2024-01-01T10:00:00Z",
                        "level": "Info",
                        "message": "Test",
                    }
                ]
            },
        ]
    )

    log_batches = []
    async with respx_stash_client.subscribe_to_logs() as subscription:
        async for logs in subscription:
            log_batches.append(logs)
            if len(log_batches) == 2:
                break

    # Verify we got both batches
    assert len(log_batches) == 2
    assert len(log_batches[0]) == 0  # Empty batch
    assert len(log_batches[1]) == 1  # Batch with one entry


# =============================================================================
# subscribe_to_scan_complete Tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_subscribe_to_scan_complete_yields_bool(
    respx_stash_client: StashClient,
) -> None:
    """Test that subscribe_to_scan_complete yields boolean values."""
    # Set up WebSocket session with scan complete events
    respx_stash_client._ws_session = MockWebSocketSession(
        [
            {"scanCompleteSubscribe": True},
            {"scanCompleteSubscribe": True},
        ]
    )

    events = []
    async with respx_stash_client.subscribe_to_scan_complete() as subscription:
        async for event in subscription:
            events.append(event)
            if len(events) == 2:
                break

    assert len(events) == 2
    assert events[0] is True
    assert events[1] is True


@pytest.mark.asyncio
@pytest.mark.unit
async def test_subscribe_to_scan_complete_no_ws_session_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test that subscribe_to_scan_complete raises if WebSocket session is not available."""
    respx_stash_client._ws_session = None

    with pytest.raises(Exception, match="Failed to connect"):
        async with respx_stash_client.subscribe_to_scan_complete() as subscription:
            [_ async for _ in subscription]


# =============================================================================
# _check_job_status Tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_check_job_status_found_running(
    respx_stash_client: StashClient,
) -> None:
    """Test _check_job_status with a running job."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "data": {
                        "findJob": {
                            "id": "job_123",
                            "status": "RUNNING",
                            "progress": 50.0,
                            "description": "Scanning metadata",
                        }
                    }
                },
            )
        ]
    )

    is_done, status = await respx_stash_client._check_job_status("job_123")

    assert is_done is False
    assert status == JobStatus.RUNNING

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "findJob" in req["query"]
    assert req["variables"]["id"] == "job_123"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_check_job_status_found_finished(
    respx_stash_client: StashClient,
) -> None:
    """Test _check_job_status with a finished job."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "data": {
                        "findJob": {
                            "id": "job_123",
                            "status": "FINISHED",
                            "progress": 100.0,
                            "description": "Scanning metadata",
                        }
                    }
                },
            )
        ]
    )

    is_done, status = await respx_stash_client._check_job_status("job_123")

    assert is_done is True
    assert status == JobStatus.FINISHED

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_check_job_status_found_cancelled(
    respx_stash_client: StashClient,
) -> None:
    """Test _check_job_status with a cancelled job."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "data": {
                        "findJob": {
                            "id": "job_123",
                            "status": "CANCELLED",
                            "progress": 75.0,
                            "description": "Scanning metadata",
                        }
                    }
                },
            )
        ]
    )

    is_done, status = await respx_stash_client._check_job_status("job_123")

    assert is_done is True
    assert status == JobStatus.CANCELLED


@pytest.mark.asyncio
@pytest.mark.unit
async def test_check_job_status_not_found(respx_stash_client: StashClient) -> None:
    """Test _check_job_status when job is not found."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json={"data": {"findJob": None}},
            )
        ]
    )

    is_done, status = await respx_stash_client._check_job_status("nonexistent")

    assert is_done is None
    assert status is None

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1


# =============================================================================
# wait_for_job_with_updates Tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_wait_for_job_with_updates_already_finished(
    respx_stash_client: StashClient,
) -> None:
    """Test wait_for_job_with_updates when job is already finished."""
    # Mock _check_job_status to return finished immediately
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "data": {
                        "findJob": {
                            "id": "job_123",
                            "status": "FINISHED",
                            "progress": 100.0,
                            "description": "Already done",
                        }
                    }
                },
            )
        ]
    )

    result = await respx_stash_client.wait_for_job_with_updates("job_123")

    assert result is True

    # Should only call _check_job_status once
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_wait_for_job_with_updates_not_found(
    respx_stash_client: StashClient,
) -> None:
    """Test wait_for_job_with_updates when job doesn't exist."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json={"data": {"findJob": None}},
            )
        ]
    )

    result = await respx_stash_client.wait_for_job_with_updates("nonexistent")

    assert result is None

    # Should call _check_job_status once
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_wait_for_job_with_updates_via_subscription(
    respx_stash_client: StashClient,
) -> None:
    """Test wait_for_job_with_updates receives updates via subscription."""
    # First call: job is running
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "data": {
                        "findJob": {
                            "id": "job_123",
                            "status": "RUNNING",
                            "progress": 10.0,
                            "description": "Processing",
                        }
                    }
                },
            )
        ]
    )

    # Set up WebSocket session with subscription updates
    respx_stash_client._ws_session = MockWebSocketSession(
        [
            {
                "jobsSubscribe": {
                    "type": "UPDATE",
                    "job": {
                        "id": "job_123",
                        "status": "RUNNING",
                        "subTasks": [],
                        "description": "Processing",
                        "progress": 50.0,
                        "addTime": "2024-01-01T00:00:00Z",
                        "error": None,
                    },
                }
            },
            {
                "jobsSubscribe": {
                    "type": "UPDATE",
                    "job": {
                        "id": "job_123",
                        "status": "FINISHED",
                        "subTasks": [],
                        "description": "Done",
                        "progress": 100.0,
                        "addTime": "2024-01-01T00:00:00Z",
                        "error": None,
                    },
                }
            },
        ]
    )

    result = await respx_stash_client.wait_for_job_with_updates("job_123")

    assert result is True


@pytest.mark.asyncio
@pytest.mark.unit
async def test_wait_for_job_with_updates_wrong_status(
    respx_stash_client: StashClient,
) -> None:
    """Test wait_for_job_with_updates when job finishes with wrong status."""
    # Job is running initially
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "data": {
                        "findJob": {
                            "id": "job_123",
                            "status": "RUNNING",
                            "progress": 10.0,
                            "description": "Processing",
                        }
                    }
                },
            )
        ]
    )

    # Set up WebSocket session - job gets cancelled instead of finished
    respx_stash_client._ws_session = MockWebSocketSession(
        [
            {
                "jobsSubscribe": {
                    "type": "UPDATE",
                    "job": {
                        "id": "job_123",
                        "status": "CANCELLED",
                        "subTasks": [],
                        "description": "Cancelled",
                        "progress": 50.0,
                        "addTime": "2024-01-01T00:00:00Z",
                        "error": None,
                    },
                }
            }
        ]
    )

    # Wait for FINISHED but job gets CANCELLED
    result = await respx_stash_client.wait_for_job_with_updates(
        "job_123", status=JobStatus.FINISHED
    )

    assert result is False


@pytest.mark.asyncio
@pytest.mark.unit
async def test_wait_for_job_with_updates_timeout(
    respx_stash_client: StashClient,
) -> None:
    """Test wait_for_job_with_updates handles timeout."""
    # Job is running
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "data": {
                        "findJob": {
                            "id": "job_123",
                            "status": "RUNNING",
                            "progress": 10.0,
                            "description": "Processing",
                        }
                    }
                },
            ),
            # Second call for wait_for_job fallback
            httpx.Response(
                200,
                json={
                    "data": {
                        "findJob": {
                            "id": "job_123",
                            "status": "RUNNING",
                            "progress": 10.0,
                            "description": "Processing",
                        }
                    }
                },
            ),
        ]
    )

    # Set up WebSocket session with empty responses (to trigger timeout)
    respx_stash_client._ws_session = MockWebSocketSession([])

    # Use very short timeout
    result = await respx_stash_client.wait_for_job_with_updates("job_123", timeout=0.1)

    # Should return None due to timeout
    assert result is None


@pytest.mark.asyncio
@pytest.mark.unit
async def test_wait_for_job_with_updates_timeout_during_wait(
    respx_stash_client: StashClient,
) -> None:
    """Test wait_for_job_with_updates handles timeout while waiting for updates."""
    # Job is running
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "data": {
                        "findJob": {
                            "id": "job_123",
                            "status": "RUNNING",
                            "progress": 10.0,
                            "description": "Processing",
                        }
                    }
                },
            )
        ]
    )

    # Create an async iterator that never yields (blocks forever)
    class BlockingAsyncIterator:
        def __aiter__(self):
            return self

        async def __anext__(self):
            # Sleep forever to trigger timeout
            await asyncio.sleep(999999)
            raise StopAsyncIteration

    class BlockingWebSocketSession:
        def subscribe(self, query):
            return BlockingAsyncIterator()

    respx_stash_client._ws_session = BlockingWebSocketSession()

    # Use very short timeout - should trigger TimeoutError exception
    result = await respx_stash_client.wait_for_job_with_updates("job_123", timeout=0.1)

    # Should return None due to timeout exception
    assert result is None


@pytest.mark.asyncio
@pytest.mark.unit
async def test_wait_for_job_with_updates_ignores_other_jobs(
    respx_stash_client: StashClient,
) -> None:
    """Test wait_for_job_with_updates ignores updates for other jobs."""
    # Job is running
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "data": {
                        "findJob": {
                            "id": "job_123",
                            "status": "RUNNING",
                            "progress": 10.0,
                            "description": "Processing",
                        }
                    }
                },
            )
        ]
    )

    # Set up WebSocket session with updates for different jobs
    respx_stash_client._ws_session = MockWebSocketSession(
        [
            # Update for different job - should be ignored
            {
                "jobsSubscribe": {
                    "type": "UPDATE",
                    "job": {
                        "id": "job_999",
                        "status": "FINISHED",
                        "subTasks": [],
                        "description": "Other job",
                        "progress": 100.0,
                        "addTime": "2024-01-01T00:00:00Z",
                        "error": None,
                    },
                }
            },
            # Update for our job
            {
                "jobsSubscribe": {
                    "type": "UPDATE",
                    "job": {
                        "id": "job_123",
                        "status": "FINISHED",
                        "subTasks": [],
                        "description": "Done",
                        "progress": 100.0,
                        "addTime": "2024-01-01T00:00:00Z",
                        "error": None,
                    },
                }
            },
        ]
    )

    result = await respx_stash_client.wait_for_job_with_updates("job_123")

    assert result is True


@pytest.mark.asyncio
@pytest.mark.unit
async def test_wait_for_job_with_updates_handles_string_status(
    respx_stash_client: StashClient,
) -> None:
    """Test wait_for_job_with_updates handles status as string."""
    # Job is running
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "data": {
                        "findJob": {
                            "id": "job_123",
                            "status": "RUNNING",
                            "progress": 10.0,
                            "description": "Processing",
                        }
                    }
                },
            )
        ]
    )

    # Set up WebSocket session with status as string (not enum)
    respx_stash_client._ws_session = MockWebSocketSession(
        [
            {
                "jobsSubscribe": {
                    "type": "UPDATE",
                    "job": {
                        "id": "job_123",
                        "status": "FINISHED",  # String instead of JobStatus enum
                        "subTasks": [],
                        "description": "Done",
                        "progress": 100.0,
                        "addTime": "2024-01-01T00:00:00Z",
                        "error": None,
                    },
                }
            }
        ]
    )

    result = await respx_stash_client.wait_for_job_with_updates("job_123")

    assert result is True


@pytest.mark.asyncio
@pytest.mark.unit
async def test_wait_for_job_with_updates_handles_missing_status(
    respx_stash_client: StashClient,
) -> None:
    """Test wait_for_job_with_updates handles update without status."""
    # Job is running
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "data": {
                        "findJob": {
                            "id": "job_123",
                            "status": "RUNNING",
                            "progress": 10.0,
                            "description": "Processing",
                        }
                    }
                },
            )
        ]
    )

    # Create mock job with None status
    class MockJob:
        def __init__(self):
            self.id = "job_123"
            self.status = None  # No status
            self.progress = 50.0
            self.description = "Processing"

    class MockUpdate:
        def __init__(self, job):
            self.job = job

    # Mock subscription iterator that returns mock updates
    async def mock_subscription_gen():
        # First update: no status (should be skipped)
        yield MockUpdate(MockJob())
        # Second update: valid status
        yield JobStatusUpdate.model_validate(
            {
                "type": "UPDATE",
                "job": {
                    "id": "job_123",
                    "status": "FINISHED",
                    "subTasks": [],
                    "description": "Done",
                    "progress": 100.0,
                    "addTime": "2024-01-01T00:00:00Z",
                },
            }
        )

    # Create a mock context manager for subscribe_to_jobs
    class MockSubscriptionContext:
        async def __aenter__(self):
            return mock_subscription_gen()

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    # Replace subscribe_to_jobs with our mock using patch.object
    def mock_subscribe():
        return MockSubscriptionContext()

    with patch.object(
        respx_stash_client, "subscribe_to_jobs", side_effect=mock_subscribe
    ):
        result = await respx_stash_client.wait_for_job_with_updates("job_123")
        assert result is True


@pytest.mark.asyncio
@pytest.mark.unit
async def test_wait_for_job_with_updates_subscription_exception_fallback(
    respx_stash_client: StashClient,
) -> None:
    """Test wait_for_job_with_updates falls back to polling on subscription error."""
    # First call: job is running
    # Second call: job is finished (for fallback polling)
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "data": {
                        "findJob": {
                            "id": "job_123",
                            "status": "RUNNING",
                            "progress": 10.0,
                            "description": "Processing",
                        }
                    }
                },
            ),
            # Fallback polling checks
            httpx.Response(
                200,
                json={
                    "data": {
                        "findJob": {
                            "id": "job_123",
                            "status": "FINISHED",
                            "progress": 100.0,
                            "description": "Done",
                        }
                    }
                },
            ),
        ]
    )

    # Set up WebSocket session to raise exception
    respx_stash_client._ws_session = MockWebSocketSession(Exception("Connection error"))

    result = await respx_stash_client.wait_for_job_with_updates("job_123")

    # Should have fallen back to polling and succeeded
    assert result is True


@pytest.mark.asyncio
@pytest.mark.unit
async def test_wait_for_job_with_updates_custom_status(
    respx_stash_client: StashClient,
) -> None:
    """Test wait_for_job_with_updates with custom status to wait for."""
    # Job is running
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "data": {
                        "findJob": {
                            "id": "job_123",
                            "status": "READY",
                            "progress": 0.0,
                            "description": "Queued",
                        }
                    }
                },
            )
        ]
    )

    # Set up WebSocket session - wait for RUNNING instead of FINISHED
    respx_stash_client._ws_session = MockWebSocketSession(
        [
            {
                "jobsSubscribe": {
                    "type": "UPDATE",
                    "job": {
                        "id": "job_123",
                        "status": "RUNNING",
                        "subTasks": [],
                        "description": "Started",
                        "progress": 10.0,
                        "addTime": "2024-01-01T00:00:00Z",
                        "error": None,
                    },
                }
            }
        ]
    )

    result = await respx_stash_client.wait_for_job_with_updates(
        "job_123", status=JobStatus.RUNNING
    )

    assert result is True


# =============================================================================
# AsyncIteratorWrapper Tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_async_iterator_wrapper_transforms_values() -> None:
    """Test AsyncIteratorWrapper correctly transforms iterator values."""
    # Create mock iterator
    source = MockAsyncIterator([1, 2, 3, 4, 5])

    # Wrap with doubling transform
    wrapped = AsyncIteratorWrapper(source, lambda x: x * 2)

    # Collect results
    results = [value async for value in wrapped]

    assert results == [2, 4, 6, 8, 10]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_async_iterator_wrapper_with_dict_transform() -> None:
    """Test AsyncIteratorWrapper with dictionary transformation."""
    source = MockAsyncIterator([{"value": 10}, {"value": 20}, {"value": 30}])

    # Extract value field
    wrapped = AsyncIteratorWrapper(source, lambda x: x["value"])

    results = [value async for value in wrapped]

    assert results == [10, 20, 30]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_async_iterator_wrapper_empty_source() -> None:
    """Test AsyncIteratorWrapper with empty source iterator."""
    source = MockAsyncIterator([])
    wrapped = AsyncIteratorWrapper(source, lambda x: x * 2)

    results = [value async for value in wrapped]

    assert results == []
