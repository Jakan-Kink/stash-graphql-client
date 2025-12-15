"""File-related client functionality."""

from typing import Any

from ... import fragments
from ...types import (
    AssignSceneFileInput,
    BaseFile,
    FileSetFingerprintsInput,
    FindFilesResultType,
    FindFoldersResultType,
    Folder,
    FolderFilterType,
    MoveFilesInput,
)
from ..protocols import StashClientProtocol


class FileClientMixin(StashClientProtocol):
    """Mixin for file-related client methods."""

    async def find_file(
        self,
        id: str | None = None,
        path: str | None = None,
    ) -> BaseFile | None:
        """Find a file by its ID or path.

        Args:
            id: The ID of the file to find (optional)
            path: The path of the file to find (optional)

        Returns:
            BaseFile object (VideoFile, ImageFile, GalleryFile, or BasicFile) if found,
            None otherwise

        Raises:
            ValueError: If neither id nor path is provided

        Examples:
            Find a file by ID:
            ```python
            file = await client.find_file(id="123")
            if file:
                print(f"Found file: {file.path}")
            ```

            Find a file by path:
            ```python
            file = await client.find_file(path="/path/to/video.mp4")
            if file:
                print(f"File size: {file.size} bytes")
            ```

            Check file type:
            ```python
            from stash_graphql_client.types import VideoFile, ImageFile

            file = await client.find_file(path="/path/to/file.mp4")
            if isinstance(file, VideoFile):
                print(f"Video: {file.width}x{file.height}, {file.duration}s")
            elif isinstance(file, ImageFile):
                print(f"Image: {file.width}x{file.height}")
            ```
        """
        if id is None and path is None:
            raise ValueError("Either id or path must be provided")

        try:
            # BaseFile is polymorphic - will return VideoFile, ImageFile, etc
            return await self.execute(
                fragments.FIND_FILE_QUERY,
                {"id": id, "path": path},
                result_type=BaseFile,
            )
        except Exception as e:
            self.log.error(f"Failed to find file (id={id}, path={path}): {e}")
            return None

    async def find_files(
        self,
        file_filter: dict[str, Any] | None = None,
        filter_: dict[str, Any] | None = None,
        ids: list[str] | None = None,
    ) -> FindFilesResultType:
        """Find files matching the given filters.

        Args:
            file_filter: Optional file-specific filter:
                - path: StringCriterionInput
                - basename: StringCriterionInput
                - dir: StringCriterionInput
                - parent_folder: HierarchicalMultiCriterionInput
                - zip_file: MultiCriterionInput
                - mod_time: TimestampCriterionInput
                - size: IntCriterionInput
            filter_: Optional general filter parameters:
                - q: str (search query)
                - direction: SortDirectionEnum (ASC/DESC)
                - page: int
                - per_page: int
                - sort: str (field to sort by)
            ids: Optional list of file IDs to retrieve

        Returns:
            FindFilesResultType containing:
                - count: Total number of matching files
                - megapixels: Total megapixels of image files
                - duration: Total duration in seconds of video files
                - size: Total size in bytes
                - files: List of BaseFile objects

        Examples:
            Find all files in a directory:
            ```python
            result = await client.find_files(
                file_filter={
                    "path": {
                        "value": "/videos/",
                        "modifier": "INCLUDES"
                    }
                }
            )
            print(f"Found {result.count} files, total size: {result.size} bytes")
            ```

            Find video files by size:
            ```python
            result = await client.find_files(
                file_filter={
                    "size": {
                        "value": 1000000000,  # 1GB
                        "modifier": "GREATER_THAN"
                    }
                }
            )
            for file in result.files:
                print(f"{file.path}: {file.size} bytes")
            ```

            Find files by IDs:
            ```python
            result = await client.find_files(ids=["1", "2", "3"])
            ```
        """
        try:
            return await self.execute(
                fragments.FIND_FILES_QUERY,
                {
                    "file_filter": file_filter,
                    "filter": filter_,
                    "ids": ids,
                },
                result_type=FindFilesResultType,
            )
        except Exception as e:
            self.log.error(f"Failed to find files: {e}")
            return FindFilesResultType(
                count=0,
                megapixels=0.0,
                duration=0.0,
                size=0,
                files=[],
            )

    async def move_files(self, input_data: MoveFilesInput | dict[str, Any]) -> bool:
        """Move files to a new location.

        Args:
            input_data: MoveFilesInput object or dictionary containing:
                - ids: List of file IDs to move (required)
                - destination_folder: Destination folder path (optional)
                - destination_folder_id: Destination folder ID (optional)
                - destination_basename: New basename for single file (optional)

                Note: Either destination_folder or destination_folder_id must be provided

        Returns:
            True if the move was successful, False otherwise

        Examples:
            Move files to a new folder by path:
            ```python
            success = await client.move_files({
                "ids": ["1", "2", "3"],
                "destination_folder": "/new/location"
            })
            ```

            Move files to a new folder by ID:
            ```python
            success = await client.move_files({
                "ids": ["1", "2"],
                "destination_folder_id": "folder123"
            })
            ```

            Move and rename a single file:
            ```python
            success = await client.move_files({
                "ids": ["1"],
                "destination_folder": "/new/location",
                "destination_basename": "newname.mp4"
            })
            ```
        """
        try:
            # Convert MoveFilesInput to dict if needed
            if isinstance(input_data, MoveFilesInput):
                input_dict = input_data.to_graphql()
            else:
                input_dict = input_data

            result = await self.execute(
                fragments.MOVE_FILES_MUTATION,
                {"input": input_dict},
            )
            return bool(result.get("moveFiles", False))
        except Exception as e:
            self.log.error(f"Failed to move files: {e}")
            return False

    async def file_set_fingerprints(
        self,
        input_data: FileSetFingerprintsInput | dict[str, Any],
    ) -> bool:
        """Set fingerprints for a file.

        Args:
            input_data: FileSetFingerprintsInput object or dictionary containing:
                - id: File ID (required)
                - fingerprints: List of SetFingerprintsInput objects with:
                    - type: Fingerprint type (required)
                    - value: Fingerprint value (optional)

        Returns:
            True if the operation was successful, False otherwise

        Examples:
            Set MD5 fingerprint:
            ```python
            success = await client.file_set_fingerprints({
                "id": "file123",
                "fingerprints": [
                    {"type": "MD5", "value": "abc123def456"}
                ]
            })
            ```

            Set multiple fingerprints:
            ```python
            success = await client.file_set_fingerprints({
                "id": "file123",
                "fingerprints": [
                    {"type": "MD5", "value": "abc123"},
                    {"type": "PHASH", "value": "def456"},
                ]
            })
            ```
        """
        try:
            # Convert FileSetFingerprintsInput to dict if needed
            if isinstance(input_data, FileSetFingerprintsInput):
                input_dict = input_data.to_graphql()
            else:
                input_dict = input_data

            result = await self.execute(
                fragments.FILE_SET_FINGERPRINTS_MUTATION,
                {"input": input_dict},
            )
            return bool(result.get("fileSetFingerprints", False))
        except Exception as e:
            self.log.error(f"Failed to set file fingerprints: {e}")
            return False

    async def scene_assign_file(
        self,
        input_data: AssignSceneFileInput | dict[str, Any],
    ) -> bool:
        """Assign a file to a scene.

        Args:
            input_data: AssignSceneFileInput object or dictionary containing:
                - scene_id: Scene ID (required)
                - file_id: File ID (required)

        Returns:
            True if the assignment was successful, False otherwise

        Examples:
            Assign a file to a scene:
            ```python
            success = await client.scene_assign_file({
                "scene_id": "scene123",
                "file_id": "file456"
            })
            ```

            Using the input type:
            ```python
            from stash_graphql_client.types import AssignSceneFileInput

            input_data = AssignSceneFileInput(
                scene_id="scene123",
                file_id="file456"
            )
            success = await client.scene_assign_file(input_data)
            ```
        """
        try:
            # Convert AssignSceneFileInput to dict if needed
            if isinstance(input_data, AssignSceneFileInput):
                input_dict = input_data.to_graphql()
            else:
                input_dict = input_data

            result = await self.execute(
                fragments.SCENE_ASSIGN_FILE_MUTATION,
                {"input": input_dict},
            )
            return bool(result.get("sceneAssignFile", False))
        except Exception as e:
            self.log.error(f"Failed to assign file to scene: {e}")
            return False

    async def delete_files(self, ids: list[str]) -> bool:
        """Delete files.

        Args:
            ids: List of file IDs to delete

        Returns:
            True if the files were successfully deleted

        Raises:
            ValueError: If any file ID is invalid
            gql.TransportError: If the request fails
        """
        try:
            result = await self.execute(
                fragments.DELETE_FILES_MUTATION,
                {"ids": ids},
            )

            return bool(result.get("deleteFiles", False))
        except Exception as e:
            self.log.error(f"Failed to delete files: {e}")
            raise

    async def find_folder(
        self,
        id: str | None = None,
        path: str | None = None,
    ) -> Folder | None:
        """Find a folder by its ID or path.

        Args:
            id: The ID of the folder to find (optional)
            path: The path of the folder to find (optional)

        Returns:
            Folder object if found, None otherwise

        Raises:
            ValueError: If neither id nor path is provided
        """
        if id is None and path is None:
            raise ValueError("Either id or path must be provided")

        try:
            return await self.execute(
                fragments.FIND_FOLDER_QUERY,
                {"id": id, "path": path},
                result_type=Folder,
            )
        except Exception as e:
            self.log.error(f"Failed to find folder (id={id}, path={path}): {e}")
            return None

    async def find_folders(
        self,
        folder_filter: FolderFilterType | dict[str, Any] | None = None,
        filter_: dict[str, Any] | None = None,
        ids: list[str] | None = None,
    ) -> FindFoldersResultType:
        """Find folders matching the given filters.

        Args:
            folder_filter: Optional folder-specific filter (FolderFilterType or dict)
            filter_: Optional general filter parameters (FindFilterType or dict)
            ids: Optional list of folder IDs to retrieve

        Returns:
            FindFoldersResultType containing count and list of folders
        """
        try:
            # Convert FolderFilterType to dict if needed
            if isinstance(folder_filter, FolderFilterType):
                folder_filter_dict = folder_filter.to_graphql()
            else:
                folder_filter_dict = folder_filter

            return await self.execute(
                fragments.FIND_FOLDERS_QUERY,
                {
                    "folder_filter": folder_filter_dict,
                    "filter": filter_,
                    "ids": ids,
                },
                result_type=FindFoldersResultType,
            )
        except Exception as e:
            self.log.error(f"Failed to find folders: {e}")
            return FindFoldersResultType(count=0, folders=[])
