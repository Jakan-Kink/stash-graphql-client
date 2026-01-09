"""Integration tests for metadata mixin functionality.

Tests metadata and database operations against a real Stash instance
with GraphQL call verification.

These tests cover SAFE metadata operations NOT already covered by subscription tests:
- metadata_clean_generated (with dryRun=True)
- metadata_auto_tag
- export_objects (read-only)
- backup_database (read-only, creates backup)
- get_configuration_defaults (read-only)

FORBIDDEN operations that must NOT run in integration tests:
- metadata_identify (can trigger external API calls to StashDB)
- metadata_export (writes to metadata directory)
- metadata_import (can overwrite database)

DESTRUCTIVE operations (anonymise, migrate, optimise, setup) are tested
ONLY via unit tests with mocked responses. They must NEVER run against real instances.

NOTE: metadata_scan, metadata_clean, and metadata_generate are tested via
subscription tests (test_subscription_integration.py) as they generate job events.
"""

import pytest

from stash_graphql_client import StashClient
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
