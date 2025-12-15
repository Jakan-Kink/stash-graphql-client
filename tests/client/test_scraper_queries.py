"""Unit tests for ScraperClientMixin list query operations.

These tests mock at the HTTP boundary using respx, allowing real code execution
through the entire GraphQL client stack including serialization/deserialization.
"""

import json

import httpx
import pytest
import respx

from stash_graphql_client import StashClient
from stash_graphql_client.types import ScrapeContentType
from tests.fixtures import create_graphql_response


# =============================================================================
# Helper functions for creating scraper test data
# =============================================================================


def create_scraper_spec_dict(
    urls: list[str] | None = None,
    supported_scrapes: list[str] | None = None,
) -> dict:
    """Create a ScraperSpec dictionary for testing."""
    return {
        "urls": urls or ["https://example.com"],
        "supported_scrapes": supported_scrapes or ["NAME", "FRAGMENT"],
    }


def create_scraper_dict(
    id: str = "scraper-123",
    name: str = "Test Scraper",
    performer: dict | None = None,
    scene: dict | None = None,
    gallery: dict | None = None,
    image: dict | None = None,
    group: dict | None = None,
) -> dict:
    """Create a Scraper dictionary for testing."""
    return {
        "id": id,
        "name": name,
        "performer": performer,
        "scene": scene,
        "gallery": gallery,
        "image": image,
        "group": group,
    }


# =============================================================================
# list_scrapers tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_list_scrapers_single_type(respx_stash_client: StashClient) -> None:
    """Test listing scrapers with single content type."""
    scraper_data = create_scraper_dict(
        id="scraper-1",
        name="Scene Scraper",
        scene=create_scraper_spec_dict(
            urls=["https://example.com"],
            supported_scrapes=["NAME", "FRAGMENT", "URL"],
        ),
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("listScrapers", [scraper_data])
            )
        ]
    )

    scrapers = await respx_stash_client.list_scrapers([ScrapeContentType.SCENE])

    assert len(scrapers) == 1
    assert scrapers[0].id == "scraper-1"
    assert scrapers[0].name == "Scene Scraper"
    assert scrapers[0].scene is not None
    assert len(scrapers[0].scene.urls) == 1
    assert scrapers[0].scene.urls[0] == "https://example.com"
    assert len(scrapers[0].scene.supported_scrapes) == 3

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "listScrapers" in req["query"]
    assert req["variables"]["types"] == ["SCENE"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_list_scrapers_multiple_types(respx_stash_client: StashClient) -> None:
    """Test listing scrapers with multiple content types."""
    scrapers_data = [
        create_scraper_dict(
            id="scraper-1",
            name="Scene Scraper",
            scene=create_scraper_spec_dict(urls=["https://scenes.com"]),
        ),
        create_scraper_dict(
            id="scraper-2",
            name="Performer Scraper",
            performer=create_scraper_spec_dict(urls=["https://performers.com"]),
        ),
    ]

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("listScrapers", scrapers_data)
            )
        ]
    )

    scrapers = await respx_stash_client.list_scrapers(
        [ScrapeContentType.SCENE, ScrapeContentType.PERFORMER]
    )

    assert len(scrapers) == 2
    assert scrapers[0].id == "scraper-1"
    assert scrapers[0].scene is not None
    assert scrapers[1].id == "scraper-2"
    assert scrapers[1].performer is not None

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["types"] == ["SCENE", "PERFORMER"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_list_scrapers_all_types(respx_stash_client: StashClient) -> None:
    """Test listing scrapers with all content types."""
    scraper_data = create_scraper_dict(
        id="universal-scraper",
        name="Universal Scraper",
        scene=create_scraper_spec_dict(),
        performer=create_scraper_spec_dict(),
        gallery=create_scraper_spec_dict(),
        image=create_scraper_spec_dict(),
        group=create_scraper_spec_dict(),
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("listScrapers", [scraper_data])
            )
        ]
    )

    scrapers = await respx_stash_client.list_scrapers(
        [
            ScrapeContentType.SCENE,
            ScrapeContentType.PERFORMER,
            ScrapeContentType.GALLERY,
            ScrapeContentType.IMAGE,
            ScrapeContentType.GROUP,
        ]
    )

    assert len(scrapers) == 1
    assert scrapers[0].id == "universal-scraper"
    assert scrapers[0].scene is not None
    assert scrapers[0].performer is not None
    assert scrapers[0].gallery is not None
    assert scrapers[0].image is not None
    assert scrapers[0].group is not None

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert set(req["variables"]["types"]) == {
        "SCENE",
        "PERFORMER",
        "GALLERY",
        "IMAGE",
        "GROUP",
    }


@pytest.mark.asyncio
@pytest.mark.unit
async def test_list_scrapers_empty(respx_stash_client: StashClient) -> None:
    """Test listing scrapers when none match criteria."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("listScrapers", []))
        ]
    )

    scrapers = await respx_stash_client.list_scrapers([ScrapeContentType.SCENE])

    assert len(scrapers) == 0
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_list_scrapers_error_returns_empty(
    respx_stash_client: StashClient,
) -> None:
    """Test that list_scrapers returns empty list on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    scrapers = await respx_stash_client.list_scrapers([ScrapeContentType.SCENE])

    assert len(scrapers) == 0
    assert len(graphql_route.calls) == 1


# =============================================================================
# Additional type variations tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_list_scrapers_performer_type(respx_stash_client: StashClient) -> None:
    """Test listing scrapers filtered by performer type."""
    scraper_data = create_scraper_dict(
        id="perf-scraper",
        name="Performer Scraper",
        performer=create_scraper_spec_dict(),
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("listScrapers", [scraper_data])
            )
        ]
    )

    scrapers = await respx_stash_client.list_scrapers([ScrapeContentType.PERFORMER])

    assert len(scrapers) == 1
    assert scrapers[0].id == "perf-scraper"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["types"] == ["PERFORMER"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_list_scrapers_gallery_type(respx_stash_client: StashClient) -> None:
    """Test listing scrapers filtered by gallery type."""
    scraper_data = create_scraper_dict(
        id="gallery-scraper",
        name="Gallery Scraper",
        gallery=create_scraper_spec_dict(),
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("listScrapers", [scraper_data])
            )
        ]
    )

    scrapers = await respx_stash_client.list_scrapers([ScrapeContentType.GALLERY])

    assert len(scrapers) == 1
    assert scrapers[0].id == "gallery-scraper"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["types"] == ["GALLERY"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_list_scrapers_image_type(respx_stash_client: StashClient) -> None:
    """Test listing scrapers filtered by image type."""
    scraper_data = create_scraper_dict(
        id="image-scraper",
        name="Image Scraper",
        image=create_scraper_spec_dict(),
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("listScrapers", [scraper_data])
            )
        ]
    )

    scrapers = await respx_stash_client.list_scrapers([ScrapeContentType.IMAGE])

    assert len(scrapers) == 1
    assert scrapers[0].id == "image-scraper"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["types"] == ["IMAGE"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_list_scrapers_group_type(respx_stash_client: StashClient) -> None:
    """Test listing scrapers filtered by group type."""
    scraper_data = create_scraper_dict(
        id="group-scraper",
        name="Group Scraper",
        group=create_scraper_spec_dict(),
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("listScrapers", [scraper_data])
            )
        ]
    )

    scrapers = await respx_stash_client.list_scrapers([ScrapeContentType.GROUP])

    assert len(scrapers) == 1
    assert scrapers[0].id == "group-scraper"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["types"] == ["GROUP"]
