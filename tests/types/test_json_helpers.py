"""Tests for the JSON narrowing helpers in stash_graphql_client.types.json."""

from typing import get_args, get_origin

import pytest
from pydantic import JsonValue as PydanticJsonValue

from stash_graphql_client.types import (
    JsonDict,
    JsonValue,
    expect_dict,
    expect_int,
    expect_list,
    str_or_none,
)


class TestExpectDict:
    def test_returns_same_dict_unchanged(self):
        payload: JsonValue = {"a": 1, "b": [1, 2]}
        assert expect_dict(payload, "payload") is payload

    def test_empty_dict_ok(self):
        assert expect_dict({}, "payload") == {}

    @pytest.mark.parametrize("value", [[], [1], "x", 5, 1.5, True, None])
    def test_non_dict_raises_typeerror(self, value):
        with pytest.raises(TypeError, match="expected payload to be an object"):
            expect_dict(value, "payload")

    def test_error_names_field_and_actual_type(self):
        with pytest.raises(
            TypeError, match="Stash: expected items to be an object, got list"
        ):
            expect_dict([1, 2], "items")


class TestExpectList:
    def test_returns_same_list_unchanged(self):
        items: JsonValue = [1, 2, 3]
        assert expect_list(items, "items") is items

    @pytest.mark.parametrize("value", [{}, {"a": 1}, "x", 5, 1.5, None])
    def test_non_list_raises_typeerror(self, value):
        with pytest.raises(TypeError, match="expected items to be an array"):
            expect_list(value, "items")


class TestExpectInt:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [(5, 5), ("42", 42), (3.9, 3), (True, 1), (False, 0), ("0", 0)],
    )
    def test_int_like_scalars_coerced(self, value, expected):
        assert expect_int(value, "id") == expected

    @pytest.mark.parametrize("value", [None, [], {}, [1]])
    def test_non_scalar_raises_typeerror(self, value):
        with pytest.raises(TypeError, match="expected id to be an int"):
            expect_int(value, "id")


class TestStrOrNone:
    def test_none_passes_through(self):
        assert str_or_none(None) is None

    @pytest.mark.parametrize(
        ("value", "expected"),
        [("hi", "hi"), (5, "5"), (1.5, "1.5"), (True, "True")],
    )
    def test_coerces_to_str(self, value, expected):
        assert str_or_none(value) == expected


class TestJsonAliases:
    def test_jsondict_is_str_to_jsonvalue_mapping(self):
        assert get_origin(JsonDict) is dict
        assert get_args(JsonDict) == (str, JsonValue)

    def test_jsonvalue_is_pydantic_reexport(self):
        assert JsonValue is PydanticJsonValue
