"""Metadata and database operations client functionality."""

from typing import Any

from ... import fragments
from ...types import (
    AnonymiseDatabaseInput,
    BackupDatabaseInput,
    CleanGeneratedInput,
    CleanMetadataInput,
    ExportObjectsInput,
    ImportObjectsInput,
    MigrateBlobsInput,
    MigrateInput,
    MigrateSceneScreenshotsInput,
)
from ..protocols import StashClientProtocol


class MetadataClientMixin(StashClientProtocol):
    """Mixin for metadata and database operation methods."""

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
                input_dict = input_data.model_dump(by_alias=True, exclude_none=True)
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
                input_dict = input_data.model_dump(by_alias=True, exclude_none=True)
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
                input_dict = input_data.model_dump(by_alias=True, exclude_none=True)
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
                input_dict = input_data.model_dump(by_alias=True, exclude_none=True)
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
                input_dict = input_data.model_dump(by_alias=True, exclude_none=True)
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
                input_dict = input_data.model_dump(by_alias=True, exclude_none=True)
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
                input_dict = input_data.model_dump(by_alias=True, exclude_none=True)
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
                input_dict = input_data.model_dump(by_alias=True, exclude_none=True)
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
                input_dict = input_data.model_dump(by_alias=True, exclude_none=True)
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
