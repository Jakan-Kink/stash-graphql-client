"""Stash GraphQL Client exceptions.

This module provides exception classes for Stash client operations:
- StashError: Base exception for all Stash-related errors
- StashGraphQLError: GraphQL query/validation errors
- StashConnectionError: Network/connection errors
- StashServerError: Server-side errors (500, 503, etc.)
- StashIntegrationError: Data integration/transformation errors
- StashSystemNotReadyError: System not ready (SETUP/NEEDS_MIGRATION)
"""

from typing import Any


class StashError(RuntimeError):
    """Base exception for Stash-related errors.

    This error is raised when communication with a Stash server fails
    or when Stash API operations encounter errors.
    """

    def __init__(self, *args: Any) -> None:
        super().__init__(*args)


class StashGraphQLError(StashError):
    """Raised when a GraphQL query fails validation or execution.

    This may be caused by:
    - Invalid GraphQL query syntax
    - Querying non-existent fields
    - GraphQL validation errors
    - Query execution errors
    """

    def __init__(self, *args: Any) -> None:
        super().__init__(*args)


class StashConnectionError(StashError):
    """Raised when connection to Stash server fails.

    This may be caused by:
    - Network connectivity issues
    - Invalid Stash URL
    - Stash server not running
    - Authentication failures
    """

    def __init__(self, *args: Any) -> None:
        super().__init__(*args)


class StashServerError(StashError):
    """Raised when Stash server returns an error response.

    This may be caused by:
    - Internal server errors (500)
    - Service unavailable (503)
    - Other server-side issues
    """

    def __init__(self, *args: Any) -> None:
        super().__init__(*args)


class StashIntegrationError(StashError):
    """Raised when data integration or transformation fails.

    This may be caused by:
    - Invalid data format from Stash API
    - Type conversion errors
    - Missing required fields
    - Schema version mismatches
    """

    def __init__(self, *args: Any) -> None:
        super().__init__(*args)


class StashSystemNotReadyError(StashError):
    """Raised when Stash system is not ready for operations.

    This occurs when the system status is:
    - SETUP: Initial setup required
    - NEEDS_MIGRATION: Database migration required
    """

    def __init__(self, *args: Any) -> None:
        super().__init__(*args)


class StashCleanupWarning(UserWarning):
    """Warning emitted when Stash cleanup tracker encounters errors during cleanup."""


__all__ = [
    "StashCleanupWarning",
    "StashConnectionError",
    "StashError",
    "StashGraphQLError",
    "StashIntegrationError",
    "StashServerError",
    "StashSystemNotReadyError",
]
