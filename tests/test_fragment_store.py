"""Tests for stash_graphql_client.fragments.FragmentStore.

Covers the FragmentStore singleton rebuild logic, capability-gated field
injection, the _inject_named_fragment_fields helper, and query string assembly.
"""

from __future__ import annotations

import pytest

from stash_graphql_client.fragments import (
    _BASE_FOLDER_FIELDS,
    _BASE_GALLERY_FIELDS,
    _BASE_GROUP_FIELDS,
    _BASE_IMAGE_FIELDS,
    _BASE_PERFORMER_FIELDS,
    _BASE_SCENE_FIELDS,
    _BASE_SCRAPED_PERFORMER_FIELDS,
    _BASE_STUDIO_FIELDS,
    _BASE_TAG_FIELDS,
    FragmentStore,
    _inject_named_fragment_fields,
)
from tests.fixtures.stash.graphql_responses import make_server_capabilities


# ---------------------------------------------------------------------------
# _inject_named_fragment_fields helper
# ---------------------------------------------------------------------------


class TestInjectNamedFragmentFields:
    """Test the helper that inserts fields into named GraphQL fragments."""

    @pytest.mark.unit
    def test_inserts_before_closing_brace(self) -> None:
        """Extra fields are inserted before the last closing brace."""
        base = "fragment Foo on Bar {\n    id\n    name\n}"
        result = _inject_named_fragment_fields(base, "    extra_field")
        assert "    extra_field" in result
        # extra_field should appear before the closing brace
        assert result.index("extra_field") < result.rindex("}")

    @pytest.mark.unit
    def test_no_closing_brace(self) -> None:
        """If there's no closing brace, fields are appended."""
        base = "fragment Foo on Bar { id"
        result = _inject_named_fragment_fields(base, "    extra")
        assert result.endswith("    extra")

    @pytest.mark.unit
    def test_preserves_existing_content(self) -> None:
        """Original fields are preserved intact."""
        base = _BASE_GROUP_FIELDS
        result = _inject_named_fragment_fields(base, "    custom_fields")
        # Original content preserved
        assert "id" in result
        assert "name" in result
        # New field injected
        assert "custom_fields" in result


# ---------------------------------------------------------------------------
# FragmentStore: base build (appSchema 75, no extras)
# ---------------------------------------------------------------------------


class TestFragmentStoreBase:
    """Test FragmentStore initialises with base (minimum-version) fields."""

    @pytest.mark.unit
    def test_default_init_uses_base_fields(self) -> None:
        """A freshly-constructed FragmentStore uses _BASE_*_FIELDS."""
        store = FragmentStore()
        assert store.SCENE_FIELDS == _BASE_SCENE_FIELDS
        assert store.PERFORMER_FIELDS == _BASE_PERFORMER_FIELDS
        assert store.STUDIO_FIELDS == _BASE_STUDIO_FIELDS
        assert store.TAG_FIELDS == _BASE_TAG_FIELDS
        assert store.GALLERY_FIELDS == _BASE_GALLERY_FIELDS
        assert store.IMAGE_FIELDS == _BASE_IMAGE_FIELDS
        assert store.GROUP_FIELDS == _BASE_GROUP_FIELDS
        assert store.FOLDER_FIELDS == _BASE_FOLDER_FIELDS

    @pytest.mark.unit
    def test_base_fields_exclude_gated_fields(self) -> None:
        """Base fields do not contain any capability-gated fields."""
        store = FragmentStore()
        # No custom_fields in any base entity
        assert "custom_fields" not in store.SCENE_FIELDS
        assert "custom_fields" not in store.STUDIO_FIELDS
        assert "custom_fields" not in store.TAG_FIELDS
        assert "custom_fields" not in store.GALLERY_FIELDS
        assert "custom_fields" not in store.IMAGE_FIELDS
        assert "custom_fields" not in store.GROUP_FIELDS
        # No career fields in base performer
        assert "career_start" not in store.PERFORMER_FIELDS
        assert "career_end" not in store.PERFORMER_FIELDS
        # No organized in base studio
        assert "organized" not in store.STUDIO_FIELDS
        # No basename in base folder
        assert "basename" not in store.FOLDER_FIELDS

    @pytest.mark.unit
    def test_build_fields_without_capabilities_falls_back(self) -> None:
        """_build_fields() with _capabilities=None falls back to _build_base() (covers L2047-2048)."""
        store = FragmentStore()
        # Rebuild with capabilities to add gated fields
        store.rebuild(make_server_capabilities(84))
        assert "custom_fields" in store.SCENE_FIELDS

        # Manually clear capabilities and call _build_fields directly
        store._capabilities = None
        store._build_fields()

        # Should have fallen back to base — no gated fields
        assert "custom_fields" not in store.SCENE_FIELDS
        assert "basename" not in store.FOLDER_FIELDS
        assert store.SCENE_FIELDS == _BASE_SCENE_FIELDS

    @pytest.mark.unit
    def test_base_queries_built(self) -> None:
        """Base store has all query attributes defined."""
        store = FragmentStore()
        # Spot-check that queries exist and contain expected operations
        assert "findScene" in store.FIND_SCENE_QUERY
        assert "findScenes" in store.FIND_SCENES_QUERY
        assert "findPerformer" in store.FIND_PERFORMER_QUERY
        assert "findStudio" in store.FIND_STUDIO_QUERY
        assert "findTag" in store.FIND_TAG_QUERY
        assert "findGallery" in store.FIND_GALLERY_QUERY
        assert "findImage" in store.FIND_IMAGE_QUERY
        assert "findGroup" in store.FIND_GROUP_QUERY
        assert "findFolder" in store.FIND_FOLDER_QUERY


# ---------------------------------------------------------------------------
# FragmentStore: rebuild with capabilities
# ---------------------------------------------------------------------------


class TestFragmentStoreRebuild:
    """Test FragmentStore.rebuild() with various capability levels."""

    @pytest.mark.unit
    def test_rebuild_minimum_same_as_base(self) -> None:
        """rebuild(appSchema=75) produces identical fields to base."""
        store = FragmentStore()
        caps = make_server_capabilities(75)
        store.rebuild(caps)

        assert store.SCENE_FIELDS == _BASE_SCENE_FIELDS
        assert store.PERFORMER_FIELDS == _BASE_PERFORMER_FIELDS
        assert store.STUDIO_FIELDS == _BASE_STUDIO_FIELDS
        assert store.TAG_FIELDS == _BASE_TAG_FIELDS
        assert store.GALLERY_FIELDS == _BASE_GALLERY_FIELDS
        assert store.IMAGE_FIELDS == _BASE_IMAGE_FIELDS
        assert store.GROUP_FIELDS == _BASE_GROUP_FIELDS
        assert store.FOLDER_FIELDS == _BASE_FOLDER_FIELDS

    @pytest.mark.unit
    def test_rebuild_max_schema_all_fields(self) -> None:
        """rebuild(appSchema=84) adds all gated fields."""
        store = FragmentStore()
        caps = make_server_capabilities(84, type_names={"DuplicationCriterionInput"})
        store.rebuild(caps)

        # Scene gets custom_fields
        assert "custom_fields" in store.SCENE_FIELDS

        # Performer gets career_start, career_end, custom_fields
        assert "career_start" in store.PERFORMER_FIELDS
        assert "career_end" in store.PERFORMER_FIELDS
        assert "custom_fields" in store.PERFORMER_FIELDS

        # Studio gets custom_fields + organized
        assert "custom_fields" in store.STUDIO_FIELDS
        assert "organized" in store.STUDIO_FIELDS

        # Tag gets custom_fields
        assert "custom_fields" in store.TAG_FIELDS

        # Gallery gets custom_fields
        assert "custom_fields" in store.GALLERY_FIELDS

        # Image gets custom_fields
        assert "custom_fields" in store.IMAGE_FIELDS

        # Group gets custom_fields (via named fragment injection)
        assert "custom_fields" in store.GROUP_FIELDS

        # Folder gets basename (via named fragment injection)
        assert "basename" in store.FOLDER_FIELDS

    @pytest.mark.unit
    def test_rebuild_studio_custom_fields_only(self) -> None:
        """appSchema 76 adds studio custom_fields but not organized."""
        store = FragmentStore()
        caps = make_server_capabilities(76, version="v0.30.0")
        store.rebuild(caps)

        assert "custom_fields" in store.STUDIO_FIELDS
        assert "organized" not in store.STUDIO_FIELDS
        # Other entities still at base
        assert "custom_fields" not in store.TAG_FIELDS
        assert "custom_fields" not in store.SCENE_FIELDS

    @pytest.mark.unit
    def test_rebuild_tag_custom_fields(self) -> None:
        """appSchema 77 adds tag custom_fields."""
        store = FragmentStore()
        caps = make_server_capabilities(77)
        store.rebuild(caps)

        assert "custom_fields" in store.TAG_FIELDS
        # Performer doesn't have career fields yet
        assert "career_start" not in store.PERFORMER_FIELDS

    @pytest.mark.unit
    def test_rebuild_performer_career(self) -> None:
        """appSchema 78 adds performer career_start/career_end."""
        store = FragmentStore()
        caps = make_server_capabilities(78)
        store.rebuild(caps)

        assert "career_start" in store.PERFORMER_FIELDS
        assert "career_end" in store.PERFORMER_FIELDS
        # Scene doesn't have custom_fields yet
        assert "custom_fields" not in store.SCENE_FIELDS

    @pytest.mark.unit
    def test_rebuild_scene_custom_fields(self) -> None:
        """appSchema 79 adds scene custom_fields."""
        store = FragmentStore()
        caps = make_server_capabilities(79)
        store.rebuild(caps)

        assert "custom_fields" in store.SCENE_FIELDS

    @pytest.mark.unit
    def test_rebuild_studio_organized(self) -> None:
        """appSchema 80 adds studio organized."""
        store = FragmentStore()
        caps = make_server_capabilities(80)
        store.rebuild(caps)

        assert "organized" in store.STUDIO_FIELDS
        assert "custom_fields" in store.STUDIO_FIELDS  # from >= 76

    @pytest.mark.unit
    def test_rebuild_gallery_custom_fields(self) -> None:
        """appSchema 81 adds gallery custom_fields."""
        store = FragmentStore()
        caps = make_server_capabilities(81)
        store.rebuild(caps)

        assert "custom_fields" in store.GALLERY_FIELDS

    @pytest.mark.unit
    def test_rebuild_group_custom_fields(self) -> None:
        """appSchema 82 adds group custom_fields via named fragment injection."""
        store = FragmentStore()
        caps = make_server_capabilities(82)
        store.rebuild(caps)

        assert "custom_fields" in store.GROUP_FIELDS
        # Verify it's still a valid named fragment
        assert "fragment GroupFields on Group" in store.GROUP_FIELDS
        assert store.GROUP_FIELDS.rstrip().endswith("}")

    @pytest.mark.unit
    def test_rebuild_image_custom_fields(self) -> None:
        """appSchema 83 adds image custom_fields."""
        store = FragmentStore()
        caps = make_server_capabilities(83)
        store.rebuild(caps)

        assert "custom_fields" in store.IMAGE_FIELDS

    @pytest.mark.unit
    def test_rebuild_folder_basename(self) -> None:
        """appSchema 84 adds folder basename via named fragment injection."""
        store = FragmentStore()
        caps = make_server_capabilities(84)
        store.rebuild(caps)

        assert "basename" in store.FOLDER_FIELDS
        # Verify it's still a valid named fragment
        assert "fragment FolderFields on Folder" in store.FOLDER_FIELDS
        assert store.FOLDER_FIELDS.rstrip().endswith("}")

    @pytest.mark.unit
    def test_rebuild_folder_sub_folders(self) -> None:
        """sub_folders injected when introspection reports the field on Folder."""
        store = FragmentStore()
        caps = make_server_capabilities(
            85,
            type_fields={"Folder": frozenset({"sub_folders"})},
        )
        store.rebuild(caps)

        assert "sub_folders" in store.FOLDER_FIELDS
        assert "fragment FolderFields on Folder" in store.FOLDER_FIELDS
        assert store.FOLDER_FIELDS.rstrip().endswith("}")

    @pytest.mark.unit
    def test_rebuild_folder_sub_folders_absent(self) -> None:
        """sub_folders NOT injected when introspection lacks the field."""
        store = FragmentStore()
        caps = make_server_capabilities(85)
        store.rebuild(caps)

        assert "sub_folders" not in store.FOLDER_FIELDS


# ---------------------------------------------------------------------------
# Query string assembly after rebuild
# ---------------------------------------------------------------------------


class TestFragmentStoreQueries:
    """Test that queries are rebuilt with the correct fields after rebuild."""

    @pytest.mark.unit
    def test_queries_reflect_rebuilt_fields(self) -> None:
        """Queries embed the rebuilt fields, not the base ones."""
        store = FragmentStore()
        caps = make_server_capabilities(84, type_names={"DuplicationCriterionInput"})
        store.rebuild(caps)

        # Scene queries should contain custom_fields via SceneFragment
        assert "custom_fields" in store.FIND_SCENE_QUERY
        assert "custom_fields" in store.FIND_SCENES_QUERY
        assert "custom_fields" in store.CREATE_SCENE_MUTATION
        assert "custom_fields" in store.UPDATE_SCENE_MUTATION

        # Performer queries should contain career fields
        assert "career_start" in store.FIND_PERFORMER_QUERY
        assert "career_end" in store.FIND_PERFORMERS_QUERY

        # Studio queries should contain organized
        assert "organized" in store.FIND_STUDIO_QUERY

        # Group queries should contain custom_fields
        assert "custom_fields" in store.FIND_GROUP_QUERY

        # Folder queries should contain basename
        assert "basename" in store.FIND_FOLDER_QUERY

    @pytest.mark.unit
    def test_base_queries_exclude_gated_fields(self) -> None:
        """Base queries do not contain gated fields."""
        store = FragmentStore()

        assert "custom_fields" not in store.FIND_SCENE_QUERY
        assert "career_start" not in store.FIND_PERFORMER_QUERY
        assert "organized" not in store.FIND_STUDIO_QUERY
        assert "custom_fields" not in store.FIND_GROUP_QUERY
        assert "basename" not in store.FIND_FOLDER_QUERY

    @pytest.mark.unit
    def test_rebuild_is_idempotent(self) -> None:
        """Calling rebuild() twice with same capabilities produces same result."""
        store = FragmentStore()
        caps = make_server_capabilities(84)

        store.rebuild(caps)
        first_scene = store.FIND_SCENE_QUERY
        first_group = store.FIND_GROUP_QUERY

        store.rebuild(caps)
        assert first_scene == store.FIND_SCENE_QUERY
        assert first_group == store.FIND_GROUP_QUERY

    @pytest.mark.unit
    def test_rebuild_downgrade(self) -> None:
        """Rebuilding with lower capabilities removes gated fields."""
        store = FragmentStore()

        # First build with all features
        store.rebuild(make_server_capabilities(84))
        assert "custom_fields" in store.SCENE_FIELDS
        assert "basename" in store.FOLDER_FIELDS

        # Downgrade to minimum
        store.rebuild(make_server_capabilities(75))
        assert "custom_fields" not in store.SCENE_FIELDS
        assert "basename" not in store.FOLDER_FIELDS
        assert "custom_fields" not in store.FIND_SCENE_QUERY
        assert "basename" not in store.FIND_FOLDER_QUERY


# ---------------------------------------------------------------------------
# FragmentStore: scraped type fields
# ---------------------------------------------------------------------------


class TestFragmentStoreScrapedTypes:
    """Test scraped type field constants and capability gating."""

    @pytest.mark.unit
    def test_base_scraped_performer_excludes_career(self) -> None:
        """Base SCRAPED_PERFORMER_FIELDS excludes career_start/career_end."""
        store = FragmentStore()
        assert "career_start" not in store.SCRAPED_PERFORMER_FIELDS
        assert "career_end" not in store.SCRAPED_PERFORMER_FIELDS

    @pytest.mark.unit
    def test_base_scraped_performer_includes_all_other_fields(self) -> None:
        """Base SCRAPED_PERFORMER_FIELDS includes penis_length, circumcised, etc."""
        store = FragmentStore()
        assert "penis_length" in store.SCRAPED_PERFORMER_FIELDS
        assert "circumcised" in store.SCRAPED_PERFORMER_FIELDS
        assert "career_length" in store.SCRAPED_PERFORMER_FIELDS
        assert "disambiguation" in store.SCRAPED_PERFORMER_FIELDS
        assert "remote_site_id" in store.SCRAPED_PERFORMER_FIELDS

    @pytest.mark.unit
    def test_rebuild_adds_career_fields_at_78(self) -> None:
        """rebuild(appSchema=78) adds career_start/career_end to SCRAPED_PERFORMER_FIELDS."""
        store = FragmentStore()
        store.rebuild(make_server_capabilities(78))
        assert "career_start" in store.SCRAPED_PERFORMER_FIELDS
        assert "career_end" in store.SCRAPED_PERFORMER_FIELDS

    @pytest.mark.unit
    def test_rebuild_excludes_career_fields_at_77(self) -> None:
        """rebuild(appSchema=77) does not add career_start/career_end."""
        store = FragmentStore()
        store.rebuild(make_server_capabilities(77))
        assert "career_start" not in store.SCRAPED_PERFORMER_FIELDS
        assert "career_end" not in store.SCRAPED_PERFORMER_FIELDS

    @pytest.mark.unit
    def test_scraped_performer_fields_match_base(self) -> None:
        """Default SCRAPED_PERFORMER_FIELDS equals the base constant."""
        store = FragmentStore()
        assert store.SCRAPED_PERFORMER_FIELDS == _BASE_SCRAPED_PERFORMER_FIELDS

    @pytest.mark.unit
    def test_scraped_scene_fields_have_nested_objects(self) -> None:
        """SCRAPED_SCENE_FIELDS includes nested studio, tags, performers, groups."""
        store = FragmentStore()
        assert "studio {" in store.SCRAPED_SCENE_FIELDS
        assert "tags {" in store.SCRAPED_SCENE_FIELDS
        assert "performers {" in store.SCRAPED_SCENE_FIELDS
        assert "groups {" in store.SCRAPED_SCENE_FIELDS

    @pytest.mark.unit
    def test_scraped_group_fields_equal_movie_fields(self) -> None:
        """SCRAPED_MOVIE_FIELDS is the same as SCRAPED_GROUP_FIELDS."""
        store = FragmentStore()
        assert store.SCRAPED_MOVIE_FIELDS == store.SCRAPED_GROUP_FIELDS

    @pytest.mark.unit
    def test_scraped_tag_fields_include_description(self) -> None:
        """SCRAPED_TAG_FIELDS includes description and alias_list."""
        store = FragmentStore()
        assert "description" in store.SCRAPED_TAG_FIELDS
        assert "alias_list" in store.SCRAPED_TAG_FIELDS

    @pytest.mark.unit
    def test_scraped_studio_fields_include_parent(self) -> None:
        """SCRAPED_STUDIO_FIELDS includes parent nested object."""
        store = FragmentStore()
        assert "parent {" in store.SCRAPED_STUDIO_FIELDS
        assert "remote_site_id" in store.SCRAPED_STUDIO_FIELDS


# ---------------------------------------------------------------------------
# Scraped type query string assembly
# ---------------------------------------------------------------------------


class TestFragmentStoreScrapedQueries:
    """Test that scraper queries are built correctly after rebuild."""

    @pytest.mark.unit
    def test_base_scraper_queries_exist(self) -> None:
        """Base store has all scraper query attributes defined."""
        store = FragmentStore()
        assert "scrapeSingleScene" in store.SCRAPE_SINGLE_SCENE_QUERY
        assert "scrapeMultiScenes" in store.SCRAPE_MULTI_SCENES_QUERY
        assert "scrapeSingleStudio" in store.SCRAPE_SINGLE_STUDIO_QUERY
        assert "scrapeSingleTag" in store.SCRAPE_SINGLE_TAG_QUERY
        assert "scrapeSinglePerformer" in store.SCRAPE_SINGLE_PERFORMER_QUERY
        assert "scrapeMultiPerformers" in store.SCRAPE_MULTI_PERFORMERS_QUERY
        assert "scrapeSingleGallery" in store.SCRAPE_SINGLE_GALLERY_QUERY
        assert "scrapeSingleMovie" in store.SCRAPE_SINGLE_MOVIE_QUERY
        assert "scrapeSingleGroup" in store.SCRAPE_SINGLE_GROUP_QUERY
        assert "scrapeSingleImage" in store.SCRAPE_SINGLE_IMAGE_QUERY
        assert "scrapeURL" in store.SCRAPE_URL_QUERY
        assert "scrapePerformerURL" in store.SCRAPE_PERFORMER_URL_QUERY
        assert "scrapeSceneURL" in store.SCRAPE_SCENE_URL_QUERY
        assert "scrapeGalleryURL" in store.SCRAPE_GALLERY_URL_QUERY
        assert "scrapeImageURL" in store.SCRAPE_IMAGE_URL_QUERY
        assert "scrapeMovieURL" in store.SCRAPE_MOVIE_URL_QUERY
        assert "scrapeGroupURL" in store.SCRAPE_GROUP_URL_QUERY

    @pytest.mark.unit
    def test_performer_queries_exclude_career_at_base(self) -> None:
        """Base scraper performer queries do not contain career_start/career_end."""
        store = FragmentStore()
        assert "career_start" not in store.SCRAPE_SINGLE_PERFORMER_QUERY
        assert "career_start" not in store.SCRAPE_MULTI_PERFORMERS_QUERY
        assert "career_start" not in store.SCRAPE_PERFORMER_URL_QUERY

    @pytest.mark.unit
    def test_performer_queries_include_career_at_78(self) -> None:
        """rebuild(appSchema=78) adds career_start/end to performer queries."""
        store = FragmentStore()
        store.rebuild(make_server_capabilities(78))
        assert "career_start" in store.SCRAPE_SINGLE_PERFORMER_QUERY
        assert "career_end" in store.SCRAPE_SINGLE_PERFORMER_QUERY
        assert "career_start" in store.SCRAPE_MULTI_PERFORMERS_QUERY
        assert "career_start" in store.SCRAPE_PERFORMER_URL_QUERY

    @pytest.mark.unit
    def test_performer_queries_include_penis_circumcised(self) -> None:
        """All performer queries include penis_length and circumcised."""
        store = FragmentStore()
        for query in [
            store.SCRAPE_SINGLE_PERFORMER_QUERY,
            store.SCRAPE_MULTI_PERFORMERS_QUERY,
            store.SCRAPE_PERFORMER_URL_QUERY,
        ]:
            assert "penis_length" in query
            assert "circumcised" in query

    @pytest.mark.unit
    def test_scrape_url_has_union_fragments(self) -> None:
        """SCRAPE_URL_QUERY contains inline fragments for all scraped types."""
        store = FragmentStore()
        assert "... on ScrapedStudio" in store.SCRAPE_URL_QUERY
        assert "... on ScrapedTag" in store.SCRAPE_URL_QUERY
        assert "... on ScrapedScene" in store.SCRAPE_URL_QUERY
        assert "... on ScrapedGallery" in store.SCRAPE_URL_QUERY
        assert "... on ScrapedImage" in store.SCRAPE_URL_QUERY
        assert "... on ScrapedMovie" in store.SCRAPE_URL_QUERY
        assert "... on ScrapedGroup" in store.SCRAPE_URL_QUERY
        assert "... on ScrapedPerformer" in store.SCRAPE_URL_QUERY
        assert "__typename" in store.SCRAPE_URL_QUERY

    @pytest.mark.unit
    def test_rebuild_downgrade_removes_career_from_scraped(self) -> None:
        """Downgrading removes career_start/end from scraped performer queries."""
        store = FragmentStore()
        store.rebuild(make_server_capabilities(84))
        assert "career_start" in store.SCRAPE_SINGLE_PERFORMER_QUERY

        store.rebuild(make_server_capabilities(75))
        assert "career_start" not in store.SCRAPE_SINGLE_PERFORMER_QUERY
        assert "career_start" not in store.SCRAPED_PERFORMER_FIELDS


# ---------------------------------------------------------------------------
# ScrapedPerformer / ScrapedPerformerInput career date coercion
# (scraped_types.py lines 137-139, 177-179)
# ---------------------------------------------------------------------------


class TestScrapedPerformerCareerDateCoercion:
    """Test _coerce_career_date on ScrapedPerformer and ScrapedPerformerInput."""

    @pytest.mark.unit
    def test_scraped_performer_career_start_int_coerced(self) -> None:
        """ScrapedPerformer coerces int career_start to str."""
        from stash_graphql_client.types.scraped_types import ScrapedPerformer

        p = ScrapedPerformer(career_start=2020)
        assert p.career_start == "2020"

    @pytest.mark.unit
    def test_scraped_performer_career_end_str_passthrough(self) -> None:
        """ScrapedPerformer passes through str career_end unchanged."""
        from stash_graphql_client.types.scraped_types import ScrapedPerformer

        p = ScrapedPerformer(career_end="2023-06")
        assert p.career_end == "2023-06"

    @pytest.mark.unit
    def test_scraped_performer_input_career_start_int_coerced(self) -> None:
        """ScrapedPerformerInput coerces int career_start to str."""
        from stash_graphql_client.types.scraped_types import ScrapedPerformerInput

        inp = ScrapedPerformerInput(career_start=2019)
        assert inp.career_start == "2019"

    @pytest.mark.unit
    def test_scraped_performer_input_career_end_str_passthrough(self) -> None:
        """ScrapedPerformerInput passes through str career_end unchanged."""
        from stash_graphql_client.types.scraped_types import ScrapedPerformerInput

        inp = ScrapedPerformerInput(career_end="2022")
        assert inp.career_end == "2022"
