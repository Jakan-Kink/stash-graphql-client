"""Integration tests for configuration mixin functionality.

Tests configuration operations against a real Stash instance.

NOTE: Most configuration tests are READ-ONLY to avoid modifying the test
Stash instance's configuration. Write tests that do modify configuration
should restore the original values after testing.
"""

import pytest

from stash_graphql_client import StashClient
from stash_graphql_client.types import (
    ConfigDefaultSettingsResult,
    ConfigGeneralResult,
    ConfigInterfaceResult,
)


# =============================================================================
# Read-only configuration tests (safe to run)
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_configuration_defaults(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test getting configuration defaults."""
    async with stash_cleanup_tracker(stash_client, auto_capture=False):
        result = await stash_client.get_configuration_defaults()

        assert result is not None
        assert isinstance(result, ConfigDefaultSettingsResult)
        # Check that basic structure is present
        assert hasattr(result, "deleteFile")
        assert hasattr(result, "deleteGenerated")


# =============================================================================
# Configure General tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_configure_general_read_current(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test configuring general settings by reading and re-applying current config.

    This is safe because we're just re-applying the same settings.
    """
    async with stash_cleanup_tracker(stash_client):
        # First get current config by setting an empty dict (returns current)
        result = await stash_client.configure_general({})

        assert result is not None
        assert isinstance(result, ConfigGeneralResult)
        # Verify key fields are present
        assert result.database_path is not None
        assert result.generated_path is not None
        assert isinstance(result.parallel_tasks, int)


# =============================================================================
# Configure Interface tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_configure_interface_read_current(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test configuring interface settings by reading current config."""
    async with stash_cleanup_tracker(stash_client):
        result = await stash_client.configure_interface({})

        assert result is not None
        assert isinstance(result, ConfigInterfaceResult)
        # Verify key fields are present
        assert result.language is not None
        assert isinstance(result.sound_on_preview, bool)


# =============================================================================
# Configure Defaults tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_configure_defaults_read_current(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test configuring default settings by reading current config."""
    async with stash_cleanup_tracker(stash_client):
        result = await stash_client.configure_defaults({})

        assert result is not None
        assert isinstance(result, ConfigDefaultSettingsResult)
        # Verify key fields are present
        assert hasattr(result, "deleteFile")
        assert hasattr(result, "deleteGenerated")
