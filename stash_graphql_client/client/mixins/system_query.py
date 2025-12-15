"""System query client functionality."""

from typing import Any

from ... import fragments
from ...errors import StashSystemNotReadyError
from ...types import (
    Directory,
    DLNAStatus,
    LogEntry,
    SQLExecResult,
    SQLQueryResult,
    StatsResultType,
)
from ...types.enums import SystemStatusEnum
from ...types.metadata import SystemStatus
from ..protocols import StashClientProtocol


class SystemQueryClientMixin(StashClientProtocol):
    """Mixin for system query methods."""

    async def get_system_status(self) -> SystemStatus | None:
        """Get the current Stash system status.

        Returns:
            SystemStatus object containing system information and status
            None if the query fails

        Examples:
            Check system status:
            ```python
            status = await client.get_system_status()
            if status:
                print(f"System status: {status.status}")
                print(f"Database path: {status.databasePath}")
            ```
        """
        try:
            result = await self.execute(fragments.SYSTEM_STATUS_QUERY)
            if status_data := result.get("systemStatus"):
                return SystemStatus(**status_data)
            return None
        except Exception as e:
            self.log.error(f"Failed to get system status: {e}")
            return None

    async def check_system_ready(self) -> None:
        """Check if the Stash system is ready for processing.

        This method queries the system status and raises an exception if the
        system is not in OK status. It should be called before starting any
        processing operations.

        Raises:
            StashSystemNotReadyError: If system status is SETUP or NEEDS_MIGRATION
            RuntimeError: If system status cannot be determined

        Examples:
            Validate system before processing:
            ```python
            try:
                await client.check_system_ready()
                # Safe to proceed with processing
                await client.metadata_scan()
            except StashSystemNotReadyError as e:
                print(f"System not ready: {e}")
                # Handle migration or setup
            ```
        """
        status = await self.get_system_status()

        if status is None:
            raise RuntimeError(
                "Unable to determine Stash system status. "
                "Cannot proceed with processing."
            )

        # Check for blocking states
        if status.status == SystemStatusEnum.NEEDS_MIGRATION:
            raise StashSystemNotReadyError(
                "Stash database requires migration. "
                "Please run the database migration before starting processing. "
                "All processing is blocked until migration is completed."
            )

        if status.status == SystemStatusEnum.SETUP:
            raise StashSystemNotReadyError(
                "Stash requires initial setup. "
                "Please complete the setup wizard before starting processing."
            )

        # System is OK, log status for debugging
        self.log.debug(
            f"Stash system ready - Status: {status.status}, "
            f"Database: {status.databasePath}, "
            f"App Schema: {status.appSchema}"
        )

    async def stats(self) -> StatsResultType:
        """Get system statistics.

        Returns:
            StatsResultType object containing counts and metrics for all entity types

        Examples:
            Get system statistics:
            ```python
            stats = await client.stats()
            print(f"Total scenes: {stats.scene_count}")
            print(f"Total performers: {stats.performer_count}")
            print(f"Total O-count: {stats.total_o_count}")
            print(f"Library size: {stats.scenes_size / (1024**3):.2f} GB")
            ```
        """
        result = await self.execute(fragments.STATS_QUERY)
        return self._decode_result(StatsResultType, result["stats"])

    async def logs(self) -> list[LogEntry]:
        """Get system logs.

        Returns:
            List of LogEntry objects containing log messages with timestamps and levels

        Examples:
            Get recent logs:
            ```python
            logs = await client.logs()
            for log in logs[-10:]:  # Last 10 entries
                print(f"[{log.time}] {log.level}: {log.message}")
            ```

            Filter by level:
            ```python
            from stash_graphql_client.types import LogLevel

            logs = await client.logs()
            errors = [log for log in logs if log.level == LogLevel.ERROR]
            print(f"Found {len(errors)} errors")
            ```
        """
        result = await self.execute(fragments.LOGS_QUERY)
        return [self._decode_result(LogEntry, log) for log in result["logs"]]

    async def dlna_status(self) -> DLNAStatus:
        """Get DLNA server status.

        Returns:
            DLNAStatus object containing DLNA server information
        """
        try:
            result = await self.execute(fragments.DLNA_STATUS_QUERY)
            if status_data := result.get("dlnaStatus"):
                return self._decode_result(DLNAStatus, status_data)
            return DLNAStatus()
        except Exception as e:
            self.log.error(f"Failed to get DLNA status: {e}")
            return DLNAStatus()

    async def directory(self, path: str | None = None, locale: str = "en") -> Directory:
        """Browse filesystem directory.

        Args:
            path: The directory path to list. If None, returns root directories
            locale: Desired collation locale (e.g., 'en-US', 'pt-BR'). Default is 'en'

        Returns:
            Directory object containing path information and subdirectories

        Examples:
            List root directories:
            ```python
            dir_info = await client.directory()
            print(f"Root directories: {dir_info.directories}")
            ```

            Browse specific path:
            ```python
            dir_info = await client.directory(path="/media/videos")
            print(f"Current path: {dir_info.path}")
            print(f"Parent: {dir_info.parent}")
            print(f"Subdirectories: {dir_info.directories}")
            ```

            Use specific locale for sorting:
            ```python
            dir_info = await client.directory(path="/home/user", locale="pt-BR")
            for subdir in dir_info.directories:
                print(subdir)
            ```
        """
        variables = {"path": path, "locale": locale}
        result = await self.execute(fragments.DIRECTORY_QUERY, variables)
        return self._decode_result(Directory, result["directory"])

    async def sql_query(
        self, sql: str, args: list[Any] | None = None
    ) -> SQLQueryResult:
        """Execute a SQL query that returns rows.

        Warning:
            This is a DANGEROUS operation that executes arbitrary SQL against the
            Stash database. Use with extreme caution. Incorrect queries can corrupt
            your database or expose sensitive information.

        Args:
            sql: The SQL query string to execute
            args: Optional list of query parameters to bind to the SQL statement

        Returns:
            SQLQueryResult containing columns and rows from the query result

        Raises:
            Exception: If the query execution fails or SQL support is not available

        Examples:
            Query database for scenes:
            ```python
            result = await client.sql_query(
                "SELECT id, title FROM scenes WHERE rating100 > ?",
                args=[80]
            )
            print(f"Columns: {result.columns}")
            for row in result.rows:
                print(f"Scene ID: {row[0]}, Title: {row[1]}")
            ```

            Count performers by gender:
            ```python
            result = await client.sql_query(
                "SELECT gender, COUNT(*) FROM performers GROUP BY gender"
            )
            for row in result.rows:
                print(f"{row[0]}: {row[1]} performers")
            ```

        Note:
            This feature requires Stash version that supports SQL queries.
            The exact version requirement should be documented in the Stash API.
        """
        variables = {"sql": sql, "args": args or []}
        result = await self.execute(fragments.SQL_QUERY_MUTATION, variables)
        return self._decode_result(SQLQueryResult, result["querySQL"])

    async def sql_exec(self, sql: str, args: list[Any] | None = None) -> SQLExecResult:
        """Execute a SQL statement without returning rows (INSERT, UPDATE, DELETE).

        Warning:
            This is a DANGEROUS operation that executes arbitrary SQL against the
            Stash database. Use with EXTREME caution. Incorrect statements can
            corrupt or destroy your database. Always backup before using this method.

        Args:
            sql: The SQL statement string to execute
            args: Optional list of statement parameters to bind to the SQL

        Returns:
            SQLExecResult containing rows_affected and last_insert_id

        Raises:
            Exception: If the statement execution fails or SQL support is not available

        Examples:
            Update scene ratings:
            ```python
            result = await client.sql_exec(
                "UPDATE scenes SET rating100 = ? WHERE id = ?",
                args=[95, "123"]
            )
            print(f"Rows affected: {result.rows_affected}")
            ```

            Delete orphaned tags (BE CAREFUL!):
            ```python
            result = await client.sql_exec(
                "DELETE FROM tags WHERE id NOT IN (SELECT tag_id FROM scene_tags)"
            )
            print(f"Deleted {result.rows_affected} orphaned tags")
            ```

            Insert custom metadata:
            ```python
            result = await client.sql_exec(
                "INSERT INTO custom_metadata (entity_id, key, value) VALUES (?, ?, ?)",
                args=["scene-123", "custom_field", "custom_value"]
            )
            print(f"Last insert ID: {result.last_insert_id}")
            ```

        Note:
            This feature requires Stash version that supports SQL execution.
            The exact version requirement should be documented in the Stash API.
            ALWAYS test queries in a development environment before production use.
        """
        variables = {"sql": sql, "args": args or []}
        result = await self.execute(fragments.SQL_EXEC_MUTATION, variables)
        return self._decode_result(SQLExecResult, result["execSQL"])
