"""Mixin for operations that are intentionally not implemented.

This mixin contains stub methods for GraphQL operations that are either:
1. Security risks (direct SQL access)
2. Not yet prioritized for implementation (DLNA, StashBox validation)

Due to Python's Method Resolution Order (MRO), this mixin is placed LAST
in the StashClient inheritance chain, so any real implementations in other
mixins will automatically override these stubs.

IMPORTANT: If you implement any of these methods in another mixin, you should
remove the corresponding stub from this file to avoid confusion.
"""

from typing import Any

from ...types import (
    DLNAStatus,
    SQLExecResult,
    SQLQueryResult,
    StashBoxValidationResult,
)


class NotImplementedClientMixin:
    """Mixin containing stubs for unimplemented GraphQL operations.

    This class serves as:
    - Documentation of which operations exist in the schema but aren't implemented
    - Type hints for IDE autocomplete
    - Clear error messages when calling unimplemented operations

    All methods here raise NotImplementedError when called.
    """

    # =========================================================================
    # SQL Operations - INTENTIONALLY NOT IMPLEMENTED (Security Risk)
    # =========================================================================
    # Direct SQL access poses significant security risks:
    # - SQL injection vulnerabilities
    # - Potential for data corruption
    # - Bypasses application-level validation and business logic
    # - Could expose sensitive data
    #
    # Users requiring SQL access should use Stash's UI or direct database tools.

    async def querySQL(self, sql: str, args: list[Any] | None = None) -> SQLQueryResult:
        """Execute SQL query.

        SECURITY: This operation is intentionally not implemented to prevent
        SQL injection vulnerabilities and unauthorized database access.

        Args:
            sql: SQL query string
            args: Optional query arguments

        Raises:
            NotImplementedError: Always raised (security measure)
        """
        raise NotImplementedError(
            "SQL queries are not implemented for security reasons. "
            "Use Stash's UI or direct database tools for SQL access."
        )

    async def execSQL(self, sql: str, args: list[Any] | None = None) -> SQLExecResult:
        """Execute SQL statement.

        SECURITY: This operation is intentionally not implemented to prevent
        SQL injection vulnerabilities and unauthorized database modifications.

        Args:
            sql: SQL statement string
            args: Optional statement arguments

        Raises:
            NotImplementedError: Always raised (security measure)
        """
        raise NotImplementedError(
            "SQL execution is not implemented for security reasons. "
            "Use Stash's UI or direct database tools for SQL access."
        )

    # =========================================================================
    # StashBox Operations - Not Yet Implemented
    # =========================================================================

    async def validateStashBoxCredentials(
        self, input_data: dict[str, Any]
    ) -> StashBoxValidationResult:
        """Validate StashBox instance credentials.

        Tests whether the provided StashBox credentials are valid.

        Args:
            input_data: Dictionary containing StashBox endpoint and API key

        Returns:
            StashBoxValidationResult with validation status

        Raises:
            NotImplementedError: Not yet implemented
        """
        raise NotImplementedError(
            "StashBox credential validation is not yet implemented. "
            "Please validate credentials through Stash's UI."
        )

    # =========================================================================
    # DLNA Operations - Not Yet Implemented
    # =========================================================================

    async def dlnaStatus(self) -> DLNAStatus:
        """Get DLNA server status.

        Returns information about the DLNA server state, including
        whether it's running and what IPs are whitelisted.

        Returns:
            DLNAStatus with server information

        Raises:
            NotImplementedError: Not yet implemented
        """
        raise NotImplementedError(
            "DLNA status query is not yet implemented. "
            "Please check DLNA status through Stash's UI."
        )
