"""Unit tests for MigrationClientMixin.

These tests mock at the HTTP boundary using respx, allowing real code execution
through the entire GraphQL client stack including serialization/deserialization.

NOTE: This test file is written BEFORE the mixin implementation exists.
The tests define the expected API contract for the migration mixin.
"""

import json

import httpx
import pytest
import respx

from stash_graphql_client import StashClient
from stash_graphql_client.types import (
    MigrateBlobsInput,
    MigrateInput,
    MigrateSceneScreenshotsInput,
)
from tests.fixtures import create_graphql_response


# =============================================================================
# migrate tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_migrate_with_dict(respx_stash_client: StashClient) -> None:
    """Test migrating database with dict input."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("migrate", "migrate-job-123")
            )
        ]
    )

    job_id = await respx_stash_client.migrate({"backupPath": "/path/to/backup.sqlite3"})

    assert job_id == "migrate-job-123"
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "migrate" in req["query"]
    assert req["variables"]["input"]["backupPath"] == "/path/to/backup.sqlite3"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_migrate_with_model(respx_stash_client: StashClient) -> None:
    """Test migrating database with MigrateInput model."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("migrate", "migrate-job-456")
            )
        ]
    )

    input_data = MigrateInput(backupPath="/backup/path/db.sqlite3")
    job_id = await respx_stash_client.migrate(input_data)

    assert job_id == "migrate-job-456"
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["input"]["backupPath"] == "/backup/path/db.sqlite3"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_migrate_error_raises(respx_stash_client: StashClient) -> None:
    """Test migrate raises on error."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    with pytest.raises(Exception):
        await respx_stash_client.migrate({"backupPath": "/path/to/backup"})


# =============================================================================
# migrate_hash_naming tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_migrate_hash_naming_success(respx_stash_client: StashClient) -> None:
    """Test migrating hash naming returns job ID."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("migrateHashNaming", "hash-job-789")
            )
        ]
    )

    job_id = await respx_stash_client.migrate_hash_naming()

    assert job_id == "hash-job-789"
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

    with pytest.raises(Exception):
        await respx_stash_client.migrate_hash_naming()


# =============================================================================
# migrate_scene_screenshots tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_migrate_scene_screenshots_with_dict(
    respx_stash_client: StashClient,
) -> None:
    """Test migrating scene screenshots with dict input."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response("migrateSceneScreenshots", "ss-job-123"),
            )
        ]
    )

    job_id = await respx_stash_client.migrate_scene_screenshots(
        {"deleteFiles": True, "overwriteExisting": False}
    )

    assert job_id == "ss-job-123"
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "migrateSceneScreenshots" in req["query"]
    assert req["variables"]["input"]["deleteFiles"] is True
    assert req["variables"]["input"]["overwriteExisting"] is False


@pytest.mark.asyncio
@pytest.mark.unit
async def test_migrate_scene_screenshots_with_model(
    respx_stash_client: StashClient,
) -> None:
    """Test migrating scene screenshots with MigrateSceneScreenshotsInput model."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response("migrateSceneScreenshots", "ss-job-456"),
            )
        ]
    )

    input_data = MigrateSceneScreenshotsInput(deleteFiles=False, overwriteExisting=True)
    job_id = await respx_stash_client.migrate_scene_screenshots(input_data)

    assert job_id == "ss-job-456"
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["input"]["deleteFiles"] is False
    assert req["variables"]["input"]["overwriteExisting"] is True


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

    with pytest.raises(Exception):
        await respx_stash_client.migrate_scene_screenshots({"deleteFiles": False})


# =============================================================================
# migrate_blobs tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_migrate_blobs_with_dict(respx_stash_client: StashClient) -> None:
    """Test migrating blobs with dict input."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("migrateBlobs", "blob-job-123")
            )
        ]
    )

    job_id = await respx_stash_client.migrate_blobs({"deleteOld": True})

    assert job_id == "blob-job-123"
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "migrateBlobs" in req["query"]
    assert req["variables"]["input"]["deleteOld"] is True


@pytest.mark.asyncio
@pytest.mark.unit
async def test_migrate_blobs_with_model(respx_stash_client: StashClient) -> None:
    """Test migrating blobs with MigrateBlobsInput model."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("migrateBlobs", "blob-job-456")
            )
        ]
    )

    input_data = MigrateBlobsInput(deleteOld=False)
    job_id = await respx_stash_client.migrate_blobs(input_data)

    assert job_id == "blob-job-456"
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
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

    with pytest.raises(Exception):
        await respx_stash_client.migrate_blobs({"deleteOld": True})
