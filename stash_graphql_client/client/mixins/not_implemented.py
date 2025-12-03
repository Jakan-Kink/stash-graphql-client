"""Mixin for not implemented methods."""

from typing import Any

from ... import fragments
from ...types import (
    DLNAStatus,
    Gallery,
    Image,
    JobStatusUpdate,
    LatestVersion,
    SQLExecResult,
    SQLQueryResult,
    StashBoxValidationResult,
    Version,
)
from ..utils import sanitize_model_data


class NotImplementedClientMixin:
    """Mixin for methods that are not yet implemented."""

    # Configuration
    async def configure_scraping(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Configure scraping settings."""
        raise NotImplementedError("Configuration not implemented")

    async def configure_plugin(
        self, plugin_id: str, input_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Configure plugin settings."""
        raise NotImplementedError("Configuration not implemented")

    # Import/Export
    async def metadata_import(self) -> str:
        """Import metadata."""
        raise NotImplementedError("Import/Export not implemented")

    async def metadata_export(self) -> str:
        """Export metadata."""
        raise NotImplementedError("Import/Export not implemented")

    async def metadata_auto_tag(self, input_data: dict[str, Any]) -> str:
        """Auto-tag metadata."""
        raise NotImplementedError("Import/Export not implemented")

    async def metadata_identify(self, input_data: dict[str, Any]) -> str:
        """Identify metadata."""
        raise NotImplementedError("Import/Export not implemented")

    # Queries
    async def scene_streams(self, id: str) -> list[dict[str, Any]]:
        """Get scene stream endpoints."""
        raise NotImplementedError("Scene streams not implemented")

    async def marker_wall(self, q: str | None = None) -> list[dict[str, Any]]:
        """Get marker wall."""
        raise NotImplementedError("Marker wall not implemented")

    async def marker_strings(
        self, q: str | None = None, sort: str | None = None
    ) -> list[dict[str, Any]]:
        """Get marker strings."""
        raise NotImplementedError("Marker strings not implemented")

    async def stats(self) -> dict[str, Any]:
        """Get system stats."""
        raise NotImplementedError("Stats not implemented")

    async def logs(self) -> list[dict[str, Any]]:
        """Get system logs."""
        raise NotImplementedError("Logs not implemented")

    # Scene Mutations
    async def scene_add_o(
        self, id: str, times: list[str] | None = None
    ) -> dict[str, Any]:
        """Add O-count to scene."""
        raise NotImplementedError("Scene O-count not implemented")

    async def scene_delete_o(
        self, id: str, times: list[str] | None = None
    ) -> dict[str, Any]:
        """Delete O-count from scene."""
        raise NotImplementedError("Scene O-count not implemented")

    async def scene_reset_o(self, id: str) -> int:
        """Reset scene O-count."""
        raise NotImplementedError("Scene O-count not implemented")

    async def scene_save_activity(
        self,
        id: str,
        resume_time: float | None = None,
        play_duration: float | None = None,
    ) -> bool:
        """Save scene activity."""
        raise NotImplementedError("Scene activity not implemented")

    async def scene_reset_activity(
        self, id: str, reset_resume: bool = False, reset_duration: bool = False
    ) -> bool:
        """Reset scene activity."""
        raise NotImplementedError("Scene activity not implemented")

    async def scene_add_play(
        self, id: str, times: list[str] | None = None
    ) -> dict[str, Any]:
        """Add play count to scene."""
        raise NotImplementedError("Scene play count not implemented")

    async def scene_delete_play(
        self, id: str, times: list[str] | None = None
    ) -> dict[str, Any]:
        """Delete play count from scene."""
        raise NotImplementedError("Scene play count not implemented")

    async def scene_reset_play_count(self, id: str) -> int:
        """Reset scene play count."""
        raise NotImplementedError("Scene play count not implemented")

    # Scene Marker Mutations
    async def scene_marker_create(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Create a scene marker."""
        raise NotImplementedError("Scene markers not implemented")

    async def scene_marker_update(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Update a scene marker."""
        raise NotImplementedError("Scene markers not implemented")

    # Image Mutations
    async def images_update(self, input_data: list[dict[str, Any]]) -> list[Image]:
        """Update multiple images."""
        raise NotImplementedError("Image updates not implemented")

    async def image_increment_o(self, id: str) -> int:
        """Increment image O-count."""
        raise NotImplementedError("Image O-count not implemented")

    async def image_decrement_o(self, id: str) -> int:
        """Decrement image O-count."""
        raise NotImplementedError("Image O-count not implemented")

    async def image_reset_o(self, id: str) -> int:
        """Reset image O-count."""
        raise NotImplementedError("Image O-count not implemented")

    # Gallery Mutations
    async def bulk_gallery_update(self, input_data: dict[str, Any]) -> list[Gallery]:
        """Update multiple galleries."""
        raise NotImplementedError("Bulk gallery update not implemented")

    # Performer Mutations

    # Studio Mutations

    # Tag Mutations

    # SQL Operations
    async def querySQL(self, sql: str, args: list[Any] | None = None) -> SQLQueryResult:
        """Execute SQL query."""
        raise NotImplementedError("SQL queries not implemented")

    async def execSQL(self, sql: str, args: list[Any] | None = None) -> SQLExecResult:
        """Execute SQL statement."""
        raise NotImplementedError("SQL execution not implemented")

    # Stash-box Operations
    async def validateStashBoxCredentials(
        self, input_data: dict[str, Any]
    ) -> StashBoxValidationResult:
        """Validate stash-box credentials."""
        raise NotImplementedError("Stash-box validation not implemented")

    # DLNA Operations
    async def dlnaStatus(self) -> DLNAStatus:
        """Get DLNA status."""
        raise NotImplementedError("DLNA not implemented")

    # Job Operations
    async def jobsSubscribe(self) -> JobStatusUpdate:
        """Subscribe to job updates."""
        raise NotImplementedError("Job subscription not implemented")

    # Version Operations
    async def version(self) -> Version:
        """Get version information.

        Returns:
            Version object containing:
                - version: Version string (optional)
                - hash: Git commit hash
                - build_time: Build timestamp

        Examples:
            Get current version:
            ```python
            version = await client.version()
            print(f"Stash version: {version.version}")
            print(f"Git hash: {version.hash}")
            print(f"Built at: {version.build_time}")
            ```
        """
        result = await self.execute(fragments.VERSION_QUERY)
        clean_data = sanitize_model_data(result["version"])
        return Version(**clean_data)

    async def latestversion(self) -> LatestVersion:
        """Get latest version information.

        Returns:
            LatestVersion object containing:
                - version: Latest version string
                - shorthash: Short git commit hash
                - release_date: Release date
                - url: Download URL

        Examples:
            Check for updates:
            ```python
            latest = await client.latestversion()
            current = await client.version()

            print(f"Latest version: {latest.version}")
            print(f"Current version: {current.version}")
            print(f"Download URL: {latest.url}")
            ```
        """
        result = await self.execute(fragments.LATEST_VERSION_QUERY)
        clean_data = sanitize_model_data(result["latestversion"])
        return LatestVersion(**clean_data)
