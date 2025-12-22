"""Integration tests for configuration mixin functionality.

Tests configuration operations against a real Stash instance.

IMPORTANT: Configuration MUTATIONS have been removed from integration tests.
All configure_* methods (configure_general, configure_interface, configure_defaults)
call GraphQL MUTATIONS that can modify Stash settings. Even passing empty dicts {}
relies on undocumented Stash API behavior and is unsafe.

These operations are tested via unit tests with mocked responses in:
  - tests/client/test_config_client.py

The only safe configuration operation for integration tests is reading configuration
defaults, which is a read-only query.
"""

import pytest

from stash_graphql_client import StashClient
from stash_graphql_client.types import ConfigDefaultSettingsResult
from tests.fixtures import capture_graphql_calls


# =============================================================================
# Read-only configuration tests (safe to run)
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_configuration_defaults(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test getting configuration defaults (read-only query)."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        result = await stash_client.get_configuration_defaults()

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for get_configuration_defaults"
        assert "configuration" in calls[0]["query"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify response
        assert result is not None
        assert isinstance(result, ConfigDefaultSettingsResult)
        # Check that basic structure is present
        assert hasattr(result, "delete_file")
        assert hasattr(result, "delete_generated")


# =============================================================================
# UNSAFE CONFIGURATION MUTATIONS - REMOVED
# =============================================================================
# The following operations are UNSAFE mutations that modify Stash configuration
# and have been removed from integration tests:
#
# ❌ configure_general: Modifies general settings (database path, generated path, etc.)
# ❌ configure_interface: Modifies UI settings (language, theme, etc.)
# ❌ configure_defaults: Modifies default operation settings
#
# These operations are tested in:
#   - tests/client/test_config_client.py (with mocked GraphQL responses)
#
# CRITICAL: These methods call MUTATIONS, not queries. Even passing empty dicts {}
# relies on undocumented Stash GraphQL API behavior. If Stash changes how it handles
# empty config inputs, these tests could modify production configuration.
# =============================================================================
