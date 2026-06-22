"""Integration tests for capability-gated fragment string composition.

Verifies that FragmentStore's FIND_X queries and CREATE/UPDATE mutations embed
(or omit) each capability-gated field to match the live server's reported caps.
Split out of test_capabilities_integration.py and consolidated per entity.
"""

import pytest

from stash_graphql_client import StashClient
from stash_graphql_client.fragments import fragment_store


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("query_attr", "checks"),
    [
        ("FIND_SCENE_QUERY", [("has_scene_custom_fields", "custom_fields", 79)]),
        (
            "FIND_PERFORMER_QUERY",
            [
                ("has_performer_career_start_end", "career_start", 78),
                ("has_performer_career_start_end", "career_end", 78),
            ],
        ),
        (
            "FIND_STUDIO_QUERY",
            [
                ("has_studio_custom_fields", "custom_fields", 76),
                ("has_studio_organized", "organized", 80),
            ],
        ),
        ("FIND_TAG_QUERY", [("has_tag_custom_fields", "custom_fields", 77)]),
        ("FIND_GALLERY_QUERY", [("has_gallery_custom_fields", "custom_fields", 81)]),
        ("FIND_IMAGE_QUERY", [("has_image_custom_fields", "custom_fields", 83)]),
        ("FIND_GROUP_QUERY", [("has_group_custom_fields", "custom_fields", 82)]),
        (
            "FIND_FOLDERS_QUERY",
            [
                ("has_folder_basename", "basename", 84),
                ("has_folder_basename", "parent_folders", 84),
                ("has_folder_sub_folders", "sub_folders", None),
            ],
        ),
    ],
)
async def test_fragment_store_query_fields_match_capabilities(
    query_attr, checks, stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """A FIND_X query embeds each capability-gated field iff the server supports it."""
    async with stash_cleanup_tracker(
        stash_client
    ):  # CCH:NO-DUMP  # reads caps + fragment strings; issues no GraphQL in body
        caps = stash_client._capabilities
        assert caps is not None

        query = str(getattr(fragment_store, query_attr))
        for cap_attr, field, threshold in checks:
            if getattr(caps, cap_attr):
                assert field in query, (
                    f"Server appSchema={caps.app_schema} supports {cap_attr} "
                    f"(>= {threshold}) but {query_attr} is missing {field}"
                )
            else:
                assert field not in query, (
                    f"Server appSchema={caps.app_schema} lacks {cap_attr} but "
                    f"{query_attr} unexpectedly contains {field}"
                )


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("mutation_attr", "checks"),
    [
        (
            "CREATE_PERFORMER_MUTATION",
            [
                ("has_performer_career_start_end", "career_start", 78),
                ("has_performer_career_start_end", "career_end", 78),
            ],
        ),
        (
            "UPDATE_PERFORMER_MUTATION",
            [
                ("has_performer_career_start_end", "career_start", 78),
                ("has_performer_career_start_end", "career_end", 78),
            ],
        ),
        (
            "CREATE_STUDIO_MUTATION",
            [
                ("has_studio_custom_fields", "custom_fields", 76),
                ("has_studio_organized", "organized", 80),
            ],
        ),
        ("CREATE_TAG_MUTATION", [("has_tag_custom_fields", "custom_fields", 77)]),
    ],
)
async def test_fragment_store_mutation_fields_match_capabilities(
    mutation_attr, checks, stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """A CREATE/UPDATE mutation embeds each capability-gated field iff supported."""
    async with stash_cleanup_tracker(
        stash_client
    ):  # CCH:NO-DUMP  # reads caps + fragment strings; issues no GraphQL in body
        caps = stash_client._capabilities
        assert caps is not None

        mutation = str(getattr(fragment_store, mutation_attr))
        for cap_attr, field, threshold in checks:
            if getattr(caps, cap_attr):
                assert field in mutation, (
                    f"Server appSchema={caps.app_schema} supports {cap_attr} "
                    f"(>= {threshold}) but {mutation_attr} is missing {field}"
                )
            else:
                assert field not in mutation, (
                    f"Server appSchema={caps.app_schema} lacks {cap_attr} but "
                    f"{mutation_attr} unexpectedly contains {field}"
                )
