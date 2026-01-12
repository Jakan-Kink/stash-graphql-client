"""Tests for validation error paths to achieve 100% coverage.

These tests specifically target the error handling code paths added in dict validation.
"""

import tempfile

import pytest

from stash_graphql_client.errors import StashConfigurationError
from stash_graphql_client.types import ConfigGeneralInput
from stash_graphql_client.types.performer import Performer


# =============================================================================
# Config Path Protection Tests
# =============================================================================


def test_config_general_input_rejects_protected_paths():
    """ConfigGeneralInput should raise StashConfigurationError for protected paths."""
    # Test that trying to set any protected path raises error
    with pytest.raises(StashConfigurationError, match="database_path"):
        ConfigGeneralInput(databasePath="/some/path")

    with pytest.raises(StashConfigurationError, match="ffmpeg_path"):
        ConfigGeneralInput(ffmpegPath="/usr/bin/ffmpeg")

    with pytest.raises(StashConfigurationError, match="generated_path"):
        ConfigGeneralInput(generatedPath="/generated")


def test_stash_configuration_error_instantiation():
    """Test that StashConfigurationError can be instantiated."""
    error = StashConfigurationError("Test error message")
    assert "Test error message" in str(error)
    assert isinstance(error, RuntimeError)


# =============================================================================
# Performer Avatar Validation Tests
# =============================================================================


@pytest.mark.asyncio
async def test_performer_update_avatar_directory_not_file(respx_stash_client):
    """Test Performer.update_avatar() rejects directory paths."""
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        performer = Performer(id="123", name="Test Performer")

        # Pass a directory instead of a file
        with pytest.raises(ValueError, match="Path is not a file"):
            await performer.update_avatar(respx_stash_client, tmpdir)


# =============================================================================
# Client Method TypeError Tests (Non-dict inputs)
# =============================================================================


@pytest.mark.asyncio
async def test_configure_general_rejects_non_dict(respx_stash_client):
    """configure_general should reject non-dict, non-Input inputs."""
    with pytest.raises(TypeError, match="ConfigGeneralInput or dict"):
        await respx_stash_client.configure_general("invalid")  # type: ignore


@pytest.mark.asyncio
async def test_configure_interface_rejects_non_dict(respx_stash_client):
    """configure_interface should reject non-dict, non-Input inputs."""
    with pytest.raises(TypeError, match="ConfigInterfaceInput or dict"):
        await respx_stash_client.configure_interface(123)  # type: ignore


@pytest.mark.asyncio
async def test_configure_dlna_rejects_non_dict(respx_stash_client):
    """configure_dlna should reject non-dict, non-Input inputs."""
    with pytest.raises(TypeError, match="ConfigDLNAInput or dict"):
        await respx_stash_client.configure_dlna([])  # type: ignore


@pytest.mark.asyncio
async def test_configure_defaults_rejects_non_dict(respx_stash_client):
    """configure_defaults should reject non-dict, non-Input inputs."""
    with pytest.raises(TypeError, match="ConfigDefaultSettingsInput or dict"):
        await respx_stash_client.configure_defaults(None)  # type: ignore


@pytest.mark.asyncio
async def test_generate_api_key_rejects_non_dict(respx_stash_client):
    """generate_api_key should reject non-dict, non-Input inputs."""
    with pytest.raises(TypeError, match="GenerateAPIKeyInput or dict"):
        await respx_stash_client.generate_api_key("invalid")  # type: ignore


@pytest.mark.asyncio
async def test_configure_scraping_rejects_non_dict(respx_stash_client):
    """configure_scraping should reject non-dict, non-Input inputs."""
    with pytest.raises(TypeError, match="ConfigScrapingInput or dict"):
        await respx_stash_client.configure_scraping(123)  # type: ignore


@pytest.mark.asyncio
async def test_validate_stashbox_credentials_rejects_non_dict(respx_stash_client):
    """validate_stashbox_credentials should reject non-dict, non-Input inputs."""
    with pytest.raises(TypeError, match="StashBoxInput or dict"):
        await respx_stash_client.validate_stashbox_credentials([])  # type: ignore


@pytest.mark.asyncio
async def test_enable_dlna_rejects_non_dict(respx_stash_client):
    """enable_dlna should reject non-dict, non-Input inputs."""
    with pytest.raises(TypeError, match="EnableDLNAInput or dict"):
        await respx_stash_client.enable_dlna(None)  # type: ignore


@pytest.mark.asyncio
async def test_disable_dlna_rejects_non_dict(respx_stash_client):
    """disable_dlna should reject non-dict, non-Input inputs."""
    with pytest.raises(TypeError, match="DisableDLNAInput or dict"):
        await respx_stash_client.disable_dlna("invalid")  # type: ignore


@pytest.mark.asyncio
async def test_add_temp_dlna_ip_rejects_non_dict(respx_stash_client):
    """add_temp_dlna_ip should reject non-dict, non-Input inputs."""
    with pytest.raises(TypeError, match="AddTempDLNAIPInput or dict"):
        await respx_stash_client.add_temp_dlna_ip(123)  # type: ignore


@pytest.mark.asyncio
async def test_remove_temp_dlna_ip_rejects_non_dict(respx_stash_client):
    """remove_temp_dlna_ip should reject non-dict, non-Input inputs."""
    with pytest.raises(TypeError, match="RemoveTempDLNAIPInput or dict"):
        await respx_stash_client.remove_temp_dlna_ip([])  # type: ignore


@pytest.mark.asyncio
async def test_destroy_saved_filter_rejects_non_dict(respx_stash_client):
    """destroy_saved_filter should reject non-dict, non-Input inputs."""
    with pytest.raises(TypeError, match="DestroyFilterInput or dict"):
        await respx_stash_client.destroy_saved_filter(123)  # type: ignore


@pytest.mark.asyncio
async def test_group_destroy_rejects_non_dict(respx_stash_client):
    """group_destroy should reject non-dict, non-GroupDestroyInput inputs."""
    with pytest.raises(TypeError, match="GroupDestroyInput or dict"):
        await respx_stash_client.group_destroy("invalid")  # type: ignore


@pytest.mark.asyncio
async def test_bulk_group_update_rejects_non_dict(respx_stash_client):
    """bulk_group_update should reject non-dict, non-BulkGroupUpdateInput inputs."""
    with pytest.raises(TypeError, match="BulkGroupUpdateInput or dict"):
        await respx_stash_client.bulk_group_update(123)  # type: ignore


@pytest.mark.asyncio
async def test_add_group_sub_groups_rejects_non_dict(respx_stash_client):
    """add_group_sub_groups should reject non-dict, non-Input inputs."""
    with pytest.raises(TypeError, match="GroupSubGroupAddInput or dict"):
        await respx_stash_client.add_group_sub_groups([])  # type: ignore


@pytest.mark.asyncio
async def test_remove_group_sub_groups_rejects_non_dict(respx_stash_client):
    """remove_group_sub_groups should reject non-dict, non-Input inputs."""
    with pytest.raises(TypeError, match="GroupSubGroupRemoveInput or dict"):
        await respx_stash_client.remove_group_sub_groups(None)  # type: ignore


@pytest.mark.asyncio
async def test_reorder_sub_groups_rejects_non_dict(respx_stash_client):
    """reorder_sub_groups should reject non-dict, non-Input inputs."""
    with pytest.raises(TypeError, match="ReorderSubGroupsInput or dict"):
        await respx_stash_client.reorder_sub_groups("invalid")  # type: ignore


@pytest.mark.asyncio
async def test_metadata_clean_rejects_non_dict(respx_stash_client):
    """metadata_clean should reject non-dict, non-Input inputs."""
    with pytest.raises(TypeError, match="CleanMetadataInput or dict"):
        await respx_stash_client.metadata_clean(123)  # type: ignore


@pytest.mark.asyncio
async def test_metadata_clean_generated_rejects_non_dict(respx_stash_client):
    """metadata_clean_generated should reject non-dict, non-Input inputs."""
    with pytest.raises(TypeError, match="CleanGeneratedInput or dict"):
        await respx_stash_client.metadata_clean_generated([])  # type: ignore


@pytest.mark.asyncio
async def test_metadata_auto_tag_rejects_non_dict(respx_stash_client):
    """metadata_auto_tag should reject non-dict, non-Input inputs."""
    with pytest.raises(TypeError, match="AutoTagMetadataInput or dict"):
        await respx_stash_client.metadata_auto_tag(None)  # type: ignore


@pytest.mark.asyncio
async def test_metadata_identify_rejects_non_dict(respx_stash_client):
    """metadata_identify should reject non-dict, non-Input inputs."""
    with pytest.raises(TypeError, match="IdentifyMetadataInput or dict"):
        await respx_stash_client.metadata_identify("invalid")  # type: ignore


@pytest.mark.asyncio
async def test_export_objects_rejects_non_dict(respx_stash_client):
    """export_objects should reject non-dict, non-Input inputs."""
    with pytest.raises(TypeError, match="ExportObjectsInput or dict"):
        await respx_stash_client.export_objects(123)  # type: ignore


@pytest.mark.asyncio
async def test_import_objects_rejects_non_dict(respx_stash_client):
    """import_objects should reject non-dict, non-Input inputs."""
    with pytest.raises(TypeError, match="ImportObjectsInput or dict"):
        await respx_stash_client.import_objects([])  # type: ignore


@pytest.mark.asyncio
async def test_backup_database_rejects_non_dict(respx_stash_client):
    """backup_database should reject non-dict, non-Input inputs."""
    with pytest.raises(TypeError, match="BackupDatabaseInput or dict"):
        await respx_stash_client.backup_database(None)  # type: ignore


@pytest.mark.asyncio
async def test_anonymise_database_rejects_non_dict(respx_stash_client):
    """anonymise_database should reject non-dict, non-Input inputs."""
    with pytest.raises(TypeError, match="AnonymiseDatabaseInput or dict"):
        await respx_stash_client.anonymise_database("invalid")  # type: ignore


@pytest.mark.asyncio
async def test_migrate_rejects_non_dict(respx_stash_client):
    """migrate should reject non-dict, non-Input inputs."""
    with pytest.raises(TypeError, match="MigrateInput or dict"):
        await respx_stash_client.migrate(123)  # type: ignore


@pytest.mark.asyncio
async def test_migrate_scene_screenshots_rejects_non_dict(respx_stash_client):
    """migrate_scene_screenshots should reject non-dict, non-Input inputs."""
    with pytest.raises(TypeError, match="MigrateSceneScreenshotsInput or dict"):
        await respx_stash_client.migrate_scene_screenshots([])  # type: ignore


@pytest.mark.asyncio
async def test_migrate_blobs_rejects_non_dict(respx_stash_client):
    """migrate_blobs should reject non-dict, non-Input inputs."""
    with pytest.raises(TypeError, match="MigrateBlobsInput or dict"):
        await respx_stash_client.migrate_blobs(None)  # type: ignore


@pytest.mark.asyncio
async def test_setup_rejects_non_dict(respx_stash_client):
    """setup should reject non-dict, non-Input inputs."""
    with pytest.raises(TypeError, match="SetupInput or dict"):
        await respx_stash_client.setup("invalid")  # type: ignore


@pytest.mark.asyncio
async def test_performer_merge_rejects_non_dict(respx_stash_client):
    """performer_merge should reject non-dict, non-Input inputs."""
    with pytest.raises(TypeError, match="PerformerMergeInput or dict"):
        await respx_stash_client.performer_merge(123)  # type: ignore


@pytest.mark.asyncio
async def test_move_files_rejects_non_dict(respx_stash_client):
    """move_files should reject non-dict, non-Input inputs."""
    with pytest.raises(TypeError, match="MoveFilesInput or dict"):
        await respx_stash_client.move_files(123)  # type: ignore


@pytest.mark.asyncio
async def test_file_set_fingerprints_rejects_non_dict(respx_stash_client):
    """file_set_fingerprints should reject non-dict, non-Input inputs."""
    with pytest.raises(TypeError, match="FileSetFingerprintsInput or dict"):
        await respx_stash_client.file_set_fingerprints("invalid")  # type: ignore


@pytest.mark.asyncio
async def test_scene_assign_file_rejects_non_dict(respx_stash_client):
    """scene_assign_file should reject non-dict, non-Input inputs."""
    with pytest.raises(TypeError, match="AssignSceneFileInput or dict"):
        await respx_stash_client.scene_assign_file([])  # type: ignore


@pytest.mark.asyncio
async def test_find_scene_by_hash_rejects_non_dict(respx_stash_client):
    """find_scene_by_hash should reject non-dict, non-Input inputs."""
    with pytest.raises(TypeError, match="SceneHashInput or dict"):
        await respx_stash_client.find_scene_by_hash(123)  # type: ignore


@pytest.mark.asyncio
async def test_submit_stashbox_fingerprints_rejects_non_dict(respx_stash_client):
    """submit_stashbox_fingerprints should reject non-dict, non-Input inputs."""
    with pytest.raises(TypeError, match="StashBoxFingerprintSubmissionInput or dict"):
        await respx_stash_client.submit_stashbox_fingerprints("invalid")  # type: ignore


@pytest.mark.asyncio
async def test_submit_stashbox_scene_draft_rejects_non_dict(respx_stash_client):
    """submit_stashbox_scene_draft should reject non-dict, non-Input inputs."""
    with pytest.raises(TypeError, match="StashBoxDraftSubmissionInput or dict"):
        await respx_stash_client.submit_stashbox_scene_draft(123)  # type: ignore


@pytest.mark.asyncio
async def test_submit_stashbox_performer_draft_rejects_non_dict(respx_stash_client):
    """submit_stashbox_performer_draft should reject non-dict, non-Input inputs."""
    with pytest.raises(TypeError, match="StashBoxDraftSubmissionInput or dict"):
        await respx_stash_client.submit_stashbox_performer_draft([])  # type: ignore
