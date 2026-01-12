"""Unit tests for MetadataClientMixin.

These tests mock at the HTTP boundary using respx, allowing real code execution
through the entire GraphQL client stack including serialization/deserialization.
"""

import json

import httpx
import pytest
import respx

from stash_graphql_client import StashClient
from stash_graphql_client.errors import StashGraphQLError
from stash_graphql_client.types import (
    AnonymiseDatabaseInput,
    AutoTagMetadataInput,
    BackupDatabaseInput,
    CleanGeneratedInput,
    CleanMetadataInput,
    ExportObjectsInput,
    ExportObjectTypeInput,
    IdentifyMetadataInput,
    IdentifySourceInput,
    ImportDuplicateEnum,
    ImportMissingRefEnum,
    ImportObjectsInput,
    ScraperSourceInput,
    SetupInput,
    StashConfigInput,
)
from tests.fixtures import create_graphql_response


# =============================================================================
# metadata_generate tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_metadata_generate_with_options_none(
    respx_stash_client: StashClient,
) -> None:
    """Test metadata_generate with options=None (covers false branch line 73)."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("metadataGenerate", "job-123")
            )
        ]
    )

    job_id = await respx_stash_client.metadata_generate(
        options=None, input_data={"sceneIDs": ["1"]}
    )

    assert job_id == "job-123"
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_metadata_generate_with_input_data_none(
    respx_stash_client: StashClient,
) -> None:
    """Test metadata_generate with input_data=None (covers false branch line 83)."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("metadataGenerate", "job-456")
            )
        ]
    )

    job_id = await respx_stash_client.metadata_generate(
        options={"covers": True}, input_data=None
    )

    assert job_id == "job-456"
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_metadata_generate_no_job_id_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test metadata_generate raises ValueError when no job ID returned (line 102)."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("metadataGenerate", None))
        ]
    )

    with pytest.raises(ValueError, match="No job ID returned from server"):
        await respx_stash_client.metadata_generate(options={"covers": True})

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_metadata_generate_exception(respx_stash_client: StashClient) -> None:
    """Test metadata_generate handles exceptions (lines 106-108)."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=Exception("Network error")
    )

    with pytest.raises(Exception, match="Network error"):
        await respx_stash_client.metadata_generate(options={"covers": True})


@pytest.mark.asyncio
@pytest.mark.unit
async def test_metadata_generate_options_invalid_type(
    respx_stash_client: StashClient,
) -> None:
    """Test metadata_generate rejects invalid options type."""
    with pytest.raises(
        TypeError, match="options must be GenerateMetadataOptions or dict"
    ):
        await respx_stash_client.metadata_generate(options=["covers"])  # type: ignore[arg-type]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_metadata_generate_input_data_invalid_type(
    respx_stash_client: StashClient,
) -> None:
    """Test metadata_generate rejects invalid input_data type."""
    with pytest.raises(
        TypeError, match="input_data must be GenerateMetadataInput or dict"
    ):
        await respx_stash_client.metadata_generate(input_data="scene-1")  # type: ignore[arg-type]


# =============================================================================
# metadata_scan tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_metadata_scan_with_flags_not_none(
    respx_stash_client: StashClient,
) -> None:
    """Test metadata_scan with flags provided (covers false branch for line 134)."""
    # Mock get_configuration_defaults
    defaults_data = {
        "scan": {
            "rescan": False,
            "scanGenerateCovers": True,
            "scanGeneratePreviews": True,
            "scanGenerateImagePreviews": True,
            "scanGenerateSprites": True,
            "scanGeneratePhashes": True,
            "scanGenerateThumbnails": True,
            "scanGenerateClipPreviews": True,
        },
        "autoTag": {},
        "generate": {},
        "deleteFile": False,
        "deleteGenerated": False,
    }

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            # First call: get_configuration_defaults
            httpx.Response(
                200,
                json=create_graphql_response(
                    "configuration", {"defaults": defaults_data}
                ),
            ),
            # Second call: metadataScan
            httpx.Response(
                200, json=create_graphql_response("metadataScan", "job-scan-1")
            ),
        ]
    )

    job_id = await respx_stash_client.metadata_scan(
        paths=[], flags={"rescan": True, "scanGenerateCovers": False}
    )

    assert job_id == "job-scan-1"
    assert len(graphql_route.calls) == 2


@pytest.mark.asyncio
@pytest.mark.unit
async def test_metadata_scan_with_paths_not_none(
    respx_stash_client: StashClient,
) -> None:
    """Test metadata_scan with paths provided (covers false branch for line 136)."""
    # Mock get_configuration_defaults
    defaults_data = {
        "scan": {
            "rescan": False,
            "scanGenerateCovers": True,
            "scanGeneratePreviews": True,
            "scanGenerateImagePreviews": True,
            "scanGenerateSprites": True,
            "scanGeneratePhashes": True,
            "scanGenerateThumbnails": True,
            "scanGenerateClipPreviews": True,
        },
        "autoTag": {},
        "generate": {},
        "deleteFile": False,
        "deleteGenerated": False,
    }

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            # First call: get_configuration_defaults
            httpx.Response(
                200,
                json=create_graphql_response(
                    "configuration", {"defaults": defaults_data}
                ),
            ),
            # Second call: metadataScan
            httpx.Response(
                200, json=create_graphql_response("metadataScan", "job-scan-2")
            ),
        ]
    )

    job_id = await respx_stash_client.metadata_scan(paths=["/path/to/scan"], flags=None)

    assert job_id == "job-scan-2"
    assert len(graphql_route.calls) == 2


@pytest.mark.asyncio
@pytest.mark.unit
async def test_metadata_scan_get_defaults_exception(
    respx_stash_client: StashClient,
) -> None:
    """Test metadata_scan when get_configuration_defaults fails (lines 156-160)."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            # First call: get_configuration_defaults fails
            Exception("Failed to get defaults"),
            # Second call: metadataScan succeeds with hardcoded defaults
            httpx.Response(
                200, json=create_graphql_response("metadataScan", "job-scan-3")
            ),
        ]
    )

    job_id = await respx_stash_client.metadata_scan(paths=[], flags=None)

    assert job_id == "job-scan-3"
    assert len(graphql_route.calls) == 2


@pytest.mark.asyncio
@pytest.mark.unit
async def test_metadata_scan_no_job_id_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test metadata_scan raises ValueError when no job ID returned (line 183)."""
    defaults_data = {
        "scan": {
            "rescan": False,
            "scanGenerateCovers": True,
            "scanGeneratePreviews": True,
            "scanGenerateImagePreviews": True,
            "scanGenerateSprites": True,
            "scanGeneratePhashes": True,
            "scanGenerateThumbnails": True,
            "scanGenerateClipPreviews": True,
        },
        "autoTag": {},
        "generate": {},
        "deleteFile": False,
        "deleteGenerated": False,
    }

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            # First call: get_configuration_defaults
            httpx.Response(
                200,
                json=create_graphql_response(
                    "configuration", {"defaults": defaults_data}
                ),
            ),
            # Second call: metadataScan returns None
            httpx.Response(200, json=create_graphql_response("metadataScan", None)),
        ]
    )

    with pytest.raises(
        ValueError, match="Failed to start metadata scan - no job ID returned"
    ):
        await respx_stash_client.metadata_scan(paths=[], flags=None)

    assert len(graphql_route.calls) == 2


@pytest.mark.asyncio
@pytest.mark.unit
async def test_metadata_scan_execute_exception(
    respx_stash_client: StashClient,
) -> None:
    """Test metadata_scan when execute fails (lines 185-187)."""
    defaults_data = {
        "scan": {
            "rescan": False,
            "scanGenerateCovers": True,
            "scanGeneratePreviews": True,
            "scanGenerateImagePreviews": True,
            "scanGenerateSprites": True,
            "scanGeneratePhashes": True,
            "scanGenerateThumbnails": True,
            "scanGenerateClipPreviews": True,
        },
        "autoTag": {},
        "generate": {},
        "deleteFile": False,
        "deleteGenerated": False,
    }

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            # First call: get_configuration_defaults
            httpx.Response(
                200,
                json=create_graphql_response(
                    "configuration", {"defaults": defaults_data}
                ),
            ),
            # Second call: metadataScan fails with GraphQL error
            httpx.Response(500, json={"errors": [{"message": "Server error"}]}),
        ]
    )

    with pytest.raises(ValueError, match="Failed to start metadata scan"):
        await respx_stash_client.metadata_scan(paths=[], flags=None)

    assert len(graphql_route.calls) == 2


# =============================================================================
# metadata_clean tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_metadata_clean_with_dict(respx_stash_client: StashClient) -> None:
    """Test cleaning metadata with dict input."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("metadataClean", "job-123")
            )
        ]
    )

    job_id = await respx_stash_client.metadata_clean(
        {"paths": ["/path/to/clean"], "dryRun": False}
    )

    assert job_id == "job-123"
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "metadataClean" in req["query"]
    assert req["variables"]["input"]["paths"] == ["/path/to/clean"]
    assert req["variables"]["input"]["dryRun"] is False


@pytest.mark.asyncio
@pytest.mark.unit
async def test_metadata_clean_with_model(respx_stash_client: StashClient) -> None:
    """Test cleaning metadata with CleanMetadataInput model."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("metadataClean", "job-456")
            )
        ]
    )

    input_data = CleanMetadataInput(paths=["/another/path"], dryRun=True)
    job_id = await respx_stash_client.metadata_clean(input_data)

    assert job_id == "job-456"
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["input"]["paths"] == ["/another/path"]
    assert req["variables"]["input"]["dryRun"] is True


@pytest.mark.asyncio
@pytest.mark.unit
async def test_metadata_clean_error_raises(respx_stash_client: StashClient) -> None:
    """Test metadata_clean raises on error."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    with pytest.raises(StashGraphQLError, match="Server error"):
        await respx_stash_client.metadata_clean({"paths": [], "dryRun": False})


# =============================================================================
# metadata_clean_generated tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_metadata_clean_generated_with_dict(
    respx_stash_client: StashClient,
) -> None:
    """Test cleaning generated files with dict input."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("metadataCleanGenerated", "job-789")
            )
        ]
    )

    job_id = await respx_stash_client.metadata_clean_generated(
        {"sprites": True, "screenshots": True, "dryRun": False}
    )

    assert job_id == "job-789"
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "metadataCleanGenerated" in req["query"]
    assert req["variables"]["input"]["sprites"] is True
    assert req["variables"]["input"]["screenshots"] is True


@pytest.mark.asyncio
@pytest.mark.unit
async def test_metadata_clean_generated_with_model(
    respx_stash_client: StashClient,
) -> None:
    """Test cleaning generated files with CleanGeneratedInput model."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("metadataCleanGenerated", "job-101")
            )
        ]
    )

    input_data = CleanGeneratedInput(
        blobFiles=True, imageThumbnails=True, markers=False, dryRun=True
    )
    job_id = await respx_stash_client.metadata_clean_generated(input_data)

    assert job_id == "job-101"
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["input"]["blobFiles"] is True
    assert req["variables"]["input"]["imageThumbnails"] is True
    assert req["variables"]["input"]["dryRun"] is True


@pytest.mark.asyncio
@pytest.mark.unit
async def test_metadata_clean_generated_error_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test metadata_clean_generated raises on error."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    with pytest.raises(StashGraphQLError, match="Server error"):
        await respx_stash_client.metadata_clean_generated({"dryRun": False})


# =============================================================================
# export_objects tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_export_objects_with_dict(respx_stash_client: StashClient) -> None:
    """Test exporting objects with dict input."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("exportObjects", "download-token-abc")
            )
        ]
    )

    token = await respx_stash_client.export_objects({"scenes": {"all": True}})

    assert token == "download-token-abc"  # nosec B105  # noqa: S105
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "exportObjects" in req["query"]
    assert req["variables"]["input"]["scenes"]["all"] is True


@pytest.mark.asyncio
@pytest.mark.unit
async def test_export_objects_with_model(respx_stash_client: StashClient) -> None:
    """Test exporting objects with ExportObjectsInput model."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("exportObjects", "download-token-xyz")
            )
        ]
    )

    input_data = ExportObjectsInput(
        performers=ExportObjectTypeInput(ids=["1", "2", "3"]),
        includeDependencies=True,
    )
    token = await respx_stash_client.export_objects(input_data)

    assert token == "download-token-xyz"  # nosec B105  # noqa: S105
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["input"]["performers"]["ids"] == ["1", "2", "3"]
    assert req["variables"]["input"]["includeDependencies"] is True


@pytest.mark.asyncio
@pytest.mark.unit
async def test_export_objects_error_raises(respx_stash_client: StashClient) -> None:
    """Test export_objects raises on error."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    with pytest.raises(StashGraphQLError, match="Server error"):
        await respx_stash_client.export_objects({"scenes": {"all": True}})


# =============================================================================
# import_objects tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_import_objects_with_dict(respx_stash_client: StashClient) -> None:
    """Test importing objects with dict input."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("importObjects", "import-job-123")
            )
        ]
    )

    job_id = await respx_stash_client.import_objects(
        {
            "file": "/path/to/export.json",
            "duplicateBehaviour": "IGNORE",
            "missingRefBehaviour": "FAIL",
        }
    )

    assert job_id == "import-job-123"
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "importObjects" in req["query"]
    assert req["variables"]["input"]["file"] == "/path/to/export.json"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_import_objects_with_model(respx_stash_client: StashClient) -> None:
    """Test importing objects with ImportObjectsInput model."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("importObjects", "import-job-456")
            )
        ]
    )

    input_data = ImportObjectsInput(
        file="/path/to/data.json",
        duplicateBehaviour=ImportDuplicateEnum.OVERWRITE,
        missingRefBehaviour=ImportMissingRefEnum.CREATE,
    )
    job_id = await respx_stash_client.import_objects(input_data)

    assert job_id == "import-job-456"
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["input"]["file"] == "/path/to/data.json"
    assert req["variables"]["input"]["duplicateBehaviour"] == "OVERWRITE"
    assert req["variables"]["input"]["missingRefBehaviour"] == "CREATE"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_import_objects_error_raises(respx_stash_client: StashClient) -> None:
    """Test import_objects raises on error."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    with pytest.raises(StashGraphQLError, match="Server error"):
        await respx_stash_client.import_objects(
            {
                "file": "/path/to/file",
                "duplicateBehaviour": "IGNORE",
                "missingRefBehaviour": "FAIL",
            }
        )


# =============================================================================
# backup_database tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_backup_database_with_dict(respx_stash_client: StashClient) -> None:
    """Test backing up database with dict input."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("backupDatabase", "backup-token-123")
            )
        ]
    )

    token = await respx_stash_client.backup_database({"download": True})

    assert token == "backup-token-123"  # nosec B105  # noqa: S105
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "backupDatabase" in req["query"]
    assert req["variables"]["input"]["download"] is True


@pytest.mark.asyncio
@pytest.mark.unit
async def test_backup_database_with_model(respx_stash_client: StashClient) -> None:
    """Test backing up database with BackupDatabaseInput model."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "backupDatabase", "/path/to/backup.sqlite3"
                ),
            )
        ]
    )

    input_data = BackupDatabaseInput(download=False)
    path = await respx_stash_client.backup_database(input_data)

    assert path == "/path/to/backup.sqlite3"
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["input"]["download"] is False


@pytest.mark.asyncio
@pytest.mark.unit
async def test_backup_database_error_raises(respx_stash_client: StashClient) -> None:
    """Test backup_database raises on error."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    with pytest.raises(StashGraphQLError, match="Server error"):
        await respx_stash_client.backup_database({"download": True})


# =============================================================================
# anonymise_database tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_anonymise_database_with_dict(respx_stash_client: StashClient) -> None:
    """Test anonymising database with dict input."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("anonymiseDatabase", "anon-token-123")
            )
        ]
    )

    token = await respx_stash_client.anonymise_database({"download": True})

    assert token == "anon-token-123"  # nosec B105  # noqa: S105
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "anonymiseDatabase" in req["query"]
    assert req["variables"]["input"]["download"] is True


@pytest.mark.asyncio
@pytest.mark.unit
async def test_anonymise_database_with_model(respx_stash_client: StashClient) -> None:
    """Test anonymising database with AnonymiseDatabaseInput model."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "anonymiseDatabase", "/path/to/anon-backup.sqlite3"
                ),
            )
        ]
    )

    input_data = AnonymiseDatabaseInput(download=False)
    path = await respx_stash_client.anonymise_database(input_data)

    assert path == "/path/to/anon-backup.sqlite3"
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["input"]["download"] is False


@pytest.mark.asyncio
@pytest.mark.unit
async def test_anonymise_database_error_raises(respx_stash_client: StashClient) -> None:
    """Test anonymise_database raises on error."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    with pytest.raises(StashGraphQLError, match="Server error"):
        await respx_stash_client.anonymise_database({"download": True})


# =============================================================================
# migrate tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_migrate_with_dict(respx_stash_client: StashClient) -> None:
    """Test database migration with dict input."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("migrate", "migrate-job-123")
            )
        ]
    )

    job_id = await respx_stash_client.migrate({"backupPath": "/path/to/backup.db"})

    assert job_id == "migrate-job-123"
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "migrate" in req["query"]
    assert req["variables"]["input"]["backupPath"] == "/path/to/backup.db"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_migrate_error_raises(respx_stash_client: StashClient) -> None:
    """Test migrate raises on error."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    with pytest.raises(StashGraphQLError, match="Server error"):
        await respx_stash_client.migrate({"backupPath": "/path/to/backup.db"})


# =============================================================================
# migrate_hash_naming tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_migrate_hash_naming_success(respx_stash_client: StashClient) -> None:
    """Test hash naming migration."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "migrateHashNaming", "hash-migrate-job-123"
                ),
            )
        ]
    )

    job_id = await respx_stash_client.migrate_hash_naming()

    assert job_id == "hash-migrate-job-123"
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "migrateHashNaming" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_migrate_hash_naming_error_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test migrate_hash_naming raises on error."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    with pytest.raises(StashGraphQLError, match="Server error"):
        await respx_stash_client.migrate_hash_naming()


# =============================================================================
# migrate_scene_screenshots tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_migrate_scene_screenshots_with_dict(
    respx_stash_client: StashClient,
) -> None:
    """Test scene screenshot migration with dict input."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "migrateSceneScreenshots", "screenshot-migrate-job-123"
                ),
            )
        ]
    )

    job_id = await respx_stash_client.migrate_scene_screenshots(
        {"deleteFiles": True, "overwriteExisting": False}
    )

    assert job_id == "screenshot-migrate-job-123"
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "migrateSceneScreenshots" in req["query"]
    assert req["variables"]["input"]["deleteFiles"] is True
    assert req["variables"]["input"]["overwriteExisting"] is False


@pytest.mark.asyncio
@pytest.mark.unit
async def test_migrate_scene_screenshots_error_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test migrate_scene_screenshots raises on error."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    with pytest.raises(StashGraphQLError, match="Server error"):
        await respx_stash_client.migrate_scene_screenshots({"deleteFiles": True})


# =============================================================================
# migrate_blobs tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_migrate_blobs_with_dict(respx_stash_client: StashClient) -> None:
    """Test blob migration with dict input."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response("migrateBlobs", "blob-migrate-job-123"),
            )
        ]
    )

    job_id = await respx_stash_client.migrate_blobs({"deleteOld": False})

    assert job_id == "blob-migrate-job-123"
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "migrateBlobs" in req["query"]
    assert req["variables"]["input"]["deleteOld"] is False


@pytest.mark.asyncio
@pytest.mark.unit
async def test_migrate_blobs_error_raises(respx_stash_client: StashClient) -> None:
    """Test migrate_blobs raises on error."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    with pytest.raises(StashGraphQLError, match="Server error"):
        await respx_stash_client.migrate_blobs({"deleteOld": True})


# =============================================================================
# optimise_database tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_optimise_database_success(respx_stash_client: StashClient) -> None:
    """Test database optimization (covers lines 698-703)."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response("optimiseDatabase", "optimise-job-123"),
            )
        ]
    )

    job_id = await respx_stash_client.optimise_database()

    assert job_id == "optimise-job-123"
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "optimiseDatabase" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_optimise_database_error_raises(respx_stash_client: StashClient) -> None:
    """Test optimise_database raises on error (covers lines 701-703)."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    with pytest.raises(StashGraphQLError, match="Server error"):
        await respx_stash_client.optimise_database()


# =============================================================================
# setup tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_setup_with_dict(respx_stash_client: StashClient) -> None:
    """Test setup with dict input (covers lines 717-730)."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(200, json=create_graphql_response("setup", True))]
    )

    result = await respx_stash_client.setup(
        {
            "stashes": [{"path": "/media/videos", "excludeVideo": False}],
            "databaseFile": "/data/stash.db",
            "generatedLocation": "/data/generated",
        }
    )

    assert result is True
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "setup" in req["query"]
    assert req["variables"]["input"]["stashes"][0]["path"] == "/media/videos"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_setup_with_model(respx_stash_client: StashClient) -> None:
    """Test setup with SetupInput model (covers lines 718-726)."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(200, json=create_graphql_response("setup", True))]
    )

    input_data = SetupInput(
        stashes=[
            StashConfigInput(path="/media/videos", excludeVideo=False),
        ],
        databaseFile="/data/stash.db",
        generatedLocation="/data/generated",
    )
    result = await respx_stash_client.setup(input_data)

    assert result is True
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["input"]["stashes"][0]["path"] == "/media/videos"
    assert req["variables"]["input"]["databaseFile"] == "/data/stash.db"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_setup_returns_false(respx_stash_client: StashClient) -> None:
    """Test setup returns False when server returns False (covers line 727)."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(200, json=create_graphql_response("setup", False))]
    )

    result = await respx_stash_client.setup({"stashes": []})

    assert result is False
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_setup_error_raises(respx_stash_client: StashClient) -> None:
    """Test setup raises on error (covers lines 728-730)."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    with pytest.raises(StashGraphQLError, match="Server error"):
        await respx_stash_client.setup({"stashes": []})


# =============================================================================
# download_ffmpeg tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_download_ffmpeg_success(respx_stash_client: StashClient) -> None:
    """Test FFmpeg download (covers lines 738-743)."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("downloadFFMPEG", "ffmpeg-job-123")
            )
        ]
    )

    job_id = await respx_stash_client.download_ffmpeg()

    assert job_id == "ffmpeg-job-123"
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "downloadFFMpeg" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_download_ffmpeg_error_raises(respx_stash_client: StashClient) -> None:
    """Test download_ffmpeg raises on error (covers lines 741-743)."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    with pytest.raises(StashGraphQLError, match="Server error"):
        await respx_stash_client.download_ffmpeg()


# =============================================================================
# metadata_auto_tag tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_metadata_auto_tag_success(respx_stash_client: StashClient) -> None:
    """Test auto-tagging metadata with AutoTagMetadataInput model."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("metadataAutoTag", "autotag-job-123")
            )
        ]
    )

    input_data = AutoTagMetadataInput(
        paths=["/path/to/content"],
        performers=["*"],  # All performers
        studios=["1", "2"],  # Specific studio IDs
        tags=None,  # No tags
    )
    job_id = await respx_stash_client.metadata_auto_tag(input_data)

    assert job_id == "autotag-job-123"
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "metadataAutoTag" in req["query"]
    assert req["variables"]["input"]["paths"] == ["/path/to/content"]
    assert req["variables"]["input"]["performers"] == ["*"]
    assert req["variables"]["input"]["studios"] == ["1", "2"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_metadata_auto_tag_with_dict(respx_stash_client: StashClient) -> None:
    """Test auto-tagging metadata with dict input."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("metadataAutoTag", "autotag-job-456")
            )
        ]
    )

    job_id = await respx_stash_client.metadata_auto_tag(
        {
            "paths": ["/another/path"],
            "performers": ["performer-1", "performer-2"],
            "studios": ["*"],
            "tags": ["tag-1"],
        }
    )

    assert job_id == "autotag-job-456"
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "metadataAutoTag" in req["query"]
    assert req["variables"]["input"]["paths"] == ["/another/path"]
    assert req["variables"]["input"]["performers"] == ["performer-1", "performer-2"]
    assert req["variables"]["input"]["studios"] == ["*"]
    assert req["variables"]["input"]["tags"] == ["tag-1"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_metadata_auto_tag_error(respx_stash_client: StashClient) -> None:
    """Test metadata_auto_tag raises on error."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    with pytest.raises(StashGraphQLError, match="Server error"):
        await respx_stash_client.metadata_auto_tag({"performers": ["*"]})


# =============================================================================
# metadata_identify tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_metadata_identify_success(respx_stash_client: StashClient) -> None:
    """Test identifying scenes with IdentifyMetadataInput model."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response("metadataIdentify", "identify-job-123"),
            )
        ]
    )

    # Create source input
    source = IdentifySourceInput(
        source=ScraperSourceInput(
            scraper_id="scraper-1",
        ),
        options=None,
    )

    input_data = IdentifyMetadataInput(
        sources=[source],
        options=None,
        sceneIDs=["scene-1", "scene-2"],
        paths=None,
    )
    job_id = await respx_stash_client.metadata_identify(input_data)

    assert job_id == "identify-job-123"
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "metadataIdentify" in req["query"]
    assert "sceneIDs" in req["variables"]["input"]
    assert req["variables"]["input"]["sceneIDs"] == ["scene-1", "scene-2"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_metadata_identify_with_dict(respx_stash_client: StashClient) -> None:
    """Test identifying scenes with dict input."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response("metadataIdentify", "identify-job-456"),
            )
        ]
    )

    job_id = await respx_stash_client.metadata_identify(
        {
            "sources": [{"source": {"scraperId": "scraper-2"}}],
            "paths": ["/path/to/scene.mp4"],
        }
    )

    assert job_id == "identify-job-456"
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "metadataIdentify" in req["query"]
    assert req["variables"]["input"]["paths"] == ["/path/to/scene.mp4"]
    assert len(req["variables"]["input"]["sources"]) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_metadata_identify_error(respx_stash_client: StashClient) -> None:
    """Test metadata_identify raises on error."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    with pytest.raises(StashGraphQLError, match="Server error"):
        await respx_stash_client.metadata_identify(
            {
                "sources": [{"source": {"scraperId": "scraper-1"}}],
                "sceneIDs": ["scene-1"],
            }
        )


# =============================================================================
# metadata_import tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_metadata_import_success(respx_stash_client: StashClient) -> None:
    """Test importing metadata (full import)."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("metadataImport", "import-job-123")
            )
        ]
    )

    job_id = await respx_stash_client.metadata_import()

    assert job_id == "import-job-123"
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "metadataImport" in req["query"]
    # metadataImport takes no arguments
    assert "variables" not in req or req.get("variables") == {}


@pytest.mark.asyncio
@pytest.mark.unit
async def test_metadata_import_error(respx_stash_client: StashClient) -> None:
    """Test metadata_import raises on error."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    with pytest.raises(StashGraphQLError, match="Server error"):
        await respx_stash_client.metadata_import()


# =============================================================================
# metadata_export tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_metadata_export_success(respx_stash_client: StashClient) -> None:
    """Test exporting metadata (full export)."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("metadataExport", "export-job-123")
            )
        ]
    )

    job_id = await respx_stash_client.metadata_export()

    assert job_id == "export-job-123"
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "metadataExport" in req["query"]
    # metadataExport takes no arguments
    assert "variables" not in req or req.get("variables") == {}


@pytest.mark.asyncio
@pytest.mark.unit
async def test_metadata_export_error(respx_stash_client: StashClient) -> None:
    """Test metadata_export raises on error."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    with pytest.raises(StashGraphQLError, match="Server error"):
        await respx_stash_client.metadata_export()
