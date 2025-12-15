"""Tests for stash_graphql_client.errors module."""

import pytest

from stash_graphql_client.errors import (
    StashCleanupWarning,
    StashConnectionError,
    StashError,
    StashGraphQLError,
    StashIntegrationError,
    StashServerError,
    StashSystemNotReadyError,
)


@pytest.mark.unit
def test_stash_error() -> None:
    """Test base StashError can be instantiated."""
    error = StashError("Base error")
    assert str(error) == "Base error"
    assert isinstance(error, RuntimeError)


@pytest.mark.unit
def test_stash_connection_error() -> None:
    """Test StashConnectionError can be instantiated."""
    error = StashConnectionError("Connection failed")
    assert str(error) == "Connection failed"
    assert isinstance(error, StashError)


@pytest.mark.unit
def test_stash_server_error() -> None:
    """Test StashServerError can be instantiated."""
    error = StashServerError("Server error")
    assert str(error) == "Server error"
    assert isinstance(error, StashError)


@pytest.mark.unit
def test_stash_integration_error() -> None:
    """Test StashIntegrationError can be instantiated."""
    error = StashIntegrationError("Integration failed")
    assert str(error) == "Integration failed"
    assert isinstance(error, StashError)


@pytest.mark.unit
def test_stash_graphql_error() -> None:
    """Test StashGraphQLError can be instantiated."""
    error = StashGraphQLError("GraphQL query failed")
    assert str(error) == "GraphQL query failed"
    assert isinstance(error, StashError)


@pytest.mark.unit
def test_stash_system_not_ready_error() -> None:
    """Test StashSystemNotReadyError can be instantiated.

    This covers line 90 in errors.py - the super().__init__() call.
    """
    error = StashSystemNotReadyError("System setup required")
    assert str(error) == "System setup required"
    assert isinstance(error, StashError)

    # Test with multiple args
    error_multi = StashSystemNotReadyError("System not ready", "SETUP")
    assert "System not ready" in str(error_multi)
    assert isinstance(error_multi, StashError)


@pytest.mark.unit
def test_stash_cleanup_warning() -> None:
    """Test StashCleanupWarning can be instantiated."""
    warning = StashCleanupWarning("Cleanup failed for some objects")
    assert str(warning) == "Cleanup failed for some objects"
    assert isinstance(warning, UserWarning)


@pytest.mark.unit
def test_error_inheritance() -> None:
    """Test that all custom errors inherit from StashError/Exception."""
    assert issubclass(StashError, RuntimeError)
    assert issubclass(StashConnectionError, StashError)
    assert issubclass(StashServerError, StashError)
    assert issubclass(StashIntegrationError, StashError)
    assert issubclass(StashGraphQLError, StashError)
    assert issubclass(StashSystemNotReadyError, StashError)
    assert issubclass(StashCleanupWarning, UserWarning)
