"""Unit tests for directory query operation.

These tests mock at the HTTP boundary using respx, allowing real code execution
through the entire GraphQL client stack including serialization/deserialization.

NOTE: This test file follows TDD - written BEFORE implementation exists.
The tests define the expected API contract for the directory query.
"""

import json

import httpx
import pytest
import respx

from stash_graphql_client import StashClient
from stash_graphql_client.errors import StashGraphQLError
from stash_graphql_client.types.unset import is_set
from tests.fixtures import create_graphql_response


# =============================================================================
# Helper function to create directory test data
# =============================================================================


def create_directory_result(
    path: str,
    parent: str | None = None,
    directories: list[str] | None = None,
) -> dict[str, str | list[str] | None]:
    """Create a directory query result matching Directory type.

    Args:
        path: The current directory path
        parent: Parent directory path (None for root)
        directories: List of subdirectory names

    Returns:
        Dict matching Directory schema

    Example:
        result = create_directory_result(
            path="/home/user/videos",
            parent="/home/user",
            directories=["movies", "clips"]
        )
    """
    return {
        "path": path,
        "parent": parent,
        "directories": directories if directories is not None else [],
    }


# =============================================================================
# directory query tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_directory_success(respx_stash_client: StashClient) -> None:
    """Test directory query with path and subdirectories."""
    directory_data = create_directory_result(
        path="/home/user/videos",
        parent="/home/user",
        directories=["movies", "clips", "raw"],
    )
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("directory", directory_data)
            )
        ]
    )

    result = await respx_stash_client.directory(path="/home/user/videos")

    assert result is not None
    assert result.path == "/home/user/videos"
    assert result.parent == "/home/user"
    assert result.directories == ["movies", "clips", "raw"]
    assert len(graphql_route.calls) == 1

    req = json.loads(graphql_route.calls[0].request.content)
    assert "directory" in req["query"]
    assert req["variables"]["path"] == "/home/user/videos"
    # Default locale should be "en"
    assert req["variables"]["locale"] == "en"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_directory_with_parent(respx_stash_client: StashClient) -> None:
    """Test directory with parent path."""
    directory_data = create_directory_result(
        path="/media/stash/scenes",
        parent="/media/stash",
        directories=["2024", "2023", "archive"],
    )
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("directory", directory_data)
            )
        ]
    )

    result = await respx_stash_client.directory(path="/media/stash/scenes")

    assert result is not None
    assert result.path == "/media/stash/scenes"
    assert result.parent == "/media/stash"
    assert is_set(result.directories)
    assert len(result.directories) == 3
    assert "2024" in result.directories
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_directory_root(respx_stash_client: StashClient) -> None:
    """Test root directory with no parent."""
    directory_data = create_directory_result(
        path="/",
        parent=None,
        directories=["home", "media", "var", "tmp"],
    )
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("directory", directory_data)
            )
        ]
    )

    result = await respx_stash_client.directory(path="/")

    assert result is not None
    assert result.path == "/"
    assert result.parent is None
    assert is_set(result.directories)
    assert len(result.directories) == 4
    assert "home" in result.directories
    assert len(graphql_route.calls) == 1

    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["path"] == "/"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_directory_empty(respx_stash_client: StashClient) -> None:
    """Test directory with no subdirectories."""
    directory_data = create_directory_result(
        path="/home/user/empty_folder",
        parent="/home/user",
        directories=[],
    )
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("directory", directory_data)
            )
        ]
    )

    result = await respx_stash_client.directory(path="/home/user/empty_folder")

    assert result is not None
    assert result.path == "/home/user/empty_folder"
    assert result.parent == "/home/user"
    assert result.directories == []
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_directory_with_custom_locale(respx_stash_client: StashClient) -> None:
    """Test directory query with custom locale parameter."""
    directory_data = create_directory_result(
        path="/home/user/docs",
        parent="/home/user",
        directories=["français", "español"],
    )
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("directory", directory_data)
            )
        ]
    )

    result = await respx_stash_client.directory(path="/home/user/docs", locale="fr-FR")

    assert result is not None
    assert result.path == "/home/user/docs"
    assert len(graphql_route.calls) == 1

    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["locale"] == "fr-FR"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_directory_windows_path(respx_stash_client: StashClient) -> None:
    """Test directory query with Windows path."""
    directory_data = create_directory_result(
        path="C:\\Users\\Admin\\Videos",
        parent="C:\\Users\\Admin",
        directories=["Movies", "Clips"],
    )
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("directory", directory_data)
            )
        ]
    )

    result = await respx_stash_client.directory(path="C:\\Users\\Admin\\Videos")

    assert result is not None
    assert result.path == "C:\\Users\\Admin\\Videos"
    assert result.parent == "C:\\Users\\Admin"
    assert len(graphql_route.calls) == 1

    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["path"] == "C:\\Users\\Admin\\Videos"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_directory_error(respx_stash_client: StashClient) -> None:
    """Test directory query error handling."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "errors": [
                        {"message": "Directory not found", "path": ["directory"]}
                    ]
                },
            )
        ]
    )

    with pytest.raises(StashGraphQLError, match="Directory not found"):
        await respx_stash_client.directory(path="/nonexistent/path")


@pytest.mark.asyncio
@pytest.mark.unit
async def test_directory_server_error(respx_stash_client: StashClient) -> None:
    """Test directory query with server error."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    with pytest.raises(StashGraphQLError, match="Server error"):
        await respx_stash_client.directory(path="/some/path")


@pytest.mark.asyncio
@pytest.mark.unit
async def test_directory_permission_error(respx_stash_client: StashClient) -> None:
    """Test directory query with permission denied error."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "errors": [
                        {
                            "message": "Permission denied",
                            "path": ["directory"],
                            "extensions": {"code": "PERMISSION_DENIED"},
                        }
                    ]
                },
            )
        ]
    )

    with pytest.raises(StashGraphQLError, match="Permission denied"):
        await respx_stash_client.directory(path="/root/protected")


@pytest.mark.asyncio
@pytest.mark.unit
async def test_directory_special_characters_in_path(
    respx_stash_client: StashClient,
) -> None:
    """Test directory with special characters in path."""
    directory_data = create_directory_result(
        path="/media/files & folders/user's stuff",
        parent="/media/files & folders",
        directories=["folder (1)", "folder [2]"],
    )
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("directory", directory_data)
            )
        ]
    )

    result = await respx_stash_client.directory(
        path="/media/files & folders/user's stuff"
    )

    assert result is not None
    assert result.path == "/media/files & folders/user's stuff"
    assert len(graphql_route.calls) == 1

    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["path"] == "/media/files & folders/user's stuff"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_directory_network_path(respx_stash_client: StashClient) -> None:
    """Test directory query with UNC/network path."""
    directory_data = create_directory_result(
        path="\\\\server\\share\\videos",
        parent="\\\\server\\share",
        directories=["backup", "archive"],
    )
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("directory", directory_data)
            )
        ]
    )

    result = await respx_stash_client.directory(path="\\\\server\\share\\videos")

    assert result is not None
    assert result.path == "\\\\server\\share\\videos"
    assert result.parent == "\\\\server\\share"
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_directory_unicode_path(respx_stash_client: StashClient) -> None:
    """Test directory with Unicode characters in path."""
    directory_data = create_directory_result(
        path="/home/用户/视频",
        parent="/home/用户",
        directories=["电影", "短片"],
    )
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("directory", directory_data)
            )
        ]
    )

    result = await respx_stash_client.directory(path="/home/用户/视频")

    assert result is not None
    assert result.path == "/home/用户/视频"
    assert result.parent == "/home/用户"
    assert is_set(result.directories)
    assert "电影" in result.directories
    assert len(graphql_route.calls) == 1
