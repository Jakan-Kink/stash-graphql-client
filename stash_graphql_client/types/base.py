"""Base types for Stash models.

Note: While this is not a schema interface, it represents a common pattern
in the schema where many types have an id field. This includes core types
like Scene, Gallery, Performer, etc., and file types like VideoFile,
ImageFile, etc.

We use this interface to provide common functionality for these types, even
though the schema doesn't explicitly define an interface for them.

All StashObject types include created_at and updated_at timestamp fields
which are managed by Stash but returned in API responses.
"""

from __future__ import annotations

import inspect
from datetime import datetime
from typing import TYPE_CHECKING, Any, ClassVar, TypeVar

from pydantic import BaseModel, ConfigDict

from stash_graphql_client.logging import client_logger as log


if TYPE_CHECKING:
    from collections.abc import Callable

    from stash_graphql_client.client import StashClient
    from stash_graphql_client.types.enums import BulkUpdateIdMode

T = TypeVar("T", bound="StashObject")


class BulkUpdateIds(BaseModel):
    """Input for bulk ID updates."""

    ids: list[str]  # [ID!]!
    mode: BulkUpdateIdMode  # BulkUpdateIdMode!


class BulkUpdateStrings(BaseModel):
    """Input for bulk string updates."""

    values: list[str]  # [String!]!
    mode: BulkUpdateIdMode  # BulkUpdateIdMode!


class StashObject(BaseModel):
    """Base interface for our Stash model implementations.

    While this is not a schema interface, it represents a common pattern in the
    schema where many types have id, created_at, and updated_at fields. We use
    this interface to provide common functionality for these types.

    Common fields (matching schema pattern):
    - id: Unique identifier (ID!)
    - created_at: When the object was created (Time!) - managed by Stash
    - updated_at: When the object was last updated (Time!) - managed by Stash

    Common functionality provided:
    - find_by_id: Find object by ID
    - save: Save object to Stash
    - to_input: Convert to GraphQL input type
    - is_dirty: Check if object has unsaved changes
    - mark_clean: Mark object as having no unsaved changes
    - mark_dirty: Mark object as having unsaved changes
    """

    # GraphQL type name (e.g., "Scene", "Performer")
    __type_name__: ClassVar[str]

    # Input type for updates (e.g., SceneUpdateInput, PerformerUpdateInput)
    __update_input_type__: ClassVar[type[BaseModel]]

    # Input type for creation (e.g., SceneCreateInput, PerformerCreateInput)
    # Optional - if not set, the type doesn't support creation
    __create_input_type__: ClassVar[type[BaseModel] | None] = None

    # Fields to include in queries
    __field_names__: ClassVar[set[str]]

    # Fields to track for changes
    __tracked_fields__: ClassVar[set[str]] = set()

    # Relationship mappings for converting to input types
    __relationships__: ClassVar[
        dict[str, tuple[str, bool, Callable[[Any], Any] | None]]
    ] = {}

    # Field conversion functions
    __field_conversions__: ClassVar[dict[str, Callable[[Any], Any]]] = {}

    # Pydantic configuration
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="allow",  # Allow extra fields for flexibility
        validate_assignment=True,  # Validate on attribute assignment
    )

    # Note: _snapshot stored in __pydantic_private__ (not serialized)

    # Required field
    id: str  # ID!

    # Timestamp fields - managed by Stash, returned in API responses
    # These are optional because they may not be present in all API responses
    # (e.g., when creating a new object before it's saved)
    created_at: datetime | None = None  # Time!
    updated_at: datetime | None = None  # Time!

    def __init__(self, **kwargs: Any) -> None:
        """Initialize object with kwargs.

        Pydantic handles field validation and initialization.
        """
        super().__init__(**kwargs)

    def model_post_init(self, _context: Any) -> None:
        """Initialize object and store snapshot after Pydantic init.

        This is called by Pydantic after all fields are initialized, so it's
        the right place to capture the initial state for dirty tracking.

        Args:
            _context: Pydantic context (unused but required by signature)
        """
        # Store snapshot of initial state using Pydantic's serialization
        # This leverages Pydantic's tested model_dump() which handles
        # nested objects, lists, and complex types correctly
        self._snapshot = self.model_dump()

    def is_dirty(self) -> bool:
        """Check if object has unsaved changes.

        Returns:
            True if object has unsaved changes (current state != snapshot)
        """
        return self.model_dump() != self._snapshot

    def get_changed_fields(self) -> dict[str, Any]:
        """Get fields that have changed since last snapshot.

        Returns:
            Dictionary of field names to current values for changed fields
        """
        current = self.model_dump()
        changed = {}

        for field in self.__tracked_fields__:
            if field not in current:
                continue

            # Field was added after snapshot
            if field not in self._snapshot:
                changed[field] = current[field]
                continue

            # Field value changed
            if current[field] != self._snapshot[field]:
                changed[field] = current[field]

        return changed

    def mark_clean(self) -> None:
        """Mark object as having no unsaved changes.

        Updates the snapshot to match the current state.
        """
        self._snapshot = self.model_dump()

    def mark_dirty(self) -> None:
        """Mark object as having unsaved changes.

        Clears the snapshot to force all tracked fields to be considered dirty.
        """
        self._snapshot = {}

    @classmethod
    def _get_field_names(cls) -> set[str]:
        """Get field names from Pydantic model definition.

        Returns:
            Set of field names to include in queries
        """
        if not hasattr(cls, "__field_names__"):
            # Try to get all fields from Pydantic model
            try:
                # Get field names from Pydantic's model_fields
                field_names = set(cls.model_fields.keys())

                # Defensive fallback if no fields were successfully extracted
                if not field_names:
                    cls.__field_names__ = {"id"}
                else:
                    cls.__field_names__ = field_names
            except (AttributeError, TypeError):
                # Fallback if model fields is not available
                cls.__field_names__ = {"id"}  # At minimum, include id field
        return cls.__field_names__

    @classmethod
    async def find_by_id(
        cls: type[T],
        client: StashClient,
        id: str,
    ) -> T | None:
        """Find object by ID.

        Args:
            client: StashClient instance
            id: Object ID

        Returns:
            Object instance if found, None otherwise
        """
        # Circular import: fragments uses types for GraphQL schema definitions
        from stash_graphql_client import fragments

        # Map type names to their corresponding find queries
        query_map = {
            "Scene": fragments.FIND_SCENE_QUERY,
            "Performer": fragments.FIND_PERFORMER_QUERY,
            "Studio": fragments.FIND_STUDIO_QUERY,
            "Tag": fragments.FIND_TAG_QUERY,
            "Gallery": fragments.FIND_GALLERY_QUERY,
            "Image": fragments.FIND_IMAGE_QUERY,
            "SceneMarker": fragments.FIND_MARKER_QUERY,
        }

        # Get the appropriate query for this type
        query = query_map.get(cls.__type_name__)
        if not query:
            # Fallback to manual query building for types not in fragments
            fields = " ".join(cls._get_field_names())
            query = f"""
                query Find{cls.__type_name__}($id: ID!) {{
                    find{cls.__type_name__}(id: $id) {{
                        {fields}
                    }}
                }}
            """

        try:
            result = await client.execute(query, {"id": id})
            data = result[f"find{cls.__type_name__}"]
            return cls(**data) if data else None
        except Exception:
            return None

    async def save(self, client: StashClient) -> None:
        """Save object to Stash.

        Args:
            client: StashClient instance

        Raises:
            ValueError: If save fails
        """
        # Skip save if object is not dirty and not new
        if not self.is_dirty() and hasattr(self, "id") and self.id != "new":
            return

        # Get input data
        try:
            input_data = await self.to_input()
            # Ensure input_data is a plain dict
            if not isinstance(input_data, dict):
                raise ValueError(
                    f"to_input() must return a dict, got {type(input_data)}"
                )

            # For existing objects, if only ID is present, no actual changes to save
            if (
                hasattr(self, "id")
                and self.id != "new"
                and set(input_data.keys()) <= {"id"}
            ):
                log.debug(f"No changes to save for {self.__type_name__} {self.id}")
                self.mark_clean()  # Mark as clean since there are no changes
                return

            is_update = hasattr(self, "id") and self.id != "new"
            operation = "Update" if is_update else "Create"
            type_name = self.__type_name__

            # Generate consistent camelCase operation key
            operation_key = f"{type_name[0].lower()}{type_name[1:]}{operation}"
            mutation = f"""
                mutation {operation}{type_name}($input: {type_name}{operation}Input!) {{
                    {operation_key}(input: $input) {{
                        id
                    }}
                }}
            """

            result = await client.execute(mutation, {"input": input_data})

            # Extract the result using the same camelCase key
            if operation_key not in result:
                raise ValueError(f"Missing '{operation_key}' in response: {result}")

            operation_result = result[operation_key]
            if operation_result is None:
                raise ValueError(f"{operation} operation returned None")

            # Update ID for new objects
            if not is_update:
                self.id = operation_result["id"]

            # Mark object as clean after successful save
            self.mark_clean()

        except Exception as e:
            raise ValueError(f"Failed to save {self.__type_name__}: {e}") from e

    @staticmethod
    async def _get_id(obj: Any) -> str | None:
        """Get ID from object or dict.

        Args:
            obj: Object to get ID from

        Returns:
            ID if found, None otherwise
        """
        if isinstance(obj, dict):
            return obj.get("id")
        if hasattr(obj, "awaitable_attrs"):
            await obj.awaitable_attrs.id
        return getattr(obj, "id", None)

    async def _process_single_relationship(
        self, value: Any, transform: Callable[[Any], Any] | None
    ) -> str | None:
        """Process a single relationship.

        Args:
            value: Value to transform
            transform: Transform function to apply

        Returns:
            Transformed value if successful, None otherwise
        """
        if not value:
            return None
        if transform is not None:
            # Check if transform is async or sync
            if inspect.iscoroutinefunction(transform):
                result = await transform(value)
            else:
                result = transform(value)
            # Ensure we return str | None as declared
            return str(result) if result is not None else None
        return None

    async def _process_list_relationship(
        self, value: list[Any], transform: Callable[[Any], Any] | None
    ) -> list[str]:
        """Process a list relationship.

        Args:
            value: List of values to transform
            transform: Transform function to apply

        Returns:
            List of transformed values
        """
        if not value:
            return []

        items = []
        for item in value:
            if transform is not None:
                # Check if transform is async or sync
                if inspect.iscoroutinefunction(transform):
                    transformed = await transform(item)
                else:
                    transformed = transform(item)
                if transformed:
                    # Ensure we append a string to the list
                    items.append(str(transformed))
        return items

    async def _process_relationships(
        self, fields_to_process: set[str]
    ) -> dict[str, Any]:
        """Process relationships according to their mappings.

        Args:
            fields_to_process: Set of field names to process

        Returns:
            Dictionary of processed relationships
        """
        data: dict[str, Any] = {}

        for rel_field in fields_to_process:
            # Skip if field is not a relationship or doesn't exist
            if rel_field not in self.__relationships__ or not hasattr(self, rel_field):
                continue

            # Get relationship mapping
            mapping = self.__relationships__[rel_field]
            target_field, is_list = mapping[:2]
            # Use explicit transform if provided and not None, otherwise use default _get_id
            transform = (
                mapping[2]
                if len(mapping) >= 3 and mapping[2] is not None
                else self._get_id
            )

            # Get and process value
            value = getattr(self, rel_field)
            if is_list:
                items = await self._process_list_relationship(value, transform)
                if items:
                    data[target_field] = items
            else:
                transformed = await self._process_single_relationship(value, transform)
                if transformed:
                    data[target_field] = transformed

        return data

    async def _process_fields(self, fields_to_process: set[str]) -> dict[str, Any]:
        """Process fields according to their converters.

        Args:
            fields_to_process: Set of field names to process

        Returns:
            Dictionary of processed fields
        """
        data = {}
        for field in fields_to_process:
            if field not in self.__field_conversions__:
                continue

            if hasattr(self, field):
                value = getattr(self, field)
                if value is not None:
                    try:
                        converter = self.__field_conversions__[field]
                        if converter is not None and callable(converter):
                            converted = converter(value)
                            if converted is not None:
                                data[field] = converted
                    except (ValueError, TypeError, ArithmeticError):
                        pass

        return data

    async def to_input(self) -> dict[str, Any]:
        """Convert to GraphQL input type.

        Returns:
            Dictionary of input fields that have changed (are dirty) plus required fields.
            For new objects (id="new"), all fields are included.
        """
        # For new objects, include all fields
        is_new = not hasattr(self, "id") or self.id == "new"
        input_obj = (
            await self._to_input_all() if is_new else await self._to_input_dirty()
        )

        # Serialize to dict - single point of serialization
        result_dict: dict[str, Any] = input_obj.model_dump(
            exclude_none=True, exclude={"client_mutation_id"}
        )
        log.debug(f"Converted {self.__type_name__} to input: {result_dict}")
        return result_dict

    async def _to_input_all(self) -> BaseModel:
        """Convert all fields to input type.

        Returns:
            Validated Pydantic input object (CreateInput or UpdateInput)

        Raises:
            ValueError: If creation is not supported and object has no ID
        """
        # Process all fields
        data = await self._process_fields(set(self.__field_conversions__.keys()))

        # Process all relationships
        rel_data = await self._process_relationships(set(self.__relationships__.keys()))
        data.update(rel_data)

        # Determine if this is a create or update operation
        is_new = not hasattr(self, "id") or self.id == "new"

        # If this is a create operation but creation isn't supported, raise an error
        if is_new and not self.__create_input_type__:
            raise ValueError(
                f"{self.__type_name__} objects cannot be created, only updated"
            )

        # Use the appropriate input type
        input_type = (
            self.__create_input_type__ if is_new else self.__update_input_type__
        )
        if input_type is None:
            if is_new:
                raise ValueError(
                    f"{self.__type_name__} objects cannot be created, only updated"
                )
            raise NotImplementedError("__update_input_type__ cannot be None")

        # Return validated Pydantic object
        return input_type(**data)

    async def _to_input_dirty(self) -> BaseModel:
        """Convert only dirty fields to input type.

        Uses snapshot-based change detection to identify modified fields.

        Returns:
            Validated Pydantic UpdateInput object with dirty fields plus ID
        """
        if (
            not hasattr(self, "__update_input_type__")
            or self.__update_input_type__ is None
        ):
            raise NotImplementedError("Subclass must define __update_input_type__")

        # Start with ID which is always required for updates
        data = {"id": self.id}

        # Get dirty fields using snapshot comparison
        # This leverages Pydantic's model_dump() for accurate change detection
        dirty_fields = set(self.get_changed_fields().keys())

        # Process dirty regular fields
        field_data = await self._process_fields(dirty_fields)
        data.update(field_data)

        # Process dirty relationships
        rel_data = await self._process_relationships(dirty_fields)
        data.update(rel_data)

        # Convert to update input type
        update_input_type = self.__update_input_type__
        if update_input_type is None:
            raise NotImplementedError("__update_input_type__ cannot be None")

        # Return validated Pydantic object
        return update_input_type(**data)

    def __hash__(self) -> int:
        """Make object hashable based on type and ID.

        Returns:
            Hash of (type_name, id)
        """
        return hash((self.__type_name__, self.id))

    def __eq__(self, other: object) -> bool:
        """Compare objects based on type and ID.

        Args:
            other: Object to compare with

        Returns:
            True if objects are equal
        """
        if not isinstance(other, StashObject):
            return NotImplemented
        return (self.__type_name__, self.id) == (other.__type_name__, other.id)
