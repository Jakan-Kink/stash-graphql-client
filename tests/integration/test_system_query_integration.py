"""Integration tests for system query mixin functionality.

Tests system-level read-only operations against a real Stash instance.

NOTE: These tests verify GraphQL calls and response structures for all system
query operations. System queries are read-only and safe to run.
"""

import pytest

from stash_graphql_client import StashClient
from stash_graphql_client.types import (
    Directory,
    DLNAStatus,
    LogEntry,
    LogLevel,
    SQLExecResult,
    SQLQueryResult,
    StatsResultType,
    SystemStatus,
)
from tests.fixtures import capture_graphql_calls


# =============================================================================
# System Status Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_system_status(
    stash_client: StashClient,
) -> None:
    """Test getting the Stash system status."""
    async with capture_graphql_calls(stash_client) as calls:
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
        assert status.appSchema is not None
        assert isinstance(status.appSchema, int)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_check_system_ready_when_ok(
    stash_client: StashClient,
) -> None:
    """Test check_system_ready when system is in OK status."""
    async with capture_graphql_calls(stash_client) as calls:
        # This should not raise an exception when system is OK
        await stash_client.check_system_ready()

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for check_system_ready"
        assert "systemStatus" in calls[0]["query"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None


# =============================================================================
# Statistics Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_stats(stash_client: StashClient) -> None:
    """Test getting system statistics."""
    async with capture_graphql_calls(stash_client) as calls:
        stats = await stash_client.stats()

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for stats"
        assert "stats" in calls[0]["query"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify response
        assert isinstance(stats, StatsResultType)
        assert hasattr(stats, "scene_count")
        assert hasattr(stats, "performer_count")
        assert hasattr(stats, "studio_count")
        assert hasattr(stats, "tag_count")
        assert hasattr(stats, "gallery_count")
        assert hasattr(stats, "image_count")
        assert hasattr(stats, "group_count")
        # All counts should be integers
        assert isinstance(stats.scene_count, int) or stats.scene_count is None
        assert isinstance(stats.performer_count, int) or stats.performer_count is None


# =============================================================================
# Logging Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_logs(stash_client: StashClient) -> None:
    """Test retrieving system logs."""
    async with capture_graphql_calls(stash_client) as calls:
        logs = await stash_client.logs()

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for logs"
        assert "logs" in calls[0]["query"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify response
        assert isinstance(logs, list)
        # Logs list may be empty or have entries
        if logs:
            for log in logs:
                assert isinstance(log, LogEntry)
                assert hasattr(log, "time")
                assert hasattr(log, "level")
                assert hasattr(log, "message")
                # Level should be a valid LogLevel enum value if present
                if log.level is not None:
                    assert isinstance(log.level, LogLevel)


# =============================================================================
# DLNA Status Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_dlna_status(stash_client: StashClient) -> None:
    """Test getting DLNA server status."""
    async with capture_graphql_calls(stash_client) as calls:
        dlna_status = await stash_client.dlna_status()

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for dlna_status"
        assert "dlnaStatus" in calls[0]["query"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify response
        assert isinstance(dlna_status, DLNAStatus)
        assert hasattr(dlna_status, "running")
        assert isinstance(dlna_status.running, bool)
        # May have optional fields
        if dlna_status.recent_ip_addresses is not None:
            assert isinstance(dlna_status.recent_ip_addresses, list)
        if dlna_status.allowed_ip_addresses is not None:
            assert isinstance(dlna_status.allowed_ip_addresses, list)


# =============================================================================
# Directory Browsing Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_directory_root(stash_client: StashClient) -> None:
    """Test browsing root directories."""
    async with capture_graphql_calls(stash_client) as calls:
        dir_info = await stash_client.directory()

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for directory root"
        assert "directory" in calls[0]["query"]
        assert calls[0]["variables"]["path"] is None
        assert calls[0]["variables"]["locale"] == "en"
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify response
        assert isinstance(dir_info, Directory)
        assert hasattr(dir_info, "path")
        assert hasattr(dir_info, "parent")
        assert hasattr(dir_info, "directories")
        assert isinstance(dir_info.directories, list)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_directory_with_locale(
    stash_client: StashClient,
) -> None:
    """Test directory browsing with custom locale."""
    async with capture_graphql_calls(stash_client) as calls:
        dir_info = await stash_client.directory(locale="pt-BR")

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for directory with locale"
        assert "directory" in calls[0]["query"]
        assert calls[0]["variables"]["locale"] == "pt-BR"
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify response
        assert isinstance(dir_info, Directory)
        assert isinstance(dir_info.directories, list)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_directory_with_path(
    stash_client: StashClient,
) -> None:
    """Test directory browsing with specific path."""
    async with capture_graphql_calls(stash_client) as calls:
        # Try to browse a common path
        dir_info = await stash_client.directory(path="/")

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for directory with path"
        assert "directory" in calls[0]["query"]
        assert calls[0]["variables"]["path"] == "/"
        assert calls[0]["variables"]["locale"] == "en"
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify response
        assert isinstance(dir_info, Directory)
        assert dir_info.path == "/"


# =============================================================================
# SQL Query Tests (Read-only)
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_sql_query_simple_select(
    stash_client: StashClient,
) -> None:
    """Test executing a simple SQL SELECT query."""
    async with capture_graphql_calls(stash_client) as calls:
        # Simple query to get count of scenes (read-only)
        result = await stash_client.sql_query("SELECT COUNT(*) as count FROM scenes")

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for sql_query"
        assert "querySQL" in calls[0]["query"]
        assert calls[0]["variables"]["sql"] == "SELECT COUNT(*) as count FROM scenes"
        assert calls[0]["variables"]["args"] == []
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify response
        assert isinstance(result, SQLQueryResult)
        assert hasattr(result, "columns")
        assert hasattr(result, "rows")
        assert isinstance(result.columns, list)
        assert isinstance(result.rows, list)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_sql_query_with_args(
    stash_client: StashClient,
) -> None:
    """Test SQL query with parameter arguments."""
    async with capture_graphql_calls(stash_client) as calls:
        # Query with parameters
        result = await stash_client.sql_query(
            "SELECT id FROM scenes WHERE rating > ?", args=[80]
        )

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for sql_query with args"
        assert "querySQL" in calls[0]["query"]
        assert calls[0]["variables"]["sql"] == "SELECT id FROM scenes WHERE rating > ?"
        assert calls[0]["variables"]["args"] == [80]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify response
        assert isinstance(result, SQLQueryResult)
        assert isinstance(result.columns, list)
        assert isinstance(result.rows, list)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_sql_query_with_multiple_args(
    stash_client: StashClient,
) -> None:
    """Test SQL query with multiple parameter arguments."""
    async with capture_graphql_calls(stash_client) as calls:
        # Query with multiple parameters
        result = await stash_client.sql_query(
            "SELECT id, title FROM scenes WHERE rating > ? AND created_at > ?",
            args=[70, "2023-01-01"],
        )

        # Verify GraphQL call
        assert len(calls) == 1, (
            "Expected 1 GraphQL call for sql_query with multiple args"
        )
        assert "querySQL" in calls[0]["query"]
        assert (
            calls[0]["variables"]["sql"]
            == "SELECT id, title FROM scenes WHERE rating > ? AND created_at > ?"
        )
        assert calls[0]["variables"]["args"] == [70, "2023-01-01"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify response
        assert isinstance(result, SQLQueryResult)
        assert isinstance(result.columns, list)
        assert isinstance(result.rows, list)


# =============================================================================
# SQL Execution Tests (Write operations - read-only test patterns)
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_sql_exec_count_affected_rows(
    stash_client: StashClient,
) -> None:
    """Test SQL exec returns proper result structure with affected rows count.

    NOTE: This test executes a no-op UPDATE to verify the response structure
    without actually modifying data.
    """
    async with capture_graphql_calls(stash_client) as calls:
        # Execute a no-op UPDATE (WHERE condition false) to verify response structure
        result = await stash_client.sql_exec(
            "UPDATE scenes SET created_at = created_at WHERE id = ?",
            args=["nonexistent-id"],
        )

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for sql_exec"
        assert "execSQL" in calls[0]["query"]
        assert (
            calls[0]["variables"]["sql"]
            == "UPDATE scenes SET created_at = created_at WHERE id = ?"
        )
        assert calls[0]["variables"]["args"] == ["nonexistent-id"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify response structure
        assert isinstance(result, SQLExecResult)
        assert hasattr(result, "rows_affected")
        assert isinstance(result.rows_affected, int)
        # Should be 0 since WHERE condition is false
        assert result.rows_affected == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_sql_exec_with_no_args(
    stash_client: StashClient,
) -> None:
    """Test SQL exec without arguments."""
    async with capture_graphql_calls(stash_client) as calls:
        # Execute a no-op query to verify structure
        result = await stash_client.sql_exec(
            "UPDATE scenes SET created_at = created_at WHERE 0"
        )

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for sql_exec without args"
        assert "execSQL" in calls[0]["query"]
        assert calls[0]["variables"]["args"] == []
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify response
        assert isinstance(result, SQLExecResult)
        assert isinstance(result.rows_affected, int)
        assert result.rows_affected == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_sql_exec_last_insert_id(
    stash_client: StashClient,
) -> None:
    """Test SQL exec result includes last_insert_id field."""
    async with capture_graphql_calls(stash_client) as calls:
        # Execute a query that won't insert but will return last_insert_id
        result = await stash_client.sql_exec(
            "UPDATE scenes SET created_at = created_at WHERE 0"
        )

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for sql_exec"
        assert "execSQL" in calls[0]["query"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify response has both fields
        assert isinstance(result, SQLExecResult)
        assert hasattr(result, "rows_affected")
        assert hasattr(result, "last_insert_id")
        assert isinstance(result.rows_affected, int)
        # last_insert_id may be int or None
        if result.last_insert_id is not None:
            assert isinstance(result.last_insert_id, int)
