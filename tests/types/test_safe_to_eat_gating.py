"""Tests for __safe_to_eat__ capability gating on StashInput.to_graphql().

Verifies that:
- Fields listed in __safe_to_eat__ are silently stripped when the server
  schema lacks them (with a warning emitted).
- Fields listed in __safe_to_eat__ pass through when the server supports them.
- No gating occurs when fragment_store._capabilities is None.
- ValueError is raised for unsupported fields NOT in __safe_to_eat__.
- Gating is skipped entirely when the type is unknown to the server schema.
"""

from __future__ import annotations

import warnings
from types import MappingProxyType
from typing import ClassVar
from unittest.mock import patch

import pytest
from pydantic import Field

from stash_graphql_client.capabilities import ServerCapabilities
from stash_graphql_client.types.base import StashInput
from stash_graphql_client.types.unset import UNSET, UnsetType


# ---------------------------------------------------------------------------
# Test helpers — tiny StashInput subclasses
# ---------------------------------------------------------------------------


class _SimpleInput(StashInput):
    """Input type with no __safe_to_eat__ fields."""

    alpha: str | None | UnsetType = Field(UNSET, alias="alpha")
    beta: int | None | UnsetType = Field(UNSET, alias="beta")


class _GatedInput(StashInput):
    """Input type where 'beta' is safe to eat."""

    __safe_to_eat__: ClassVar[frozenset[str]] = frozenset({"beta"})

    alpha: str | None | UnsetType = Field(UNSET, alias="alpha")
    beta: int | None | UnsetType = Field(UNSET, alias="beta")


def _make_caps(
    *,
    type_name: str | None = None,
    fields: frozenset[str] | None = None,
) -> ServerCapabilities:
    """Build a minimal ServerCapabilities for testing."""
    type_names: set[str] = set()
    type_fields_dict: dict[str, frozenset[str]] = {}

    if type_name is not None:
        type_names.add(type_name)
        type_fields_dict[type_name] = fields or frozenset()

    return ServerCapabilities(
        app_schema=75,
        version_string="v0.30.0-test",
        type_names=frozenset(type_names),
        type_fields=MappingProxyType(
            {k: frozenset(v) for k, v in type_fields_dict.items()}
        ),
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestSafeToEatGating:
    """Tests for __safe_to_eat__ capability gating."""

    def test_no_gating_when_capabilities_is_none(self) -> None:
        """to_graphql() passes all fields through when capabilities are None."""
        obj = _GatedInput(alpha="hello", beta=42)

        with patch("stash_graphql_client.types.base.fragment_store") as mock_store:
            mock_store._capabilities = None
            result = obj.to_graphql()

        assert result == {"alpha": "hello", "beta": 42}

    def test_no_gating_when_type_unknown_to_schema(self) -> None:
        """to_graphql() passes all fields through when type is not in schema."""
        obj = _GatedInput(alpha="hello", beta=42)

        # Caps with NO types at all — _GatedInput is unknown
        caps = _make_caps()

        with patch("stash_graphql_client.types.base.fragment_store") as mock_store:
            mock_store._capabilities = caps
            result = obj.to_graphql()

        assert result == {"alpha": "hello", "beta": 42}

    def test_safe_fields_stripped_when_server_lacks_them(self) -> None:
        """Fields in __safe_to_eat__ are stripped when server doesn't have them."""
        obj = _GatedInput(alpha="hello", beta=42)

        # Server knows _GatedInput but only has "alpha", not "beta"
        caps = _make_caps(
            type_name="_GatedInput",
            fields=frozenset({"alpha"}),
        )

        with (
            patch("stash_graphql_client.types.base.fragment_store") as mock_store,
            warnings.catch_warnings(record=True) as caught,
        ):
            warnings.simplefilter("always")
            mock_store._capabilities = caps
            result = obj.to_graphql()

        assert result == {"alpha": "hello"}
        assert "beta" not in result

        # Verify a warning was emitted
        safe_warnings = [w for w in caught if "Server lacks 'beta'" in str(w.message)]
        assert len(safe_warnings) == 1

    def test_safe_fields_pass_through_when_server_supports_them(self) -> None:
        """Fields in __safe_to_eat__ pass through when server supports them."""
        obj = _GatedInput(alpha="hello", beta=42)

        # Server knows _GatedInput with both fields
        caps = _make_caps(
            type_name="_GatedInput",
            fields=frozenset({"alpha", "beta"}),
        )

        with patch("stash_graphql_client.types.base.fragment_store") as mock_store:
            mock_store._capabilities = caps
            result = obj.to_graphql()

        assert result == {"alpha": "hello", "beta": 42}

    def test_unsupported_field_not_in_safe_to_eat_raises(self) -> None:
        """Unsupported field NOT in __safe_to_eat__ raises ValueError."""
        obj = _SimpleInput(alpha="hello", beta=42)

        # Server knows _SimpleInput but only has "alpha" — "beta" is NOT safe to eat
        caps = _make_caps(
            type_name="_SimpleInput",
            fields=frozenset({"alpha"}),
        )

        with patch("stash_graphql_client.types.base.fragment_store") as mock_store:
            mock_store._capabilities = caps
            with pytest.raises(ValueError, match="Server does not support 'beta'"):
                obj.to_graphql()

    def test_unset_fields_excluded_before_gating(self) -> None:
        """UNSET fields are excluded before capability gating runs."""
        obj = _GatedInput(alpha="hello")  # beta stays UNSET

        # Server knows _GatedInput with only "alpha" — "beta" would fail if present
        caps = _make_caps(
            type_name="_GatedInput",
            fields=frozenset({"alpha"}),
        )

        with patch("stash_graphql_client.types.base.fragment_store") as mock_store:
            mock_store._capabilities = caps
            result = obj.to_graphql()

        assert result == {"alpha": "hello"}

    def test_all_fields_supported_no_warnings(self) -> None:
        """No warnings when all fields are supported by the server."""
        obj = _GatedInput(alpha="hello", beta=42)

        caps = _make_caps(
            type_name="_GatedInput",
            fields=frozenset({"alpha", "beta"}),
        )

        with (
            patch("stash_graphql_client.types.base.fragment_store") as mock_store,
            warnings.catch_warnings(record=True) as caught,
        ):
            warnings.simplefilter("always")
            mock_store._capabilities = caps
            obj.to_graphql()

        # Filter for our specific warnings (ignore deprecation warnings etc.)
        gating_warnings = [w for w in caught if "Server lacks" in str(w.message)]
        assert len(gating_warnings) == 0
