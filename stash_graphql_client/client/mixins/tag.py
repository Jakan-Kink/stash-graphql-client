"""Tag-related client functionality."""

from typing import Any

from ... import fragments
from ...types import FindTagsResultType, Tag, TagDestroyInput
from ..protocols import StashClientProtocol


class TagClientMixin(StashClientProtocol):
    """Mixin for tag-related client methods."""

    async def find_tag(self, id: str) -> Tag | None:
        """Find a tag by its ID.

        Args:
            id: The ID of the tag to find

        Returns:
            Tag object if found, None otherwise
        """
        try:
            result = await self.execute(
                fragments.FIND_TAG_QUERY,
                {"id": id},
            )
            if result and result.get("findTag"):
                return self._decode_result(Tag, result["findTag"])
            return None
        except Exception as e:
            self.log.error(f"Failed to find tag {id}: {e}")
            return None

    async def find_tags(
        self,
        filter_: dict[str, Any] | None = None,
        tag_filter: dict[str, Any] | None = None,
        q: str | None = None,
    ) -> FindTagsResultType:
        """Find tags matching the given filters.

        Args:
            filter_: Optional general filter parameters:
                - q: str (search query)
                - direction: SortDirectionEnum (ASC/DESC)
                - page: int
                - per_page: int
                - sort: str (field to sort by)
            tag_filter: Optional tag-specific filter
            q: Optional search query (alternative to filter_["q"])

        Returns:
            FindTagsResultType containing:
                - count: Total number of matching tags
                - tags: List of Tag objects

        Note:
        """
        if filter_ is None:
            filter_ = {"per_page": -1}
        try:
            # Add q to filter if provided
            if q is not None:
                filter_ = dict(filter_ or {})
                filter_["q"] = q

            result = await self.execute(
                fragments.FIND_TAGS_QUERY,
                {"filter": filter_, "tag_filter": tag_filter},
            )
            return FindTagsResultType(**result["findTags"])
        except Exception as e:
            self.log.error(f"Failed to find tags: {e}")
            return FindTagsResultType(count=0, tags=[])

    async def create_tag(self, tag: Tag) -> Tag:
        """Create a new tag in Stash.

        Args:
            tag: Tag object with the data to create. Required fields:
                - name: Tag name

        Returns:
            Created Tag object with ID and any server-generated fields

        Raises:
            ValueError: If the tag data is invalid
            gql.TransportError: If the request fails
        """
        try:
            input_data = await tag.to_input()
            result = await self.execute(
                fragments.CREATE_TAG_MUTATION,
                {"input": input_data},
            )
            return self._decode_result(Tag, result["tagCreate"])
        except Exception as e:
            error_message = str(e)
            if "tag with name" in error_message and "already exists" in error_message:
                self.log.info(
                    f"Tag '{tag.name}' already exists. Fetching existing tag."
                )
                # Clear both tag caches
                # Try to find the existing tag with exact name match
                results: FindTagsResultType = await self.find_tags(
                    tag_filter={"name": {"value": tag.name, "modifier": "EQUALS"}},
                )
                if results.count > 0:
                    # results.tags[0] is already a Pydantic Tag object
                    return results.tags[0]
                raise  # Re-raise if we couldn't find the tag
            self.log.error(f"Failed to create tag: {e}")
            raise

    async def tags_merge(
        self,
        source: list[str],
        destination: str,
    ) -> Tag:
        """Merge multiple tags into one.

        Args:
            source: List of source tag IDs to merge
            destination: Destination tag ID

        Returns:
            Updated destination Tag object

        Raises:
            ValueError: If the tag data is invalid
            gql.TransportError: If the request fails
        """
        try:
            result = await self.execute(
                fragments.TAGS_MERGE_MUTATION,
                {"input": {"source": source, "destination": destination}},
            )
            # Clear caches since we've modified tags
            return self._decode_result(Tag, result["tagsMerge"])
        except Exception as e:
            self.log.error(f"Failed to merge tags {source} into {destination}: {e}")
            raise

    async def bulk_tag_update(
        self,
        ids: list[str],
        description: str | None = None,
        aliases: list[str] | None = None,
        favorite: bool | None = None,
        parent_ids: list[str] | None = None,
        child_ids: list[str] | None = None,
    ) -> list[Tag]:
        """Update multiple tags at once.

        Args:
            ids: List of tag IDs to update
            description: Optional description to set
            aliases: Optional list of aliases to set
            favorite: Optional favorite flag to set
            parent_ids: Optional list of parent tag IDs to set
            child_ids: Optional list of child tag IDs to set

        Returns:
            List of updated Tag objects

        Raises:
            ValueError: If the tag data is invalid
            gql.TransportError: If the request fails
        """
        try:
            # Explicitly annotate the dictionary with precise type information
            input_data: dict[str, Any] = {"ids": ids}
            if description is not None:
                input_data["description"] = description  # Type is str, not list[str]
            if aliases is not None:
                input_data["aliases"] = aliases
            if favorite is not None:
                input_data["favorite"] = favorite  # Type is bool, not list[str]
            if parent_ids is not None:
                input_data["parent_ids"] = parent_ids
            if child_ids is not None:
                input_data["child_ids"] = child_ids

            result = await self.execute(
                fragments.BULK_TAG_UPDATE_MUTATION,
                {"input": input_data},
            )
            # Clear caches since we've modified tags
            return [self._decode_result(Tag, tag) for tag in result["bulkTagUpdate"]]
        except Exception as e:
            self.log.error(f"Failed to bulk update tags {ids}: {e}")
            raise

    async def update_tag(self, tag: Tag) -> Tag:
        """Update an existing tag in Stash.

        Args:
            tag: Tag object with updated data. Required fields:
                - id: Tag ID to update
                Any other fields that are set will be updated.
                Fields that are None will be ignored.

        Returns:
            Updated Tag object with any server-generated fields

        Raises:
            ValueError: If the tag data is invalid
            gql.TransportError: If the request fails
        """
        try:
            input_data = await tag.to_input()
            result = await self.execute(
                fragments.UPDATE_TAG_MUTATION,
                {"input": input_data},
            )
            # Clear caches since we've modified a tag
            return self._decode_result(Tag, result["tagUpdate"])
        except Exception as e:
            self.log.error(f"Failed to update tag: {e}")
            raise

    async def tag_destroy(
        self,
        input_data: TagDestroyInput | dict[str, Any],
    ) -> bool:
        """Delete a tag.

        Args:
            input_data: TagDestroyInput object or dictionary containing:
                - id: Tag ID to delete (required)

        Returns:
            True if the tag was successfully deleted

        Raises:
            ValueError: If the tag ID is invalid
            gql.TransportError: If the request fails
        """
        try:
            if isinstance(input_data, TagDestroyInput):
                input_dict = input_data.to_graphql()
            else:
                input_dict = input_data

            result = await self.execute(
                fragments.TAG_DESTROY_MUTATION,
                {"input": input_dict},
            )

            return bool(result.get("tagDestroy", False))
        except Exception as e:
            self.log.error(f"Failed to delete tag: {e}")
            raise

    async def tags_destroy(self, ids: list[str]) -> bool:
        """Delete multiple tags.

        Args:
            ids: List of tag IDs to delete

        Returns:
            True if the tags were successfully deleted

        Raises:
            ValueError: If any tag ID is invalid
            gql.TransportError: If the request fails
        """
        try:
            result = await self.execute(
                fragments.TAGS_DESTROY_MUTATION,
                {"ids": ids},
            )

            return bool(result.get("tagsDestroy", False))
        except Exception as e:
            self.log.error(f"Failed to delete tags: {e}")
            raise

    async def map_tag_ids(
        self,
        tags: list[str | dict[str, Any] | Tag],
        create: bool = False,
    ) -> list[str]:
        """Convert tag names/objects to IDs, optionally creating missing tags.

        This is a convenience method to resolve tag references to their IDs,
        reducing boilerplate when working with tag relationships.

        Args:
            tags: List of tag references, can be:
                - str: Tag name (searches for exact match)
                - dict: Tag filter criteria (e.g., {"name": "Action"})
                - Tag: Tag object (extracts ID if present, otherwise searches by name)
            create: If True, create tags that don't exist. Default is False.

        Returns:
            List of tag IDs. Skips tags that aren't found (unless create=True).

        Examples:
            Map tag names to IDs:
            ```python
            tag_ids = await client.map_tag_ids(["Action", "Drama", "Comedy"])
            # Returns: ["1", "2", "3"] (IDs of existing tags)
            ```

            Auto-create missing tags:
            ```python
            tag_ids = await client.map_tag_ids(
                ["Action", "NewTag", "Drama"],
                create=True
            )
            # Creates "NewTag" if it doesn't exist
            ```

            Mix of strings and Tag objects:
            ```python
            tag_obj = Tag(name="Action")
            tag_ids = await client.map_tag_ids([tag_obj, "Drama"])
            ```

            Use in scene creation:
            ```python
            scene = Scene(
                title="My Scene",
                tags=[]  # Will populate with tag IDs
            )
            scene.tags = await client.map_tag_ids(
                ["Action", "Drama"],
                create=True
            )
            created_scene = await client.create_scene(scene)
            ```
        """
        tag_ids: list[str] = []

        for tag_input in tags:
            try:
                # Handle Tag objects
                tag_name: str | None = None
                if isinstance(tag_input, Tag):
                    # If tag has an ID, use it directly
                    if tag_input.id:
                        tag_ids.append(tag_input.id)
                        continue
                    # Otherwise search by name
                    tag_name = tag_input.name or ""

                # Handle string input (tag name)
                if isinstance(tag_input, str):
                    tag_name = tag_input

                if tag_name:
                    # Search for exact match
                    results = await self.find_tags(
                        tag_filter={"name": {"value": tag_name, "modifier": "EQUALS"}}
                    )
                    if results.count > 0:
                        tag_ids.append(results.tags[0].id)  # type: ignore[union-attr]
                    elif create:
                        # Create new tag
                        self.log.info(f"Creating missing tag: '{tag_name}'")
                        new_tag = await self.create_tag(Tag(name=tag_name))
                        tag_ids.append(new_tag.id)  # type: ignore[union-attr]
                    else:
                        self.log.warning(f"Tag '{tag_name}' not found and create=False")

                # Handle dict input (filter criteria)
                elif isinstance(tag_input, dict):
                    name = tag_input.get("name")
                    if name:
                        results = await self.find_tags(
                            tag_filter={"name": {"value": name, "modifier": "EQUALS"}}
                        )
                        if results.count > 0:
                            tag_ids.append(results.tags[0].id)  # type: ignore[union-attr]
                        elif create:
                            self.log.info(f"Creating missing tag: '{name}'")
                            new_tag = await self.create_tag(Tag(name=name))
                            tag_ids.append(new_tag.id)  # type: ignore[union-attr]
                        else:
                            self.log.warning(f"Tag '{name}' not found and create=False")

            except Exception as e:
                self.log.error(f"Failed to map tag {tag_input}: {e}")
                continue

        return tag_ids
