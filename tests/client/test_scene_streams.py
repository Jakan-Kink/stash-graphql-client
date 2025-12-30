"""Unit tests for sceneStreams query operation.

These tests follow TDD approach - written BEFORE implementation exists.
Tests mock at the HTTP boundary using respx, allowing real code execution
through the entire GraphQL client stack including serialization/deserialization.

Schema Reference (schema/schema.graphql line 57):
    sceneStreams(id: ID!): [SceneStreamEndpoint!]!

Type Definition (schema/types/scene.graphql):
    type SceneStreamEndpoint {
        url: String!
        mime_type: String!
        label: String
    }
"""

import json

import httpx
import pytest
import respx

from stash_graphql_client import StashClient
from stash_graphql_client.types.unset import is_set
from tests.fixtures import create_graphql_response


def create_scene_stream_endpoint_dict(
    url: str,
    mime_type: str,
    label: str | None = None,
) -> dict:
    """Create a SceneStreamEndpoint dictionary for testing.

    Args:
        url: Stream URL (required)
        mime_type: MIME type of the stream (required)
        label: Optional label for the stream

    Returns:
        Dictionary matching SceneStreamEndpoint GraphQL type
    """
    return {
        "url": url,
        "mime_type": mime_type,
        "label": label,
    }


# =============================================================================
# Success Case Tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_streams_success_multiple_endpoints(
    respx_stash_client: StashClient,
) -> None:
    """Test sceneStreams with multiple stream endpoints.

    Verifies:
    - Query accepts scene ID parameter
    - Returns list of SceneStreamEndpoint objects
    - Each endpoint has url, mime_type, and label fields
    - GraphQL query is correctly constructed
    """
    stream_endpoints = [
        create_scene_stream_endpoint_dict(
            url="https://example.com/stream/scene_123/direct.mp4",
            mime_type="video/mp4",
            label="Direct stream",
        ),
        create_scene_stream_endpoint_dict(
            url="https://example.com/stream/scene_123/hls/master.m3u8",
            mime_type="application/vnd.apple.mpegurl",
            label="HLS",
        ),
        create_scene_stream_endpoint_dict(
            url="https://example.com/stream/scene_123/dash/manifest.mpd",
            mime_type="application/dash+xml",
            label="DASH",
        ),
    ]

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("sceneStreams", stream_endpoints)
            )
        ]
    )

    result = await respx_stash_client.scene_streams("123")

    # Verify the result is a list of SceneStreamEndpoint objects
    assert result is not None
    assert isinstance(result, list)
    assert len(result) == 3

    # Verify first endpoint (Direct stream)
    assert result[0].url == "https://example.com/stream/scene_123/direct.mp4"
    assert result[0].mime_type == "video/mp4"
    assert result[0].label == "Direct stream"

    # Verify second endpoint (HLS)
    assert result[1].url == "https://example.com/stream/scene_123/hls/master.m3u8"
    assert result[1].mime_type == "application/vnd.apple.mpegurl"
    assert result[1].label == "HLS"

    # Verify third endpoint (DASH)
    assert result[2].url == "https://example.com/stream/scene_123/dash/manifest.mpd"
    assert result[2].mime_type == "application/dash+xml"
    assert result[2].label == "DASH"

    # REQUIRED: Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "sceneStreams" in req["query"]
    assert req["variables"]["id"] == "123"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_streams_empty(respx_stash_client: StashClient) -> None:
    """Test sceneStreams with no available streams.

    Verifies:
    - Returns empty list when no streams available
    - GraphQL query still executes correctly
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("sceneStreams", []))
        ]
    )

    result = await respx_stash_client.scene_streams("456")

    # Verify empty list returned
    assert result is not None
    assert isinstance(result, list)
    assert len(result) == 0

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "sceneStreams" in req["query"]
    assert req["variables"]["id"] == "456"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_streams_single(respx_stash_client: StashClient) -> None:
    """Test sceneStreams with a single stream endpoint.

    Verifies:
    - Works correctly with single stream
    - Label field can be None
    """
    stream_endpoint = create_scene_stream_endpoint_dict(
        url="https://example.com/stream/scene_789/video.webm",
        mime_type="video/webm",
        label=None,  # No label
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("sceneStreams", [stream_endpoint])
            )
        ]
    )

    result = await respx_stash_client.scene_streams("789")

    # Verify single stream
    assert result is not None
    assert isinstance(result, list)
    assert len(result) == 1

    # Verify stream details
    assert result[0].url == "https://example.com/stream/scene_789/video.webm"
    assert result[0].mime_type == "video/webm"
    assert result[0].label is None  # Label is optional

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "sceneStreams" in req["query"]
    assert req["variables"]["id"] == "789"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_streams_with_various_mime_types(
    respx_stash_client: StashClient,
) -> None:
    """Test sceneStreams with various common MIME types.

    Verifies:
    - Handles different video MIME types correctly
    - Tests common streaming formats
    """
    stream_endpoints = [
        create_scene_stream_endpoint_dict(
            url="https://example.com/stream/1/direct.mp4",
            mime_type="video/mp4",
            label="MP4",
        ),
        create_scene_stream_endpoint_dict(
            url="https://example.com/stream/1/direct.webm",
            mime_type="video/webm",
            label="WebM",
        ),
        create_scene_stream_endpoint_dict(
            url="https://example.com/stream/1/direct.mkv",
            mime_type="video/x-matroska",
            label="MKV",
        ),
        create_scene_stream_endpoint_dict(
            url="https://example.com/stream/1/transcode.ts",
            mime_type="video/mp2t",
            label="MPEG-TS",
        ),
    ]

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("sceneStreams", stream_endpoints)
            )
        ]
    )

    result = await respx_stash_client.scene_streams("mime-test-123")

    # Verify all MIME types preserved correctly
    assert len(result) == 4
    assert result[0].mime_type == "video/mp4"
    assert result[1].mime_type == "video/webm"
    assert result[2].mime_type == "video/x-matroska"
    assert result[3].mime_type == "video/mp2t"

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1


# =============================================================================
# Error Handling Tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_streams_error(respx_stash_client: StashClient) -> None:
    """Test sceneStreams error handling.

    Verifies:
    - GraphQL errors are properly handled
    - Returns empty list on error (following project pattern)
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "errors": [{"message": "Scene not found", "path": ["sceneStreams"]}]
                },
            )
        ]
    )

    result = await respx_stash_client.scene_streams("nonexistent")

    # Verify empty list returned on error (following project pattern)
    assert result == []

    # Verify GraphQL call was made
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_streams_server_error(respx_stash_client: StashClient) -> None:
    """Test sceneStreams with server error response.

    Verifies:
    - HTTP 500 errors are handled gracefully
    - Returns empty list on server error
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Internal server error"}]})
        ]
    )

    result = await respx_stash_client.scene_streams("server-error-scene")

    # Verify empty list returned on server error
    assert result == []

    # Verify GraphQL call was attempted
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_streams_empty_id_returns_empty_list(
    respx_stash_client: StashClient,
) -> None:
    """Test that scene_streams returns empty list for empty ID.

    Note: Current implementation doesn't validate empty IDs.
    This test documents current behavior. Consider adding validation
    to match find_scene pattern in the future.

    Verifies:
    - Empty string ID returns empty list (current behavior)
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(200, json={"errors": [{"message": "Invalid ID"}]})]
    )

    result = await respx_stash_client.scene_streams("")

    # Current behavior: returns empty list on error
    assert result == []
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_streams_none_id_returns_empty_list(
    respx_stash_client: StashClient,
) -> None:
    """Test that scene_streams with None ID returns empty list.

    Note: Current implementation doesn't validate None IDs.
    The GraphQL library accepts None and the server returns an error.

    Verifies:
    - None ID returns empty list after server error (current behavior)
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json={"errors": [{"message": "Variable 'id' cannot be null"}]}
            )
        ]
    )

    # None is passed through to GraphQL, which returns an error
    result = await respx_stash_client.scene_streams(None)  # type: ignore[arg-type]

    # Current behavior: returns empty list on error
    assert result == []
    assert len(graphql_route.calls) == 1


# =============================================================================
# Edge Case Tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_streams_special_characters_in_url(
    respx_stash_client: StashClient,
) -> None:
    """Test sceneStreams with special characters in URLs.

    Verifies:
    - URLs with query parameters are handled correctly
    - Special characters are preserved
    """
    stream_endpoint = create_scene_stream_endpoint_dict(
        url="https://example.com/stream/scene_123/video.mp4?token=abc123&quality=high",
        mime_type="video/mp4",
        label="Direct (with auth)",
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("sceneStreams", [stream_endpoint])
            )
        ]
    )

    result = await respx_stash_client.scene_streams("123")

    # Verify URL with query parameters preserved
    assert len(result) == 1
    assert is_set(result[0].url)
    assert "token=abc123" in result[0].url
    assert "quality=high" in result[0].url

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_streams_long_labels(respx_stash_client: StashClient) -> None:
    """Test sceneStreams with long label strings.

    Verifies:
    - Long label strings are handled correctly
    - No truncation of label data
    """
    long_label = "Very long descriptive label for the stream endpoint that includes many details about the quality, format, and encoding settings used for this particular stream variant"

    stream_endpoint = create_scene_stream_endpoint_dict(
        url="https://example.com/stream/test/video.mp4",
        mime_type="video/mp4",
        label=long_label,
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("sceneStreams", [stream_endpoint])
            )
        ]
    )

    result = await respx_stash_client.scene_streams("label-test")

    # Verify long label preserved
    assert len(result) == 1
    assert is_set(result[0].label)
    assert result[0].label == long_label
    assert len(result[0].label) > 100  # Verify it's actually long

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_streams_unicode_in_labels(respx_stash_client: StashClient) -> None:
    """Test sceneStreams with Unicode characters in labels.

    Verifies:
    - Unicode characters in labels are handled correctly
    - Internationalization support
    """
    stream_endpoints = [
        create_scene_stream_endpoint_dict(
            url="https://example.com/stream/1/video.mp4",
            mime_type="video/mp4",
            label="高画質 (High Quality)",
        ),
        create_scene_stream_endpoint_dict(
            url="https://example.com/stream/1/video_low.mp4",
            mime_type="video/mp4",
            label="標準画質 (Standard Quality)",
        ),
    ]

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("sceneStreams", stream_endpoints)
            )
        ]
    )

    result = await respx_stash_client.scene_streams("unicode-test")

    # Verify Unicode labels preserved
    assert len(result) == 2
    assert result[0].label == "高画質 (High Quality)"
    assert result[1].label == "標準画質 (Standard Quality)"

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scene_streams_no_result_key(respx_stash_client: StashClient) -> None:
    """Test scene_streams when result doesn't contain key.

    Verifies:
    - Returns empty list when sceneStreams not in result
    - Follows pattern from scene_generate_screenshot tests
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(200, json={"data": {"otherField": "value"}})]
    )

    result = await respx_stash_client.scene_streams("no-key-test")

    # Verify empty list returned when key missing
    assert result == []

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
