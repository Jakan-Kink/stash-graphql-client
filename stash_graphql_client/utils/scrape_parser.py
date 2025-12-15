"""Utilities for parsing and transforming scraped data into Stash input types.

This module provides utilities inspired by stashapi's scrape parsing functionality,
helping transform scraped data from various sources into properly formatted
create/update input types for the Stash GraphQL API.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from stash_graphql_client.types import (
    UNSET,
    PerformerCreateInput,
    SceneCreateInput,
    ScrapedPerformer,
    ScrapedScene,
    UnsetType,
)


if TYPE_CHECKING:
    from stash_graphql_client.client import StashClient


class ScrapeParser:
    """Utility class for transforming scraped data into Stash input types.

    This class provides methods to convert scraped data from various sources
    (scrapers, APIs, etc.) into properly formatted input objects for creating
    or updating Stash entities.

    Examples:
        Parse scraped scene data:
        ```python
        from stash_graphql_client.utils import ScrapeParser

        parser = ScrapeParser()
        scraped_scene = ScrapedScene(
            title="Example Scene",
            duration=1800,  # 30 minutes in seconds
            studio=ScrapedStudio(name="Studio Name"),
            performers=[ScrapedPerformer(name="Performer 1")]
        )

        scene_input = parser.scene_from_scrape(scraped_scene)
        # scene_input is now a SceneCreateInput ready to use
        ```

        Parse duration strings:
        ```python
        parser = ScrapeParser()
        seconds = parser.parse_duration("01:30:45")  # Returns 5445
        seconds = parser.parse_duration("30:00")     # Returns 1800
        seconds = parser.parse_duration("45")        # Returns 45
        ```

        Resolve entities with client integration:
        ```python
        parser = ScrapeParser(client=stash_client)

        # Resolve studio by name
        studio_id = await parser.resolve_studio("Studio Name")

        # Resolve performer by name
        performer_id = await parser.resolve_performer("Performer Name")

        # Resolve multiple tags
        tag_ids = await parser.resolve_tags(["Tag1", "Tag2", "Tag3"])
        ```
    """

    def __init__(self, client: StashClient | None = None):
        """Initialize the ScrapeParser.

        Args:
            client: Optional StashClient for resolving existing entities by name.
                   If provided, enables entity resolution methods.
        """
        self.client = client

    @staticmethod
    def parse_duration(duration: str | int | None) -> int | None:
        """Parse duration string into seconds.

        Supports various duration formats:
        - HH:MM:SS (e.g., "01:30:45" -> 5445 seconds)
        - MM:SS (e.g., "30:00" -> 1800 seconds)
        - SS (e.g., "45" -> 45 seconds)
        - Integer (already in seconds)
        - None (returns None)

        Args:
            duration: Duration as string (HH:MM:SS, MM:SS, or SS) or integer (seconds)

        Returns:
            Duration in seconds, or None if input is None or invalid

        Examples:
            >>> ScrapeParser.parse_duration("01:30:45")
            5445
            >>> ScrapeParser.parse_duration("30:00")
            1800
            >>> ScrapeParser.parse_duration("45")
            45
            >>> ScrapeParser.parse_duration(1800)
            1800
            >>> ScrapeParser.parse_duration(None)
            None
        """
        if duration is None:
            return None

        # If already an integer, return it
        if isinstance(duration, int):
            return duration

        # Remove whitespace
        duration = duration.strip()

        # Try parsing as HH:MM:SS or MM:SS or SS
        time_pattern = r"^(?:(\d+):)?(\d+):(\d+)$"
        match = re.match(time_pattern, duration)

        if match:
            hours_str, minutes_str, seconds_str = match.groups()
            hours = int(hours_str) if hours_str else 0
            minutes = int(minutes_str)
            seconds = int(seconds_str)

            # Validate time values
            if minutes >= 60 or seconds >= 60:
                return None

            return hours * 3600 + minutes * 60 + seconds

        # Try parsing as plain seconds
        try:
            return int(duration)
        except ValueError:
            return None

    def scene_from_scrape(
        self,
        scraped: ScrapedScene,
        studio_id: str | None | UnsetType = UNSET,
        performer_ids: list[str] | None | UnsetType = UNSET,
        tag_ids: list[str] | None | UnsetType = UNSET,
    ) -> SceneCreateInput:
        """Convert ScrapedScene to SceneCreateInput.

        This method transforms a ScrapedScene object (from a scraper) into a
        SceneCreateInput object suitable for creating a new scene via the API.

        Args:
            scraped: The ScrapedScene object from a scraper
            studio_id: Optional studio ID to use instead of resolving from scraped.studio
            performer_ids: Optional performer IDs to use instead of resolving from scraped.performers
            tag_ids: Optional tag IDs to use instead of resolving from scraped.tags

        Returns:
            SceneCreateInput object ready to use with sceneCreate mutation

        Examples:
            Basic conversion:
            ```python
            parser = ScrapeParser()
            scraped = ScrapedScene(
                title="Example Scene",
                details="Scene description",
                date="2024-01-15",
                duration=1800
            )
            scene_input = parser.scene_from_scrape(scraped)
            ```

            With explicit IDs:
            ```python
            scene_input = parser.scene_from_scrape(
                scraped,
                studio_id="studio-123",
                performer_ids=["perf-1", "perf-2"],
                tag_ids=["tag-1", "tag-2"]
            )
            ```
        """
        # Note: duration is not included in SceneCreateInput as it's derived from file metadata
        # Parse duration method exists for other use cases but is not used here

        # Extract studio ID if provided in scraped data
        extracted_studio_id = UNSET
        if (
            studio_id is UNSET
            and scraped.studio is not None
            and scraped.studio is not UNSET
            and hasattr(scraped.studio, "stored_id")
            and scraped.studio.stored_id is not UNSET
            and scraped.studio.stored_id is not None
        ):
            extracted_studio_id = scraped.studio.stored_id

        # Extract performer IDs if provided in scraped data
        extracted_performer_ids = UNSET
        if (
            performer_ids is UNSET
            and scraped.performers is not None
            and scraped.performers is not UNSET
        ):
            perf_ids = [
                perf.stored_id
                for perf in scraped.performers
                if hasattr(perf, "stored_id")
                and perf.stored_id is not UNSET
                and perf.stored_id is not None
            ]
            if perf_ids:
                extracted_performer_ids = perf_ids

        # Extract tag IDs if provided in scraped data
        extracted_tag_ids = UNSET
        if tag_ids is UNSET and scraped.tags is not None and scraped.tags is not UNSET:
            tag_id_list = [
                tag.stored_id
                for tag in scraped.tags
                if hasattr(tag, "stored_id")
                and tag.stored_id is not UNSET
                and tag.stored_id is not None
            ]
            if tag_id_list:
                extracted_tag_ids = tag_id_list

        return SceneCreateInput(
            title=scraped.title if scraped.title is not UNSET else UNSET,
            code=scraped.code if scraped.code is not UNSET else UNSET,
            details=scraped.details if scraped.details is not UNSET else UNSET,
            director=scraped.director if scraped.director is not UNSET else UNSET,
            urls=scraped.urls if scraped.urls is not UNSET else UNSET,
            date=scraped.date if scraped.date is not UNSET else UNSET,
            studio_id=studio_id if studio_id is not UNSET else extracted_studio_id,
            performer_ids=performer_ids
            if performer_ids is not UNSET
            else extracted_performer_ids,
            tag_ids=tag_ids if tag_ids is not UNSET else extracted_tag_ids,
            cover_image=scraped.image if scraped.image is not UNSET else UNSET,
        )

    def performer_from_scrape(
        self,
        scraped: ScrapedPerformer,
        tag_ids: list[str] | None | UnsetType = UNSET,
    ) -> PerformerCreateInput:
        """Convert ScrapedPerformer to PerformerCreateInput.

        This method transforms a ScrapedPerformer object (from a scraper) into a
        PerformerCreateInput object suitable for creating a new performer via the API.

        Note:
            String fields like height, weight, measurements are converted to their
            proper numeric/formatted types where possible. Height strings are parsed
            to centimeters, weight to kg, etc.

        Args:
            scraped: The ScrapedPerformer object from a scraper
            tag_ids: Optional tag IDs to use instead of resolving from scraped.tags

        Returns:
            PerformerCreateInput object ready to use with performerCreate mutation

        Examples:
            Basic conversion:
            ```python
            parser = ScrapeParser()
            scraped = ScrapedPerformer(
                name="Performer Name",
                gender="FEMALE",
                birthdate="1990-01-15",
                ethnicity="Caucasian"
            )
            performer_input = parser.performer_from_scrape(scraped)
            ```

            With explicit tag IDs:
            ```python
            performer_input = parser.performer_from_scrape(
                scraped,
                tag_ids=["tag-1", "tag-2"]
            )
            ```
        """
        # Extract tag IDs if provided in scraped data
        extracted_tag_ids = UNSET
        if tag_ids is UNSET and scraped.tags is not None and scraped.tags is not UNSET:
            tag_id_list = [
                tag.stored_id
                for tag in scraped.tags
                if hasattr(tag, "stored_id")
                and tag.stored_id is not UNSET
                and tag.stored_id is not None
            ]
            if tag_id_list:
                extracted_tag_ids = tag_id_list

        # Parse height from string to cm
        height_cm = UNSET
        if scraped.height is not None and scraped.height is not UNSET:
            height_cm = self._parse_height(scraped.height)

        # Parse weight from string to kg
        weight = UNSET
        if scraped.weight is not None and scraped.weight is not UNSET:
            weight = self._parse_weight(scraped.weight)

        # Convert aliases from comma-delimited string to list
        alias_list = UNSET
        if scraped.aliases is not None and scraped.aliases is not UNSET:
            alias_list = [a.strip() for a in scraped.aliases.split(",") if a.strip()]

        # Use first image if available
        image = UNSET
        if (
            scraped.images is not None
            and scraped.images is not UNSET
            and scraped.images
        ):
            image = scraped.images[0]

        return PerformerCreateInput(
            name=scraped.name
            if scraped.name is not UNSET and scraped.name is not None
            else "Unknown",
            disambiguation=scraped.disambiguation
            if scraped.disambiguation is not UNSET
            else UNSET,
            gender=scraped.gender if scraped.gender is not UNSET else UNSET,  # type: ignore
            birthdate=scraped.birthdate if scraped.birthdate is not UNSET else UNSET,
            ethnicity=scraped.ethnicity if scraped.ethnicity is not UNSET else UNSET,
            country=scraped.country if scraped.country is not UNSET else UNSET,
            eye_color=scraped.eye_color if scraped.eye_color is not UNSET else UNSET,
            height_cm=height_cm,
            measurements=scraped.measurements
            if scraped.measurements is not UNSET
            else UNSET,
            fake_tits=scraped.fake_tits if scraped.fake_tits is not UNSET else UNSET,
            career_length=scraped.career_length
            if scraped.career_length is not UNSET
            else UNSET,
            tattoos=scraped.tattoos if scraped.tattoos is not UNSET else UNSET,
            piercings=scraped.piercings if scraped.piercings is not UNSET else UNSET,
            alias_list=alias_list,
            tag_ids=tag_ids if tag_ids is not UNSET else extracted_tag_ids,
            image=image,
            details=scraped.details if scraped.details is not UNSET else UNSET,
            death_date=scraped.death_date if scraped.death_date is not UNSET else UNSET,
            hair_color=scraped.hair_color if scraped.hair_color is not UNSET else UNSET,
            weight=weight,
            urls=scraped.urls if scraped.urls is not UNSET else UNSET,
        )

    @staticmethod
    def _parse_height(height: str) -> int | UnsetType:
        """Parse height string to centimeters.

        Supports formats like:
        - "170cm" or "170" -> 170
        - "5'9\"" or "5'9" -> 175 (feet/inches to cm)
        - "1.70m" or "1.70" -> 170

        Args:
            height: Height as string

        Returns:
            Height in centimeters, or UNSET if parsing fails
        """
        if not height:
            return UNSET

        height = height.strip().lower()

        # Try cm format
        cm_match = re.match(r"(\d+)\s*cm", height)
        if cm_match:
            return int(cm_match.group(1))

        # Try feet/inches format
        feet_match = re.match(r"(\d+)'(\d+)", height)
        if feet_match:
            feet = int(feet_match.group(1))
            inches = int(feet_match.group(2))
            total_inches = feet * 12 + inches
            return int(total_inches * 2.54)  # Convert to cm

        # Try meters format
        meters_match = re.match(r"(\d+\.?\d*)\s*m", height)
        if meters_match:
            meters = float(meters_match.group(1))
            return int(meters * 100)

        # Try plain number (assume cm)
        try:
            return int(height)
        except ValueError:
            return UNSET

    @staticmethod
    def _parse_weight(weight: str) -> int | UnsetType:
        """Parse weight string to kilograms.

        Supports formats like:
        - "70kg" or "70" -> 70
        - "154lbs" or "154 lbs" -> 70 (pounds to kg)

        Args:
            weight: Weight as string

        Returns:
            Weight in kilograms, or UNSET if parsing fails
        """
        if not weight:
            return UNSET

        weight = weight.strip().lower()

        # Try kg format
        kg_match = re.match(r"(\d+)\s*kg", weight)
        if kg_match:
            return int(kg_match.group(1))

        # Try lbs format
        lbs_match = re.match(r"(\d+)\s*lbs?", weight)
        if lbs_match:
            lbs = int(lbs_match.group(1))
            return int(lbs * 0.453592)  # Convert to kg

        # Try plain number (assume kg)
        try:
            return int(weight)
        except ValueError:
            return UNSET

    async def resolve_studio(self, name: str) -> str | None:
        """Look up existing studio by name and return its ID.

        Requires a client to be set during initialization.

        Args:
            name: Studio name to search for

        Returns:
            Studio ID if found, None otherwise

        Raises:
            RuntimeError: If no client was provided during initialization

        Examples:
            ```python
            parser = ScrapeParser(client=stash_client)
            studio_id = await parser.resolve_studio("Studio Name")
            if studio_id:
                print(f"Found studio: {studio_id}")
            ```
        """
        if not self.client:
            raise RuntimeError("Client required for entity resolution")

        result = await self.client.find_studios()
        for studio in result.studios:
            if studio.name == name:
                return studio.id
        return None

    async def resolve_performer(self, name: str) -> str | None:
        """Look up existing performer by name and return their ID.

        Requires a client to be set during initialization.

        Args:
            name: Performer name to search for

        Returns:
            Performer ID if found, None otherwise

        Raises:
            RuntimeError: If no client was provided during initialization

        Examples:
            ```python
            parser = ScrapeParser(client=stash_client)
            performer_id = await parser.resolve_performer("Performer Name")
            if performer_id:
                print(f"Found performer: {performer_id}")
            ```
        """
        if not self.client:
            raise RuntimeError("Client required for entity resolution")

        result = await self.client.find_performers()
        for performer in result.performers:
            if performer.name == name:
                return performer.id
        return None

    async def resolve_tag(self, name: str) -> str | None:
        """Look up existing tag by name and return its ID.

        Requires a client to be set during initialization.

        Args:
            name: Tag name to search for

        Returns:
            Tag ID if found, None otherwise

        Raises:
            RuntimeError: If no client was provided during initialization

        Examples:
            ```python
            parser = ScrapeParser(client=stash_client)
            tag_id = await parser.resolve_tag("Tag Name")
            if tag_id:
                print(f"Found tag: {tag_id}")
            ```
        """
        if not self.client:
            raise RuntimeError("Client required for entity resolution")

        result = await self.client.find_tags()
        for tag in result.tags:
            if tag.name == name:
                return tag.id
        return None

    async def resolve_tags(self, names: list[str]) -> list[str]:
        """Look up multiple existing tags by name and return their IDs.

        Only returns IDs for tags that were found. Missing tags are skipped.

        Requires a client to be set during initialization.

        Args:
            names: List of tag names to search for

        Returns:
            List of tag IDs for tags that were found

        Raises:
            RuntimeError: If no client was provided during initialization

        Examples:
            ```python
            parser = ScrapeParser(client=stash_client)
            tag_ids = await parser.resolve_tags(["Tag1", "Tag2", "Tag3"])
            print(f"Found {len(tag_ids)} tags")
            ```
        """
        if not self.client:
            raise RuntimeError("Client required for entity resolution")

        result = await self.client.find_tags()
        tag_map = {
            tag.name: tag.id
            for tag in result.tags
            if tag.name is not None and tag.name is not UNSET
        }

        found_ids = []
        for name in names:
            if name in tag_map and tag_map[name] is not None:
                tag_id = tag_map[name]
                if tag_id is not UNSET and tag_id is not None:
                    found_ids.append(tag_id)
        return found_ids
