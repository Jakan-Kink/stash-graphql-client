"""Unit tests for ScraperClientMixin URL scraping operations.

These tests mock at the HTTP boundary using respx, allowing real code execution
through the entire GraphQL client stack including serialization/deserialization.

URL scraping operations return union types and require __typename handling.
"""

import json

import httpx
import pytest
import respx

from stash_graphql_client import StashClient
from stash_graphql_client.types import ScrapeContentType
from tests.fixtures import create_graphql_response


# =============================================================================
# Helper functions for creating scraped content test data
# =============================================================================


def create_scraped_tag_dict(
    stored_id: str | None = None,
    name: str = "Tag Name",
) -> dict:
    """Create a ScrapedTag dictionary for testing."""
    return {
        "stored_id": stored_id,
        "name": name,
    }


def create_scraped_studio_dict(
    stored_id: str | None = None,
    name: str = "Studio Name",
    urls: list[str] | None = None,
) -> dict:
    """Create a ScrapedStudio dictionary for testing."""
    return {
        "stored_id": stored_id,
        "name": name,
        "urls": urls or ["https://example.com/studio"],
    }


def create_scraped_scene_dict(
    title: str = "Scene Title",
    code: str | None = "SCENE-001",
    details: str | None = "Scene details",
    urls: list[str] | None = None,
    date: str | None = "2024-01-15",
) -> dict:
    """Create a ScrapedScene dictionary for testing."""
    return {
        "title": title,
        "code": code,
        "details": details,
        "urls": urls or ["https://example.com/scene"],
        "date": date,
    }


def create_scraped_performer_dict(
    stored_id: str | None = None,
    name: str = "Performer Name",
    gender: str | None = "FEMALE",
    urls: list[str] | None = None,
) -> dict:
    """Create a ScrapedPerformer dictionary for testing."""
    return {
        "stored_id": stored_id,
        "name": name,
        "gender": gender,
        "urls": urls or ["https://example.com/performer"],
    }


def create_scraped_gallery_dict(
    title: str = "Gallery Title",
    code: str | None = "GAL-001",
    details: str | None = "Gallery details",
    urls: list[str] | None = None,
    date: str | None = "2024-01-15",
) -> dict:
    """Create a ScrapedGallery dictionary for testing."""
    return {
        "title": title,
        "code": code,
        "details": details,
        "urls": urls or ["https://example.com/gallery"],
        "date": date,
    }


def create_scraped_image_dict(
    title: str = "Image Title",
    code: str | None = "IMG-001",
    details: str | None = "Image details",
    urls: list[str] | None = None,
    date: str | None = "2024-01-15",
) -> dict:
    """Create a ScrapedImage dictionary for testing."""
    return {
        "title": title,
        "code": code,
        "details": details,
        "urls": urls or ["https://example.com/image"],
        "date": date,
    }


def create_scraped_movie_dict(
    stored_id: str | None = None,
    name: str = "Movie Name",
    aliases: str | None = None,
    duration: str | None = "7200",
    date: str | None = "2024-01-15",
) -> dict:
    """Create a ScrapedMovie dictionary for testing."""
    return {
        "stored_id": stored_id,
        "name": name,
        "aliases": aliases,
        "duration": duration,
        "date": date,
    }


def create_scraped_group_dict(
    stored_id: str | None = None,
    name: str = "Group Name",
    aliases: str | None = None,
    duration: str | None = "7200",
    date: str | None = "2024-01-15",
) -> dict:
    """Create a ScrapedGroup dictionary for testing."""
    return {
        "stored_id": stored_id,
        "name": name,
        "aliases": aliases,
        "duration": duration,
        "date": date,
    }


# =============================================================================
# scrape_url tests (union type with __typename)
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_url_scene(respx_stash_client: StashClient) -> None:
    """Test scraping a scene from URL."""
    scene_data = create_scraped_scene_dict(title="Test Scene")
    scene_data["__typename"] = "ScrapedScene"

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("scrapeURL", scene_data))
        ]
    )

    result = await respx_stash_client.scrape_url(
        "https://example.com/scene/123", ScrapeContentType.SCENE
    )

    assert result is not None
    assert result.title == "Test Scene"
    assert result.code == "SCENE-001"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "scrapeURL" in req["query"]
    assert "__typename" in req["query"]
    assert req["variables"]["url"] == "https://example.com/scene/123"
    assert req["variables"]["ty"] == "SCENE"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_url_performer(respx_stash_client: StashClient) -> None:
    """Test scraping a performer from URL."""
    performer_data = create_scraped_performer_dict(name="Jane Doe")
    performer_data["__typename"] = "ScrapedPerformer"

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("scrapeURL", performer_data)
            )
        ]
    )

    result = await respx_stash_client.scrape_url(
        "https://example.com/performer/456", ScrapeContentType.PERFORMER
    )

    assert result is not None
    assert result.name == "Jane Doe"
    assert result.gender == "FEMALE"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["url"] == "https://example.com/performer/456"
    assert req["variables"]["ty"] == "PERFORMER"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_url_studio(respx_stash_client: StashClient) -> None:
    """Test scraping a studio from URL."""
    studio_data = create_scraped_studio_dict(name="Acme Studios")
    studio_data["__typename"] = "ScrapedStudio"

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("scrapeURL", studio_data))
        ]
    )

    result = await respx_stash_client.scrape_url(
        "https://example.com/studio/789",
        ScrapeContentType.SCENE,  # Studio can be part of scene scraping
    )

    assert result is not None
    assert result.name == "Acme Studios"
    assert len(result.urls) == 1

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_url_gallery(respx_stash_client: StashClient) -> None:
    """Test scraping a gallery from URL."""
    gallery_data = create_scraped_gallery_dict(title="Photo Gallery")
    gallery_data["__typename"] = "ScrapedGallery"

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("scrapeURL", gallery_data))
        ]
    )

    result = await respx_stash_client.scrape_url(
        "https://example.com/gallery/111", ScrapeContentType.GALLERY
    )

    assert result is not None
    assert result.title == "Photo Gallery"
    assert result.code == "GAL-001"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["ty"] == "GALLERY"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_url_image(respx_stash_client: StashClient) -> None:
    """Test scraping an image from URL."""
    image_data = create_scraped_image_dict(title="Single Image")
    image_data["__typename"] = "ScrapedImage"

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("scrapeURL", image_data))
        ]
    )

    result = await respx_stash_client.scrape_url(
        "https://example.com/image/222", ScrapeContentType.IMAGE
    )

    assert result is not None
    assert result.title == "Single Image"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["ty"] == "IMAGE"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_url_group(respx_stash_client: StashClient) -> None:
    """Test scraping a group from URL."""
    group_data = create_scraped_group_dict(name="Movie Series")
    group_data["__typename"] = "ScrapedGroup"

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("scrapeURL", group_data))
        ]
    )

    result = await respx_stash_client.scrape_url(
        "https://example.com/group/333", ScrapeContentType.GROUP
    )

    assert result is not None
    assert result.name == "Movie Series"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["ty"] == "GROUP"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_url_unknown_typename(respx_stash_client: StashClient) -> None:
    """Test scraping URL with unknown __typename returns None."""
    data = {"__typename": "UnknownType", "name": "Something"}

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("scrapeURL", data))
        ]
    )

    result = await respx_stash_client.scrape_url(
        "https://example.com/unknown", ScrapeContentType.SCENE
    )

    assert result is None
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_url_null_result(respx_stash_client: StashClient) -> None:
    """Test scraping URL that returns null."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("scrapeURL", None))
        ]
    )

    result = await respx_stash_client.scrape_url(
        "https://example.com/notfound", ScrapeContentType.SCENE
    )

    assert result is None
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_url_error_returns_none(respx_stash_client: StashClient) -> None:
    """Test that scrape_url returns None on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    result = await respx_stash_client.scrape_url(
        "https://example.com/scene/123", ScrapeContentType.SCENE
    )

    assert result is None
    assert len(graphql_route.calls) == 1


# =============================================================================
# Specific URL scraping methods tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_scene_url(respx_stash_client: StashClient) -> None:
    """Test scraping scene from URL using dedicated method."""
    scene_data = create_scraped_scene_dict(
        title="Specific Scene",
        code="SC-999",
        date="2024-02-20",
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("scrapeSceneURL", scene_data)
            )
        ]
    )

    result = await respx_stash_client.scrape_scene_url("https://example.com/scene/999")

    assert result is not None
    assert result.title == "Specific Scene"
    assert result.code == "SC-999"
    assert result.date == "2024-02-20"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "scrapeSceneURL" in req["query"]
    assert req["variables"]["url"] == "https://example.com/scene/999"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_scene_url_with_nested_data(
    respx_stash_client: StashClient,
) -> None:
    """Test scraping scene URL with studio and tags."""
    scene_data = create_scraped_scene_dict(title="Complex Scene")
    scene_data["studio"] = create_scraped_studio_dict(name="Test Studio")
    scene_data["tags"] = [
        create_scraped_tag_dict(name="Tag1"),
        create_scraped_tag_dict(name="Tag2"),
    ]

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("scrapeSceneURL", scene_data)
            )
        ]
    )

    result = await respx_stash_client.scrape_scene_url(
        "https://example.com/scene/complex"
    )

    assert result is not None
    assert result.title == "Complex Scene"
    assert result.studio is not None
    assert result.studio.name == "Test Studio"
    assert result.tags is not None
    assert len(result.tags) == 2

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_performer_url(respx_stash_client: StashClient) -> None:
    """Test scraping performer from URL using dedicated method."""
    performer_data = create_scraped_performer_dict(
        name="John Doe",
        gender="MALE",
    )
    performer_data["birthdate"] = "1990-05-15"
    performer_data["ethnicity"] = "Caucasian"

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("scrapePerformerURL", performer_data)
            )
        ]
    )

    result = await respx_stash_client.scrape_performer_url(
        "https://example.com/performer/john"
    )

    assert result is not None
    assert result.name == "John Doe"
    assert result.gender == "MALE"
    assert result.birthdate == "1990-05-15"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "scrapePerformerURL" in req["query"]
    assert req["variables"]["url"] == "https://example.com/performer/john"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_gallery_url(respx_stash_client: StashClient) -> None:
    """Test scraping gallery from URL using dedicated method."""
    gallery_data = create_scraped_gallery_dict(
        title="Photo Set",
        code="PS-001",
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("scrapeGalleryURL", gallery_data)
            )
        ]
    )

    result = await respx_stash_client.scrape_gallery_url(
        "https://example.com/gallery/photoset"
    )

    assert result is not None
    assert result.title == "Photo Set"
    assert result.code == "PS-001"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "scrapeGalleryURL" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_image_url(respx_stash_client: StashClient) -> None:
    """Test scraping image from URL using dedicated method."""
    image_data = create_scraped_image_dict(
        title="Photo Image",
        code="IMG-999",
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("scrapeImageURL", image_data)
            )
        ]
    )

    result = await respx_stash_client.scrape_image_url(
        "https://example.com/image/photo"
    )

    assert result is not None
    assert result.title == "Photo Image"
    assert result.code == "IMG-999"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "scrapeImageURL" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_movie_url(respx_stash_client: StashClient) -> None:
    """Test scraping movie from URL using deprecated method."""
    movie_data = create_scraped_movie_dict(
        name="Classic Movie",
        duration="5400",
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("scrapeMovieURL", movie_data)
            )
        ]
    )

    result = await respx_stash_client.scrape_movie_url(
        "https://example.com/movie/classic"
    )

    assert result is not None
    assert result.name == "Classic Movie"
    assert result.duration == "5400"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "scrapeMovieURL" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_group_url(respx_stash_client: StashClient) -> None:
    """Test scraping group from URL using dedicated method."""
    group_data = create_scraped_group_dict(
        name="Film Series",
        aliases="Series 1, Series One",
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("scrapeGroupURL", group_data)
            )
        ]
    )

    result = await respx_stash_client.scrape_group_url(
        "https://example.com/group/series"
    )

    assert result is not None
    assert result.name == "Film Series"
    assert result.aliases == "Series 1, Series One"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "scrapeGroupURL" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_url_methods_return_none_on_error(
    respx_stash_client: StashClient,
) -> None:
    """Test that specific scrape URL methods return None on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    result = await respx_stash_client.scrape_scene_url(
        "https://example.com/scene/error"
    )

    assert result is None
    assert len(graphql_route.calls) == 1
