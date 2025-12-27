"""Tests for UNSET sentinel and is_set TypeGuard."""

import pytest

from stash_graphql_client.types import UNSET, UnsetType, is_set


class TestUnsetType:
    """Test UnsetType sentinel behavior."""

    def test_unset_is_singleton(self):
        """Test that UNSET is a singleton - all instances are the same object."""
        another_unset = UnsetType()
        assert UNSET is another_unset
        assert id(UNSET) == id(another_unset)

    def test_unset_repr(self):
        """Test UNSET string representation."""
        assert repr(UNSET) == "UNSET"
        assert str(UNSET) == "UNSET"

    def test_unset_is_falsy(self):
        """Test that UNSET is falsy like None."""
        assert not UNSET
        assert bool(UNSET) is False

    def test_unset_equality(self):
        """Test UNSET equality checks."""
        assert UNSET == UNSET  # noqa: PLR0124
        assert UnsetType() == UNSET
        assert UNSET != None  # noqa: E711
        assert UNSET != 0
        assert UNSET != False  # noqa: E712
        assert UNSET != ""

    def test_unset_hashable(self):
        """Test that UNSET can be used in sets and dicts."""
        # Should not raise
        unset_set = {UNSET, "value"}
        assert UNSET in unset_set

        unset_dict = {UNSET: "unset_value", "key": "value"}
        assert unset_dict[UNSET] == "unset_value"


class TestIsSetTypeGuard:
    """Test is_set() TypeGuard function."""

    def test_is_set_returns_false_for_unset(self):
        """Test that is_set returns False for UNSET."""
        assert is_set(UNSET) is False

    def test_is_set_returns_true_for_none(self):
        """Test that is_set returns True for None (None is a set value)."""
        assert is_set(None) is True

    def test_is_set_returns_true_for_values(self):
        """Test that is_set returns True for actual values."""
        assert is_set("value") is True
        assert is_set(0) is True
        assert is_set(False) is True
        assert is_set([]) is True
        assert is_set({}) is True
        assert is_set(42) is True

    def test_is_set_equivalent_to_is_not_unset(self):
        """Test that is_set(value) is equivalent to value is not UNSET."""
        values = [UNSET, None, "", 0, False, [], {}, "value", 42]

        for value in values:
            assert is_set(value) == (not isinstance(value, UnsetType))

    def test_is_set_with_list_field(self):
        """Test is_set with list fields (common pattern in types)."""
        from stash_graphql_client.types import Scene

        # Scene with empty list (set)
        scene1 = Scene(id="1", title="Test", tags=[], organized=False, urls=[])
        assert is_set(scene1.tags) is True

        # Scene with UNSET tags (unset)
        scene2 = Scene.model_construct(id="2", title="Test", tags=UNSET)
        assert is_set(scene2.tags) is False

    def test_is_set_enables_type_narrowing(self):
        """Test that is_set enables type narrowing in control flow.

        This test verifies the runtime behavior. Type checkers like Pylance
        will use the TypeGuard to narrow types statically.
        """
        from stash_graphql_client.types import Scene

        scene = Scene(id="1", title="Test", tags=[], organized=False, urls=[])

        # Using is_set for type narrowing
        if is_set(scene.tags):
            # At this point, type checkers know scene.tags is list[Tag]
            # not list[Tag] | UnsetType
            assert isinstance(scene.tags, list)
            assert len(scene.tags) == 0  # No type error

        # With UNSET tags
        scene2 = Scene.model_construct(id="2", title="Test", tags=UNSET)

        if is_set(scene2.tags):
            pytest.fail("Should not enter this block when tags is UNSET")
        else:
            # This branch is taken
            assert isinstance(scene2.tags, UnsetType)
