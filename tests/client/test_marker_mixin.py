"""Unit tests for MarkerClientMixin.

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
    BulkSceneMarkerUpdateInput,
    BulkUpdateIds,
    Scene,
    SceneMarker,
    Tag,
)
from tests.fixtures import (
    create_find_markers_result,
    create_graphql_response,
    create_marker_dict,
    create_scene_dict,
    create_tag_dict,
)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_marker(respx_stash_client: StashClient) -> None:
    """Test finding a marker by ID."""
    scene_data = create_scene_dict(id="scene_123", title="Test Scene")
    tag_data = create_tag_dict(id="tag_123", name="Intro")
    marker_data = create_marker_dict(
        id="123",
        title="Chapter 1",
        seconds=30.5,
        scene=scene_data,
        primary_tag=tag_data,
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findSceneMarkers",
                    create_find_markers_result(count=1, scene_markers=[marker_data]),
                ),
            )
        ]
    )

    marker = await respx_stash_client.find_marker("123")

    # Verify the result
    assert marker is not None
    assert marker.id == "123"
    assert marker.title == "Chapter 1"
    assert marker.seconds == 30.5

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "findSceneMarkers" in req["query"]
    assert req["variables"]["id"] == "123"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_marker_not_found(respx_stash_client: StashClient) -> None:
    """Test finding a marker that doesn't exist."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findSceneMarkers",
                    create_find_markers_result(count=0, scene_markers=[]),
                ),
            )
        ]
    )

    marker = await respx_stash_client.find_marker("999")

    assert marker is None

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_marker_empty_result(respx_stash_client: StashClient) -> None:
    """Test finding a marker when query succeeds but scene_markers array is empty.

    This specifically tests the branch where findSceneMarkers returns a valid
    response structure but with an empty scene_markers array (32->36 branch).
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "data": {
                        "findSceneMarkers": {
                            "scene_markers": []  # Valid response, empty array
                        }
                    }
                },
            )
        ]
    )

    marker = await respx_stash_client.find_marker("999")

    assert marker is None

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_marker_error_returns_none(respx_stash_client: StashClient) -> None:
    """Test handling errors when finding a marker returns None."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(500, json={"errors": [{"message": "Test error"}]})]
    )

    marker = await respx_stash_client.find_marker("error_marker")

    assert marker is None

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_markers(respx_stash_client: StashClient) -> None:
    """Test finding markers with filters."""
    marker_data = create_marker_dict(
        id="123",
        title="Test Marker",
        seconds=10.0,
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findSceneMarkers",
                    create_find_markers_result(count=1, scene_markers=[marker_data]),
                ),
            )
        ]
    )

    result = await respx_stash_client.find_markers()

    # Verify the results
    assert result.count == 1
    assert len(result.scene_markers) == 1
    assert result.scene_markers[0].id == "123"
    assert result.scene_markers[0].title == "Test Marker"

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "findSceneMarkers" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_markers_empty(respx_stash_client: StashClient) -> None:
    """Test finding markers when none exist."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findSceneMarkers",
                    create_find_markers_result(count=0, scene_markers=[]),
                ),
            )
        ]
    )

    result = await respx_stash_client.find_markers()

    assert result.count == 0
    assert len(result.scene_markers) == 0

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_markers_with_filter(respx_stash_client: StashClient) -> None:
    """Test finding markers with custom filter parameters."""
    marker_data = create_marker_dict(id="123", title="Filtered Marker")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findSceneMarkers",
                    create_find_markers_result(count=1, scene_markers=[marker_data]),
                ),
            )
        ]
    )

    result = await respx_stash_client.find_markers(filter_={"per_page": 10, "page": 1})

    assert result.count == 1
    assert result.scene_markers[0].title == "Filtered Marker"

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["filter"]["per_page"] == 10
    assert req["variables"]["filter"]["page"] == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_markers_with_query(respx_stash_client: StashClient) -> None:
    """Test finding markers with search query."""
    marker_data = create_marker_dict(id="123", title="Search Result Marker")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findSceneMarkers",
                    create_find_markers_result(count=1, scene_markers=[marker_data]),
                ),
            )
        ]
    )

    result = await respx_stash_client.find_markers(q="Search Result")

    assert result.count == 1
    assert result.scene_markers[0].title == "Search Result Marker"

    # Verify GraphQL call includes q parameter
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["filter"]["q"] == "Search Result"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_markers_with_marker_filter(respx_stash_client: StashClient) -> None:
    """Test finding markers with marker-specific filter."""
    marker_data = create_marker_dict(id="123", title="Tagged Marker")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findSceneMarkers",
                    create_find_markers_result(count=1, scene_markers=[marker_data]),
                ),
            )
        ]
    )

    result = await respx_stash_client.find_markers(
        marker_filter={"tags": {"value": ["tag_123"], "modifier": "INCLUDES"}}
    )

    assert result.count == 1

    # Verify GraphQL call includes marker_filter
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["marker_filter"]["tags"]["value"] == ["tag_123"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_markers_error_returns_empty(
    respx_stash_client: StashClient,
) -> None:
    """Test that find_markers returns empty result on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    result = await respx_stash_client.find_markers()

    assert result.count == 0
    assert len(result.scene_markers) == 0

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_marker_with_tags(respx_stash_client: StashClient) -> None:
    """Test finding a marker with tags."""
    tag_data = [
        create_tag_dict(id="tag_1", name="Tag 1"),
        create_tag_dict(id="tag_2", name="Tag 2"),
    ]
    primary_tag = create_tag_dict(id="primary_tag", name="Primary")
    marker_data = create_marker_dict(
        id="123",
        title="Marker with Tags",
        primary_tag=primary_tag,
        tags=tag_data,
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findSceneMarkers",
                    create_find_markers_result(count=1, scene_markers=[marker_data]),
                ),
            )
        ]
    )

    marker = await respx_stash_client.find_marker("123")

    assert marker is not None
    assert marker.primary_tag is not None
    assert marker.primary_tag.id == "primary_tag"
    assert len(marker.tags) == 2
    assert marker.tags[0].id == "tag_1"
    assert marker.tags[1].id == "tag_2"

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_marker_tags(respx_stash_client: StashClient) -> None:
    """Test getting scene marker tags for a scene."""
    marker_tags_data = [
        {
            "tag": create_tag_dict(id="tag_1", name="Intro"),
            "scene_markers": [create_marker_dict(id="m1", title="Intro Start")],
        },
        {
            "tag": create_tag_dict(id="tag_2", name="Outro"),
            "scene_markers": [create_marker_dict(id="m2", title="Outro Start")],
        },
    ]

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("sceneMarkerTags", marker_tags_data)
            )
        ]
    )

    result = await respx_stash_client.scene_marker_tags("scene_123")

    # Verify the results
    assert len(result) == 2
    assert result[0]["tag"]["id"] == "tag_1"
    assert result[1]["tag"]["id"] == "tag_2"

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "sceneMarkerTags" in req["query"]
    assert req["variables"]["scene_id"] == "scene_123"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_marker_tags_error_returns_empty(
    respx_stash_client: StashClient,
) -> None:
    """Test that scene_marker_tags returns empty list on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    result = await respx_stash_client.scene_marker_tags("scene_123")

    assert result == []

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_marker_destroy(respx_stash_client: StashClient) -> None:
    """Test destroying a scene marker."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("sceneMarkerDestroy", True)
            )
        ]
    )

    result = await respx_stash_client.scene_marker_destroy("123")

    assert result is True

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "sceneMarkerDestroy" in req["query"]
    assert req["variables"]["id"] == "123"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_markers_destroy(respx_stash_client: StashClient) -> None:
    """Test destroying multiple scene markers."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("sceneMarkersDestroy", True)
            )
        ]
    )

    result = await respx_stash_client.scene_markers_destroy(["123", "456", "789"])

    assert result is True

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "sceneMarkersDestroy" in req["query"]
    assert req["variables"]["ids"] == ["123", "456", "789"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_marker_destroy_error_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test that scene_marker_destroy raises on error.

    This covers lines 175-177: exception handling in scene_marker_destroy.
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    with pytest.raises(StashGraphQLError):
        await respx_stash_client.scene_marker_destroy("123")

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_markers_destroy_error_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test that scene_markers_destroy raises on error.

    This covers lines 199-201: exception handling in scene_markers_destroy.
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    with pytest.raises(StashGraphQLError):
        await respx_stash_client.scene_markers_destroy(["123", "456"])

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_marker(respx_stash_client: StashClient) -> None:
    """Test creating a new scene marker."""
    # Mock response for created marker
    created_marker_data = create_marker_dict(
        id="new_marker_123",
        title="New Chapter",
        seconds=45.0,
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response("sceneMarkerCreate", created_marker_data),
            )
        ]
    )

    # Create a new marker object using .new() to properly set _is_new=True
    scene = Scene(id="scene_123", title="Test Scene")
    primary_tag = Tag(id="tag_123", name="Chapter")
    marker = SceneMarker.new(
        title="New Chapter",
        seconds=45.0,
        scene=scene,
        primary_tag=primary_tag,
        tags=[],
        stream="/stream/marker",
        preview="/preview/marker.jpg",
        screenshot="/screenshot/marker.jpg",
    )

    result = await respx_stash_client.create_marker(marker)

    # Verify the result
    assert result is not None
    assert result.id == "new_marker_123"
    assert result.title == "New Chapter"
    assert result.seconds == 45.0

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "sceneMarkerCreate" in req["query"]
    assert req["variables"]["input"]["title"] == "New Chapter"
    assert req["variables"]["input"]["seconds"] == 45.0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_marker_error_raises(respx_stash_client: StashClient) -> None:
    """Test that create_marker raises on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    scene = Scene(id="scene_123", title="Test Scene")
    primary_tag = Tag(id="tag_123", name="Chapter")
    marker = SceneMarker(
        id="new",
        title="Fail Marker",
        seconds=0.0,
        scene=scene,
        primary_tag=primary_tag,
        tags=[],
        stream="/stream/marker",
        preview="/preview/marker.jpg",
        screenshot="/screenshot/marker.jpg",
    )

    with pytest.raises(StashGraphQLError):
        await respx_stash_client.create_marker(marker)

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_marker(respx_stash_client: StashClient) -> None:
    """Test updating an existing scene marker."""
    # Mock response for updated marker
    updated_marker_data = create_marker_dict(
        id="marker_123",
        title="Updated Chapter",
        seconds=60.0,
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response("sceneMarkerUpdate", updated_marker_data),
            )
        ]
    )

    # Create an existing marker object and modify it
    scene = Scene(id="scene_123", title="Test Scene")
    primary_tag = Tag(id="tag_123", name="Chapter")
    marker = SceneMarker(
        id="marker_123",
        title="Original Chapter",
        seconds=45.0,
        scene=scene,
        primary_tag=primary_tag,
        tags=[],
        stream="/stream/marker",
        preview="/preview/marker.jpg",
        screenshot="/screenshot/marker.jpg",
    )

    # Modify the marker to trigger dirty tracking
    marker.title = "Updated Chapter"
    marker.seconds = 60.0

    result = await respx_stash_client.update_marker(marker)

    # Verify the result
    assert result is not None
    assert result.id == "marker_123"
    assert result.title == "Updated Chapter"
    assert result.seconds == 60.0

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "sceneMarkerUpdate" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_marker_error_raises(respx_stash_client: StashClient) -> None:
    """Test that update_marker raises on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    scene = Scene(id="scene_123", title="Test Scene")
    primary_tag = Tag(id="tag_123", name="Chapter")
    marker = SceneMarker(
        id="marker_123",
        title="Fail Marker",
        seconds=0.0,
        scene=scene,
        primary_tag=primary_tag,
        tags=[],
        stream="/stream/marker",
        preview="/preview/marker.jpg",
        screenshot="/screenshot/marker.jpg",
    )
    marker.title = "Updated Title"

    with pytest.raises(StashGraphQLError):
        await respx_stash_client.update_marker(marker)

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_bulk_scene_marker_update_with_dict(
    respx_stash_client: StashClient,
) -> None:
    """Test bulk updating scene markers with a dict input.

    This covers line 241-242: else branch when input_data is a dict.
    """
    updated_markers_data = [
        create_marker_dict(id="m1", title="Updated Marker 1", seconds=10.0),
        create_marker_dict(id="m2", title="Updated Marker 2", seconds=20.0),
        create_marker_dict(id="m3", title="Updated Marker 3", seconds=30.0),
    ]

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "bulkSceneMarkerUpdate", updated_markers_data
                ),
            )
        ]
    )

    # Use a dict input (the else branch)
    input_dict = {
        "ids": ["m1", "m2", "m3"],
        "title": "Updated Marker",
    }

    result = await respx_stash_client.bulk_scene_marker_update(input_dict)

    # Verify the results
    assert len(result) == 3
    assert result[0].id == "m1"
    assert result[1].id == "m2"
    assert result[2].id == "m3"

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "bulkSceneMarkerUpdate" in req["query"]
    assert req["variables"]["input"]["ids"] == ["m1", "m2", "m3"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_bulk_scene_marker_update_with_input_type(
    respx_stash_client: StashClient,
) -> None:
    """Test bulk updating scene markers with BulkSceneMarkerUpdateInput Pydantic model.

    This covers line 239-240: if isinstance(input_data, BulkSceneMarkerUpdateInput).
    """
    updated_markers_data = [
        create_marker_dict(id="m1", title="Updated Marker 1", seconds=10.0),
        create_marker_dict(id="m2", title="Updated Marker 2", seconds=20.0),
    ]

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "bulkSceneMarkerUpdate", updated_markers_data
                ),
            )
        ]
    )

    # Use the Pydantic model input (triggers the isinstance branch)
    input_data = BulkSceneMarkerUpdateInput(
        ids=["m1", "m2"],
        title="Updated Title",
        tag_ids=BulkUpdateIds(ids=["tag1", "tag2"], mode="ADD"),
    )

    result = await respx_stash_client.bulk_scene_marker_update(input_data)

    # Verify the results
    assert len(result) == 2
    assert result[0].id == "m1"
    assert result[1].id == "m2"

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "bulkSceneMarkerUpdate" in req["query"]
    assert req["variables"]["input"]["ids"] == ["m1", "m2"]
    assert req["variables"]["input"]["title"] == "Updated Title"
    assert req["variables"]["input"]["tag_ids"]["ids"] == [
        "tag1",
        "tag2",
    ]  # Schema uses snake_case


@pytest.mark.asyncio
@pytest.mark.unit
async def test_bulk_scene_marker_update_error_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test that bulk_scene_marker_update raises on error.

    This covers lines 251-253: exception handling in bulk_scene_marker_update.
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    input_data = BulkSceneMarkerUpdateInput(
        ids=["m1", "m2"],
        title="Will Fail",
    )

    with pytest.raises(StashGraphQLError):
        await respx_stash_client.bulk_scene_marker_update(input_data)

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_marker_wall(respx_stash_client: StashClient) -> None:
    """Test getting marker wall."""
    marker_data = [
        {"id": "m1", "title": "Marker 1", "seconds": 10.0},
        {"id": "m2", "title": "Marker 2", "seconds": 20.0},
    ]

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(200, json={"data": {"markerWall": marker_data}})]
    )

    markers = await respx_stash_client.marker_wall(q="test")

    assert len(markers) == 2
    assert markers[0].id == "m1"
    assert markers[1].id == "m2"
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_marker_wall_error_returns_empty(respx_stash_client: StashClient) -> None:
    """Test that marker_wall returns empty list on error."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    markers = await respx_stash_client.marker_wall(q="test")

    assert markers == []


@pytest.mark.asyncio
@pytest.mark.unit
async def test_marker_strings(respx_stash_client: StashClient) -> None:
    """Test getting marker strings."""
    strings_data = [
        {"id": "bj", "title": "BJ", "count": 5},
        {"id": "hj", "title": "HJ", "count": 3},
    ]

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json={"data": {"markerStrings": strings_data}})
        ]
    )

    strings = await respx_stash_client.marker_strings(q="test", sort="count")

    assert len(strings) == 2
    assert strings[0].id == "bj"
    assert strings[0].count == 5
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_marker_strings_error_returns_empty(
    respx_stash_client: StashClient,
) -> None:
    """Test that marker_strings returns empty list on error."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    strings = await respx_stash_client.marker_strings(q="test")

    assert strings == []


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_markers_none_result_returns_empty(
    respx_stash_client: StashClient,
) -> None:
    """Test find_markers returns empty result when GraphQL returns findSceneMarkers: null.

    This covers line 78 in marker.py - the return when result.get("findSceneMarkers") is falsy.
    The response has the findSceneMarkers key, but with a null value.
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "data": {"findSceneMarkers": None}
                },  # Key exists but value is None
            )
        ]
    )

    result = await respx_stash_client.find_markers()

    assert result.count == 0
    assert result.scene_markers == []
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_marker_null_find_scene_markers_returns_none(
    respx_stash_client: StashClient,
) -> None:
    """Test find_marker returns None when findSceneMarkers is null.

    This covers line 32 in marker.py - the branch where result exists but
    result.get("findSceneMarkers") is falsy (None).
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "data": {"findSceneMarkers": None}
                },  # Key exists but value is None
            )
        ]
    )

    marker = await respx_stash_client.find_marker("123")

    assert marker is None
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_marker_null_result_returns_none(
    respx_stash_client: StashClient,
) -> None:
    """Test find_marker returns None when data itself is null.

    This covers line 32 in marker.py - the branch where result is falsy (None).
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json={"data": None},  # Entire data is None
            )
        ]
    )

    marker = await respx_stash_client.find_marker("123")

    assert marker is None
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_markers_null_result_returns_empty(
    respx_stash_client: StashClient,
) -> None:
    """Test find_markers returns empty result when data itself is null.

    This covers line 76 in marker.py - the branch where result is falsy (None).
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json={"data": None},  # Entire data is None
            )
        ]
    )

    result = await respx_stash_client.find_markers()

    assert result.count == 0
    assert result.scene_markers == []
    assert len(graphql_route.calls) == 1
