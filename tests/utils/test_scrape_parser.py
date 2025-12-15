"""Tests for ScrapeParser utility."""

import httpx
import pytest
import respx

from stash_graphql_client import StashClient
from stash_graphql_client.types import (
    UNSET,
    ScrapedPerformer,
    ScrapedScene,
    ScrapedStudio,
    ScrapedTag,
)
from stash_graphql_client.utils import ScrapeParser
from tests.fixtures.stash.graphql_responses import create_graphql_response


# =============================================================================
# Duration Parsing Tests
# =============================================================================


@pytest.mark.unit
def test_parse_duration_hh_mm_ss():
    """Test parsing HH:MM:SS format."""
    parser = ScrapeParser()
    assert parser.parse_duration("01:30:45") == 5445  # 1h 30m 45s


@pytest.mark.unit
def test_parse_duration_mm_ss():
    """Test parsing MM:SS format."""
    parser = ScrapeParser()
    assert parser.parse_duration("30:00") == 1800  # 30 minutes


@pytest.mark.unit
def test_parse_duration_ss():
    """Test parsing SS format (seconds only)."""
    parser = ScrapeParser()
    assert parser.parse_duration("45") == 45


@pytest.mark.unit
def test_parse_duration_integer():
    """Test parsing integer (already in seconds)."""
    parser = ScrapeParser()
    assert parser.parse_duration(1800) == 1800


@pytest.mark.unit
def test_parse_duration_none():
    """Test parsing None returns None."""
    parser = ScrapeParser()
    assert parser.parse_duration(None) is None


@pytest.mark.unit
def test_parse_duration_invalid():
    """Test parsing invalid string returns None."""
    parser = ScrapeParser()
    assert parser.parse_duration("invalid") is None
    assert parser.parse_duration("25:75:99") is None


@pytest.mark.unit
def test_parse_duration_with_whitespace():
    """Test parsing duration with whitespace."""
    parser = ScrapeParser()
    assert parser.parse_duration("  01:30:45  ") == 5445


# =============================================================================
# Height Parsing Tests
# =============================================================================


@pytest.mark.unit
def test_parse_height_cm():
    """Test parsing height in cm format."""
    parser = ScrapeParser()
    assert parser._parse_height("170cm") == 170
    assert parser._parse_height("170 cm") == 170


@pytest.mark.unit
def test_parse_height_feet_inches():
    """Test parsing height in feet/inches format."""
    parser = ScrapeParser()
    # 5'9" = 5*12 + 9 = 69 inches * 2.54 = 175.26 cm
    assert parser._parse_height("5'9") == 175
    assert parser._parse_height("6'2") == 187


@pytest.mark.unit
def test_parse_height_meters():
    """Test parsing height in meters format."""
    parser = ScrapeParser()
    assert parser._parse_height("1.70m") == 170
    assert parser._parse_height("1.85 m") == 185


@pytest.mark.unit
def test_parse_height_plain_number():
    """Test parsing height as plain number (assumes cm)."""
    parser = ScrapeParser()
    assert parser._parse_height("170") == 170


@pytest.mark.unit
def test_parse_height_invalid():
    """Test parsing invalid height returns UNSET."""
    parser = ScrapeParser()
    assert parser._parse_height("invalid") is UNSET
    assert parser._parse_height("") is UNSET


# =============================================================================
# Weight Parsing Tests
# =============================================================================


@pytest.mark.unit
def test_parse_weight_kg():
    """Test parsing weight in kg format."""
    parser = ScrapeParser()
    assert parser._parse_weight("70kg") == 70
    assert parser._parse_weight("70 kg") == 70


@pytest.mark.unit
def test_parse_weight_lbs():
    """Test parsing weight in lbs format."""
    parser = ScrapeParser()
    # 154 lbs * 0.453592 = 69.85 kg
    assert parser._parse_weight("154lbs") == 69
    assert parser._parse_weight("154 lb") == 69


@pytest.mark.unit
def test_parse_weight_plain_number():
    """Test parsing weight as plain number (assumes kg)."""
    parser = ScrapeParser()
    assert parser._parse_weight("70") == 70


@pytest.mark.unit
def test_parse_weight_invalid():
    """Test parsing invalid weight returns UNSET."""
    parser = ScrapeParser()
    assert parser._parse_weight("invalid") is UNSET
    assert parser._parse_weight("") is UNSET


# =============================================================================
# Scene Conversion Tests
# =============================================================================


@pytest.mark.unit
def test_scene_from_scrape_basic():
    """Test basic scene conversion from scraped data."""
    parser = ScrapeParser()
    scraped = ScrapedScene(
        title="Test Scene",
        code="TST-001",
        details="Test details",
        director="Test Director",
        urls=["https://example.com/scene"],
        date="2024-01-15",
    )

    result = parser.scene_from_scrape(scraped)

    assert result.title == "Test Scene"
    assert result.code == "TST-001"
    assert result.details == "Test details"
    assert result.director == "Test Director"
    assert result.urls == ["https://example.com/scene"]
    assert result.date == "2024-01-15"


@pytest.mark.unit
def test_scene_from_scrape_with_duration_int():
    """Test scene conversion with duration as integer in seconds."""
    parser = ScrapeParser()
    scraped = ScrapedScene(
        title="Test Scene",
        duration=5400,  # Integer (90 minutes in seconds)
    )

    result = parser.scene_from_scrape(scraped)

    # Duration is parsed but SceneCreateInput doesn't have duration field
    # Just verify it doesn't crash
    assert result.title == "Test Scene"


@pytest.mark.unit
def test_scene_from_scrape_with_duration_string():
    """Test scene conversion with duration as string (HH:MM:SS).

    This covers line 192: parse_duration is called when duration is a string.
    Using model_construct to bypass Pydantic validation since scrapers may return strings.
    """
    parser = ScrapeParser()
    scraped = ScrapedScene.model_construct(
        title="Test Scene",
        duration="01:30:00",  # String (90 minutes in HH:MM:SS format)
    )

    result = parser.scene_from_scrape(scraped)

    # Line 192 is covered when duration is parsed from string
    assert result.title == "Test Scene"


@pytest.mark.unit
def test_scene_from_scrape_with_studio():
    """Test scene conversion with studio stored_id."""
    parser = ScrapeParser()
    scraped = ScrapedScene(
        title="Test Scene",
        studio=ScrapedStudio.model_construct(
            stored_id="studio-123", name="Test Studio"
        ),
    )

    result = parser.scene_from_scrape(scraped)

    assert result.title == "Test Scene"
    assert result.studio_id == "studio-123"


@pytest.mark.unit
def test_scene_from_scrape_with_explicit_studio_id():
    """Test scene conversion with explicit studio_id override."""
    parser = ScrapeParser()
    scraped = ScrapedScene(
        title="Test Scene",
        studio=ScrapedStudio.model_construct(
            stored_id="studio-123", name="Test Studio"
        ),
    )

    result = parser.scene_from_scrape(scraped, studio_id="studio-456")

    assert result.studio_id == "studio-456"  # Should use explicit ID


@pytest.mark.unit
def test_scene_from_scrape_with_performers():
    """Test scene conversion with performers."""
    parser = ScrapeParser()
    scraped = ScrapedScene(
        title="Test Scene",
        performers=[
            ScrapedPerformer.model_construct(stored_id="perf-1", name="Performer 1"),
            ScrapedPerformer.model_construct(stored_id="perf-2", name="Performer 2"),
        ],
    )

    result = parser.scene_from_scrape(scraped)

    assert result.title == "Test Scene"
    assert result.performer_ids == ["perf-1", "perf-2"]


@pytest.mark.unit
def test_scene_from_scrape_with_tags():
    """Test scene conversion with tags."""
    parser = ScrapeParser()
    scraped = ScrapedScene(
        title="Test Scene",
        tags=[
            ScrapedTag.model_construct(stored_id="tag-1", name="Tag 1"),
            ScrapedTag.model_construct(stored_id="tag-2", name="Tag 2"),
        ],
    )

    result = parser.scene_from_scrape(scraped)

    assert result.title == "Test Scene"
    assert result.tag_ids == ["tag-1", "tag-2"]


@pytest.mark.unit
def test_scene_from_scrape_with_image():
    """Test scene conversion with cover image."""
    parser = ScrapeParser()
    scraped = ScrapedScene(
        title="Test Scene",
        image="data:image/jpeg;base64,/9j/4AAQSkZJRg...",
    )

    result = parser.scene_from_scrape(scraped)

    assert result.title == "Test Scene"
    assert result.cover_image == "data:image/jpeg;base64,/9j/4AAQSkZJRg..."


@pytest.mark.unit
def test_scene_from_scrape_unset_fields():
    """Test scene conversion with UNSET fields."""
    parser = ScrapeParser()
    scraped = ScrapedScene(
        title="Test Scene",
        # Other fields remain UNSET
    )

    result = parser.scene_from_scrape(scraped)

    assert result.title == "Test Scene"
    assert result.code is UNSET
    assert result.details is UNSET


@pytest.mark.unit
def test_scene_from_scrape_studio_without_stored_id():
    """Test scene conversion when studio has no stored_id.

    This covers lines 199->203 FALSE: when studio exists but doesn't have stored_id
    or stored_id is UNSET/None.
    """
    parser = ScrapeParser()
    # Studio with no stored_id attribute (or stored_id is UNSET)
    scraped = ScrapedScene(
        title="Test Scene",
        studio=ScrapedStudio(name="Test Studio"),  # No stored_id
    )

    result = parser.scene_from_scrape(scraped)

    assert result.title == "Test Scene"
    assert result.studio_id is UNSET  # Should remain UNSET when no stored_id


@pytest.mark.unit
def test_scene_from_scrape_performers_without_stored_id():
    """Test scene conversion when performers have no stored_id.

    This covers lines 207->206 FALSE and 209->213 FALSE: when performers exist
    but don't have stored_id, resulting in empty perf_ids list.
    """
    parser = ScrapeParser()
    # Performers with no stored_id attribute
    scraped = ScrapedScene(
        title="Test Scene",
        performers=[
            ScrapedPerformer(name="Performer 1"),  # No stored_id
            ScrapedPerformer(name="Performer 2"),  # No stored_id
        ],
    )

    result = parser.scene_from_scrape(scraped)

    assert result.title == "Test Scene"
    assert result.performer_ids is UNSET  # Should remain UNSET when no stored_ids


@pytest.mark.unit
def test_scene_from_scrape_tags_without_stored_id():
    """Test scene conversion when tags have no stored_id.

    This covers similar logic for tags: when tags exist but don't have stored_id,
    resulting in empty tag_id_list.
    """
    parser = ScrapeParser()
    # Tags with no stored_id attribute
    scraped = ScrapedScene(
        title="Test Scene",
        tags=[
            ScrapedTag(name="Tag 1"),  # No stored_id
            ScrapedTag(name="Tag 2"),  # No stored_id
        ],
    )

    result = parser.scene_from_scrape(scraped)

    assert result.title == "Test Scene"
    assert result.tag_ids is UNSET  # Should remain UNSET when no stored_ids


@pytest.mark.unit
def test_scene_from_scrape_performers_mixed_stored_ids():
    """Test scene conversion with mixed performers (some with stored_id, some without).

    This tests that only performers with valid stored_id are included.
    """
    parser = ScrapeParser()
    scraped = ScrapedScene(
        title="Test Scene",
        performers=[
            ScrapedPerformer.model_construct(
                stored_id="perf-1", name="Performer 1"
            ),  # Has ID
            ScrapedPerformer(name="Performer 2"),  # No stored_id
            ScrapedPerformer.model_construct(
                stored_id="perf-3", name="Performer 3"
            ),  # Has ID
        ],
    )

    result = parser.scene_from_scrape(scraped)

    assert result.title == "Test Scene"
    assert result.performer_ids == ["perf-1", "perf-3"]  # Only those with stored_id


# =============================================================================
# Performer Conversion Tests
# =============================================================================


@pytest.mark.unit
def test_performer_from_scrape_basic():
    """Test basic performer conversion from scraped data."""
    parser = ScrapeParser()
    scraped = ScrapedPerformer(
        name="Test Performer",
        gender="FEMALE",
        birthdate="1990-01-15",
        ethnicity="Caucasian",
        country="USA",
    )

    result = parser.performer_from_scrape(scraped)

    assert result.name == "Test Performer"
    assert result.gender == "FEMALE"
    assert result.birthdate == "1990-01-15"
    assert result.ethnicity == "Caucasian"
    assert result.country == "USA"


@pytest.mark.unit
def test_performer_from_scrape_with_height():
    """Test performer conversion with height string."""
    parser = ScrapeParser()
    scraped = ScrapedPerformer(
        name="Test Performer",
        height="5'9",
    )

    result = parser.performer_from_scrape(scraped)

    assert result.name == "Test Performer"
    assert result.height_cm == 175


@pytest.mark.unit
def test_performer_from_scrape_with_weight():
    """Test performer conversion with weight string."""
    parser = ScrapeParser()
    scraped = ScrapedPerformer(
        name="Test Performer",
        weight="154lbs",
    )

    result = parser.performer_from_scrape(scraped)

    assert result.name == "Test Performer"
    assert result.weight == 69


@pytest.mark.unit
def test_performer_from_scrape_with_aliases():
    """Test performer conversion with aliases."""
    parser = ScrapeParser()
    scraped = ScrapedPerformer(
        name="Test Performer",
        aliases="Alias 1, Alias 2, Alias 3",
    )

    result = parser.performer_from_scrape(scraped)

    assert result.name == "Test Performer"
    assert result.alias_list == ["Alias 1", "Alias 2", "Alias 3"]


@pytest.mark.unit
def test_performer_from_scrape_with_images():
    """Test performer conversion with multiple images (uses first)."""
    parser = ScrapeParser()
    scraped = ScrapedPerformer(
        name="Test Performer",
        images=[
            "data:image/jpeg;base64,image1...",
            "data:image/jpeg;base64,image2...",
        ],
    )

    result = parser.performer_from_scrape(scraped)

    assert result.name == "Test Performer"
    assert result.image == "data:image/jpeg;base64,image1..."


@pytest.mark.unit
def test_performer_from_scrape_with_tags():
    """Test performer conversion with tags."""
    parser = ScrapeParser()
    scraped = ScrapedPerformer(
        name="Test Performer",
        tags=[
            ScrapedTag.model_construct(stored_id="tag-1", name="Tag 1"),
            ScrapedTag.model_construct(stored_id="tag-2", name="Tag 2"),
        ],
    )

    result = parser.performer_from_scrape(scraped)

    assert result.name == "Test Performer"
    assert result.tag_ids == ["tag-1", "tag-2"]


@pytest.mark.unit
def test_performer_from_scrape_with_explicit_tag_ids():
    """Test performer conversion with explicit tag_ids override."""
    parser = ScrapeParser()
    scraped = ScrapedPerformer(
        name="Test Performer",
        tags=[
            ScrapedTag.model_construct(stored_id="tag-1", name="Tag 1"),
        ],
    )

    result = parser.performer_from_scrape(scraped, tag_ids=["tag-3", "tag-4"])

    assert result.tag_ids == ["tag-3", "tag-4"]  # Should use explicit IDs


@pytest.mark.unit
def test_performer_from_scrape_no_name():
    """Test performer conversion with no name defaults to 'Unknown'."""
    parser = ScrapeParser()
    scraped = ScrapedPerformer(
        gender="FEMALE",
    )

    result = parser.performer_from_scrape(scraped)

    assert result.name == "Unknown"


@pytest.mark.unit
def test_performer_from_scrape_all_fields():
    """Test performer conversion with all fields populated."""
    parser = ScrapeParser()
    scraped = ScrapedPerformer.model_construct(
        name="Test Performer",
        disambiguation="The Original",
        gender="FEMALE",
        birthdate="1990-01-15",
        ethnicity="Caucasian",
        country="USA",
        eye_color="Blue",
        height="5'9",
        measurements="34-24-36",
        fake_tits="No",
        career_length="2010-2020",
        tattoos="None",
        piercings="Ears",
        aliases="Alias 1, Alias 2",
        details="Test details",
        death_date="2021-01-01",
        hair_color="Blonde",
        weight="154lbs",
        urls=["https://example.com/performer"],
    )

    result = parser.performer_from_scrape(scraped)

    assert result.name == "Test Performer"
    assert result.disambiguation == "The Original"
    assert result.gender == "FEMALE"
    assert result.birthdate == "1990-01-15"
    assert result.ethnicity == "Caucasian"
    assert result.country == "USA"
    assert result.eye_color == "Blue"
    assert result.height_cm == 175
    assert result.measurements == "34-24-36"
    assert result.fake_tits == "No"
    assert result.career_length == "2010-2020"
    assert result.tattoos == "None"
    assert result.piercings == "Ears"
    assert result.alias_list == ["Alias 1", "Alias 2"]
    assert result.details == "Test details"
    assert result.death_date == "2021-01-01"
    assert result.hair_color == "Blonde"
    assert result.weight == 69
    assert result.urls == ["https://example.com/performer"]


@pytest.mark.unit
def test_performer_from_scrape_tags_without_stored_id():
    """Test performer conversion when tags have no stored_id.

    This covers lines 283->282 FALSE and 285->289 FALSE: when tags exist
    but don't have stored_id, resulting in empty tag_id_list.
    """
    parser = ScrapeParser()
    # Tags with no stored_id attribute
    scraped = ScrapedPerformer(
        name="Test Performer",
        tags=[
            ScrapedTag(name="Tag 1"),  # No stored_id
            ScrapedTag(name="Tag 2"),  # No stored_id
        ],
    )

    result = parser.performer_from_scrape(scraped)

    assert result.name == "Test Performer"
    assert result.tag_ids is UNSET  # Should remain UNSET when no stored_ids


# =============================================================================
# Entity Resolution Tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_resolve_studio_found(respx_stash_client: StashClient):
    """Test resolving studio by name when found."""
    # Mock find_studios response
    studios_data = {
        "count": 2,
        "studios": [
            {
                "id": "studio-1",
                "name": "Studio Alpha",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            },
            {
                "id": "studio-2",
                "name": "Studio Beta",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            },
        ],
    }

    respx.post("http://localhost:9999/graphql").mock(
        return_value=httpx.Response(
            200, json=create_graphql_response("findStudios", studios_data)
        )
    )

    parser = ScrapeParser(client=respx_stash_client)
    studio_id = await parser.resolve_studio("Studio Beta")

    assert studio_id == "studio-2"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_resolve_studio_not_found(respx_stash_client: StashClient):
    """Test resolving studio by name when not found."""
    studios_data = {
        "count": 1,
        "studios": [
            {
                "id": "studio-1",
                "name": "Studio Alpha",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            },
        ],
    }

    respx.post("http://localhost:9999/graphql").mock(
        return_value=httpx.Response(
            200, json=create_graphql_response("findStudios", studios_data)
        )
    )

    parser = ScrapeParser(client=respx_stash_client)
    studio_id = await parser.resolve_studio("Nonexistent Studio")

    assert studio_id is None


@pytest.mark.asyncio
@pytest.mark.unit
async def test_resolve_performer_found(respx_stash_client: StashClient):
    """Test resolving performer by name when found."""
    performers_data = {
        "count": 2,
        "performers": [
            {
                "id": "perf-1",
                "name": "Performer One",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            },
            {
                "id": "perf-2",
                "name": "Performer Two",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            },
        ],
    }

    respx.post("http://localhost:9999/graphql").mock(
        return_value=httpx.Response(
            200, json=create_graphql_response("findPerformers", performers_data)
        )
    )

    parser = ScrapeParser(client=respx_stash_client)
    performer_id = await parser.resolve_performer("Performer Two")

    assert performer_id == "perf-2"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_resolve_tag_found(respx_stash_client: StashClient):
    """Test resolving tag by name when found."""
    tags_data = {
        "count": 3,
        "tags": [
            {
                "id": "tag-1",
                "name": "Tag Alpha",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            },
            {
                "id": "tag-2",
                "name": "Tag Beta",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            },
            {
                "id": "tag-3",
                "name": "Tag Gamma",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            },
        ],
    }

    respx.post("http://localhost:9999/graphql").mock(
        return_value=httpx.Response(
            200, json=create_graphql_response("findTags", tags_data)
        )
    )

    parser = ScrapeParser(client=respx_stash_client)
    tag_id = await parser.resolve_tag("Tag Beta")

    assert tag_id == "tag-2"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_resolve_tags_multiple(respx_stash_client: StashClient):
    """Test resolving multiple tags by name."""
    tags_data = {
        "count": 4,
        "tags": [
            {
                "id": "tag-1",
                "name": "Tag Alpha",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            },
            {
                "id": "tag-2",
                "name": "Tag Beta",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            },
            {
                "id": "tag-3",
                "name": "Tag Gamma",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            },
            {
                "id": "tag-4",
                "name": "Tag Delta",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            },
        ],
    }

    respx.post("http://localhost:9999/graphql").mock(
        return_value=httpx.Response(
            200, json=create_graphql_response("findTags", tags_data)
        )
    )

    parser = ScrapeParser(client=respx_stash_client)
    tag_ids = await parser.resolve_tags(["Tag Beta", "Tag Delta", "Nonexistent Tag"])

    # Should return IDs only for found tags
    assert tag_ids == ["tag-2", "tag-4"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_resolve_studio_no_client():
    """Test resolve_studio raises error when no client provided."""
    parser = ScrapeParser()  # No client

    with pytest.raises(RuntimeError, match="Client required"):
        await parser.resolve_studio("Studio Name")


@pytest.mark.asyncio
@pytest.mark.unit
async def test_resolve_performer_no_client():
    """Test resolve_performer raises error when no client provided."""
    parser = ScrapeParser()  # No client

    with pytest.raises(RuntimeError, match="Client required"):
        await parser.resolve_performer("Performer Name")


@pytest.mark.asyncio
@pytest.mark.unit
async def test_resolve_tag_no_client():
    """Test resolve_tag raises error when no client provided."""
    parser = ScrapeParser()  # No client

    with pytest.raises(RuntimeError, match="Client required"):
        await parser.resolve_tag("Tag Name")


@pytest.mark.asyncio
@pytest.mark.unit
async def test_resolve_tags_no_client():
    """Test resolve_tags raises error when no client provided."""
    parser = ScrapeParser()  # No client

    with pytest.raises(RuntimeError, match="Client required"):
        await parser.resolve_tags(["Tag1", "Tag2"])


@pytest.mark.asyncio
@pytest.mark.unit
async def test_resolve_performer_not_found(respx_stash_client: StashClient):
    """Test resolve_performer returns None when performer not found.

    This covers line 473: return None when no matching performer.
    """
    performers_data = {
        "count": 2,
        "performers": [
            {
                "id": "perf-1",
                "name": "Performer One",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            },
            {
                "id": "perf-2",
                "name": "Performer Two",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            },
        ],
    }

    respx.post("http://localhost:9999/graphql").mock(
        return_value=httpx.Response(
            200, json=create_graphql_response("findPerformers", performers_data)
        )
    )

    parser = ScrapeParser(client=respx_stash_client)
    # Search for performer that doesn't exist in the list
    performer_id = await parser.resolve_performer("Nonexistent Performer")

    assert performer_id is None  # Line 473 is covered


@pytest.mark.asyncio
@pytest.mark.unit
async def test_resolve_tag_not_found(respx_stash_client: StashClient):
    """Test resolve_tag returns None when tag not found.

    This covers line 504: return None when no matching tag.
    """
    tags_data = {
        "count": 2,
        "tags": [
            {
                "id": "tag-1",
                "name": "Tag Alpha",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            },
            {
                "id": "tag-2",
                "name": "Tag Beta",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            },
        ],
    }

    respx.post("http://localhost:9999/graphql").mock(
        return_value=httpx.Response(
            200, json=create_graphql_response("findTags", tags_data)
        )
    )

    parser = ScrapeParser(client=respx_stash_client)
    # Search for tag that doesn't exist in the list
    tag_id = await parser.resolve_tag("Nonexistent Tag")

    assert tag_id is None  # Line 504 is covered


@pytest.mark.asyncio
@pytest.mark.unit
async def test_resolve_tags_skips_unset_ids(respx_stash_client: StashClient):
    """Test resolve_tags skips tags with UNSET IDs.

    This covers line 539->536: when tag_id is UNSET (field wasn't queried),
    skip adding it to the result list.
    """
    from unittest.mock import patch

    from stash_graphql_client.types import Tag

    # Mock find_tags to return tags where one has UNSET id
    async def mock_find_tags(*args, **kwargs):
        from stash_graphql_client.types import FindTagsResultType

        # Create tags with model_construct to set UNSET id
        tag1 = Tag.model_construct(id="tag-1", name="Tag Alpha")
        tag2 = Tag.model_construct(id=UNSET, name="Tag Beta")  # UNSET id!
        tag3 = Tag.model_construct(id="tag-3", name="Tag Gamma")

        return FindTagsResultType(count=3, tags=[tag1, tag2, tag3])

    with patch.object(respx_stash_client, "find_tags", side_effect=mock_find_tags):
        parser = ScrapeParser(client=respx_stash_client)
        tag_ids = await parser.resolve_tags(["Tag Alpha", "Tag Beta", "Tag Gamma"])

    # Tag Beta has UNSET id, so it's filtered at line 539
    assert tag_ids == ["tag-1", "tag-3"]  # Line 539->536 is covered!
