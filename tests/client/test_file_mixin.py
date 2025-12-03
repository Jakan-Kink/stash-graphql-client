"""Unit tests for FileClientMixin.

These tests mock at the HTTP boundary using respx, allowing real code execution
through the entire GraphQL client stack including serialization/deserialization.
"""

import json

import httpx
import pytest
import respx

from stash_graphql_client import StashClient
from stash_graphql_client.types.files import (
    AssignSceneFileInput,
    FileSetFingerprintsInput,
    MoveFilesInput,
    SetFingerprintsInput,
)
from stash_graphql_client.types.filters import FolderFilterType
from tests.fixtures import (
    create_file_dict,
    create_find_files_result,
    create_find_folders_result,
    create_folder_dict,
    create_graphql_response,
)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_file_by_id(respx_stash_client: StashClient) -> None:
    """Test finding a file by ID."""
    file_data = create_file_dict(
        id="123",
        path="/videos/scene.mp4",
        size=1024000000,
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("findFile", file_data))
        ]
    )

    file = await respx_stash_client.find_file(id="123")

    # Verify the result
    assert file is not None
    assert file.id == "123"
    assert file.path == "/videos/scene.mp4"
    assert file.size == 1024000000

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "findFile" in req["query"]
    assert req["variables"]["id"] == "123"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_file_by_path(respx_stash_client: StashClient) -> None:
    """Test finding a file by path."""
    file_data = create_file_dict(
        id="456",
        path="/images/photo.jpg",
        size=512000,
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("findFile", file_data))
        ]
    )

    file = await respx_stash_client.find_file(path="/images/photo.jpg")

    assert file is not None
    assert file.path == "/images/photo.jpg"

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["path"] == "/images/photo.jpg"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_file_not_found(respx_stash_client: StashClient) -> None:
    """Test finding a file that doesn't exist."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("findFile", None))
        ]
    )

    file = await respx_stash_client.find_file(id="none_file")

    assert file is None

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_file_no_params_raises_value_error(
    respx_stash_client: StashClient,
) -> None:
    """Test that find_file raises ValueError when neither id nor path is provided."""
    with pytest.raises(ValueError, match="Either id or path must be provided"):
        await respx_stash_client.find_file()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_file_error_returns_none(respx_stash_client: StashClient) -> None:
    """Test handling errors when finding a file returns None."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(500, json={"errors": [{"message": "Test error"}]})]
    )

    file = await respx_stash_client.find_file(id="error_file")

    assert file is None

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_files(respx_stash_client: StashClient) -> None:
    """Test finding files."""
    file_data = create_file_dict(
        id="123",
        path="/videos/scene.mp4",
        size=1024000,
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findFiles",
                    create_find_files_result(
                        count=1,
                        files=[file_data],
                        megapixels=0.0,
                        duration=120.5,
                        size=1024000,
                    ),
                ),
            )
        ]
    )

    result = await respx_stash_client.find_files()

    # Verify the results
    assert result.count == 1
    assert len(result.files) == 1
    assert result.files[0].id == "123"
    assert result.duration == 120.5
    assert result.size == 1024000

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "findFiles" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_files_empty(respx_stash_client: StashClient) -> None:
    """Test finding files when none exist."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findFiles",
                    create_find_files_result(count=0, files=[]),
                ),
            )
        ]
    )

    result = await respx_stash_client.find_files()

    assert result.count == 0
    assert len(result.files) == 0

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_files_with_filter(respx_stash_client: StashClient) -> None:
    """Test finding files with filter parameters."""
    file_data = create_file_dict(id="123", path="/videos/filtered.mp4")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findFiles",
                    create_find_files_result(count=1, files=[file_data]),
                ),
            )
        ]
    )

    result = await respx_stash_client.find_files(filter_={"per_page": 10, "page": 1})

    assert result.count == 1

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["filter"]["per_page"] == 10
    assert req["variables"]["filter"]["page"] == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_files_with_file_filter(respx_stash_client: StashClient) -> None:
    """Test finding files with file-specific filter."""
    file_data = create_file_dict(id="123", path="/videos/large.mp4", size=1000000000)

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findFiles",
                    create_find_files_result(count=1, files=[file_data]),
                ),
            )
        ]
    )

    result = await respx_stash_client.find_files(
        file_filter={"size": {"value": 1000000000, "modifier": "GREATER_THAN"}}
    )

    assert result.count == 1

    # Verify GraphQL call includes file_filter
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["file_filter"]["size"]["value"] == 1000000000


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_files_by_ids(respx_stash_client: StashClient) -> None:
    """Test finding files by a list of IDs."""
    files_data = [
        create_file_dict(id="1", path="/videos/file1.mp4"),
        create_file_dict(id="2", path="/videos/file2.mp4"),
        create_file_dict(id="3", path="/videos/file3.mp4"),
    ]

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findFiles",
                    create_find_files_result(count=3, files=files_data),
                ),
            )
        ]
    )

    result = await respx_stash_client.find_files(ids=["1", "2", "3"])

    assert result.count == 3
    assert len(result.files) == 3

    # Verify GraphQL call includes ids
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["ids"] == ["1", "2", "3"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_files_error_returns_empty(respx_stash_client: StashClient) -> None:
    """Test that find_files returns empty result on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    result = await respx_stash_client.find_files()

    assert result.count == 0
    assert len(result.files) == 0
    assert result.megapixels == 0.0
    assert result.duration == 0.0
    assert result.size == 0

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_move_files(respx_stash_client: StashClient) -> None:
    """Test moving files to a new location."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("moveFiles", True))
        ]
    )

    result = await respx_stash_client.move_files(
        {"ids": ["1", "2", "3"], "destination_folder": "/new/location"}
    )

    assert result is True

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "moveFiles" in req["query"]
    assert req["variables"]["input"]["ids"] == ["1", "2", "3"]
    assert req["variables"]["input"]["destination_folder"] == "/new/location"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_move_files_with_rename(respx_stash_client: StashClient) -> None:
    """Test moving a single file with rename."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("moveFiles", True))
        ]
    )

    result = await respx_stash_client.move_files(
        {
            "ids": ["1"],
            "destination_folder": "/new/location",
            "destination_basename": "renamed.mp4",
        }
    )

    assert result is True

    # Verify GraphQL call includes basename
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["input"]["destination_basename"] == "renamed.mp4"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_move_files_error_returns_false(respx_stash_client: StashClient) -> None:
    """Test that move_files returns False on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    result = await respx_stash_client.move_files(
        {"ids": ["1"], "destination_folder": "/fail"}
    )

    assert result is False

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_file_set_fingerprints(respx_stash_client: StashClient) -> None:
    """Test setting file fingerprints."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("fileSetFingerprints", True)
            )
        ]
    )

    result = await respx_stash_client.file_set_fingerprints(
        {"id": "file123", "fingerprints": [{"type": "MD5", "value": "abc123def456"}]}
    )

    assert result is True

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "fileSetFingerprints" in req["query"]
    assert req["variables"]["input"]["id"] == "file123"
    assert req["variables"]["input"]["fingerprints"][0]["type"] == "MD5"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_file_set_fingerprints_error_returns_false(
    respx_stash_client: StashClient,
) -> None:
    """Test that file_set_fingerprints returns False on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    result = await respx_stash_client.file_set_fingerprints(
        {"id": "file123", "fingerprints": []}
    )

    assert result is False

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_assign_file(respx_stash_client: StashClient) -> None:
    """Test assigning a file to a scene."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("sceneAssignFile", True))
        ]
    )

    result = await respx_stash_client.scene_assign_file(
        {"scene_id": "scene123", "file_id": "file456"}
    )

    assert result is True

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "sceneAssignFile" in req["query"]
    assert req["variables"]["input"]["scene_id"] == "scene123"
    assert req["variables"]["input"]["file_id"] == "file456"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_assign_file_error_returns_false(
    respx_stash_client: StashClient,
) -> None:
    """Test that scene_assign_file returns False on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    result = await respx_stash_client.scene_assign_file(
        {"scene_id": "scene123", "file_id": "file456"}
    )

    assert result is False

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_delete_files(respx_stash_client: StashClient) -> None:
    """Test deleting files."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("deleteFiles", True))
        ]
    )

    result = await respx_stash_client.delete_files(ids=["1", "2", "3"])

    assert result is True

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "deleteFiles" in req["query"]
    assert req["variables"]["ids"] == ["1", "2", "3"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_delete_files_error_raises(respx_stash_client: StashClient) -> None:
    """Test that delete_files raises on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    with pytest.raises(ValueError):
        await respx_stash_client.delete_files(ids=["1"])

    assert len(graphql_route.calls) == 1


# Tests for Pydantic input types (covering isinstance branches)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_move_files_with_input_type(respx_stash_client: StashClient) -> None:
    """Test moving files using MoveFilesInput Pydantic model.

    This covers line 214: if isinstance(input_data, MoveFilesInput)
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("moveFiles", True))
        ]
    )

    input_data = MoveFilesInput(
        ids=["1", "2"],
        destination_folder="/new/path",
        destination_basename="renamed.mp4",
    )
    result = await respx_stash_client.move_files(input_data)

    assert result is True

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["input"]["ids"] == ["1", "2"]
    assert req["variables"]["input"]["destination_folder"] == "/new/path"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_file_set_fingerprints_with_input_type(
    respx_stash_client: StashClient,
) -> None:
    """Test setting fingerprints using FileSetFingerprintsInput Pydantic model.

    This covers line 268: if isinstance(input_data, FileSetFingerprintsInput)
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("fileSetFingerprints", True)
            )
        ]
    )

    input_data = FileSetFingerprintsInput(
        id="file123",
        fingerprints=[
            SetFingerprintsInput(type="MD5", value="abc123"),
            SetFingerprintsInput(type="PHASH", value="def456"),
        ],
    )
    result = await respx_stash_client.file_set_fingerprints(input_data)

    assert result is True

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["input"]["id"] == "file123"
    assert len(req["variables"]["input"]["fingerprints"]) == 2


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_assign_file_with_input_type(
    respx_stash_client: StashClient,
) -> None:
    """Test assigning file to scene using AssignSceneFileInput Pydantic model.

    This covers line 318: if isinstance(input_data, AssignSceneFileInput)
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("sceneAssignFile", True))
        ]
    )

    input_data = AssignSceneFileInput(scene_id="scene123", file_id="file456")
    result = await respx_stash_client.scene_assign_file(input_data)

    assert result is True

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["input"]["scene_id"] == "scene123"
    assert req["variables"]["input"]["file_id"] == "file456"


# Tests for find_folder (lines 372-386)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_folder_by_id(respx_stash_client: StashClient) -> None:
    """Test finding a folder by ID.

    This covers lines 372-386: find_folder method.
    """
    folder_data = create_folder_dict(id="folder123", path="/videos/scenes")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("findFolder", folder_data))
        ]
    )

    folder = await respx_stash_client.find_folder(id="folder123")

    assert folder is not None
    assert folder.id == "folder123"
    assert folder.path == "/videos/scenes"

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "findFolder" in req["query"]
    assert req["variables"]["id"] == "folder123"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_folder_by_path(respx_stash_client: StashClient) -> None:
    """Test finding a folder by path."""
    folder_data = create_folder_dict(id="folder456", path="/images/gallery")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("findFolder", folder_data))
        ]
    )

    folder = await respx_stash_client.find_folder(path="/images/gallery")

    assert folder is not None
    assert folder.path == "/images/gallery"

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["path"] == "/images/gallery"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_folder_not_found(respx_stash_client: StashClient) -> None:
    """Test finding a folder that doesn't exist."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("findFolder", None))
        ]
    )

    folder = await respx_stash_client.find_folder(id="nonexistent")

    assert folder is None

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_folder_no_params_raises_value_error(
    respx_stash_client: StashClient,
) -> None:
    """Test that find_folder raises ValueError when neither id nor path provided."""
    with pytest.raises(ValueError, match="Either id or path must be provided"):
        await respx_stash_client.find_folder()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_folder_error_returns_none(respx_stash_client: StashClient) -> None:
    """Test that find_folder returns None on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    folder = await respx_stash_client.find_folder(id="error_folder")

    assert folder is None

    assert len(graphql_route.calls) == 1


# Tests for find_folders (lines 404-422)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_folders(respx_stash_client: StashClient) -> None:
    """Test finding folders.

    This covers lines 404-422: find_folders method.
    """
    folder_data = [
        create_folder_dict(id="folder1", path="/videos"),
        create_folder_dict(id="folder2", path="/images"),
    ]

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findFolders",
                    create_find_folders_result(count=2, folders=folder_data),
                ),
            )
        ]
    )

    result = await respx_stash_client.find_folders()

    assert result.count == 2
    assert len(result.folders) == 2
    assert result.folders[0].id == "folder1"

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "findFolders" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_folders_empty(respx_stash_client: StashClient) -> None:
    """Test finding folders when none exist."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findFolders", create_find_folders_result(count=0, folders=[])
                ),
            )
        ]
    )

    result = await respx_stash_client.find_folders()

    assert result.count == 0
    assert len(result.folders) == 0

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_folders_with_filter(respx_stash_client: StashClient) -> None:
    """Test finding folders with filter parameters."""
    folder_data = [create_folder_dict(id="folder1", path="/filtered")]

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findFolders",
                    create_find_folders_result(count=1, folders=folder_data),
                ),
            )
        ]
    )

    result = await respx_stash_client.find_folders(filter_={"per_page": 10, "page": 1})

    assert result.count == 1

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["filter"]["per_page"] == 10


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_folders_with_folder_filter_type(
    respx_stash_client: StashClient,
) -> None:
    """Test finding folders with FolderFilterType Pydantic model.

    This covers line 406-407: if isinstance(folder_filter, FolderFilterType)
    """
    folder_data = [create_folder_dict(id="folder1", path="/videos/scenes")]

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findFolders",
                    create_find_folders_result(count=1, folders=folder_data),
                ),
            )
        ]
    )

    folder_filter = FolderFilterType(path={"value": "/videos", "modifier": "INCLUDES"})
    result = await respx_stash_client.find_folders(folder_filter=folder_filter)

    assert result.count == 1

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["folder_filter"]["path"]["value"] == "/videos"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_folders_by_ids(respx_stash_client: StashClient) -> None:
    """Test finding folders by a list of IDs."""
    folder_data = [
        create_folder_dict(id="folder1", path="/path1"),
        create_folder_dict(id="folder2", path="/path2"),
    ]

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findFolders",
                    create_find_folders_result(count=2, folders=folder_data),
                ),
            )
        ]
    )

    result = await respx_stash_client.find_folders(ids=["folder1", "folder2"])

    assert result.count == 2

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["ids"] == ["folder1", "folder2"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_folders_error_returns_empty(
    respx_stash_client: StashClient,
) -> None:
    """Test that find_folders returns empty result on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    result = await respx_stash_client.find_folders()

    assert result.count == 0
    assert len(result.folders) == 0

    assert len(graphql_route.calls) == 1
