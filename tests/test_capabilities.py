"""Tests for stash_graphql_client.capabilities module.

Covers ServerCapabilities dataclass properties, detect_capabilities() through
the full respx HTTP path, version enforcement, and error wrapping.
"""

from __future__ import annotations

import httpx
import pytest
import respx

from stash_graphql_client.capabilities import (
    CAPABILITY_DETECTION_QUERY,
    MIN_SUPPORTED_APP_SCHEMA,
    ServerCapabilities,
)
from stash_graphql_client.errors import StashError, StashVersionError
from tests.fixtures import dump_graphql_calls
from tests.fixtures.stash.graphql_responses import (
    create_capability_response,
    make_server_capabilities,
)


# ---------------------------------------------------------------------------
# ServerCapabilities appSchema-derived property tests
# ---------------------------------------------------------------------------


class TestServerCapabilitiesProperties:
    """Test capability properties at boundary appSchema values."""

    @pytest.mark.unit
    def test_minimum_schema_no_extras(self) -> None:
        """appSchema 75 (minimum) — no optional capabilities."""
        caps = make_server_capabilities(75)
        assert not caps.has_studio_custom_fields
        assert not caps.has_tag_custom_fields
        assert not caps.has_performer_career_start_end
        assert not caps.has_scene_custom_fields
        assert not caps.has_studio_organized
        assert not caps.has_gallery_custom_fields
        assert not caps.has_group_custom_fields
        assert not caps.has_image_custom_fields
        assert not caps.has_folder_basename

    @pytest.mark.unit
    def test_studio_custom_fields_boundary(self) -> None:
        """has_studio_custom_fields flips at appSchema 76."""
        assert not make_server_capabilities(75).has_studio_custom_fields
        assert make_server_capabilities(76).has_studio_custom_fields
        assert make_server_capabilities(77).has_studio_custom_fields

    @pytest.mark.unit
    def test_tag_custom_fields_boundary(self) -> None:
        """has_tag_custom_fields flips at appSchema 77."""
        assert not make_server_capabilities(76).has_tag_custom_fields
        assert make_server_capabilities(77).has_tag_custom_fields

    @pytest.mark.unit
    def test_performer_career_start_end_boundary(self) -> None:
        """has_performer_career_start_end flips at appSchema 78."""
        assert not make_server_capabilities(77).has_performer_career_start_end
        assert make_server_capabilities(78).has_performer_career_start_end

    @pytest.mark.unit
    def test_scene_custom_fields_boundary(self) -> None:
        """has_scene_custom_fields flips at appSchema 79."""
        assert not make_server_capabilities(78).has_scene_custom_fields
        assert make_server_capabilities(79).has_scene_custom_fields

    @pytest.mark.unit
    def test_studio_organized_boundary(self) -> None:
        """has_studio_organized flips at appSchema 80."""
        assert not make_server_capabilities(79).has_studio_organized
        assert make_server_capabilities(80).has_studio_organized

    @pytest.mark.unit
    def test_gallery_custom_fields_boundary(self) -> None:
        """has_gallery_custom_fields flips at appSchema 81."""
        assert not make_server_capabilities(80).has_gallery_custom_fields
        assert make_server_capabilities(81).has_gallery_custom_fields

    @pytest.mark.unit
    def test_group_custom_fields_boundary(self) -> None:
        """has_group_custom_fields flips at appSchema 82."""
        assert not make_server_capabilities(81).has_group_custom_fields
        assert make_server_capabilities(82).has_group_custom_fields

    @pytest.mark.unit
    def test_image_custom_fields_boundary(self) -> None:
        """has_image_custom_fields flips at appSchema 83."""
        assert not make_server_capabilities(82).has_image_custom_fields
        assert make_server_capabilities(83).has_image_custom_fields

    @pytest.mark.unit
    def test_folder_basename_boundary(self) -> None:
        """has_folder_basename flips at appSchema 84."""
        assert not make_server_capabilities(83).has_folder_basename
        assert make_server_capabilities(84).has_folder_basename

    @pytest.mark.unit
    def test_folder_sub_folders_introspection_gated(self) -> None:
        """has_folder_sub_folders uses introspection, not appSchema threshold."""
        # Without type_fields, even high appSchema is False
        assert not make_server_capabilities(85).has_folder_sub_folders
        # With the field present in introspection data, it's True
        caps = make_server_capabilities(
            85,
            type_fields={"Folder": frozenset({"sub_folders"})},
        )
        assert caps.has_folder_sub_folders

    @pytest.mark.unit
    def test_performer_career_date_strings_boundary(self) -> None:
        """has_performer_career_date_strings flips at appSchema 85."""
        assert not make_server_capabilities(84).has_performer_career_date_strings
        assert make_server_capabilities(85).has_performer_career_date_strings

    @pytest.mark.unit
    def test_max_schema_all_capabilities(self) -> None:
        """Very high appSchema — all schema-gated capabilities enabled."""
        caps = make_server_capabilities(
            9999,
            type_names={
                "DuplicationCriterionInput",
                "PerformerMergeInput",
            },
            mutation_names={
                "bulkSceneMarkerUpdate",
                "bulkStudioUpdate",
                "destroyFiles",
                "revealFileInFileManager",
                "revealFolderInFileManager",
                "stashBoxBatchTagTag",
                "stashBoxBatchPerformerTag",
                "stashBoxBatchStudioTag",
            },
            query_names={"scrapeSingleTag"},
            type_fields={"Folder": frozenset({"sub_folders"})},
        )
        assert caps.has_studio_custom_fields
        assert caps.has_tag_custom_fields
        assert caps.has_performer_career_start_end
        assert caps.has_scene_custom_fields
        assert caps.has_studio_organized
        assert caps.has_gallery_custom_fields
        assert caps.has_group_custom_fields
        assert caps.has_image_custom_fields
        assert caps.has_folder_basename
        assert caps.has_performer_career_date_strings
        assert caps.has_folder_sub_folders
        assert caps.uses_new_duplication_type
        assert caps.has_type("PerformerMergeInput")
        assert caps.has_mutation("bulkSceneMarkerUpdate")
        assert caps.has_mutation("bulkStudioUpdate")
        assert caps.has_mutation("destroyFiles")
        assert caps.has_mutation("revealFileInFileManager")
        assert caps.has_mutation("revealFolderInFileManager")
        assert caps.has_mutation("stashBoxBatchTagTag")
        assert caps.has_mutation("stashBoxBatchPerformerTag")
        assert caps.has_mutation("stashBoxBatchStudioTag")
        assert caps.has_query("scrapeSingleTag")

    @pytest.mark.unit
    def test_uses_new_duplication_type(self) -> None:
        """uses_new_duplication_type delegates to has_type('DuplicationCriterionInput')."""
        assert not make_server_capabilities(84).uses_new_duplication_type
        assert make_server_capabilities(
            84, type_names={"DuplicationCriterionInput"}
        ).uses_new_duplication_type
        # Independent of appSchema — purely based on type existence
        assert make_server_capabilities(
            75, type_names={"DuplicationCriterionInput"}
        ).uses_new_duplication_type

    @pytest.mark.unit
    def test_frozen_dataclass(self) -> None:
        """ServerCapabilities is immutable (frozen dataclass)."""
        caps = make_server_capabilities(75)
        with pytest.raises(AttributeError):
            caps.app_schema = 84  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Lookup method tests
# ---------------------------------------------------------------------------


class TestLookupMethods:
    """Test has_query(), has_mutation(), has_type(), type_has_field(), input_has_field()."""

    @pytest.mark.unit
    def test_has_query(self) -> None:
        caps = make_server_capabilities(
            75, query_names={"findScenes", "findPerformers"}
        )
        assert caps.has_query("findScenes")
        assert caps.has_query("findPerformers")
        assert not caps.has_query("scrapeSingleTag")

    @pytest.mark.unit
    def test_has_mutation(self) -> None:
        caps = make_server_capabilities(75, mutation_names={"bulkStudioUpdate"})
        assert caps.has_mutation("bulkStudioUpdate")
        assert not caps.has_mutation("destroyFiles")

    @pytest.mark.unit
    def test_has_subscription(self) -> None:
        caps = make_server_capabilities(
            75, subscription_names={"jobsSubscribe", "loggingSubscribe"}
        )
        assert caps.has_subscription("jobsSubscribe")
        assert caps.has_subscription("loggingSubscribe")
        assert not caps.has_subscription("nonExistent")

    @pytest.mark.unit
    def test_has_type(self) -> None:
        caps = make_server_capabilities(75, type_names={"Scene", "Tag"})
        assert caps.has_type("Scene")
        assert caps.has_type("Tag")
        assert not caps.has_type("NonExistent")

    @pytest.mark.unit
    def test_type_has_field(self) -> None:
        caps = make_server_capabilities(
            75,
            type_fields={
                "Scene": frozenset({"id", "title", "custom_fields"}),
            },
        )
        assert caps.type_has_field("Scene", "id")
        assert caps.type_has_field("Scene", "title")
        assert not caps.type_has_field("Scene", "nonexistent")
        assert not caps.type_has_field("NonExistent", "id")

    @pytest.mark.unit
    def test_input_has_field(self) -> None:
        caps = make_server_capabilities(
            75,
            type_fields={
                "GenerateMetadataInput": frozenset({"covers", "sprites", "paths"}),
            },
        )
        assert caps.input_has_field("GenerateMetadataInput", "covers")
        assert caps.input_has_field("GenerateMetadataInput", "paths")
        assert not caps.input_has_field("GenerateMetadataInput", "imageIDs")
        assert not caps.input_has_field("UnknownInput", "covers")


# ---------------------------------------------------------------------------
# detect_capabilities() via respx (full HTTP path)
# ---------------------------------------------------------------------------


class TestDetectCapabilitiesViaClient:
    """Test capability detection through the full client init path with respx."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_detection_minimum_server(self, stash_context) -> None:
        """Client initialises successfully against minimum-version server."""
        with respx.mock:
            graphql_route = respx.post("http://localhost:9999/graphql").mock(
                return_value=httpx.Response(
                    200,
                    json=create_capability_response(
                        app_schema=75,
                        version="v0.30.0",
                    ),
                )
            )
            try:
                client = await stash_context.get_client()
            finally:
                dump_graphql_calls(graphql_route.calls)
            try:
                assert client._capabilities is not None
                assert client._capabilities.app_schema == 75
                assert client._capabilities.version_string == "v0.30.0"
                assert not client._capabilities.has_type("DuplicationCriterionInput")
            finally:
                await client.close()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_detection_latest_develop(self, stash_context) -> None:
        """Client detects capabilities on latest develop build."""
        with respx.mock:
            graphql_route = respx.post("http://localhost:9999/graphql").mock(
                return_value=httpx.Response(
                    200,
                    json=create_capability_response(
                        app_schema=84,
                        version="v0.30.1-98-gc874bd56",
                        type_names={"DuplicationCriterionInput"},
                    ),
                )
            )
            try:
                client = await stash_context.get_client()
            finally:
                dump_graphql_calls(graphql_route.calls)
            try:
                caps = client._capabilities
                assert caps is not None
                assert caps.app_schema == 84
                assert caps.version_string == "v0.30.1-98-gc874bd56"
                assert caps.has_type("DuplicationCriterionInput")
                assert caps.has_folder_basename
                assert caps.uses_new_duplication_type
            finally:
                await client.close()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_version_too_old_raises(self, stash_context) -> None:
        """Client raises RuntimeError wrapping StashVersionError for appSchema < 75.

        The StashVersionError is raised by detect_capabilities() but gets
        caught and re-wrapped by StashContext.get_client() as RuntimeError.
        """
        with respx.mock:
            graphql_route = respx.post("http://localhost:9999/graphql").mock(
                return_value=httpx.Response(
                    200,
                    json=create_capability_response(
                        app_schema=74,
                        version="v0.29.0",
                    ),
                )
            )
            try:
                with pytest.raises(RuntimeError, match="below minimum supported"):
                    await stash_context.get_client()
            finally:
                dump_graphql_calls(graphql_route.calls)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_server_error_during_detection(self, stash_context) -> None:
        """Server errors during detection bubble up through client init."""
        with respx.mock:
            graphql_route = respx.post("http://localhost:9999/graphql").mock(
                return_value=httpx.Response(500, text="Internal Server Error")
            )
            try:
                with pytest.raises(RuntimeError, match="Failed to initialize"):
                    await stash_context.get_client()
            finally:
                dump_graphql_calls(graphql_route.calls)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_capabilities_exposed_on_context(self, stash_context) -> None:
        """StashContext.capabilities returns detected capabilities after init."""
        with respx.mock:
            graphql_route = respx.post("http://localhost:9999/graphql").mock(
                return_value=httpx.Response(
                    200,
                    json=create_capability_response(
                        app_schema=80,
                        version="v0.30.1",
                    ),
                )
            )
            try:
                client = await stash_context.get_client()
            finally:
                dump_graphql_calls(graphql_route.calls)
            try:
                caps = stash_context.capabilities
                assert isinstance(caps, ServerCapabilities)
                assert caps.app_schema == 80
                assert caps.has_studio_organized
                assert not caps.has_gallery_custom_fields
            finally:
                await client.close()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_capabilities_not_available_before_init(self, stash_context) -> None:
        """StashContext.capabilities raises before client init."""
        with pytest.raises(RuntimeError, match="Capabilities not available"):
            _ = stash_context.capabilities


# ---------------------------------------------------------------------------
# Constants tests
# ---------------------------------------------------------------------------


class TestCapabilityConstants:
    """Test module-level constants."""

    @pytest.mark.unit
    def test_min_supported_app_schema(self) -> None:
        """MIN_SUPPORTED_APP_SCHEMA matches Stash v0.30.0 (appSchema 75)."""
        assert MIN_SUPPORTED_APP_SCHEMA == 75

    @pytest.mark.unit
    def test_capability_query_contains_required_fields(self) -> None:
        """The detection query probes version, systemStatus, and __schema fields."""
        assert "version" in CAPABILITY_DETECTION_QUERY
        assert "systemStatus" in CAPABILITY_DETECTION_QUERY
        assert "appSchema" in CAPABILITY_DETECTION_QUERY
        assert "__schema" in CAPABILITY_DETECTION_QUERY
        assert "queryType" in CAPABILITY_DETECTION_QUERY
        assert "mutationType" in CAPABILITY_DETECTION_QUERY
        assert "subscriptionType" in CAPABILITY_DETECTION_QUERY
        assert "types" in CAPABILITY_DETECTION_QUERY
        assert "inputFields" in CAPABILITY_DETECTION_QUERY


# ---------------------------------------------------------------------------
# StashVersionError tests
# ---------------------------------------------------------------------------


class TestStashVersionError:
    """Test StashVersionError in errors.py."""

    @pytest.mark.unit
    def test_inherits_from_stash_error(self) -> None:
        assert issubclass(StashVersionError, StashError)

    @pytest.mark.unit
    def test_can_be_instantiated(self) -> None:
        error = StashVersionError("Server too old")
        assert str(error) == "Server too old"
        assert isinstance(error, RuntimeError)
