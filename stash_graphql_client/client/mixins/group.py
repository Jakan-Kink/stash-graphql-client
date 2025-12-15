"""Group-related client functionality."""

from typing import Any

from ... import fragments
from ...types import (
    BulkGroupUpdateInput,
    FindGroupsResultType,
    Group,
    GroupDestroyInput,
    GroupSubGroupAddInput,
    GroupSubGroupRemoveInput,
    ReorderSubGroupsInput,
)
from ..protocols import StashClientProtocol


class GroupClientMixin(StashClientProtocol):
    """Mixin for group-related client methods."""

    async def find_group(self, group_id: str) -> Group | None:
        """Find a group by ID.

        Args:
            group_id: Group ID to search for

        Returns:
            Group object if found, None otherwise

        Examples:
            ```python
            group = await client.find_group("123")
            if group:
                print(f"Found group: {group.name}")
                print(f"Duration: {group.duration} seconds")
                print(f"Director: {group.director}")
            ```

            Access group relationships:
            ```python
            group = await client.find_group("123")
            if group:
                # Get scene titles
                scene_titles = [s.title for s in group.scenes]
                # Get studio name
                studio_name = group.studio.name if group.studio else None
                # Get tag names
                tags = [t.name for t in group.tags]
                # Get sub-groups
                sub_groups = [sg.group.name for sg in group.sub_groups]
            ```
        """
        try:
            # Use result_type to let execute() handle Pydantic decoding with field aliases
            result = await self.execute(
                fragments.FIND_GROUP_QUERY,
                {"id": group_id},
                result_type=Group,
            )
            return result if result else None
        except Exception as e:
            self.log.error(f"Failed to find group {group_id}: {e}")
            return None

    async def find_groups(
        self,
        filter_: dict[str, Any] | None = None,
        group_filter: dict[str, Any] | None = None,
        ids: list[str] | None = None,
        q: str | None = None,
    ) -> FindGroupsResultType:
        """Find groups matching the given filters.

        Args:
            filter_: Optional general filter parameters:
                - q: str (search query)
                - direction: SortDirectionEnum (ASC/DESC)
                - page: int
                - per_page: int
                - sort: str (field to sort by)
            group_filter: Optional group-specific filter:
                - name: StringCriterionInput
                - director: StringCriterionInput
                - synopsis: StringCriterionInput
                - duration: IntCriterionInput
                - rating100: IntCriterionInput
                - date: DateCriterionInput
                - url: StringCriterionInput
                - is_missing: str (what data is missing)
                - studios: HierarchicalMultiCriterionInput
                - tags: HierarchicalMultiCriterionInput
            ids: Optional list of group IDs to filter by
            q: Optional search query (alternative to filter_["q"])

        Returns:
            FindGroupsResultType containing:
                - count: Total number of matching groups
                - groups: List of Group objects

        Examples:
            Find all groups:
            ```python
            result = await client.find_groups()
            print(f"Found {result.count} groups")
            for group in result.groups:
                print(f"- {group.name}")
            ```

            Search by name:
            ```python
            result = await client.find_groups(q="Action")
            print(f"Found {result.count} groups matching 'Action'")
            ```

            Find groups by filter:
            ```python
            result = await client.find_groups(
                group_filter={
                    "name": {
                        "value": "Series",
                        "modifier": "INCLUDES"
                    }
                }
            )
            ```

            Find groups with specific tags:
            ```python
            result = await client.find_groups(
                group_filter={
                    "tags": {
                        "value": ["tag1", "tag2"],
                        "modifier": "INCLUDES_ALL"
                    }
                }
            )
            ```

            Find groups with high rating and sort by name:
            ```python
            result = await client.find_groups(
                filter_={
                    "direction": "ASC",
                    "sort": "name",
                },
                group_filter={
                    "rating100": {
                        "value": 80,
                        "modifier": "GREATER_THAN"
                    }
                }
            )
            ```

            Paginate results:
            ```python
            result = await client.find_groups(
                filter_={
                    "page": 1,
                    "per_page": 25,
                }
            )
            ```

            Find specific groups by IDs:
            ```python
            result = await client.find_groups(ids=["123", "456", "789"])
            ```
        """
        if filter_ is None:
            filter_ = {"per_page": -1}
        try:
            # Add q to filter if provided
            if q is not None:
                filter_ = dict(filter_)  # Copy since we have a default
                filter_["q"] = q

            result = await self.execute(
                fragments.FIND_GROUPS_QUERY,
                {"filter": filter_, "group_filter": group_filter, "ids": ids},
            )
            return self._decode_result(FindGroupsResultType, result["findGroups"])
        except Exception as e:
            self.log.error(f"Failed to find groups: {e}")
            return FindGroupsResultType(count=0, groups=[])

    async def create_group(self, group: Group) -> Group:
        """Create a new group in Stash.

        Args:
            group: Group object with the data to create. Required fields:
                - name: Group name

        Returns:
            Created Group object with ID and any server-generated fields

        Raises:
            ValueError: If the group data is invalid
            gql.TransportError: If the request fails

        Examples:
            Create a basic group:
            ```python
            group = Group(name="Test Series")
            created = await client.create_group(group)
            print(f"Created group with ID: {created.id}")
            ```

            Create group with metadata:
            ```python
            group = Group(
                name="Action Movie Series",
                director="John Director",
                synopsis="An action-packed series",
                duration=7200,
                date="2020-01-01",
                rating100=85,
            )
            created = await client.create_group(group)
            ```

            Create group with relationships:
            ```python
            from stash_graphql_client.types import Tag, Studio

            # Fetch tags and studio
            tag1 = await client.find_tag("tag1_id")
            tag2 = await client.find_tag("tag2_id")
            studio = await client.find_studio("studio_id")

            group = Group(
                name="Tagged Group",
                tags=[tag1, tag2],
                studio=studio,
            )
            created = await client.create_group(group)
            ```
        """
        input_data = await group.to_input()
        return await self.execute(
            fragments.CREATE_GROUP_MUTATION,
            {"input": input_data},
            result_type=Group,
        )

    async def update_group(self, group: Group) -> Group:
        """Update an existing group in Stash.

        Args:
            group: Group object with updated data. Must include ID field.

        Returns:
            Updated Group object

        Raises:
            ValueError: If the group ID is missing or data is invalid
            gql.TransportError: If the request fails

        Examples:
            Update group name and director:
            ```python
            group = await client.find_group("123")
            group.name = "Updated Name"
            group.director = "New Director"
            updated = await client.update_group(group)
            ```

            Update group rating:
            ```python
            group = await client.find_group("123")
            group.rating100 = 90
            updated = await client.update_group(group)
            ```

            Update group tags:
            ```python
            group = await client.find_group("123")
            tag1 = await client.find_tag("tag1_id")
            tag2 = await client.find_tag("tag2_id")
            group.tags = [tag1, tag2]
            updated = await client.update_group(group)
            ```
        """
        if not group.id:
            raise ValueError("Group must have an ID to update")

        input_data = await group.to_input()
        return await self.execute(
            fragments.UPDATE_GROUP_MUTATION,
            {"input": input_data},
            result_type=Group,
        )

    async def group_destroy(
        self, input_data: GroupDestroyInput | dict[str, Any]
    ) -> bool:
        """Delete a group from Stash.

        Args:
            input_data: GroupDestroyInput or dict with:
                - id: Group ID to delete

        Returns:
            True if deletion was successful

        Raises:
            gql.TransportError: If the request fails

        Examples:
            Delete by ID using dict:
            ```python
            result = await client.group_destroy({"id": "123"})
            if result:
                print("Group deleted successfully")
            ```

            Delete using GroupDestroyInput:
            ```python
            from stash_graphql_client.types import GroupDestroyInput

            input_data = GroupDestroyInput(id="123")
            result = await client.group_destroy(input_data)
            ```
        """
        if isinstance(input_data, dict):
            input_data = GroupDestroyInput(**input_data)

        result = await self.execute(
            fragments.GROUP_DESTROY_MUTATION,
            {"input": input_data.to_graphql()},
        )
        return result.get("groupDestroy", False)

    async def groups_destroy(self, ids: list[str]) -> bool:
        """Delete multiple groups from Stash.

        Args:
            ids: List of group IDs to delete

        Returns:
            True if deletion was successful

        Raises:
            gql.TransportError: If the request fails

        Examples:
            ```python
            result = await client.groups_destroy(["123", "456", "789"])
            if result:
                print("Groups deleted successfully")
            ```
        """
        result = await self.execute(
            fragments.GROUPS_DESTROY_MUTATION,
            {"ids": ids},
        )
        return result.get("groupsDestroy", False)

    async def bulk_group_update(
        self, input_data: BulkGroupUpdateInput | dict[str, Any]
    ) -> list[Group]:
        """Bulk update multiple groups.

        Args:
            input_data: BulkGroupUpdateInput or dict with:
                - ids: List of group IDs to update
                - rating100: Optional rating (1-100)
                - studio_id: Optional studio ID
                - director: Optional director name
                - urls: Optional list of URLs
                - tag_ids: Optional list of tag IDs
                - containing_groups: Optional groups that contain these groups
                - sub_groups: Optional sub-groups

        Returns:
            List of updated Group objects

        Raises:
            gql.TransportError: If the request fails

        Examples:
            Update rating for multiple groups:
            ```python
            result = await client.bulk_group_update({
                "ids": ["1", "2", "3"],
                "rating100": 85
            })
            print(f"Updated {len(result)} groups")
            ```

            Add tags to multiple groups:
            ```python
            from stash_graphql_client.types import BulkGroupUpdateInput

            input_data = BulkGroupUpdateInput(
                ids=["1", "2", "3"],
                tag_ids=["tag1", "tag2"]
            )
            result = await client.bulk_group_update(input_data)
            ```

            Set studio for multiple groups:
            ```python
            result = await client.bulk_group_update({
                "ids": ["1", "2", "3"],
                "studio_id": "studio_123"
            })
            ```
        """
        if isinstance(input_data, dict):
            input_data = BulkGroupUpdateInput(**input_data)

        result = await self.execute(
            fragments.BULK_GROUP_UPDATE_MUTATION,
            {"input": input_data.to_graphql()},
        )
        return [
            self._decode_result(Group, g) for g in result.get("bulkGroupUpdate", [])
        ]

    async def add_group_sub_groups(
        self, input_data: GroupSubGroupAddInput | dict[str, Any]
    ) -> bool:
        """Add sub-groups to a group.

        Args:
            input_data: GroupSubGroupAddInput or dict with:
                - containing_group_id: ID of the parent group
                - sub_groups: List of GroupDescriptionInput dicts with group_id and optional description
                - insert_index: Optional index at which to insert (default: append to end)

        Returns:
            True if successful

        Raises:
            gql.TransportError: If the request fails

        Examples:
            Add sub-groups to end:
            ```python
            result = await client.add_group_sub_groups({
                "containing_group_id": "parent_123",
                "sub_groups": [
                    {"group_id": "child_456"},
                    {"group_id": "child_789", "description": "Episode 1"}
                ]
            })
            ```

            Insert sub-groups at specific index:
            ```python
            from stash_graphql_client.types import (
                GroupSubGroupAddInput,
                GroupDescriptionInput
            )

            input_data = GroupSubGroupAddInput(
                containing_group_id="parent_123",
                sub_groups=[
                    GroupDescriptionInput(group_id="child_456", description="Episode 2")
                ],
                insert_index=1
            )
            result = await client.add_group_sub_groups(input_data)
            ```
        """
        if isinstance(input_data, dict):
            input_data = GroupSubGroupAddInput(**input_data)

        result = await self.execute(
            fragments.ADD_GROUP_SUB_GROUPS_MUTATION,
            {"input": input_data.to_graphql()},
        )
        return result.get("addGroupSubGroups", False)

    async def remove_group_sub_groups(
        self, input_data: GroupSubGroupRemoveInput | dict[str, Any]
    ) -> bool:
        """Remove sub-groups from a group.

        Args:
            input_data: GroupSubGroupRemoveInput or dict with:
                - containing_group_id: ID of the parent group
                - sub_group_ids: List of sub-group IDs to remove

        Returns:
            True if successful

        Raises:
            gql.TransportError: If the request fails

        Examples:
            Remove sub-groups:
            ```python
            result = await client.remove_group_sub_groups({
                "containing_group_id": "parent_123",
                "sub_group_ids": ["child_456", "child_789"]
            })
            ```

            Using typed input:
            ```python
            from stash_graphql_client.types import GroupSubGroupRemoveInput

            input_data = GroupSubGroupRemoveInput(
                containing_group_id="parent_123",
                sub_group_ids=["child_456", "child_789"]
            )
            result = await client.remove_group_sub_groups(input_data)
            ```
        """
        if isinstance(input_data, dict):
            input_data = GroupSubGroupRemoveInput(**input_data)

        result = await self.execute(
            fragments.REMOVE_GROUP_SUB_GROUPS_MUTATION,
            {"input": input_data.to_graphql()},
        )
        return result.get("removeGroupSubGroups", False)

    async def reorder_sub_groups(
        self, input_data: ReorderSubGroupsInput | dict[str, Any]
    ) -> bool:
        """Reorder sub-groups within a group.

        Args:
            input_data: ReorderSubGroupsInput or dict with:
                - group_id: ID of the parent group
                - sub_group_ids: List of sub-group IDs to reorder (must be subset of existing)
                - insert_at_id: Sub-group ID at which to insert the reordered groups
                - insert_after: If True, insert after insert_at_id; if False, insert before

        Returns:
            True if successful

        Raises:
            gql.TransportError: If the request fails

        Examples:
            Reorder sub-groups:
            ```python
            result = await client.reorder_sub_groups({
                "group_id": "parent_123",
                "sub_group_ids": ["child_2", "child_3"],
                "insert_at_id": "child_1",
                "insert_after": True
            })
            ```

            Using typed input:
            ```python
            from stash_graphql_client.types import ReorderSubGroupsInput

            input_data = ReorderSubGroupsInput(
                group_id="parent_123",
                sub_group_ids=["child_2", "child_3"],
                "insert_at_id": "child_1",
                insert_after=False
            )
            result = await client.reorder_sub_groups(input_data)
            ```
        """
        if isinstance(input_data, dict):
            input_data = ReorderSubGroupsInput(**input_data)

        result = await self.execute(
            fragments.REORDER_SUB_GROUPS_MUTATION,
            {"input": input_data.to_graphql()},
        )
        return result.get("reorderSubGroups", False)
