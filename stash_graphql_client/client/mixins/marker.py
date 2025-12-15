"""Marker-related client functionality."""

from typing import Any

from ... import fragments
from ...types import (
    BulkSceneMarkerUpdateInput,
    FindSceneMarkersResultType,
    MarkerStringsResultType,
    SceneMarker,
)
from ..protocols import StashClientProtocol


class MarkerClientMixin(StashClientProtocol):
    """Mixin for marker-related client methods."""

    async def find_marker(self, id: str) -> SceneMarker | None:
        """Find a scene marker by its ID.

        Args:
            id: The ID of the marker to find

        Returns:
            SceneMarker object if found, None otherwise
        """
        try:
            result = await self.execute(
                fragments.FIND_MARKER_QUERY,
                {"id": id},
            )
            if result and result.get("findSceneMarker"):
                return self._decode_result(SceneMarker, result["findSceneMarker"])
            return None
        except Exception as e:
            self.log.error(f"Failed to find marker {id}: {e}")
            return None

    async def find_markers(
        self,
        filter_: dict[str, Any] | None = None,
        marker_filter: dict[str, Any] | None = None,
        q: str | None = None,
    ) -> FindSceneMarkersResultType:
        """Find scene markers matching the given filters.

        Args:
            filter_: Optional general filter parameters:
                - q: str (search query)
                - direction: SortDirectionEnum (ASC/DESC)
                - page: int
                - per_page: int
                - sort: str (field to sort by)
            marker_filter: Optional marker-specific filter
            q: Optional search query (alternative to filter_["q"])

        Returns:
            FindSceneMarkersResultType containing:
                - count: Total number of matching markers
                - scene_markers: List of SceneMarker objects
        """
        if filter_ is None:
            filter_ = {"per_page": -1}
        try:
            # Add q to filter if provided
            if q is not None:
                filter_ = dict(filter_ or {})
                filter_["q"] = q

            result = await self.execute(
                fragments.FIND_MARKERS_QUERY,
                {"filter": filter_, "marker_filter": marker_filter},
            )
            if result and result.get("findSceneMarkers"):
                return self._decode_result(
                    FindSceneMarkersResultType, result["findSceneMarkers"]
                )
            return FindSceneMarkersResultType(count=0, scene_markers=[])
        except Exception as e:
            self.log.error(f"Failed to find markers: {e}")
            return FindSceneMarkersResultType(count=0, scene_markers=[])

    async def create_marker(self, marker: SceneMarker) -> SceneMarker:
        """Create a new scene marker in Stash.

        Args:
            marker: SceneMarker object with the data to create. Required fields:
                - title: Marker title
                - scene_id: ID of the scene this marker belongs to
                - seconds: Time in seconds where the marker occurs

        Returns:
            Created SceneMarker object with ID and any server-generated fields

        Raises:
            ValueError: If the marker data is invalid
            gql.TransportError: If the request fails
        """
        try:
            input_data = await marker.to_input()
            result = await self.execute(
                fragments.CREATE_MARKER_MUTATION,
                {"input": input_data},
            )
            return self._decode_result(SceneMarker, result["sceneMarkerCreate"])
        except Exception as e:
            self.log.error(f"Failed to create marker: {e}")
            raise

    async def scene_marker_tags(self, scene_id: str) -> list[dict[str, Any]]:
        """Get scene marker tags for a scene.

        Args:
            scene_id: Scene ID

        Returns:
            List of scene marker tags, each containing:
                - tag: Tag object
                - scene_markers: List of SceneMarker objects
        """
        try:
            result = await self.execute(
                fragments.SCENE_MARKER_TAG_QUERY,
                {"scene_id": scene_id},
            )
            # Explicitly convert to list of dictionaries
            return [dict(tag) for tag in result["sceneMarkerTags"]]
        except Exception as e:
            self.log.error(f"Failed to get scene marker tags for scene {scene_id}: {e}")
            return []

    async def update_marker(self, marker: SceneMarker) -> SceneMarker:
        """Update an existing scene marker in Stash.

        Args:
            marker: SceneMarker object with updated data. Required fields:
                - id: Marker ID to update
                Any other fields that are set will be updated.
                Fields that are None will be ignored.

        Returns:
            Updated SceneMarker object with any server-generated fields

        Raises:
            ValueError: If the marker data is invalid
            gql.TransportError: If the request fails
        """
        try:
            input_data = await marker.to_input()
            result = await self.execute(
                fragments.UPDATE_MARKER_MUTATION,
                {"input": input_data},
            )
            return self._decode_result(SceneMarker, result["sceneMarkerUpdate"])
        except Exception as e:
            self.log.error(f"Failed to update marker: {e}")
            raise

    async def scene_marker_destroy(self, id: str) -> bool:
        """Delete a scene marker.

        Args:
            id: Scene marker ID to delete

        Returns:
            True if the scene marker was successfully deleted

        Raises:
            ValueError: If the scene marker ID is invalid
            gql.TransportError: If the request fails
        """
        try:
            result = await self.execute(
                fragments.SCENE_MARKER_DESTROY_MUTATION,
                {"id": id},
            )

            return bool(result.get("sceneMarkerDestroy", False))
        except Exception as e:
            self.log.error(f"Failed to delete scene marker: {e}")
            raise

    async def scene_markers_destroy(self, ids: list[str]) -> bool:
        """Delete multiple scene markers.

        Args:
            ids: List of scene marker IDs to delete

        Returns:
            True if the scene markers were successfully deleted

        Raises:
            ValueError: If any scene marker ID is invalid
            gql.TransportError: If the request fails
        """
        try:
            result = await self.execute(
                fragments.SCENE_MARKERS_DESTROY_MUTATION,
                {"ids": ids},
            )

            return bool(result.get("sceneMarkersDestroy", False))
        except Exception as e:
            self.log.error(f"Failed to delete scene markers: {e}")
            raise

    async def bulk_scene_marker_update(
        self,
        input_data: BulkSceneMarkerUpdateInput | dict[str, Any],
    ) -> list[SceneMarker]:
        """Bulk update scene markers.

        Args:
            input_data: BulkSceneMarkerUpdateInput object or dictionary containing:
                - ids: List of scene marker IDs to update (optional)
                - And any fields to update (e.g., primary_tag_id, tag_ids, etc.)

        Returns:
            List of updated SceneMarker objects

        Examples:
            Update multiple markers' primary tag:
            ```python
            markers = await client.bulk_scene_marker_update({
                "ids": ["1", "2", "3"],
                "primary_tag_id": "tag123"
            })
            ```

            Add tags to multiple markers:
            ```python
            from stash_graphql_client.types import BulkSceneMarkerUpdateInput, BulkUpdateIds

            input_data = BulkSceneMarkerUpdateInput(
                ids=["1", "2", "3"],
                tag_ids=BulkUpdateIds(ids=["tag1", "tag2"], mode="ADD")
            )
            markers = await client.bulk_scene_marker_update(input_data)
            ```
        """
        try:
            # Convert BulkSceneMarkerUpdateInput to dict if needed
            if isinstance(input_data, BulkSceneMarkerUpdateInput):
                input_dict = input_data.to_graphql()
            else:
                input_dict = input_data

            result = await self.execute(
                fragments.BULK_SCENE_MARKER_UPDATE_MUTATION,
                {"input": input_dict},
            )

            markers_data = result.get("bulkSceneMarkerUpdate", [])
            return [self._decode_result(SceneMarker, m) for m in markers_data]
        except Exception as e:
            self.log.error(f"Failed to bulk update scene markers: {e}")
            raise

    async def marker_wall(self, q: str | None = None) -> list[SceneMarker]:
        """Get marker wall - random markers for display.

        Args:
            q: Optional search query to filter markers

        Returns:
            List of SceneMarker objects selected for wall display

        Examples:
            Get all wall markers:
            ```python
            markers = await client.marker_wall()
            print(f"Found {len(markers)} markers for wall")
            ```

            Search wall markers:
            ```python
            markers = await client.marker_wall(q="interview")
            ```
        """
        try:
            result = await self.execute(
                fragments.MARKER_WALL_QUERY,
                {"q": q} if q else {},
            )
            markers_data = result.get("markerWall", [])
            return [self._decode_result(SceneMarker, m) for m in markers_data]
        except Exception as e:
            self.log.error(f"Failed to get marker wall: {e}")
            return []

    async def marker_strings(
        self, q: str | None = None, sort: str | None = None
    ) -> list[MarkerStringsResultType]:
        """Get marker title strings with counts.

        Args:
            q: Optional search query to filter marker titles
            sort: Optional sort order for results

        Returns:
            List of MarkerStringsResultType objects containing:
                - id: Marker title ID
                - title: Marker title string
                - count: Number of markers with this title

        Examples:
            Get all marker title strings:
            ```python
            strings = await client.marker_strings()
            for s in strings:
                print(f"{s.title}: {s.count} markers")
            ```

            Search and sort marker strings:
            ```python
            strings = await client.marker_strings(q="bj", sort="count")
            ```
        """
        try:
            result = await self.execute(
                fragments.MARKER_STRINGS_QUERY,
                {"q": q, "sort": sort},
            )
            strings_data = result.get("markerStrings", [])
            return [
                self._decode_result(MarkerStringsResultType, s) for s in strings_data
            ]
        except Exception as e:
            self.log.error(f"Failed to get marker strings: {e}")
            return []
