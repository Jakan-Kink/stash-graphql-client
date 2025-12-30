"""Unit tests for ScraperClientMixin single/multi scraping and mutation operations.

These tests mock at the HTTP boundary using respx, allowing real code execution
through the entire GraphQL client stack including serialization/deserialization.
"""

import json

import httpx
import pytest
import respx

from stash_graphql_client import StashClient
from stash_graphql_client.types import (
    ScrapeMultiPerformersInput,
    ScrapeMultiScenesInput,
    ScraperSourceInput,
    ScrapeSingleGalleryInput,
    ScrapeSingleGroupInput,
    ScrapeSingleImageInput,
    ScrapeSingleMovieInput,
    ScrapeSinglePerformerInput,
    ScrapeSingleSceneInput,
    ScrapeSingleStudioInput,
)
from stash_graphql_client.types.unset import is_set
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
        "urls": urls or [],
    }


def create_scraped_performer_dict(
    stored_id: str | None = None,
    name: str = "Performer Name",
    gender: str | None = None,
    urls: list[str] | None = None,
) -> dict:
    """Create a ScrapedPerformer dictionary for testing."""
    return {
        "stored_id": stored_id,
        "name": name,
        "gender": gender,
        "urls": urls or [],
    }


def create_scraped_scene_dict(
    title: str = "Scene Title",
    code: str | None = None,
    details: str | None = None,
    urls: list[str] | None = None,
    date: str | None = None,
) -> dict:
    """Create a ScrapedScene dictionary for testing."""
    return {
        "title": title,
        "code": code,
        "details": details,
        "urls": urls or [],
        "date": date,
    }


def create_scraped_gallery_dict(
    title: str = "Gallery Title",
    code: str | None = None,
    details: str | None = None,
) -> dict:
    """Create a ScrapedGallery dictionary for testing."""
    return {
        "title": title,
        "code": code,
        "details": details,
    }


def create_scraped_image_dict(
    title: str = "Image Title",
    code: str | None = None,
    details: str | None = None,
) -> dict:
    """Create a ScrapedImage dictionary for testing."""
    return {
        "title": title,
        "code": code,
        "details": details,
    }


def create_scraped_movie_dict(
    stored_id: str | None = None,
    name: str = "Movie Name",
    aliases: str | None = None,
) -> dict:
    """Create a ScrapedMovie dictionary for testing."""
    return {
        "stored_id": stored_id,
        "name": name,
        "aliases": aliases,
    }


def create_scraped_group_dict(
    stored_id: str | None = None,
    name: str = "Group Name",
    aliases: str | None = None,
) -> dict:
    """Create a ScrapedGroup dictionary for testing."""
    return {
        "stored_id": stored_id,
        "name": name,
        "aliases": aliases,
    }


# =============================================================================
# scrape_single_scene tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_single_scene_by_query(respx_stash_client: StashClient) -> None:
    """Test scraping single scene by query string."""
    scene_data = create_scraped_scene_dict(
        title="Test Scene",
        code="TS-001",
        date="2024-01-15",
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("scrapeSingleScene", [scene_data])
            )
        ]
    )

    source = ScraperSourceInput(scraper_id="scraper-123")
    input_data = ScrapeSingleSceneInput(query="Test Scene")

    scenes = await respx_stash_client.scrape_single_scene(source, input_data)

    assert len(scenes) == 1
    assert scenes[0].title == "Test Scene"
    assert scenes[0].code == "TS-001"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "scrapeSingleScene" in req["query"]
    assert "source" in req["variables"]
    assert "input" in req["variables"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_single_scene_by_id(respx_stash_client: StashClient) -> None:
    """Test scraping single scene by scene ID."""
    scene_data = create_scraped_scene_dict(title="Scene by ID")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("scrapeSingleScene", [scene_data])
            )
        ]
    )

    source = ScraperSourceInput(scraper_id="scraper-123")
    input_data = ScrapeSingleSceneInput(scene_id="scene-456")

    scenes = await respx_stash_client.scrape_single_scene(source, input_data)

    assert len(scenes) == 1
    assert scenes[0].title == "Scene by ID"

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_single_scene_from_stashbox(
    respx_stash_client: StashClient,
) -> None:
    """Test scraping single scene from StashBox endpoint."""
    scene_data = create_scraped_scene_dict(title="StashBox Scene")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("scrapeSingleScene", [scene_data])
            )
        ]
    )

    source = ScraperSourceInput(stash_box_endpoint="https://stashdb.org")
    input_data = ScrapeSingleSceneInput(query="StashBox Scene")

    scenes = await respx_stash_client.scrape_single_scene(source, input_data)

    assert len(scenes) == 1
    assert scenes[0].title == "StashBox Scene"

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_single_scene_multiple_results(
    respx_stash_client: StashClient,
) -> None:
    """Test scraping single scene returning multiple matches."""
    scenes_data = [
        create_scraped_scene_dict(title="Match 1", code="M1-001"),
        create_scraped_scene_dict(title="Match 2", code="M2-002"),
        create_scraped_scene_dict(title="Match 3", code="M3-003"),
    ]

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("scrapeSingleScene", scenes_data)
            )
        ]
    )

    source = ScraperSourceInput(scraper_id="scraper-123")
    input_data = ScrapeSingleSceneInput(query="ambiguous")

    scenes = await respx_stash_client.scrape_single_scene(source, input_data)

    assert len(scenes) == 3
    assert scenes[0].title == "Match 1"
    assert scenes[1].title == "Match 2"
    assert scenes[2].title == "Match 3"

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_single_scene_empty_result(
    respx_stash_client: StashClient,
) -> None:
    """Test scraping single scene with no results."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("scrapeSingleScene", []))
        ]
    )

    source = ScraperSourceInput(scraper_id="scraper-123")
    input_data = ScrapeSingleSceneInput(query="nonexistent")

    scenes = await respx_stash_client.scrape_single_scene(source, input_data)

    assert len(scenes) == 0
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_single_scene_error_returns_empty(
    respx_stash_client: StashClient,
) -> None:
    """Test that scrape_single_scene returns empty list on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    source = ScraperSourceInput(scraper_id="scraper-123")
    input_data = ScrapeSingleSceneInput(query="error")

    scenes = await respx_stash_client.scrape_single_scene(source, input_data)

    assert len(scenes) == 0
    assert len(graphql_route.calls) == 1


# =============================================================================
# scrape_multi_scenes tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_multi_scenes(respx_stash_client: StashClient) -> None:
    """Test scraping multiple scenes."""
    results_data = [
        [
            create_scraped_scene_dict(title="Scene 1A"),
            create_scraped_scene_dict(title="Scene 1B"),
        ],
        [create_scraped_scene_dict(title="Scene 2A")],
        [],
    ]

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("scrapeMultiScenes", results_data)
            )
        ]
    )

    source = ScraperSourceInput(scraper_id="scraper-123")
    input_data = ScrapeMultiScenesInput(scene_ids=["1", "2", "3"])

    results = await respx_stash_client.scrape_multi_scenes(source, input_data)

    assert len(results) == 3
    assert len(results[0]) == 2
    assert results[0][0].title == "Scene 1A"
    assert results[0][1].title == "Scene 1B"
    assert len(results[1]) == 1
    assert results[1][0].title == "Scene 2A"
    assert len(results[2]) == 0

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "scrapeMultiScenes" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_multi_scenes_empty_result(
    respx_stash_client: StashClient,
) -> None:
    """Test scraping multiple scenes with no results."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("scrapeMultiScenes", []))
        ]
    )

    source = ScraperSourceInput(scraper_id="scraper-123")
    input_data = ScrapeMultiScenesInput(scene_ids=["nonexistent"])

    results = await respx_stash_client.scrape_multi_scenes(source, input_data)

    assert len(results) == 0
    assert len(graphql_route.calls) == 1


# =============================================================================
# scrape_single_studio tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_single_studio(respx_stash_client: StashClient) -> None:
    """Test scraping single studio."""
    studio_data = create_scraped_studio_dict(
        name="Test Studio",
        urls=["https://example.com/studio"],
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("scrapeSingleStudio", [studio_data])
            )
        ]
    )

    source = ScraperSourceInput(scraper_id="scraper-123")
    input_data = ScrapeSingleStudioInput(query="Test Studio")

    studios = await respx_stash_client.scrape_single_studio(source, input_data)

    assert len(studios) == 1
    assert studios[0].name == "Test Studio"
    assert is_set(studios[0].urls)
    assert studios[0].urls is not None
    assert len(studios[0].urls) == 1

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "scrapeSingleStudio" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_single_studio_multiple_results(
    respx_stash_client: StashClient,
) -> None:
    """Test scraping single studio with multiple matches."""
    studios_data = [
        create_scraped_studio_dict(name="Studio A"),
        create_scraped_studio_dict(name="Studio B"),
    ]

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("scrapeSingleStudio", studios_data)
            )
        ]
    )

    source = ScraperSourceInput(scraper_id="scraper-123")
    input_data = ScrapeSingleStudioInput(query="Studio")

    studios = await respx_stash_client.scrape_single_studio(source, input_data)

    assert len(studios) == 2
    assert studios[0].name == "Studio A"
    assert studios[1].name == "Studio B"

    assert len(graphql_route.calls) == 1


# =============================================================================
# scrape_single_performer tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_single_performer_by_query(
    respx_stash_client: StashClient,
) -> None:
    """Test scraping single performer by query."""
    performer_data = create_scraped_performer_dict(
        name="Jane Doe",
        gender="FEMALE",
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response("scrapeSinglePerformer", [performer_data]),
            )
        ]
    )

    source = ScraperSourceInput(scraper_id="scraper-123")
    input_data = ScrapeSinglePerformerInput(query="Jane Doe")

    performers = await respx_stash_client.scrape_single_performer(source, input_data)

    assert len(performers) == 1
    assert performers[0].name == "Jane Doe"
    assert performers[0].gender == "FEMALE"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "scrapeSinglePerformer" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_single_performer_by_id(respx_stash_client: StashClient) -> None:
    """Test scraping single performer by performer ID."""
    performer_data = create_scraped_performer_dict(name="Performer by ID")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response("scrapeSinglePerformer", [performer_data]),
            )
        ]
    )

    source = ScraperSourceInput(scraper_id="scraper-123")
    input_data = ScrapeSinglePerformerInput(performer_id="123")

    performers = await respx_stash_client.scrape_single_performer(source, input_data)

    assert len(performers) == 1
    assert performers[0].name == "Performer by ID"

    assert len(graphql_route.calls) == 1


# =============================================================================
# scrape_multi_performers tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_multi_performers(respx_stash_client: StashClient) -> None:
    """Test scraping multiple performers."""
    results_data = [
        [
            create_scraped_performer_dict(name="Perf 1A"),
            create_scraped_performer_dict(name="Perf 1B"),
        ],
        [create_scraped_performer_dict(name="Perf 2A")],
    ]

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("scrapeMultiPerformers", results_data)
            )
        ]
    )

    source = ScraperSourceInput(scraper_id="scraper-123")
    input_data = ScrapeMultiPerformersInput(performer_ids=["1", "2"])

    results = await respx_stash_client.scrape_multi_performers(source, input_data)

    assert len(results) == 2
    assert len(results[0]) == 2
    assert results[0][0].name == "Perf 1A"
    assert results[0][1].name == "Perf 1B"
    assert len(results[1]) == 1
    assert results[1][0].name == "Perf 2A"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "scrapeMultiPerformers" in req["query"]


# =============================================================================
# scrape_single_gallery tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_single_gallery(respx_stash_client: StashClient) -> None:
    """Test scraping single gallery."""
    gallery_data = create_scraped_gallery_dict(
        title="Test Gallery",
        code="GAL-001",
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("scrapeSingleGallery", [gallery_data])
            )
        ]
    )

    source = ScraperSourceInput(scraper_id="scraper-123")
    input_data = ScrapeSingleGalleryInput(query="Test Gallery")

    galleries = await respx_stash_client.scrape_single_gallery(source, input_data)

    assert len(galleries) == 1
    assert galleries[0].title == "Test Gallery"
    assert galleries[0].code == "GAL-001"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "scrapeSingleGallery" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_single_gallery_by_id(respx_stash_client: StashClient) -> None:
    """Test scraping single gallery by gallery ID."""
    gallery_data = create_scraped_gallery_dict(title="Gallery by ID")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("scrapeSingleGallery", [gallery_data])
            )
        ]
    )

    source = ScraperSourceInput(scraper_id="scraper-123")
    input_data = ScrapeSingleGalleryInput(gallery_id="456")

    galleries = await respx_stash_client.scrape_single_gallery(source, input_data)

    assert len(galleries) == 1
    assert galleries[0].title == "Gallery by ID"

    assert len(graphql_route.calls) == 1


# =============================================================================
# scrape_single_movie tests (deprecated)
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_single_movie(respx_stash_client: StashClient) -> None:
    """Test scraping single movie using deprecated method."""
    movie_data = create_scraped_movie_dict(
        name="Test Movie",
        aliases="TM",
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("scrapeSingleMovie", [movie_data])
            )
        ]
    )

    source = ScraperSourceInput(scraper_id="scraper-123")
    input_data = ScrapeSingleMovieInput(query="Test Movie")

    movies = await respx_stash_client.scrape_single_movie(source, input_data)

    assert len(movies) == 1
    assert movies[0].name == "Test Movie"
    assert movies[0].aliases == "TM"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "scrapeSingleMovie" in req["query"]


# =============================================================================
# scrape_single_group tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_single_group(respx_stash_client: StashClient) -> None:
    """Test scraping single group."""
    group_data = create_scraped_group_dict(
        name="Test Group",
        aliases="TG, Test G",
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("scrapeSingleGroup", [group_data])
            )
        ]
    )

    source = ScraperSourceInput(scraper_id="scraper-123")
    input_data = ScrapeSingleGroupInput(query="Test Group")

    groups = await respx_stash_client.scrape_single_group(source, input_data)

    assert len(groups) == 1
    assert groups[0].name == "Test Group"
    assert groups[0].aliases == "TG, Test G"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "scrapeSingleGroup" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_single_group_by_id(respx_stash_client: StashClient) -> None:
    """Test scraping single group by group ID."""
    group_data = create_scraped_group_dict(name="Group by ID")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("scrapeSingleGroup", [group_data])
            )
        ]
    )

    source = ScraperSourceInput(scraper_id="scraper-123")
    input_data = ScrapeSingleGroupInput(group_id="789")

    groups = await respx_stash_client.scrape_single_group(source, input_data)

    assert len(groups) == 1
    assert groups[0].name == "Group by ID"

    assert len(graphql_route.calls) == 1


# =============================================================================
# scrape_single_image tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_single_image(respx_stash_client: StashClient) -> None:
    """Test scraping single image."""
    image_data = create_scraped_image_dict(
        title="Test Image",
        code="IMG-001",
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("scrapeSingleImage", [image_data])
            )
        ]
    )

    source = ScraperSourceInput(scraper_id="scraper-123")
    input_data = ScrapeSingleImageInput(query="Test Image")

    images = await respx_stash_client.scrape_single_image(source, input_data)

    assert len(images) == 1
    assert images[0].title == "Test Image"
    assert images[0].code == "IMG-001"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "scrapeSingleImage" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_single_image_by_id(respx_stash_client: StashClient) -> None:
    """Test scraping single image by image ID."""
    image_data = create_scraped_image_dict(title="Image by ID")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("scrapeSingleImage", [image_data])
            )
        ]
    )

    source = ScraperSourceInput(scraper_id="scraper-123")
    input_data = ScrapeSingleImageInput(image_id="101")

    images = await respx_stash_client.scrape_single_image(source, input_data)

    assert len(images) == 1
    assert images[0].title == "Image by ID"

    assert len(graphql_route.calls) == 1


# =============================================================================
# reload_scrapers mutation tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_reload_scrapers_success(respx_stash_client: StashClient) -> None:
    """Test reloading scrapers successfully."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("reloadScrapers", True))
        ]
    )

    result = await respx_stash_client.reload_scrapers()

    assert result is True

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "reloadScrapers" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_reload_scrapers_failure(respx_stash_client: StashClient) -> None:
    """Test reloading scrapers returning false."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("reloadScrapers", False))
        ]
    )

    result = await respx_stash_client.reload_scrapers()

    assert result is False
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_reload_scrapers_error_returns_false(
    respx_stash_client: StashClient,
) -> None:
    """Test that reload_scrapers returns False on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    result = await respx_stash_client.reload_scrapers()

    assert result is False
    assert len(graphql_route.calls) == 1
