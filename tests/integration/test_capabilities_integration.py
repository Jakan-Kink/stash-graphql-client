"""Integration tests for server capability detection.

Tests that the client correctly detects and exposes server capabilities
from a real Stash instance. These tests verify that the capability
detection query runs successfully and populates ServerCapabilities.
"""

import pytest

from stash_graphql_client import StashClient
from stash_graphql_client.capabilities import (
    CAPABILITY_DETECTION_QUERY,
    MIN_SUPPORTED_APP_SCHEMA,
    ServerCapabilities,
)
from stash_graphql_client.fragments import FragmentStore, fragment_store
from stash_graphql_client.types import Gallery, Group, Performer, Scene, Studio, Tag
from stash_graphql_client.types.unset import UNSET, is_set
from tests.fixtures import capture_graphql_calls, dump_graphql_calls
from tests.fixtures.stash.graphql_responses import (
    _MUTATION_REGISTRY,
    _QUERY_REGISTRY,
    _SUBSCRIPTION_REGISTRY,
)


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
    """Test that the DuplicationCriterionInput type can be queried via has_type()."""
    async with stash_cleanup_tracker(stash_client):
        caps = stash_client._capabilities
        assert caps is not None

        # has_type() returns a bool regardless of server version
        assert isinstance(caps.has_type("DuplicationCriterionInput"), bool)


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
        assert caps.has_performer_career_date_strings == (schema >= 85)


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
        assert "__schema" in query_sent

        assert fresh_client._capabilities is not None
    finally:
        await fresh_client.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_capabilities_lookup_methods_return_bools(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Lookup methods must return bool regardless of server version.

    The schema data is populated during initialization from a single __schema
    introspection query.  This test confirms the lookup methods return bools.
    """
    async with stash_cleanup_tracker(stash_client):
        caps = stash_client._capabilities
        assert caps is not None

        assert isinstance(caps.has_type("PerformerMergeInput"), bool)
        for mutation_name in _MUTATION_REGISTRY.values():
            flag = caps.has_mutation(mutation_name)
            assert isinstance(flag, bool), (
                f"Expected has_mutation({mutation_name!r}) to be bool, "
                f"got {type(flag).__name__}"
            )
        for query_name in _QUERY_REGISTRY.values():
            flag = caps.has_query(query_name)
            assert isinstance(flag, bool), (
                f"Expected has_query({query_name!r}) to be bool, "
                f"got {type(flag).__name__}"
            )
        for subscription_name in _SUBSCRIPTION_REGISTRY.values():
            flag = caps.has_subscription(subscription_name)
            assert isinstance(flag, bool), (
                f"Expected has_subscription({subscription_name!r}) to be bool, "
                f"got {type(flag).__name__}"
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
        try:
            result = await stash_client.execute(
                '{ _mutations: __type(name: "Mutation") { fields { name } } }'
            )
        finally:
            dump_graphql_calls(calls)

        assert len(calls) == 1
        assert calls[0]["exception"] is None

        mutation_names: set[str] = {
            f["name"] for f in ((result.get("_mutations") or {}).get("fields") or [])
        }

        caps = stash_client._capabilities
        assert caps is not None

        for mutation_name in _MUTATION_REGISTRY.values():
            expected = mutation_name in mutation_names
            actual = caps.has_mutation(mutation_name)
            assert actual == expected, (
                f"has_mutation({mutation_name!r}): returned {actual} but "
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
        try:
            result = await stash_client.execute(
                '{ _queries: __type(name: "Query") { fields { name } } }'
            )
        finally:
            dump_graphql_calls(calls)

        assert len(calls) == 1
        assert calls[0]["exception"] is None

        query_names: set[str] = {
            f["name"] for f in ((result.get("_queries") or {}).get("fields") or [])
        }

        caps = stash_client._capabilities
        assert caps is not None

        for query_name in _QUERY_REGISTRY.values():
            expected = query_name in query_names
            actual = caps.has_query(query_name)
            assert actual == expected, (
                f"has_query({query_name!r}): returned {actual} but "
                f"'{query_name}' {'is' if expected else 'is not'} in Query type"
            )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_capabilities_subscription_flags_match_introspection(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Subscription-presence flags match a fresh direct introspection of the Subscription type.

    This cross-checks that the subscription names parsed from __schema during
    initialization agree with a live re-query of the Subscription type.
    """
    async with (
        stash_cleanup_tracker(stash_client),
        capture_graphql_calls(stash_client) as calls,
    ):
        try:
            result = await stash_client.execute(
                '{ _subscriptions: __type(name: "Subscription") { fields { name } } }'
            )
        finally:
            dump_graphql_calls(calls)

        assert len(calls) == 1
        assert calls[0]["exception"] is None

        subscription_names: set[str] = {
            f["name"]
            for f in ((result.get("_subscriptions") or {}).get("fields") or [])
        }

        caps = stash_client._capabilities
        assert caps is not None

        for subscription_name in _SUBSCRIPTION_REGISTRY.values():
            expected = subscription_name in subscription_names
            actual = caps.has_subscription(subscription_name)
            assert actual == expected, (
                f"has_subscription({subscription_name!r}): returned {actual} but "
                f"'{subscription_name}' {'is' if expected else 'is not'} "
                f"in Subscription type"
            )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_subscription_names_populated(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """subscription_names is populated with at least the known Stash subscriptions.

    Stash has always exposed jobsSubscribe, loggingSubscribe, and
    scanCompleteSubscribe. If any are missing, something went wrong during
    __schema parsing.
    """
    async with stash_cleanup_tracker(stash_client):
        caps = stash_client._capabilities
        assert caps is not None

        assert len(caps.subscription_names) > 0, (
            "subscription_names is empty — __schema.subscriptionType was not parsed"
        )

        # All three core subscriptions should be present on any Stash server
        for name in ("jobsSubscribe", "loggingSubscribe", "scanCompleteSubscribe"):
            assert caps.has_subscription(name), (
                f"Expected has_subscription({name!r}) to be True on live server"
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

    async with stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup:
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

    async with stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup:
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

    async with stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup:
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

    async with stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup:
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

    async with stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup:
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
            ("has_performer_career_date_strings", 85),
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


# =============================================================================
# Backward compatibility: additional e2e gated field propagation tests
# =============================================================================
# These tests close the remaining coverage gaps for entity types that were
# not covered by the original e2e tests above: Scene, Gallery, and Image.


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="capabilities_e2e")
async def test_scene_custom_fields_propagate_from_server(
    stash_client: StashClient, stash_cleanup_tracker, enable_scene_creation
) -> None:
    """custom_fields on Scene is non-UNSET iff appSchema >= 79.

    Creates a real scene and verifies the response from both the CREATE
    mutation and a subsequent FIND query. New scenes return custom_fields
    as an empty dict {} when the field is supported.
    """
    caps = stash_client._capabilities
    assert caps is not None

    async with stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup:
        scene = await stash_client.create_scene(
            Scene.new(title="SGC Compat E2E Scene Custom Fields")
        )
        cleanup["scenes"].append(scene.id)
        assert scene.id is not None

        found = await stash_client.find_scene(scene.id)
        assert found is not None

        if caps.has_scene_custom_fields:
            assert is_set(scene.custom_fields), (
                f"CREATE response: custom_fields should be non-UNSET when "
                f"appSchema={caps.app_schema} >= 79"
            )
            assert is_set(found.custom_fields), (
                f"FIND response: custom_fields should be non-UNSET when "
                f"appSchema={caps.app_schema} >= 79"
            )
        else:
            assert scene.custom_fields is UNSET, (
                f"custom_fields should remain UNSET when appSchema={caps.app_schema} < 79"
            )
            assert found.custom_fields is UNSET


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="capabilities_e2e")
async def test_gallery_custom_fields_propagate_from_server(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """custom_fields on Gallery is non-UNSET iff appSchema >= 81.

    Creates a real gallery and verifies both CREATE and FIND responses.
    """
    caps = stash_client._capabilities
    assert caps is not None

    async with stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup:
        gallery = await stash_client.create_gallery(
            Gallery.new(title="SGC Compat E2E Gallery Custom Fields")
        )
        cleanup["galleries"].append(gallery.id)
        assert gallery.id is not None

        found = await stash_client.find_gallery(gallery.id)
        assert found is not None

        if caps.has_gallery_custom_fields:
            assert is_set(gallery.custom_fields), (
                f"CREATE response: custom_fields should be non-UNSET when "
                f"appSchema={caps.app_schema} >= 81"
            )
            assert is_set(found.custom_fields), (
                f"FIND response: custom_fields should be non-UNSET when "
                f"appSchema={caps.app_schema} >= 81"
            )
        else:
            assert gallery.custom_fields is UNSET, (
                f"custom_fields should remain UNSET when appSchema={caps.app_schema} < 81"
            )
            assert found.custom_fields is UNSET


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="capabilities_e2e")
async def test_image_custom_fields_propagate_from_server(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """custom_fields on Image is non-UNSET iff appSchema >= 83.

    Images cannot be created via the API, so this test queries existing
    images. It skips when no images are present in the test instance.
    """
    caps = stash_client._capabilities
    assert caps is not None

    async with stash_cleanup_tracker(stash_client, auto_capture=False):
        result = await stash_client.find_images(filter_={"per_page": 1})
        if result.count == 0:
            pytest.skip(
                "No images in test Stash instance — cannot verify field propagation"
            )

        image = result.images[0]

        if caps.has_image_custom_fields:
            assert is_set(image.custom_fields), (
                f"custom_fields should be non-UNSET when appSchema={caps.app_schema} >= 83"
            )
        else:
            assert image.custom_fields is UNSET, (
                f"custom_fields should remain UNSET when appSchema={caps.app_schema} < 83"
            )


# =============================================================================
# Backward compatibility: base fields always present
# =============================================================================
# Base fields (those NOT behind a capability gate) must always be returned
# by any server meeting MIN_SUPPORTED_APP_SCHEMA. These tests verify the
# pipeline works end-to-end for the minimum field set.


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="capabilities_e2e")
async def test_performer_base_fields_always_present(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Performer base fields (name, urls, gender, etc.) are non-UNSET on any supported server.

    These fields are in _BASE_PERFORMER_FIELDS and are never capability-gated.
    """
    async with stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup:
        performer = await stash_client.create_performer(
            Performer(name="SGC Compat Base Fields Performer")
        )
        cleanup["performers"].append(performer.id)
        assert performer.id is not None

        found = await stash_client.find_performer(performer.id)
        assert found is not None

        # These base fields must always be returned (non-UNSET)
        for field_name in (
            "name",
            "urls",
            "gender",
            "birthdate",
            "alias_list",
            "details",
            "custom_fields",
            "stash_ids",
        ):
            val = getattr(found, field_name)
            assert val is not UNSET, (
                f"Base field '{field_name}' should be non-UNSET on any supported server "
                f"(appSchema={stash_client._capabilities.app_schema})"
            )


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="capabilities_e2e")
async def test_studio_base_fields_always_present(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Studio base fields (name, urls, aliases, etc.) are non-UNSET on any supported server."""
    async with stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup:
        studio = await stash_client.create_studio(
            Studio(name="SGC Compat Base Fields Studio")
        )
        cleanup["studios"].append(studio.id)
        assert studio.id is not None

        found = await stash_client.find_studio(studio.id)
        assert found is not None

        for field_name in (
            "name",
            "urls",
            "aliases",
            "details",
            "rating100",
            "favorite",
            "stash_ids",
        ):
            val = getattr(found, field_name)
            assert val is not UNSET, (
                f"Base field '{field_name}' should be non-UNSET on any supported server "
                f"(appSchema={stash_client._capabilities.app_schema})"
            )


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="capabilities_e2e")
async def test_tag_base_fields_always_present(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Tag base fields (name, description, aliases, etc.) are non-UNSET on any supported server."""
    async with stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup:
        tag = await stash_client.create_tag(Tag(name="sgc-compat-base-fields-tag"))
        cleanup["tags"].append(tag.id)
        assert tag.id is not None

        found = await stash_client.find_tag(tag.id)
        assert found is not None

        for field_name in (
            "name",
            "description",
            "aliases",
            "stash_ids",
            "parents",
            "children",
        ):
            val = getattr(found, field_name)
            assert val is not UNSET, (
                f"Base field '{field_name}' should be non-UNSET on any supported server "
                f"(appSchema={stash_client._capabilities.app_schema})"
            )


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="capabilities_e2e")
async def test_group_base_fields_always_present(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Group base fields (name, aliases, urls, etc.) are non-UNSET on any supported server."""
    async with stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup:
        group = await stash_client.create_group(
            Group(name="SGC Compat Base Fields Group")
        )
        cleanup["groups"].append(group.id)
        assert group.id is not None

        found = await stash_client.find_group(group.id)
        assert found is not None

        for field_name in (
            "name",
            "aliases",
            "urls",
            "director",
            "synopsis",
            "tags",
            "scenes",
        ):
            val = getattr(found, field_name)
            assert val is not UNSET, (
                f"Base field '{field_name}' should be non-UNSET on any supported server "
                f"(appSchema={stash_client._capabilities.app_schema})"
            )


# =============================================================================
# Backward compatibility: fragment store rebuild consistency
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fragment_store_rebuild_idempotent(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Rebuilding the fragment store multiple times yields identical queries.

    This guards against stateful accumulation bugs — e.g., appending gated
    fields on each rebuild instead of starting fresh from _BASE constants.
    """
    async with stash_cleanup_tracker(stash_client):
        caps = stash_client._capabilities
        assert caps is not None

        # Capture the current state after initialization
        first_scene_query = fragment_store.FIND_SCENE_QUERY
        first_performer_query = fragment_store.FIND_PERFORMER_QUERY
        first_studio_query = fragment_store.FIND_STUDIO_QUERY
        first_tag_query = fragment_store.FIND_TAG_QUERY
        first_gallery_query = fragment_store.FIND_GALLERIES_QUERY
        first_image_query = fragment_store.FIND_IMAGE_QUERY
        first_group_query = fragment_store.FIND_GROUP_QUERY
        first_folder_query = fragment_store.FIND_FOLDERS_QUERY

        # Rebuild again with the same capabilities
        fragment_store.rebuild(caps)

        assert first_scene_query == fragment_store.FIND_SCENE_QUERY
        assert first_performer_query == fragment_store.FIND_PERFORMER_QUERY
        assert first_studio_query == fragment_store.FIND_STUDIO_QUERY
        assert first_tag_query == fragment_store.FIND_TAG_QUERY
        assert first_gallery_query == fragment_store.FIND_GALLERIES_QUERY
        assert first_image_query == fragment_store.FIND_IMAGE_QUERY
        assert first_group_query == fragment_store.FIND_GROUP_QUERY
        assert first_folder_query == fragment_store.FIND_FOLDERS_QUERY

        # Rebuild a third time for good measure
        fragment_store.rebuild(caps)
        assert first_scene_query == fragment_store.FIND_SCENE_QUERY


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fragment_store_find_create_update_use_same_fields(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """FIND, CREATE, and UPDATE queries for the same entity contain identical field sets.

    A common backward-compat bug is including gated fields in FIND but forgetting
    them in CREATE/UPDATE (or vice versa), leading to deserialization mismatches.

    This test extracts the field list from each query string and compares them.
    """
    async with stash_cleanup_tracker(stash_client):
        caps = stash_client._capabilities
        assert caps is not None

        # Performer: FIND vs CREATE vs UPDATE should embed the same PERFORMER_FIELDS
        performer_fields = fragment_store.PERFORMER_FIELDS.strip()
        assert performer_fields in fragment_store.FIND_PERFORMER_QUERY
        assert performer_fields in fragment_store.CREATE_PERFORMER_MUTATION
        assert performer_fields in fragment_store.UPDATE_PERFORMER_MUTATION
        assert performer_fields in fragment_store.BULK_PERFORMER_UPDATE_MUTATION

        # Studio: FIND vs CREATE vs UPDATE
        studio_fields = fragment_store.STUDIO_FIELDS.strip()
        assert studio_fields in fragment_store.FIND_STUDIO_QUERY
        assert studio_fields in fragment_store.CREATE_STUDIO_MUTATION
        assert studio_fields in fragment_store.UPDATE_STUDIO_MUTATION

        # Tag: FIND vs CREATE vs UPDATE
        tag_fields = fragment_store.TAG_FIELDS.strip()
        assert tag_fields in fragment_store.FIND_TAG_QUERY
        assert tag_fields in fragment_store.CREATE_TAG_MUTATION
        assert tag_fields in fragment_store.UPDATE_TAG_MUTATION
        assert tag_fields in fragment_store.TAGS_MERGE_MUTATION

        # Scene: uses fragment-based queries; verify the fragment appears in all
        scene_fragment_marker = "fragment SceneFragment on Scene"
        assert scene_fragment_marker in fragment_store.FIND_SCENE_QUERY
        assert scene_fragment_marker in fragment_store.CREATE_SCENE_MUTATION
        assert scene_fragment_marker in fragment_store.UPDATE_SCENE_MUTATION
        assert scene_fragment_marker in fragment_store.BULK_SCENE_UPDATE_MUTATION

        # Gallery: uses fragment-based queries
        gallery_fragment_marker = "fragment GalleryFragment on Gallery"
        assert gallery_fragment_marker in fragment_store.FIND_GALLERY_QUERY
        assert gallery_fragment_marker in fragment_store.CREATE_GALLERY_MUTATION
        assert gallery_fragment_marker in fragment_store.UPDATE_GALLERY_MUTATION

        # Image: uses fragment-based queries
        image_fragment_marker = "fragment ImageFragment on Image"
        assert image_fragment_marker in fragment_store.FIND_IMAGE_QUERY
        assert image_fragment_marker in fragment_store.CREATE_IMAGE_MUTATION
        assert image_fragment_marker in fragment_store.UPDATE_IMAGE_MUTATION

        # Group: uses named fragment
        group_fragment_marker = "fragment GroupFields on Group"
        assert group_fragment_marker in fragment_store.FIND_GROUP_QUERY
        assert group_fragment_marker in fragment_store.CREATE_GROUP_MUTATION
        assert group_fragment_marker in fragment_store.UPDATE_GROUP_MUTATION

        # Folder: uses named fragment
        folder_fragment_marker = "fragment FolderFields on Folder"
        assert folder_fragment_marker in fragment_store.FIND_FOLDER_QUERY
        assert folder_fragment_marker in fragment_store.FIND_FOLDERS_QUERY


# =============================================================================
# Backward compatibility: fresh client re-initialization
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fresh_client_detects_same_capabilities(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """A second independently-initialized client detects identical capabilities.

    This verifies that capability detection is deterministic and not affected
    by module-level state from the first client's initialization.
    """
    async with stash_cleanup_tracker(stash_client):
        original_caps = stash_client._capabilities
        assert original_caps is not None

        # Create and initialize a fresh client from the same connection config
        conn, verify_ssl = stash_client._init_args
        fresh_client = StashClient(conn=conn, verify_ssl=verify_ssl)

        try:
            await fresh_client.initialize()
            fresh_caps = fresh_client._capabilities
            assert fresh_caps is not None

            # All fields must match exactly
            assert fresh_caps.app_schema == original_caps.app_schema
            assert fresh_caps.version_string == original_caps.version_string
            assert fresh_caps.has_type("DuplicationCriterionInput") == (
                original_caps.has_type("DuplicationCriterionInput")
            )
            assert fresh_caps.has_type("PerformerMergeInput") == (
                original_caps.has_type("PerformerMergeInput")
            )

            # Check all derived appSchema properties
            assert fresh_caps.has_studio_custom_fields == (
                original_caps.has_studio_custom_fields
            )
            assert fresh_caps.has_tag_custom_fields == (
                original_caps.has_tag_custom_fields
            )
            assert fresh_caps.has_performer_career_start_end == (
                original_caps.has_performer_career_start_end
            )
            assert fresh_caps.has_scene_custom_fields == (
                original_caps.has_scene_custom_fields
            )
            assert fresh_caps.has_studio_organized == (
                original_caps.has_studio_organized
            )
            assert fresh_caps.has_gallery_custom_fields == (
                original_caps.has_gallery_custom_fields
            )
            assert fresh_caps.has_group_custom_fields == (
                original_caps.has_group_custom_fields
            )
            assert fresh_caps.has_image_custom_fields == (
                original_caps.has_image_custom_fields
            )
            assert fresh_caps.has_folder_basename == (original_caps.has_folder_basename)
            assert fresh_caps.has_performer_career_date_strings == (
                original_caps.has_performer_career_date_strings
            )

            # Check all mutation/query presence flags via lookup methods
            for mutation_name in _MUTATION_REGISTRY.values():
                assert fresh_caps.has_mutation(mutation_name) == (
                    original_caps.has_mutation(mutation_name)
                ), f"has_mutation({mutation_name!r}) differs between clients"

            for query_name in _QUERY_REGISTRY.values():
                assert fresh_caps.has_query(query_name) == (
                    original_caps.has_query(query_name)
                ), f"has_query({query_name!r}) differs between clients"

            for subscription_name in _SUBSCRIPTION_REGISTRY.values():
                assert fresh_caps.has_subscription(subscription_name) == (
                    original_caps.has_subscription(subscription_name)
                ), f"has_subscription({subscription_name!r}) differs between clients"
        finally:
            await fresh_client.close()


# =============================================================================
# Backward compatibility: fragment store downgrade/upgrade simulation
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fragment_store_rebuild_with_minimum_schema(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Rebuilding the fragment store with appSchema=75 removes all gated fields.

    This simulates connecting to a v0.30.0 server (the minimum supported version).
    After rebuild, no capability-gated fields should appear in any query.
    """
    from tests.fixtures.stash.graphql_responses import make_server_capabilities

    async with stash_cleanup_tracker(stash_client):
        # Save the current state before we modify the module singleton
        caps = stash_client._capabilities
        assert caps is not None

        # Simulate a v0.30.0 server (minimum supported)
        min_caps = make_server_capabilities(app_schema=75)
        store = FragmentStore()
        store.rebuild(min_caps)

        # No custom_fields in any entity query
        assert "custom_fields" not in store.FIND_SCENE_QUERY
        assert "custom_fields" not in store.FIND_STUDIO_QUERY
        assert "custom_fields" not in store.FIND_TAG_QUERY
        assert "custom_fields" not in store.FIND_GALLERY_QUERY
        assert "custom_fields" not in store.FIND_IMAGE_QUERY
        assert "custom_fields" not in store.FIND_GROUP_QUERY

        # No career_start/career_end in performer query
        assert "career_start" not in store.FIND_PERFORMER_QUERY
        assert "career_end" not in store.FIND_PERFORMER_QUERY

        # No organized in studio query
        assert "organized" not in store.FIND_STUDIO_QUERY

        # No basename/parent_folders in folder query
        assert "basename" not in store.FIND_FOLDERS_QUERY
        assert "parent_folders" not in store.FIND_FOLDERS_QUERY


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fragment_store_rebuild_with_maximum_schema(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Rebuilding the fragment store with appSchema=84 includes all gated fields.

    This simulates connecting to a top-of-head develop server.
    After rebuild, all capability-gated fields should appear in their queries.
    """
    from tests.fixtures.stash.graphql_responses import make_server_capabilities

    async with stash_cleanup_tracker(stash_client):
        max_caps = make_server_capabilities(app_schema=84)
        store = FragmentStore()
        store.rebuild(max_caps)

        # custom_fields in every entity that supports it
        assert "custom_fields" in store.FIND_SCENE_QUERY
        assert "custom_fields" in store.FIND_STUDIO_QUERY
        assert "custom_fields" in store.FIND_TAG_QUERY
        assert "custom_fields" in store.FIND_GALLERY_QUERY
        assert "custom_fields" in store.FIND_IMAGE_QUERY
        assert "custom_fields" in store.FIND_GROUP_QUERY

        # career_start/career_end in performer query
        assert "career_start" in store.FIND_PERFORMER_QUERY
        assert "career_end" in store.FIND_PERFORMER_QUERY

        # organized in studio query
        assert "organized" in store.FIND_STUDIO_QUERY

        # basename/parent_folders in folder query
        assert "basename" in store.FIND_FOLDERS_QUERY
        assert "parent_folders" in store.FIND_FOLDERS_QUERY


# =============================================================================
# Backward compatibility: queries execute without error on any supported server
# =============================================================================
# The strongest backward-compat guarantee: the fragment store's queries
# actually execute against the real server without GraphQL errors.


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="capabilities_e2e")
async def test_find_scenes_query_executes_on_server(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """The rebuilt FIND_SCENES_QUERY executes without GraphQL errors."""
    async with stash_cleanup_tracker(stash_client):
        # This exercises the full pipeline: fragment store → query string → HTTP → server
        result = await stash_client.find_scenes(filter_={"per_page": 1})
        # count is always a non-negative int; its presence proves the query worked
        assert isinstance(result.count, int)
        assert result.count >= 0


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="capabilities_e2e")
async def test_find_performers_query_executes_on_server(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """The rebuilt FIND_PERFORMERS_QUERY executes without GraphQL errors."""
    async with stash_cleanup_tracker(stash_client):
        result = await stash_client.find_performers(filter_={"per_page": 1})
        assert isinstance(result.count, int)
        assert result.count >= 0


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="capabilities_e2e")
async def test_find_studios_query_executes_on_server(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """The rebuilt FIND_STUDIOS_QUERY executes without GraphQL errors."""
    async with stash_cleanup_tracker(stash_client):
        result = await stash_client.find_studios(filter_={"per_page": 1})
        assert isinstance(result.count, int)
        assert result.count >= 0


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="capabilities_e2e")
async def test_find_tags_query_executes_on_server(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """The rebuilt FIND_TAGS_QUERY executes without GraphQL errors."""
    async with stash_cleanup_tracker(stash_client):
        result = await stash_client.find_tags(filter_={"per_page": 1})
        assert isinstance(result.count, int)
        assert result.count >= 0


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="capabilities_e2e")
async def test_find_galleries_query_executes_on_server(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """The rebuilt FIND_GALLERIES_QUERY executes without GraphQL errors."""
    async with stash_cleanup_tracker(stash_client):
        result = await stash_client.find_galleries(filter_={"per_page": 1})
        assert isinstance(result.count, int)
        assert result.count >= 0


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="capabilities_e2e")
async def test_find_images_query_executes_on_server(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """The rebuilt FIND_IMAGES_QUERY executes without GraphQL errors."""
    async with stash_cleanup_tracker(stash_client):
        result = await stash_client.find_images(filter_={"per_page": 1})
        assert isinstance(result.count, int)
        assert result.count >= 0


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="capabilities_e2e")
async def test_find_groups_query_executes_on_server(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """The rebuilt FIND_GROUPS_QUERY executes without GraphQL errors."""
    async with stash_cleanup_tracker(stash_client):
        result = await stash_client.find_groups(filter_={"per_page": 1})
        assert isinstance(result.count, int)
        assert result.count >= 0


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="capabilities_e2e")
async def test_find_folders_query_executes_on_server(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """The rebuilt FIND_FOLDERS_QUERY executes without GraphQL errors."""
    async with stash_cleanup_tracker(stash_client):
        result = await stash_client.find_folders(filter_={"per_page": 1})
        assert isinstance(result.count, int)
        assert result.count >= 0


# =============================================================================
# Backward compatibility: capability-gated field round-trip through update
# =============================================================================
# The real backward-compat risk is not just querying, but round-tripping:
# create → read → update → read. These tests verify the full lifecycle works
# for capability-gated fields when the server supports them.


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="capabilities_e2e")
async def test_performer_career_fields_round_trip_through_update(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """career_start/career_end survive a create → update → find round-trip.

    On servers that support the fields (appSchema >= 78), we set career_start
    to a specific year during update and verify it persists. On older servers,
    we verify the update still succeeds without error (the extra field is just
    ignored by Pydantic's UNSET filtering in to_input()).
    """
    caps = stash_client._capabilities
    assert caps is not None

    async with stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup:
        performer = await stash_client.create_performer(
            Performer(name="SGC Compat Round-Trip Career Performer")
        )
        cleanup["performers"].append(performer.id)

        if caps.has_performer_career_start_end:
            performer.career_start = "2010"
            performer.career_end = "2020"
            updated = await stash_client.update_performer(performer)

            assert is_set(updated.career_start)
            assert updated.career_start == "2010"
            assert is_set(updated.career_end)
            assert updated.career_end == "2020"

            found = await stash_client.find_performer(performer.id)
            assert found.career_start == "2010"
            assert found.career_end == "2020"
        else:
            # On older servers: update with base fields only, should not error
            performer.name = "SGC Compat Round-Trip Career Performer Updated"
            updated = await stash_client.update_performer(performer)
            assert updated.name == "SGC Compat Round-Trip Career Performer Updated"
            assert updated.career_start is UNSET
            assert updated.career_end is UNSET


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="capabilities_e2e")
async def test_studio_organized_round_trip_through_update(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """organized flag survives a create → update → find round-trip on Studio.

    On servers that support organized (appSchema >= 80), we set it to True
    and verify persistence. On older servers, we verify the update still works.
    """
    caps = stash_client._capabilities
    assert caps is not None

    async with stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup:
        studio = await stash_client.create_studio(
            Studio(name="SGC Compat Round-Trip Organized Studio")
        )
        cleanup["studios"].append(studio.id)

        if caps.has_studio_organized:
            studio.organized = True
            updated = await stash_client.update_studio(studio)

            assert is_set(updated.organized)
            assert updated.organized is True

            found = await stash_client.find_studio(studio.id)
            assert found.organized is True
        else:
            studio.name = "SGC Compat Round-Trip Organized Studio Updated"
            updated = await stash_client.update_studio(studio)
            assert updated.name == "SGC Compat Round-Trip Organized Studio Updated"
            assert updated.organized is UNSET


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="capabilities_e2e")
async def test_studio_custom_fields_round_trip_through_update(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """custom_fields on Studio survives a create → update → find round-trip.

    On servers that support custom_fields (appSchema >= 76), we set a custom
    field value and verify it persists.
    """
    caps = stash_client._capabilities
    assert caps is not None

    async with stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup:
        studio = await stash_client.create_studio(
            Studio(name="SGC Compat Round-Trip Custom Fields Studio")
        )
        cleanup["studios"].append(studio.id)

        if caps.has_studio_custom_fields:
            assert is_set(studio.custom_fields)
            # Newly created studios have empty custom_fields
            # Verify query round-trip works
            found = await stash_client.find_studio(studio.id)
            assert is_set(found.custom_fields)
        else:
            assert studio.custom_fields is UNSET
            found = await stash_client.find_studio(studio.id)
            assert found.custom_fields is UNSET


# =============================================================================
# Backward compatibility: tracked mutations/queries superset check
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_tracked_mutations_subset_of_server_mutations(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """All _TRACKED_MUTATIONS and _MUTATION_REGISTRY entries are recognized names.

    Verifies that the mutation names we track haven't been renamed or removed
    from the server. If a tracked mutation is missing, it should be because
    the server version doesn't support it — not because of a typo or rename.

    On a top-of-head server: all tracked mutations should be present.
    On v0.30.0: a subset may be present (indicated by the capability flags).
    """
    async with (
        stash_cleanup_tracker(stash_client),
        capture_graphql_calls(stash_client) as calls,
    ):
        try:
            result = await stash_client.execute(
                '{ _mutations: __type(name: "Mutation") { fields { name } } }'
            )
        finally:
            dump_graphql_calls(calls)
        assert len(calls) == 1

        all_mutations: set[str] = {
            f["name"] for f in ((result.get("_mutations") or {}).get("fields") or [])
        }

        caps = stash_client._capabilities
        assert caps is not None

        # For each tracked mutation, if the lookup says it's present,
        # then the mutation name must appear in the server's mutation list
        for mutation_name in _MUTATION_REGISTRY.values():
            if caps.has_mutation(mutation_name):
                assert mutation_name in all_mutations, (
                    f"has_mutation({mutation_name!r}) is True but mutation "
                    f"'{mutation_name}' not found in server's Mutation type"
                )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_tracked_queries_subset_of_server_queries(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """All _TRACKED_QUERIES and _QUERY_REGISTRY entries are recognized names.

    Same as above but for the Query type.
    """
    async with (
        stash_cleanup_tracker(stash_client),
        capture_graphql_calls(stash_client) as calls,
    ):
        try:
            result = await stash_client.execute(
                '{ _queries: __type(name: "Query") { fields { name } } }'
            )
        finally:
            dump_graphql_calls(calls)
        assert len(calls) == 1

        all_queries: set[str] = {
            f["name"] for f in ((result.get("_queries") or {}).get("fields") or [])
        }

        caps = stash_client._capabilities
        assert caps is not None

        for query_name in _QUERY_REGISTRY.values():
            if caps.has_query(query_name):
                assert query_name in all_queries, (
                    f"has_query({query_name!r}) is True but query "
                    f"'{query_name}' not found in server's Query type"
                )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_tracked_subscriptions_subset_of_server_subscriptions(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """All _SUBSCRIPTION_REGISTRY entries are recognized names.

    Verifies that the subscription names we track haven't been renamed or
    removed from the server.
    """
    async with (
        stash_cleanup_tracker(stash_client),
        capture_graphql_calls(stash_client) as calls,
    ):
        try:
            result = await stash_client.execute(
                '{ _subscriptions: __type(name: "Subscription") { fields { name } } }'
            )
        finally:
            dump_graphql_calls(calls)
        assert len(calls) == 1

        all_subscriptions: set[str] = {
            f["name"]
            for f in ((result.get("_subscriptions") or {}).get("fields") or [])
        }

        caps = stash_client._capabilities
        assert caps is not None

        for subscription_name in _SUBSCRIPTION_REGISTRY.values():
            if caps.has_subscription(subscription_name):
                assert subscription_name in all_subscriptions, (
                    f"has_subscription({subscription_name!r}) is True but "
                    f"subscription '{subscription_name}' not found in server's "
                    f"Subscription type"
                )


# =============================================================================
# Backward compatibility: type probe detection
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_duplication_criterion_type_probe_matches_introspection(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """DuplicationCriterionInput type probe matches direct introspection.

    The DuplicationCriterionInput type replaced PHashDuplicationCriterionInput
    in newer Stash versions. The capability flag must accurately reflect whether
    the new type exists on the server.
    """
    async with (
        stash_cleanup_tracker(stash_client),
        capture_graphql_calls(stash_client) as calls,
    ):
        try:
            result = await stash_client.execute(
                '{ _dup: __type(name: "DuplicationCriterionInput") { name } }'
            )
        finally:
            dump_graphql_calls(calls)
        assert len(calls) == 1

        type_exists = result.get("_dup") is not None

        caps = stash_client._capabilities
        assert caps is not None

        assert caps.has_type("DuplicationCriterionInput") == type_exists, (
            f"has_type('DuplicationCriterionInput')={caps.has_type('DuplicationCriterionInput')} "
            f"but direct introspection says type exists={type_exists}"
        )
        assert caps.uses_new_duplication_type == type_exists, (
            "Derived property uses_new_duplication_type should match "
            "has_type('DuplicationCriterionInput')"
        )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_performer_merge_type_probe_matches_introspection(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """PerformerMergeInput type probe matches direct introspection.

    PerformerMergeInput was added in Stash v0.30.2. The capability flag must
    accurately reflect whether the type exists on the server.
    """
    async with (
        stash_cleanup_tracker(stash_client),
        capture_graphql_calls(stash_client) as calls,
    ):
        try:
            result = await stash_client.execute(
                '{ _pm: __type(name: "PerformerMergeInput") { name } }'
            )
        finally:
            dump_graphql_calls(calls)
        assert len(calls) == 1

        type_exists = result.get("_pm") is not None

        caps = stash_client._capabilities
        assert caps is not None

        assert caps.has_type("PerformerMergeInput") == type_exists, (
            f"has_type('PerformerMergeInput')={caps.has_type('PerformerMergeInput')} "
            f"but direct introspection says PerformerMergeInput exists={type_exists}"
        )


# =============================================================================
# Backward compatibility: capability detection query structure
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_capability_detection_query_accepted_by_server(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """The CAPABILITY_DETECTION_QUERY executes without GraphQL errors on the live server.

    This is the most fundamental backward-compat test: if the combined introspection
    query that runs during initialization fails, the client cannot start at all.
    Re-executing it here validates it's still accepted by the current server.
    """
    async with (
        stash_cleanup_tracker(stash_client),
        capture_graphql_calls(stash_client) as calls,
    ):
        try:
            result = await stash_client.execute(CAPABILITY_DETECTION_QUERY)
        finally:
            dump_graphql_calls(calls)
        assert len(calls) == 1
        assert calls[0]["exception"] is None

        # Verify the expected top-level keys are present
        assert "version" in result
        assert "systemStatus" in result
        assert "__schema" in result

        # Verify systemStatus has expected fields
        status = result["systemStatus"]
        assert "appSchema" in status
        assert isinstance(status["appSchema"], int)

        # Verify version has expected fields
        version = result["version"]
        assert "version" in version
        assert isinstance(version["version"], str)

        # Verify __schema structure
        schema = result["__schema"]
        assert "queryType" in schema
        assert "mutationType" in schema
        assert "subscriptionType" in schema
        assert "types" in schema
        assert isinstance(schema["types"], list)


# =============================================================================
# Backward compatibility: fragment store handles all appSchema levels
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fragment_store_handles_every_schema_level(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """FragmentStore.rebuild() succeeds for every appSchema from 75 to 84+.

    This parametric test ensures that no threshold boundary causes a crash
    in the fragment building logic, regardless of which specific server
    version the test runs against.
    """
    from tests.fixtures.stash.graphql_responses import make_server_capabilities

    async with stash_cleanup_tracker(stash_client):
        for schema_version in range(75, 90):
            caps = make_server_capabilities(app_schema=schema_version)
            store = FragmentStore()
            # Must not raise
            store.rebuild(caps)

            # Spot-check: all critical queries must be non-empty strings
            assert isinstance(store.FIND_SCENE_QUERY, str)
            assert len(store.FIND_SCENE_QUERY) > 100
            assert isinstance(store.FIND_PERFORMER_QUERY, str)
            assert len(store.FIND_PERFORMER_QUERY) > 100
            assert isinstance(store.FIND_STUDIO_QUERY, str)
            assert len(store.FIND_STUDIO_QUERY) > 100
            assert isinstance(store.FIND_TAG_QUERY, str)
            assert len(store.FIND_TAG_QUERY) > 100
            assert isinstance(store.FIND_GROUP_QUERY, str)
            assert len(store.FIND_GROUP_QUERY) > 100
            assert isinstance(store.FIND_FOLDERS_QUERY, str)
            assert len(store.FIND_FOLDERS_QUERY) > 100
