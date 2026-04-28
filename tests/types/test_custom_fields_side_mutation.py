"""Tests for the custom_fields side-mutation handler on StashObject.

Covers the diff helper (snapshot vs current), the per-entity capability gate,
the CustomFieldsInput pydantic validators (key length / whitespace / nested
values / mutually exclusive modes), and the end-to-end save() path on Scene
(the pilot entity).
"""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from stash_graphql_client.types.base import StashObject
from stash_graphql_client.types.metadata import (
    CustomFieldsInput,
    _validate_custom_field_name,
)
from stash_graphql_client.types.scene import Scene
from stash_graphql_client.types.unset import UNSET
from tests.fixtures import create_graphql_response, dump_graphql_calls
from tests.fixtures.stash.graphql_responses import make_server_capabilities


# ---------------------------------------------------------------------------
# CustomFieldsInput validators (mirror server-side rules in custom_fields.go)
# ---------------------------------------------------------------------------


class TestCustomFieldsInputValidators:
    """The Pydantic class enforces the same constraints the Stash server does."""

    def test_accepts_scalar_values(self) -> None:
        cfi = CustomFieldsInput(
            partial={"a": "x", "b": 1, "c": 1.5, "d": True, "e": None}
        )
        assert cfi.partial == {"a": "x", "b": 1, "c": 1.5, "d": True, "e": None}

    def test_rejects_dict_value(self) -> None:
        with pytest.raises(TypeError, match="must be scalar"):
            CustomFieldsInput(partial={"k": {"nested": 1}})

    def test_rejects_list_value(self) -> None:
        with pytest.raises(TypeError, match="must be scalar"):
            CustomFieldsInput(partial={"k": [1, 2, 3]})

    def test_rejects_empty_key(self) -> None:
        with pytest.raises(ValueError, match="cannot be empty"):
            CustomFieldsInput(partial={"": "v"})

    def test_rejects_whitespace_padded_key(self) -> None:
        with pytest.raises(ValueError, match="leading or trailing whitespace"):
            CustomFieldsInput(partial={" key ": "v"})

    def test_rejects_oversized_key(self) -> None:
        long_key = "x" * 65  # 65 ASCII bytes
        with pytest.raises(ValueError, match="64 bytes"):
            CustomFieldsInput(partial={long_key: "v"})

    def test_oversized_check_is_byte_length_not_char_count(self) -> None:
        # 33 multi-byte UTF-8 chars * 2 bytes each = 66 bytes - over the limit
        # despite being only 33 characters
        multibyte = "é" * 33
        assert len(multibyte) == 33
        assert len(multibyte.encode("utf-8")) == 66
        with pytest.raises(ValueError, match="64 bytes"):
            CustomFieldsInput(partial={multibyte: "v"})

    def test_remove_keys_validated_too(self) -> None:
        with pytest.raises(ValueError, match="leading or trailing"):
            CustomFieldsInput(remove=[" bad "])

    def test_full_and_partial_are_mutually_exclusive(self) -> None:
        with pytest.raises(ValueError, match="mutually exclusive"):
            CustomFieldsInput(full={"a": "x"}, partial={"b": "y"})

    def test_partial_remove_overlap_rejected(self) -> None:
        with pytest.raises(ValueError, match="both partial and remove"):
            CustomFieldsInput(partial={"k": "v"}, remove=["k"])

    def test_full_alone_is_fine(self) -> None:
        cfi = CustomFieldsInput(full={"a": "x"})
        assert cfi.full == {"a": "x"}

    def test_remove_alone_is_fine(self) -> None:
        cfi = CustomFieldsInput(remove=["a", "b"])
        assert cfi.remove == ["a", "b"]

    def test_validator_passes_through_non_dict_partial(self) -> None:
        """When partial is explicitly None, validator returns it unchanged."""
        # Explicit None bypasses the default-skip path and runs the validator,
        # exercising the non-dict early return.
        cfi = CustomFieldsInput(full={"a": "x"}, partial=None)
        assert cfi.partial is None

    def test_validator_passes_through_non_list_remove(self) -> None:
        """When remove is explicitly None, validator returns it unchanged."""
        cfi = CustomFieldsInput(remove=None)
        assert cfi.remove is None

    def test_validate_custom_field_name_rejects_non_string(self) -> None:
        """Non-string keys are rejected at the helper level.

        Pydantic's ``dict[str, Any]`` typing usually coerces or rejects non-str
        keys before the validator runs, but the helper itself defends in depth.
        """
        with pytest.raises(ValueError, match="must be a string"):
            _validate_custom_field_name(1)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# _diff_custom_fields: snapshot vs current → CustomFieldsInput
# ---------------------------------------------------------------------------


def _scene_with_snapshot(snapshot: dict | UNSET, current: dict | UNSET) -> Scene:  # type: ignore[valid-type]
    """Build a Scene whose custom_fields snapshot and current differ as specified."""
    scene = Scene(id="1", custom_fields=snapshot if snapshot is not UNSET else UNSET)
    # model_post_init has already snapshotted from the constructor value.
    if current is not UNSET:
        scene.custom_fields = current
    return scene


class TestDiffCustomFields:
    """Verify the diff helper produces correct CustomFieldsInput payloads."""

    def test_no_change_returns_none(self) -> None:
        scene = _scene_with_snapshot({"a": "x"}, {"a": "x"})
        assert StashObject._diff_custom_fields(scene) is None

    def test_unset_current_returns_none(self) -> None:
        scene = _scene_with_snapshot({"a": "x"}, UNSET)
        # Snapshot has data, current is UNSET — no payload (we don't wipe-via-diff).
        assert StashObject._diff_custom_fields(scene) is None

    def test_added_key_emits_partial(self) -> None:
        scene = _scene_with_snapshot({"a": "x"}, {"a": "x", "b": "y"})
        cfi = StashObject._diff_custom_fields(scene)
        assert cfi is not None
        assert cfi.partial == {"b": "y"}
        assert cfi.remove is UNSET

    def test_changed_value_emits_partial(self) -> None:
        scene = _scene_with_snapshot({"a": "x"}, {"a": "y"})
        cfi = StashObject._diff_custom_fields(scene)
        assert cfi is not None
        assert cfi.partial == {"a": "y"}
        assert cfi.remove is UNSET

    def test_removed_key_emits_remove(self) -> None:
        scene = _scene_with_snapshot({"a": "x", "b": "y"}, {"a": "x"})
        cfi = StashObject._diff_custom_fields(scene)
        assert cfi is not None
        assert cfi.partial is UNSET
        assert cfi.remove == ["b"]

    def test_partial_and_remove_combined(self) -> None:
        scene = _scene_with_snapshot(
            {"a": "x", "b": "y", "c": "z"}, {"a": "X", "c": "z", "d": "new"}
        )
        cfi = StashObject._diff_custom_fields(scene)
        assert cfi is not None
        assert cfi.partial == {"a": "X", "d": "new"}
        assert cfi.remove == ["b"]

    def test_unset_snapshot_emits_partial_only(self) -> None:
        # Field was never read; current is freshly assigned. Can't compute removes.
        scene = Scene(id="1")  # custom_fields defaults to UNSET → snapshotted as UNSET
        scene.custom_fields = {"a": "x", "b": "y"}
        cfi = StashObject._diff_custom_fields(scene)
        assert cfi is not None
        assert cfi.partial == {"a": "x", "b": "y"}
        assert cfi.remove is UNSET

    def test_in_place_mutation_detected(self) -> None:
        # Snapshot is shallow-copied so in-place mutation of current doesn't
        # silently mutate the snapshot too.
        scene = Scene(id="1", custom_fields={"a": "x"})
        scene.custom_fields["a"] = "y"
        cfi = StashObject._diff_custom_fields(scene)
        assert cfi is not None
        assert cfi.partial == {"a": "y"}

    def test_diff_returns_none_when_current_is_none(self) -> None:
        """Defensive branch: current=None (Pydantic shouldn't allow but we guard)."""
        scene = Scene(id="1")
        # Bypass Pydantic validation to force an out-of-band value.
        object.__setattr__(scene, "custom_fields", None)
        assert StashObject._diff_custom_fields(scene) is None

    def test_diff_returns_none_when_current_is_not_dict(self) -> None:
        """Defensive branch: non-dict current value is rejected silently."""
        scene = Scene(id="1")
        object.__setattr__(scene, "custom_fields", "not-a-dict")
        assert StashObject._diff_custom_fields(scene) is None

    def test_diff_returns_none_when_unset_snapshot_and_empty_current(self) -> None:
        """UNSET snapshot + empty current = nothing to send (no payload)."""
        scene = Scene(id="1")  # snapshot UNSET
        scene.custom_fields = {}  # current empty dict
        assert StashObject._diff_custom_fields(scene) is None

    def test_diff_handles_non_dict_snapshot_with_current(self) -> None:
        """Defensive branch: snapshot got into a non-dict state somehow.

        Falls back to partial-only (same as the UNSET-snapshot path) — we can't
        compute removes against a non-dict snapshot, so we upsert current keys.
        """
        scene = Scene(id="1", custom_fields={"a": "x"})
        # Force snapshot into a defensive-only state.
        scene._snapshot["custom_fields"] = ["unexpected", "list"]
        cfi = StashObject._diff_custom_fields(scene)
        assert cfi is not None
        assert cfi.partial == {"a": "x"}
        assert cfi.remove is UNSET

    def test_diff_returns_none_when_non_dict_snapshot_and_empty_current(self) -> None:
        """Defensive branch: non-dict snapshot + empty current → no payload."""
        scene = Scene(id="1", custom_fields={"a": "x"})
        scene._snapshot["custom_fields"] = ["unexpected"]
        # Mark current as empty (preserve type via Pydantic-bypass).
        object.__setattr__(scene, "custom_fields", {})
        assert StashObject._diff_custom_fields(scene) is None


# ---------------------------------------------------------------------------
# Side-mutation handler: capability gate + end-to-end save()
# ---------------------------------------------------------------------------


class TestCustomFieldsRegistrationInvariant:
    """Every entity that declares a ``custom_fields`` field MUST register the
    side-mutation handler — otherwise writes to ``entity.custom_fields`` are
    silently dropped on save (the bug this whole feature exists to fix).

    This invariant catches a future entity that adds ``custom_fields`` but
    forgets either ``__tracked_fields__`` or ``__side_mutations__`` registration.
    """

    def test_every_class_with_custom_fields_registers_handler(self) -> None:
        # Walk all StashObject subclasses (recursively) and find any with a
        # `custom_fields` model field. Each must have it tracked AND registered
        # as a side mutation.
        def _all_subclasses(cls: type) -> set[type]:
            seen: set[type] = set()
            stack = list(cls.__subclasses__())
            while stack:
                sub = stack.pop()
                if sub in seen:
                    continue
                seen.add(sub)
                stack.extend(sub.__subclasses__())
            return seen

        offenders: list[str] = []
        for cls in _all_subclasses(StashObject):
            if "custom_fields" not in getattr(cls, "model_fields", {}):
                continue
            if "custom_fields" not in cls.__tracked_fields__:
                offenders.append(
                    f"{cls.__name__}: declares custom_fields field but missing "
                    "from __tracked_fields__ — writes will be silently dropped"
                )
            if "custom_fields" not in cls.__side_mutations__:
                offenders.append(
                    f"{cls.__name__}: declares custom_fields field but missing "
                    "from __side_mutations__ — writes will be silently dropped"
                )
        assert not offenders, "\n".join(offenders)


class TestCustomFieldsSideMutation:
    """The handler is registered on Scene and fires correctly through save()."""

    def test_handler_registered_on_scene(self) -> None:
        assert "custom_fields" in Scene.__side_mutations__
        assert "custom_fields" in Scene.__tracked_fields__

    @pytest.mark.asyncio
    async def test_save_fires_partial_update_when_capability_present(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """save() with a dirty custom_fields should fire sceneUpdate via the handler."""
        # Upgrade the client's capabilities so has_scene_custom_fields is True.
        respx_stash_client._capabilities = make_server_capabilities(84)

        scene = Scene(id="42", custom_fields={"existing": "v0"})
        scene.mark_clean()
        scene.custom_fields = {"existing": "v0", "_mm_d": "watermark"}

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            return_value=httpx.Response(
                200, json=create_graphql_response("sceneUpdate", {"id": "42"})
            )
        )

        try:
            await scene.save(respx_stash_client)
        finally:
            dump_graphql_calls(graphql_route.calls)

        # Exactly one call — the side-mutation handler's sceneUpdate
        assert len(graphql_route.calls) == 1
        req = json.loads(graphql_route.calls[0].request.content)
        assert "sceneUpdate" in req["query"]
        assert "UpdateSceneCustomFields" in req["query"]
        assert req["variables"]["input"]["id"] == "42"
        cf_payload = req["variables"]["input"]["custom_fields"]
        # partial only — existing key wasn't changed, _mm_d is new
        assert cf_payload.get("partial") == {"_mm_d": "watermark"}
        assert "remove" not in cf_payload
        assert "full" not in cf_payload

    @pytest.mark.asyncio
    async def test_save_raises_capability_error_when_unsupported(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """Server below appSchema 79 → handler raises StashCapabilityError."""
        respx_stash_client._capabilities = make_server_capabilities(75)  # < 79

        scene = Scene(id="42", custom_fields={"existing": "v0"})
        scene.mark_clean()
        scene.custom_fields = {"existing": "v0", "_mm_d": "watermark"}

        respx.post("http://localhost:9999/graphql").mock(
            return_value=httpx.Response(
                200, json=create_graphql_response("sceneUpdate", {"id": "42"})
            )
        )

        with pytest.raises(ValueError, match="has_scene_custom_fields"):
            # save() wraps handler errors in ValueError("Failed to save Scene: ...")
            await scene.save(respx_stash_client)

    @pytest.mark.asyncio
    async def test_save_skips_handler_when_no_change(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """No diff → handler is a no-op even when capability is supported."""
        respx_stash_client._capabilities = make_server_capabilities(84)

        scene = Scene(id="42", custom_fields={"existing": "v0"})
        scene.mark_clean()
        # No change to custom_fields. Save with no other dirty fields → nothing fires.

        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            return_value=httpx.Response(
                200, json=create_graphql_response("sceneUpdate", {"id": "42"})
            )
        )

        await scene.save(respx_stash_client)

        # Object isn't dirty, so save() returns early — zero calls.
        assert len(graphql_route.calls) == 0

    @pytest.mark.asyncio
    async def test_handler_returns_silently_when_no_diff(
        self, respx_stash_client, respx_entity_store
    ) -> None:
        """Direct handler invocation: capability OK, no diff → early return.

        Covers the ``if cfi is None: return`` branch in the factory closure
        for the case where the dispatcher fires the handler but the diff
        helper produces no payload (e.g., a no-op assignment that didn't
        actually change values).

        Uses the real client + respx (project's "mock at HTTP boundary only"
        rule) — any errant mutation would land at the respx route and the
        zero-call assertion would fail.
        """
        respx_stash_client._capabilities = make_server_capabilities(84)

        # Scene with snapshot == current — no diff.
        scene = Scene(id="42", custom_fields={"a": "x"})
        assert StashObject._diff_custom_fields(scene) is None

        # Catch any HTTP call the handler might errantly make.
        graphql_route = respx.post("http://localhost:9999/graphql").mock(
            return_value=httpx.Response(
                200, json=create_graphql_response("sceneUpdate", {"id": "42"})
            )
        )

        handler = Scene.__side_mutations__["custom_fields"]
        await handler(respx_stash_client, scene)

        # No HTTP call — the handler short-circuited on cfi=None.
        assert len(graphql_route.calls) == 0
