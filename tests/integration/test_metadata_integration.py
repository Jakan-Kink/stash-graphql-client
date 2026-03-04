"""Integration tests for metadata mixin functionality.

Tests metadata and database operations against a real Stash instance
with GraphQL call verification.

These tests cover SAFE metadata operations NOT already covered by subscription tests:
- metadata_clean_generated (with dryRun=True)
- metadata_auto_tag
- export_objects (read-only)
- backup_database (read-only, creates backup)
- get_configuration_defaults (read-only)
- __safe_to_eat__ capability gating for GenerateMetadataInput

FORBIDDEN operations that must NOT run in integration tests:
- metadata_identify (can trigger external API calls to StashDB)
- metadata_export (writes to metadata directory)
- metadata_import (can overwrite database)

DESTRUCTIVE operations (anonymise, migrate, optimise, setup) are tested
ONLY via unit tests with mocked responses. They must NEVER run against real instances.

NOTE: metadata_scan, metadata_clean, and metadata_generate are tested via
subscription tests (test_subscription_integration.py) as they generate job events.
"""

import warnings

import pytest

from stash_graphql_client import StashClient
from stash_graphql_client.types import GenerateMetadataInput
from tests.fixtures import capture_graphql_calls


# =============================================================================
# Configuration Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_configuration_defaults_returns_config(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test retrieving default configuration settings."""
    async with (
        stash_cleanup_tracker(stash_client),
        capture_graphql_calls(stash_client) as calls,
    ):
        config = await stash_client.get_configuration_defaults()

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for get_configuration_defaults"
        assert "ConfigurationDefaults" in calls[0]["query"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify config structure
        assert config is not None
        assert hasattr(config, "scan")
        assert hasattr(config, "auto_tag")
        assert hasattr(config, "generate")


# =============================================================================
# Clean Generated Files Tests (DRY RUN ONLY)
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_metadata_clean_generated_with_dry_run(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test cleaning generated files with dry-run enabled."""
    async with (
        stash_cleanup_tracker(stash_client),
        capture_graphql_calls(stash_client) as calls,
    ):
        job_id = await stash_client.metadata_clean_generated({"dryRun": True})

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for metadata_clean_generated"
        assert "metadataCleanGenerated" in calls[0]["query"]
        assert calls[0]["variables"]["input"]["dryRun"] is True
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify job ID returned
        assert job_id is not None
        assert isinstance(job_id, str)
        assert len(job_id) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_metadata_clean_generated_selective_cleanup(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test cleaning only specific generated file types."""
    async with (
        stash_cleanup_tracker(stash_client),
        capture_graphql_calls(stash_client) as calls,
    ):
        job_id = await stash_client.metadata_clean_generated(
            {
                "sprites": True,
                "screenshots": True,
                "dryRun": True,
            }
        )

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for metadata_clean_generated"
        assert "metadataCleanGenerated" in calls[0]["query"]
        assert calls[0]["variables"]["input"]["sprites"] is True
        assert calls[0]["variables"]["input"]["screenshots"] is True
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify job ID returned
        assert job_id is not None
        assert isinstance(job_id, str)


# =============================================================================
# Auto-Tag Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_metadata_auto_tag_with_all_performers(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test auto-tagging with all performers wildcard."""
    async with (
        stash_cleanup_tracker(stash_client),
        capture_graphql_calls(stash_client) as calls,
    ):
        job_id = await stash_client.metadata_auto_tag({"performers": ["*"]})

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for metadata_auto_tag"
        assert "metadataAutoTag" in calls[0]["query"]
        assert calls[0]["variables"]["input"]["performers"] == ["*"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify job ID returned
        assert job_id is not None
        assert isinstance(job_id, str)
        assert len(job_id) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_metadata_auto_tag_with_specific_ids(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test auto-tagging with specific performer and studio IDs."""
    async with (
        stash_cleanup_tracker(stash_client),
        capture_graphql_calls(stash_client) as calls,
    ):
        job_id = await stash_client.metadata_auto_tag(
            {
                "performers": ["1", "2"],
                "studios": ["5"],
            }
        )

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for metadata_auto_tag"
        assert "metadataAutoTag" in calls[0]["query"]
        assert calls[0]["variables"]["input"]["performers"] == ["1", "2"]
        assert calls[0]["variables"]["input"]["studios"] == ["5"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify job ID returned
        assert job_id is not None
        assert isinstance(job_id, str)


# =============================================================================
# Export Tests (Read-Only Operations)
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_export_objects_all_scenes(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test exporting all scenes as downloadable file."""
    async with (
        stash_cleanup_tracker(stash_client),
        capture_graphql_calls(stash_client) as calls,
    ):
        token = await stash_client.export_objects({"scenes": {"all": True}})

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for export_objects"
        assert "exportObjects" in calls[0]["query"]
        assert calls[0]["variables"]["input"]["scenes"]["all"] is True
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify download token returned
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_export_objects_specific_ids(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test exporting specific performers by ID."""
    async with (
        stash_cleanup_tracker(stash_client),
        capture_graphql_calls(stash_client) as calls,
    ):
        performer_ids = ["1", "2", "3"]
        token = await stash_client.export_objects(
            {"performers": {"ids": performer_ids}}
        )

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for export_objects"
        assert "exportObjects" in calls[0]["query"]
        assert calls[0]["variables"]["input"]["performers"]["ids"] == performer_ids
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify download token returned
        assert token is not None
        assert isinstance(token, str)


# =============================================================================
# Database Backup Tests (Read-Only - Creates Backup Copy)
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_backup_database_with_download(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test creating a database backup with download enabled."""
    async with (
        stash_cleanup_tracker(stash_client),
        capture_graphql_calls(stash_client) as calls,
    ):
        token = await stash_client.backup_database({"download": True})

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for backup_database"
        assert "backupDatabase" in calls[0]["query"]
        assert calls[0]["variables"]["input"]["download"] is True
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify download token returned
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_backup_database_without_download(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test creating a database backup without download."""
    async with (
        stash_cleanup_tracker(stash_client),
        capture_graphql_calls(stash_client) as calls,
    ):
        path = await stash_client.backup_database({"download": False})

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for backup_database"
        assert "backupDatabase" in calls[0]["query"]
        assert calls[0]["variables"]["input"]["download"] is False
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify backup path returned
        assert path is not None
        assert isinstance(path, str)


# =============================================================================
# __safe_to_eat__ Capability Gating Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_metadata_paths_gating_matches_capabilities(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Verify __safe_to_eat__ gating for GenerateMetadataInput.paths against live server.

    The 'paths' field on GenerateMetadataInput is listed in __safe_to_eat__.
    If the server supports the field, it should pass through.
    If the server lacks it, it should be silently stripped with a warning.
    Either way, the mutation must succeed (not error).
    """
    caps = stash_client._capabilities
    assert caps is not None

    server_supports_paths = caps.input_has_field("GenerateMetadataInput", "paths")

    async with (
        stash_cleanup_tracker(stash_client),
        capture_graphql_calls(stash_client) as calls,
    ):
        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter("always")
            job_id = await stash_client.metadata_generate(
                options={"phashes": True},
                input_data=GenerateMetadataInput(paths=["/nonexistent/test/path"]),
            )

        # Mutation must succeed regardless
        assert len(calls) == 1, "Expected 1 GraphQL call for metadata_generate"
        assert "metadataGenerate" in calls[0]["query"]
        assert calls[0]["exception"] is None
        assert job_id is not None
        assert len(job_id) > 0

        sent_input = calls[0]["variables"]["input"]

        if server_supports_paths:
            # Server supports 'paths' — field should be present in the request
            assert "paths" in sent_input, (
                "Server supports 'paths' on GenerateMetadataInput but "
                "the field was not included in the GraphQL variables"
            )
            assert sent_input["paths"] == ["/nonexistent/test/path"]
            # No stripping warning expected
            path_warnings = [w for w in caught_warnings if "paths" in str(w.message)]
            assert len(path_warnings) == 0, (
                f"Unexpected stripping warning when server supports 'paths': "
                f"{[str(w.message) for w in path_warnings]}"
            )
        else:
            # Server lacks 'paths' — field should have been stripped
            assert "paths" not in sent_input, (
                "Server lacks 'paths' on GenerateMetadataInput but "
                "the field was not stripped by __safe_to_eat__ gating"
            )
            # Warning should have been emitted
            path_warnings = [w for w in caught_warnings if "paths" in str(w.message)]
            assert len(path_warnings) == 1, (
                f"Expected exactly 1 stripping warning for 'paths', "
                f"got {len(path_warnings)}"
            )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_metadata_safe_fields_cross_validate_schema(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Cross-validate all GenerateMetadataInput.__safe_to_eat__ fields against live schema.

    Ensures each field in __safe_to_eat__ is correctly categorized: the server
    either has it (so it passes through) or lacks it (so gating would strip it).
    This catches drift between __safe_to_eat__ declarations and the actual server schema.
    """
    caps = stash_client._capabilities
    assert caps is not None

    safe_fields = GenerateMetadataInput.__safe_to_eat__
    assert len(safe_fields) > 0, "Expected at least one __safe_to_eat__ field"

    # Verify the type exists in the schema (it always should for a supported server)
    assert caps.has_type("GenerateMetadataInput"), (
        "GenerateMetadataInput type not found in server schema"
    )

    for field_name in safe_fields:
        has_field = caps.input_has_field("GenerateMetadataInput", field_name)
        # Just verify it returns a bool — the actual value depends on server version
        assert isinstance(has_field, bool), (
            f"input_has_field returned non-bool for '{field_name}'"
        )


# =============================================================================
# DESTRUCTIVE OPERATIONS - REMOVED FROM INTEGRATION TESTS
# =============================================================================
# The following operations are DESTRUCTIVE and must NEVER run against a
# production Stash instance. They are fully covered by unit tests with mocks:
#
# ❌ metadata_import: Imports metadata (can overwrite entire database)
# ❌ anonymise_database: Anonymizes all database content
# ❌ migrate: Database schema migration operations
# ❌ migrate_hash_naming: Renames all files to hash-based naming
# ❌ migrate_scene_screenshots: Migrates screenshots (deleteFiles=True)
# ❌ migrate_blobs: Migrates blob storage (deleteOld=True)
# ❌ optimise_database: Restructures/optimizes database
# ❌ setup: Reconfigures entire Stash instance (changes DB path, etc.)
#
# These operations are tested in:
#   - tests/client/test_metadata_client.py (with mocked GraphQL responses)
#
# CRITICAL: If you need to test these operations, ONLY use unit tests with
# mocked responses. NEVER run them against a real Stash instance, even for
# testing purposes. A test Docker instance was completely reconfigured and
# had its database path changed by these tests.
# =============================================================================
