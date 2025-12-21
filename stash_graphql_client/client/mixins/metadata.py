"""Metadata and database operations client functionality."""

from typing import Any

from ... import fragments
from ...types import (
    AnonymiseDatabaseInput,
    AutoTagMetadataInput,
    AutoTagMetadataOptions,
    BackupDatabaseInput,
    CleanGeneratedInput,
    CleanMetadataInput,
    ConfigDefaultSettingsResult,
    ConfigResult,
    ExportObjectsInput,
    GenerateMetadataInput,
    GenerateMetadataOptions,
    IdentifyMetadataInput,
    ImportObjectsInput,
    MigrateBlobsInput,
    MigrateInput,
    MigrateSceneScreenshotsInput,
    ScanMetadataInput,
    ScanMetadataOptions,
    SetupInput,
)
from ...types.unset import UNSET
from ..protocols import StashClientProtocol


class MetadataClientMixin(StashClientProtocol):
    """Mixin for metadata and database operation methods."""

    async def metadata_generate(
        self,
        options: GenerateMetadataOptions | dict[str, Any] | None = None,
        input_data: GenerateMetadataInput | dict[str, Any] | None = None,
    ) -> str:
        """Generate metadata.

        Args:
            options: GenerateMetadataOptions object or dictionary of what to generate:
                - covers: bool - Generate covers
                - sprites: bool - Generate sprites
                - previews: bool - Generate previews
                - imagePreviews: bool - Generate image previews
                - previewOptions: GeneratePreviewOptionsInput
                    - previewSegments: int - Number of segments in a preview file
                    - previewSegmentDuration: float - Duration of each segment in seconds
                    - previewExcludeStart: str - Duration to exclude from start
                    - previewExcludeEnd: str - Duration to exclude from end
                    - previewPreset: PreviewPreset - Preset when generating preview
                - markers: bool - Generate markers
                - markerImagePreviews: bool - Generate marker image previews
                - markerScreenshots: bool - Generate marker screenshots
                - transcodes: bool - Generate transcodes
                - forceTranscodes: bool - Generate transcodes even if not required
                - phashes: bool - Generate phashes
                - interactiveHeatmapsSpeeds: bool - Generate interactive heatmaps speeds
                - imageThumbnails: bool - Generate image thumbnails
                - clipPreviews: bool - Generate clip previews
            input_data: Optional GenerateMetadataInput object or dictionary to specify what to process:
                - sceneIDs: list[str] - List of scene IDs to generate for (default: all)
                - markerIDs: list[str] - List of marker IDs to generate for (default: all)
                - overwrite: bool - Overwrite existing media (default: False)

        Returns:
            Job ID for the generation task

        Raises:
            ValueError: If the input data is invalid
            gql.TransportError: If the request fails
        """
        try:
            # Convert GenerateMetadataOptions to dict if needed
            options_dict = {}
            if options is not None:
                if isinstance(options, GenerateMetadataOptions):
                    options_dict = {
                        k: v for k, v in vars(options).items() if v is not None
                    }
                else:
                    options_dict = options

            # Convert GenerateMetadataInput to dict if needed
            input_dict = {}
            if input_data is not None:
                if isinstance(input_data, GenerateMetadataInput):
                    input_dict = {
                        k: v for k, v in vars(input_data).items() if v is not None
                    }
                else:
                    input_dict = input_data

            # Combine options and input data
            variables = {"input": {**options_dict, **input_dict}}

            # Execute mutation with combined input
            result = await self.execute(fragments.METADATA_GENERATE_MUTATION, variables)

            job_id = result.get("metadataGenerate")
            if not job_id:
                raise ValueError("No job ID returned from server")

            return str(job_id)

        except Exception as e:
            self.log.error(f"Failed to generate metadata: {e}")
            raise

    async def metadata_scan(
        self,
        paths: list[str] | None = None,
        flags: dict[str, Any] | None = None,
    ) -> str:
        """Start a metadata scan job.

        Args:
            paths: List of paths to scan (empty for all paths)
            flags: Optional scan flags matching ScanMetadataInput schema:
                - rescan: bool
                - scanGenerateCovers: bool
                - scanGeneratePreviews: bool
                - scanGenerateImagePreviews: bool
                - scanGenerateSprites: bool
                - scanGeneratePhashes: bool
                - scanGenerateThumbnails: bool
                - scanGenerateClipPreviews: bool
                - filter: ScanMetaDataFilterInput

        Returns:
            Job ID for the scan operation
        """
        # Get scan input object with defaults from config
        if flags is None:
            flags = {}
        if paths is None:
            paths = []
        try:
            defaults = await self.get_configuration_defaults()
            scan_input = ScanMetadataInput(
                paths=paths,
                rescan=getattr(defaults.scan, "rescan", False),
                scanGenerateCovers=getattr(defaults.scan, "scanGenerateCovers", True),
                scanGeneratePreviews=getattr(
                    defaults.scan, "scanGeneratePreviews", True
                ),
                scanGenerateImagePreviews=getattr(
                    defaults.scan, "scanGenerateImagePreviews", True
                ),
                scanGenerateSprites=getattr(defaults.scan, "scanGenerateSprites", True),
                scanGeneratePhashes=getattr(defaults.scan, "scanGeneratePhashes", True),
                scanGenerateThumbnails=getattr(
                    defaults.scan, "scanGenerateThumbnails", True
                ),
                scanGenerateClipPreviews=getattr(
                    defaults.scan, "scanGenerateClipPreviews", True
                ),
            )
        except Exception as e:
            self.log.warning(
                f"Failed to get scan defaults: {e}, using hardcoded defaults"
            )
            scan_input = ScanMetadataInput(
                paths=paths,
                rescan=False,
                scanGenerateCovers=True,
                scanGeneratePreviews=True,
                scanGenerateImagePreviews=True,
                scanGenerateSprites=True,
                scanGeneratePhashes=True,
                scanGenerateThumbnails=True,
                scanGenerateClipPreviews=True,
            )

        # Override with any provided flags
        if flags:
            for key, value in flags.items():
                setattr(scan_input, key, value)

        # Convert to dict for GraphQL
        variables = {"input": scan_input.__dict__}
        try:
            result = await self.execute(fragments.METADATA_SCAN_MUTATION, variables)
            job_id = result.get("metadataScan")
            if not job_id:
                raise ValueError("Failed to start metadata scan - no job ID returned")
            return str(job_id)
        except Exception as e:
            self.log.error(f"Failed to start metadata scan: {e}")
            raise ValueError(f"Failed to start metadata scan: {e}")

    async def get_configuration_defaults(self) -> ConfigDefaultSettingsResult:
        """Get default configuration settings."""
        try:
            # Use new execute() with result_type for automatic deserialization
            config = await self.execute(
                fragments.CONFIG_DEFAULTS_QUERY, result_type=ConfigResult
            )

            # ConfigResult has a defaults field - Pydantic handles all nested objects
            if config and config.defaults is not UNSET:
                return config.defaults

            # Fallback to defaults
            self.log.warning("No defaults in response, using hardcoded values")
            return ConfigDefaultSettingsResult(
                scan=ScanMetadataOptions(
                    rescan=False,
                    scanGenerateCovers=True,
                    scanGeneratePreviews=True,
                    scanGenerateImagePreviews=True,
                    scanGenerateSprites=True,
                    scanGeneratePhashes=True,
                    scanGenerateThumbnails=True,
                    scanGenerateClipPreviews=True,
                ),
                autoTag=AutoTagMetadataOptions(),
                generate=GenerateMetadataOptions(),
                deleteFile=False,
                deleteGenerated=False,
            )
        except Exception as e:
            self.log.error(f"Failed to get configuration defaults: {e}")
            raise

    async def metadata_clean(
        self,
        input_data: CleanMetadataInput | dict[str, Any],
    ) -> str:
        """Clean metadata and remove orphaned database entries.

        Args:
            input_data: CleanMetadataInput object or dictionary containing:
                - paths: List of paths to clean (optional)
                - dry_run: Whether to perform a dry run (optional, default: False)

        Returns:
            Job ID for the clean operation

        Examples:
            Clean all metadata:
            ```python
            job_id = await client.metadata_clean({"dry_run": False})
            print(f"Clean job started: {job_id}")
            ```

            Dry run to see what would be cleaned:
            ```python
            job_id = await client.metadata_clean({"dry_run": True})
            ```

            Clean specific paths:
            ```python
            from stash_graphql_client.types import CleanMetadataInput

            input_data = CleanMetadataInput(
                paths=["/path/to/clean"],
                dry_run=False
            )
            job_id = await client.metadata_clean(input_data)
            ```
        """
        try:
            if isinstance(input_data, CleanMetadataInput):
                input_dict = input_data.to_graphql()
            else:
                input_dict = input_data

            result = await self.execute(
                fragments.METADATA_CLEAN_MUTATION,
                {"input": input_dict},
            )
            return str(result.get("metadataClean", ""))
        except Exception as e:
            self.log.error(f"Failed to clean metadata: {e}")
            raise

    async def metadata_clean_generated(
        self,
        input_data: CleanGeneratedInput | dict[str, Any],
    ) -> str:
        """Clean generated files (sprites, previews, screenshots, etc.).

        Args:
            input_data: CleanGeneratedInput object or dictionary containing:
                - blobFiles: Clean blob files (optional)
                - dryRun: Whether to perform a dry run (optional, default: False)
                - imageThumbnails: Clean image thumbnails (optional)
                - markers: Clean marker files (optional)
                - screenshots: Clean screenshot files (optional)
                - sprites: Clean sprite files (optional)
                - transcodes: Clean transcode files (optional)

        Returns:
            Job ID for the clean operation

        Examples:
            Clean all generated files:
            ```python
            job_id = await client.metadata_clean_generated({
                "blobFiles": True,
                "imageThumbnails": True,
                "markers": True,
                "screenshots": True,
                "sprites": True,
                "transcodes": True,
                "dryRun": False
            })
            ```

            Dry run to see what would be cleaned:
            ```python
            job_id = await client.metadata_clean_generated({"dryRun": True})
            ```

            Clean only specific types:
            ```python
            from stash_graphql_client.types import CleanGeneratedInput

            input_data = CleanGeneratedInput(
                sprites=True,
                screenshots=True,
                dryRun=False
            )
            job_id = await client.metadata_clean_generated(input_data)
            ```
        """
        try:
            if isinstance(input_data, CleanGeneratedInput):
                input_dict = input_data.to_graphql()
            else:
                input_dict = input_data

            result = await self.execute(
                fragments.METADATA_CLEAN_GENERATED_MUTATION,
                {"input": input_dict},
            )
            return str(result.get("metadataCleanGenerated", ""))
        except Exception as e:
            self.log.error(f"Failed to clean generated files: {e}")
            raise

    async def metadata_auto_tag(
        self,
        input_data: AutoTagMetadataInput | dict[str, Any],
    ) -> str:
        """Start auto-tagging metadata task.

        Args:
            input_data: AutoTagMetadataInput object or dictionary containing:
                - paths: List of paths to tag, None for all files (optional)
                - performers: List of performer IDs to tag with, or ["*"] for all (optional)
                - studios: List of studio IDs to tag with, or ["*"] for all (optional)
                - tags: List of tag IDs to tag with, or ["*"] for all (optional)

        Returns:
            Job ID for the auto-tagging task

        Examples:
            Auto-tag all files with all performers:
            ```python
            job_id = await client.metadata_auto_tag({
                "performers": ["*"]
            })
            print(f"Auto-tag job started: {job_id}")
            ```

            Auto-tag specific paths with specific performers:
            ```python
            from stash_graphql_client.types import AutoTagMetadataInput

            input_data = AutoTagMetadataInput(
                paths=["/path/to/videos"],
                performers=["1", "2", "3"],
                studios=["*"],
                tags=None
            )
            job_id = await client.metadata_auto_tag(input_data)
            ```
        """
        try:
            if isinstance(input_data, AutoTagMetadataInput):
                input_dict = input_data.to_graphql()
            else:
                input_dict = input_data

            result = await self.execute(
                fragments.METADATA_AUTO_TAG_MUTATION,
                {"input": input_dict},
            )
            return str(result.get("metadataAutoTag", ""))
        except Exception as e:
            self.log.error(f"Failed to start auto-tag: {e}")
            raise

    async def metadata_identify(
        self,
        input_data: IdentifyMetadataInput | dict[str, Any],
    ) -> str:
        """Start metadata identification task using scrapers.

        Args:
            input_data: IdentifyMetadataInput object or dictionary containing:
                - sources: List of scraper sources to use (required)
                - options: Identification options (optional)
                - sceneIDs: List of scene IDs to identify (optional)
                - paths: List of scene paths to identify (optional, ignored if sceneIDs set)

        Returns:
            Job ID for the identification task

        Examples:
            Identify scenes using a stash-box endpoint:
            ```python
            job_id = await client.metadata_identify({
                "sources": [
                    {
                        "source": {
                            "stashBoxEndpoint": "https://stashdb.org/graphql"
                        }
                    }
                ],
                "sceneIDs": ["1", "2", "3"]
            })
            print(f"Identify job started: {job_id}")
            ```

            Identify with custom options:
            ```python
            from stash_graphql_client.types import (
                IdentifyMetadataInput,
                IdentifySourceInput,
                ScraperSourceInput,
                IdentifyMetadataOptionsInput
            )

            input_data = IdentifyMetadataInput(
                sources=[
                    IdentifySourceInput(
                        source=ScraperSourceInput(
                            stashBoxEndpoint="https://stashdb.org/graphql"
                        ),
                        options=IdentifyMetadataOptionsInput(
                            setCoverImage=True,
                            includeMalePerformers=False
                        )
                    )
                ],
                paths=["/path/to/scenes"]
            )
            job_id = await client.metadata_identify(input_data)
            ```
        """
        try:
            if isinstance(input_data, IdentifyMetadataInput):
                input_dict = input_data.to_graphql()
            else:
                input_dict = input_data

            result = await self.execute(
                fragments.METADATA_IDENTIFY_MUTATION,
                {"input": input_dict},
            )
            return str(result.get("metadataIdentify", ""))
        except Exception as e:
            self.log.error(f"Failed to start identify: {e}")
            raise

    async def metadata_import(self) -> str:
        """Start full metadata import from metadata directory.

        This operation completely wipes the database and imports from the
        metadata directory. Use with caution.

        Returns:
            Job ID for the import task

        Examples:
            Start full metadata import:
            ```python
            job_id = await client.metadata_import()
            print(f"Import job started: {job_id}")
            ```
        """
        try:
            result = await self.execute(fragments.METADATA_IMPORT_MUTATION, {})
            return str(result.get("metadataImport", ""))
        except Exception as e:
            self.log.error(f"Failed to start metadata import: {e}")
            raise

    async def metadata_export(self) -> str:
        """Start full metadata export to metadata directory.

        Exports the entire database to the configured metadata directory.

        Returns:
            Job ID for the export task

        Examples:
            Start full metadata export:
            ```python
            job_id = await client.metadata_export()
            print(f"Export job started: {job_id}")
            ```
        """
        try:
            result = await self.execute(fragments.METADATA_EXPORT_MUTATION, {})
            return str(result.get("metadataExport", ""))
        except Exception as e:
            self.log.error(f"Failed to start metadata export: {e}")
            raise

    async def export_objects(
        self,
        input_data: ExportObjectsInput | dict[str, Any],
    ) -> str:
        """Export objects to a downloadable file.

        Args:
            input_data: ExportObjectsInput object or dictionary containing:
                - ids: List of object IDs to export (optional)
                - all: Export all objects (optional, default: False)
                - type: Object type to export (required)
                - format: Export format (optional)

        Returns:
            Download token for the exported file

        Examples:
            Export all scenes:
            ```python
            token = await client.export_objects({
                "all": True,
                "type": "SCENE"
            })
            download_url = f"{client.url}/downloads/{token}"
            ```

            Export specific performers:
            ```python
            from stash_graphql_client.types import ExportObjectsInput

            input_data = ExportObjectsInput(
                ids=["1", "2", "3"],
                type="PERFORMER"
            )
            token = await client.export_objects(input_data)
            ```
        """
        try:
            if isinstance(input_data, ExportObjectsInput):
                input_dict = input_data.to_graphql()
            else:
                input_dict = input_data

            result = await self.execute(
                fragments.EXPORT_OBJECTS_MUTATION,
                {"input": input_dict},
            )
            return str(result.get("exportObjects", ""))
        except Exception as e:
            self.log.error(f"Failed to export objects: {e}")
            raise

    async def import_objects(
        self,
        input_data: ImportObjectsInput | dict[str, Any],
    ) -> str:
        """Import objects from a file.

        Args:
            input_data: ImportObjectsInput object or dictionary containing:
                - file: File to import from (required)
                - duplicateBehaviour: How to handle duplicates (optional)
                - missingRefBehaviour: How to handle missing references (optional)

        Returns:
            Import job ID

        Examples:
            Import from file:
            ```python
            job_id = await client.import_objects({
                "file": "/path/to/export.json"
            })
            print(f"Import job started: {job_id}")
            ```

            Import with duplicate handling:
            ```python
            from stash_graphql_client.types import ImportObjectsInput

            input_data = ImportObjectsInput(
                file="/path/to/export.json",
                duplicateBehaviour="IGNORE"
            )
            job_id = await client.import_objects(input_data)
            ```
        """
        try:
            if isinstance(input_data, ImportObjectsInput):
                input_dict = input_data.to_graphql()
            else:
                input_dict = input_data

            result = await self.execute(
                fragments.IMPORT_OBJECTS_MUTATION,
                {"input": input_dict},
            )
            return str(result.get("importObjects", ""))
        except Exception as e:
            self.log.error(f"Failed to import objects: {e}")
            raise

    async def backup_database(
        self,
        input_data: BackupDatabaseInput | dict[str, Any],
    ) -> str:
        """Create a database backup.

        Args:
            input_data: BackupDatabaseInput object or dictionary containing:
                - download: Whether to download the backup (optional, default: True)

        Returns:
            Backup file path or download token

        Examples:
            Create and download backup:
            ```python
            token = await client.backup_database({"download": True})
            download_url = f"{client.url}/downloads/{token}"
            ```

            Create backup without downloading:
            ```python
            from stash_graphql_client.types import BackupDatabaseInput

            input_data = BackupDatabaseInput(download=False)
            path = await client.backup_database(input_data)
            print(f"Backup created at: {path}")
            ```
        """
        try:
            if isinstance(input_data, BackupDatabaseInput):
                input_dict = input_data.to_graphql()
            else:
                input_dict = input_data

            result = await self.execute(
                fragments.BACKUP_DATABASE_MUTATION,
                {"input": input_dict},
            )
            return str(result.get("backupDatabase", ""))
        except Exception as e:
            self.log.error(f"Failed to backup database: {e}")
            raise

    async def anonymise_database(
        self,
        input_data: AnonymiseDatabaseInput | dict[str, Any],
    ) -> str:
        """Anonymise the database by removing identifying information.

        Args:
            input_data: AnonymiseDatabaseInput object or dictionary containing:
                - download: Whether to download the anonymised backup (optional, default: True)

        Returns:
            Anonymised backup file path or download token

        Examples:
            Anonymise and download:
            ```python
            token = await client.anonymise_database({"download": True})
            download_url = f"{client.url}/downloads/{token}"
            ```

            Anonymise without downloading:
            ```python
            from stash_graphql_client.types import AnonymiseDatabaseInput

            input_data = AnonymiseDatabaseInput(download=False)
            path = await client.anonymise_database(input_data)
            print(f"Anonymised backup created at: {path}")
            ```
        """
        try:
            if isinstance(input_data, AnonymiseDatabaseInput):
                input_dict = input_data.to_graphql()
            else:
                input_dict = input_data

            result = await self.execute(
                fragments.ANONYMISE_DATABASE_MUTATION,
                {"input": input_dict},
            )
            return str(result.get("anonymiseDatabase", ""))
        except Exception as e:
            self.log.error(f"Failed to anonymise database: {e}")
            raise

    async def migrate(
        self,
        input_data: MigrateInput | dict[str, Any],
    ) -> str:
        """Migrate database to the latest schema version.

        Args:
            input_data: MigrateInput object or dictionary containing:
                - backupPath: Path to create backup before migration (required)

        Returns:
            Migration job ID

        Examples:
            Migrate database with backup:
            ```python
            job_id = await client.migrate({"backupPath": "/path/to/backup.db"})
            print(f"Migration job started: {job_id}")
            ```

            Using the input type:
            ```python
            from stash_graphql_client.types import MigrateInput

            input_data = MigrateInput(backupPath="/path/to/backup.db")
            job_id = await client.migrate(input_data)
            ```
        """
        try:
            if isinstance(input_data, MigrateInput):
                input_dict = input_data.to_graphql()
            else:
                input_dict = input_data

            result = await self.execute(
                fragments.MIGRATE_MUTATION,
                {"input": input_dict},
            )
            return str(result.get("migrate", ""))
        except Exception as e:
            self.log.error(f"Failed to migrate database: {e}")
            raise

    async def migrate_hash_naming(self) -> str:
        """Migrate hash naming scheme to the latest version.

        Returns:
            Migration job ID

        Examples:
            Migrate hash naming:
            ```python
            job_id = await client.migrate_hash_naming()
            print(f"Hash naming migration started: {job_id}")
            ```
        """
        try:
            result = await self.execute(
                fragments.MIGRATE_HASH_NAMING_MUTATION,
                {},
            )
            return str(result.get("migrateHashNaming", ""))
        except Exception as e:
            self.log.error(f"Failed to migrate hash naming: {e}")
            raise

    async def migrate_scene_screenshots(
        self,
        input_data: MigrateSceneScreenshotsInput | dict[str, Any],
    ) -> str:
        """Migrate scene screenshots to the latest storage format.

        Args:
            input_data: MigrateSceneScreenshotsInput object or dictionary containing:
                - deleteFiles: Delete old screenshot files (optional)
                - overwriteExisting: Overwrite existing screenshots (optional)

        Returns:
            Migration job ID

        Examples:
            Migrate screenshots and delete old files:
            ```python
            job_id = await client.migrate_scene_screenshots({
                "deleteFiles": True,
                "overwriteExisting": False
            })
            print(f"Screenshot migration started: {job_id}")
            ```

            Using the input type:
            ```python
            from stash_graphql_client.types import MigrateSceneScreenshotsInput

            input_data = MigrateSceneScreenshotsInput(
                deleteFiles=True,
                overwriteExisting=True
            )
            job_id = await client.migrate_scene_screenshots(input_data)
            ```
        """
        try:
            if isinstance(input_data, MigrateSceneScreenshotsInput):
                input_dict = input_data.to_graphql()
            else:
                input_dict = input_data

            result = await self.execute(
                fragments.MIGRATE_SCENE_SCREENSHOTS_MUTATION,
                {"input": input_dict},
            )
            return str(result.get("migrateSceneScreenshots", ""))
        except Exception as e:
            self.log.error(f"Failed to migrate scene screenshots: {e}")
            raise

    async def migrate_blobs(
        self,
        input_data: MigrateBlobsInput | dict[str, Any],
    ) -> str:
        """Migrate blobs to the latest storage format.

        Args:
            input_data: MigrateBlobsInput object or dictionary containing:
                - deleteOld: Delete old blob files after migration (optional)

        Returns:
            Migration job ID

        Examples:
            Migrate blobs and keep old files:
            ```python
            job_id = await client.migrate_blobs({"deleteOld": False})
            print(f"Blob migration started: {job_id}")
            ```

            Using the input type:
            ```python
            from stash_graphql_client.types import MigrateBlobsInput

            input_data = MigrateBlobsInput(deleteOld=True)
            job_id = await client.migrate_blobs(input_data)
            ```
        """
        try:
            if isinstance(input_data, MigrateBlobsInput):
                input_dict = input_data.to_graphql()
            else:
                input_dict = input_data

            result = await self.execute(
                fragments.MIGRATE_BLOBS_MUTATION,
                {"input": input_dict},
            )
            return str(result.get("migrateBlobs", ""))
        except Exception as e:
            self.log.error(f"Failed to migrate blobs: {e}")
            raise

    async def optimise_database(self) -> str:
        """Optimize the database.

        Returns:
            Job ID for the optimization task
        """
        try:
            result = await self.execute(fragments.OPTIMISE_DATABASE_MUTATION, {})
            return str(result.get("optimiseDatabase", ""))
        except Exception as e:
            self.log.error(f"Failed to optimize database: {e}")
            raise

    async def setup(
        self,
        input_data: SetupInput | dict[str, Any],
    ) -> bool:
        """Run initial Stash setup.

        Args:
            input_data: SetupInput object or dictionary

        Returns:
            True if successful
        """
        try:
            if isinstance(input_data, SetupInput):
                input_dict = input_data.to_graphql()
            else:
                input_dict = input_data

            result = await self.execute(
                fragments.SETUP_MUTATION,
                {"input": input_dict},
            )
            return bool(result.get("setup", False))
        except Exception as e:
            self.log.error(f"Failed to run setup: {e}")
            raise

    async def download_ffmpeg(self) -> str:
        """Download FFmpeg binary.

        Returns:
            Job ID for the download task
        """
        try:
            result = await self.execute(fragments.DOWNLOAD_FFMPEG_MUTATION, {})
            return str(result.get("downloadFFMPEG", ""))
        except Exception as e:
            self.log.error(f"Failed to download FFmpeg: {e}")
            raise
