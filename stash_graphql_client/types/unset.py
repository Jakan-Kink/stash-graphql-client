"""UNSET sentinel for three-level field system.

Provides a sentinel value to distinguish between:
- Set to a value: field = "value"
- Set to null: field = None
- Unset/untouched: field = UNSET (default)

This enables partial updates where only modified fields are included in
GraphQL mutations, avoiding the need to send all fields on every update.

Example:
    >>> from stash_graphql_client.types.unset import UNSET
    >>> from stash_graphql_client.types import Scene
    >>>
    >>> # Create a new scene with only title set
    >>> scene = Scene(title="Example")
    >>> scene.title = "Example"  # Set to value
    >>> scene.rating100 = None    # Explicitly set to null
    >>> scene.details = UNSET     # Never touched (default)
    >>>
    >>> # to_input() only includes non-UNSET fields
    >>> input_dict = await scene.to_input()
    >>> # {"title": "Example", "rating100": null}
    >>> # "details" is omitted because it's UNSET
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic_core import core_schema


if TYPE_CHECKING:
    import sys

    # TypeIs is stdlib from 3.13 and in typing_extensions before that. It is only
    # referenced in (stringized) annotations, so it is never imported at runtime;
    # the version split keeps type-checkers correct whether a consumer configures
    # them for 3.12 (the floor) or 3.13+.
    if sys.version_info >= (3, 13):
        from typing import TypeIs
    else:
        from typing_extensions import TypeIs


class UnsetType:
    """Sentinel value representing an unset field.

    Used throughout the type system to indicate a field has never been set,
    as distinct from being explicitly set to None.

    This is a singleton - all instances are the same object.
    """

    _instance: UnsetType | None = None

    def __new__(cls) -> UnsetType:
        """Ensure only one instance of UnsetType exists (singleton pattern)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        """Return string representation of UNSET."""
        return "UNSET"

    def __bool__(self) -> bool:
        """UNSET is always falsy."""
        return False

    def __eq__(self, other: object) -> bool:
        """Check equality - only equal to other UnsetType instances."""
        return isinstance(other, UnsetType)

    def __hash__(self) -> int:
        """Make UNSET hashable for use in sets/dicts."""
        return hash("UNSET")

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: Any
    ) -> core_schema.CoreSchema:
        """Provide Pydantic schema for UnsetType.

        This tells Pydantic to treat UnsetType as a valid type that requires
        no validation - it's just a marker/sentinel value.
        """

        # Define a validator that accepts UnsetType instances
        def validate_unset(value: Any) -> UnsetType:
            if isinstance(value, UnsetType):
                return value
            # Otherwise, this is an error (shouldn't happen in practice)
            raise ValueError(f"Expected UnsetType, got {type(value)}")

        # Use is-instance schema with the validator
        return core_schema.with_info_before_validator_function(
            lambda value, _: validate_unset(value),
            core_schema.is_instance_schema(cls),
            # Provide a serialization schema
            # In JSON mode, serialize as None (will be filtered by to_graphql())
            # In Python mode, return the instance itself
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: None,
                return_schema=core_schema.none_schema(),
                when_used="json",
            ),
        )


# Singleton instance - use this throughout the codebase
UNSET = UnsetType()


def is_set[T](value: T | UnsetType) -> TypeIs[T]:
    """Type guard narrowing away ``UNSET``, leaving the concrete (possibly null) value.

    A ``TypeIs`` guard, so it narrows *both* branches: after ``if is_set(value)`` the
    value is type ``T`` (``UnsetType`` removed); in the ``else`` branch it is
    ``UnsetType``. Use :func:`is_present` to also exclude ``None``.

    Args:
        value: A value that might be UNSET or an actual value of type T.

    Returns:
        True if value is not UNSET, False if value is UNSET.

    Example:
        >>> from stash_graphql_client.types import Scene, is_set
        >>> scene = Scene(id="1", title="Test", scenes=[])
        >>> if is_set(scene.scenes):
        ...     scene_obj in scene.scenes  # type checker knows scenes is list[Scene]

    Note:
        At runtime this is equivalent to ``value is not UNSET``.
    """
    return value is not UNSET


def is_unset[T](value: T | UnsetType) -> TypeIs[UnsetType]:
    """Type guard narrowing to ``UnsetType`` - the dual of :func:`is_set`.

    A ``TypeIs`` guard, so the ``else`` branch narrows too: after
    ``if is_unset(value): ...`` the value is ``UnsetType``; past an early return the
    value is type ``T``. This enables a guard-clause style without wrapping each later
    access::

        if is_unset(scene.path):
            return
        PurePath(scene.path)  # narrowed to str - no is_set/present wrapper needed

    Args:
        value: A value that might be UNSET or an actual value of type T.

    Returns:
        True if value is UNSET, False otherwise.

    Note:
        At runtime this is equivalent to ``value is UNSET``.
    """
    return value is UNSET


def is_present[T](value: T | None | UnsetType) -> TypeIs[T]:
    """Type guard narrowing a three-state field to a concrete, non-null value.

    Like :func:`is_set`, but also excludes ``None``: after ``is_present(value)`` a
    static type checker knows the value is neither ``UNSET`` nor ``None`` and can be
    treated as type ``T``. As a ``TypeIs`` guard it also narrows the ``else`` branch
    (to ``None | UnsetType``). Useful for the ``T | None | UnsetType`` entity fields
    where a single ``assert is_present(field)`` replaces a two-step
    ``is_set(field)`` + ``field is not None`` narrowing.

    Args:
        value: A three-state value that might be UNSET, None, or a value of type T.

    Returns:
        True if value is neither UNSET nor None.

    Example:
        >>> from stash_graphql_client.types import Scene, is_present
        >>> scene = Scene(id="1", tags=[])
        >>> if is_present(scene.tags):
        ...     tag in scene.tags  # OK: type checker knows scene.tags is list[Tag]
    """
    return value is not UNSET and value is not None


def present[T](value: T | None | UnsetType) -> T:
    """Return a three-state field's concrete value, requiring it be set and non-null.

    The value-returning counterpart of :func:`is_present`: use it inline where a
    queried, non-null field is expected, e.g. ``present(obj.tags)[0]`` or
    ``x in present(obj.tags)``. Unlike an ``assert is_present(...)`` it re-narrows at
    each call site, so it is robust where a static checker would otherwise drop
    attribute narrowing (e.g. across an intervening ``await``). Raises if the value
    is ``UNSET`` or ``None`` so bad data never passes silently.

    Args:
        value: A three-state value that should be a real value of type T.

    Returns:
        The value, narrowed to T.

    Raises:
        ValueError: If the value is UNSET or None.
    """
    if isinstance(value, UnsetType):
        raise ValueError("present(): value is UNSET (field was not queried)")
    if value is None:
        raise ValueError("present(): value is None")
    return value


__all__ = ["UNSET", "UnsetType", "is_present", "is_set", "is_unset", "present"]
