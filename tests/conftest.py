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
# Integration Test State Validation (xdist-aware)
# =============================================================================

# Global flag to track Stash availability
_stash_available = None
_initial_state = None


async def _capture_stash_state():
    """Async helper to capture Stash state counts."""
    from stash_graphql_client.context import StashContext

    conn = {
        "Scheme": "http",
        "Host": "localhost",
        "Port": 9999,
    }

    context = StashContext(conn=conn, verify_ssl=False)
    client = await context.get_client()

    try:
        # Capture state counts
        scenes_result = await client.find_scenes()
        images_result = await client.find_images()
        galleries_result = await client.find_galleries()
        performers_result = await client.find_performers()
        studios_result = await client.find_studios()
        tags_result = await client.find_tags()

        return {
            "scenes": scenes_result.count,
            "images": images_result.count,
            "galleries": galleries_result.count,
            "performers": performers_result.count,
            "studios": studios_result.count,
            "tags": tags_result.count,
        }
    finally:
        await client.close()
        await context.close()


def pytest_sessionstart(session):
    """Hook called at the start of the test session (runs on controller).

    This captures the initial Stash state before any tests run.
    Unlike session-scoped fixtures, this hook ALWAYS runs on the controller,
    even with xdist workers.
    """
    import asyncio

    global _stash_available, _initial_state

    # Skip if running as xdist worker
    if hasattr(session.config, "workerinput"):
        return

    try:
        # Capture initial state (controller only)
        _initial_state = asyncio.run(_capture_stash_state())
        _stash_available = True

        print(f"\n{'=' * 70}")
        print("STASH STATE VALIDATION: Initial state captured")
        print(f"{'=' * 70}")
        for entity_type, count in _initial_state.items():
            print(f"  {entity_type}: {count}")
        print(f"{'=' * 70}\n")

    except Exception as e:
        # Stash not available - mark as unavailable and skip integration tests
        _stash_available = False
        print(f"\n{'=' * 70}")
        print(
            "STASH STATE VALIDATION: Stash unavailable - integration tests will be skipped"
        )
        print(f"Reason: {e}")
        print(f"{'=' * 70}\n")


@pytest.fixture(scope="session")
def stash_state():
    """Provide access to captured Stash state.

    Returns dict with counts for: scenes, images, galleries, performers, studios, tags
    Returns None if Stash unavailable.
    """
    return _initial_state if _stash_available else None


@pytest.fixture(autouse=True)
def skip_if_no_data(request, stash_state):
    """Auto-skip tests that require specific Stash data types.

    Usage in test files:
        @pytest.mark.requires_scenes
        def test_something():
            ...
    """
    # Skip if Stash not available
    if stash_state is None:
        if (
            request.node.get_closest_marker("requires_scenes")
            or request.node.get_closest_marker("requires_images")
            or request.node.get_closest_marker("requires_galleries")
            or request.node.get_closest_marker("requires_performers")
            or request.node.get_closest_marker("requires_studios")
            or request.node.get_closest_marker("requires_tags")
        ):
            pytest.skip("Stash not available")
        return

    # Check data requirements
    if (
        request.node.get_closest_marker("requires_scenes")
        and stash_state["scenes"] == 0
    ):
        pytest.skip("No scenes in Stash")
    if (
        request.node.get_closest_marker("requires_images")
        and stash_state["images"] == 0
    ):
        pytest.skip("No images in Stash")
    if (
        request.node.get_closest_marker("requires_galleries")
        and stash_state["galleries"] == 0
    ):
        pytest.skip("No galleries in Stash")
    if (
        request.node.get_closest_marker("requires_performers")
        and stash_state["performers"] == 0
    ):
        pytest.skip("No performers in Stash")
    if (
        request.node.get_closest_marker("requires_studios")
        and stash_state["studios"] == 0
    ):
        pytest.skip("No studios in Stash")
    if request.node.get_closest_marker("requires_tags") and stash_state["tags"] == 0:
        pytest.skip("No tags in Stash")


def pytest_sessionfinish(session, exitstatus):
    """Hook called at the end of the test session (runs on controller).

    This validates the final Stash state matches the initial state.
    Unlike session-scoped fixtures, this hook ALWAYS runs on the controller,
    even with xdist workers.
    """
    import asyncio

    # Skip if running as xdist worker
    if hasattr(session.config, "workerinput"):
        return

    # Skip if Stash was never available (read-only access, no global needed)
    if not _stash_available or _initial_state is None:
        return

    try:
        # Capture final state (controller only)
        final_state = asyncio.run(_capture_stash_state())

        print(f"\n{'=' * 70}")
        print("STASH STATE VALIDATION: Final state captured")
        print(f"{'=' * 70}")
        for entity_type, count in final_state.items():
            print(f"  {entity_type}: {count}")
        print(f"{'=' * 70}\n")

        # Compare initial and final states
        divergences = []
        for entity_type in _initial_state:
            initial_count = _initial_state[entity_type]
            final_count = final_state[entity_type]
            if final_count != initial_count:
                delta = final_count - initial_count
                divergences.append(
                    f"  {entity_type}: {initial_count} -> {final_count} "
                    f"({'+' if delta > 0 else ''}{delta})"
                )

        if divergences:
            error_msg = (
                "\n" + "=" * 70 + "\n"
                "STASH STATE VALIDATION FAILED: Environment was modified!\n"
                + "="
                * 70
                + "\n"
                "Tests left artifacts behind:\n"
                + "\n".join(divergences)
                + "\n\nThis indicates tests created objects without cleaning them up.\n"
                "All integration tests MUST use stash_cleanup_tracker fixture.\n"
                + "="
                * 70
            )
            print(error_msg)
            # Don't fail here - just warn (exitstatus already set by tests)
        else:
            print(f"\n{'=' * 70}")
            print("STASH STATE VALIDATION: ✓ Environment unchanged")
            print(f"{'=' * 70}\n")

    except Exception as e:
        print(f"\n{'=' * 70}")
        print(f"STASH STATE VALIDATION: Failed to validate final state: {e}")
        print(f"{'=' * 70}\n")


# =============================================================================
# Pytest Hooks for Test Validation
# =============================================================================


def pytest_runtest_setup(item):
    """Hook that runs before each test to enforce requirements.

    - Skip integration tests if Stash is unavailable
    """
    # Skip integration tests if Stash is unavailable
    if "integration" in item.keywords and _stash_available is False:
        pytest.skip("Skipping integration test - Stash server unavailable")


def pytest_collection_modifyitems(config, items):
    """Hook to validate fixture usage and add markers.

    Future: When stash_client and stash_cleanup_tracker fixtures are added,
    enforce that tests using real Stash clients also use cleanup trackers.
    """
    # Placeholder for future cleanup enforcement
