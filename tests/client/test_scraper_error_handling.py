"""Unit tests for ScraperClientMixin error handling.

These tests specifically cover exception paths to improve code coverage.
"""

import httpx
import pytest
import respx

from stash_graphql_client import StashClient
from stash_graphql_client.types import (
    ScrapeContentType,
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


# =============================================================================
# Exception handling tests for all scraper methods
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_multi_scenes_exception(respx_stash_client: StashClient) -> None:
    """Test scrape_multi_scenes handles exceptions gracefully."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=Exception("Network error")
    )

    source = ScraperSourceInput(scraper_id="test-scraper")
    input_data = ScrapeMultiScenesInput(scene_ids=["1", "2"])

    scenes = await respx_stash_client.scrape_multi_scenes(source, input_data)

    assert len(scenes) == 0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_single_studio_exception(respx_stash_client: StashClient) -> None:
    """Test scrape_single_studio handles exceptions gracefully."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=Exception("Network error")
    )

    source = ScraperSourceInput(scraper_id="test-scraper")
    input_data = ScrapeSingleStudioInput(query="Test Studio")

    studios = await respx_stash_client.scrape_single_studio(source, input_data)

    assert len(studios) == 0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_multi_performers_exception(
    respx_stash_client: StashClient,
) -> None:
    """Test scrape_multi_performers handles exceptions gracefully."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=Exception("Network error")
    )

    source = ScraperSourceInput(scraper_id="test-scraper")
    input_data = ScrapeMultiPerformersInput(performer_ids=["1", "2"])

    performers = await respx_stash_client.scrape_multi_performers(source, input_data)

    assert len(performers) == 0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_single_gallery_exception(respx_stash_client: StashClient) -> None:
    """Test scrape_single_gallery handles exceptions gracefully."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=Exception("Network error")
    )

    source = ScraperSourceInput(scraper_id="test-scraper")
    input_data = ScrapeSingleGalleryInput(query="Test Gallery")

    galleries = await respx_stash_client.scrape_single_gallery(source, input_data)

    assert len(galleries) == 0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_single_group_exception(respx_stash_client: StashClient) -> None:
    """Test scrape_single_group handles exceptions gracefully."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=Exception("Network error")
    )

    source = ScraperSourceInput(scraper_id="test-scraper")
    input_data = ScrapeSingleGroupInput(query="Test Group")

    groups = await respx_stash_client.scrape_single_group(source, input_data)

    assert len(groups) == 0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_single_image_exception(respx_stash_client: StashClient) -> None:
    """Test scrape_single_image handles exceptions gracefully."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=Exception("Network error")
    )

    source = ScraperSourceInput(scraper_id="test-scraper")
    input_data = ScrapeSingleImageInput(query="Test Image")

    images = await respx_stash_client.scrape_single_image(source, input_data)

    assert len(images) == 0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_url_exception(respx_stash_client: StashClient) -> None:
    """Test scrapeURL handles exceptions gracefully."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=Exception("Network error")
    )

    content = await respx_stash_client.scrape_url(
        url="https://example.com", ty=ScrapeContentType.SCENE
    )

    assert content is None


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_performer_url_exception(respx_stash_client: StashClient) -> None:
    """Test scrapePerformerURL handles exceptions gracefully."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=Exception("Network error")
    )

    performer = await respx_stash_client.scrape_performer_url("https://example.com")

    assert performer is None


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_scene_url_exception(respx_stash_client: StashClient) -> None:
    """Test scrapeSceneURL handles exceptions gracefully."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=Exception("Network error")
    )

    scene = await respx_stash_client.scrape_scene_url("https://example.com")

    assert scene is None


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_gallery_url_exception(respx_stash_client: StashClient) -> None:
    """Test scrapeGalleryURL handles exceptions gracefully."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=Exception("Network error")
    )

    gallery = await respx_stash_client.scrape_gallery_url("https://example.com")

    assert gallery is None


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_image_url_exception(respx_stash_client: StashClient) -> None:
    """Test scrapeImageURL handles exceptions gracefully."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=Exception("Network error")
    )

    image = await respx_stash_client.scrape_image_url("https://example.com")

    assert image is None


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_group_url_exception(respx_stash_client: StashClient) -> None:
    """Test scrapeGroupURL handles exceptions gracefully."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=Exception("Network error")
    )

    group = await respx_stash_client.scrape_group_url("https://example.com")

    assert group is None


# Additional tests for scrape_single_scene and scrape_single_performer exception handling
# These methods also have exception handlers that need coverage


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_single_scene_exception(respx_stash_client: StashClient) -> None:
    """Test scrape_single_scene handles exceptions gracefully."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=Exception("Network error")
    )

    source = ScraperSourceInput(scraper_id="test-scraper")
    input_data = ScrapeSingleSceneInput(query="Test Scene")

    scenes = await respx_stash_client.scrape_single_scene(source, input_data)

    assert len(scenes) == 0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_single_performer_exception(
    respx_stash_client: StashClient,
) -> None:
    """Test scrape_single_performer handles exceptions gracefully."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=Exception("Network error")
    )

    source = ScraperSourceInput(scraper_id="test-scraper")
    input_data = ScrapeSinglePerformerInput(query="Test Performer")

    performers = await respx_stash_client.scrape_single_performer(source, input_data)

    assert len(performers) == 0


# =============================================================================
# False branch tests (when result doesn't contain expected field)
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_single_studio_empty_result(
    respx_stash_client: StashClient,
) -> None:
    """Test scrape_single_studio when result doesn't contain scrapeSingleStudio (line 330)."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(200, json={"data": {"scrapeSingleStudio": None}})]
    )

    source = ScraperSourceInput(scraper_id="test-scraper")
    input_data = ScrapeSingleStudioInput(query="Test Studio")

    studios = await respx_stash_client.scrape_single_studio(source, input_data)

    assert len(studios) == 0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_single_performer_empty_result(
    respx_stash_client: StashClient,
) -> None:
    """Test scrape_single_performer when result doesn't contain scrapeSinglePerformer (line 411)."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json={"data": {"scrapeSinglePerformer": None}})
        ]
    )

    source = ScraperSourceInput(scraper_id="test-scraper")
    input_data = ScrapeSinglePerformerInput(query="Test Performer")

    performers = await respx_stash_client.scrape_single_performer(source, input_data)

    assert len(performers) == 0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_multi_performers_empty_result(
    respx_stash_client: StashClient,
) -> None:
    """Test scrape_multi_performers when result doesn't contain scrapeMultiPerformers (line 488)."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json={"data": {"scrapeMultiPerformers": None}})
        ]
    )

    source = ScraperSourceInput(scraper_id="test-scraper")
    input_data = ScrapeMultiPerformersInput(performer_ids=["1", "2"])

    performers = await respx_stash_client.scrape_multi_performers(source, input_data)

    assert len(performers) == 0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_single_gallery_empty_result(
    respx_stash_client: StashClient,
) -> None:
    """Test scrape_single_gallery when result doesn't contain scrapeSingleGallery (line 559)."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(200, json={"data": {"scrapeSingleGallery": None}})]
    )

    source = ScraperSourceInput(scraper_id="test-scraper")
    input_data = ScrapeSingleGalleryInput(query="Test Gallery")

    galleries = await respx_stash_client.scrape_single_gallery(source, input_data)

    assert len(galleries) == 0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_single_movie_empty_result(
    respx_stash_client: StashClient,
) -> None:
    """Test scrape_single_movie when result doesn't contain scrapeSingleMovie (line 627)."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(200, json={"data": {"scrapeSingleMovie": None}})]
    )

    source = ScraperSourceInput(scraper_id="test-scraper")
    input_data = ScrapeSingleMovieInput(query="Test Movie")

    movies = await respx_stash_client.scrape_single_movie(source, input_data)

    assert len(movies) == 0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_single_movie_exception(respx_stash_client: StashClient) -> None:
    """Test scrape_single_movie handles exceptions gracefully (lines 628-630)."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=Exception("Network error")
    )

    source = ScraperSourceInput(scraper_id="test-scraper")
    input_data = ScrapeSingleMovieInput(query="Test Movie")

    movies = await respx_stash_client.scrape_single_movie(source, input_data)

    assert len(movies) == 0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_single_group_empty_result(
    respx_stash_client: StashClient,
) -> None:
    """Test scrape_single_group when result doesn't contain scrapeSingleGroup (line 699)."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(200, json={"data": {"scrapeSingleGroup": None}})]
    )

    source = ScraperSourceInput(scraper_id="test-scraper")
    input_data = ScrapeSingleGroupInput(query="Test Group")

    groups = await respx_stash_client.scrape_single_group(source, input_data)

    assert len(groups) == 0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_single_image_empty_result(
    respx_stash_client: StashClient,
) -> None:
    """Test scrape_single_image when result doesn't contain scrapeSingleImage (line 770)."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(200, json={"data": {"scrapeSingleImage": None}})]
    )

    source = ScraperSourceInput(scraper_id="test-scraper")
    input_data = ScrapeSingleImageInput(query="Test Image")

    images = await respx_stash_client.scrape_single_image(source, input_data)

    assert len(images) == 0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_performer_url_empty_result(
    respx_stash_client: StashClient,
) -> None:
    """Test scrapePerformerURL when result doesn't contain scrapePerformerURL (line 965)."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(200, json={"data": {"scrapePerformerURL": None}})]
    )

    performer = await respx_stash_client.scrape_performer_url("https://example.com")

    assert performer is None


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_scene_url_empty_result(respx_stash_client: StashClient) -> None:
    """Test scrapeSceneURL when result doesn't contain scrapeSceneURL (line 1028)."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(200, json={"data": {"scrapeSceneURL": None}})]
    )

    scene = await respx_stash_client.scrape_scene_url("https://example.com")

    assert scene is None


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_gallery_url_empty_result(respx_stash_client: StashClient) -> None:
    """Test scrapeGalleryURL when result doesn't contain scrapeGalleryURL (line 1083)."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(200, json={"data": {"scrapeGalleryURL": None}})]
    )

    gallery = await respx_stash_client.scrape_gallery_url("https://example.com")

    assert gallery is None


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_group_url_empty_result(respx_stash_client: StashClient) -> None:
    """Test scrapeGroupURL when result doesn't contain scrapeGroupURL (line 1138)."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(200, json={"data": {"scrapeGroupURL": None}})]
    )

    group = await respx_stash_client.scrape_group_url("https://example.com")

    assert group is None


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_movie_url_empty_result(respx_stash_client: StashClient) -> None:
    """Test scrapeMovieURL when result doesn't contain scrapeMovieURL (line 1197)."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(200, json={"data": {"scrapeMovieURL": None}})]
    )

    movie = await respx_stash_client.scrape_movie_url("https://example.com")

    assert movie is None


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_movie_url_exception(respx_stash_client: StashClient) -> None:
    """Test scrapeMovieURL handles exceptions gracefully (lines 1198-1200)."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=Exception("Network error")
    )

    movie = await respx_stash_client.scrape_movie_url("https://example.com")

    assert movie is None


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scrape_image_url_empty_result(respx_stash_client: StashClient) -> None:
    """Test scrapeImageURL when result doesn't contain scrapeImageURL (line 1253)."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(200, json={"data": {"scrapeImageURL": None}})]
    )

    image = await respx_stash_client.scrape_image_url("https://example.com")

    assert image is None
