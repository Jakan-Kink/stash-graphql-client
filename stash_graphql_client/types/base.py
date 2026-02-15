"""Base types for Stash models.

Note: While this is not a schema interface, it represents a common pattern
in the schema where many types have an id field. This includes core types
like Scene, Gallery, Performer, etc., and file types like VideoFile,
ImageFile, etc.

We use this interface to provide common functionality for these types, even
though the schema doesn't explicitly define an interface for them.

Note: created_at and updated_at are handled by Stash internally and not
included in this interface.

Three-Level Field System:
-------------------------
This module implements a three-level field system using the UNSET sentinel:

1. Set to a value: field = "example"
2. Set to null: field = None
3. Unset/untouched: field = UNSET (default)

This enables partial updates where only modified fields are included in
GraphQL mutations, avoiding the need to send all fields on every update.

UUID4 for New Objects:
---------------------
New objects automatically receive a UUID4 identifier when created without an ID.
This temporary ID is replaced with the server-assigned ID after save operations.

Example:
    >>> scene = Scene(title="Example")  # Auto-generates UUID4 for scene.id
    >>> scene.is_new()  # True
    >>> await scene.save(client)  # Server assigns real ID
    >>> scene.is_new()  # False
"""

from __future__ import annotations

import inspect
import types
import uuid
import warnings
from typing import TYPE_CHECKING, Any, ClassVar, Self, TypeVar, get_args, get_origin

from pydantic import (
    BaseModel,
    ConfigDict,
    ModelWrapValidatorHandler,
    PrivateAttr,
    ValidationInfo,
    model_validator,
)

from stash_graphql_client import fragments
from stash_graphql_client.errors import StashIntegrationError, StashUnmappedFieldWarning
from stash_graphql_client.logging import client_logger as log
from stash_graphql_client.types.scalars import Time
from stash_graphql_client.types.unset import UNSET, UnsetType, is_set


if TYPE_CHECKING:
    from collections.abc import Callable

    from stash_graphql_client.client import StashClient
    from stash_graphql_client.store import StashEntityStore
    from stash_graphql_client.types.enums import BulkUpdateIdMode

T = TypeVar("T", bound="StashObject")


# =============================================================================
# Relationship Metadata
# =============================================================================


class RelationshipMetadata:
    """Metadata describing a bidirectional relationship between Stash entity types.

    All relationships in Stash auto-sync bidirectionally via backend referential
    integrity. This metadata documents how to read/write each relationship and
    provides information for convenience helpers.

    Attributes:
        target_field: Field name in *UpdateInput/*CreateInput (e.g., 'gallery_ids')
        is_list: True for many-to-many, False for many-to-one
        transform: Optional transform function for complex types (e.g., StashID → StashIDInput)
        query_field: Field name when reading (e.g., 'galleries'). Defaults to relationship name.
        inverse_type: Type of the related entity (e.g., 'Gallery' as string to avoid circular imports)
        inverse_query_field: Field name on inverse type (e.g., 'scenes' on Gallery)
        query_strategy: How to query the inverse relationship
        filter_query_hint: For filter_query strategy, example filter usage
        auto_sync: Backend maintains referential integrity (always True for Stash)
        notes: Additional implementation notes or caveats

    Query Strategies:
        - 'direct_field': Use nested field (e.g., gallery.scenes)
        - 'filter_query': Use find* with filter (e.g., findScenes(scene_filter))
        - 'complex_object': Nested object with metadata (e.g., group.sub_groups[].group)

    Example:
        >>> from stash_graphql_client.types import RelationshipMetadata
        >>>
        >>> # Simple many-to-many with direct field
        >>> galleries_rel = RelationshipMetadata(
        ...     target_field="gallery_ids",
        ...     is_list=True,
        ...     query_field="galleries",
        ...     inverse_type="Gallery",
        ...     inverse_query_field="scenes",
        ...     query_strategy="direct_field",
        ... )
        >>>
        >>> # Many-to-one with filter query
        >>> studio_rel = RelationshipMetadata(
        ...     target_field="studio_id",
        ...     is_list=False,
        ...     query_field="studio",
        ...     inverse_type="Studio",
        ...     query_strategy="filter_query",
        ...     filter_query_hint='findScenes(scene_filter={studios: {value: [studio_id]}})',
        ... )
    """

    def __init__(
        self,
        target_field: str,
        is_list: bool,
        transform: Callable[[Any], Any] | None = None,
        *,
        query_field: str | None = None,
        inverse_type: str | type | None = None,
        inverse_query_field: str | None = None,
        query_strategy: str = "direct_field",
        filter_query_hint: str | None = None,
        auto_sync: bool = True,
        notes: str = "",
    ):
        """Initialize relationship metadata.

        Args:
            target_field: Field name in *UpdateInput/*CreateInput
            is_list: True for many-to-many, False for many-to-one
            transform: Optional transform function for complex types
            query_field: Field name when reading. Defaults to smart conversion of target_field.
            inverse_type: Type of the related entity (string or type)
            inverse_query_field: Field name on inverse type
            query_strategy: How to query inverse ('direct_field', 'filter_query', 'complex_object')
            filter_query_hint: Example filter usage for filter_query strategy
            auto_sync: Backend maintains referential integrity (always True)
            notes: Additional implementation notes
        """
        self.target_field = target_field
        self.is_list = is_list
        self.transform = transform

        # Auto-derive query_field if not provided
        if query_field is None:
            # Convert studio_id → studio, gallery_ids → galleries, etc.
            if target_field.endswith("_ids"):
                query_field = target_field[:-4] + "s"  # gallery_ids → galleries
            elif target_field.endswith("_id"):
                query_field = target_field[:-3]  # studio_id → studio
            else:
                query_field = target_field  # Already correct (e.g., stash_ids)

        self.query_field = query_field
        self.inverse_type = inverse_type
        self.inverse_query_field = inverse_query_field
        self.query_strategy = query_strategy
        self.filter_query_hint = filter_query_hint
        self.auto_sync = auto_sync
        self.notes = notes

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"RelationshipMetadata("
            f"target_field={self.target_field!r}, "
            f"query_field={self.query_field!r}, "
            f"strategy={self.query_strategy!r})"
        )

    def to_tuple(self) -> tuple[str, bool, Callable[[Any], Any] | None]:
        """Convert to legacy tuple format for backward compatibility.

        Returns:
            (target_field, is_list, transform)
        """
        return (self.target_field, self.is_list, self.transform)


class FromGraphQLMixin:
    """Mixin for types that can be returned directly from GraphQL queries.

    This includes:
    - Result types (FindScenesResultType, etc.)
    - Entity types returned by find{Type}(id) queries (Scene, Performer, etc.)
    - System types (StashConfig, SystemStatus, etc.)
    """

    @classmethod
    def from_graphql(cls: type[T], data: dict[str, Any]) -> T:  # type: ignore[misc]
        """Deserialize from GraphQL response data.

        This method provides symmetric deserialization to complement
        StashInput.to_graphql(). It's functionally equivalent to
        model_validate() but provides clearer intent.

        Recursively processes nested StashObject dicts to ensure they
        also have _received_fields tracking.

        Args:
            data: Dictionary from GraphQL response

        Returns:
            Instance of the type with data validated

        Raises:
            ValueError: If __typename doesn't match the class name
        """
        # Validate __typename matches class name (if present in data)
        # This ensures type safety when explicitly deserializing to a specific type
        # For polymorphic types (interfaces/unions), allow concrete implementations
        if isinstance(data, dict) and "__typename" in data:
            expected = cls.__name__
            actual = data["__typename"]
            # Check if this might be polymorphic (interface/union with subclasses)
            # If the class has subclasses, allow different __typename (field validators will handle it)
            if actual != expected and not cls.__subclasses__():
                raise ValueError(
                    f"Type mismatch: Attempting to deserialize {actual} as {expected}"
                )

        # Recursively process nested StashObject dicts
        processed_data = cls._process_nested_graphql(data)

        # Mark this data as coming from GraphQL for _received_fields tracking
        return cls.model_validate(processed_data, context={"from_graphql": True})  # type: ignore[attr-defined]

    @classmethod
    def _process_nested_graphql(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Recursively process nested dicts that should be StashObjects.

        Args:
            data: Dictionary potentially containing nested StashObject dicts

        Returns:
            Dictionary with nested dicts preprocessed via from_graphql
        """
        processed: dict[str, Any] = {}

        for field_name, value in data.items():
            if value is None:
                processed[field_name] = value
                continue

            # Check if this field should be a StashObject type
            if field_name in cls.model_fields:  # type: ignore[attr-defined]
                field_info = cls.model_fields[field_name]  # type: ignore[attr-defined]
                annotation = field_info.annotation

                # Handle Optional[Type], Type | None, and List[Type]
                origin = get_origin(annotation)
                args = get_args(annotation)

                # For Union types (created with | syntax in modern Python)
                if origin is types.UnionType:
                    # Filter out None and UnsetType to get the actual type
                    non_none_args = [
                        arg
                        for arg in args
                        if arg is not type(None) and arg is not UnsetType
                    ]
                    if len(non_none_args) == 1:
                        annotation = non_none_args[0]
                        # Re-check origin and args for the unwrapped annotation
                        origin = get_origin(annotation)
                        args = get_args(annotation) if origin else ()

                # For List[Type]
                if origin is list and args and isinstance(value, list):
                    item_type = args[0]
                    if isinstance(item_type, type) and issubclass(
                        item_type, StashObject
                    ):
                        # Process list items through from_graphql
                        processed[field_name] = [
                            item_type.from_graphql(item)
                            if isinstance(item, dict)
                            else item
                            for item in value
                        ]
                        continue

                # Single StashObject field
                if (
                    isinstance(annotation, type)
                    and issubclass(annotation, StashObject)
                    and isinstance(value, dict)
                ):
                    processed[field_name] = annotation.from_graphql(value)
                    continue

            processed[field_name] = value

        return processed

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:  # type: ignore[misc]
        """Alias for from_graphql() for backwards compatibility.

        Args:
            data: Dictionary from GraphQL response

        Returns:
            Instance of the type with data validated
        """
        return cls.from_graphql(data)  # type: ignore[arg-type,misc]


class StashInput(BaseModel):
    """Base class for all Stash GraphQL input types.

    Configures Pydantic to accept both Python snake_case field names
    and GraphQL camelCase aliases during construction, while serializing
    to camelCase for GraphQL using Field aliases and by_alias=True.

    This allows tests and Python code to use Pythonic naming conventions
    while ensuring GraphQL compatibility.

    Example:
        ```python
        class MyInput(StashInput):
            my_field: str = Field(alias="myField")

        # Both work during construction:
        MyInput(my_field="value")    # Python style
        MyInput(myField="value")     # GraphQL style

        # Serialization always uses GraphQL style:
        obj.to_graphql()  # {"myField": "value"}
        ```
    """

    model_config = ConfigDict(
        populate_by_name=True,
        # Custom serializer to skip UNSET values during JSON serialization
        ser_json_inf_nan="constants",  # Not related, but good practice
        extra="allow",  # Allow extra fields but warn about them (see validator below)
    )

    @model_validator(mode="before")
    @classmethod
    def _warn_extra_fields(cls, data: Any) -> Any:
        """Emit deprecation warning for unknown fields.

        In v0.11.0, we emit warnings for unknown fields to help users identify typos.
        In v0.12.0+, unknown fields will be rejected with ValidationError (extra="forbid").

        This gives users at least one full release cycle to fix field name typos
        before they become hard errors.
        """
        if not isinstance(data, dict):
            return data

        # Get known field names (both Python snake_case and GraphQL camelCase aliases)
        known_fields = set()
        for field_name, field_info in cls.model_fields.items():
            known_fields.add(field_name)  # Python name (e.g., "tag_ids")
            if field_info.alias:
                known_fields.add(field_info.alias)  # GraphQL alias (e.g., "tagIds")

        # Find extra fields that aren't recognized, excluding internal fields
        # (e.g., __typename from GraphQL introspection) — mirrors sanitize_model_data()
        extra_fields = {
            k for k in set(data.keys()) - known_fields if not k.startswith("_")
        }

        if extra_fields:
            warnings.warn(
                f"{cls.__name__}: Unknown fields will be rejected in v0.12.0: "
                f"{', '.join(sorted(extra_fields))}. "
                f"Please check for typos or outdated field names. "
                f"Common mistakes: 'tag_id' should be 'tag_ids' (plural), "
                f"'performer_id' should be 'performer_ids' (plural).",
                DeprecationWarning,
                stacklevel=4,  # Points to user's code, not this validator
            )

        return data

    def to_graphql(self) -> dict[str, Any]:
        """Convert to GraphQL-compatible dictionary.

        Excludes UNSET sentinel values but keeps None (null) values.
        This allows:
        - UNSET fields to be omitted from the request (not sent to GraphQL)
        - None fields to explicitly clear/null values in GraphQL
        - Regular values to be sent normally

        Returns:
            Dictionary ready to send to GraphQL API with camelCase field names

        Example:
            ```python
            from .unset import UNSET

            input_obj = SceneUpdateInput(
                title="New Title",  # Send this value
                rating=None,         # Send null (clear rating)
                url=UNSET            # Don't send at all
            )
            result = input_obj.to_graphql()
            # {'title': 'New Title', 'rating': None}  # url excluded
            ```
        """
        # Build exclude set using Python field names (not aliases)
        # Pydantic's exclude parameter works with field names, not aliases
        exclude_fields = {
            field_name
            for field_name in self.__class__.model_fields
            if isinstance(getattr(self, field_name, None), UnsetType)
        }

        # Dump with JSON serialization, excluding UNSET fields
        # Pydantic will handle the alias conversion and exclude the right fields
        return self.model_dump(by_alias=True, mode="json", exclude=exclude_fields)


class BulkUpdateStrings(StashInput):
    """Input for bulk string updates."""

    values: list[str] | UnsetType = UNSET  # [String!]!
    mode: BulkUpdateIdMode | UnsetType = UNSET  # BulkUpdateIdMode!


class BulkUpdateIds(StashInput):
    """Input for bulk ID updates."""

    ids: list[str] | UnsetType = UNSET  # [ID!]!
    mode: BulkUpdateIdMode | UnsetType = UNSET  # BulkUpdateIdMode!


class StashResult(FromGraphQLMixin, BaseModel):
    """Base class for all Stash GraphQL result/output types.

    Result types wrap collections of entities returned from list queries
    like findScenes, findPerformers, etc.

    Example result types:
    - FindScenesResultType
    - FindPerformersResultType
    - StatsResultType
    """

    model_config = ConfigDict(populate_by_name=True)


class StashObject(FromGraphQLMixin, BaseModel):
    """Base interface for our Stash model implementations.

    While this is not a schema interface, it represents a common pattern in the
    schema where many types have id, created_at, and updated_at fields. We use
    this interface to provide common functionality for these types.

    Common fields (matching schema pattern):
    - id: Unique identifier (ID!)
    Note: created_at and updated_at are handled by Stash internally

    Common functionality provided:
    - find_by_id: Find object by ID
    - save: Save object to Stash
    - to_input: Convert to GraphQL input type
    - is_dirty: Check if object has unsaved changes
    - mark_clean: Mark object as having no unsaved changes
    - mark_dirty: Mark object as having unsaved changes

    Identity Map Integration:
    - Uses mode='wrap' validator to check cache before construction
    - Returns cached instance if entity already exists in store
    - Automatically caches new instances after construction
    """

    # Class-level store reference (set by StashContext during initialization)
    # This enables identity map pattern without context propagation issues
    _store: ClassVar[StashEntityStore | None] = None

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
        dict[
            str,
            tuple[str, bool, Callable[[Any], Any] | None] | RelationshipMetadata,
        ]
    ] = {}

    # Field conversion functions
    __field_conversions__: ClassVar[dict[str, Callable[[Any], Any]]] = {}

    # Fields to try for compact repr (first set+non-None field wins)
    __short_repr_fields__: ClassVar[tuple[str, ...]] = ()

    # Max items to show in list-of-StashObject repr before truncating
    _SHORT_REPR_LIST_LIMIT: ClassVar[int] = 2

    # Pydantic configuration
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="allow",  # Allow extra fields for flexibility
        validate_assignment=True,  # Validate on attribute assignment
        populate_by_name=True,  # Accept both snake_case and camelCase
    )

    # Private attributes (stored in __pydantic_private__, survives validate_assignment)
    _snapshot: dict = PrivateAttr(default_factory=dict)
    _is_new: bool = PrivateAttr(default=False)
    _received_fields: set = PrivateAttr(default_factory=set)

    id: str = ""  # Auto-generates UUID4 if empty/None in __init__
    created_at: Time | UnsetType = UNSET  # Time! - Stash internal
    updated_at: Time | UnsetType = UNSET  # Time! - Stash internal

    def __setattr__(self, name: str, value: Any) -> None:
        """Override setattr to automatically sync inverse relationships.

        When a relationship field is set, this automatically updates the inverse
        side on related objects if they're in the same identity map.
        """
        # Use Pydantic's normal setattr for the assignment
        super().__setattr__(name, value)

        # Sync inverse relationships if this is a relationship field
        if name in self.__relationships__:
            self._sync_inverse_relationship(name, value)

    def _sync_inverse_relationship(self, field_name: str, new_value: Any) -> None:
        """Sync the inverse side of a relationship when it's set.

        Args:
            field_name: The relationship field name that was set
            new_value: The new value (object, list of objects, or None)
        """
        # Skip if value is UNSET or if no relationship metadata
        if isinstance(new_value, UnsetType) or field_name not in self.__relationships__:
            return

        # Get relationship metadata
        mapping = self.__relationships__[field_name]

        # Only sync for RelationshipMetadata with inverse info
        if not isinstance(mapping, RelationshipMetadata):
            return
        if not mapping.inverse_query_field or not mapping.inverse_type:
            return

        # Handle list relationships
        if mapping.is_list and isinstance(new_value, list):
            for related_obj in new_value:
                if not isinstance(related_obj, StashObject):
                    continue
                self._add_to_inverse(related_obj, mapping.inverse_query_field)

        # Handle single object relationships
        elif new_value is not None and isinstance(new_value, StashObject):
            self._add_to_inverse(new_value, mapping.inverse_query_field)

    def _add_to_inverse(self, related_obj: StashObject, inverse_field: str) -> None:
        """Add this object to the inverse relationship field on related object.

        Args:
            related_obj: The related object to update
            inverse_field: The field name on the related object to update
        """
        # Get current inverse value
        current_inverse = getattr(related_obj, inverse_field, UNSET)

        # Skip if UNSET (not loaded)
        if isinstance(current_inverse, UnsetType):
            return

        # Handle list inverse fields
        if isinstance(current_inverse, list):
            if self not in current_inverse:
                current_inverse.append(self)
        # Handle single object inverse fields
        else:
            # Use object.__setattr__ to avoid triggering another sync
            object.__setattr__(related_obj, inverse_field, self)

    # =========================================================================
    # Generic Relationship Management Helpers
    # =========================================================================

    async def _add_to_relationship(
        self, field_name: str, related_obj: StashObject
    ) -> None:
        """Add an object to a relationship field (generic helper).

        This method leverages RelationshipMetadata to:
        1. Fetch the field from store if UNSET
        2. Fetch the inverse field from store if UNSET (for bidirectional sync)
        3. Initialize to [] if None (for list relationships)
        4. Add object if not already present
        5. Sync inverse relationship automatically

        Args:
            field_name: Name of the relationship field (e.g., "parents", "galleries")
            related_obj: The object to add to the relationship

        Raises:
            ValueError: If field_name is not in __relationships__
            StashIntegrationError: If store is not available when needed

        Example:
            >>> tag = await client.find_tag("child_id")
            >>> parent = await client.find_tag("parent_id")
            >>> await tag._add_to_relationship("parents", parent)
            >>> await store.save(tag)
        """

        # 1. Validate field has metadata
        if field_name not in self.__relationships__:
            raise ValueError(
                f"No relationship metadata for field '{field_name}' on {self.__type_name__}"
            )

        metadata = self.__relationships__[field_name]
        if not isinstance(metadata, RelationshipMetadata):
            raise ValueError(
                f"Field '{field_name}' uses old tuple syntax, not RelationshipMetadata"
            )

        # 2. Get current value of the field
        current_value = getattr(self, field_name)

        # 3. If UNSET, fetch from store
        if isinstance(current_value, UnsetType):
            if self._store is None:
                raise StashIntegrationError(
                    f"Cannot add to '{field_name}': store not available. "
                    f"Ensure the {self.__type_name__} was loaded through a StashEntityStore."
                )
            await self._store.populate(self, fields=[field_name])
            current_value = getattr(self, field_name)

        # 4. Initialize to [] if None (for list relationships)
        if current_value is None and metadata.is_list:
            current_value = []
            setattr(self, field_name, current_value)

        # 5. Fetch inverse field if UNSET (for bidirectional sync)
        if metadata.inverse_query_field:
            inverse_field = metadata.inverse_query_field
            inverse_value = getattr(related_obj, inverse_field, UNSET)

            if isinstance(inverse_value, UnsetType):
                if related_obj._store is None:
                    raise StashIntegrationError(
                        f"Cannot sync inverse '{inverse_field}': store not available. "
                        f"Ensure the {metadata.inverse_type} was loaded through a StashEntityStore."
                    )
                await related_obj._store.populate(related_obj, fields=[inverse_field])

            # Initialize inverse to [] if None
            inverse_value = getattr(related_obj, inverse_field)
            if inverse_value is None:
                # Check if inverse is a list relationship
                inverse_meta = related_obj.__relationships__.get(inverse_field)
                if (
                    isinstance(inverse_meta, RelationshipMetadata)
                    and inverse_meta.is_list
                ):
                    setattr(related_obj, inverse_field, [])

        # 6. Add to list or set single value
        if metadata.is_list:
            current_value = getattr(self, field_name)
            if current_value is not None and related_obj not in current_value:
                current_value.append(related_obj)
                # Manually sync inverse since append() doesn't trigger __setattr__
                self._sync_inverse_relationship(field_name, current_value)
        else:
            # Setting triggers __setattr__ -> _sync_inverse_relationship()
            setattr(self, field_name, related_obj)

    async def _remove_from_relationship(
        self, field_name: str, related_obj: StashObject
    ) -> None:
        """Remove an object from a relationship field (generic helper).

        This method leverages RelationshipMetadata to:
        1. Skip if field is UNSET (nothing to remove)
        2. Skip if field is None (nothing to remove)
        3. Remove object if present
        4. Sync inverse relationship automatically

        Args:
            field_name: Name of the relationship field (e.g., "parents", "galleries")
            related_obj: The object to remove from the relationship

        Raises:
            ValueError: If field_name is not in __relationships__

        Example:
            >>> tag = await client.find_tag("child_id")
            >>> parent = await client.find_tag("parent_id")
            >>> await tag._remove_from_relationship("parents", parent)
            >>> await store.save(tag)
        """
        # 1. Validate field has metadata
        if field_name not in self.__relationships__:
            raise ValueError(
                f"No relationship metadata for field '{field_name}' on {self.__type_name__}"
            )

        metadata = self.__relationships__[field_name]
        if not isinstance(metadata, RelationshipMetadata):
            raise ValueError(
                f"Field '{field_name}' uses old tuple syntax, not RelationshipMetadata"
            )

        # 2. Get current value
        current_value = getattr(self, field_name)

        # 3. Skip if UNSET or None (nothing to remove)
        if isinstance(current_value, UnsetType) or current_value is None:
            return

        # 4. Remove from list or clear single value
        if metadata.is_list:
            if isinstance(current_value, list) and related_obj in current_value:
                current_value.remove(related_obj)
                # Sync inverse (removing this object from related_obj's inverse field)
                if metadata.inverse_query_field:
                    inverse_field = metadata.inverse_query_field
                    inverse_value = getattr(related_obj, inverse_field, UNSET)
                    if (
                        not isinstance(inverse_value, UnsetType)
                        and inverse_value is not None
                    ):
                        if isinstance(inverse_value, list) and self in inverse_value:
                            inverse_value.remove(self)
                        elif inverse_value is self:
                            # Single object inverse - set to None
                            setattr(related_obj, inverse_field, None)
        # Single object - set to None if it matches
        elif current_value is related_obj:
            setattr(self, field_name, None)

    def __init__(self, **data: Any) -> None:
        """Initialize StashObject with UUID4 auto-generation for new objects.

        If no 'id' is provided, automatically generates a UUID4 hex string (32 chars)
        and sets the _is_new flag to True. This temporary ID is replaced with the
        server-assigned ID after save operations.

        Args:
            **data: Field values for the object
        """
        # Save original state before modifying data
        is_new_object = (
            "id" not in data or data.get("id") is None or data.get("id") == ""
        )

        # Auto-generate UUID4 for new objects without an ID
        if is_new_object:
            data["id"] = uuid.uuid4().hex
            log.debug(
                f"Auto-generated UUID4 for new {self.__class__.__name__}: {data['id']}"
            )

        super().__init__(**data)

        # _received_fields is auto-initialized to set() by PrivateAttr default_factory
        # _is_new is auto-initialized to False by PrivateAttr default

        # Set _is_new flag based on ID logic
        if is_new_object:
            self._is_new = True
        else:
            self._is_new = (
                len(self.id) == 32 and not self.id.isdigit()
            ) or self.id == "new"

    @classmethod
    def new(cls: type[T], **data: Any) -> T:
        """Create a new object that hasn't been saved to the server yet.

        This is a convenience method that creates a new instance without providing
        an 'id', which triggers UUID4 auto-generation and sets _is_new=True.

        This is equivalent to calling the constructor without an 'id' field, but
        makes the intent more explicit in the code.

        Args:
            **data: Field values for the new object (excluding 'id')

        Returns:
            New instance with auto-generated UUID4 and _is_new=True

        Example:
            >>> tag = Tag.new(name="New Tag", description="A new tag")
            >>> tag.is_new()  # True
            >>> tag.id  # '3fa85f6457174562b3fc2c963f66afa6' (UUID4 hex)
        """
        # Create instance without id to trigger UUID generation
        return cls(**data)

    def is_new(self) -> bool:
        """Check if this is a new object not yet saved to the server.

        Uses the _is_new flag which is set during initialization for new objects
        or when explicitly creating new objects with UUID4 identifiers.

        Returns:
            True if this object has not been saved to the server
        """
        return self._is_new

    def update_id(self, server_id: str) -> None:
        """Update the temporary UUID with the server-assigned ID.

        This should be called after a successful create operation to replace
        the auto-generated UUID with the permanent ID from the server. Also
        marks the object as no longer new.

        Args:
            server_id: The permanent ID assigned by the Stash server

        Example:
            >>> scene = Scene(title="Example")  # Auto-generates UUID
            >>> scene.id  # "a1b2c3d4e5f6..."
            >>> scene._is_new  # True
            >>> await scene.save(client)  # Server assigns ID "123"
            >>> scene.id  # "123"
            >>> scene._is_new  # False
        """
        old_id = self.id
        self.id = server_id
        # Mark as no longer new
        self._is_new = False
        log.debug(f"Updated {self.__class__.__name__} ID: {old_id} -> {server_id}")

    @model_validator(mode="before")
    @classmethod
    def _warn_extra_fields(cls, data: Any) -> Any:
        """Emit warning for unmapped fields in GraphQL response data.

        Unlike StashInput._warn_extra_fields (which uses DeprecationWarning for
        user typos heading toward extra="forbid"), this uses StashUnmappedFieldWarning
        because the extra fields come from the Stash server — not user error.
        The server may be newer (fields not yet mapped), older (deprecated fields
        no longer declared), or a schema rename occurred between versions.

        Internal fields (_-prefixed like __typename) are silently ignored.
        """
        if not isinstance(data, dict):
            return data

        # Get known field names (both Python snake_case and GraphQL camelCase aliases)
        known_fields = set()
        for field_name, field_info in cls.model_fields.items():
            known_fields.add(field_name)  # Python name
            if field_info.alias:
                known_fields.add(field_info.alias)  # GraphQL alias

        # Find extra fields, excluding _-prefixed internal fields
        extra_fields = {
            k for k in set(data.keys()) - known_fields if not k.startswith("_")
        }

        if extra_fields:
            warnings.warn(
                f"{cls.__name__}: Unmapped fields from server: "
                f"{', '.join(sorted(extra_fields))}. "
                f"The Stash server may be newer (fields not yet mapped) "
                f"or older (deprecated fields no longer supported).",
                StashUnmappedFieldWarning,
                stacklevel=4,
            )

        return data

    @model_validator(mode="wrap")
    @classmethod
    def _identity_map_validator(
        cls, data: Any, handler: ModelWrapValidatorHandler[Self], info: ValidationInfo
    ) -> Self:
        """Identity map validator with nested object support.

        This validator implements the identity map pattern:
        1. Validate __typename matches expected type (if present)
        2. If data has an ID, check if entity is already cached
        3. If cached, return the cached instance (skip construction)
        4. Process nested StashObject dicts to replace with cached instances
        5. Call handler() for normal Pydantic construction with processed data
        6. Cache the newly constructed instance

        This ensures same ID = same object reference for both top-level
        and nested objects.

        Args:
            data: Raw data (dict, model instance, or other)
            handler: Pydantic's validation handler

        Returns:
            Entity instance (either from cache or newly constructed)

        Raises:
            ValueError: If __typename doesn't match expected type
        """
        # Skip identity map if no store or not a dict
        if not cls._store or not isinstance(data, dict):
            return handler(data)

        # Check cache for current object if it has an ID
        if "id" in data:
            cache_key = (cls.__type_name__, data["id"])

            # Return cached instance if it exists and hasn't expired
            if cache_key in cls._store._cache:
                cached_entry = cls._store._cache[cache_key]
                if not cached_entry.is_expired():
                    cached_obj = cached_entry.entity
                    log.debug(
                        f"Identity map: returning cached {cls.__type_name__} {data['id']}"
                    )
                    # Merge new fields from data into cached instance
                    # Track old and new received fields
                    old_received: set[str] = cached_obj._received_fields
                    new_fields = set(data.keys())

                    # Process nested lookups for new data
                    processed_data = cls._process_nested_cache_lookups(data)

                    # Update field values from new data
                    for field_name, field_value in processed_data.items():
                        if hasattr(cached_obj, field_name):
                            setattr(cached_obj, field_name, field_value)

                    # Merge received fields
                    merged_received = old_received | new_fields
                    cached_obj._received_fields = merged_received
                    log.debug(
                        f"Identity map: merged {len(new_fields)} new fields into cached "
                        f"{cls.__type_name__} {data['id']}"
                    )
                    return cached_obj
                # Expired - remove from cache
                del cls._store._cache[cache_key]
                log.debug(
                    f"Identity map: evicted expired {cls.__type_name__} {data['id']}"
                )

        # Process nested StashObjects to use cached instances
        # This happens BEFORE handler is called, so Pydantic will use the cached objects
        processed_data = cls._process_nested_cache_lookups(data)

        # Normal construction path with processed data
        # Pass context to nested objects so they also track _received_fields
        instance = handler(processed_data, info.context if info.context else None)

        # Track which fields were received from GraphQL
        # Only set _received_fields for data that came through from_graphql()
        # Factory-built and directly constructed objects keep empty _received_fields
        if isinstance(data, dict) and info.context and info.context.get("from_graphql"):
            received_fields = set(data.keys())
            instance._received_fields = received_fields
            log.debug(
                f"Identity map: tracked {len(received_fields)} received fields for {cls.__type_name__}"
            )

        # Cache the new instance
        cls._store._cache_entity(instance)
        log.debug(f"Identity map: cached new {cls.__type_name__} {instance.id}")

        return instance

    @classmethod
    def _process_nested_cache_lookups(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Process nested dicts to replace with cached StashObject instances.

        Args:
            data: Dictionary potentially containing nested StashObject dicts

        Returns:
            Dictionary with nested dicts replaced by cached instances where available
        """
        if not cls._store:
            return data

        # Get field info from Pydantic model
        processed = data.copy()

        for field_name, field_info in cls.model_fields.items():
            if field_name not in data:
                continue

            value = data[field_name]
            if value is None:
                continue

            # Get the field's annotation to check if it's a StashObject type
            annotation = field_info.annotation

            # Handle Union types created with | syntax (types.UnionType)
            # Must check this BEFORE get_origin() since get_origin() may not handle it
            if isinstance(annotation, types.UnionType):
                args = get_args(annotation)
                # Filter out None and UnsetType
                non_none_args = [
                    arg
                    for arg in args
                    if arg is not type(None) and arg is not UnsetType
                ]
                if len(non_none_args) == 1:
                    annotation = non_none_args[0]

            # Get origin and args for the (potentially unwrapped) annotation
            origin = get_origin(annotation)
            args = get_args(annotation)

            # For List[Type]
            if origin is list:
                if args and isinstance(value, list):
                    # Process list of potential StashObjects
                    item_type = args[0]
                    if isinstance(item_type, type) and issubclass(
                        item_type, StashObject
                    ):
                        processed_list = []
                        for item in value:
                            if isinstance(item, dict) and "id" in item:
                                # Check cache for this item
                                cache_key = (item_type.__type_name__, item["id"])
                                if cache_key in cls._store._cache:
                                    cached_entry = cls._store._cache[cache_key]
                                    if not cached_entry.is_expired():
                                        log.debug(
                                            f"Identity map: using cached {item_type.__type_name__} {item['id']} for nested list"
                                        )
                                        processed_list.append(cached_entry.entity)
                                        continue
                            processed_list.append(item)
                        processed[field_name] = processed_list
                continue

            # Check if this field is a StashObject type (single object, not list)
            if (
                isinstance(annotation, type)
                and issubclass(annotation, StashObject)
                and isinstance(value, dict)
                and "id" in value
            ):
                # Check cache for nested object
                cache_key = (annotation.__type_name__, value["id"])
                if cache_key in cls._store._cache:
                    cached_entry = cls._store._cache[cache_key]
                    if not cached_entry.is_expired():
                        log.debug(
                            f"Identity map: using cached {annotation.__type_name__} {value['id']} for nested field"
                        )
                        processed[field_name] = cached_entry.entity

        return processed

    @staticmethod
    def _snapshot_value(value: Any) -> Any:
        """Create a snapshot copy of a field value for dirty tracking.

        Mutable collections (lists) are shallow copied to detect in-place modifications.
        Immutables, StashObjects, and special values (None, UNSET) are stored by reference.

        Args:
            value: Field value to snapshot

        Returns:
            Copy of value if mutable collection, otherwise the value itself
        """
        # Lists need shallow copy to detect append/extend/remove operations
        if isinstance(value, list):
            return value.copy()
        # Primitives, StashObjects, None, UNSET can be stored by reference
        return value

    def model_post_init(self, _context: Any) -> None:
        """Initialize object and store snapshot after Pydantic init.

        This is called by Pydantic after all fields are initialized, so it's
        the right place to capture the initial state for dirty tracking.

        Args:
            _context: Pydantic context (unused but required by signature)
        """
        # Store snapshot of initial state by capturing field values directly
        # This avoids circular reference errors when model_dump() would recurse
        # into bidirectional relationships (e.g., Scene.performers ↔ Performer.scenes)
        # Use _snapshot_value to copy mutable collections (lists)
        self._snapshot = {
            field: self._snapshot_value(getattr(self, field, UNSET))
            for field in self.__tracked_fields__
        }

    def is_dirty(self) -> bool:
        """Check if tracked fields have unsaved changes.

        Compares current field values with snapshot using object identity for
        StashObjects to avoid circular reference errors during comparison.

        Returns:
            True if any tracked field has changed since last snapshot
        """
        for field in self.__tracked_fields__:
            current_value = getattr(self, field, UNSET)
            snapshot_value = self._snapshot.get(field, UNSET)

            # Direct comparison - uses __eq__ which compares by ID for StashObjects
            if current_value != snapshot_value:
                return True

        return False

    def get_changed_fields(self) -> dict[str, Any]:
        """Get fields that have changed since last snapshot.

        Returns:
            Dictionary of field names to current values for changed fields
        """
        changed = {}

        for field in self.__tracked_fields__:
            current_value = getattr(self, field, UNSET)
            snapshot_value = self._snapshot.get(field, UNSET)

            # Field value changed (uses __eq__ which compares by ID for StashObjects)
            if current_value != snapshot_value:
                changed[field] = current_value

        return changed

    def mark_clean(self) -> None:
        """Mark object as having no unsaved changes.

        Updates the snapshot to match the current state.
        """
        # Capture current field values directly to avoid circular reference errors
        # Use _snapshot_value to copy mutable collections (lists)
        self._snapshot = {
            field: self._snapshot_value(getattr(self, field, UNSET))
            for field in self.__tracked_fields__
        }

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
            return cls.from_graphql(data) if data else None
        except Exception:
            return None

    async def save(self, client: StashClient) -> None:
        """Save object to Stash.

        For new objects (created without a server ID), this performs a create
        operation and updates the temporary UUID with the server-assigned ID.

        For existing objects, this performs an update operation, but only if
        there are dirty (changed) fields.

        Args:
            client: StashClient instance

        Raises:
            ValueError: If save fails
        """
        # Skip save if object is not dirty and not new
        if not self.is_dirty() and not self.is_new():
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
            if not self.is_new() and set(input_data.keys()) <= {"id"}:
                log.debug(f"No changes to save for {self.__type_name__} {self.id}")
                self.mark_clean()  # Mark as clean since there are no changes
                return

            is_update = not self.is_new()
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

            # Update ID for new objects using the dedicated method
            if not is_update:
                self.update_id(operation_result["id"])

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

        Relationships with value UNSET are excluded. Relationships with value None
        are included to allow clearing server-side relationships.

        Args:
            fields_to_process: Set of field names to process

        Returns:
            Dictionary of processed relationships (UNSET relationships excluded)
        """
        data: dict[str, Any] = {}

        for rel_field in fields_to_process:
            # Skip if field is not a relationship or doesn't exist
            if rel_field not in self.__relationships__ or not hasattr(self, rel_field):
                continue

            # Get value and skip if UNSET
            value = getattr(self, rel_field)
            if isinstance(value, UnsetType):
                continue

            # Get relationship mapping (supports both RelationshipMetadata and legacy tuple)
            mapping = self.__relationships__[rel_field]

            # Handle both new RelationshipMetadata and legacy tuple format
            if isinstance(mapping, RelationshipMetadata):
                # New format: use RelationshipMetadata attributes
                target_field = mapping.target_field
                is_list = mapping.is_list
                transform = (
                    mapping.transform if mapping.transform is not None else self._get_id
                )
            else:
                # Legacy format: tuple (target_field, is_list, transform)
                target_field, is_list = mapping[:2]
                transform = (
                    mapping[2]
                    if len(mapping) >= 3 and mapping[2] is not None
                    else self._get_id
                )

            # Process value (including None to clear relationships)
            if value is None:
                data[target_field] = None
            elif is_list:
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

        Fields with value UNSET are excluded. Fields with value None are included
        to allow clearing server-side values.

        Args:
            fields_to_process: Set of field names to process

        Returns:
            Dictionary of processed fields (UNSET fields excluded)
        """
        data: dict[str, Any] = {}
        for field in fields_to_process:
            if field not in self.__field_conversions__:
                continue

            if hasattr(self, field):
                value = getattr(self, field)

                # Skip UNSET fields entirely
                if isinstance(value, UnsetType):
                    continue

                # Include None values (to clear server values)
                if value is None:
                    data[field] = None
                else:
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

        For new objects (with temporary UUID), includes all fields.
        For existing objects, includes only dirty (changed) fields plus ID.

        Fields with value UNSET are excluded from the input to avoid
        overwriting server values that were never touched locally.

        Returns:
            Dictionary of input fields. For new objects, all non-UNSET fields
            are included. For existing objects, only changed fields plus ID.
        """
        # For new objects, include all fields
        input_obj = (
            await self._to_input_all()
            if self.is_new()
            else await self._to_input_dirty()
        )

        # Serialize to dict - single point of serialization
        result_dict: dict[str, Any] = input_obj.model_dump(
            exclude_none=True, exclude={"client_mutation_id"}
        )
        log.debug(f"Converted {self.__type_name__} to input: {result_dict}")
        return result_dict

    async def _to_input_all(self) -> BaseModel:
        """Convert all fields to input type.

        For new objects, uses CreateInput type. For existing objects (rare case),
        uses UpdateInput type.

        Fields with value UNSET are excluded from the resulting input.

        Returns:
            Validated Pydantic input object (CreateInput or UpdateInput)

        Raises:
            ValueError: If creation is not supported and object is new
        """
        # Process all fields
        data = await self._process_fields(set(self.__field_conversions__.keys()))

        # Process all relationships
        rel_data = await self._process_relationships(set(self.__relationships__.keys()))
        data.update(rel_data)

        # Determine if this is a create or update operation
        object_is_new = self.is_new()

        # If this is a create operation but creation isn't supported, raise an error
        if object_is_new and not self.__create_input_type__:
            raise ValueError(
                f"{self.__type_name__} objects cannot be created, only updated"
            )

        # Use the appropriate input type
        input_type = (
            self.__create_input_type__ if object_is_new else self.__update_input_type__
        )
        if input_type is None:
            # Note: object_is_new case already handled by check at line 1028
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

    def _short_repr(self) -> str:
        """Compact repr for nested display inside another object's repr."""
        parts: list[str] = []
        for field in self.__short_repr_fields__:
            val = getattr(self, field, UNSET)
            if is_set(val) and val is not None:
                parts.append(f"{field}={val!r}")
        if not parts:
            return f"{self.__type_name__}(id={self.id!r})"
        return f"{self.__type_name__}({', '.join(parts)})"

    def __repr__(self) -> str:
        """Shallow repr that avoids recursive expansion of relationship fields."""
        parts: list[str] = [f"id={self.id!r}"]

        for field_name in sorted(self.__class__.model_fields):
            if field_name == "id":
                continue
            val = getattr(self, field_name, UNSET)
            if not is_set(val):
                continue

            if isinstance(val, StashObject):
                parts.append(f"{field_name}={val._short_repr()}")
            elif isinstance(val, list) and val and isinstance(val[0], StashObject):
                limit = self._SHORT_REPR_LIST_LIMIT
                items = [item._short_repr() for item in val[:limit]]
                suffix = f", ..{len(val) - limit} more" if len(val) > limit else ""
                parts.append(f"{field_name}=[{', '.join(items)}{suffix}]")
            else:
                r = repr(val)
                if len(r) > 200:
                    r = r[:197] + "..."
                parts.append(f"{field_name}={r}")

        return f"{self.__type_name__}({', '.join(parts)})"
