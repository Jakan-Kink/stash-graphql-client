"""Unit tests for SceneClientMixin.

These tests mock at the HTTP boundary using respx, allowing real code execution
through the entire GraphQL client stack including serialization/deserialization.
"""

import json

import httpx
import pytest
import respx

from stash_graphql_client import StashClient
from stash_graphql_client.types import (
    Scene,
    SceneDestroyInput,
    SceneMergeInput,
    ScenesDestroyInput,
)
from tests.fixtures import (
    create_find_scenes_result,
    create_graphql_response,
    create_performer_dict,
    create_scene_dict,
    create_studio_dict,
    create_tag_dict,
)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_scene(respx_stash_client: StashClient) -> None:
    """Test finding a scene by ID."""
    scene_data = create_scene_dict(
        id="123",
        title="Test Scene",
        urls=["https://example.com/scene"],
        details="Test scene details",
        date="2024-01-15",
        organized=True,
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("findScene", scene_data))
        ]
    )

    scene = await respx_stash_client.find_scene("123")

    # Verify the result
    assert scene is not None
    assert scene.id == "123"
    assert scene.title == "Test Scene"
    assert scene.urls == ["https://example.com/scene"]
    assert scene.organized is True

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "findScene" in req["query"]
    assert req["variables"]["id"] == "123"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_scene_not_found(respx_stash_client: StashClient) -> None:
    """Test finding a scene that doesn't exist."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("findScene", None))
        ]
    )

    scene = await respx_stash_client.find_scene("999")

    assert scene is None

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_scene_empty_id_raises_value_error(
    respx_stash_client: StashClient,
) -> None:
    """Test that find_scene raises ValueError for empty ID."""
    with pytest.raises(ValueError, match="Scene ID cannot be empty"):
        await respx_stash_client.find_scene("")


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_scene_none_id_raises_value_error(
    respx_stash_client: StashClient,
) -> None:
    """Test that find_scene raises ValueError for None ID."""
    with pytest.raises(ValueError, match="Scene ID cannot be empty"):
        await respx_stash_client.find_scene(None)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_scene_error_returns_none(respx_stash_client: StashClient) -> None:
    """Test handling errors when finding a scene returns None."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(500, json={"errors": [{"message": "Test error"}]})]
    )

    scene = await respx_stash_client.find_scene("99999")

    assert scene is None

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_scenes(respx_stash_client: StashClient) -> None:
    """Test finding scenes with filters."""
    scene_data = create_scene_dict(
        id="123",
        title="Test Scene",
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findScenes",
                    create_find_scenes_result(
                        count=1, scenes=[scene_data], duration=120.5, filesize=1024000
                    ),
                ),
            )
        ]
    )

    result = await respx_stash_client.find_scenes()

    # Verify the results
    assert result.count == 1
    assert len(result.scenes) == 1
    assert result.scenes[0].id == "123"
    assert result.scenes[0].title == "Test Scene"
    assert result.duration == 120.5
    assert result.filesize == 1024000

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "findScenes" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_scenes_empty(respx_stash_client: StashClient) -> None:
    """Test finding scenes when none exist."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findScenes",
                    create_find_scenes_result(count=0, scenes=[]),
                ),
            )
        ]
    )

    result = await respx_stash_client.find_scenes()

    assert result.count == 0
    assert len(result.scenes) == 0

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_scenes_with_filter(respx_stash_client: StashClient) -> None:
    """Test finding scenes with custom filter parameters."""
    scene_data = create_scene_dict(id="123", title="Filtered Scene")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findScenes",
                    create_find_scenes_result(count=1, scenes=[scene_data]),
                ),
            )
        ]
    )

    result = await respx_stash_client.find_scenes(filter_={"per_page": 10, "page": 1})

    assert result.count == 1
    assert result.scenes[0].title == "Filtered Scene"

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["filter"]["per_page"] == 10
    assert req["variables"]["filter"]["page"] == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_scenes_with_query(respx_stash_client: StashClient) -> None:
    """Test finding scenes with search query."""
    scene_data = create_scene_dict(id="123", title="Search Result Scene")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findScenes",
                    create_find_scenes_result(count=1, scenes=[scene_data]),
                ),
            )
        ]
    )

    result = await respx_stash_client.find_scenes(q="Search Result")

    assert result.count == 1
    assert result.scenes[0].title == "Search Result Scene"

    # Verify GraphQL call includes q parameter
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["filter"]["q"] == "Search Result"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_scenes_with_scene_filter(respx_stash_client: StashClient) -> None:
    """Test finding scenes with scene-specific filter."""
    scene_data = create_scene_dict(id="123", title="Organized Scene", organized=True)

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findScenes",
                    create_find_scenes_result(count=1, scenes=[scene_data]),
                ),
            )
        ]
    )

    result = await respx_stash_client.find_scenes(scene_filter={"organized": True})

    assert result.count == 1
    assert result.scenes[0].organized is True

    # Verify GraphQL call includes scene_filter
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["scene_filter"]["organized"] is True


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_scenes_error_returns_empty(respx_stash_client: StashClient) -> None:
    """Test that find_scenes returns empty result on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    result = await respx_stash_client.find_scenes()

    assert result.count == 0
    assert len(result.scenes) == 0
    assert result.duration == 0
    assert result.filesize == 0

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_scene_with_studio(respx_stash_client: StashClient) -> None:
    """Test finding a scene with studio relationship."""
    studio_data = create_studio_dict(id="studio_123", name="Test Studio")
    scene_data = create_scene_dict(
        id="123",
        title="Scene with Studio",
        studio=studio_data,
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("findScene", scene_data))
        ]
    )

    scene = await respx_stash_client.find_scene("123")

    assert scene is not None
    assert scene.studio is not None
    assert scene.studio.id == "studio_123"
    assert scene.studio.name == "Test Studio"

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_scene_with_performers(respx_stash_client: StashClient) -> None:
    """Test finding a scene with performers."""
    performer_data = [
        create_performer_dict(id="perf_1", name="Performer 1"),
        create_performer_dict(id="perf_2", name="Performer 2"),
    ]
    scene_data = create_scene_dict(
        id="123",
        title="Scene with Performers",
        performers=performer_data,
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("findScene", scene_data))
        ]
    )

    scene = await respx_stash_client.find_scene("123")

    assert scene is not None
    assert len(scene.performers) == 2
    assert scene.performers[0].id == "perf_1"
    assert scene.performers[1].id == "perf_2"

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_scene_with_tags(respx_stash_client: StashClient) -> None:
    """Test finding a scene with tags."""
    tag_data = [
        create_tag_dict(id="tag_1", name="Tag 1"),
        create_tag_dict(id="tag_2", name="Tag 2"),
    ]
    scene_data = create_scene_dict(
        id="123",
        title="Scene with Tags",
        tags=tag_data,
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("findScene", scene_data))
        ]
    )

    scene = await respx_stash_client.find_scene("123")

    assert scene is not None
    assert len(scene.tags) == 2
    assert scene.tags[0].id == "tag_1"
    assert scene.tags[1].id == "tag_2"

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_duplicate_scenes(respx_stash_client: StashClient) -> None:
    """Test finding duplicate scenes."""
    # Create groups of duplicate scenes
    group1 = [
        create_scene_dict(id="123", title="Scene 1"),
        create_scene_dict(id="456", title="Scene 1 Copy"),
    ]
    group2 = [
        create_scene_dict(id="789", title="Scene 2"),
        create_scene_dict(id="101", title="Scene 2 Copy"),
    ]

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response("findDuplicateScenes", [group1, group2]),
            )
        ]
    )

    result = await respx_stash_client.find_duplicate_scenes()

    # Verify the results - should be list of lists
    assert len(result) == 2
    assert len(result[0]) == 2
    assert len(result[1]) == 2

    # Each item should be a Scene object
    assert isinstance(result[0][0], Scene)
    assert result[0][0].id == "123"
    assert result[0][1].id == "456"

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "findDuplicateScenes" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_duplicate_scenes_with_params(
    respx_stash_client: StashClient,
) -> None:
    """Test finding duplicate scenes with custom parameters."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response("findDuplicateScenes", []),
            )
        ]
    )

    result = await respx_stash_client.find_duplicate_scenes(
        distance=10, duration_diff=5.0
    )

    assert result == []

    # Verify GraphQL call includes parameters
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["distance"] == 10
    assert req["variables"]["duration_diff"] == 5.0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_duplicate_scenes_error_returns_empty(
    respx_stash_client: StashClient,
) -> None:
    """Test that find_duplicate_scenes returns empty list on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    result = await respx_stash_client.find_duplicate_scenes()

    assert result == []

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_wall(respx_stash_client: StashClient) -> None:
    """Test getting random scenes for the wall."""
    scenes_data = [
        create_scene_dict(id="123", title="Scene 1"),
        create_scene_dict(id="456", title="Scene 2"),
        create_scene_dict(id="789", title="Scene 3"),
    ]

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response("sceneWall", scenes_data),
            )
        ]
    )

    result = await respx_stash_client.scene_wall()

    # Verify the results
    assert len(result) == 3
    assert all(isinstance(s, Scene) for s in result)
    assert result[0].id == "123"
    assert result[1].id == "456"
    assert result[2].id == "789"

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "sceneWall" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_wall_with_query(respx_stash_client: StashClient) -> None:
    """Test getting random scenes with search query."""
    scenes_data = [
        create_scene_dict(id="123", title="Matching Scene"),
    ]

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response("sceneWall", scenes_data),
            )
        ]
    )

    result = await respx_stash_client.scene_wall(q="Matching")

    assert len(result) == 1
    assert result[0].title == "Matching Scene"

    # Verify GraphQL call includes q parameter
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["q"] == "Matching"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_wall_error_returns_empty(respx_stash_client: StashClient) -> None:
    """Test that scene_wall returns empty list on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    result = await respx_stash_client.scene_wall()

    assert result == []

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_parse_scene_filenames(respx_stash_client: StashClient) -> None:
    """Test parsing scene filenames."""
    parse_result = {
        "count": 2,
        "results": [
            {"scene": {"id": "123"}, "title": "Parsed Title 1"},
            {"scene": {"id": "456"}, "title": "Parsed Title 2"},
        ],
    }

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response("parseSceneFilenames", parse_result),
            )
        ]
    )

    result = await respx_stash_client.parse_scene_filenames()

    # Verify the results
    assert result["count"] == 2
    assert len(result["results"]) == 2

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "parseSceneFilenames" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_parse_scene_filenames_with_config(
    respx_stash_client: StashClient,
) -> None:
    """Test parsing scene filenames with custom config."""
    parse_result = {"count": 0, "results": []}

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response("parseSceneFilenames", parse_result),
            )
        ]
    )

    result = await respx_stash_client.parse_scene_filenames(
        filter_={"q": "test"},
        config={"capitalizeTitle": True, "whitespace": False},
    )

    assert result == {"count": 0, "results": []}

    # Verify GraphQL call includes config
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["filter"]["q"] == "test"
    assert req["variables"]["config"]["capitalizeTitle"] is True
    assert req["variables"]["config"]["whitespace"] is False


@pytest.mark.asyncio
@pytest.mark.unit
async def test_parse_scene_filenames_error_returns_empty(
    respx_stash_client: StashClient,
) -> None:
    """Test that parse_scene_filenames returns empty dict on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    result = await respx_stash_client.parse_scene_filenames()

    assert result == {}

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_generate_screenshot(respx_stash_client: StashClient) -> None:
    """Test generating a scene screenshot."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "sceneGenerateScreenshot", "/path/to/screenshot.jpg"
                ),
            )
        ]
    )

    result = await respx_stash_client.scene_generate_screenshot("123", at=10.5)

    assert result == "/path/to/screenshot.jpg"

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "sceneGenerateScreenshot" in req["query"]
    assert req["variables"]["id"] == "123"
    assert req["variables"]["at"] == 10.5


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_generate_screenshot_without_timestamp(
    respx_stash_client: StashClient,
) -> None:
    """Test generating a scene screenshot without timestamp."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "sceneGenerateScreenshot", "/path/to/default.jpg"
                ),
            )
        ]
    )

    result = await respx_stash_client.scene_generate_screenshot("123")

    assert result == "/path/to/default.jpg"

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["at"] is None


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_scene_by_hash(respx_stash_client: StashClient) -> None:
    """Test finding a scene by hash."""
    scene_data = create_scene_dict(
        id="123",
        title="Found by Hash",
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("findSceneByHash", scene_data)
            )
        ]
    )

    result = await respx_stash_client.find_scene_by_hash({"checksum": "abc123def456"})

    assert result is not None
    assert result.id == "123"
    assert result.title == "Found by Hash"

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "findSceneByHash" in req["query"]
    assert req["variables"]["input"]["checksum"] == "abc123def456"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_scene_by_hash_not_found(respx_stash_client: StashClient) -> None:
    """Test finding a scene by hash that doesn't exist."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("findSceneByHash", None))
        ]
    )

    result = await respx_stash_client.find_scene_by_hash({"oshash": "xyz789"})

    assert result is None

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_scene_by_hash_error_returns_none(
    respx_stash_client: StashClient,
) -> None:
    """Test that find_scene_by_hash returns None on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    result = await respx_stash_client.find_scene_by_hash({"checksum": "test"})

    assert result is None

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_destroy(respx_stash_client: StashClient) -> None:
    """Test destroying a scene."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("sceneDestroy", True))
        ]
    )

    result = await respx_stash_client.scene_destroy({"id": "123"})

    assert result is True

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "sceneDestroy" in req["query"]
    assert req["variables"]["input"]["id"] == "123"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_destroy_with_options(respx_stash_client: StashClient) -> None:
    """Test destroying a scene with delete options."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("sceneDestroy", True))
        ]
    )

    result = await respx_stash_client.scene_destroy(
        {"id": "123", "delete_file": True, "delete_generated": False}
    )

    assert result is True

    # Verify GraphQL call includes options
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["input"]["delete_file"] is True
    assert req["variables"]["input"]["delete_generated"] is False


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scenes_destroy(respx_stash_client: StashClient) -> None:
    """Test destroying multiple scenes."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("scenesDestroy", True))
        ]
    )

    result = await respx_stash_client.scenes_destroy({"ids": ["123", "456", "789"]})

    assert result is True

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "scenesDestroy" in req["query"]
    assert req["variables"]["input"]["ids"] == ["123", "456", "789"]


# =============================================================================
# Create and Update tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_scene(respx_stash_client: StashClient, mock_scene) -> None:
    """Test creating a new scene."""
    created_scene_data = create_scene_dict(
        id="new_123",
        title="New Scene",
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("sceneCreate", created_scene_data)
            )
        ]
    )

    result = await respx_stash_client.create_scene(mock_scene)

    assert result is not None
    assert result.id == "new_123"
    assert result.title == "New Scene"

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "sceneCreate" in req["query"]
    assert "input" in req["variables"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_scene(respx_stash_client: StashClient, mock_scene) -> None:
    """Test updating an existing scene."""
    updated_scene_data = create_scene_dict(
        id="123",
        title="Updated Scene",
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("sceneUpdate", updated_scene_data)
            )
        ]
    )

    result = await respx_stash_client.update_scene(mock_scene)

    assert result is not None
    assert result.id == "123"
    assert result.title == "Updated Scene"

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "sceneUpdate" in req["query"]
    assert "input" in req["variables"]


# =============================================================================
# Error handling tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_scene_error(respx_stash_client: StashClient, mock_scene) -> None:
    """Test create_scene error handling."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json={"errors": [{"message": "Failed to create scene"}]}
            )
        ]
    )

    with pytest.raises(Exception, match="Failed to create scene"):
        await respx_stash_client.create_scene(mock_scene)

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_scene_error(respx_stash_client: StashClient, mock_scene) -> None:
    """Test update_scene error handling."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json={"errors": [{"message": "Failed to update scene"}]}
            )
        ]
    )

    with pytest.raises(Exception, match="Failed to update scene"):
        await respx_stash_client.update_scene(mock_scene)

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_scene_missing_id_error(respx_stash_client: StashClient) -> None:
    """Test update_scene raises error when response has no ID."""
    scene_without_id = create_scene_dict(id="123", title="Test")
    del scene_without_id["id"]

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("sceneUpdate", scene_without_id)
            )
        ]
    )

    scene = Scene(id="123", title="Test")

    with pytest.raises(Exception, match="sceneUpdate returned scene without ID"):
        await respx_stash_client.update_scene(scene)

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_bulk_scene_update_error(respx_stash_client: StashClient) -> None:
    """Test bulk_scene_update error handling."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json={"errors": [{"message": "Failed to bulk update"}]})
        ]
    )

    input_data = {
        "ids": ["1", "2"],
        "tag_ids": {"ids": ["tag1"], "mode": "ADD"},
    }

    with pytest.raises(Exception, match="Failed to bulk update"):
        await respx_stash_client.bulk_scene_update(input_data)

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scenes_update_error(respx_stash_client: StashClient) -> None:
    """Test scenes_update error handling."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json={"errors": [{"message": "Failed to update scenes"}]}
            )
        ]
    )

    scenes = [Scene(id="1", title="Scene 1"), Scene(id="2", title="Scene 2")]

    with pytest.raises(Exception, match="Failed to update scenes"):
        await respx_stash_client.scenes_update(scenes)

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_generate_screenshot_error(respx_stash_client: StashClient) -> None:
    """Test scene_generate_screenshot error handling."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json={"errors": [{"message": "Failed to generate screenshot"}]}
            )
        ]
    )

    with pytest.raises(Exception, match="Failed to generate screenshot"):
        await respx_stash_client.scene_generate_screenshot("123", at=10.5)

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_scene_by_hash_with_model_input(
    respx_stash_client: StashClient,
) -> None:
    """Test finding a scene by hash using SceneHashInput model."""
    from stash_graphql_client.types import SceneHashInput

    scene_data = create_scene_dict(id="123", title="Test Scene")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("findSceneByHash", scene_data)
            )
        ]
    )

    # Test with SceneHashInput model instead of dict
    input_data = SceneHashInput(checksum="abc123")
    scene = await respx_stash_client.find_scene_by_hash(input_data)

    assert scene is not None
    assert scene.id == "123"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "findSceneByHash" in req["query"]
    assert req["variables"]["input"]["checksum"] == "abc123"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_destroy_error(respx_stash_client: StashClient) -> None:
    """Test scene_destroy error handling."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json={"errors": [{"message": "Failed to delete scene"}]}
            )
        ]
    )

    with pytest.raises(Exception, match="Failed to delete scene"):
        await respx_stash_client.scene_destroy({"id": "123"})

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scenes_destroy_error(respx_stash_client: StashClient) -> None:
    """Test scenes_destroy error handling."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json={"errors": [{"message": "Failed to delete scenes"}]}
            )
        ]
    )

    with pytest.raises(Exception, match="Failed to delete scenes"):
        await respx_stash_client.scenes_destroy({"ids": ["123", "456"]})

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_merge(respx_stash_client: StashClient) -> None:
    """Test merging scenes."""
    from stash_graphql_client.types import SceneMergeInput

    merged_scene_data = create_scene_dict(id="123", title="Merged Scene")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("sceneMerge", merged_scene_data)
            )
        ]
    )

    input_data = SceneMergeInput(
        destination="123",
        source=["456", "789"],
    )

    scene = await respx_stash_client.scene_merge(input_data)

    assert scene is not None
    assert scene.id == "123"
    assert scene.title == "Merged Scene"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "sceneMerge" in req["query"]
    assert req["variables"]["input"]["destination"] == "123"
    assert req["variables"]["input"]["source"] == ["456", "789"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_merge_error(respx_stash_client: StashClient) -> None:
    """Test scene_merge error handling."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json={"errors": [{"message": "Failed to merge scenes"}]}
            )
        ]
    )

    input_data = SceneMergeInput(destination="123", source=["456"])

    with pytest.raises(Exception, match="Failed to merge scenes"):
        await respx_stash_client.scene_merge(input_data)

    assert len(graphql_route.calls) == 1


# =============================================================================
# Additional coverage tests for specific branches
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_bulk_scene_update_success(respx_stash_client: StashClient) -> None:
    """Test bulk updating scenes successfully.

    This covers line 470: successful bulk update returning list.
    """
    updated_scenes_data = [
        create_scene_dict(id="s1", title="Scene 1"),
        create_scene_dict(id="s2", title="Scene 2"),
        create_scene_dict(id="s3", title="Scene 3"),
    ]

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response("bulkSceneUpdate", updated_scenes_data),
            )
        ]
    )

    input_data = {
        "ids": ["s1", "s2", "s3"],
        "rating100": 80,
    }

    result = await respx_stash_client.bulk_scene_update(input_data)

    assert len(result) == 3
    assert result[0].id == "s1"
    assert result[1].id == "s2"
    assert result[2].id == "s3"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "bulkSceneUpdate" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scenes_update_success(respx_stash_client: StashClient) -> None:
    """Test updating multiple scenes with individual data successfully.

    This covers line 493: successful scenes update returning list.
    """
    updated_scenes_data = [
        create_scene_dict(id="s1", title="Updated Scene 1"),
        create_scene_dict(id="s2", title="Updated Scene 2"),
    ]

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("scenesUpdate", updated_scenes_data)
            )
        ]
    )

    scenes = [
        Scene(id="s1", title="Updated Scene 1"),
        Scene(id="s2", title="Updated Scene 2"),
    ]

    result = await respx_stash_client.scenes_update(scenes)

    assert len(result) == 2
    assert result[0].id == "s1"
    assert result[1].id == "s2"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "scenesUpdate" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_generate_screenshot_no_result_key(
    respx_stash_client: StashClient,
) -> None:
    """Test scene_generate_screenshot when result doesn't contain key.

    This covers line 527: return "" when sceneGenerateScreenshot not in result.
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(200, json={"data": {"otherField": "value"}})]
    )

    result = await respx_stash_client.scene_generate_screenshot("123")

    assert result == ""
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_destroy_with_input_type(respx_stash_client: StashClient) -> None:
    """Test destroying a scene with SceneDestroyInput.

    This covers line 650-651: if isinstance(input_data, SceneDestroyInput).
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("sceneDestroy", True))
        ]
    )

    input_data = SceneDestroyInput(id="123", delete_file=True, delete_generated=False)
    result = await respx_stash_client.scene_destroy(input_data)

    assert result is True

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "sceneDestroy" in req["query"]
    assert req["variables"]["input"]["id"] == "123"
    assert req["variables"]["input"]["delete_file"] is True
    assert req["variables"]["input"]["delete_generated"] is False


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scenes_destroy_with_input_type(respx_stash_client: StashClient) -> None:
    """Test destroying multiple scenes with ScenesDestroyInput.

    This covers line 718-719: if isinstance(input_data, ScenesDestroyInput).
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("scenesDestroy", True))
        ]
    )

    input_data = ScenesDestroyInput(
        ids=["123", "456", "789"],
        delete_file=False,
        delete_generated=True,
    )
    result = await respx_stash_client.scenes_destroy(input_data)

    assert result is True

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "scenesDestroy" in req["query"]
    assert req["variables"]["input"]["ids"] == ["123", "456", "789"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_merge_with_dict(respx_stash_client: StashClient) -> None:
    """Test merging scenes with dict input.

    This covers line 782-783: else branch when input_data is a dict.
    """
    merged_scene_data = create_scene_dict(id="dest", title="Merged Scene")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("sceneMerge", merged_scene_data)
            )
        ]
    )

    result = await respx_stash_client.scene_merge(
        {"source": ["src1", "src2"], "destination": "dest"}
    )

    assert result is not None
    assert result.id == "dest"
    assert result.title == "Merged Scene"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "sceneMerge" in req["query"]
