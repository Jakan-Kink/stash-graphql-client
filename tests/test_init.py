"""Tests for stash_graphql_client.__init__ module.

Tests package initialization, version handling, and public API exports.
"""

from unittest.mock import patch

import pytest


class TestVersionHandling:
    """Test __version__ attribute and fallback behavior."""

    @pytest.mark.unit
    def test_version_is_string(self) -> None:
        """Test that __version__ is a string."""
        import stash_graphql_client

        assert isinstance(stash_graphql_client.__version__, str)
        assert len(stash_graphql_client.__version__) > 0

    @pytest.mark.unit
    def test_version_format(self) -> None:
        """Test that __version__ follows semantic versioning format."""
        import stash_graphql_client

        # Should be either X.Y.Z or X.Y.Z.devN (or similar dev version)
        version = stash_graphql_client.__version__
        assert "." in version  # At least one dot

    @pytest.mark.unit
    def test_version_fallback_on_package_not_found(self) -> None:
        """Test that __version__ falls back to 0.0.0.dev0 when package not installed.

        This tests lines 72-74 in __init__.py - the PackageNotFoundError handler.
        """
        import sys
        from importlib.metadata import PackageNotFoundError

        # Remove the module from cache to force fresh import
        if "stash_graphql_client" in sys.modules:
            del sys.modules["stash_graphql_client"]

        # Mock the version() function at import time
        with patch(
            "importlib.metadata.version",
            side_effect=PackageNotFoundError("stash-graphql-client"),
        ):
            # Import with mocked version - should trigger fallback
            import stash_graphql_client

            # Should have fallback version
            assert stash_graphql_client.__version__ == "0.0.0.dev0"

            # Clean up - remove from cache again
            del sys.modules["stash_graphql_client"]

        # Re-import normally to restore for other tests
        import stash_graphql_client

        # Verify module is back in normal state
        assert stash_graphql_client.__version__ != "0.0.0.dev0"


class TestPublicAPI:
    """Test that public API exports are available."""

    @pytest.mark.unit
    def test_client_exports(self) -> None:
        """Test that StashClient and StashContext are exported."""
        from stash_graphql_client import StashClient, StashContext

        assert StashClient is not None
        assert StashContext is not None

    @pytest.mark.unit
    def test_store_exports(self) -> None:
        """Test that StashEntityStore and CacheEntry are exported."""
        from stash_graphql_client import CacheEntry, StashEntityStore

        assert StashEntityStore is not None
        assert CacheEntry is not None

    @pytest.mark.unit
    def test_logging_exports(self) -> None:
        """Test that logging utilities are exported."""
        from stash_graphql_client import (
            client_logger,
            configure_logging,
            processing_logger,
            stash_logger,
        )

        assert stash_logger is not None
        assert client_logger is not None
        assert processing_logger is not None
        assert configure_logging is not None

    @pytest.mark.unit
    def test_type_exports(self) -> None:
        """Test that common types are exported."""
        from stash_graphql_client import (
            Gallery,
            Image,
            Performer,
            Scene,
            Studio,
            Tag,
        )

        assert Gallery is not None
        assert Image is not None
        assert Performer is not None
        assert Scene is not None
        assert Studio is not None
        assert Tag is not None

    @pytest.mark.unit
    def test_input_type_exports(self) -> None:
        """Test that input types are exported."""
        from stash_graphql_client import (
            GalleryCreateInput,
            PerformerCreateInput,
            SceneCreateInput,
            StudioCreateInput,
            TagCreateInput,
        )

        assert GalleryCreateInput is not None
        assert PerformerCreateInput is not None
        assert SceneCreateInput is not None
        assert StudioCreateInput is not None
        assert TagCreateInput is not None

    @pytest.mark.unit
    def test_all_attribute_exists(self) -> None:
        """Test that __all__ attribute exists and contains expected exports."""
        import stash_graphql_client

        assert hasattr(stash_graphql_client, "__all__")
        assert isinstance(stash_graphql_client.__all__, list)
        assert len(stash_graphql_client.__all__) > 0

        # Verify key exports are in __all__
        assert "StashClient" in stash_graphql_client.__all__
        assert "StashContext" in stash_graphql_client.__all__
        assert "StashEntityStore" in stash_graphql_client.__all__
        assert "__version__" in stash_graphql_client.__all__
