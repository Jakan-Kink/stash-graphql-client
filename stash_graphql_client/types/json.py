"""JSON value typing and runtime narrowing helpers.

GraphQL responses are JSON, so response payloads are naturally typed as
``JsonValue`` / ``JsonDict`` rather than ``Any``. The ``expect_*`` helpers
narrow a ``JsonValue`` to a concrete shape at runtime, raising ``TypeError``
when the server delivers something other than the expected JSON type.
"""

from __future__ import annotations

from pydantic import JsonValue  # re-exported for ergonomics (Pydantic v2 type)


__all__ = [
    "JsonDict",
    "JsonValue",
    "expect_dict",
    "expect_int",
    "expect_list",
    "str_or_none",
]

# A JSON object; one level narrower than JsonValue (also admits arrays/scalars).
JsonDict = dict[str, JsonValue]


def expect_dict(value: JsonValue, what: str) -> JsonDict:
    """Narrow a JSON value to an object, or raise a precise TypeError.

    Args:
        value: The JSON value to narrow.
        what: Human-readable field name, used in the error message.

    Returns:
        The value as a JsonDict.

    Raises:
        TypeError: If value is not a dict.
    """
    if not isinstance(value, dict):
        raise TypeError(
            f"Stash: expected {what} to be an object, got {type(value).__name__}"
        )
    return value


def expect_list(value: JsonValue, what: str) -> list[JsonValue]:
    """Narrow a JSON value to an array, or raise a precise TypeError.

    Args:
        value: The JSON value to narrow.
        what: Human-readable field name, used in the error message.

    Returns:
        The value as a list of JsonValue.

    Raises:
        TypeError: If value is not a list.
    """
    if not isinstance(value, list):
        raise TypeError(
            f"Stash: expected {what} to be an array, got {type(value).__name__}"
        )
    return value


def expect_int(value: JsonValue, what: str) -> int:
    """Narrow a JSON scalar to an int, or raise a precise TypeError.

    Accepts the int-like scalars Stash delivers (str/int/float/bool); a
    container or None means the field was not the id-like scalar expected.

    Args:
        value: The JSON value to narrow.
        what: Human-readable field name, used in the error message.

    Returns:
        The value coerced to int.

    Raises:
        TypeError: If value is not an int-like scalar.
    """
    if isinstance(value, (str, int, float)):
        return int(value)
    raise TypeError(f"Stash: expected {what} to be an int, got {type(value).__name__}")


def str_or_none(value: JsonValue) -> str | None:
    """Coerce an optional JSON string field to str, preserving None.

    Args:
        value: The JSON value to coerce.

    Returns:
        None if value is None, otherwise str(value).
    """
    return None if value is None else str(value)
