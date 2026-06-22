"""Integration tests for capability-gated query execution and base fields.

Two backward-compat guarantees against a live server: the rebuilt FIND_X
queries execute without GraphQL errors, and the non-gated base fields are always
returned (non-UNSET) on any supported server. Split out of
test_capabilities_integration.py and consolidated per entity.
"""

import pytest

from stash_graphql_client import StashClient
from stash_graphql_client.types import Group, Performer, Studio, Tag
from stash_graphql_client.types.unset import UNSET
from tests.fixtures import capture_graphql_calls, dump_graphql_calls


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="capabilities_e2e")
@pytest.mark.parametrize(
    "find_method",
    [
        "find_scenes",
        "find_performers",
        "find_studios",
        "find_tags",
        "find_galleries",
        "find_images",
        "find_groups",
        "find_folders",
    ],
)
async def test_find_query_executes_on_server(
    find_method, stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """The rebuilt FIND_X query executes without GraphQL errors.

    Exercises the full pipeline: fragment store -> query string -> HTTP -> server.
    A non-negative int count proves the query executed.
    """
    async with (
        stash_cleanup_tracker(stash_client),
        capture_graphql_calls(stash_client) as calls,
    ):
        try:
            result = await getattr(stash_client, find_method)(filter_={"per_page": 1})
        finally:
            dump_graphql_calls(calls, find_method)
        assert isinstance(result.count, int)
        assert result.count >= 0


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="capabilities_e2e")
@pytest.mark.parametrize(
    ("entity_class", "name", "create_method", "find_method", "cleanup_key", "fields"),
    [
        (
            Performer,
            "SGC Compat Base Fields Performer",
            "create_performer",
            "find_performer",
            "performers",
            (
                "name",
                "urls",
                "gender",
                "birthdate",
                "alias_list",
                "details",
                "custom_fields",
                "stash_ids",
            ),
        ),
        (
            Studio,
            "SGC Compat Base Fields Studio",
            "create_studio",
            "find_studio",
            "studios",
            (
                "name",
                "urls",
                "aliases",
                "details",
                "rating100",
                "favorite",
                "stash_ids",
            ),
        ),
        (
            Tag,
            "sgc-compat-base-fields-tag",
            "create_tag",
            "find_tag",
            "tags",
            ("name", "description", "aliases", "stash_ids", "parents", "children"),
        ),
        (
            Group,
            "SGC Compat Base Fields Group",
            "create_group",
            "find_group",
            "groups",
            ("name", "aliases", "urls", "director", "synopsis", "tags", "scenes"),
        ),
    ],
)
async def test_base_fields_always_present(
    entity_class,
    name,
    create_method,
    find_method,
    cleanup_key,
    fields,
    stash_client: StashClient,
    stash_cleanup_tracker,
) -> None:
    """Non-gated base fields are non-UNSET on any supported server.

    These fields are never capability-gated, so a create + find round-trip must
    return each of them as non-UNSET on any server meeting MIN_SUPPORTED_APP_SCHEMA.
    """
    caps = stash_client._capabilities
    assert caps is not None

    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        try:
            entity = await getattr(stash_client, create_method)(entity_class(name=name))
        finally:
            dump_graphql_calls(calls, create_method)
        cleanup[cleanup_key].append(entity.id)
        assert entity.id is not None

        try:
            found = await getattr(stash_client, find_method)(entity.id)
        finally:
            dump_graphql_calls(calls, find_method)
        assert found is not None

        for field_name in fields:
            val = getattr(found, field_name)
            assert val is not UNSET, (
                f"Base field '{field_name}' should be non-UNSET on any supported "
                f"server (appSchema={caps.app_schema})"
            )
