"""Integration tests for the custom_fields side-mutation handler.

Validates the read-write round-trip for each entity that supports
``custom_fields`` against a real Stash instance:

1. Set ``entity.custom_fields = {...}`` and ``save()`` — verify the keys
   land on the server (handler diffs UNSET → partial-only).
2. Modify a subset (add key + change value + delete key) and ``save()``
   again — verify the server state reflects partial+remove semantics
   without wiping untouched keys.

These tests exercise the production flow that downstream consumers
(notably MMsD's `_mm_d` watermark / version-stamping pipeline) depend on.

Skip rules:
- Skipped automatically when ``client.capabilities.has_<entity>_custom_fields``
  is False (server appSchema below the threshold for that entity).
- Performer custom_fields predates the appSchema 75 floor (migration 71),
  so its test runs against any supported server.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

import pytest

from stash_graphql_client import StashClient
from stash_graphql_client.types import (
    Gallery,
    Group,
    Performer,
    Scene,
    Studio,
    Tag,
)
from stash_graphql_client.types.unset import is_set
from tests.fixtures import capture_graphql_calls, dump_graphql_calls


def _unique_suffix() -> str:
    """Avoid key collisions across reruns / parallel test workers."""
    return uuid.uuid4().hex[:8]


def _skip_unless_capability(client: StashClient, attr: str | None) -> None:
    """Skip the test unless the server supports custom_fields for this entity.

    ``attr=None`` means "always supported" (Performer — pre-floor).
    """
    if attr is None:
        return
    caps = client.capabilities
    if caps is None or not getattr(caps, attr, False):
        pytest.skip(
            f"Server appSchema does not support {attr} — "
            f"custom_fields side-mutation handler not exercised on this server"
        )


# =============================================================================
# Scene — the MMsD production target. Most thorough coverage here.
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_scene_custom_fields_round_trip(
    stash_client: StashClient, stash_cleanup_tracker, enable_scene_creation
) -> None:
    """Set, modify, partial-update, remove — verify full round-trip on Scene.

    Mirrors MMsD's `_mm_d` watermark pattern: stamp a version, later modify
    the stamp, eventually remove it. Verifies partial+remove semantics don't
    wipe unrelated keys (the whole point of the side-mutation handler).
    """
    _skip_unless_capability(stash_client, "has_scene_custom_fields")
    suffix = _unique_suffix()

    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        scene = Scene.new(title=f"cf_int_test_{suffix}")
        scene = await stash_client.create_scene(scene)
        cleanup["scenes"].append(scene.id)
        calls.clear()

        # ── Step 1: set initial custom_fields, save ───────────────────────
        scene.custom_fields = {
            f"_mm_d_{suffix}": json.dumps({"ver": "1.0", "synced_at": "t0"}),
            f"keep_{suffix}": "untouched",
            f"drop_later_{suffix}": "will-be-removed",
        }
        try:
            await scene.save(stash_client)
        finally:
            dump_graphql_calls(calls, "scene cf initial save")

        # save() may emit zero or one main-mutation call (no non-cf changes
        # since the entity was just created and marked clean implicitly via
        # the create round-trip). The side-mutation handler always fires.
        side_call = next(c for c in calls if "UpdateSceneCustomFields" in c["query"])
        assert side_call["variables"]["input"]["id"] == scene.id
        cf_payload = side_call["variables"]["input"]["custom_fields"]
        assert "partial" in cf_payload
        assert set(cf_payload["partial"]) == {
            f"_mm_d_{suffix}",
            f"keep_{suffix}",
            f"drop_later_{suffix}",
        }
        assert "remove" not in cf_payload  # snapshot was UNSET → no removes
        calls.clear()

        # Re-read from server to confirm persistence.
        reloaded = await stash_client.find_scene(scene.id)
        assert reloaded is not None
        assert is_set(reloaded.custom_fields)
        assert reloaded.custom_fields == {
            f"_mm_d_{suffix}": json.dumps({"ver": "1.0", "synced_at": "t0"}),
            f"keep_{suffix}": "untouched",
            f"drop_later_{suffix}": "will-be-removed",
        }
        calls.clear()

        # ── Step 2: change one value, drop one key, add another, save ─────
        reloaded.custom_fields = {
            f"_mm_d_{suffix}": json.dumps({"ver": "2.0", "synced_at": "t1"}),  # changed
            f"keep_{suffix}": "untouched",  # unchanged → must NOT appear
            f"new_{suffix}": "added",  # new
            # drop_later_{suffix} omitted → must appear in remove
        }
        try:
            await reloaded.save(stash_client)
        finally:
            dump_graphql_calls(calls, "scene cf diff save")

        side_call = next(c for c in calls if "UpdateSceneCustomFields" in c["query"])
        cf_payload = side_call["variables"]["input"]["custom_fields"]
        assert set(cf_payload["partial"]) == {f"_mm_d_{suffix}", f"new_{suffix}"}
        assert cf_payload["partial"][f"_mm_d_{suffix}"] == json.dumps(
            {"ver": "2.0", "synced_at": "t1"}
        )
        assert cf_payload["remove"] == [f"drop_later_{suffix}"]
        # `keep_{suffix}` must NOT appear in either — it didn't change.
        assert f"keep_{suffix}" not in cf_payload["partial"]
        calls.clear()

        # Re-read and confirm server state matches.
        reloaded = await stash_client.find_scene(scene.id)
        assert reloaded is not None
        assert reloaded.custom_fields == {
            f"_mm_d_{suffix}": json.dumps({"ver": "2.0", "synced_at": "t1"}),
            f"keep_{suffix}": "untouched",
            f"new_{suffix}": "added",
        }


# =============================================================================
# Performer — pre-floor (migration 71), no capability gate
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_performer_custom_fields_pre_floor(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Performer custom_fields predates the appSchema 75 floor — always works.

    Exercises the ``capability_attr=None`` factory branch end-to-end.
    """
    suffix = _unique_suffix()

    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
    ):
        perf = await stash_client.create_performer(
            Performer.new(name=f"cf_perf_{suffix}")
        )
        cleanup["performers"].append(perf.id)

        perf.custom_fields = {f"k_{suffix}": "v1"}
        await perf.save(stash_client)

        reloaded = await stash_client.find_performer(perf.id)
        assert reloaded is not None
        assert is_set(reloaded.custom_fields)
        assert reloaded.custom_fields.get(f"k_{suffix}") == "v1"


# =============================================================================
# Studio / Tag / Gallery / Group — capability-gated, lighter coverage
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_studio_custom_fields(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    _skip_unless_capability(stash_client, "has_studio_custom_fields")
    suffix = _unique_suffix()

    async with stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup:
        studio = await stash_client.create_studio(
            Studio.new(name=f"cf_studio_{suffix}")
        )
        cleanup["studios"].append(studio.id)

        studio.custom_fields = {f"k_{suffix}": "v1", f"k2_{suffix}": "v2"}
        await studio.save(stash_client)

        reloaded = await stash_client.find_studio(studio.id)
        assert reloaded is not None
        assert reloaded.custom_fields.get(f"k_{suffix}") == "v1"
        assert reloaded.custom_fields.get(f"k2_{suffix}") == "v2"

        # Modify + remove
        reloaded.custom_fields = {f"k_{suffix}": "v1-updated"}
        await reloaded.save(stash_client)

        reloaded2 = await stash_client.find_studio(studio.id)
        assert reloaded2 is not None
        assert reloaded2.custom_fields.get(f"k_{suffix}") == "v1-updated"
        assert f"k2_{suffix}" not in reloaded2.custom_fields


@pytest.mark.integration
@pytest.mark.asyncio
async def test_tag_custom_fields(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    _skip_unless_capability(stash_client, "has_tag_custom_fields")
    suffix = _unique_suffix()

    async with stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup:
        tag = await stash_client.create_tag(Tag.new(name=f"cf_tag_{suffix}"))
        cleanup["tags"].append(tag.id)

        tag.custom_fields = {f"k_{suffix}": "tag_value"}
        await tag.save(stash_client)

        reloaded = await stash_client.find_tag(tag.id)
        assert reloaded is not None
        assert reloaded.custom_fields.get(f"k_{suffix}") == "tag_value"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_gallery_custom_fields(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    _skip_unless_capability(stash_client, "has_gallery_custom_fields")
    suffix = _unique_suffix()

    async with stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup:
        gallery = await stash_client.create_gallery(
            Gallery.new(title=f"cf_gallery_{suffix}")
        )
        cleanup["galleries"].append(gallery.id)

        gallery.custom_fields = {f"k_{suffix}": "gallery_value"}
        await gallery.save(stash_client)

        reloaded = await stash_client.find_gallery(gallery.id)
        assert reloaded is not None
        assert reloaded.custom_fields.get(f"k_{suffix}") == "gallery_value"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_group_custom_fields(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    _skip_unless_capability(stash_client, "has_group_custom_fields")
    suffix = _unique_suffix()

    async with stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup:
        group = await stash_client.create_group(Group.new(name=f"cf_group_{suffix}"))
        cleanup["groups"].append(group.id)

        group.custom_fields = {f"k_{suffix}": "group_value"}
        await group.save(stash_client)

        reloaded = await stash_client.find_group(group.id)
        assert reloaded is not None
        assert reloaded.custom_fields.get(f"k_{suffix}") == "group_value"


# =============================================================================
# Image — not user-creatable; exercise via find-existing + update
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_images
async def test_image_custom_fields_on_existing(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Image custom_fields path: find existing image, modify, save, verify.

    Images aren't user-creatable (only the scanner creates them), so this
    test piggybacks on whatever images already exist in the test server's
    library. The custom_fields keys are uniquely suffixed and removed at the
    end so the image's existing custom_fields aren't polluted between runs.
    """
    _skip_unless_capability(stash_client, "has_image_custom_fields")
    suffix = _unique_suffix()
    test_key = f"_int_test_{suffix}"

    async with stash_cleanup_tracker(stash_client, auto_capture=False):
        result = await stash_client.find_images(filter_={"per_page": 1})
        if not is_set(result.images) or not result.images:
            pytest.skip("No images in test Stash library")
        image_id = result.images[0].id

        image = await stash_client.find_image(image_id)
        assert image is not None
        original_cf: dict[str, Any] = (
            dict(image.custom_fields) if is_set(image.custom_fields) else {}
        )

        try:
            # Add a unique key without disturbing existing ones.
            image.custom_fields = {**original_cf, test_key: "stamp"}
            await image.save(stash_client)

            reloaded = await stash_client.find_image(image_id)
            assert reloaded is not None
            assert reloaded.custom_fields.get(test_key) == "stamp"
            # Verify side-mutation handler didn't wipe other keys.
            for k, v in original_cf.items():
                assert reloaded.custom_fields.get(k) == v, (
                    f"Existing custom_field {k!r} was clobbered by "
                    "the side-mutation save"
                )
        finally:
            # Clean up: remove the test key so the image's custom_fields are
            # restored to their pre-test state.
            cleanup_image = await stash_client.find_image(image_id)
            if cleanup_image is not None and is_set(cleanup_image.custom_fields):
                cleanup_image.custom_fields = {
                    k: v
                    for k, v in cleanup_image.custom_fields.items()
                    if k != test_key
                }
                await cleanup_image.save(stash_client)
