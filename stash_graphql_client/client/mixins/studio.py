"""Studio-related client functionality."""

from typing import Any

from ... import fragments
from ...types import (
    BulkStudioUpdateInput,
    FindStudiosResultType,
    Studio,
    StudioDestroyInput,
)
from ..protocols import StashClientProtocol


class StudioClientMixin(StashClientProtocol):
    """Mixin for studio-related client methods."""

    async def find_studio(self, id: str) -> Studio | None:
        """Find a studio by its ID.

        Args:
            id: The ID of the studio to find

        Returns:
            Studio object if found, None otherwise
        """
        try:
            return await self.execute(
                fragments.FIND_STUDIO_QUERY,
                {"id": id},
                result_type=Studio,
            )
        except Exception as e:
            self.log.error(f"Failed to find studio {id}: {e}")
            return None

    async def find_studios(
        self,
        filter_: dict[str, Any] | None = None,
        studio_filter: dict[str, Any] | None = None,
        q: str | None = None,
    ) -> FindStudiosResultType:
        """Find studios matching the given filters.

        Args:
            filter_: Optional general filter parameters:
                - q: str (search query)
                - direction: SortDirectionEnum (ASC/DESC)
                - page: int
                - per_page: int
                - sort: str (field to sort by)
            studio_filter: Optional studio-specific filter
            q: Optional search query (alternative to filter_["q"])

        Returns:
            FindStudiosResultType containing:
                - count: Total number of matching studios
                - studios: List of Studio objects
        """
        if filter_ is None:
            filter_ = {"per_page": -1}
        try:
            # Add q to filter if provided
            if q is not None:
                filter_ = dict(filter_ or {})
                filter_["q"] = q

            return await self.execute(
                fragments.FIND_STUDIOS_QUERY,
                {"filter": filter_, "studio_filter": studio_filter},
                result_type=FindStudiosResultType,
            )
        except Exception as e:
            self.log.error(f"Failed to find studios: {e}")
            return FindStudiosResultType(count=0, studios=[])

    async def create_studio(self, studio: Studio) -> Studio:
        """Create a new studio in Stash.

        Args:
            studio: Studio object with the data to create. Required fields:
                - name: Studio name

        Returns:
            Created Studio object with ID and any server-generated fields

        Raises:
            ValueError: If the studio data is invalid
            gql.TransportError: If the request fails
        """
        try:
            input_data = await studio.to_input()
            return await self.execute(
                fragments.CREATE_STUDIO_MUTATION,
                {"input": input_data},
                result_type=Studio,
            )
        except Exception as e:
            self.log.error(f"Failed to create studio: {e}")
            raise

    async def update_studio(self, studio: Studio) -> Studio:
        """Update an existing studio in Stash.

        Args:
            studio: Studio object with updated data. Required fields:
                - id: Studio ID to update
                Any other fields that are set will be updated.
                Fields that are None will be ignored.

        Returns:
            Updated Studio object with any server-generated fields

        Raises:
            ValueError: If the studio data is invalid
            gql.TransportError: If the request fails
        """
        try:
            input_data = await studio.to_input()
            return await self.execute(
                fragments.UPDATE_STUDIO_MUTATION,
                {"input": input_data},
                result_type=Studio,
            )
        except Exception as e:
            self.log.error(f"Failed to update studio: {e}")
            raise

    async def studio_destroy(
        self,
        input_data: StudioDestroyInput | dict[str, Any],
    ) -> bool:
        """Delete a studio.

        Args:
            input_data: StudioDestroyInput object or dictionary containing:
                - id: Studio ID to delete (required)

        Returns:
            True if the studio was successfully deleted

        Raises:
            ValueError: If the studio ID is invalid
            gql.TransportError: If the request fails
        """
        try:
            if isinstance(input_data, StudioDestroyInput):
                input_dict = input_data.to_graphql()
            else:
                input_dict = input_data

            result = await self.execute(
                fragments.STUDIO_DESTROY_MUTATION,
                {"input": input_dict},
            )

            return bool(result.get("studioDestroy", False))
        except Exception as e:
            self.log.error(f"Failed to delete studio: {e}")
            raise

    async def studios_destroy(self, ids: list[str]) -> bool:
        """Delete multiple studios.

        Args:
            ids: List of studio IDs to delete

        Returns:
            True if the studios were successfully deleted

        Raises:
            ValueError: If any studio ID is invalid
            gql.TransportError: If the request fails
        """
        try:
            result = await self.execute(
                fragments.STUDIOS_DESTROY_MUTATION,
                {"ids": ids},
            )

            return bool(result.get("studiosDestroy", False))
        except Exception as e:
            self.log.error(f"Failed to delete studios: {e}")
            raise

    async def bulk_studio_update(
        self,
        input_data: BulkStudioUpdateInput | dict[str, Any],
    ) -> list[Studio]:
        """Bulk update studios.

        Args:
            input_data: BulkStudioUpdateInput object or dictionary containing:
                - ids: List of studio IDs to update (optional)
                - And any fields to update (e.g., url, rating100, etc.)

        Returns:
            List of updated Studio objects

        Examples:
            Update multiple studios' ratings:
            ```python
            studios = await client.bulk_studio_update({
                "ids": ["1", "2", "3"],
                "rating100": 80
            })
            ```

            Add tags to multiple studios:
            ```python
            from stash_graphql_client.types import BulkStudioUpdateInput, BulkUpdateIds

            input_data = BulkStudioUpdateInput(
                ids=["1", "2", "3"],
                tag_ids=BulkUpdateIds(ids=["tag1", "tag2"], mode="ADD")
            )
            studios = await client.bulk_studio_update(input_data)
            ```
        """
        try:
            # Convert BulkStudioUpdateInput to dict if needed
            if isinstance(input_data, BulkStudioUpdateInput):
                input_dict = input_data.to_graphql()
            else:
                input_dict = input_data

            return await self.execute(
                fragments.BULK_STUDIO_UPDATE_MUTATION,
                {"input": input_dict},
                result_type=list[Studio],
            )
        except Exception as e:
            self.log.error(f"Failed to bulk update studios: {e}")
            raise

    async def find_studio_hierarchy(self, studio_id: str) -> list[Studio]:
        """Get full parent chain from root to this studio.

        Recursively traverses the parent_studio relationship to build a complete
        hierarchy from the root studio down to the specified studio.

        Args:
            studio_id: The ID of the studio to get hierarchy for

        Returns:
            List of Studio objects ordered from root (index 0) to the specified
            studio (last index). Returns empty list if studio not found.

        Examples:
            Get studio hierarchy:
            ```python
            # Studio structure: Root > Parent > Child
            hierarchy = await client.find_studio_hierarchy("child_id")
            # Returns: [<Root Studio>, <Parent Studio>, <Child Studio>]
            for i, studio in enumerate(hierarchy):
                print(f"Level {i}: {studio.name}")
            ```

            Check if studio has parents:
            ```python
            hierarchy = await client.find_studio_hierarchy("studio_id")
            if len(hierarchy) > 1:
                print(f"Root studio: {hierarchy[0].name}")
                print(f"Direct parent: {hierarchy[-2].name}")
            ```
        """
        hierarchy: list[Studio] = []
        current = await self.find_studio(studio_id)

        if not current:
            return hierarchy

        # Build hierarchy from child to root
        while current:  # pragma: no branch
            hierarchy.append(current)
            # Check if parent_studio exists and is not UNSET/None
            if current.parent_studio and hasattr(current.parent_studio, "id"):
                current = current.parent_studio
            else:
                break

        # Reverse to get root-first ordering
        return list(reversed(hierarchy))

    async def find_studio_root(self, studio_id: str) -> Studio | None:
        """Find the top-level parent studio.

        Traverses the parent chain to find the root studio (the one with no parent).

        Args:
            studio_id: The ID of the studio to find root for

        Returns:
            Root Studio object, or None if studio not found

        Examples:
            Get root studio:
            ```python
            root = await client.find_studio_root("child_studio_id")
            if root:
                print(f"Root studio: {root.name}")
            ```

            Compare studio with its root:
            ```python
            studio = await client.find_studio("studio_id")
            root = await client.find_studio_root("studio_id")
            if studio and root:
                if studio.id == root.id:
                    print("This is a root studio")
                else:
                    print(f"Root is: {root.name}")
            ```
        """
        hierarchy = await self.find_studio_hierarchy(studio_id)
        return hierarchy[0] if hierarchy else None

    async def map_studio_ids(
        self,
        studios: list[str | dict[str, Any] | Studio],
        create: bool = False,
    ) -> list[str]:
        """Convert studio names/objects to IDs, optionally creating missing studios.

        This is a convenience method to resolve studio references to their IDs,
        reducing boilerplate when working with studio relationships.

        Args:
            studios: List of studio references, can be:
                - str: Studio name (searches for exact match)
                - dict: Studio filter criteria (e.g., {"name": "Acme Studios"})
                - Studio: Studio object (extracts ID if present, otherwise searches by name)
            create: If True, create studios that don't exist. Default is False.

        Returns:
            List of studio IDs. Skips studios that aren't found (unless create=True).

        Examples:
            Map studio names to IDs:
            ```python
            studio_ids = await client.map_studio_ids(["Acme", "Foo Studios", "Bar Inc"])
            # Returns: ["1", "2", "3"] (IDs of existing studios)
            ```

            Auto-create missing studios:
            ```python
            studio_ids = await client.map_studio_ids(
                ["Acme", "NewStudio"],
                create=True
            )
            # Creates "NewStudio" if it doesn't exist
            ```

            Mix of strings and Studio objects:
            ```python
            studio_obj = Studio(name="Acme")
            studio_ids = await client.map_studio_ids([studio_obj, "Foo Studios"])
            ```

            Use in scene creation:
            ```python
            scene = Scene(
                title="My Scene",
                studio=None  # Will populate with studio ID
            )
            studio_ids = await client.map_studio_ids(["Acme"], create=True)
            if studio_ids:
                scene.studio = Studio(id=studio_ids[0])
            created_scene = await client.create_scene(scene)
            ```
        """
        studio_ids: list[str] = []

        for studio_input in studios:
            try:
                # Handle Studio objects
                studio_name: str | None = None
                if isinstance(studio_input, Studio):
                    # If studio has a server-assigned ID, use it directly
                    if not studio_input.is_new():
                        studio_ids.append(studio_input.id)
                        continue
                    # Otherwise search by name
                    studio_name = studio_input.name or ""

                # Handle string input (studio name)
                if isinstance(studio_input, str):
                    studio_name = studio_input

                if studio_name:
                    # Search for exact match
                    results = await self.find_studios(
                        studio_filter={
                            "name": {"value": studio_name, "modifier": "EQUALS"}
                        }
                    )
                    if results.count > 0:
                        studio_ids.append(results.studios[0].id)  # type: ignore[union-attr]
                    elif create:
                        # Create new studio
                        self.log.info(f"Creating missing studio: '{studio_name}'")
                        new_studio = await self.create_studio(Studio(name=studio_name))
                        studio_ids.append(new_studio.id)  # type: ignore[union-attr]
                    else:
                        self.log.warning(
                            f"Studio '{studio_name}' not found and create=False"
                        )

                # Handle dict input (filter criteria)
                elif isinstance(studio_input, dict):
                    name = studio_input.get("name")
                    if name:
                        results = await self.find_studios(
                            studio_filter={
                                "name": {"value": name, "modifier": "EQUALS"}
                            }
                        )
                        if results.count > 0:
                            studio_ids.append(results.studios[0].id)  # type: ignore[union-attr]
                        elif create:
                            self.log.info(f"Creating missing studio: '{name}'")
                            new_studio = await self.create_studio(Studio(name=name))
                            studio_ids.append(new_studio.id)  # type: ignore[union-attr]
                        else:
                            self.log.warning(
                                f"Studio '{name}' not found and create=False"
                            )

            except Exception as e:
                self.log.error(f"Failed to map studio {studio_input}: {e}")
                continue

        return studio_ids
