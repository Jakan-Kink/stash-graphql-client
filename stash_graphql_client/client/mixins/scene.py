"""Scene-related client functionality."""

from typing import TYPE_CHECKING, Any

from ... import fragments
from ...types import (
    FindScenesResultType,
    HistoryMutationResult,
    Scene,
    SceneDestroyInput,
    SceneHashInput,
    SceneMarker,
    SceneMergeInput,
    ScenesDestroyInput,
)
from ...types.scene import SceneStreamEndpoint
from ..protocols import StashClientProtocol


if TYPE_CHECKING:
    pass


class SceneClientMixin(StashClientProtocol):
    """Mixin for scene-related client methods."""

    async def find_scene(self, id: str) -> Scene | None:
        """Find a scene by its ID.

        Args:
            id: The ID of the scene to find

        Returns:
            Scene object if found, None otherwise

        Raises:
            ValueError: If scene ID is None or empty

        Examples:
            Find a scene and check its title:
            ```python
            scene = await client.find_scene("123")

            if scene:
                print(f"Found scene: {scene.title}")
            ```

            Access scene relationships:
            ```python
            scene = await client.find_scene("123")

            if scene:
                # Get performer names
                performers = [p.name for p in scene.performers]
                # Get studio name
                studio_name = scene.studio.name if scene.studio else None
                # Get tag names
                tags = [t.name for t in scene.tags]
            ```

            Check scene paths:
            ```python
            scene = await client.find_scene("123")

            if scene:
                # Get streaming URL
                stream_url = scene.paths.stream
                # Get preview URL
                preview_url = scene.paths.preview
            ```
        """
        # Validate scene ID
        if id is None or id == "":
            raise ValueError("Scene ID cannot be empty")

        try:
            result = await self.execute(
                fragments.FIND_SCENE_QUERY,
                {"id": id},
                result_type=Scene,
            )

            return result if result else None
        except Exception as e:
            self.log.error(f"Failed to find scene {id}: {e}")

            return None

    async def find_scenes(
        self,
        filter_: dict[str, Any] | None = None,
        scene_filter: dict[str, Any] | None = None,
        q: str | None = None,
    ) -> FindScenesResultType:
        """Find scenes matching the given filters.

        Args:
            filter_: Optional general filter parameters:
                - q: str (search query)
                - direction: SortDirectionEnum (ASC/DESC)
                - page: int
                - per_page: int
                - sort: str (field to sort by)
            q: Optional search query (alternative to filter_["q"])
            scene_filter: Optional scene-specific filter:
                - file_count: IntCriterionInput
                - is_missing: str (what data is missing)
                - organized: bool
                - path: StringCriterionInput
                - performer_count: IntCriterionInput
                - performer_tags: HierarchicalMultiCriterionInput
                - performers: MultiCriterionInput
                - rating100: IntCriterionInput
                - resolution: ResolutionEnum
                - studios: HierarchicalMultiCriterionInput
                - tag_count: IntCriterionInput
                - tags: HierarchicalMultiCriterionInput
                - title: StringCriterionInput

        Returns:
            FindScenesResultType containing:
                - count: Total number of matching scenes
                - duration: Total duration in seconds
                - filesize: Total size in bytes
                - scenes: List of Scene objects

        Examples:
            Find all organized scenes:
            ```python
            result = await client.find_scenes(
                scene_filter={"organized": True}
            )
            print(f"Found {result.count} organized scenes")
            for scene in result.scenes:
                print(f"- {scene.title}")
            ```

            Find scenes with specific performers:
            ```python
            result = await client.find_scenes(
                scene_filter={
                    "performers": {
                        "value": ["performer1", "performer2"],
                        "modifier": "INCLUDES_ALL"
                    }
                }
            )
            ```

            Find scenes with high rating and sort by date:
            ```python
            result = await client.find_scenes(
                filter_={
                    "direction": "DESC",
                    "sort": "date",
                },
                scene_filter={
                    "rating100": {
                        "value": 80,
                        "modifier": "GREATER_THAN"
                    }
                }
            )
            ```

            Paginate results:
            ```python
            result = await client.find_scenes(
                filter_={
                    "page": 1,
                    "per_page": 25,
                }
            )
            ```
        """
        if filter_ is None:
            filter_ = {"per_page": -1}
        try:
            # Add q to filter if provided
            if q is not None:
                filter_ = dict(filter_ or {})
                filter_["q"] = q

            # execute() with result_type returns the typed object directly
            return await self.execute(
                fragments.FIND_SCENES_QUERY,
                {"filter": filter_, "scene_filter": scene_filter},
                result_type=FindScenesResultType,
            )
        except Exception as e:
            self.log.error(f"Failed to find scenes: {e}")

            return FindScenesResultType(count=0, duration=0, filesize=0, scenes=[])

    async def create_scene(self, scene: Scene) -> Scene:
        """Create a new scene in Stash.

        Args:
            scene: Scene object with the data to create. Required fields:
                - title: Scene title
                - urls: List of URLs associated with the scene
                - organized: Whether the scene is organized

                Note: created_at and updated_at are handled by Stash

        Returns:
            Created Scene object with ID and any server-generated fields

        Raises:
            ValueError: If the scene data is invalid
            gql.TransportError: If the request fails

        Examples:
            Create a basic scene:
            ```python
            scene = Scene(
                title="My Scene",
                urls=["https://example.com/scene"],
                organized=True,  # created_at and updated_at handled by Stash
            )
            created = await client.create_scene(scene)
            print(f"Created scene with ID: {created.id}")
            ```

            Create scene with relationships:
            ```python
            scene = Scene(
                title="My Scene",
                urls=["https://example.com/scene"],
                organized=True,  # created_at and updated_at handled by Stash
                # Add relationships
                performers=[performer1, performer2],
                studio=studio,
                tags=[tag1, tag2],
            )
            created = await client.create_scene(scene)
            ```

            Create scene with metadata:
            ```python
            scene = Scene(
                title="My Scene",
                urls=["https://example.com/scene"],
                organized=True,  # created_at and updated_at handled by Stash
                # Add metadata
                details="Scene description",
                date="2024-01-31",
                rating100=85,
                code="SCENE123",
            )
            created = await client.create_scene(scene)
            ```
        """
        try:
            input_data = await scene.to_input()
            return await self.execute(
                fragments.CREATE_SCENE_MUTATION,
                {"input": input_data},
                result_type=Scene,
            )
        except Exception as e:
            self.log.error(f"Failed to create scene: {e}")
            raise

    async def update_scene(self, scene: Scene) -> Scene:
        """Update an existing scene in Stash.

        Args:
            scene: Scene object with updated data. Required fields:
                - id: Scene ID to update
                Any other fields that are set will be updated.
                Fields that are None will be ignored.

        Returns:
            Updated Scene object with any server-generated fields

        Raises:
            ValueError: If the scene data is invalid
            gql.TransportError: If the request fails

        Examples:
            Update scene title and rating:
            ```python
            scene = await client.find_scene("123")
            if scene:
                scene.title = "New Title"
                scene.rating100 = 90
                updated = await client.update_scene(scene)
                print(f"Updated scene: {updated.title}")
            ```

            Update scene relationships:
            ```python
            scene = await client.find_scene("123")
            if scene:
                # Add new performers
                scene.performers.extend([new_performer1, new_performer2])
                # Set new studio
                scene.studio = new_studio
                # Add new tags
                scene.tags.extend([new_tag1, new_tag2])
                updated = await client.update_scene(scene)
            ```

            Update scene metadata:
            ```python
            scene = await client.find_scene("123")
            if scene:
                # Update metadata
                scene.details = "New description"
                scene.date = "2024-01-31"
                scene.code = "NEWCODE123"
                scene.organized = True
                updated = await client.update_scene(scene)
            ```

            Update scene URLs:
            ```python
            scene = await client.find_scene("123")
            if scene:
                # Replace URLs
                scene.urls = [
                    "https://example.com/new-url",
                ]
                updated = await client.update_scene(scene)
            ```

            Remove scene relationships:
            ```python
            scene = await client.find_scene("123")
            if scene:
                # Clear studio
                scene.studio = None
                # Clear performers
                scene.performers = []
                updated = await client.update_scene(scene)
            ```
        """
        try:
            input_data = await scene.to_input()
            return await self.execute(
                fragments.UPDATE_SCENE_MUTATION,
                {"input": input_data},
                result_type=Scene,
            )
        except Exception as e:
            self.log.error(f"Failed to update scene: {e}")
            raise

    async def find_duplicate_scenes(
        self,
        distance: int | None = None,
        duration_diff: float | None = None,
    ) -> list[list[Scene]]:
        """Find groups of scenes that are perceptual duplicates.

        Args:
            distance: Maximum phash distance between scenes to be considered duplicates
            duration_diff: Maximum difference in seconds between scene durations

        Returns:
            List of scene groups, where each group is a list of duplicate scenes
        """
        try:
            result = await self.execute(
                fragments.FIND_DUPLICATE_SCENES_QUERY,
                {
                    "distance": distance,
                    "duration_diff": duration_diff,
                },
            )

            return [
                [self._decode_result(Scene, scene) for scene in group]
                for group in result["findDuplicateScenes"]
            ]
        except Exception as e:
            self.log.error(f"Failed to find duplicate scenes: {e}")

            return []

    async def parse_scene_filenames(
        self,
        filter_: dict[str, Any] | None = None,
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Parse scene filenames using the given configuration.

        Args:
            filter_: Optional filter to select scenes
            config: Parser configuration:
                - whitespace_separator: bool
                - field_separator: str
                - fields: list[str]

        Returns:
            Dictionary containing parse results
        """
        try:
            result = await self.execute(
                fragments.PARSE_SCENE_FILENAMES_QUERY,
                {
                    "filter": filter_,
                    "config": config,
                },
            )

            return dict(result["parseSceneFilenames"])
        except Exception as e:
            self.log.error(f"Failed to parse scene filenames: {e}")

            return {}

    async def scene_wall(self, q: str | None = None) -> list[Scene]:
        """Get random scenes for the wall.

        Args:
            q: Optional search query

        Returns:
            List of random Scene objects
        """
        try:
            result = await self.execute(
                fragments.SCENE_WALL_QUERY,
                {"q": q},
            )

            return [self._decode_result(Scene, scene) for scene in result["sceneWall"]]
        except Exception as e:
            self.log.error(f"Failed to get scene wall: {e}")

            return []

    async def bulk_scene_update(self, input_data: dict[str, Any]) -> list[Scene]:
        """Update multiple scenes at once.

        Args:
            input_data: Dictionary containing:
                - ids: List of scene IDs to update
                - Any other fields to update on all scenes

        Returns:
            List of updated Scene objects
        """
        try:
            result = await self.execute(
                fragments.BULK_SCENE_UPDATE_MUTATION,
                {"input": input_data},
            )
            return [
                self._decode_result(Scene, scene) for scene in result["bulkSceneUpdate"]
            ]
        except Exception as e:
            self.log.error(f"Failed to bulk update scenes: {e}")
            raise

    async def scenes_update(self, scenes: list[Scene]) -> list[Scene]:
        """Update multiple scenes with individual data.

        Args:
            scenes: List of Scene objects to update, each must have an ID

        Returns:
            List of updated Scene objects
        """
        try:
            result = await self.execute(
                fragments.SCENES_UPDATE_MUTATION,
                {"input": [await scene.to_input() for scene in scenes]},
            )

            return [
                self._decode_result(Scene, scene) for scene in result["scenesUpdate"]
            ]
        except Exception as e:
            self.log.error(f"Failed to update scenes: {e}")
            raise

    async def scene_generate_screenshot(
        self,
        id: str,
        at: float | None = None,
    ) -> str:
        """Generate a screenshot for a scene.

        Args:
            id: Scene ID
            at: Optional time in seconds to take screenshot at

        Returns:
            Path to the generated screenshot

        Raises:
            ValueError: If the scene is not found
            gql.TransportError: If the request fails
        """
        try:
            result = await self.execute(
                fragments.SCENE_GENERATE_SCREENSHOT_MUTATION,
                {"id": id, "at": at},
            )
            if result and "sceneGenerateScreenshot" in result:
                # Explicitly convert to string to match return type
                return str(result["sceneGenerateScreenshot"])

            return ""
        except Exception as e:
            self.log.error(f"Failed to generate screenshot for scene {id}: {e}")
            raise

    async def find_scene_by_hash(
        self,
        input_data: SceneHashInput | dict[str, Any],
    ) -> Scene | None:
        """Find a scene by its hash (checksum or oshash).

        Args:
            input_data: SceneHashInput object or dictionary containing:
                - checksum: MD5 checksum of the file (optional)
                - oshash: OSHash of the file (optional)

                Note: At least one hash must be provided

        Returns:
            Scene object if found, None otherwise

        Examples:
            Find scene by MD5 checksum:
            ```python
            scene = await client.find_scene_by_hash({
                "checksum": "abc123def456..."
            })
            if scene:
                print(f"Found scene: {scene.title}")
            ```

            Find scene by OSHash:
            ```python
            scene = await client.find_scene_by_hash({
                "oshash": "xyz789..."
            })
            ```

            Using the input type:
            ```python
            from ...types import SceneHashInput

            input_data = SceneHashInput(checksum="abc123")
            scene = await client.find_scene_by_hash(input_data)
            ```
        """
        try:
            # Convert SceneHashInput to dict if needed
            if isinstance(input_data, SceneHashInput):
                input_dict = input_data.to_graphql()
            else:
                input_dict = input_data

            result = await self.execute(
                fragments.FIND_SCENE_BY_HASH_QUERY,
                {"input": input_dict},
                result_type=Scene,
            )

            return result if result else None
        except Exception as e:
            self.log.error(f"Failed to find scene by hash: {e}")

            return None

    async def scene_destroy(
        self,
        input_data: SceneDestroyInput | dict[str, Any],
    ) -> bool:
        """Delete a scene.

        Args:
            input_data: SceneDestroyInput object or dictionary containing:
                - id: Scene ID to delete (required)
                - delete_file: Whether to delete the scene's file (optional, default: False)
                - delete_generated: Whether to delete generated files (optional, default: True)

        Returns:
            True if the scene was successfully deleted

        Raises:
            ValueError: If the scene ID is invalid
            gql.TransportError: If the request fails

        Examples:
            Delete a scene without deleting the file:
            ```python
            result = await client.scene_destroy({
                "id": "123",
                "delete_file": False,
                "delete_generated": True
            })
            print(f"Scene deleted: {result}")
            ```

            Delete a scene and its file:
            ```python
            result = await client.scene_destroy({
                "id": "123",
                "delete_file": True,
                "delete_generated": True
            })
            ```

            Using the input type:
            ```python
            from ...types import SceneDestroyInput

            input_data = SceneDestroyInput(
                id="123",
                delete_file=True,
                delete_generated=True
            )
            result = await client.scene_destroy(input_data)
            ```
        """
        try:
            # Convert SceneDestroyInput to dict if needed
            if isinstance(input_data, SceneDestroyInput):
                input_dict = input_data.to_graphql()
            else:
                input_dict = input_data

            result = await self.execute(
                fragments.SCENE_DESTROY_MUTATION,
                {"input": input_dict},
            )

            return bool(result.get("sceneDestroy", False))
        except Exception as e:
            self.log.error(f"Failed to delete scene: {e}")
            raise

    async def scenes_destroy(
        self,
        input_data: ScenesDestroyInput | dict[str, Any],
    ) -> bool:
        """Delete multiple scenes.

        Args:
            input_data: ScenesDestroyInput object or dictionary containing:
                - ids: List of scene IDs to delete (required)
                - delete_file: Whether to delete the scenes' files (optional, default: False)
                - delete_generated: Whether to delete generated files (optional, default: True)

        Returns:
            True if the scenes were successfully deleted

        Raises:
            ValueError: If any scene ID is invalid
            gql.TransportError: If the request fails

        Examples:
            Delete multiple scenes without deleting files:
            ```python
            result = await client.scenes_destroy({
                "ids": ["123", "456", "789"],
                "delete_file": False,
                "delete_generated": True
            })
            print(f"Scenes deleted: {result}")
            ```

            Delete multiple scenes and their files:
            ```python
            result = await client.scenes_destroy({
                "ids": ["123", "456"],
                "delete_file": True,
                "delete_generated": True
            })
            ```

            Using the input type:
            ```python
            from ...types import ScenesDestroyInput

            input_data = ScenesDestroyInput(
                ids=["123", "456", "789"],
                delete_file=False,
                delete_generated=True
            )
            result = await client.scenes_destroy(input_data)
            ```
        """
        try:
            # Convert ScenesDestroyInput to dict if needed
            if isinstance(input_data, ScenesDestroyInput):
                input_dict = input_data.to_graphql()
            else:
                input_dict = input_data

            result = await self.execute(
                fragments.SCENES_DESTROY_MUTATION,
                {"input": input_dict},
            )

            return bool(result.get("scenesDestroy", False))
        except Exception as e:
            self.log.error(f"Failed to delete scenes: {e}")
            raise

    async def scene_merge(
        self,
        input_data: SceneMergeInput | dict[str, Any],
    ) -> Scene:
        """Merge multiple scenes into one destination scene.

        Args:
            input_data: SceneMergeInput object or dictionary containing:
                - source: List of source scene IDs to merge (required)
                - destination: Destination scene ID (required)
                - values: Optional SceneUpdateInput with values to apply to merged scene
                - play_history: Whether to merge play history (optional, default: False)
                - o_history: Whether to merge o-count history (optional, default: False)

        Returns:
            Updated destination Scene object

        Raises:
            ValueError: If the input data is invalid
            gql.TransportError: If the request fails

        Examples:
            Merge two scenes into one:
            ```python
            merged = await client.scene_merge({
                "source": ["123", "456"],
                "destination": "789"
            })
            print(f"Merged into scene: {merged.title}")
            ```

            Merge scenes and update metadata:
            ```python
            from stash_graphql_client.types import SceneMergeInput

            input_data = SceneMergeInput(
                source=["123", "456"],
                destination="789",
                values={"title": "Merged Scene"},
                play_history=True,
                o_history=True
            )
            merged = await client.scene_merge(input_data)
            ```
        """
        try:
            # Convert SceneMergeInput to dict if needed
            if isinstance(input_data, SceneMergeInput):
                input_dict = input_data.to_graphql()
            else:
                input_dict = input_data

            return await self.execute(
                fragments.SCENE_MERGE_MUTATION,
                {"input": input_dict},
                result_type=Scene,
            )
        except Exception as e:
            self.log.error(f"Failed to merge scenes: {e}")
            raise

    # Scene Activity & Counter Operations

    async def scene_add_o(
        self,
        id: str,
        times: list[str] | None = None,
    ) -> HistoryMutationResult:
        """Add O-count entry for a scene.

        Args:
            id: Scene ID
            times: Optional list of timestamps. If not provided, uses current time.

        Returns:
            HistoryMutationResult containing:
                - count: New O-count value
                - history: List of all O timestamps

        Examples:
            Add O-count with current time:
            ```python
            result = await client.scene_add_o("123")
            print(f"New O-count: {result.count}")
            ```

            Add O-count with specific times:
            ```python
            result = await client.scene_add_o(
                "123",
                times=["2024-01-15T10:30:00Z", "2024-01-16T14:20:00Z"]
            )
            ```
        """
        try:
            result = await self.execute(
                fragments.SCENE_ADD_O_MUTATION,
                {"id": id, "times": times},
            )
            return self._decode_result(HistoryMutationResult, result["sceneAddO"])
        except Exception as e:
            self.log.error(f"Failed to add O-count for scene {id}: {e}")
            raise

    async def scene_delete_o(
        self,
        id: str,
        times: list[str] | None = None,
    ) -> HistoryMutationResult:
        """Delete O-count entry from a scene.

        Args:
            id: Scene ID
            times: Optional list of timestamps to remove. If not provided, removes last entry.

        Returns:
            HistoryMutationResult containing:
                - count: New O-count value
                - history: List of remaining O timestamps

        Examples:
            Remove last O-count entry:
            ```python
            result = await client.scene_delete_o("123")
            print(f"New O-count: {result.count}")
            ```

            Remove specific timestamp:
            ```python
            result = await client.scene_delete_o(
                "123",
                times=["2024-01-15T10:30:00Z"]
            )
            ```
        """
        try:
            result = await self.execute(
                fragments.SCENE_DELETE_O_MUTATION,
                {"id": id, "times": times},
            )
            return self._decode_result(HistoryMutationResult, result["sceneDeleteO"])
        except Exception as e:
            self.log.error(f"Failed to delete O-count for scene {id}: {e}")
            raise

    async def scene_reset_o(self, id: str) -> int:
        """Reset scene O-count to 0.

        Args:
            id: Scene ID

        Returns:
            New O-count value (0)

        Example:
            ```python
            count = await client.scene_reset_o("123")
            print(f"O-count reset to: {count}")
            ```
        """
        try:
            result = await self.execute(
                fragments.SCENE_RESET_O_MUTATION,
                {"id": id},
            )
            return int(result["sceneResetO"])
        except Exception as e:
            self.log.error(f"Failed to reset O-count for scene {id}: {e}")
            raise

    async def scene_save_activity(
        self,
        id: str,
        resume_time: float | None = None,
        play_duration: float | None = None,
    ) -> bool:
        """Save scene playback activity.

        Args:
            id: Scene ID
            resume_time: Resume time point in seconds
            play_duration: Duration played in seconds

        Returns:
            True if activity was saved successfully

        Examples:
            Save resume point:
            ```python
            await client.scene_save_activity("123", resume_time=120.5)
            ```

            Save play duration:
            ```python
            await client.scene_save_activity("123", play_duration=300.0)
            ```

            Save both:
            ```python
            await client.scene_save_activity(
                "123",
                resume_time=120.5,
                play_duration=300.0
            )
            ```
        """
        try:
            result = await self.execute(
                fragments.SCENE_SAVE_ACTIVITY_MUTATION,
                {
                    "id": id,
                    "resume_time": resume_time,
                    "playDuration": play_duration,
                },
            )
            return bool(result.get("sceneSaveActivity", False))
        except Exception as e:
            self.log.error(f"Failed to save activity for scene {id}: {e}")
            raise

    async def scene_reset_activity(
        self,
        id: str,
        reset_resume: bool = False,
        reset_duration: bool = False,
    ) -> bool:
        """Reset scene activity tracking.

        Args:
            id: Scene ID
            reset_resume: Whether to reset resume time point
            reset_duration: Whether to reset play duration

        Returns:
            True if activity was reset successfully

        Examples:
            Reset resume point:
            ```python
            await client.scene_reset_activity("123", reset_resume=True)
            ```

            Reset play duration:
            ```python
            await client.scene_reset_activity("123", reset_duration=True)
            ```

            Reset both:
            ```python
            await client.scene_reset_activity(
                "123",
                reset_resume=True,
                reset_duration=True
            )
            ```
        """
        try:
            result = await self.execute(
                fragments.SCENE_RESET_ACTIVITY_MUTATION,
                {
                    "id": id,
                    "reset_resume": reset_resume,
                    "reset_duration": reset_duration,
                },
            )
            return bool(result.get("sceneResetActivity", False))
        except Exception as e:
            self.log.error(f"Failed to reset activity for scene {id}: {e}")
            raise

    async def scene_add_play(
        self,
        id: str,
        times: list[str] | None = None,
    ) -> HistoryMutationResult:
        """Add play count entry for a scene.

        Args:
            id: Scene ID
            times: Optional list of timestamps. If not provided, uses current time.

        Returns:
            HistoryMutationResult containing:
                - count: New play count value
                - history: List of all play timestamps

        Examples:
            Add play with current time:
            ```python
            result = await client.scene_add_play("123")
            print(f"New play count: {result.count}")
            ```

            Add play with specific times:
            ```python
            result = await client.scene_add_play(
                "123",
                times=["2024-01-15T10:30:00Z"]
            )
            ```
        """
        try:
            result = await self.execute(
                fragments.SCENE_ADD_PLAY_MUTATION,
                {"id": id, "times": times},
            )
            return self._decode_result(HistoryMutationResult, result["sceneAddPlay"])
        except Exception as e:
            self.log.error(f"Failed to add play count for scene {id}: {e}")
            raise

    async def scene_delete_play(
        self,
        id: str,
        times: list[str] | None = None,
    ) -> HistoryMutationResult:
        """Delete play count entry from a scene.

        Args:
            id: Scene ID
            times: Optional list of timestamps to remove. If not provided, removes last entry.

        Returns:
            HistoryMutationResult containing:
                - count: New play count value
                - history: List of remaining play timestamps

        Examples:
            Remove last play entry:
            ```python
            result = await client.scene_delete_play("123")
            print(f"New play count: {result.count}")
            ```

            Remove specific timestamp:
            ```python
            result = await client.scene_delete_play(
                "123",
                times=["2024-01-15T10:30:00Z"]
            )
            ```
        """
        try:
            result = await self.execute(
                fragments.SCENE_DELETE_PLAY_MUTATION,
                {"id": id, "times": times},
            )
            return self._decode_result(HistoryMutationResult, result["sceneDeletePlay"])
        except Exception as e:
            self.log.error(f"Failed to delete play count for scene {id}: {e}")
            raise

    async def scene_reset_play_count(self, id: str) -> int:
        """Reset scene play count to 0.

        Args:
            id: Scene ID

        Returns:
            New play count value (0)

        Example:
            ```python
            count = await client.scene_reset_play_count("123")
            print(f"Play count reset to: {count}")
            ```
        """
        try:
            result = await self.execute(
                fragments.SCENE_RESET_PLAY_COUNT_MUTATION,
                {"id": id},
            )
            return int(result["sceneResetPlayCount"])
        except Exception as e:
            self.log.error(f"Failed to reset play count for scene {id}: {e}")
            raise

    async def find_scenes_by_path_regex(
        self,
        filter_: dict[str, Any] | None = None,
    ) -> list[Scene]:
        """Find scenes by path regex pattern.

        Args:
            filter_: Filter parameters

        Returns:
            List of Scene objects matching the path pattern
        """
        try:
            result = await self.execute(
                fragments.FIND_SCENES_BY_PATH_REGEX_QUERY,
                {"filter": filter_},
            )
            scenes_data = result.get("findScenesByPathRegex", [])
            return [self._decode_result(Scene, s) for s in scenes_data]
        except Exception as e:
            self.log.error(f"Failed to find scenes by path regex: {e}")
            return []

    async def scene_streams(self, scene_id: str) -> list["SceneStreamEndpoint"]:
        """Get streaming endpoints for a scene.

        Args:
            scene_id: The ID of the scene

        Returns:
            List of SceneStreamEndpoint objects containing:
                - url: Stream URL
                - mime_type: MIME type of the stream
                - label: Label for the stream quality/format

        Examples:
            Get streaming endpoints:
            ```python
            streams = await client.scene_streams("123")
            for stream in streams:
                print(f"{stream.label}: {stream.url} ({stream.mime_type})")
            ```

            Access specific stream properties:
            ```python
            streams = await client.scene_streams("123")
            if streams:
                primary_stream = streams[0]
                print(f"Primary stream URL: {primary_stream.url}")
            ```
        """
        try:
            result = await self.execute(
                fragments.SCENE_STREAMS_QUERY,
                {"id": scene_id},
            )
            streams_data = result.get("sceneStreams", [])
            return [self._decode_result(SceneStreamEndpoint, s) for s in streams_data]
        except Exception as e:
            self.log.error(f"Failed to get scene streams for scene {scene_id}: {e}")
            return []

    # Scene Marker Utility Methods

    async def merge_scene_markers(
        self,
        target_scene_id: str,
        source_scene_ids: list[str],
    ) -> list[Any]:
        """Merge scene markers from source scenes to target scene.

        This utility method copies all markers from one or more source scenes to a
        target scene. Useful when consolidating duplicate scenes or merging content.

        Args:
            target_scene_id: The ID of the target scene to copy markers to
            source_scene_ids: List of source scene IDs to copy markers from

        Returns:
            List of SceneMarker objects that were created on the target scene

        Examples:
            Merge markers from a single source:
            ```python
            markers = await client.merge_scene_markers(
                target_scene_id="123",
                source_scene_ids=["456"]
            )
            print(f"Copied {len(markers)} markers to target scene")
            ```

            Merge markers from multiple sources:
            ```python
            markers = await client.merge_scene_markers(
                target_scene_id="123",
                source_scene_ids=["456", "789", "101"]
            )
            for marker in markers:
                print(f"Marker: {marker.title} at {marker.seconds}s")
            ```

            Use with scene merge workflow:
            ```python
            # First merge the scenes
            merged = await client.scene_merge({
                "source": ["source1", "source2"],
                "destination": "target"
            })

            # Then copy markers
            markers = await client.merge_scene_markers(
                target_scene_id="target",
                source_scene_ids=["source1", "source2"]
            )
            ```
        """
        try:
            created_markers = []

            # Process each source scene
            for source_id in source_scene_ids:
                # Find all markers in the source scene
                marker_filter = {
                    "scene_id": {
                        "value": [source_id],
                        "modifier": "INCLUDES",
                    }
                }

                result = await self.execute(
                    fragments.FIND_MARKERS_QUERY,
                    {"filter": {"per_page": -1}, "marker_filter": marker_filter},
                )

                if not result or not result.get("findSceneMarkers"):
                    continue

                markers_data = result["findSceneMarkers"].get("scene_markers", [])

                # Create each marker on the target scene
                for marker_data in markers_data:
                    marker = self._decode_result(SceneMarker, marker_data)

                    # Extract tag IDs from tags
                    tag_ids = None
                    if marker.tags and marker.tags is not None:
                        tag_ids = [tag.id for tag in marker.tags if tag and tag.id]

                    # Extract primary tag ID
                    primary_tag_id = None
                    if marker.primary_tag and marker.primary_tag is not None:
                        primary_tag_id = marker.primary_tag.id

                    # Create new marker on target scene with same metadata
                    marker_input = {
                        "scene_id": target_scene_id,
                        "title": marker.title,
                        "seconds": marker.seconds,
                        "primary_tag_id": primary_tag_id,
                        "tag_ids": tag_ids,
                    }

                    # Add end_seconds if present
                    if (
                        marker.end_seconds is not None
                        and marker.end_seconds is not None
                    ):
                        marker_input["end_seconds"] = marker.end_seconds

                    create_result = await self.execute(
                        fragments.CREATE_MARKER_MUTATION,
                        {"input": marker_input},
                    )

                    created_marker = self._decode_result(
                        SceneMarker, create_result["sceneMarkerCreate"]
                    )
                    created_markers.append(created_marker)

            return created_markers

        except Exception as e:
            self.log.error(f"Failed to merge scene markers: {e}")
            return []

    async def find_duplicate_scenes_wrapper(
        self,
        distance: int = 0,
        duration_diff: float | None = None,
    ) -> list[list[Scene]]:
        """Find duplicate scenes with sensible default parameters.

        This is a convenience wrapper around find_duplicate_scenes() that provides
        better defaults for common use cases. A distance of 0 finds exact phash
        matches (true duplicates), while higher values find similar scenes.

        Args:
            distance: Maximum phash distance (default: 0 for exact duplicates)
                - 0: Exact phash matches (identical frames)
                - 1-5: Very similar scenes (same content, different encode)
                - 6-10: Similar scenes (same source, different quality)
                - 11+: Potentially different scenes
            duration_diff: Maximum duration difference in seconds (default: None)
                - None: No duration filtering
                - 0.0: Exact duration match
                - 1.0-10.0: Similar duration (accounts for encoding differences)
                - 10.0+: Loose duration matching

        Returns:
            List of scene groups, where each group is a list of duplicate scenes

        Examples:
            Find exact duplicates (phash distance = 0):
            ```python
            duplicates = await client.find_duplicate_scenes_wrapper()
            for group in duplicates:
                print(f"Found {len(group)} exact duplicates:")
                for scene in group:
                    print(f"  - {scene.title}")
            ```

            Find similar scenes (allow small phash differences):
            ```python
            similar = await client.find_duplicate_scenes_wrapper(distance=5)
            for group in similar:
                print(f"Found {len(group)} similar scenes")
            ```

            Find duplicates with similar duration:
            ```python
            duplicates = await client.find_duplicate_scenes_wrapper(
                distance=0,
                duration_diff=2.0  # Within 2 seconds
            )
            ```

            Use in cleanup workflow:
            ```python
            # Find exact duplicates
            duplicates = await client.find_duplicate_scenes_wrapper()

            for group in duplicates:
                # Keep the first scene, delete the rest
                to_delete = [scene.id for scene in group[1:]]
                if to_delete:
                    await client.scenes_destroy({
                        "ids": to_delete,
                        "delete_file": True
                    })
            ```
        """
        return await self.find_duplicate_scenes(
            distance=distance,
            duration_diff=duration_diff,
        )
