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
        caps = make_server_capabilities(84, has_dup=True)
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


# ---------------------------------------------------------------------------
# Query string assembly after rebuild
# ---------------------------------------------------------------------------


class TestFragmentStoreQueries:
    """Test that queries are rebuilt with the correct fields after rebuild."""

    @pytest.mark.unit
    def test_queries_reflect_rebuilt_fields(self) -> None:
        """Queries embed the rebuilt fields, not the base ones."""
        store = FragmentStore()
        caps = make_server_capabilities(84, has_dup=True)
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
