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
    SceneHashInput,
    SceneMergeInput,
    ScenesDestroyInput,
)
from stash_graphql_client.types.unset import is_set
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
        await respx_stash_client.find_scene(None)  # type: ignore[arg-type]


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
    assert isinstance(result.scenes, list)
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
    assert is_set(result.scenes)
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
    assert is_set(result.scenes)
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
    assert is_set(result.scenes)
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
    assert is_set(result.scenes)
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
    assert is_set(result.scenes)
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
    assert is_set(scene.studio)
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
    assert is_set(scene.performers)
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
    assert is_set(scene.tags)
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


# =============================================================================
# find_scenes_by_path_regex tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_scenes_by_path_regex(respx_stash_client: StashClient) -> None:
    """Test finding scenes by path regex.

    This covers lines 1091-1100: successful retrieval.
    """
    # Actual API response structure from findScenesByPathRegex
    result_data = {
        "count": 2,
        "duration": 240.5,
        "filesize": 1024000,
        "scenes": [
            create_scene_dict(id="s1", title="Scene 1", urls=[]),
            create_scene_dict(id="s2", title="Scene 2", urls=[]),
        ],
    }

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response("findScenesByPathRegex", result_data),
            )
        ]
    )

    result = await respx_stash_client.find_scenes_by_path_regex(
        filter_={"path": ".*test.*"}
    )

    # Verify FindScenesResultType structure
    assert result.count == 2
    assert result.duration == 240.5
    assert result.filesize == 1024000
    assert len(result.scenes) == 2
    assert result.scenes[0].id == "s1"
    assert result.scenes[0].title == "Scene 1"
    assert result.scenes[1].id == "s2"
    assert result.scenes[1].title == "Scene 2"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "findScenesByPathRegex" in req["query"]
    assert req["variables"]["filter"]["path"] == ".*test.*"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_scenes_by_path_regex_error_returns_empty(
    respx_stash_client: StashClient,
) -> None:
    """Test that find_scenes_by_path_regex returns empty result on error.

    This covers lines 1098-1100: exception handling.
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    result = await respx_stash_client.find_scenes_by_path_regex(
        filter_={"path": ".*test.*"}
    )

    assert result.count == 0
    assert result.duration == 0
    assert result.filesize == 0
    assert result.scenes == []
    assert len(graphql_route.calls) == 1


# =============================================================================
# scene_streams tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_streams(respx_stash_client: StashClient) -> None:
    """Test getting scene streaming endpoints."""
    streams_data = [
        {
            "url": "http://localhost:9999/scene/123/stream.mp4",
            "mime_type": "video/mp4",
            "label": "Direct stream",
        },
        {
            "url": "http://localhost:9999/scene/123/stream.webm",
            "mime_type": "video/webm",
            "label": "WebM stream",
        },
    ]

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response("sceneStreams", streams_data),
            )
        ]
    )

    result = await respx_stash_client.scene_streams("123")

    # Verify the results
    assert len(result) == 2
    assert result[0].url == "http://localhost:9999/scene/123/stream.mp4"
    assert result[0].mime_type == "video/mp4"
    assert result[0].label == "Direct stream"
    assert result[1].url == "http://localhost:9999/scene/123/stream.webm"
    assert result[1].mime_type == "video/webm"
    assert result[1].label == "WebM stream"

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "sceneStreams" in req["query"]
    assert req["variables"]["id"] == "123"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_streams_empty(respx_stash_client: StashClient) -> None:
    """Test getting scene streams when none exist."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response("sceneStreams", []),
            )
        ]
    )

    result = await respx_stash_client.scene_streams("456")

    assert result == []

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "sceneStreams" in req["query"]
    assert req["variables"]["id"] == "456"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_streams_error_returns_empty(
    respx_stash_client: StashClient,
) -> None:
    """Test that scene_streams returns empty list on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    result = await respx_stash_client.scene_streams("999")

    assert result == []

    assert len(graphql_route.calls) == 1


# =============================================================================
# Scene marker utility method tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_merge_scene_markers_single_source(
    respx_stash_client: StashClient,
) -> None:
    """Test merging markers from a single source scene to target scene."""
    # Mock finding markers from source scene
    source_markers = [
        {
            "id": "marker1",
            "title": "Marker 1",
            "seconds": 10.0,
            "scene": {"id": "source1"},
            "primary_tag": {"id": "tag1"},
            "tags": [{"id": "tag1"}, {"id": "tag2"}],
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        },
        {
            "id": "marker2",
            "title": "Marker 2",
            "seconds": 20.0,
            "scene": {"id": "source1"},
            "primary_tag": {"id": "tag2"},
            "tags": [{"id": "tag2"}],
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        },
    ]

    # Mock created markers on target scene
    created_marker1 = {
        "id": "new_marker1",
        "title": "Marker 1",
        "seconds": 10.0,
        "scene": {"id": "target"},
        "primary_tag": {"id": "tag1"},
        "tags": [{"id": "tag1"}, {"id": "tag2"}],
        "created_at": "2024-01-02T00:00:00Z",
        "updated_at": "2024-01-02T00:00:00Z",
    }
    created_marker2 = {
        "id": "new_marker2",
        "title": "Marker 2",
        "seconds": 20.0,
        "scene": {"id": "target"},
        "primary_tag": {"id": "tag2"},
        "tags": [{"id": "tag2"}],
        "created_at": "2024-01-02T00:00:00Z",
        "updated_at": "2024-01-02T00:00:00Z",
    }

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            # First call: find markers from source scene
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findSceneMarkers",
                    {"count": 2, "scene_markers": source_markers},
                ),
            ),
            # Second call: create first marker
            httpx.Response(
                200,
                json=create_graphql_response("sceneMarkerCreate", created_marker1),
            ),
            # Third call: create second marker
            httpx.Response(
                200,
                json=create_graphql_response("sceneMarkerCreate", created_marker2),
            ),
        ]
    )

    result = await respx_stash_client.merge_scene_markers("target", ["source1"])

    # Verify the results
    assert len(result) == 2
    assert result[0].id == "new_marker1"
    assert result[0].title == "Marker 1"
    assert result[0].seconds == 10.0
    assert result[1].id == "new_marker2"
    assert result[1].title == "Marker 2"
    assert result[1].seconds == 20.0

    # Verify GraphQL calls
    assert len(graphql_route.calls) == 3

    # Verify first call (find markers from source)
    req1 = json.loads(graphql_route.calls[0].request.content)
    assert "findSceneMarkers" in req1["query"]
    assert req1["variables"]["marker_filter"]["scene_id"]["value"] == ["source1"]

    # Verify second call (create first marker)
    req2 = json.loads(graphql_route.calls[1].request.content)
    assert "sceneMarkerCreate" in req2["query"]
    assert req2["variables"]["input"]["scene_id"] == "target"
    assert req2["variables"]["input"]["title"] == "Marker 1"
    assert req2["variables"]["input"]["seconds"] == 10.0
    assert req2["variables"]["input"]["primary_tag_id"] == "tag1"
    assert req2["variables"]["input"]["tag_ids"] == ["tag1", "tag2"]

    # Verify third call (create second marker)
    req3 = json.loads(graphql_route.calls[2].request.content)
    assert "sceneMarkerCreate" in req3["query"]
    assert req3["variables"]["input"]["scene_id"] == "target"
    assert req3["variables"]["input"]["title"] == "Marker 2"
    assert req3["variables"]["input"]["seconds"] == 20.0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_merge_scene_markers_multiple_sources(
    respx_stash_client: StashClient,
) -> None:
    """Test merging markers from multiple source scenes."""
    # Mock finding markers from both source scenes
    source1_markers = [
        {
            "id": "marker1",
            "title": "Source 1 Marker",
            "seconds": 10.0,
            "scene": {"id": "source1"},
            "primary_tag": {"id": "tag1"},
            "tags": [{"id": "tag1"}],
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        },
    ]

    source2_markers = [
        {
            "id": "marker2",
            "title": "Source 2 Marker",
            "seconds": 20.0,
            "scene": {"id": "source2"},
            "primary_tag": {"id": "tag2"},
            "tags": [{"id": "tag2"}],
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        },
    ]

    created_marker1 = {
        "id": "new1",
        "title": "Source 1 Marker",
        "seconds": 10.0,
        "scene": {"id": "target"},
        "primary_tag": {"id": "tag1"},
        "tags": [{"id": "tag1"}],
        "created_at": "2024-01-02T00:00:00Z",
        "updated_at": "2024-01-02T00:00:00Z",
    }

    created_marker2 = {
        "id": "new2",
        "title": "Source 2 Marker",
        "seconds": 20.0,
        "scene": {"id": "target"},
        "primary_tag": {"id": "tag2"},
        "tags": [{"id": "tag2"}],
        "created_at": "2024-01-02T00:00:00Z",
        "updated_at": "2024-01-02T00:00:00Z",
    }

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            # Find markers from source1
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findSceneMarkers",
                    {"count": 1, "scene_markers": source1_markers},
                ),
            ),
            # Create marker from source1
            httpx.Response(
                200,
                json=create_graphql_response("sceneMarkerCreate", created_marker1),
            ),
            # Find markers from source2
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findSceneMarkers",
                    {"count": 1, "scene_markers": source2_markers},
                ),
            ),
            # Create marker from source2
            httpx.Response(
                200,
                json=create_graphql_response("sceneMarkerCreate", created_marker2),
            ),
        ]
    )

    result = await respx_stash_client.merge_scene_markers(
        "target", ["source1", "source2"]
    )

    # Verify the results
    assert len(result) == 2
    assert result[0].title == "Source 1 Marker"
    assert result[1].title == "Source 2 Marker"

    # Verify we made the right number of calls
    assert len(graphql_route.calls) == 4


@pytest.mark.asyncio
@pytest.mark.unit
async def test_merge_scene_markers_no_markers_in_source(
    respx_stash_client: StashClient,
) -> None:
    """Test merging when source scene has no markers."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            # Find markers returns empty
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findSceneMarkers",
                    {"count": 0, "scene_markers": []},
                ),
            ),
        ]
    )

    result = await respx_stash_client.merge_scene_markers("target", ["source1"])

    # Should return empty list
    assert result == []

    # Verify we only called find_markers once
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_merge_scene_markers_error_handling(
    respx_stash_client: StashClient,
) -> None:
    """Test error handling when merging scene markers fails."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Database error"}]})
        ]
    )

    result = await respx_stash_client.merge_scene_markers("target", ["source1"])

    # Should return empty list on error
    assert result == []

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_duplicate_scenes_wrapper_default_params(
    respx_stash_client: StashClient,
) -> None:
    """Test find_duplicate_scenes_wrapper with default parameters."""
    # Create groups of duplicate scenes
    group1 = [
        create_scene_dict(id="1", title="Scene 1"),
        create_scene_dict(id="2", title="Scene 1 Duplicate"),
    ]

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response("findDuplicateScenes", [group1]),
            )
        ]
    )

    result = await respx_stash_client.find_duplicate_scenes_wrapper()

    # Verify results
    assert len(result) == 1
    assert len(result[0]) == 2
    assert result[0][0].id == "1"
    assert result[0][1].id == "2"

    # Verify GraphQL call with default parameters
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "findDuplicateScenes" in req["query"]
    # Check default distance parameter
    assert req["variables"]["distance"] == 0
    # Check that duration_diff is None by default
    assert req["variables"]["duration_diff"] is None


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_duplicate_scenes_wrapper_custom_distance(
    respx_stash_client: StashClient,
) -> None:
    """Test find_duplicate_scenes_wrapper with custom distance threshold."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response("findDuplicateScenes", []),
            )
        ]
    )

    result = await respx_stash_client.find_duplicate_scenes_wrapper(distance=10)

    assert result == []

    # Verify custom distance parameter
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["distance"] == 10


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_duplicate_scenes_wrapper_custom_duration_diff(
    respx_stash_client: StashClient,
) -> None:
    """Test find_duplicate_scenes_wrapper with custom duration difference."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response("findDuplicateScenes", []),
            )
        ]
    )

    result = await respx_stash_client.find_duplicate_scenes_wrapper(duration_diff=5.0)

    assert result == []

    # Verify custom duration_diff parameter
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["duration_diff"] == 5.0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_duplicate_scenes_wrapper_both_params(
    respx_stash_client: StashClient,
) -> None:
    """Test find_duplicate_scenes_wrapper with both custom parameters."""
    group1 = [
        create_scene_dict(id="1", title="Scene 1"),
        create_scene_dict(id="2", title="Scene 1 Similar"),
    ]
    group2 = [
        create_scene_dict(id="3", title="Scene 2"),
        create_scene_dict(id="4", title="Scene 2 Similar"),
    ]

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response("findDuplicateScenes", [group1, group2]),
            )
        ]
    )

    result = await respx_stash_client.find_duplicate_scenes_wrapper(
        distance=15, duration_diff=10.0
    )

    assert len(result) == 2
    assert len(result[0]) == 2
    assert len(result[1]) == 2

    # Verify both parameters
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["distance"] == 15
    assert req["variables"]["duration_diff"] == 10.0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_duplicate_scenes_wrapper_error_handling(
    respx_stash_client: StashClient,
) -> None:
    """Test error handling in find_duplicate_scenes_wrapper."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    result = await respx_stash_client.find_duplicate_scenes_wrapper()

    assert result == []

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_merge_scene_markers_with_end_seconds_and_no_tags(
    respx_stash_client: StashClient,
) -> None:
    """Test merging markers with end_seconds and no tags/primary_tag."""
    # Marker with end_seconds but no tags or primary_tag
    source_markers = [
        {
            "id": "marker1",
            "title": "Marker with end",
            "seconds": 10.0,
            "end_seconds": 15.0,
            "scene": {"id": "source1"},
            "primary_tag": None,
            "tags": None,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        },
    ]

    created_marker = {
        "id": "new1",
        "title": "Marker with end",
        "seconds": 10.0,
        "end_seconds": 15.0,
        "scene": {"id": "target"},
        "primary_tag": None,
        "tags": None,
        "created_at": "2024-01-02T00:00:00Z",
        "updated_at": "2024-01-02T00:00:00Z",
    }

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findSceneMarkers",
                    {"count": 1, "scene_markers": source_markers},
                ),
            ),
            httpx.Response(
                200,
                json=create_graphql_response("sceneMarkerCreate", created_marker),
            ),
        ]
    )

    result = await respx_stash_client.merge_scene_markers("target", ["source1"])

    assert len(result) == 1
    assert result[0].end_seconds == 15.0

    # Verify the create call included end_seconds but not tags
    assert len(graphql_route.calls) == 2
    req = json.loads(graphql_route.calls[1].request.content)
    assert req["variables"]["input"]["end_seconds"] == 15.0
    assert req["variables"]["input"]["tag_ids"] is None
    assert req["variables"]["input"]["primary_tag_id"] is None


@pytest.mark.asyncio
@pytest.mark.unit
async def test_merge_scene_markers_null_result(
    respx_stash_client: StashClient,
) -> None:
    """Test merging when findSceneMarkers returns null result.

    This covers line 1224: continue when result.get("findSceneMarkers") is None.
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            # Find markers returns null/empty response
            httpx.Response(200, json={"data": {}}),  # No "findSceneMarkers" key
        ]
    )

    result = await respx_stash_client.merge_scene_markers("target", ["source1"])

    # Should return empty list (skipped source due to null result)
    assert result == []

    # Verify we only called find_markers once
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_merge_scene_markers_without_end_seconds(
    respx_stash_client: StashClient,
) -> None:
    """Test merging markers without end_seconds.

    This covers lines 1252->1258 FALSE: when marker.end_seconds is None,
    the field is not included in marker_input.
    """
    # Marker without end_seconds
    source_markers = [
        {
            "id": "marker1",
            "title": "Marker without end",
            "seconds": 10.0,
            "end_seconds": None,  # None instead of a value
            "scene": {"id": "source1"},
            "primary_tag": {"id": "tag1", "name": "Test Tag"},
            "tags": [{"id": "tag1", "name": "Test Tag"}],
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        },
    ]

    created_marker = {
        "id": "new1",
        "title": "Marker without end",
        "seconds": 10.0,
        "end_seconds": None,
        "scene": {"id": "target"},
        "primary_tag": {"id": "tag1", "name": "Test Tag"},
        "tags": [{"id": "tag1", "name": "Test Tag"}],
        "created_at": "2024-01-02T00:00:00Z",
        "updated_at": "2024-01-02T00:00:00Z",
    }

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findSceneMarkers",
                    {"count": 1, "scene_markers": source_markers},
                ),
            ),
            httpx.Response(
                200,
                json=create_graphql_response("sceneMarkerCreate", created_marker),
            ),
        ]
    )

    result = await respx_stash_client.merge_scene_markers("target", ["source1"])

    assert len(result) == 1
    assert result[0].end_seconds is None

    # Verify the create call did NOT include end_seconds
    assert len(graphql_route.calls) == 2
    req = json.loads(graphql_route.calls[1].request.content)
    assert "end_seconds" not in req["variables"]["input"]  # Key should not be present
    assert req["variables"]["input"]["tag_ids"] == ["tag1"]
    assert req["variables"]["input"]["primary_tag_id"] == "tag1"
