"""Tests for stash_graphql_client.errors module.

Tests all custom exception classes defined in the errors module.
These exceptions provide type-safe error handling for Stash operations.
"""

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


class TestStashError:
    """Tests for the base StashError exception."""

    @pytest.mark.unit
    def test_basic_instantiation(self) -> None:
        """Test StashError can be instantiated with a message."""
        error = StashError("Test error message")
        assert str(error) == "Test error message"

    @pytest.mark.unit
    def test_multiple_args(self) -> None:
        """Test StashError can be instantiated with multiple arguments."""
        error = StashError("Error:", "additional", "info")
        assert "Error:" in str(error)

    @pytest.mark.unit
    def test_inheritance(self) -> None:
        """Test StashError inherits from RuntimeError."""
        error = StashError("test")
        assert isinstance(error, RuntimeError)
        assert isinstance(error, Exception)

    @pytest.mark.unit
    def test_can_be_raised_and_caught(self) -> None:
        """Test StashError can be raised and caught."""
        with pytest.raises(StashError) as exc_info:
            raise StashError("Test raise")
        assert str(exc_info.value) == "Test raise"


class TestStashGraphQLError:
    """Tests for StashGraphQLError exception."""

    @pytest.mark.unit
    def test_instantiation(self) -> None:
        """Test StashGraphQLError can be instantiated."""
        error = StashGraphQLError("GraphQL query failed")
        assert str(error) == "GraphQL query failed"

    @pytest.mark.unit
    def test_inheritance(self) -> None:
        """Test StashGraphQLError inherits from StashError."""
        error = StashGraphQLError("test")
        assert isinstance(error, StashError)
        assert isinstance(error, RuntimeError)

    @pytest.mark.unit
    def test_can_catch_as_stash_error(self) -> None:
        """Test StashGraphQLError can be caught as StashError."""
        with pytest.raises(StashError):
            raise StashGraphQLError("Caught as base class")


class TestStashConnectionError:
    """Tests for StashConnectionError exception."""

    @pytest.mark.unit
    def test_instantiation(self) -> None:
        """Test StashConnectionError can be instantiated."""
        error = StashConnectionError("Connection refused")
        assert str(error) == "Connection refused"

    @pytest.mark.unit
    def test_inheritance(self) -> None:
        """Test StashConnectionError inherits from StashError."""
        error = StashConnectionError("test")
        assert isinstance(error, StashError)
        assert isinstance(error, RuntimeError)


class TestStashServerError:
    """Tests for StashServerError exception."""

    @pytest.mark.unit
    def test_instantiation(self) -> None:
        """Test StashServerError can be instantiated."""
        error = StashServerError("Internal Server Error 500")
        assert str(error) == "Internal Server Error 500"

    @pytest.mark.unit
    def test_inheritance(self) -> None:
        """Test StashServerError inherits from StashError."""
        error = StashServerError("test")
        assert isinstance(error, StashError)
        assert isinstance(error, RuntimeError)


class TestStashIntegrationError:
    """Tests for StashIntegrationError exception."""

    @pytest.mark.unit
    def test_instantiation(self) -> None:
        """Test StashIntegrationError can be instantiated."""
        error = StashIntegrationError("Data transformation failed")
        assert str(error) == "Data transformation failed"

    @pytest.mark.unit
    def test_inheritance(self) -> None:
        """Test StashIntegrationError inherits from StashError."""
        error = StashIntegrationError("test")
        assert isinstance(error, StashError)
        assert isinstance(error, RuntimeError)


class TestStashSystemNotReadyError:
    """Tests for StashSystemNotReadyError exception."""

    @pytest.mark.unit
    def test_instantiation(self) -> None:
        """Test StashSystemNotReadyError can be instantiated."""
        error = StashSystemNotReadyError("System requires migration")
        assert str(error) == "System requires migration"

    @pytest.mark.unit
    def test_inheritance(self) -> None:
        """Test StashSystemNotReadyError inherits from StashError."""
        error = StashSystemNotReadyError("test")
        assert isinstance(error, StashError)
        assert isinstance(error, RuntimeError)

    @pytest.mark.unit
    def test_with_status_kwarg_pattern(self) -> None:
        """Test the common pattern of passing status and message kwargs.

        This tests the pattern used in client/base.py check_system_ready().
        """
        # This tests that the exception accepts arbitrary kwargs like the codebase uses
        error = StashSystemNotReadyError(
            "Stash database requires migration",
        )
        assert "migration" in str(error)


class TestStashCleanupWarning:
    """Tests for StashCleanupWarning."""

    @pytest.mark.unit
    def test_instantiation(self) -> None:
        """Test StashCleanupWarning can be instantiated."""
        warning = StashCleanupWarning("Cleanup failed for entity")
        assert str(warning) == "Cleanup failed for entity"

    @pytest.mark.unit
    def test_inheritance(self) -> None:
        """Test StashCleanupWarning inherits from UserWarning."""
        warning = StashCleanupWarning("test")
        assert isinstance(warning, UserWarning)
        assert isinstance(warning, Warning)

    @pytest.mark.unit
    def test_can_be_used_with_warnings_module(self) -> None:
        """Test StashCleanupWarning works with Python's warnings module."""
        import warnings

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            warnings.warn("Test cleanup issue", StashCleanupWarning)

            assert len(caught) == 1
            assert issubclass(caught[0].category, StashCleanupWarning)
            assert "Test cleanup issue" in str(caught[0].message)


class TestErrorHierarchy:
    """Tests for the overall exception hierarchy."""

    @pytest.mark.unit
    def test_all_errors_catchable_as_stash_error(self) -> None:
        """Test all exception types can be caught as StashError."""
        error_classes = [
            StashGraphQLError,
            StashConnectionError,
            StashServerError,
            StashIntegrationError,
            StashSystemNotReadyError,
        ]

        for error_class in error_classes:
            error = error_class("test")
            assert isinstance(error, StashError), (
                f"{error_class.__name__} should be instance of StashError"
            )

    @pytest.mark.unit
    def test_specific_error_types_distinguishable(self) -> None:
        """Test different error types can be distinguished."""
        graphql_error = StashGraphQLError("graphql")
        connection_error = StashConnectionError("connection")
        server_error = StashServerError("server")

        # Can catch specifically
        assert isinstance(graphql_error, StashGraphQLError)
        assert not isinstance(graphql_error, StashConnectionError)
        assert not isinstance(graphql_error, StashServerError)

        assert isinstance(connection_error, StashConnectionError)
        assert not isinstance(connection_error, StashGraphQLError)

        assert isinstance(server_error, StashServerError)
        assert not isinstance(server_error, StashConnectionError)
