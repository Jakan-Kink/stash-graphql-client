"""Tests for verifying fragment field completeness.

These tests verify that GraphQL fragments include all expected fields from the schema.
They use respx to mock HTTP responses at the edge and verify that the client correctly
deserializes all fields.

NOTE: This test file is written BEFORE the fragment updates are made.
Tests will fail until the fragments are updated to include all fields.
"""

import httpx
import pytest
import respx

from stash_graphql_client import StashClient
from tests.fixtures import (
    create_find_performers_result,
    create_find_studios_result,
    create_graphql_response,
    create_marker_dict,
    create_performer_dict,
    create_studio_dict,
    create_tag_dict,
)


# =============================================================================
# Performer fragment completeness tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_performer_fragment_includes_weight(
    respx_stash_client: StashClient,
) -> None:
    """Test that performer fragment includes weight field."""
    performer_data = create_performer_dict(id="1", name="Test Performer", weight=150)
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findPerformers",
                    create_find_performers_result(count=1, performers=[performer_data]),
                ),
            )
        ]
    )

    result = await respx_stash_client.find_performers()

    assert result.count == 1
    performer = result.performers[0]
    assert performer.weight == 150


@pytest.mark.asyncio
@pytest.mark.unit
async def test_performer_fragment_includes_rating100(
    respx_stash_client: StashClient,
) -> None:
    """Test that performer fragment includes rating100 field."""
    performer_data = create_performer_dict(id="1", name="Test Performer", rating100=85)
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findPerformers",
                    create_find_performers_result(count=1, performers=[performer_data]),
                ),
            )
        ]
    )

    result = await respx_stash_client.find_performers()

    assert result.count == 1
    performer = result.performers[0]
    assert performer.rating100 == 85


@pytest.mark.asyncio
@pytest.mark.unit
async def test_performer_fragment_includes_death_date(
    respx_stash_client: StashClient,
) -> None:
    """Test that performer fragment includes death_date field."""
    performer_data = create_performer_dict(
        id="1", name="Test Performer", death_date="2020-01-15"
    )
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findPerformers",
                    create_find_performers_result(count=1, performers=[performer_data]),
                ),
            )
        ]
    )

    result = await respx_stash_client.find_performers()

    assert result.count == 1
    performer = result.performers[0]
    assert performer.death_date == "2020-01-15"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_performer_fragment_includes_favorite(
    respx_stash_client: StashClient,
) -> None:
    """Test that performer fragment includes favorite field."""
    performer_data = create_performer_dict(id="1", name="Test Performer", favorite=True)
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findPerformers",
                    create_find_performers_result(count=1, performers=[performer_data]),
                ),
            )
        ]
    )

    result = await respx_stash_client.find_performers()

    assert result.count == 1
    performer = result.performers[0]
    assert performer.favorite is True


@pytest.mark.asyncio
@pytest.mark.unit
async def test_performer_fragment_includes_ignore_auto_tag(
    respx_stash_client: StashClient,
) -> None:
    """Test that performer fragment includes ignore_auto_tag field."""
    performer_data = create_performer_dict(
        id="1", name="Test Performer", ignore_auto_tag=True
    )
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findPerformers",
                    create_find_performers_result(count=1, performers=[performer_data]),
                ),
            )
        ]
    )

    result = await respx_stash_client.find_performers()

    assert result.count == 1
    performer = result.performers[0]
    assert performer.ignore_auto_tag is True


@pytest.mark.asyncio
@pytest.mark.unit
async def test_performer_fragment_includes_height_cm(
    respx_stash_client: StashClient,
) -> None:
    """Test that performer fragment includes height_cm field."""
    performer_data = create_performer_dict(id="1", name="Test Performer", height_cm=175)
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findPerformers",
                    create_find_performers_result(count=1, performers=[performer_data]),
                ),
            )
        ]
    )

    result = await respx_stash_client.find_performers()

    assert result.count == 1
    performer = result.performers[0]
    assert performer.height_cm == 175


@pytest.mark.asyncio
@pytest.mark.unit
async def test_performer_fragment_includes_career_length(
    respx_stash_client: StashClient,
) -> None:
    """Test that performer fragment includes career_length field."""
    performer_data = create_performer_dict(
        id="1", name="Test Performer", career_length="2010-2020"
    )
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findPerformers",
                    create_find_performers_result(count=1, performers=[performer_data]),
                ),
            )
        ]
    )

    result = await respx_stash_client.find_performers()

    assert result.count == 1
    performer = result.performers[0]
    assert performer.career_length == "2010-2020"


# =============================================================================
# Studio fragment completeness tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_studio_fragment_includes_child_studios(
    respx_stash_client: StashClient,
) -> None:
    """Test that studio fragment includes child_studios field.

    Note: child_studios are returned as stubs with just ID (following the
    StashEntityStore pattern). Full Studio details can be fetched separately.
    """
    # Child studios are stubs - just the ID for lookup
    child_studio_stub = {"id": "2"}
    studio_data = create_studio_dict(
        id="1", name="Parent Studio", child_studios=[child_studio_stub]
    )
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findStudios",
                    create_find_studios_result(count=1, studios=[studio_data]),
                ),
            )
        ]
    )

    result = await respx_stash_client.find_studios()

    assert result.count == 1
    studio = result.studios[0]
    assert len(studio.child_studios) == 1
    # child_studios are stubs with just ID for StashEntityStore lookup
    assert studio.child_studios[0].id == "2"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_studio_fragment_includes_stash_ids(
    respx_stash_client: StashClient,
) -> None:
    """Test that studio fragment includes stash_ids field."""
    studio_data = create_studio_dict(
        id="1",
        name="Test Studio",
        stash_ids=[
            {
                "endpoint": "https://stashdb.org",
                "stash_id": "abc123",
                "updated_at": "2024-01-15T10:30:00Z",  # Required by StashID type
            }
        ],
    )
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findStudios",
                    create_find_studios_result(count=1, studios=[studio_data]),
                ),
            )
        ]
    )

    result = await respx_stash_client.find_studios()

    assert result.count == 1
    studio = result.studios[0]
    assert len(studio.stash_ids) == 1
    assert studio.stash_ids[0].stash_id == "abc123"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_studio_fragment_includes_rating100(
    respx_stash_client: StashClient,
) -> None:
    """Test that studio fragment includes rating100 field."""
    studio_data = create_studio_dict(id="1", name="Test Studio", rating100=90)
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findStudios",
                    create_find_studios_result(count=1, studios=[studio_data]),
                ),
            )
        ]
    )

    result = await respx_stash_client.find_studios()

    assert result.count == 1
    studio = result.studios[0]
    assert studio.rating100 == 90


@pytest.mark.asyncio
@pytest.mark.unit
async def test_studio_fragment_includes_favorite(
    respx_stash_client: StashClient,
) -> None:
    """Test that studio fragment includes favorite field."""
    studio_data = create_studio_dict(id="1", name="Test Studio", favorite=True)
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findStudios",
                    create_find_studios_result(count=1, studios=[studio_data]),
                ),
            )
        ]
    )

    result = await respx_stash_client.find_studios()

    assert result.count == 1
    studio = result.studios[0]
    assert studio.favorite is True


@pytest.mark.asyncio
@pytest.mark.unit
async def test_studio_fragment_includes_ignore_auto_tag(
    respx_stash_client: StashClient,
) -> None:
    """Test that studio fragment includes ignore_auto_tag field."""
    studio_data = create_studio_dict(id="1", name="Test Studio", ignore_auto_tag=True)
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findStudios",
                    create_find_studios_result(count=1, studios=[studio_data]),
                ),
            )
        ]
    )

    result = await respx_stash_client.find_studios()

    assert result.count == 1
    studio = result.studios[0]
    assert studio.ignore_auto_tag is True


# =============================================================================
# Tag fragment completeness tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_tag_fragment_includes_sort_name(
    respx_stash_client: StashClient,
) -> None:
    """Test that tag fragment includes sort_name field."""
    tag_data = create_tag_dict(id="1", name="The Tag", sort_name="Tag, The")
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findTags",
                    {"count": 1, "tags": [tag_data]},
                ),
            )
        ]
    )

    result = await respx_stash_client.find_tags()

    assert result.count == 1
    tag = result.tags[0]
    assert tag.sort_name == "Tag, The"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_tag_fragment_includes_favorite(
    respx_stash_client: StashClient,
) -> None:
    """Test that tag fragment includes favorite field."""
    tag_data = create_tag_dict(id="1", name="Test Tag", favorite=True)
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findTags",
                    {"count": 1, "tags": [tag_data]},
                ),
            )
        ]
    )

    result = await respx_stash_client.find_tags()

    assert result.count == 1
    tag = result.tags[0]
    assert tag.favorite is True


@pytest.mark.asyncio
@pytest.mark.unit
async def test_tag_fragment_includes_ignore_auto_tag(
    respx_stash_client: StashClient,
) -> None:
    """Test that tag fragment includes ignore_auto_tag field."""
    tag_data = create_tag_dict(id="1", name="Test Tag", ignore_auto_tag=True)
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findTags",
                    {"count": 1, "tags": [tag_data]},
                ),
            )
        ]
    )

    result = await respx_stash_client.find_tags()

    assert result.count == 1
    tag = result.tags[0]
    assert tag.ignore_auto_tag is True


# =============================================================================
# SceneMarker fragment completeness tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_marker_fragment_includes_end_seconds(
    respx_stash_client: StashClient,
) -> None:
    """Test that marker fragment includes end_seconds field."""
    marker_data = create_marker_dict(
        id="1", title="Test Marker", seconds=10.5, end_seconds=25.0
    )
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response("findSceneMarker", marker_data),
            )
        ]
    )

    result = await respx_stash_client.find_marker("1")

    assert result is not None
    assert result.end_seconds == 25.0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_marker_fragment_includes_stream(
    respx_stash_client: StashClient,
) -> None:
    """Test that marker fragment includes stream field."""
    marker_data = create_marker_dict(
        id="1", title="Test Marker", stream="/scene/1/marker/1/stream"
    )
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response("findSceneMarker", marker_data),
            )
        ]
    )

    result = await respx_stash_client.find_marker("1")

    assert result is not None
    assert result.stream == "/scene/1/marker/1/stream"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_marker_fragment_includes_preview(
    respx_stash_client: StashClient,
) -> None:
    """Test that marker fragment includes preview field."""
    marker_data = create_marker_dict(
        id="1", title="Test Marker", preview="/scene/1/marker/1/preview.jpg"
    )
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response("findSceneMarker", marker_data),
            )
        ]
    )

    result = await respx_stash_client.find_marker("1")

    assert result is not None
    assert result.preview == "/scene/1/marker/1/preview.jpg"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_marker_fragment_includes_screenshot(
    respx_stash_client: StashClient,
) -> None:
    """Test that marker fragment includes screenshot field."""
    marker_data = create_marker_dict(
        id="1", title="Test Marker", screenshot="/scene/1/marker/1/screenshot.jpg"
    )
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response("findSceneMarker", marker_data),
            )
        ]
    )

    result = await respx_stash_client.find_marker("1")

    assert result is not None
    assert result.screenshot == "/scene/1/marker/1/screenshot.jpg"
