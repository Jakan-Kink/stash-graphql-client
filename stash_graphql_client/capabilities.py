"""Server capability detection for Stash GraphQL client.

Detects the Stash server's appSchema version and available features at connect time.
Used by FragmentStore to build version-appropriate GraphQL fragments.
"""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from .errors import StashError, StashVersionError


if TYPE_CHECKING:
    pass

# Minimum supported appSchema version (Stash v0.30.0)
MIN_SUPPORTED_APP_SCHEMA = 75

# Combined introspection query — fetches version info + type probes in a single round trip
CAPABILITY_DETECTION_QUERY = """{
    version { version }
    systemStatus { appSchema status }
    _dup: __type(name: "DuplicationCriterionInput") { name }
}"""


@dataclass(frozen=True)
class ServerCapabilities:
    """Immutable snapshot of detected server capabilities.

    Created once during client initialization and used by FragmentStore
    to build version-appropriate GraphQL fragments.

    Attributes:
        app_schema: The server's appSchema version number.
        version_string: The server's version string (e.g. "v0.30.0").
        has_duplication_criterion_input: Whether the DuplicationCriterionInput type exists.
    """

    app_schema: int
    version_string: str
    has_duplication_criterion_input: bool

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
    def uses_new_duplication_type(self) -> bool:
        """Whether the server uses DuplicationCriterionInput (vs PHashDuplicationCriterionInput)."""
        return self.has_duplication_criterion_input


# Type alias for the execute function passed to detect_capabilities
ExecuteFn = Callable[[str, dict[str, Any] | None], Coroutine[Any, Any, dict[str, Any]]]


async def detect_capabilities(
    execute_fn: ExecuteFn,
    log: Any,
) -> ServerCapabilities:
    """Detect server capabilities via introspection.

    Runs a single combined query to determine the server's appSchema version
    and available types. The execute_fn should be a low-level function that
    bypasses the normal _ensure_initialized() check (since we're calling this
    during initialization).

    Args:
        execute_fn: Async function that executes a raw GraphQL query string
                    and returns the result dict. Signature: (query, variables) -> dict.
        log: Logger instance (duck-typed).

    Returns:
        ServerCapabilities instance with detected feature flags.

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

    # Detect type existence via __type probes
    has_dup = result.get("_dup") is not None

    capabilities = ServerCapabilities(
        app_schema=app_schema,
        version_string=version_string,
        has_duplication_criterion_input=has_dup,
    )

    log.info(
        f"Server capabilities detected: version={version_string}, "
        f"appSchema={app_schema}, has_dup_criterion={has_dup}"
    )

    return capabilities
