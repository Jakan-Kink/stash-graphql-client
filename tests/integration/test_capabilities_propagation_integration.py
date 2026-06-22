"""Integration tests for end-to-end capability-gated field propagation.

Verifies the full pipeline ServerCapabilities -> FragmentStore.rebuild() ->
query string -> server response -> Pydantic deserialization: a gated field is
non-UNSET iff the server supports it, across create/find and round-trip update.
Split out of test_capabilities_integration.py.
"""

import pytest

from stash_graphql_client import StashClient
from stash_graphql_client.types import Gallery, Group, Performer, Scene, Studio, Tag
from stash_graphql_client.types.unset import UNSET, is_set
from tests.fixtures import capture_graphql_calls, dump_graphql_calls


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="capabilities_e2e")
async def test_performer_career_fields_propagate_from_server(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """career_start/career_end are non-UNSET iff appSchema >= 78."""
    caps = stash_client._capabilities
    assert caps is not None

    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        try:
            performer = await stash_client.create_performer(
                Performer(name="SGC Caps E2E Performer")
            )
        finally:
            dump_graphql_calls(calls, "create_performer")
        cleanup["performers"].append(performer.id)
        assert performer.id is not None

        try:
            found = await stash_client.find_performer(performer.id)
        finally:
            dump_graphql_calls(calls, "find_performer")
        assert found is not None

        if caps.has_performer_career_start_end:
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
    """organized is non-UNSET iff appSchema >= 80."""
    caps = stash_client._capabilities
    assert caps is not None

    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        try:
            studio = await stash_client.create_studio(
                Studio(name="SGC Caps E2E Studio Organized")
            )
        finally:
            dump_graphql_calls(calls, "create_studio")
        cleanup["studios"].append(studio.id)
        assert studio.id is not None

        try:
            found = await stash_client.find_studio(studio.id)
        finally:
            dump_graphql_calls(calls, "find_studio")
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
    """custom_fields on Studio is non-UNSET iff appSchema >= 76."""
    caps = stash_client._capabilities
    assert caps is not None

    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        try:
            studio = await stash_client.create_studio(
                Studio(name="SGC Caps E2E Studio Custom Fields")
            )
        finally:
            dump_graphql_calls(calls, "create_studio")
        cleanup["studios"].append(studio.id)
        assert studio.id is not None

        try:
            found = await stash_client.find_studio(studio.id)
        finally:
            dump_graphql_calls(calls, "find_studio")
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

    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        try:
            tag = await stash_client.create_tag(
                Tag(name="sgc-caps-e2e-tag-custom-fields")
            )
        finally:
            dump_graphql_calls(calls, "create_tag")
        cleanup["tags"].append(tag.id)
        assert tag.id is not None

        try:
            found = await stash_client.find_tag(tag.id)
        finally:
            dump_graphql_calls(calls, "find_tag")
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
    a different code path than the inline-fragment entities above.
    """
    caps = stash_client._capabilities
    assert caps is not None

    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        try:
            group = await stash_client.create_group(
                Group(name="SGC Caps E2E Group Custom Fields")
            )
        finally:
            dump_graphql_calls(calls, "create_group")
        cleanup["groups"].append(group.id)
        assert group.id is not None

        try:
            found = await stash_client.find_group(group.id)
        finally:
            dump_graphql_calls(calls, "find_group")
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

    Folders can't be created via the API, so this queries existing folders and
    skips when none are present. Folder uses the named-fragment injection path.
    """
    caps = stash_client._capabilities
    assert caps is not None

    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        try:
            result = await stash_client.find_folders(filter_={"per_page": 1})
        finally:
            dump_graphql_calls(calls, "find_folders")
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

        if caps.has_folder_sub_folders:
            assert is_set(folder.sub_folders), (
                "sub_folders should be non-UNSET when server reports Folder.sub_folders"
            )
        else:
            assert folder.sub_folders is UNSET, (
                "sub_folders should remain UNSET when server lacks Folder.sub_folders"
            )


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="capabilities_e2e")
async def test_scene_custom_fields_propagate_from_server(
    stash_client: StashClient, stash_cleanup_tracker, enable_scene_creation
) -> None:
    """custom_fields on Scene is non-UNSET iff appSchema >= 79."""
    caps = stash_client._capabilities
    assert caps is not None

    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        try:
            scene = await stash_client.create_scene(
                Scene.new(title="SGC Compat E2E Scene Custom Fields")
            )
        finally:
            dump_graphql_calls(calls, "create_scene")
        cleanup["scenes"].append(scene.id)
        assert scene.id is not None

        try:
            found = await stash_client.find_scene(scene.id)
        finally:
            dump_graphql_calls(calls, "find_scene")
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
    """custom_fields on Gallery is non-UNSET iff appSchema >= 81."""
    caps = stash_client._capabilities
    assert caps is not None

    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        try:
            gallery = await stash_client.create_gallery(
                Gallery.new(title="SGC Compat E2E Gallery Custom Fields")
            )
        finally:
            dump_graphql_calls(calls, "create_gallery")
        cleanup["galleries"].append(gallery.id)
        assert gallery.id is not None

        try:
            found = await stash_client.find_gallery(gallery.id)
        finally:
            dump_graphql_calls(calls, "find_gallery")
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
async def test_image_custom_fields_propagate_from_server(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """custom_fields on Image is non-UNSET iff appSchema >= 83.

    Images cannot be created via the API, so this queries existing images and
    skips when none are present.
    """
    caps = stash_client._capabilities
    assert caps is not None

    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        try:
            result = await stash_client.find_images(filter_={"per_page": 1})
        finally:
            dump_graphql_calls(calls, "find_images")
        if result.count == 0:
            pytest.skip(
                "No images in test Stash instance — cannot verify field propagation"
            )

        assert is_set(result.images)

        image = result.images[0]

        if caps.has_image_custom_fields:
            assert is_set(image.custom_fields), (
                f"custom_fields should be non-UNSET when appSchema={caps.app_schema} >= 83"
            )
        else:
            assert image.custom_fields is UNSET, (
                f"custom_fields should remain UNSET when appSchema={caps.app_schema} < 83"
            )


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="capabilities_e2e")
async def test_performer_career_fields_round_trip_through_update(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """career_start/career_end survive a create -> update -> find round-trip."""
    caps = stash_client._capabilities
    assert caps is not None

    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        try:
            performer = await stash_client.create_performer(
                Performer(name="SGC Compat Round-Trip Career Performer")
            )
        finally:
            dump_graphql_calls(calls, "create_performer")
        cleanup["performers"].append(performer.id)

        if caps.has_performer_career_start_end:
            performer.career_start = "2010"
            performer.career_end = "2020"
            try:
                updated = await stash_client.update_performer(performer)
            finally:
                dump_graphql_calls(calls, "update_performer")
            assert is_set(updated.career_start)
            assert updated.career_start == "2010"
            assert is_set(updated.career_end)
            assert updated.career_end == "2020"

            try:
                found = await stash_client.find_performer(performer.id)
            finally:
                dump_graphql_calls(calls, "find_performer")
            assert found is not None
            assert found.career_start == "2010"
            assert found.career_end == "2020"
        else:
            performer.name = "SGC Compat Round-Trip Career Performer Updated"
            try:
                updated = await stash_client.update_performer(performer)
            finally:
                dump_graphql_calls(calls, "update_performer")
            assert updated.name == "SGC Compat Round-Trip Career Performer Updated"
            assert updated.career_start is UNSET
            assert updated.career_end is UNSET


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="capabilities_e2e")
async def test_studio_organized_round_trip_through_update(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """organized flag survives a create -> update -> find round-trip on Studio."""
    caps = stash_client._capabilities
    assert caps is not None

    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        try:
            studio = await stash_client.create_studio(
                Studio(name="SGC Compat Round-Trip Organized Studio")
            )
        finally:
            dump_graphql_calls(calls, "create_studio")
        cleanup["studios"].append(studio.id)

        if caps.has_studio_organized:
            studio.organized = True
            try:
                updated = await stash_client.update_studio(studio)
            finally:
                dump_graphql_calls(calls, "update_studio")
            assert is_set(updated.organized)
            assert updated.organized is True

            try:
                found = await stash_client.find_studio(studio.id)
            finally:
                dump_graphql_calls(calls, "find_studio")
            assert found is not None
            assert found.organized is True
        else:
            studio.name = "SGC Compat Round-Trip Organized Studio Updated"
            try:
                updated = await stash_client.update_studio(studio)
            finally:
                dump_graphql_calls(calls, "update_studio")
            assert updated.name == "SGC Compat Round-Trip Organized Studio Updated"
            assert updated.organized is UNSET


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="capabilities_e2e")
async def test_studio_custom_fields_round_trip_through_update(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """custom_fields on Studio survives a create -> update -> find round-trip."""
    caps = stash_client._capabilities
    assert caps is not None

    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        try:
            studio = await stash_client.create_studio(
                Studio(name="SGC Compat Round-Trip Custom Fields Studio")
            )
        finally:
            dump_graphql_calls(calls, "create_studio")
        cleanup["studios"].append(studio.id)

        if caps.has_studio_custom_fields:
            assert is_set(studio.custom_fields)
            try:
                found = await stash_client.find_studio(studio.id)
            finally:
                dump_graphql_calls(calls, "find_studio")
            assert found is not None
            assert is_set(found.custom_fields)
        else:
            assert studio.custom_fields is UNSET
            try:
                found = await stash_client.find_studio(studio.id)
            finally:
                dump_graphql_calls(calls, "find_studio")
            assert found is not None
            assert found.custom_fields is UNSET
