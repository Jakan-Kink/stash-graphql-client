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

    Future: When stash_client and stash_cleanup_tracker fixtures are added,
    enforce that tests using real Stash clients also use cleanup trackers.
    """
    # Placeholder for future cleanup enforcement
