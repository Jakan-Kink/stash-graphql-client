"""Scraper-related client functionality."""

from typing import Any

from ... import fragments
from ...types import (
    ScrapeContentType,
    ScrapedGallery,
    ScrapedGroup,
    ScrapedImage,
    ScrapedMovie,
    ScrapedPerformer,
    ScrapedScene,
    ScrapedStudio,
    ScrapeMultiPerformersInput,
    ScrapeMultiScenesInput,
    Scraper,
    ScraperSourceInput,
    ScrapeSingleGalleryInput,
    ScrapeSingleGroupInput,
    ScrapeSingleImageInput,
    ScrapeSingleMovieInput,
    ScrapeSinglePerformerInput,
    ScrapeSingleSceneInput,
    ScrapeSingleStudioInput,
    StashBoxDraftSubmissionInput,
    StashBoxFingerprintSubmissionInput,
)
from ..protocols import StashClientProtocol


class ScraperClientMixin(StashClientProtocol):
    """Mixin for scraper-related client methods."""

    async def list_scrapers(
        self,
        types: list[ScrapeContentType],
    ) -> list[Scraper]:
        """List available scrapers filtered by content types.

        Args:
            types: List of content types to filter scrapers by
                (GALLERY, IMAGE, MOVIE, GROUP, PERFORMER, SCENE)

        Returns:
            List of Scraper objects matching the requested types

        Examples:
            List all scene scrapers:
            ```python
            scrapers = await client.list_scrapers([ScrapeContentType.SCENE])
            for scraper in scrapers:
                print(f"Scene scraper: {scraper.name}")
            ```

            List multiple scraper types:
            ```python
            from stash_graphql_client.types import ScrapeContentType
            scrapers = await client.list_scrapers([
                ScrapeContentType.SCENE,
                ScrapeContentType.PERFORMER
            ])
            ```

            Check scraper capabilities:
            ```python
            scrapers = await client.list_scrapers([ScrapeContentType.SCENE])
            for scraper in scrapers:
                if scraper.scene:
                    print(f"{scraper.name} supports: {scraper.scene.supported_scrapes}")
                    print(f"URLs: {scraper.scene.urls}")
            ```
        """
        query = """
            query ListScrapers($types: [ScrapeContentType!]!) {
                listScrapers(types: $types) {
                    id
                    name
                    performer {
                        urls
                        supported_scrapes
                    }
                    scene {
                        urls
                        supported_scrapes
                    }
                    gallery {
                        urls
                        supported_scrapes
                    }
                    image {
                        urls
                        supported_scrapes
                    }
                    group {
                        urls
                        supported_scrapes
                    }
                }
            }
        """
        try:
            result = await self.execute(
                query,
                {
                    "types": [
                        t.value if isinstance(t, ScrapeContentType) else t
                        for t in types
                    ]
                },
            )
            if result and result.get("listScrapers"):
                return [
                    self._decode_result(Scraper, scraper_data)
                    for scraper_data in result["listScrapers"]
                ]
            return []
        except Exception as e:
            self.log.error(f"Failed to list scrapers: {e}")
            return []

    async def scrape_single_scene(
        self,
        source: ScraperSourceInput,
        input: ScrapeSingleSceneInput,
    ) -> list[ScrapedScene]:
        """Scrape for a single scene.

        Args:
            source: Scraper source (scraper_id or stash_box_endpoint)
            input: Scene scraping input (query, scene_id, or scene_input)

        Returns:
            List of ScrapedScene objects

        Examples:
            Scrape by query string:
            ```python
            source = ScraperSourceInput(scraper_id="scraper-123")
            input = ScrapeSingleSceneInput(query="scene title")
            scenes = await client.scrape_single_scene(source, input)
            ```

            Scrape by scene ID (using fingerprints):
            ```python
            source = ScraperSourceInput(scraper_id="scraper-123")
            input = ScrapeSingleSceneInput(scene_id="scene-456")
            scenes = await client.scrape_single_scene(source, input)
            ```

            Scrape from StashBox:
            ```python
            source = ScraperSourceInput(stash_box_endpoint="https://stashdb.org")
            input = ScrapeSingleSceneInput(query="scene title")
            scenes = await client.scrape_single_scene(source, input)
            ```
        """
        query = """
            query ScrapeSingleScene($source: ScraperSourceInput!, $input: ScrapeSingleSceneInput!) {
                scrapeSingleScene(source: $source, input: $input) {
                    title
                    code
                    details
                    director
                    urls
                    date
                    image
                    studio {
                        stored_id
                        name
                        urls
                    }
                    tags {
                        stored_id
                        name
                    }
                    performers {
                        stored_id
                        name
                        gender
                        urls
                    }
                    groups {
                        stored_id
                        name
                    }
                    remote_site_id
                    duration
                }
            }
        """
        try:
            result = await self.execute(
                query,
                {
                    "source": source.to_graphql()
                    if hasattr(source, "to_graphql")
                    else source,
                    "input": input.to_graphql()
                    if hasattr(input, "to_graphql")
                    else input,
                },
            )
            if result and result.get("scrapeSingleScene"):
                return [
                    self._decode_result(ScrapedScene, scene_data)
                    for scene_data in result["scrapeSingleScene"]
                ]
            return []
        except Exception as e:
            self.log.error(f"Failed to scrape single scene: {e}")
            return []

    async def scrape_multi_scenes(
        self,
        source: ScraperSourceInput,
        input: ScrapeMultiScenesInput,
    ) -> list[list[ScrapedScene]]:
        """Scrape for multiple scenes.

        Args:
            source: Scraper source (scraper_id or stash_box_endpoint)
            input: Multi-scene scraping input (scene_ids)

        Returns:
            List of lists of ScrapedScene objects (one list per input scene)

        Examples:
            Scrape multiple scenes:
            ```python
            source = ScraperSourceInput(scraper_id="scraper-123")
            input = ScrapeMultiScenesInput(scene_ids=["1", "2", "3"])
            results = await client.scrape_multi_scenes(source, input)
            for i, scenes in enumerate(results):
                print(f"Scene {i+1}: {len(scenes)} matches found")
            ```
        """
        query = """
            query ScrapeMultiScenes($source: ScraperSourceInput!, $input: ScrapeMultiScenesInput!) {
                scrapeMultiScenes(source: $source, input: $input) {
                    title
                    code
                    details
                    director
                    urls
                    date
                    image
                    studio {
                        stored_id
                        name
                    }
                    tags {
                        stored_id
                        name
                    }
                    performers {
                        stored_id
                        name
                    }
                    remote_site_id
                    duration
                }
            }
        """
        try:
            result = await self.execute(
                query,
                {
                    "source": source.to_graphql()
                    if hasattr(source, "to_graphql")
                    else source,
                    "input": input.to_graphql()
                    if hasattr(input, "to_graphql")
                    else input,
                },
            )
            if result and result.get("scrapeMultiScenes"):
                return [
                    [
                        self._decode_result(ScrapedScene, scene_data)
                        for scene_data in scene_list
                    ]
                    for scene_list in result["scrapeMultiScenes"]
                ]
            return []
        except Exception as e:
            self.log.error(f"Failed to scrape multiple scenes: {e}")
            return []

    async def scrape_single_studio(
        self,
        source: ScraperSourceInput,
        input: ScrapeSingleStudioInput,
    ) -> list[ScrapedStudio]:
        """Scrape for a single studio.

        Args:
            source: Scraper source (scraper_id or stash_box_endpoint)
            input: Studio scraping input (query - can be name or Stash ID)

        Returns:
            List of ScrapedStudio objects

        Examples:
            Scrape studio by name:
            ```python
            source = ScraperSourceInput(scraper_id="scraper-123")
            input = ScrapeSingleStudioInput(query="Studio Name")
            studios = await client.scrape_single_studio(source, input)
            ```
        """
        query = """
            query ScrapeSingleStudio($source: ScraperSourceInput!, $input: ScrapeSingleStudioInput!) {
                scrapeSingleStudio(source: $source, input: $input) {
                    stored_id
                    name
                    urls
                    parent {
                        stored_id
                        name
                    }
                    image
                    details
                    aliases
                    tags {
                        stored_id
                        name
                    }
                    remote_site_id
                }
            }
        """
        try:
            result = await self.execute(
                query,
                {
                    "source": source.to_graphql()
                    if hasattr(source, "to_graphql")
                    else source,
                    "input": input.to_graphql()
                    if hasattr(input, "to_graphql")
                    else input,
                },
            )
            if result and result.get("scrapeSingleStudio"):
                return [
                    self._decode_result(ScrapedStudio, studio_data)
                    for studio_data in result["scrapeSingleStudio"]
                ]
            return []
        except Exception as e:
            self.log.error(f"Failed to scrape single studio: {e}")
            return []

    async def scrape_single_performer(
        self,
        source: ScraperSourceInput,
        input: ScrapeSinglePerformerInput,
    ) -> list[ScrapedPerformer]:
        """Scrape for a single performer.

        Args:
            source: Scraper source (scraper_id or stash_box_endpoint)
            input: Performer scraping input (query, performer_id, or performer_input)

        Returns:
            List of ScrapedPerformer objects

        Examples:
            Scrape by query string:
            ```python
            source = ScraperSourceInput(scraper_id="scraper-123")
            input = ScrapeSinglePerformerInput(query="Performer Name")
            performers = await client.scrape_single_performer(source, input)
            ```

            Scrape by performer ID:
            ```python
            source = ScraperSourceInput(scraper_id="scraper-123")
            input = ScrapeSinglePerformerInput(performer_id="123")
            performers = await client.scrape_single_performer(source, input)
            ```
        """
        query = """
            query ScrapeSinglePerformer($source: ScraperSourceInput!, $input: ScrapeSinglePerformerInput!) {
                scrapeSinglePerformer(source: $source, input: $input) {
                    stored_id
                    name
                    disambiguation
                    gender
                    urls
                    birthdate
                    ethnicity
                    country
                    eye_color
                    height
                    measurements
                    fake_tits
                    penis_length
                    circumcised
                    career_length
                    tattoos
                    piercings
                    aliases
                    tags {
                        stored_id
                        name
                    }
                    images
                    details
                    death_date
                    hair_color
                    weight
                    remote_site_id
                }
            }
        """
        try:
            result = await self.execute(
                query,
                {
                    "source": source.to_graphql()
                    if hasattr(source, "to_graphql")
                    else source,
                    "input": input.to_graphql()
                    if hasattr(input, "to_graphql")
                    else input,
                },
            )
            if result and result.get("scrapeSinglePerformer"):
                return [
                    self._decode_result(ScrapedPerformer, performer_data)
                    for performer_data in result["scrapeSinglePerformer"]
                ]
            return []
        except Exception as e:
            self.log.error(f"Failed to scrape single performer: {e}")
            return []

    async def scrape_multi_performers(
        self,
        source: ScraperSourceInput,
        input: ScrapeMultiPerformersInput,
    ) -> list[list[ScrapedPerformer]]:
        """Scrape for multiple performers.

        Args:
            source: Scraper source (scraper_id or stash_box_endpoint)
            input: Multi-performer scraping input (performer_ids)

        Returns:
            List of lists of ScrapedPerformer objects (one list per input performer)

        Examples:
            Scrape multiple performers:
            ```python
            source = ScraperSourceInput(scraper_id="scraper-123")
            input = ScrapeMultiPerformersInput(performer_ids=["1", "2", "3"])
            results = await client.scrape_multi_performers(source, input)
            for i, performers in enumerate(results):
                print(f"Performer {i+1}: {len(performers)} matches found")
            ```
        """
        query = """
            query ScrapeMultiPerformers($source: ScraperSourceInput!, $input: ScrapeMultiPerformersInput!) {
                scrapeMultiPerformers(source: $source, input: $input) {
                    stored_id
                    name
                    disambiguation
                    gender
                    urls
                    birthdate
                    ethnicity
                    country
                    eye_color
                    height
                    measurements
                    fake_tits
                    career_length
                    tattoos
                    piercings
                    aliases
                    tags {
                        stored_id
                        name
                    }
                    images
                    details
                    death_date
                    hair_color
                    weight
                    remote_site_id
                }
            }
        """
        try:
            result = await self.execute(
                query,
                {
                    "source": source.to_graphql()
                    if hasattr(source, "to_graphql")
                    else source,
                    "input": input.to_graphql()
                    if hasattr(input, "to_graphql")
                    else input,
                },
            )
            if result and result.get("scrapeMultiPerformers"):
                return [
                    [
                        self._decode_result(ScrapedPerformer, performer_data)
                        for performer_data in performer_list
                    ]
                    for performer_list in result["scrapeMultiPerformers"]
                ]
            return []
        except Exception as e:
            self.log.error(f"Failed to scrape multiple performers: {e}")
            return []

    async def scrape_single_gallery(
        self,
        source: ScraperSourceInput,
        input: ScrapeSingleGalleryInput,
    ) -> list[ScrapedGallery]:
        """Scrape for a single gallery.

        Args:
            source: Scraper source (scraper_id or stash_box_endpoint)
            input: Gallery scraping input (query, gallery_id, or gallery_input)

        Returns:
            List of ScrapedGallery objects

        Examples:
            Scrape by query string:
            ```python
            source = ScraperSourceInput(scraper_id="scraper-123")
            input = ScrapeSingleGalleryInput(query="gallery title")
            galleries = await client.scrape_single_gallery(source, input)
            ```

            Scrape by gallery ID:
            ```python
            source = ScraperSourceInput(scraper_id="scraper-123")
            input = ScrapeSingleGalleryInput(gallery_id="456")
            galleries = await client.scrape_single_gallery(source, input)
            ```
        """
        query = """
            query ScrapeSingleGallery($source: ScraperSourceInput!, $input: ScrapeSingleGalleryInput!) {
                scrapeSingleGallery(source: $source, input: $input) {
                    title
                    code
                    details
                    photographer
                    urls
                    date
                    studio {
                        stored_id
                        name
                    }
                    tags {
                        stored_id
                        name
                    }
                    performers {
                        stored_id
                        name
                    }
                }
            }
        """
        try:
            result = await self.execute(
                query,
                {
                    "source": source.to_graphql()
                    if hasattr(source, "to_graphql")
                    else source,
                    "input": input.to_graphql()
                    if hasattr(input, "to_graphql")
                    else input,
                },
            )
            if result and result.get("scrapeSingleGallery"):
                return [
                    self._decode_result(ScrapedGallery, gallery_data)
                    for gallery_data in result["scrapeSingleGallery"]
                ]
            return []
        except Exception as e:
            self.log.error(f"Failed to scrape single gallery: {e}")
            return []

    async def scrape_single_movie(
        self,
        source: ScraperSourceInput,
        input: ScrapeSingleMovieInput,
    ) -> list[ScrapedMovie]:
        """Scrape for a single movie.

        .. deprecated::
            Use :meth:`scrape_single_group` instead.

        Args:
            source: Scraper source (scraper_id or stash_box_endpoint)
            input: Movie scraping input (query, movie_id, or movie_input)

        Returns:
            List of ScrapedMovie objects

        Examples:
            Scrape by query string:
            ```python
            source = ScraperSourceInput(scraper_id="scraper-123")
            input = ScrapeSingleMovieInput(query="movie title")
            movies = await client.scrape_single_movie(source, input)
            ```
        """
        query = """
            query ScrapeSingleMovie($source: ScraperSourceInput!, $input: ScrapeSingleMovieInput!) {
                scrapeSingleMovie(source: $source, input: $input) {
                    stored_id
                    name
                    aliases
                    duration
                    date
                    rating
                    director
                    urls
                    synopsis
                    studio {
                        stored_id
                        name
                    }
                    tags {
                        stored_id
                        name
                    }
                    front_image
                    back_image
                }
            }
        """
        try:
            result = await self.execute(
                query,
                {
                    "source": source.to_graphql()
                    if hasattr(source, "to_graphql")
                    else source,
                    "input": input.to_graphql()
                    if hasattr(input, "to_graphql")
                    else input,
                },
            )
            if result and result.get("scrapeSingleMovie"):
                return [
                    self._decode_result(ScrapedMovie, movie_data)
                    for movie_data in result["scrapeSingleMovie"]
                ]
            return []
        except Exception as e:
            self.log.error(f"Failed to scrape single movie: {e}")
            return []

    async def scrape_single_group(
        self,
        source: ScraperSourceInput,
        input: ScrapeSingleGroupInput,
    ) -> list[ScrapedGroup]:
        """Scrape for a single group.

        Args:
            source: Scraper source (scraper_id or stash_box_endpoint)
            input: Group scraping input (query, group_id, or group_input)

        Returns:
            List of ScrapedGroup objects

        Examples:
            Scrape by query string:
            ```python
            source = ScraperSourceInput(scraper_id="scraper-123")
            input = ScrapeSingleGroupInput(query="group title")
            groups = await client.scrape_single_group(source, input)
            ```

            Scrape by group ID:
            ```python
            source = ScraperSourceInput(scraper_id="scraper-123")
            input = ScrapeSingleGroupInput(group_id="789")
            groups = await client.scrape_single_group(source, input)
            ```
        """
        query = """
            query ScrapeSingleGroup($source: ScraperSourceInput!, $input: ScrapeSingleGroupInput!) {
                scrapeSingleGroup(source: $source, input: $input) {
                    stored_id
                    name
                    aliases
                    duration
                    date
                    rating
                    director
                    urls
                    synopsis
                    studio {
                        stored_id
                        name
                    }
                    tags {
                        stored_id
                        name
                    }
                    front_image
                    back_image
                }
            }
        """
        try:
            result = await self.execute(
                query,
                {
                    "source": source.to_graphql()
                    if hasattr(source, "to_graphql")
                    else source,
                    "input": input.to_graphql()
                    if hasattr(input, "to_graphql")
                    else input,
                },
            )
            if result and result.get("scrapeSingleGroup"):
                return [
                    self._decode_result(ScrapedGroup, group_data)
                    for group_data in result["scrapeSingleGroup"]
                ]
            return []
        except Exception as e:
            self.log.error(f"Failed to scrape single group: {e}")
            return []

    async def scrape_single_image(
        self,
        source: ScraperSourceInput,
        input: ScrapeSingleImageInput,
    ) -> list[ScrapedImage]:
        """Scrape for a single image.

        Args:
            source: Scraper source (scraper_id or stash_box_endpoint)
            input: Image scraping input (query, image_id, or image_input)

        Returns:
            List of ScrapedImage objects

        Examples:
            Scrape by query string:
            ```python
            source = ScraperSourceInput(scraper_id="scraper-123")
            input = ScrapeSingleImageInput(query="image title")
            images = await client.scrape_single_image(source, input)
            ```

            Scrape by image ID:
            ```python
            source = ScraperSourceInput(scraper_id="scraper-123")
            input = ScrapeSingleImageInput(image_id="101")
            images = await client.scrape_single_image(source, input)
            ```
        """
        query = """
            query ScrapeSingleImage($source: ScraperSourceInput!, $input: ScrapeSingleImageInput!) {
                scrapeSingleImage(source: $source, input: $input) {
                    title
                    code
                    details
                    photographer
                    urls
                    date
                    studio {
                        stored_id
                        name
                    }
                    tags {
                        stored_id
                        name
                    }
                    performers {
                        stored_id
                        name
                    }
                }
            }
        """
        try:
            result = await self.execute(
                query,
                {
                    "source": source.to_graphql()
                    if hasattr(source, "to_graphql")
                    else source,
                    "input": input.to_graphql()
                    if hasattr(input, "to_graphql")
                    else input,
                },
            )
            if result and result.get("scrapeSingleImage"):
                return [
                    self._decode_result(ScrapedImage, image_data)
                    for image_data in result["scrapeSingleImage"]
                ]
            return []
        except Exception as e:
            self.log.error(f"Failed to scrape single image: {e}")
            return []

    async def scrape_url(
        self,
        url: str,
        ty: ScrapeContentType,
    ) -> Any:
        """Scrape content based on a URL.

        Args:
            url: The URL to scrape
            ty: Type of content to scrape (GALLERY, IMAGE, MOVIE, GROUP, PERFORMER, SCENE)

        Returns:
            ScrapedContent union type (could be any scraped type based on ty parameter)

        Note:
            Returns ScrapedStudio, ScrapedTag, ScrapedScene, ScrapedGallery,
            ScrapedImage, ScrapedMovie, ScrapedGroup, or ScrapedPerformer
            depending on the content type.

        Examples:
            Scrape a scene from URL:
            ```python
            from stash_graphql_client.types import ScrapeContentType
            content = await client.scrape_url(
                "https://example.com/scene/123",
                ScrapeContentType.SCENE
            )
            if content:
                print(f"Scraped scene: {content.title}")
            ```

            Scrape a performer from URL:
            ```python
            content = await client.scrape_url(
                "https://example.com/performer/456",
                ScrapeContentType.PERFORMER
            )
            if content:
                print(f"Scraped performer: {content.name}")
            ```
        """
        query = """
            query ScrapeURL($url: String!, $ty: ScrapeContentType!) {
                scrapeURL(url: $url, ty: $ty) {
                    __typename
                    ... on ScrapedStudio {
                        stored_id
                        name
                        urls
                    }
                    ... on ScrapedTag {
                        stored_id
                        name
                    }
                    ... on ScrapedScene {
                        title
                        code
                        details
                        urls
                        date
                    }
                    ... on ScrapedGallery {
                        title
                        code
                        details
                        urls
                        date
                    }
                    ... on ScrapedImage {
                        title
                        code
                        details
                        urls
                        date
                    }
                    ... on ScrapedMovie {
                        stored_id
                        name
                        aliases
                        duration
                        date
                    }
                    ... on ScrapedGroup {
                        stored_id
                        name
                        aliases
                        duration
                        date
                    }
                    ... on ScrapedPerformer {
                        stored_id
                        name
                        gender
                        urls
                    }
                }
            }
        """
        try:
            result = await self.execute(
                query,
                {
                    "url": url,
                    "ty": ty.value if isinstance(ty, ScrapeContentType) else ty,
                },
            )
            if result and result.get("scrapeURL"):
                # Determine the type based on __typename
                data = result["scrapeURL"]
                typename = data.get("__typename", "")

                type_map = {
                    "ScrapedStudio": ScrapedStudio,
                    "ScrapedScene": ScrapedScene,
                    "ScrapedGallery": ScrapedGallery,
                    "ScrapedImage": ScrapedImage,
                    "ScrapedMovie": ScrapedMovie,
                    "ScrapedGroup": ScrapedGroup,
                    "ScrapedPerformer": ScrapedPerformer,
                }

                result_type = type_map.get(typename)
                if result_type:
                    return self._decode_result(result_type, data)

            return None
        except Exception as e:
            self.log.error(f"Failed to scrape URL {url}: {e}")
            return None

    async def scrape_performer_url(
        self,
        url: str,
    ) -> ScrapedPerformer | None:
        """Scrape a complete performer record based on a URL.

        Args:
            url: The URL to scrape performer from

        Returns:
            ScrapedPerformer object if successful, None otherwise

        Examples:
            Scrape performer from URL:
            ```python
            performer = await client.scrape_performer_url("https://example.com/performer/123")
            if performer:
                print(f"Name: {performer.name}")
                print(f"Birthdate: {performer.birthdate}")
                print(f"Gender: {performer.gender}")
            ```
        """
        query = """
            query ScrapePerformerURL($url: String!) {
                scrapePerformerURL(url: $url) {
                    stored_id
                    name
                    disambiguation
                    gender
                    urls
                    birthdate
                    ethnicity
                    country
                    eye_color
                    height
                    measurements
                    fake_tits
                    penis_length
                    circumcised
                    career_length
                    tattoos
                    piercings
                    aliases
                    tags {
                        stored_id
                        name
                    }
                    images
                    details
                    death_date
                    hair_color
                    weight
                    remote_site_id
                }
            }
        """
        try:
            result = await self.execute(query, {"url": url})
            if result and result.get("scrapePerformerURL"):
                return self._decode_result(
                    ScrapedPerformer, result["scrapePerformerURL"]
                )
            return None
        except Exception as e:
            self.log.error(f"Failed to scrape performer URL {url}: {e}")
            return None

    async def scrape_scene_url(
        self,
        url: str,
    ) -> ScrapedScene | None:
        """Scrape a complete scene record based on a URL.

        Args:
            url: The URL to scrape scene from

        Returns:
            ScrapedScene object if successful, None otherwise

        Examples:
            Scrape scene from URL:
            ```python
            scene = await client.scrape_scene_url("https://example.com/scene/123")
            if scene:
                print(f"Title: {scene.title}")
                print(f"Date: {scene.date}")
                print(f"Studio: {scene.studio.name if scene.studio else 'Unknown'}")
            ```
        """
        query = """
            query ScrapeSceneURL($url: String!) {
                scrapeSceneURL(url: $url) {
                    title
                    code
                    details
                    director
                    urls
                    date
                    image
                    studio {
                        stored_id
                        name
                        urls
                    }
                    tags {
                        stored_id
                        name
                    }
                    performers {
                        stored_id
                        name
                    }
                    groups {
                        stored_id
                        name
                    }
                    remote_site_id
                    duration
                }
            }
        """
        try:
            result = await self.execute(query, {"url": url})
            if result and result.get("scrapeSceneURL"):
                return self._decode_result(ScrapedScene, result["scrapeSceneURL"])
            return None
        except Exception as e:
            self.log.error(f"Failed to scrape scene URL {url}: {e}")
            return None

    async def scrape_gallery_url(
        self,
        url: str,
    ) -> ScrapedGallery | None:
        """Scrape a complete gallery record based on a URL.

        Args:
            url: The URL to scrape gallery from

        Returns:
            ScrapedGallery object if successful, None otherwise

        Examples:
            Scrape gallery from URL:
            ```python
            gallery = await client.scrape_gallery_url("https://example.com/gallery/123")
            if gallery:
                print(f"Title: {gallery.title}")
                print(f"Date: {gallery.date}")
                print(f"Performers: {len(gallery.performers or [])}")
            ```
        """
        query = """
            query ScrapeGalleryURL($url: String!) {
                scrapeGalleryURL(url: $url) {
                    title
                    code
                    details
                    photographer
                    urls
                    date
                    studio {
                        stored_id
                        name
                    }
                    tags {
                        stored_id
                        name
                    }
                    performers {
                        stored_id
                        name
                    }
                }
            }
        """
        try:
            result = await self.execute(query, {"url": url})
            if result and result.get("scrapeGalleryURL"):
                return self._decode_result(ScrapedGallery, result["scrapeGalleryURL"])
            return None
        except Exception as e:
            self.log.error(f"Failed to scrape gallery URL {url}: {e}")
            return None

    async def scrape_image_url(
        self,
        url: str,
    ) -> ScrapedImage | None:
        """Scrape a complete image record based on a URL.

        Args:
            url: The URL to scrape image from

        Returns:
            ScrapedImage object if successful, None otherwise

        Examples:
            Scrape image from URL:
            ```python
            image = await client.scrape_image_url("https://example.com/image/123")
            if image:
                print(f"Title: {image.title}")
                print(f"Date: {image.date}")
                print(f"Tags: {len(image.tags or [])}")
            ```
        """
        query = """
            query ScrapeImageURL($url: String!) {
                scrapeImageURL(url: $url) {
                    title
                    code
                    details
                    photographer
                    urls
                    date
                    studio {
                        stored_id
                        name
                    }
                    tags {
                        stored_id
                        name
                    }
                    performers {
                        stored_id
                        name
                    }
                }
            }
        """
        try:
            result = await self.execute(query, {"url": url})
            if result and result.get("scrapeImageURL"):
                return self._decode_result(ScrapedImage, result["scrapeImageURL"])
            return None
        except Exception as e:
            self.log.error(f"Failed to scrape image URL {url}: {e}")
            return None

    async def scrape_movie_url(
        self,
        url: str,
    ) -> ScrapedMovie | None:
        """Scrape a complete movie record based on a URL.

        .. deprecated::
            Use :meth:`scrape_group_url` instead.

        Args:
            url: The URL to scrape movie from

        Returns:
            ScrapedMovie object if successful, None otherwise

        Examples:
            Scrape movie from URL:
            ```python
            movie = await client.scrape_movie_url("https://example.com/movie/123")
            if movie:
                print(f"Name: {movie.name}")
                print(f"Date: {movie.date}")
                print(f"Duration: {movie.duration}")
            ```
        """
        query = """
            query ScrapeMovieURL($url: String!) {
                scrapeMovieURL(url: $url) {
                    stored_id
                    name
                    aliases
                    duration
                    date
                    rating
                    director
                    urls
                    synopsis
                    studio {
                        stored_id
                        name
                    }
                    tags {
                        stored_id
                        name
                    }
                    front_image
                    back_image
                }
            }
        """
        try:
            result = await self.execute(query, {"url": url})
            if result and result.get("scrapeMovieURL"):
                return self._decode_result(ScrapedMovie, result["scrapeMovieURL"])
            return None
        except Exception as e:
            self.log.error(f"Failed to scrape movie URL {url}: {e}")
            return None

    async def scrape_group_url(
        self,
        url: str,
    ) -> ScrapedGroup | None:
        """Scrape a complete group record based on a URL.

        Args:
            url: The URL to scrape group from

        Returns:
            ScrapedGroup object if successful, None otherwise

        Examples:
            Scrape group from URL:
            ```python
            group = await client.scrape_group_url("https://example.com/group/123")
            if group:
                print(f"Name: {group.name}")
                print(f"Date: {group.date}")
                print(f"Synopsis: {group.synopsis}")
            ```
        """
        query = """
            query ScrapeGroupURL($url: String!) {
                scrapeGroupURL(url: $url) {
                    stored_id
                    name
                    aliases
                    duration
                    date
                    rating
                    director
                    urls
                    synopsis
                    studio {
                        stored_id
                        name
                    }
                    tags {
                        stored_id
                        name
                    }
                    front_image
                    back_image
                }
            }
        """
        try:
            result = await self.execute(query, {"url": url})
            if result and result.get("scrapeGroupURL"):
                return self._decode_result(ScrapedGroup, result["scrapeGroupURL"])
            return None
        except Exception as e:
            self.log.error(f"Failed to scrape group URL {url}: {e}")
            return None

    async def reload_scrapers(self) -> bool:
        """Reload all scrapers from configuration.

        Returns:
            True if successful, False otherwise

        Examples:
            Reload scrapers after configuration change:
            ```python
            success = await client.reload_scrapers()
            if success:
                print("Scrapers reloaded successfully")
                # List scrapers to verify
                scrapers = await client.list_scrapers([ScrapeContentType.SCENE])
                print(f"Found {len(scrapers)} scene scrapers")
            ```
        """
        query = """
            mutation ReloadScrapers {
                reloadScrapers
            }
        """
        try:
            result = await self.execute(query, {})
            return result.get("reloadScrapers", False) if result else False
        except Exception as e:
            self.log.error(f"Failed to reload scrapers: {e}")
            return False

    async def submit_stashbox_fingerprints(
        self,
        input_data: StashBoxFingerprintSubmissionInput | dict[str, Any],
    ) -> bool:
        """Submit fingerprints to StashBox.

        Args:
            input_data: StashBoxFingerprintSubmissionInput object or dictionary

        Returns:
            True if successful
        """
        try:
            if isinstance(input_data, StashBoxFingerprintSubmissionInput):
                input_dict = input_data.to_graphql()
            else:
                input_dict = input_data

            result = await self.execute(
                fragments.SUBMIT_STASHBOX_FINGERPRINTS_MUTATION,
                {"input": input_dict},
            )
            return bool(result.get("submitStashBoxFingerprints", False))
        except Exception as e:
            self.log.error(f"Failed to submit StashBox fingerprints: {e}")
            raise

    async def submit_stashbox_scene_draft(
        self,
        input_data: StashBoxDraftSubmissionInput | dict[str, Any],
    ) -> str:
        """Submit scene draft to StashBox.

        Args:
            input_data: StashBoxDraftSubmissionInput object or dictionary

        Returns:
            Draft ID
        """
        try:
            if isinstance(input_data, StashBoxDraftSubmissionInput):
                input_dict = input_data.to_graphql()
            else:
                input_dict = input_data

            result = await self.execute(
                fragments.SUBMIT_STASHBOX_SCENE_DRAFT_MUTATION,
                {"input": input_dict},
            )
            return str(result.get("submitStashBoxSceneDraft", ""))
        except Exception as e:
            self.log.error(f"Failed to submit StashBox scene draft: {e}")
            raise

    async def submit_stashbox_performer_draft(
        self,
        input_data: StashBoxDraftSubmissionInput | dict[str, Any],
    ) -> str:
        """Submit performer draft to StashBox.

        Args:
            input_data: StashBoxDraftSubmissionInput object or dictionary

        Returns:
            Draft ID
        """
        try:
            if isinstance(input_data, StashBoxDraftSubmissionInput):
                input_dict = input_data.to_graphql()
            else:
                input_dict = input_data

            result = await self.execute(
                fragments.SUBMIT_STASHBOX_PERFORMER_DRAFT_MUTATION,
                {"input": input_dict},
            )
            return str(result.get("submitStashBoxPerformerDraft", ""))
        except Exception as e:
            self.log.error(f"Failed to submit StashBox performer draft: {e}")
            raise

    async def stashbox_batch_performer_tag(
        self,
        input_data: dict[str, Any],
    ) -> str:
        """Batch tag performers from StashBox.

        Args:
            input_data: Batch performer tag input dictionary

        Returns:
            Job ID
        """
        try:
            result = await self.execute(
                fragments.STASHBOX_BATCH_PERFORMER_TAG_MUTATION,
                {"input": input_data},
            )
            return str(result.get("stashBoxBatchPerformerTag", ""))
        except Exception as e:
            self.log.error(f"Failed to batch tag performers: {e}")
            raise

    async def stashbox_batch_studio_tag(
        self,
        input_data: dict[str, Any],
    ) -> str:
        """Batch tag studios from StashBox.

        Args:
            input_data: Batch studio tag input dictionary

        Returns:
            Job ID
        """
        try:
            result = await self.execute(
                fragments.STASHBOX_BATCH_STUDIO_TAG_MUTATION,
                {"input": input_data},
            )
            return str(result.get("stashBoxBatchStudioTag", ""))
        except Exception as e:
            self.log.error(f"Failed to batch tag studios: {e}")
            raise
