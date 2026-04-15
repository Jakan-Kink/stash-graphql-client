"""Server capability detection for Stash GraphQL client.

Detects the Stash server's appSchema version and available features at connect time.
Used by FragmentStore to build version-appropriate GraphQL fragments.

Instead of individual ``__type`` probes (which require adding a new alias, boolean
field, and registry entry for every capability), this module uses a single
``__schema`` introspection query that returns the full type catalog.  Parsed
schema data is stored on ``ServerCapabilities`` so capabilities can be queried
dynamically via lookup methods like ``has_mutation()``, ``has_type()``, and
``input_has_field()``.
"""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

from .errors import StashError, StashVersionError


if TYPE_CHECKING:
    pass

# Minimum supported appSchema version (Stash v0.30.0)
MIN_SUPPORTED_APP_SCHEMA = 75

# Combined introspection query — fetches version info + full schema catalog
# in a single round trip.
CAPABILITY_DETECTION_QUERY = """{
    version { version }
    systemStatus { appSchema status }
    __schema {
        queryType { name fields { name } }
        mutationType { name fields { name } }
        subscriptionType { name fields { name } }
        types { name kind fields { name } inputFields { name } }
    }
}"""


@dataclass(frozen=True)
class ServerCapabilities:
    """Immutable snapshot of detected server capabilities.

    Created once during client initialization and used by FragmentStore
    to build version-appropriate GraphQL fragments, and by ``StashInput.to_graphql()``
    for runtime field gating.

    Instead of individual boolean flags for each capability, this class stores
    parsed schema data (frozensets of type/field names) and provides lookup
    methods for dynamic capability queries.

    Attributes:
        app_schema: The server's appSchema version number.
        version_string: The server's version string (e.g. "v0.30.0").
        query_names: Names of all root query fields.
        mutation_names: Names of all root mutation fields.
        subscription_names: Names of all root subscription fields.
        type_names: Names of all types in the schema.
        type_fields: Mapping of type name -> frozenset of field/inputField names.
    """

    app_schema: int
    version_string: str
    # Parsed schema data
    query_names: frozenset[str] = field(default_factory=frozenset)
    mutation_names: frozenset[str] = field(default_factory=frozenset)
    subscription_names: frozenset[str] = field(default_factory=frozenset)
    type_names: frozenset[str] = field(default_factory=frozenset)
    type_fields: MappingProxyType[str, frozenset[str]] = field(
        default_factory=lambda: MappingProxyType({})
    )

    # --- Dynamic lookup methods ---

    def has_query(self, name: str) -> bool:
        """Check if a root query field exists."""
        return name in self.query_names

    def has_mutation(self, name: str) -> bool:
        """Check if a root mutation field exists."""
        return name in self.mutation_names

    def has_subscription(self, name: str) -> bool:
        """Check if a root subscription field exists."""
        return name in self.subscription_names

    def has_type(self, name: str) -> bool:
        """Check if a type exists in the schema."""
        return name in self.type_names

    def type_has_field(self, type_name: str, field_name: str) -> bool:
        """Check if an OBJECT type has a specific field."""
        return field_name in self.type_fields.get(type_name, frozenset())

    def input_has_field(self, type_name: str, field_name: str) -> bool:
        """Check if an INPUT_OBJECT type has a specific inputField.

        Uses the same ``type_fields`` map — both OBJECT ``fields`` and
        INPUT_OBJECT ``inputFields`` are stored under the type name.
        """
        return field_name in self.type_fields.get(type_name, frozenset())

    # --- Derived capability properties (based on appSchema) ---

    @property
    def has_studio_custom_fields(self) -> bool:
        """Studios gained custom_fields at appSchema >= 76."""
        return self.app_schema >= 76

    @property
    def has_tag_custom_fields(self) -> bool:
        """Tags gained custom_fields at appSchema >= 77."""
        return self.app_schema >= 77

    @property
    def has_performer_career_start_end(self) -> bool:
        """Performers gained career_start/career_end at appSchema >= 78."""
        return self.app_schema >= 78

    @property
    def has_scene_custom_fields(self) -> bool:
        """Scenes gained custom_fields at appSchema >= 79."""
        return self.app_schema >= 79

    @property
    def has_studio_organized(self) -> bool:
        """Studios gained organized field at appSchema >= 80."""
        return self.app_schema >= 80

    @property
    def has_gallery_custom_fields(self) -> bool:
        """Galleries gained custom_fields at appSchema >= 81."""
        return self.app_schema >= 81

    @property
    def has_group_custom_fields(self) -> bool:
        """Groups gained custom_fields at appSchema >= 82."""
        return self.app_schema >= 82

    @property
    def has_image_custom_fields(self) -> bool:
        """Images gained custom_fields at appSchema >= 83."""
        return self.app_schema >= 83

    @property
    def has_folder_basename(self) -> bool:
        """Folders gained basename/parent_folders at appSchema >= 84."""
        return self.app_schema >= 84

    @property
    def has_performer_career_date_strings(self) -> bool:
        """Performer career_start/career_end changed from Int to String (fuzzy date) at appSchema >= 85."""
        return self.app_schema >= 85

    @property
    def has_folder_sub_folders(self) -> bool:
        """Folders gained sub_folders field (appSchema >= 85, introspection-gated)."""
        return self.type_has_field("Folder", "sub_folders")

    @property
    def uses_new_duplication_type(self) -> bool:
        """Whether the server uses DuplicationCriterionInput (vs PHashDuplicationCriterionInput)."""
        return self.has_type("DuplicationCriterionInput")


# Type alias for the execute function passed to detect_capabilities
ExecuteFn = Callable[[str, dict[str, Any] | None], Coroutine[Any, Any, dict[str, Any]]]


async def detect_capabilities(
    execute_fn: ExecuteFn,
    log: Any,
) -> ServerCapabilities:
    """Detect server capabilities via ``__schema`` introspection.

    Runs a single combined query to determine the server's appSchema version
    and full type catalog. The execute_fn should be a low-level function that
    bypasses the normal _ensure_initialized() check (since we're calling this
    during initialization).

    Args:
        execute_fn: Async function that executes a raw GraphQL query string
                    and returns the result dict. Signature: (query, variables) -> dict.
        log: Logger instance (duck-typed).

    Returns:
        ServerCapabilities instance with parsed schema data.

    Raises:
        StashVersionError: If the server's appSchema < MIN_SUPPORTED_APP_SCHEMA.
        StashError: If the capability detection query fails.
    """
    log.debug("Detecting server capabilities...")

    try:
        result = await execute_fn(CAPABILITY_DETECTION_QUERY, None)
    except Exception as e:
        raise StashError(f"Failed to detect server capabilities: {e}") from e

    # Extract version info
    version_data = result.get("version") or {}
    version_string = version_data.get("version", "unknown")

    status_data = result.get("systemStatus") or {}
    app_schema = status_data.get("appSchema", 0)

    # Check minimum version
    if app_schema < MIN_SUPPORTED_APP_SCHEMA:
        raise StashVersionError(
            f"Stash server appSchema {app_schema} (version {version_string}) "
            f"is below minimum supported version {MIN_SUPPORTED_APP_SCHEMA}. "
            f"Please upgrade to Stash v0.30.0 or later."
        )

    # Parse __schema introspection data
    schema_data = result.get("__schema") or {}

    # Extract query names
    query_type = schema_data.get("queryType") or {}
    query_names = frozenset(f["name"] for f in (query_type.get("fields") or []))

    # Extract mutation names
    mutation_type = schema_data.get("mutationType") or {}
    mutation_names = frozenset(f["name"] for f in (mutation_type.get("fields") or []))

    # Extract subscription names
    subscription_type = schema_data.get("subscriptionType") or {}
    subscription_names = frozenset(
        f["name"] for f in (subscription_type.get("fields") or [])
    )

    # Build type_fields map and type_names set
    type_fields_dict: dict[str, frozenset[str]] = {}
    all_type_names: set[str] = set()

    for type_info in schema_data.get("types") or []:
        type_name = type_info.get("name", "")
        kind = type_info.get("kind", "")
        all_type_names.add(type_name)

        # OBJECT types use "fields", INPUT_OBJECT types use "inputFields"
        if kind == "OBJECT" and type_info.get("fields"):
            type_fields_dict[type_name] = frozenset(
                f["name"] for f in type_info["fields"]
            )
        elif kind == "INPUT_OBJECT" and type_info.get("inputFields"):
            type_fields_dict[type_name] = frozenset(
                f["name"] for f in type_info["inputFields"]
            )

    capabilities = ServerCapabilities(
        app_schema=app_schema,
        version_string=version_string,
        query_names=query_names,
        mutation_names=mutation_names,
        subscription_names=subscription_names,
        type_names=frozenset(all_type_names),
        type_fields=MappingProxyType(type_fields_dict),
    )

    log.info(
        f"Server capabilities detected: version={version_string}, "
        f"appSchema={app_schema}, "
        f"types={len(all_type_names)}, "
        f"queries={len(query_names)}, "
        f"mutations={len(mutation_names)}, "
        f"subscriptions={len(subscription_names)}"
    )

    return capabilities
