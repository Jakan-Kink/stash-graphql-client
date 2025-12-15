"""Scraper types from schema/types/scraper.graphql, scraped-performer.graphql, and scraped-group.graphql."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from .base import FromGraphQLMixin, StashInput
from .unset import UNSET, UnsetType


if TYPE_CHECKING:
    from .scene import SceneFileType


class ScrapeType(str, Enum):
    """Type of scraping operation from schema/types/scraper.graphql."""

    NAME = "NAME"  # From text query
    FRAGMENT = "FRAGMENT"  # From existing object
    URL = "URL"  # From URL


class ScrapeContentType(str, Enum):
    """Type of the content a scraper generates from schema/types/scraper.graphql."""

    GALLERY = "GALLERY"
    IMAGE = "IMAGE"
    MOVIE = "MOVIE"
    GROUP = "GROUP"
    PERFORMER = "PERFORMER"
    SCENE = "SCENE"


class ScraperSpec(FromGraphQLMixin, BaseModel):
    """Scraper specification from schema/types/scraper.graphql."""

    urls: list[str] | None | UnsetType = (
        UNSET  # [String!] - URLs matching these can be scraped with
    )
    supported_scrapes: list[ScrapeType] | UnsetType = Field(
        default=UNSET
    )  # [ScrapeType!]!


class Scraper(FromGraphQLMixin, BaseModel):
    """Scraper from schema/types/scraper.graphql."""

    id: str | None | UnsetType = UNSET  # ID!
    name: str | None | UnsetType = UNSET  # String!
    performer: ScraperSpec | None | UnsetType = (
        UNSET  # ScraperSpec - Details for performer scraper
    )
    scene: ScraperSpec | None | UnsetType = (
        UNSET  # ScraperSpec - Details for scene scraper
    )
    gallery: ScraperSpec | None | UnsetType = (
        UNSET  # ScraperSpec - Details for gallery scraper
    )
    image: ScraperSpec | None | UnsetType = (
        UNSET  # ScraperSpec - Details for image scraper
    )
    group: ScraperSpec | None | UnsetType = (
        UNSET  # ScraperSpec - Details for group scraper
    )


class ScrapedTag(FromGraphQLMixin, BaseModel):
    """Tag data from scraper from schema/types/scraper.graphql."""

    stored_id: str | None | UnsetType = Field(
        default=UNSET, alias="storedID"
    )  # ID - Set if tag matched
    name: str | None | UnsetType = UNSET  # String!
    remote_site_id: str | None | UnsetType = Field(
        default=UNSET, alias="remoteSiteID"
    )  # String - Remote site ID, if applicable


class ScrapedStudio(FromGraphQLMixin, BaseModel):
    """Studio data from scraper from schema/types/scraper.graphql."""

    stored_id: str | None | UnsetType = Field(
        default=UNSET, alias="storedID"
    )  # ID - Set if studio matched
    name: str | None | UnsetType = UNSET  # String!
    urls: list[str] | None | UnsetType = UNSET  # [String!]
    parent: ScrapedStudio | None | UnsetType = UNSET  # ScrapedStudio
    image: str | None | UnsetType = UNSET  # String
    details: str | None | UnsetType = UNSET  # String
    aliases: str | None | UnsetType = (
        UNSET  # String - Aliases must be comma-delimited to be parsed correctly
    )
    tags: list[ScrapedTag] | None | UnsetType = UNSET  # [ScrapedTag!]
    remote_site_id: str | None | UnsetType = Field(
        default=UNSET, alias="remoteSiteID"
    )  # String - Remote site ID


class ScrapedPerformer(FromGraphQLMixin, BaseModel):
    """A performer from a scraping operation from schema/types/scraped-performer.graphql."""

    stored_id: str | None | UnsetType = Field(
        default=UNSET, alias="storedID"
    )  # ID - Set if performer matched
    name: str | None | UnsetType = UNSET  # String
    disambiguation: str | None | UnsetType = UNSET  # String
    gender: str | None | UnsetType = UNSET  # String
    urls: list[str] | None | UnsetType = UNSET  # [String!]
    birthdate: str | None | UnsetType = UNSET  # String
    ethnicity: str | None | UnsetType = UNSET  # String
    country: str | None | UnsetType = UNSET  # String
    eye_color: str | None | UnsetType = Field(default=UNSET, alias="eyeColor")  # String
    height: str | None | UnsetType = UNSET  # String
    measurements: str | None | UnsetType = UNSET  # String
    fake_tits: str | None | UnsetType = Field(default=UNSET, alias="fakeTits")  # String
    penis_length: str | None | UnsetType = Field(
        default=UNSET, alias="penisLength"
    )  # String
    circumcised: str | None | UnsetType = UNSET  # String
    career_length: str | None | UnsetType = Field(
        default=UNSET, alias="careerLength"
    )  # String
    tattoos: str | None | UnsetType = UNSET  # String
    piercings: str | None | UnsetType = UNSET  # String
    aliases: str | None | UnsetType = (
        UNSET  # String - aliases must be comma-delimited to be parsed correctly
    )
    tags: list[ScrapedTag] | None | UnsetType = UNSET  # [ScrapedTag!]
    images: list[str] | None | UnsetType = UNSET  # [String!]
    details: str | None | UnsetType = UNSET  # String
    death_date: str | None | UnsetType = Field(
        default=UNSET, alias="deathDate"
    )  # String
    hair_color: str | None | UnsetType = Field(
        default=UNSET, alias="hairColor"
    )  # String
    weight: str | None | UnsetType = UNSET  # String
    remote_site_id: str | None | UnsetType = Field(
        default=UNSET, alias="remoteSiteID"
    )  # String


class ScrapedPerformerInput(StashInput):
    """Input for scraped performer from schema/types/scraped-performer.graphql."""

    stored_id: str | None | UnsetType = Field(
        default=UNSET, alias="storedID"
    )  # ID - Set if performer matched
    name: str | None | UnsetType = UNSET  # String
    disambiguation: str | None | UnsetType = UNSET  # String
    gender: str | None | UnsetType = UNSET  # String
    urls: list[str] | None | UnsetType = UNSET  # [String!]
    birthdate: str | None | UnsetType = UNSET  # String
    ethnicity: str | None | UnsetType = UNSET  # String
    country: str | None | UnsetType = UNSET  # String
    eye_color: str | None | UnsetType = Field(default=UNSET, alias="eyeColor")  # String
    height: str | None | UnsetType = UNSET  # String
    measurements: str | None | UnsetType = UNSET  # String
    fake_tits: str | None | UnsetType = Field(default=UNSET, alias="fakeTits")  # String
    penis_length: str | None | UnsetType = Field(
        default=UNSET, alias="penisLength"
    )  # String
    circumcised: str | None | UnsetType = UNSET  # String
    career_length: str | None | UnsetType = Field(
        default=UNSET, alias="careerLength"
    )  # String
    tattoos: str | None | UnsetType = UNSET  # String
    piercings: str | None | UnsetType = UNSET  # String
    aliases: str | None | UnsetType = UNSET  # String
    details: str | None | UnsetType = UNSET  # String
    death_date: str | None | UnsetType = Field(
        default=UNSET, alias="deathDate"
    )  # String
    hair_color: str | None | UnsetType = Field(
        default=UNSET, alias="hairColor"
    )  # String
    weight: str | None | UnsetType = UNSET  # String
    remote_site_id: str | None | UnsetType = Field(
        default=UNSET, alias="remoteSiteID"
    )  # String


class ScrapedScene(FromGraphQLMixin, BaseModel):
    """Scene data from scraper from schema/types/scraper.graphql."""

    title: str | None | UnsetType = UNSET  # String
    code: str | None | UnsetType = UNSET  # String
    details: str | None | UnsetType = UNSET  # String
    director: str | None | UnsetType = UNSET  # String
    urls: list[str] | None | UnsetType = UNSET  # [String!]
    date: str | None | UnsetType = UNSET  # String
    image: str | None | UnsetType = (
        UNSET  # String - This should be a base64 encoded data URL
    )
    file: SceneFileType | None | UnsetType = UNSET  # SceneFileType (Resolver)
    studio: ScrapedStudio | None | UnsetType = UNSET  # ScrapedStudio
    tags: list[ScrapedTag] | None | UnsetType = UNSET  # [ScrapedTag!]
    performers: list[ScrapedPerformer] | None | UnsetType = UNSET  # [ScrapedPerformer!]
    groups: list[ScrapedGroup] | None | UnsetType = UNSET  # [ScrapedGroup!]
    remote_site_id: str | None | UnsetType = Field(
        default=UNSET, alias="remoteSiteID"
    )  # String
    duration: int | None | UnsetType = UNSET  # Int
    fingerprints: list[StashBoxFingerprint] | None | UnsetType = (
        UNSET  # [StashBoxFingerprint!]
    )


class ScrapedSceneInput(StashInput):
    """Input for scraped scene from schema/types/scraper.graphql."""

    title: str | None | UnsetType = UNSET  # String
    code: str | None | UnsetType = UNSET  # String
    details: str | None | UnsetType = UNSET  # String
    director: str | None | UnsetType = UNSET  # String
    urls: list[str] | None | UnsetType = UNSET  # [String!]
    date: str | None | UnsetType = UNSET  # String
    remote_site_id: str | None | UnsetType = Field(
        default=UNSET, alias="remoteSiteID"
    )  # String


class ScrapedGallery(FromGraphQLMixin, BaseModel):
    """Gallery data from scraper from schema/types/scraper.graphql."""

    title: str | None | UnsetType = UNSET  # String
    code: str | None | UnsetType = UNSET  # String
    details: str | None | UnsetType = UNSET  # String
    photographer: str | None | UnsetType = UNSET  # String
    urls: list[str] | None | UnsetType = UNSET  # [String!]
    date: str | None | UnsetType = UNSET  # String
    studio: ScrapedStudio | None | UnsetType = UNSET  # ScrapedStudio
    tags: list[ScrapedTag] | None | UnsetType = UNSET  # [ScrapedTag!]
    performers: list[ScrapedPerformer] | None | UnsetType = UNSET  # [ScrapedPerformer!]


class ScrapedGalleryInput(StashInput):
    """Input for scraped gallery from schema/types/scraper.graphql."""

    title: str | None | UnsetType = UNSET  # String
    code: str | None | UnsetType = UNSET  # String
    details: str | None | UnsetType = UNSET  # String
    photographer: str | None | UnsetType = UNSET  # String
    urls: list[str] | None | UnsetType = UNSET  # [String!]
    date: str | None | UnsetType = UNSET  # String


class ScrapedImage(FromGraphQLMixin, BaseModel):
    """Image data from scraper from schema/types/scraper.graphql."""

    title: str | None | UnsetType = UNSET  # String
    code: str | None | UnsetType = UNSET  # String
    details: str | None | UnsetType = UNSET  # String
    photographer: str | None | UnsetType = UNSET  # String
    urls: list[str] | None | UnsetType = UNSET  # [String!]
    date: str | None | UnsetType = UNSET  # String
    studio: ScrapedStudio | None | UnsetType = UNSET  # ScrapedStudio
    tags: list[ScrapedTag] | None | UnsetType = UNSET  # [ScrapedTag!]
    performers: list[ScrapedPerformer] | None | UnsetType = UNSET  # [ScrapedPerformer!]


class ScrapedImageInput(StashInput):
    """Input for scraped image from schema/types/scraper.graphql."""

    title: str | None | UnsetType = UNSET  # String
    code: str | None | UnsetType = UNSET  # String
    details: str | None | UnsetType = UNSET  # String
    urls: list[str] | None | UnsetType = UNSET  # [String!]
    date: str | None | UnsetType = UNSET  # String


class ScrapedMovie(FromGraphQLMixin, BaseModel):
    """A movie from a scraping operation from schema/types/scraped-group.graphql."""

    stored_id: str | None | UnsetType = Field(default=UNSET, alias="storedID")  # ID
    name: str | None | UnsetType = UNSET  # String
    aliases: str | None | UnsetType = UNSET  # String
    duration: str | None | UnsetType = UNSET  # String
    date: str | None | UnsetType = UNSET  # String
    rating: str | None | UnsetType = UNSET  # String
    director: str | None | UnsetType = UNSET  # String
    urls: list[str] | None | UnsetType = UNSET  # [String!]
    synopsis: str | None | UnsetType = UNSET  # String
    studio: ScrapedStudio | None | UnsetType = UNSET  # ScrapedStudio
    tags: list[ScrapedTag] | None | UnsetType = UNSET  # [ScrapedTag!]
    front_image: str | None | UnsetType = Field(
        default=UNSET, alias="frontImage"
    )  # String - This should be a base64 encoded data URL
    back_image: str | None | UnsetType = Field(
        default=UNSET, alias="backImage"
    )  # String - This should be a base64 encoded data URL


class ScrapedMovieInput(StashInput):
    """Input for scraped movie from schema/types/scraped-group.graphql."""

    name: str | None | UnsetType = UNSET  # String
    aliases: str | None | UnsetType = UNSET  # String
    duration: str | None | UnsetType = UNSET  # String
    date: str | None | UnsetType = UNSET  # String
    rating: str | None | UnsetType = UNSET  # String
    director: str | None | UnsetType = UNSET  # String
    urls: list[str] | None | UnsetType = UNSET  # [String!]
    synopsis: str | None | UnsetType = UNSET  # String


class ScrapedGroup(FromGraphQLMixin, BaseModel):
    """A group from a scraping operation from schema/types/scraped-group.graphql."""

    stored_id: str | None | UnsetType = Field(default=UNSET, alias="storedID")  # ID
    name: str | None | UnsetType = UNSET  # String
    aliases: str | None | UnsetType = UNSET  # String
    duration: str | None | UnsetType = UNSET  # String
    date: str | None | UnsetType = UNSET  # String
    rating: str | None | UnsetType = UNSET  # String
    director: str | None | UnsetType = UNSET  # String
    urls: list[str] | None | UnsetType = UNSET  # [String!]
    synopsis: str | None | UnsetType = UNSET  # String
    studio: ScrapedStudio | None | UnsetType = UNSET  # ScrapedStudio
    tags: list[ScrapedTag] | None | UnsetType = UNSET  # [ScrapedTag!]
    front_image: str | None | UnsetType = Field(
        default=UNSET, alias="frontImage"
    )  # String - This should be a base64 encoded data URL
    back_image: str | None | UnsetType = Field(
        default=UNSET, alias="backImage"
    )  # String - This should be a base64 encoded data URL


class ScrapedGroupInput(StashInput):
    """Input for scraped group from schema/types/scraped-group.graphql."""

    name: str | None | UnsetType = UNSET  # String
    aliases: str | None | UnsetType = UNSET  # String
    duration: str | None | UnsetType = UNSET  # String
    date: str | None | UnsetType = UNSET  # String
    rating: str | None | UnsetType = UNSET  # String
    director: str | None | UnsetType = UNSET  # String
    urls: list[str] | None | UnsetType = UNSET  # [String!]
    synopsis: str | None | UnsetType = UNSET  # String


class ScraperSource(FromGraphQLMixin, BaseModel):
    """Scraper source from schema/types/scraper.graphql."""

    stash_box_endpoint: str | None | UnsetType = Field(
        default=UNSET, alias="stashBoxEndpoint"
    )  # String - Stash-box endpoint
    scraper_id: str | None | UnsetType = Field(
        default=UNSET, alias="scraperID"
    )  # ID - Scraper ID to scrape with


class ScraperSourceInput(StashInput):
    """Input for scraper source from schema/types/scraper.graphql."""

    stash_box_endpoint: str | None | UnsetType = UNSET  # String - Stash-box endpoint
    scraper_id: str | None | UnsetType = UNSET  # ID - Scraper ID to scrape with


class ScrapeSingleSceneInput(StashInput):
    """Input for scraping a single scene from schema/types/scraper.graphql."""

    query: str | None | UnsetType = UNSET  # String - Instructs to query by string
    scene_id: str | None | UnsetType = (
        UNSET  # ID - Instructs to query by scene fingerprints
    )
    scene_input: ScrapedSceneInput | None | UnsetType = (
        UNSET  # ScrapedSceneInput - Instructs to query by scene fragment
    )


class ScrapeMultiScenesInput(StashInput):
    """Input for scraping multiple scenes from schema/types/scraper.graphql."""

    scene_ids: list[str] | None | UnsetType = (
        UNSET  # [ID!] - Instructs to query by scene fingerprints
    )


class ScrapeSingleStudioInput(StashInput):
    """Input for scraping a single studio from schema/types/scraper.graphql."""

    query: str | None | UnsetType = (
        UNSET  # String - Query can be either a name or a Stash ID
    )


class ScrapeSinglePerformerInput(StashInput):
    """Input for scraping a single performer from schema/types/scraper.graphql."""

    query: str | None | UnsetType = UNSET  # String - Instructs to query by string
    performer_id: str | None | UnsetType = (
        UNSET  # ID - Instructs to query by performer id
    )
    performer_input: ScrapedPerformerInput | None | UnsetType = (
        UNSET  # ScrapedPerformerInput - Instructs to query by performer fragment
    )


class ScrapeMultiPerformersInput(StashInput):
    """Input for scraping multiple performers from schema/types/scraper.graphql."""

    performer_ids: list[str] | None | UnsetType = (
        UNSET  # [ID!] - Instructs to query by scene fingerprints
    )


class ScrapeSingleGalleryInput(StashInput):
    """Input for scraping a single gallery from schema/types/scraper.graphql."""

    query: str | None | UnsetType = UNSET  # String - Instructs to query by string
    gallery_id: str | None | UnsetType = UNSET  # ID - Instructs to query by gallery id
    gallery_input: ScrapedGalleryInput | None | UnsetType = (
        UNSET  # ScrapedGalleryInput - Instructs to query by gallery fragment
    )


class ScrapeSingleImageInput(StashInput):
    """Input for scraping a single image from schema/types/scraper.graphql."""

    query: str | None | UnsetType = UNSET  # String - Instructs to query by string
    image_id: str | None | UnsetType = UNSET  # ID - Instructs to query by image id
    image_input: ScrapedImageInput | None | UnsetType = (
        UNSET  # ScrapedImageInput - Instructs to query by image fragment
    )


class ScrapeSingleMovieInput(StashInput):
    """Input for scraping a single movie from schema/types/scraper.graphql."""

    query: str | None | UnsetType = UNSET  # String - Instructs to query by string
    movie_id: str | None | UnsetType = UNSET  # ID - Instructs to query by movie id
    movie_input: ScrapedMovieInput | None | UnsetType = (
        UNSET  # ScrapedMovieInput - Instructs to query by movie fragment
    )


class ScrapeSingleGroupInput(StashInput):
    """Input for scraping a single group from schema/types/scraper.graphql."""

    query: str | None | UnsetType = UNSET  # String - Instructs to query by string
    group_id: str | None | UnsetType = UNSET  # ID - Instructs to query by group id
    group_input: ScrapedGroupInput | None | UnsetType = (
        UNSET  # ScrapedGroupInput - Instructs to query by group fragment
    )


class StashBoxSceneQueryInput(StashInput):
    """Input for StashBox scene query from schema/types/scraper.graphql."""

    stash_box_endpoint: str | None | UnsetType = (
        UNSET  # String - Endpoint of the stash-box instance to use
    )
    scene_ids: list[str] | None | UnsetType = (
        UNSET  # [ID!] - Instructs query by scene fingerprints
    )
    q: str | None | UnsetType = UNSET  # String - Query by query string


class StashBoxPerformerQueryInput(StashInput):
    """Input for StashBox performer query from schema/types/scraper.graphql."""

    stash_box_endpoint: str | None | UnsetType = (
        UNSET  # String - Endpoint of the stash-box instance to use
    )
    performer_ids: list[str] | None | UnsetType = (
        UNSET  # [ID!] - Instructs query by scene fingerprints
    )
    q: str | None | UnsetType = UNSET  # String - Query by query string


class StashBoxPerformerQueryResult(FromGraphQLMixin, BaseModel):
    """Result for StashBox performer query from schema/types/scraper.graphql."""

    query: str | UnsetType = UNSET  # String!
    results: list[ScrapedPerformer] | UnsetType = Field(
        default=UNSET
    )  # [ScrapedPerformer!]!


class StashBoxFingerprint(FromGraphQLMixin, BaseModel):
    """StashBox fingerprint from schema/types/scraper.graphql."""

    algorithm: str | UnsetType = UNSET  # String!
    hash: str | UnsetType = UNSET  # String!
    duration: int | UnsetType = UNSET  # Int!


class StashBoxBatchTagInput(StashInput):
    """Input for StashBox batch tagging from schema/types/scraper.graphql.

    Accepts either ids, or a combination of names and stash_ids.
    If none are set, then all existing items will be tagged.
    """

    stash_box_endpoint: str | None | UnsetType = (
        UNSET  # String - Endpoint of the stash-box instance to use
    )
    exclude_fields: list[str] | None | UnsetType = (
        UNSET  # [String!] - Fields to exclude when executing the tagging
    )
    refresh: bool | UnsetType = (
        UNSET  # Boolean! - Refresh items already tagged by StashBox if true
    )
    create_parent: bool | UnsetType = Field(
        default=UNSET, alias="createParent"
    )  # Boolean! - If batch adding studios, should their parent studios also be created?
    ids: list[str] | None | UnsetType = (
        UNSET  # [ID!] - IDs in stash of the items to update
    )
    names: list[str] | None | UnsetType = (
        UNSET  # [String!] - Names of the items in the stash-box instance to search for and create
    )
    stash_ids: list[str] | None | UnsetType = (
        UNSET  # [String!] - Stash IDs of the items in the stash-box instance to search for and create
    )


# ScrapedContent union would need special handling in Python
# For now, we can represent it as a type alias or handle it at runtime
# ScrapedContent = Union[ScrapedStudio, ScrapedTag, ScrapedScene, ScrapedGallery,
#                        ScrapedImage, ScrapedMovie, ScrapedGroup, ScrapedPerformer]
