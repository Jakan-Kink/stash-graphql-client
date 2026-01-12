"""Unit tests for ScraperClientMixin StashBox operations.

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
    StashBoxDraftSubmissionInput,
    StashBoxFingerprintSubmissionInput,
)
from tests.fixtures import create_graphql_response


# =============================================================================
# submit_stashbox_fingerprints tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_submit_stashbox_fingerprints_with_dict(
    respx_stash_client: StashClient,
) -> None:
    """Test submitting fingerprints to StashBox with dict input.

    This covers lines 1344-1357: successful submission with dict.
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("submitStashBoxFingerprints", True)
            )
        ]
    )

    input_dict = {
        "stash_box_endpoint": "https://stashdb.org",
        "scene_ids": ["scene123"],
    }

    result = await respx_stash_client.submit_stashbox_fingerprints(input_dict)

    assert result is True

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "submitStashBoxFingerprints" in req["query"]
    assert req["variables"]["input"]["stash_box_endpoint"] == "https://stashdb.org"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_submit_stashbox_fingerprints_with_input_type(
    respx_stash_client: StashClient,
) -> None:
    """Test submitting fingerprints with StashBoxFingerprintSubmissionInput.

    This covers lines 1345-1346: if isinstance check.
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("submitStashBoxFingerprints", True)
            )
        ]
    )

    input_data = StashBoxFingerprintSubmissionInput(
        scene_ids=["scene123", "scene456"],
        stash_box_endpoint="https://stashdb.org",
    )

    result = await respx_stash_client.submit_stashbox_fingerprints(input_data)

    assert result is True

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "submitStashBoxFingerprints" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_submit_stashbox_fingerprints_error_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test that submit_stashbox_fingerprints raises on error.

    This covers lines 1355-1357: exception handling.
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    input_dict = {
        "stash_box_endpoint": "https://stashdb.org",
        "scene_ids": ["scene123"],
    }

    with pytest.raises(StashGraphQLError):
        await respx_stash_client.submit_stashbox_fingerprints(input_dict)

    assert len(graphql_route.calls) == 1


# =============================================================================
# submit_stashbox_scene_draft tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_submit_stashbox_scene_draft_with_dict(
    respx_stash_client: StashClient,
) -> None:
    """Test submitting scene draft to StashBox with dict input.

    This covers lines 1371-1384: successful submission with dict.
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response("submitStashBoxSceneDraft", "draft-123"),
            )
        ]
    )

    input_dict = {
        "stash_box_endpoint": "https://stashdb.org",
        "id": "scene456",
    }

    result = await respx_stash_client.submit_stashbox_scene_draft(input_dict)

    assert result == "draft-123"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "submitStashBoxSceneDraft" in req["query"]
    assert req["variables"]["input"]["stash_box_endpoint"] == "https://stashdb.org"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_submit_stashbox_scene_draft_with_input_type(
    respx_stash_client: StashClient,
) -> None:
    """Test submitting scene draft with StashBoxDraftSubmissionInput.

    This covers lines 1372-1373: if isinstance check.
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response("submitStashBoxSceneDraft", "draft-456"),
            )
        ]
    )

    input_data = StashBoxDraftSubmissionInput(
        stash_box_endpoint="https://stashdb.org",
        id="scene789",
    )

    result = await respx_stash_client.submit_stashbox_scene_draft(input_data)

    assert result == "draft-456"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "submitStashBoxSceneDraft" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_submit_stashbox_scene_draft_error_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test that submit_stashbox_scene_draft raises on error.

    This covers lines 1382-1384: exception handling.
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    input_dict = {
        "stash_box_endpoint": "https://stashdb.org",
        "id": "scene123",
    }

    with pytest.raises(StashGraphQLError):
        await respx_stash_client.submit_stashbox_scene_draft(input_dict)

    assert len(graphql_route.calls) == 1


# =============================================================================
# submit_stashbox_performer_draft tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_submit_stashbox_performer_draft_with_dict(
    respx_stash_client: StashClient,
) -> None:
    """Test submitting performer draft to StashBox with dict input.

    This covers lines 1398-1411: successful submission with dict.
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "submitStashBoxPerformerDraft", "performer-draft-123"
                ),
            )
        ]
    )

    input_dict = {
        "stash_box_endpoint": "https://stashdb.org",
        "id": "performer456",
    }

    result = await respx_stash_client.submit_stashbox_performer_draft(input_dict)

    assert result == "performer-draft-123"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "submitStashBoxPerformerDraft" in req["query"]
    assert req["variables"]["input"]["stash_box_endpoint"] == "https://stashdb.org"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_submit_stashbox_performer_draft_with_input_type(
    respx_stash_client: StashClient,
) -> None:
    """Test submitting performer draft with StashBoxDraftSubmissionInput.

    This covers lines 1399-1400: if isinstance check.
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "submitStashBoxPerformerDraft", "performer-draft-456"
                ),
            )
        ]
    )

    input_data = StashBoxDraftSubmissionInput(
        stash_box_endpoint="https://stashdb.org",
        id="performer789",
    )

    result = await respx_stash_client.submit_stashbox_performer_draft(input_data)

    assert result == "performer-draft-456"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "submitStashBoxPerformerDraft" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_submit_stashbox_performer_draft_error_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test that submit_stashbox_performer_draft raises on error.

    This covers lines 1409-1411: exception handling.
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    input_dict = {
        "stash_box_endpoint": "https://stashdb.org",
        "id": "performer123",
    }

    with pytest.raises(StashGraphQLError):
        await respx_stash_client.submit_stashbox_performer_draft(input_dict)

    assert len(graphql_route.calls) == 1


# =============================================================================
# stashbox_batch_performer_tag tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_stashbox_batch_performer_tag(respx_stash_client: StashClient) -> None:
    """Test batch tagging performers from StashBox.

    This covers lines 1425-1433: successful batch tagging.
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response("stashBoxBatchPerformerTag", "job-123"),
            )
        ]
    )

    input_dict = {
        "stash_box_endpoint": "https://stashdb.org",
        "performer_ids": ["p1", "p2", "p3"],
    }

    result = await respx_stash_client.stashbox_batch_performer_tag(input_dict)

    assert result == "job-123"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "stashBoxBatchPerformerTag" in req["query"]
    assert req["variables"]["input"]["stash_box_endpoint"] == "https://stashdb.org"
    assert req["variables"]["input"]["performer_ids"] == ["p1", "p2", "p3"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_stashbox_batch_performer_tag_error_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test that stashbox_batch_performer_tag raises on error.

    This covers lines 1431-1433: exception handling.
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    input_dict = {
        "stash_box_endpoint": "https://stashdb.org",
        "performer_ids": ["p1"],
    }

    with pytest.raises(StashGraphQLError):
        await respx_stash_client.stashbox_batch_performer_tag(input_dict)

    assert len(graphql_route.calls) == 1


# =============================================================================
# stashbox_batch_studio_tag tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_stashbox_batch_studio_tag(respx_stash_client: StashClient) -> None:
    """Test batch tagging studios from StashBox.

    This covers lines 1447-1455: successful batch tagging.
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response("stashBoxBatchStudioTag", "job-456"),
            )
        ]
    )

    input_dict = {
        "stash_box_endpoint": "https://stashdb.org",
        "studio_ids": ["s1", "s2", "s3"],
    }

    result = await respx_stash_client.stashbox_batch_studio_tag(input_dict)

    assert result == "job-456"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "stashBoxBatchStudioTag" in req["query"]
    assert req["variables"]["input"]["stash_box_endpoint"] == "https://stashdb.org"
    assert req["variables"]["input"]["studio_ids"] == ["s1", "s2", "s3"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_stashbox_batch_studio_tag_error_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test that stashbox_batch_studio_tag raises on error.

    This covers lines 1453-1455: exception handling.
    """
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    input_dict = {
        "stash_box_endpoint": "https://stashdb.org",
        "studio_ids": ["s1"],
    }

    with pytest.raises(StashGraphQLError):
        await respx_stash_client.stashbox_batch_studio_tag(input_dict)

    assert len(graphql_route.calls) == 1
