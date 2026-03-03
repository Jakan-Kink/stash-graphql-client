"""Integration tests for server capability detection.

Tests that the client correctly detects and exposes server capabilities
from a real Stash instance. These tests verify that the capability
detection query runs successfully and populates ServerCapabilities.
"""

import pytest

from stash_graphql_client import StashClient
from stash_graphql_client.capabilities import (
    MIN_SUPPORTED_APP_SCHEMA,
    ServerCapabilities,
)
from stash_graphql_client.fragments import fragment_store
from stash_graphql_client.types import Group, Performer, Studio, Tag
from stash_graphql_client.types.unset import UNSET, is_set
from tests.fixtures import capture_graphql_calls
from tests.fixtures.stash.graphql_responses import _MUTATION_REGISTRY, _QUERY_REGISTRY


@pytest.mark.integration
@pytest.mark.asyncio
async def test_capabilities_detected_after_init(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test that ServerCapabilities is populated after client initialization."""
    async with stash_cleanup_tracker(stash_client):
        assert stash_client._capabilities is not None
        assert isinstance(stash_client._capabilities, ServerCapabilities)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_capabilities_app_schema_meets_minimum(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test that detected appSchema meets the library's minimum requirement.

    If initialization succeeded, the server must be >= MIN_SUPPORTED_APP_SCHEMA.
    This test verifies the value was populated correctly (not zero, not None).
    """
    async with stash_cleanup_tracker(stash_client):
        caps = stash_client._capabilities
        assert caps is not None

        assert isinstance(caps.app_schema, int)
        assert caps.app_schema >= MIN_SUPPORTED_APP_SCHEMA, (
            f"Connected server appSchema {caps.app_schema} "
            f"is below minimum {MIN_SUPPORTED_APP_SCHEMA}"
        )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_capabilities_version_string_populated(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test that the version string was read from the server."""
    async with stash_cleanup_tracker(stash_client):
        caps = stash_client._capabilities
        assert caps is not None

        assert isinstance(caps.version_string, str)
        assert len(caps.version_string) > 0
        assert caps.version_string != "unknown"
        # Stash versions begin with "v"
        assert caps.version_string.startswith("v"), (
            f"Expected version_string to start with 'v', got: {caps.version_string!r}"
        )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_capabilities_duplication_criterion_flag(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test that the DuplicationCriterionInput type probe is a boolean."""
    async with stash_cleanup_tracker(stash_client):
        caps = stash_client._capabilities
        assert caps is not None

        # The flag itself must be a bool regardless of server version
        assert isinstance(caps.has_duplication_criterion_input, bool)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_capabilities_derived_properties_consistent(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test that derived capability properties are consistent with app_schema."""
    async with stash_cleanup_tracker(stash_client):
        caps = stash_client._capabilities
        assert caps is not None

        schema = caps.app_schema

        # Each derived property must agree with the raw app_schema value
        assert caps.has_studio_custom_fields == (schema >= 76)
        assert caps.has_tag_custom_fields == (schema >= 77)
        assert caps.has_performer_career_start_end == (schema >= 78)
        assert caps.has_scene_custom_fields == (schema >= 79)
        assert caps.has_studio_organized == (schema >= 80)
        assert caps.has_gallery_custom_fields == (schema >= 81)
        assert caps.has_group_custom_fields == (schema >= 82)
        assert caps.has_image_custom_fields == (schema >= 83)
        assert caps.has_folder_basename == (schema >= 84)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fragment_store_rebuilt_with_server_capabilities(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test that the fragment store was rebuilt with the detected capabilities.

    After initialization, the fragment store should have all queries built
    and available. Accessing them should not raise AttributeError.
    """
    async with stash_cleanup_tracker(stash_client):
        # These queries must exist after a successful rebuild
        assert fragment_store.FIND_TAG_QUERY is not None
        assert fragment_store.FIND_PERFORMER_QUERY is not None
        assert fragment_store.FIND_SCENE_QUERY is not None
        assert fragment_store.FIND_STUDIO_QUERY is not None

        # They should be non-empty strings (the fragment + query body)
        assert len(str(fragment_store.FIND_TAG_QUERY)) > 0
        assert len(str(fragment_store.FIND_PERFORMER_QUERY)) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_capability_detection_no_calls_after_init(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test that reading capabilities does not trigger additional GraphQL calls.

    The CAPABILITY_DETECTION_QUERY ran once during initialization. After that,
    reading _capabilities should be a pure attribute access with no network I/O.
    """
    async with (
        stash_cleanup_tracker(stash_client),
        capture_graphql_calls(stash_client) as calls,
    ):
        # No additional calls should happen just from reading capabilities
        assert stash_client._capabilities is not None
        assert len(calls) == 0, (
            "Reading _capabilities should not trigger any GraphQL calls"
        )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_capability_detection_uses_single_combined_query(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test that initialization uses exactly one GraphQL round-trip.

    The CAPABILITY_DETECTION_QUERY bundles version + systemStatus + __type into
    a single request. We verify this by creating a fresh client from the same
    connection config and wrapping _raw_execute — the method that is passed to
    detect_capabilities and maps 1:1 to HTTP round-trips — before calling
    initialize(), then asserting it was invoked exactly once with the combined query.
    """
    from unittest.mock import patch

    conn, verify_ssl = stash_client._init_args
    fresh_client = StashClient(conn=conn, verify_ssl=verify_ssl)

    try:
        with patch.object(
            fresh_client,
            "_raw_execute",
            wraps=fresh_client._raw_execute,
        ) as mock_raw:
            await fresh_client.initialize()

        # Exactly one HTTP round-trip during initialization
        assert mock_raw.call_count == 1, (
            f"Expected exactly 1 GraphQL round-trip during initialization, "
            f"got {mock_raw.call_count}"
        )

        # That single call must be the combined capability detection query
        query_sent = mock_raw.call_args[0][0]
        assert "systemStatus" in query_sent
        assert "version" in query_sent
        assert "__type" in query_sent

        assert fresh_client._capabilities is not None
    finally:
        await fresh_client.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_capabilities_mutation_flags_are_booleans(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """All mutation- and query-presence flags must be bool regardless of server version.

    The flags are populated during initialization from a single introspection
    query. This test confirms they were parsed correctly into Python bools.
    """
    async with stash_cleanup_tracker(stash_client):
        caps = stash_client._capabilities
        assert caps is not None

        assert isinstance(caps.has_performer_merge_input, bool)
        for field_name in _MUTATION_REGISTRY:
            flag = getattr(caps, field_name)
            assert isinstance(flag, bool), (
                f"Expected {field_name} to be bool, got {type(flag).__name__}"
            )
        for field_name in _QUERY_REGISTRY:
            flag = getattr(caps, field_name)
            assert isinstance(flag, bool), (
                f"Expected {field_name} to be bool, got {type(flag).__name__}"
            )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_capabilities_mutation_flags_match_introspection(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Mutation-presence flags match a fresh direct introspection of the Mutation type.

    This cross-checks that the flags set during initialization (from the combined
    CAPABILITY_DETECTION_QUERY) agree with a live re-query of the Mutation type.
    """
    async with (
        stash_cleanup_tracker(stash_client),
        capture_graphql_calls(stash_client) as calls,
    ):
        result = await stash_client.execute(
            '{ _mutations: __type(name: "Mutation") { fields { name } } }'
        )

        assert len(calls) == 1
        assert calls[0]["exception"] is None

        mutation_names: set[str] = {
            f["name"] for f in ((result.get("_mutations") or {}).get("fields") or [])
        }

        caps = stash_client._capabilities
        assert caps is not None

        for field_name, mutation_name in _MUTATION_REGISTRY.items():
            expected = mutation_name in mutation_names
            actual = getattr(caps, field_name)
            assert actual == expected, (
                f"{field_name}: capability flag is {actual} but "
                f"'{mutation_name}' {'is' if expected else 'is not'} in Mutation type"
            )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_capabilities_query_flags_match_introspection(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Query-presence flags match a fresh direct introspection of the Query type.

    This cross-checks that the flags set during initialization (from the combined
    CAPABILITY_DETECTION_QUERY) agree with a live re-query of the Query type.
    """
    async with (
        stash_cleanup_tracker(stash_client),
        capture_graphql_calls(stash_client) as calls,
    ):
        result = await stash_client.execute(
            '{ _queries: __type(name: "Query") { fields { name } } }'
        )

        assert len(calls) == 1
        assert calls[0]["exception"] is None

        query_names: set[str] = {
            f["name"] for f in ((result.get("_queries") or {}).get("fields") or [])
        }

        caps = stash_client._capabilities
        assert caps is not None

        for field_name, query_name in _QUERY_REGISTRY.items():
            expected = query_name in query_names
            actual = getattr(caps, field_name)
            assert actual == expected, (
                f"{field_name}: capability flag is {actual} but "
                f"'{query_name}' {'is' if expected else 'is not'} in Query type"
            )


# =============================================================================
# Fragment store field-content tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fragment_store_scene_fields_match_capabilities(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """FIND_SCENE_QUERY contains custom_fields iff the server supports it."""
    async with stash_cleanup_tracker(stash_client):
        caps = stash_client._capabilities
        assert caps is not None

        query = str(fragment_store.FIND_SCENE_QUERY)
        if caps.has_scene_custom_fields:
            assert "custom_fields" in query, (
                f"Server appSchema={caps.app_schema} >= 79 but FIND_SCENE_QUERY "
                f"is missing custom_fields"
            )
        else:
            assert "custom_fields" not in query, (
                f"Server appSchema={caps.app_schema} < 79 but FIND_SCENE_QUERY "
                f"unexpectedly contains custom_fields"
            )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fragment_store_performer_fields_match_capabilities(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """FIND_PERFORMER_QUERY contains career_start/career_end iff the server supports it."""
    async with stash_cleanup_tracker(stash_client):
        caps = stash_client._capabilities
        assert caps is not None

        query = str(fragment_store.FIND_PERFORMER_QUERY)
        if caps.has_performer_career_start_end:
            assert "career_start" in query, (
                f"Server appSchema={caps.app_schema} >= 78 but FIND_PERFORMER_QUERY "
                f"is missing career_start"
            )
            assert "career_end" in query, (
                f"Server appSchema={caps.app_schema} >= 78 but FIND_PERFORMER_QUERY "
                f"is missing career_end"
            )
        else:
            assert "career_start" not in query
            assert "career_end" not in query


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fragment_store_studio_fields_match_capabilities(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """FIND_STUDIO_QUERY contains custom_fields/organized based on server capabilities."""
    async with stash_cleanup_tracker(stash_client):
        caps = stash_client._capabilities
        assert caps is not None

        query = str(fragment_store.FIND_STUDIO_QUERY)
        if caps.has_studio_custom_fields:
            assert "custom_fields" in query, (
                f"Server appSchema={caps.app_schema} >= 76 but FIND_STUDIO_QUERY "
                f"is missing custom_fields"
            )
        else:
            assert "custom_fields" not in query

        if caps.has_studio_organized:
            assert "organized" in query, (
                f"Server appSchema={caps.app_schema} >= 80 but FIND_STUDIO_QUERY "
                f"is missing organized"
            )
        else:
            assert "organized" not in query


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fragment_store_tag_fields_match_capabilities(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """FIND_TAG_QUERY contains custom_fields iff the server supports it."""
    async with stash_cleanup_tracker(stash_client):
        caps = stash_client._capabilities
        assert caps is not None

        query = str(fragment_store.FIND_TAG_QUERY)
        if caps.has_tag_custom_fields:
            assert "custom_fields" in query, (
                f"Server appSchema={caps.app_schema} >= 77 but FIND_TAG_QUERY "
                f"is missing custom_fields"
            )
        else:
            assert "custom_fields" not in query


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fragment_store_gallery_fields_match_capabilities(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """FIND_GALLERY_QUERY contains custom_fields iff the server supports it."""
    async with stash_cleanup_tracker(stash_client):
        caps = stash_client._capabilities
        assert caps is not None

        query = str(fragment_store.FIND_GALLERY_QUERY)
        if caps.has_gallery_custom_fields:
            assert "custom_fields" in query, (
                f"Server appSchema={caps.app_schema} >= 81 but FIND_GALLERY_QUERY "
                f"is missing custom_fields"
            )
        else:
            assert "custom_fields" not in query


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fragment_store_image_fields_match_capabilities(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """FIND_IMAGE_QUERY contains custom_fields iff the server supports it."""
    async with stash_cleanup_tracker(stash_client):
        caps = stash_client._capabilities
        assert caps is not None

        query = str(fragment_store.FIND_IMAGE_QUERY)
        if caps.has_image_custom_fields:
            assert "custom_fields" in query, (
                f"Server appSchema={caps.app_schema} >= 83 but FIND_IMAGE_QUERY "
                f"is missing custom_fields"
            )
        else:
            assert "custom_fields" not in query


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fragment_store_group_fields_match_capabilities(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """FIND_GROUP_QUERY contains custom_fields iff the server supports it."""
    async with stash_cleanup_tracker(stash_client):
        caps = stash_client._capabilities
        assert caps is not None

        query = str(fragment_store.FIND_GROUP_QUERY)
        if caps.has_group_custom_fields:
            assert "custom_fields" in query, (
                f"Server appSchema={caps.app_schema} >= 82 but FIND_GROUP_QUERY "
                f"is missing custom_fields"
            )
        else:
            assert "custom_fields" not in query


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fragment_store_folder_fields_match_capabilities(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """FIND_FOLDER_QUERY contains basename/parent_folders iff the server supports it."""
    async with stash_cleanup_tracker(stash_client):
        caps = stash_client._capabilities
        assert caps is not None

        query = str(fragment_store.FIND_FOLDERS_QUERY)
        if caps.has_folder_basename:
            assert "basename" in query, (
                f"Server appSchema={caps.app_schema} >= 84 but FIND_FOLDERS_QUERY "
                f"is missing basename"
            )
            assert "parent_folders" in query, (
                f"Server appSchema={caps.app_schema} >= 84 but FIND_FOLDERS_QUERY "
                f"is missing parent_folders"
            )
        else:
            assert "basename" not in query
            assert "parent_folders" not in query


# =============================================================================
# Mutation fragment string spot-checks
# =============================================================================
# The query-string tests above verify FIND_X queries. These verify that
# CREATE / UPDATE mutations embed the same rebuilt fragment — i.e., the full
# rebuild covers mutations, not just queries.


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fragment_store_create_performer_mutation_matches_capabilities(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """CREATE_PERFORMER_MUTATION contains career_start/career_end iff the server supports it."""
    async with stash_cleanup_tracker(stash_client):
        caps = stash_client._capabilities
        assert caps is not None

        mutation = str(fragment_store.CREATE_PERFORMER_MUTATION)
        if caps.has_performer_career_start_end:
            assert "career_start" in mutation, (
                f"Server appSchema={caps.app_schema} >= 78 but CREATE_PERFORMER_MUTATION "
                f"is missing career_start"
            )
            assert "career_end" in mutation, (
                f"Server appSchema={caps.app_schema} >= 78 but CREATE_PERFORMER_MUTATION "
                f"is missing career_end"
            )
        else:
            assert "career_start" not in mutation
            assert "career_end" not in mutation


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fragment_store_update_performer_mutation_matches_capabilities(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """UPDATE_PERFORMER_MUTATION contains career_start/career_end iff the server supports it."""
    async with stash_cleanup_tracker(stash_client):
        caps = stash_client._capabilities
        assert caps is not None

        mutation = str(fragment_store.UPDATE_PERFORMER_MUTATION)
        if caps.has_performer_career_start_end:
            assert "career_start" in mutation, (
                f"Server appSchema={caps.app_schema} >= 78 but UPDATE_PERFORMER_MUTATION "
                f"is missing career_start"
            )
            assert "career_end" in mutation
        else:
            assert "career_start" not in mutation
            assert "career_end" not in mutation


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fragment_store_create_studio_mutation_matches_capabilities(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """CREATE_STUDIO_MUTATION contains custom_fields/organized based on server capabilities."""
    async with stash_cleanup_tracker(stash_client):
        caps = stash_client._capabilities
        assert caps is not None

        mutation = str(fragment_store.CREATE_STUDIO_MUTATION)
        if caps.has_studio_custom_fields:
            assert "custom_fields" in mutation, (
                f"Server appSchema={caps.app_schema} >= 76 but CREATE_STUDIO_MUTATION "
                f"is missing custom_fields"
            )
        else:
            assert "custom_fields" not in mutation

        if caps.has_studio_organized:
            assert "organized" in mutation, (
                f"Server appSchema={caps.app_schema} >= 80 but CREATE_STUDIO_MUTATION "
                f"is missing organized"
            )
        else:
            assert "organized" not in mutation


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fragment_store_create_tag_mutation_matches_capabilities(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """CREATE_TAG_MUTATION contains custom_fields iff the server supports it."""
    async with stash_cleanup_tracker(stash_client):
        caps = stash_client._capabilities
        assert caps is not None

        mutation = str(fragment_store.CREATE_TAG_MUTATION)
        if caps.has_tag_custom_fields:
            assert "custom_fields" in mutation, (
                f"Server appSchema={caps.app_schema} >= 77 but CREATE_TAG_MUTATION "
                f"is missing custom_fields"
            )
        else:
            assert "custom_fields" not in mutation


# =============================================================================
# End-to-end gated field propagation tests
# =============================================================================
# These tests close the loop between capability detection and actual server
# responses. They verify the full pipeline:
#
#   ServerCapabilities → FragmentStore.rebuild() → GraphQL query string
#   → HTTP request → server response → Pydantic deserialization
#
# A field is "present" when it's non-UNSET (the value may be None — that is a
# valid server-returned null — but it must not be UNSET, which would mean the
# field was never requested / never deserialized).
#
# Tests are bidirectional: when the capability IS supported, fields must be
# non-UNSET; when it is NOT supported, fields must remain UNSET.


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="capabilities_e2e")
async def test_performer_career_fields_propagate_from_server(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """career_start/career_end are non-UNSET iff appSchema >= 78.

    Creates a real performer and verifies the response from both the
    CREATE mutation and a subsequent FIND query. Both embed the same
    PerformerFields fragment; if rebuild() injected the fields correctly,
    the server returns them and Pydantic deserializes them as non-UNSET
    (None for a newly-created performer with no career dates set).
    """
    caps = stash_client._capabilities
    assert caps is not None

    async with stash_cleanup_tracker(stash_client) as cleanup:
        performer = await stash_client.create_performer(
            Performer(name="SGC Caps E2E Performer")
        )
        cleanup["performers"].append(performer.id)
        assert performer.id is not None

        found = await stash_client.find_performer(performer.id)
        assert found is not None

        if caps.has_performer_career_start_end:
            # Both the CREATE response and the FIND response must have the field set.
            assert is_set(performer.career_start), (
                f"CREATE response: career_start should be non-UNSET when "
                f"appSchema={caps.app_schema} >= 78"
            )
            assert is_set(performer.career_end), (
                f"CREATE response: career_end should be non-UNSET when "
                f"appSchema={caps.app_schema} >= 78"
            )
            assert is_set(found.career_start), (
                f"FIND response: career_start should be non-UNSET when "
                f"appSchema={caps.app_schema} >= 78"
            )
            assert is_set(found.career_end), (
                f"FIND response: career_end should be non-UNSET when "
                f"appSchema={caps.app_schema} >= 78"
            )
        else:
            # Fields were not in the fragment; Pydantic must leave them UNSET.
            assert performer.career_start is UNSET, (
                f"career_start should remain UNSET when appSchema={caps.app_schema} < 78"
            )
            assert performer.career_end is UNSET, (
                f"career_end should remain UNSET when appSchema={caps.app_schema} < 78"
            )
            assert found.career_start is UNSET
            assert found.career_end is UNSET


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="capabilities_e2e")
async def test_studio_organized_field_propagates_from_server(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """organized is non-UNSET iff appSchema >= 80.

    Creates a real studio and checks both the CREATE and FIND responses.
    New studios always have organized=False, so when the field is supported
    it must deserialize as exactly False (not UNSET, not None).
    """
    caps = stash_client._capabilities
    assert caps is not None

    async with stash_cleanup_tracker(stash_client) as cleanup:
        studio = await stash_client.create_studio(
            Studio(name="SGC Caps E2E Studio Organized")
        )
        cleanup["studios"].append(studio.id)
        assert studio.id is not None

        found = await stash_client.find_studio(studio.id)
        assert found is not None

        if caps.has_studio_organized:
            assert is_set(studio.organized), (
                f"CREATE response: organized should be non-UNSET when "
                f"appSchema={caps.app_schema} >= 80"
            )
            assert is_set(found.organized), (
                f"FIND response: organized should be non-UNSET when "
                f"appSchema={caps.app_schema} >= 80"
            )
            # New studios are always unorganized
            assert found.organized is False
        else:
            assert studio.organized is UNSET, (
                f"organized should remain UNSET when appSchema={caps.app_schema} < 80"
            )
            assert found.organized is UNSET


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="capabilities_e2e")
async def test_studio_custom_fields_propagate_from_server(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """custom_fields on Studio is non-UNSET iff appSchema >= 76.

    New studios return custom_fields as an empty dict {}, not None or UNSET.
    """
    caps = stash_client._capabilities
    assert caps is not None

    async with stash_cleanup_tracker(stash_client) as cleanup:
        studio = await stash_client.create_studio(
            Studio(name="SGC Caps E2E Studio Custom Fields")
        )
        cleanup["studios"].append(studio.id)
        assert studio.id is not None

        found = await stash_client.find_studio(studio.id)
        assert found is not None

        if caps.has_studio_custom_fields:
            assert is_set(studio.custom_fields), (
                f"CREATE response: custom_fields should be non-UNSET when "
                f"appSchema={caps.app_schema} >= 76"
            )
            assert is_set(found.custom_fields), (
                f"FIND response: custom_fields should be non-UNSET when "
                f"appSchema={caps.app_schema} >= 76"
            )
        else:
            assert studio.custom_fields is UNSET, (
                f"custom_fields should remain UNSET when appSchema={caps.app_schema} < 76"
            )
            assert found.custom_fields is UNSET


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="capabilities_e2e")
async def test_tag_custom_fields_propagate_from_server(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """custom_fields on Tag is non-UNSET iff appSchema >= 77."""
    caps = stash_client._capabilities
    assert caps is not None

    async with stash_cleanup_tracker(stash_client) as cleanup:
        tag = await stash_client.create_tag(Tag(name="sgc-caps-e2e-tag-custom-fields"))
        cleanup["tags"].append(tag.id)
        assert tag.id is not None

        found = await stash_client.find_tag(tag.id)
        assert found is not None

        if caps.has_tag_custom_fields:
            assert is_set(tag.custom_fields), (
                f"CREATE response: custom_fields should be non-UNSET when "
                f"appSchema={caps.app_schema} >= 77"
            )
            assert is_set(found.custom_fields), (
                f"FIND response: custom_fields should be non-UNSET when "
                f"appSchema={caps.app_schema} >= 77"
            )
        else:
            assert tag.custom_fields is UNSET, (
                f"custom_fields should remain UNSET when appSchema={caps.app_schema} < 77"
            )
            assert found.custom_fields is UNSET


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="capabilities_e2e")
async def test_group_custom_fields_propagate_from_server(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """custom_fields on Group is non-UNSET iff appSchema >= 82.

    Group uses the named-fragment injection path (_inject_named_fragment_fields),
    which is a different code path than the inline-fragment entities above.
    This verifies that path works end-to-end too.
    """
    caps = stash_client._capabilities
    assert caps is not None

    async with stash_cleanup_tracker(stash_client) as cleanup:
        group = await stash_client.create_group(
            Group(name="SGC Caps E2E Group Custom Fields")
        )
        cleanup["groups"].append(group.id)
        assert group.id is not None

        found = await stash_client.find_group(group.id)
        assert found is not None

        if caps.has_group_custom_fields:
            assert is_set(group.custom_fields), (
                f"CREATE response: custom_fields should be non-UNSET when "
                f"appSchema={caps.app_schema} >= 82"
            )
            assert is_set(found.custom_fields), (
                f"FIND response: custom_fields should be non-UNSET when "
                f"appSchema={caps.app_schema} >= 82"
            )
        else:
            assert group.custom_fields is UNSET, (
                f"custom_fields should remain UNSET when appSchema={caps.app_schema} < 82"
            )
            assert found.custom_fields is UNSET


@pytest.mark.integration
@pytest.mark.asyncio
async def test_folder_basename_propagates_from_server(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """basename/parent_folders on Folder are non-UNSET iff appSchema >= 84.

    Folders can't be created via the API, so this test queries existing folders.
    It skips when no folders are present in the test instance.

    Folder also uses the named-fragment injection path, making this test
    complementary to test_group_custom_fields_propagate_from_server.
    """
    caps = stash_client._capabilities
    assert caps is not None

    async with stash_cleanup_tracker(stash_client, auto_capture=False):
        result = await stash_client.find_folders(filter_={"per_page": 1})
        if result.count == 0:
            pytest.skip(
                "No folders in test Stash instance — cannot verify field propagation"
            )

        folder = result.folders[0]

        if caps.has_folder_basename:
            assert is_set(folder.basename), (
                f"basename should be non-UNSET when appSchema={caps.app_schema} >= 84"
            )
            assert is_set(folder.parent_folders), (
                f"parent_folders should be non-UNSET when appSchema={caps.app_schema} >= 84"
            )
        else:
            assert folder.basename is UNSET, (
                f"basename should remain UNSET when appSchema={caps.app_schema} < 84"
            )
            assert folder.parent_folders is UNSET, (
                f"parent_folders should remain UNSET when appSchema={caps.app_schema} < 84"
            )


# =============================================================================
# Capability flag monotonicity
# =============================================================================
# appSchema is cumulative: schema N includes all features from 1..N-1.
# If a high-schema feature is present, all lower-schema features must also be
# present. This guards against a regression where the thresholds are mis-ordered.


@pytest.mark.integration
@pytest.mark.asyncio
async def test_capabilities_flags_are_monotonic(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Higher appSchema features imply all lower-schema features are also present.

    The appSchema thresholds form a chain: 76 < 77 < 78 < 79 < 80 < 81 < 82 < 83 < 84.
    If the server has feature N, it must also have all features < N.
    """
    async with stash_cleanup_tracker(stash_client):
        caps = stash_client._capabilities
        assert caps is not None

        # Ordered chain: (flag, threshold) from lowest to highest
        chain = [
            ("has_studio_custom_fields", 76),
            ("has_tag_custom_fields", 77),
            ("has_performer_career_start_end", 78),
            ("has_scene_custom_fields", 79),
            ("has_studio_organized", 80),
            ("has_gallery_custom_fields", 81),
            ("has_group_custom_fields", 82),
            ("has_image_custom_fields", 83),
            ("has_folder_basename", 84),
        ]

        for i, (flag, threshold) in enumerate(chain):
            if getattr(caps, flag):
                # All lower-threshold flags must also be True
                for lower_flag, lower_threshold in chain[:i]:
                    assert getattr(caps, lower_flag), (
                        f"{flag} (appSchema >= {threshold}) is True but "
                        f"{lower_flag} (appSchema >= {lower_threshold}) is False — "
                        f"appSchema monotonicity violated (server appSchema={caps.app_schema})"
                    )
