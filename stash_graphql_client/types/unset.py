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
    pass


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

__all__ = ["UNSET", "UnsetType"]
