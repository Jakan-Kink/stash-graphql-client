"""Integration tests for server capability detection.

Tests that the client correctly detects and exposes server capabilities from a
real Stash instance: the detection query runs successfully and populates
ServerCapabilities, the flags match live introspection, and the fragment store
rebuilds consistently for any appSchema. End-to-end gated-field propagation,
query execution, and fragment string composition live in the sibling
test_capabilities_{propagation,queries,fragments}_integration.py files.
"""

import pytest

from stash_graphql_client import StashClient
from stash_graphql_client.capabilities import (
    CAPABILITY_DETECTION_QUERY,
    MIN_SUPPORTED_APP_SCHEMA,
    ServerCapabilities,
)
from stash_graphql_client.fragments import FragmentStore, fragment_store
from stash_graphql_client.types import expect_dict
from tests.fixtures import (
    capture_graphql_calls,
    dump_graphql_calls,
    introspection_field_names,
)
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
    async with stash_cleanup_tracker(
        stash_client
    ):  # CCH:NO-DUMP  # reads caps; no GraphQL in body
        assert stash_client._capabilities is not None
        assert isinstance(stash_client._capabilities, ServerCapabilities)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_capabilities_app_schema_meets_minimum(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test that detected appSchema meets the library's minimum requirement."""
    async with stash_cleanup_tracker(
        stash_client
    ):  # CCH:NO-DUMP  # reads caps; no GraphQL in body
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
    async with stash_cleanup_tracker(
        stash_client
    ):  # CCH:NO-DUMP  # reads caps; no GraphQL in body
        caps = stash_client._capabilities
        assert caps is not None

        assert isinstance(caps.version_string, str)
        assert caps.version_string != "unknown"
        # On tagged builds, version starts with "v"; on develop/untagged it's empty
        if caps.version_string:
            assert caps.version_string.startswith("v"), (
                f"Expected version_string to start with 'v', got: {caps.version_string!r}"
            )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_capabilities_duplication_criterion_flag(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test that the DuplicationCriterionInput type can be queried via has_type()."""
    async with stash_cleanup_tracker(
        stash_client
    ):  # CCH:NO-DUMP  # reads caps; no GraphQL in body
        caps = stash_client._capabilities
        assert caps is not None

        assert isinstance(caps.has_type("DuplicationCriterionInput"), bool)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_capabilities_derived_properties_consistent(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test that derived capability properties are consistent with app_schema."""
    async with stash_cleanup_tracker(
        stash_client
    ):  # CCH:NO-DUMP  # reads caps; no GraphQL in body
        caps = stash_client._capabilities
        assert caps is not None

        schema = caps.app_schema

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
    """Test that the fragment store was rebuilt with the detected capabilities."""
    async with stash_cleanup_tracker(
        stash_client
    ):  # CCH:NO-DUMP  # reads fragment strings; no GraphQL in body
        assert fragment_store.FIND_TAG_QUERY is not None
        assert fragment_store.FIND_PERFORMER_QUERY is not None
        assert fragment_store.FIND_SCENE_QUERY is not None
        assert fragment_store.FIND_STUDIO_QUERY is not None

        assert len(str(fragment_store.FIND_TAG_QUERY)) > 0
        assert len(str(fragment_store.FIND_PERFORMER_QUERY)) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_capability_detection_no_calls_after_init(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test that reading capabilities does not trigger additional GraphQL calls."""
    async with (
        stash_cleanup_tracker(
            stash_client
        ),  # CCH:NO-DUMP  # asserts zero GraphQL calls; capability read is pure attribute access
        capture_graphql_calls(stash_client) as calls,
    ):
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
    a single request. We verify this by creating a fresh client and wrapping
    _raw_execute before calling initialize(), then asserting it was invoked
    exactly once with the combined query.
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

        assert mock_raw.call_count == 1, (
            f"Expected exactly 1 GraphQL round-trip during initialization, "
            f"got {mock_raw.call_count}"
        )

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
    """Lookup methods must return bool regardless of server version."""
    async with stash_cleanup_tracker(
        stash_client
    ):  # CCH:NO-DUMP  # reads caps lookups; no GraphQL in body
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
    """Mutation-presence flags match a fresh direct introspection of the Mutation type."""
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

        mutation_names = introspection_field_names(result, "_mutations")

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
    """Query-presence flags match a fresh direct introspection of the Query type."""
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

        query_names = introspection_field_names(result, "_queries")

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
    """Subscription-presence flags match a fresh direct introspection of the Subscription type."""
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

        subscription_names = introspection_field_names(result, "_subscriptions")

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
    """subscription_names is populated with at least the known Stash subscriptions."""
    async with stash_cleanup_tracker(
        stash_client
    ):  # CCH:NO-DUMP  # reads caps; no GraphQL in body
        caps = stash_client._capabilities
        assert caps is not None

        assert len(caps.subscription_names) > 0, (
            "subscription_names is empty — __schema.subscriptionType was not parsed"
        )

        for name in ("jobsSubscribe", "loggingSubscribe", "scanCompleteSubscribe"):
            assert caps.has_subscription(name), (
                f"Expected has_subscription({name!r}) to be True on live server"
            )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_capabilities_flags_are_monotonic(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Higher appSchema features imply all lower-schema features are also present."""
    async with stash_cleanup_tracker(
        stash_client
    ):  # CCH:NO-DUMP  # reads caps flags; no GraphQL in body
        caps = stash_client._capabilities
        assert caps is not None

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
                for lower_flag, lower_threshold in chain[:i]:
                    assert getattr(caps, lower_flag), (
                        f"{flag} (appSchema >= {threshold}) is True but "
                        f"{lower_flag} (appSchema >= {lower_threshold}) is False — "
                        f"appSchema monotonicity violated (server appSchema={caps.app_schema})"
                    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fragment_store_rebuild_idempotent(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Rebuilding the fragment store multiple times yields identical queries."""
    async with stash_cleanup_tracker(
        stash_client
    ):  # CCH:NO-DUMP  # inspects fragment strings; no GraphQL in body
        caps = stash_client._capabilities
        assert caps is not None

        first_scene_query = fragment_store.FIND_SCENE_QUERY
        first_performer_query = fragment_store.FIND_PERFORMER_QUERY
        first_studio_query = fragment_store.FIND_STUDIO_QUERY
        first_tag_query = fragment_store.FIND_TAG_QUERY
        first_gallery_query = fragment_store.FIND_GALLERIES_QUERY
        first_image_query = fragment_store.FIND_IMAGE_QUERY
        first_group_query = fragment_store.FIND_GROUP_QUERY
        first_folder_query = fragment_store.FIND_FOLDERS_QUERY

        fragment_store.rebuild(caps)

        assert first_scene_query == fragment_store.FIND_SCENE_QUERY
        assert first_performer_query == fragment_store.FIND_PERFORMER_QUERY
        assert first_studio_query == fragment_store.FIND_STUDIO_QUERY
        assert first_tag_query == fragment_store.FIND_TAG_QUERY
        assert first_gallery_query == fragment_store.FIND_GALLERIES_QUERY
        assert first_image_query == fragment_store.FIND_IMAGE_QUERY
        assert first_group_query == fragment_store.FIND_GROUP_QUERY
        assert first_folder_query == fragment_store.FIND_FOLDERS_QUERY

        fragment_store.rebuild(caps)
        assert first_scene_query == fragment_store.FIND_SCENE_QUERY


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fragment_store_find_create_update_use_same_fields(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """FIND, CREATE, and UPDATE queries for the same entity contain identical field sets."""
    async with stash_cleanup_tracker(
        stash_client
    ):  # CCH:NO-DUMP  # inspects fragment strings; no GraphQL in body
        caps = stash_client._capabilities
        assert caps is not None

        performer_fields = fragment_store.PERFORMER_FIELDS.strip()
        assert performer_fields in fragment_store.FIND_PERFORMER_QUERY
        assert performer_fields in fragment_store.CREATE_PERFORMER_MUTATION
        assert performer_fields in fragment_store.UPDATE_PERFORMER_MUTATION
        assert performer_fields in fragment_store.BULK_PERFORMER_UPDATE_MUTATION

        studio_fields = fragment_store.STUDIO_FIELDS.strip()
        assert studio_fields in fragment_store.FIND_STUDIO_QUERY
        assert studio_fields in fragment_store.CREATE_STUDIO_MUTATION
        assert studio_fields in fragment_store.UPDATE_STUDIO_MUTATION

        tag_fields = fragment_store.TAG_FIELDS.strip()
        assert tag_fields in fragment_store.FIND_TAG_QUERY
        assert tag_fields in fragment_store.CREATE_TAG_MUTATION
        assert tag_fields in fragment_store.UPDATE_TAG_MUTATION
        assert tag_fields in fragment_store.TAGS_MERGE_MUTATION

        scene_fragment_marker = "fragment SceneFragment on Scene"
        assert scene_fragment_marker in fragment_store.FIND_SCENE_QUERY
        assert scene_fragment_marker in fragment_store.CREATE_SCENE_MUTATION
        assert scene_fragment_marker in fragment_store.UPDATE_SCENE_MUTATION
        assert scene_fragment_marker in fragment_store.BULK_SCENE_UPDATE_MUTATION

        gallery_fragment_marker = "fragment GalleryFragment on Gallery"
        assert gallery_fragment_marker in fragment_store.FIND_GALLERY_QUERY
        assert gallery_fragment_marker in fragment_store.CREATE_GALLERY_MUTATION
        assert gallery_fragment_marker in fragment_store.UPDATE_GALLERY_MUTATION

        image_fragment_marker = "fragment ImageFragment on Image"
        assert image_fragment_marker in fragment_store.FIND_IMAGE_QUERY
        assert image_fragment_marker in fragment_store.CREATE_IMAGE_MUTATION
        assert image_fragment_marker in fragment_store.UPDATE_IMAGE_MUTATION

        group_fragment_marker = "fragment GroupFields on Group"
        assert group_fragment_marker in fragment_store.FIND_GROUP_QUERY
        assert group_fragment_marker in fragment_store.CREATE_GROUP_MUTATION
        assert group_fragment_marker in fragment_store.UPDATE_GROUP_MUTATION

        folder_fragment_marker = "fragment FolderFields on Folder"
        assert folder_fragment_marker in fragment_store.FIND_FOLDER_QUERY
        assert folder_fragment_marker in fragment_store.FIND_FOLDERS_QUERY


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fresh_client_detects_same_capabilities(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """A second independently-initialized client detects identical capabilities."""
    async with stash_cleanup_tracker(
        stash_client
    ):  # CCH:NO-DUMP  # GraphQL is issued via a separate fresh_client, not stash_client
        original_caps = stash_client._capabilities
        assert original_caps is not None

        conn, verify_ssl = stash_client._init_args
        fresh_client = StashClient(conn=conn, verify_ssl=verify_ssl)

        try:
            await fresh_client.initialize()
            fresh_caps = fresh_client._capabilities
            assert fresh_caps is not None

            assert fresh_caps.app_schema == original_caps.app_schema
            assert fresh_caps.version_string == original_caps.version_string
            assert fresh_caps.has_type("DuplicationCriterionInput") == (
                original_caps.has_type("DuplicationCriterionInput")
            )
            assert fresh_caps.has_type("PerformerMergeInput") == (
                original_caps.has_type("PerformerMergeInput")
            )

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
            assert fresh_caps.has_folder_sub_folders == (
                original_caps.has_folder_sub_folders
            )
            assert fresh_caps.has_performer_career_date_strings == (
                original_caps.has_performer_career_date_strings
            )

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


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fragment_store_rebuild_with_minimum_schema(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Rebuilding the fragment store with appSchema=75 removes all gated fields."""
    from tests.fixtures.stash.graphql_responses import make_server_capabilities

    async with stash_cleanup_tracker(
        stash_client
    ):  # CCH:NO-DUMP  # rebuilds a local store from synthetic caps; no GraphQL in body
        caps = stash_client._capabilities
        assert caps is not None

        min_caps = make_server_capabilities(app_schema=75)
        store = FragmentStore()
        store.rebuild(min_caps)

        assert "custom_fields" not in store.FIND_SCENE_QUERY
        assert "custom_fields" not in store.FIND_STUDIO_QUERY
        assert "custom_fields" not in store.FIND_TAG_QUERY
        assert "custom_fields" not in store.FIND_GALLERY_QUERY
        assert "custom_fields" not in store.FIND_IMAGE_QUERY
        assert "custom_fields" not in store.FIND_GROUP_QUERY

        assert "career_start" not in store.FIND_PERFORMER_QUERY
        assert "career_end" not in store.FIND_PERFORMER_QUERY

        assert "organized" not in store.FIND_STUDIO_QUERY

        assert "basename" not in store.FIND_FOLDERS_QUERY
        assert "parent_folders" not in store.FIND_FOLDERS_QUERY


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fragment_store_rebuild_with_maximum_schema(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Rebuilding the fragment store with appSchema=84 includes all gated fields."""
    from tests.fixtures.stash.graphql_responses import make_server_capabilities

    async with stash_cleanup_tracker(
        stash_client
    ):  # CCH:NO-DUMP  # rebuilds a local store from synthetic caps; no GraphQL in body
        max_caps = make_server_capabilities(app_schema=84)
        store = FragmentStore()
        store.rebuild(max_caps)

        assert "custom_fields" in store.FIND_SCENE_QUERY
        assert "custom_fields" in store.FIND_STUDIO_QUERY
        assert "custom_fields" in store.FIND_TAG_QUERY
        assert "custom_fields" in store.FIND_GALLERY_QUERY
        assert "custom_fields" in store.FIND_IMAGE_QUERY
        assert "custom_fields" in store.FIND_GROUP_QUERY

        assert "career_start" in store.FIND_PERFORMER_QUERY
        assert "career_end" in store.FIND_PERFORMER_QUERY

        assert "organized" in store.FIND_STUDIO_QUERY

        assert "basename" in store.FIND_FOLDERS_QUERY
        assert "parent_folders" in store.FIND_FOLDERS_QUERY


@pytest.mark.integration
@pytest.mark.asyncio
async def test_tracked_mutations_subset_of_server_mutations(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """All tracked mutation names are recognized by the server's Mutation type."""
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

        all_mutations: set[str] = introspection_field_names(result, "_mutations")

        caps = stash_client._capabilities
        assert caps is not None

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
    """All tracked query names are recognized by the server's Query type."""
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

        all_queries: set[str] = introspection_field_names(result, "_queries")

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
    """All tracked subscription names are recognized by the server's Subscription type."""
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

        all_subscriptions: set[str] = introspection_field_names(
            result, "_subscriptions"
        )

        caps = stash_client._capabilities
        assert caps is not None

        for subscription_name in _SUBSCRIPTION_REGISTRY.values():
            if caps.has_subscription(subscription_name):
                assert subscription_name in all_subscriptions, (
                    f"has_subscription({subscription_name!r}) is True but "
                    f"subscription '{subscription_name}' not found in server's "
                    f"Subscription type"
                )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_duplication_criterion_type_probe_matches_introspection(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """DuplicationCriterionInput type probe matches direct introspection."""
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
    """PerformerMergeInput type probe matches direct introspection."""
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


@pytest.mark.integration
@pytest.mark.asyncio
async def test_capability_detection_query_accepted_by_server(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """The CAPABILITY_DETECTION_QUERY executes without GraphQL errors on the live server."""
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

        assert "version" in result
        assert "systemStatus" in result
        assert "__schema" in result

        status = expect_dict(
            result["systemStatus"],
            "test_capability_detection_query_accepted_by_server (systemStatus)",
        )
        assert "appSchema" in status
        assert isinstance(status["appSchema"], int)

        version = expect_dict(
            result["version"],
            "test_capability_detection_query_accepted_by_server (version)",
        )
        assert "version" in version
        assert isinstance(version["version"], str)

        schema = expect_dict(
            result["__schema"],
            "test_capability_detection_query_accepted_by_server (__schema)",
        )
        assert "queryType" in schema
        assert "mutationType" in schema
        assert "subscriptionType" in schema
        assert "types" in schema
        assert isinstance(schema["types"], list)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fragment_store_handles_every_schema_level(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """FragmentStore.rebuild() succeeds for every appSchema from 75 to 89."""
    from tests.fixtures.stash.graphql_responses import make_server_capabilities

    async with stash_cleanup_tracker(
        stash_client
    ):  # CCH:NO-DUMP  # rebuilds local stores from synthetic caps; no GraphQL in body
        for schema_version in range(75, 90):
            caps = make_server_capabilities(app_schema=schema_version)
            store = FragmentStore()
            store.rebuild(caps)

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
