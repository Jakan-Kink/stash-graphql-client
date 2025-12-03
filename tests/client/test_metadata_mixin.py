"""Unit tests for MetadataClientMixin.

These tests mock at the HTTP boundary using respx, allowing real code execution
through the entire GraphQL client stack including serialization/deserialization.
"""

import json

import httpx
import pytest
import respx

from stash_graphql_client import StashClient
from stash_graphql_client.types import (
    AnonymiseDatabaseInput,
    BackupDatabaseInput,
    CleanGeneratedInput,
    CleanMetadataInput,
    ExportObjectsInput,
    ExportObjectTypeInput,
    ImportDuplicateEnum,
    ImportMissingRefEnum,
    ImportObjectsInput,
)
from tests.fixtures import create_graphql_response


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

    with pytest.raises(Exception):
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

    with pytest.raises(Exception):
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

    assert token == "download-token-abc"
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

    assert token == "download-token-xyz"
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

    with pytest.raises(Exception):
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

    with pytest.raises(Exception):
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

    assert token == "backup-token-123"
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

    with pytest.raises(Exception):
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

    assert token == "anon-token-123"
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

    with pytest.raises(Exception):
        await respx_stash_client.anonymise_database({"download": True})
