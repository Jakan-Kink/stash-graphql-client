"""Filter-related client functionality."""

from typing import Any

from ... import fragments
from ...types import DestroyFilterInput, SavedFilter, SaveFilterInput
from ..protocols import StashClientProtocol


class FilterClientMixin(StashClientProtocol):
    """Mixin for filter-related client methods."""

    async def save_filter(
        self,
        input_data: SaveFilterInput | dict[str, Any],
    ) -> SavedFilter:
        """Save or update a filter.

        Args:
            input_data: SaveFilterInput object or dictionary containing:
                - mode: FilterMode (required) - Type of filter (SCENES, PERFORMERS, etc.)
                - name: str (required) - Name of the filter
                - id: str (optional) - If provided, updates existing filter
                - find_filter: FindFilterType (optional) - General filter parameters
                - object_filter: dict (optional) - Type-specific filter criteria
                - ui_options: dict (optional) - UI display options

        Returns:
            SavedFilter object with the saved filter data

        Examples:
            Save a new filter:
            ```python
            from stash_graphql_client.types import SaveFilterInput, FilterMode

            input_data = SaveFilterInput(
                mode=FilterMode.SCENES,
                name="My Favorite Scenes",
                find_filter={"per_page": 25},
                object_filter={"is_missing": "performers"}
            )
            saved_filter = await client.save_filter(input_data)
            ```

            Update an existing filter:
            ```python
            input_data = SaveFilterInput(
                id="123",
                mode=FilterMode.SCENES,
                name="Updated Filter Name"
            )
            saved_filter = await client.save_filter(input_data)
            ```
        """
        try:
            if isinstance(input_data, SaveFilterInput):
                input_dict = input_data.to_graphql()
            else:
                input_dict = input_data

            result = await self.execute(
                fragments.SAVE_FILTER_MUTATION,
                {"input": input_dict},
            )

            return self._decode_result(SavedFilter, result["saveFilter"])
        except Exception as e:
            self.log.error(f"Failed to save filter: {e}")
            raise

    async def destroy_saved_filter(
        self,
        input_data: DestroyFilterInput | dict[str, Any],
    ) -> bool:
        """Delete a saved filter.

        Args:
            input_data: DestroyFilterInput object or dictionary containing:
                - id: Filter ID to delete (required)

        Returns:
            True if the filter was successfully deleted

        Examples:
            ```python
            from stash_graphql_client.types import DestroyFilterInput

            input_data = DestroyFilterInput(id="123")
            success = await client.destroy_saved_filter(input_data)
            ```

            Using a dictionary:
            ```python
            success = await client.destroy_saved_filter({"id": "123"})
            ```
        """
        try:
            if isinstance(input_data, DestroyFilterInput):
                input_dict = input_data.to_graphql()
            else:
                input_dict = input_data

            result = await self.execute(
                fragments.DESTROY_SAVED_FILTER_MUTATION,
                {"input": input_dict},
            )

            return bool(result.get("destroySavedFilter", False))
        except Exception as e:
            self.log.error(f"Failed to delete saved filter: {e}")
            raise
