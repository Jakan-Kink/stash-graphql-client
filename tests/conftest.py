"""Master test configuration and fixtures for stash-graphql-client.

This configuration provides essential test infrastructure and imports
organized fixtures from dedicated modules in tests/fixtures/.

Key Principles (from STASH_TEST_MIGRATION_TODO.md):
- NO MagicMock/AsyncMock/Mock for internal methods
- Use respx for HTTP mocking at external boundaries
- Real objects and FactoryBoy factories for all Stash types
- Patch context manager based spies when verifying orchestration

Organization:
- fixtures/stash/type_factories.py - FactoryBoy factories for Stash types
- fixtures/stash/graphql_responses.py - GraphQL response generators
- fixtures/stash/test_objects.py - TestStashObject implementations
"""

import os
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

# Import all fixtures via wildcard
from tests.fixtures import *


# Set testing environment variable
os.environ["TESTING"] = "1"


# =============================================================================
# Core Infrastructure Fixtures
# =============================================================================


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


# =============================================================================
# Pytest Hooks for Test Validation
# =============================================================================


def pytest_collection_modifyitems(config, items):
    """Hook to validate fixture usage and add markers.

    Ensures that any test using Stash fixtures also uses stash_cleanup_tracker
    for proper test isolation and cleanup.

    This enforcement applies to:
    - stash_client: Direct access to StashClient
    - stash_context: StashContext that creates stash_client internally

    Even if a test only does reads, we require the cleanup tracker to:
    1. Be consistent across all integration tests
    2. Ensure cleanup is in place if someone adds writes later
    3. Make the pattern explicit and documented

    Tests that violate this requirement are marked with xfail(strict=True),
    which means:
    - If the test would pass, it fails (enforcement)
    - If the test would fail naturally, it fails (expected)
    - If Stash is unavailable and test skips, it skips (expected)

    EXCEPTIONS:
    - respx_stash_client: Uses respx to mock HTTP, no cleanup needed
    - Tests in tests/types/: Unit tests for data conversion only
    """
    for item in items:
        if hasattr(item, "fixturenames"):
            # Check if test uses any Stash fixture that requires cleanup
            uses_stash_fixture = (
                "stash_client" in item.fixturenames
                or "stash_context" in item.fixturenames
            )

            # Exception: respx fixtures use HTTP mocking, no real Stash calls
            uses_respx = "respx_stash_client" in item.fixturenames

            # Exception: tests/types/ are unit tests for data models
            is_types_test = "tests/types/" in str(item.fspath)

            has_cleanup = "stash_cleanup_tracker" in item.fixturenames

            # Enforce cleanup requirement
            if (
                uses_stash_fixture
                and not uses_respx
                and not is_types_test
                and not has_cleanup
            ):
                item.add_marker(
                    pytest.mark.xfail(
                        reason="Tests using Stash fixtures (stash_client, stash_context) "
                        "MUST also use stash_cleanup_tracker for test isolation and cleanup.",
                        strict=True,
                    )
                )
