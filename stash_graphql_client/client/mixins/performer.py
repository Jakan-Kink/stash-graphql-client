"""Performer-related client functionality."""

from typing import Any

from ... import fragments
from ...types import (
    BulkPerformerUpdateInput,
    FindPerformersResultType,
    OnMultipleMatch,
    Performer,
    PerformerDestroyInput,
)
from ..protocols import StashClientProtocol


class PerformerClientMixin(StashClientProtocol):
    """Mixin for performer-related client methods."""

    async def find_performer(
        self,
        performer: int | str | dict,
    ) -> Performer | None:
        """Find a performer by ID, name, or filter.

        Args:
            performer: Can be:
                - ID (int/str): Find by ID
                - Name (str): Find by name
                - Dict: Find by filter criteria

        Returns:
            Performer object if found, None otherwise

        Examples:
            Find by ID:
            ```python
            performer = await client.find_performer("123")
            if performer:
                print(f"Found performer: {performer.name}")
            ```

            Find by name:
            ```python
            performer = await client.find_performer("Performer Name")
            if performer:
                print(f"Found performer with ID: {performer.id}")
            ```

            Find by filter:
            ```python
            performer = await client.find_performer({
                "name": "Performer Name",
                "disambiguation": "2000s"
            })
            ```

            Access performer relationships:
            ```python
            performer = await client.find_performer("123")
            if performer:
                # Get scene titles
                scene_titles = [s.title for s in performer.scenes]
                # Get studio name
                studio_name = performer.studio.name if performer.studio else None
                # Get tag names
                tags = [t.name for t in performer.tags]
            ```
        """
        try:
            # Parse input to handle different types
            parsed_input = self._parse_obj_for_ID(performer)
            result = None  # Initialize to avoid unbound variable warning

            if isinstance(parsed_input, dict):
                # If it's a name filter, try name then alias
                name = parsed_input.get("name")
                if name:
                    # Try by name first
                    result = await self.find_performers(
                        performer_filter={"name": {"value": name, "modifier": "EQUALS"}}
                    )
                    if result.count > 0:
                        return result.performers[0]

                    # Try by alias
                    result = await self.find_performers(
                        performer_filter={
                            "aliases": {"value": name, "modifier": "INCLUDES"}
                        }
                    )
                    if result.count > 0:
                        return result.performers[0]

                    return None
            else:
                # If it's an ID, use direct lookup
                result = await self.execute(
                    fragments.FIND_PERFORMER_QUERY,
                    {"id": str(parsed_input)},
                )
                if result and result.get("findPerformer"):
                    return self._decode_result(Performer, result["findPerformer"])
                return None
            return None
        except Exception as e:
            self.log.error(f"Failed to find performer {performer}: {e}")
            return None

    async def find_performers(
        self,
        filter_: dict[str, Any] | None = None,
        performer_filter: dict[str, Any] | None = None,
        q: str | None = None,
    ) -> FindPerformersResultType:
        """Find performers matching the given filters.

        Args:
            filter_: Optional general filter parameters:
                - q: str (search query)
                - direction: SortDirectionEnum (ASC/DESC)
                - page: int
                - per_page: int
                - sort: str (field to sort by)
            q: Optional search query (alternative to filter_["q"])
            performer_filter: Optional performer-specific filter:
                - birth_year: IntCriterionInput
                - age: IntCriterionInput
                - ethnicity: StringCriterionInput
                - country: StringCriterionInput
                - eye_color: StringCriterionInput
                - height: StringCriterionInput
                - measurements: StringCriterionInput
                - fake_tits: StringCriterionInput
                - career_length: StringCriterionInput
                - tattoos: StringCriterionInput
                - piercings: StringCriterionInput
                - favorite: bool
                - rating100: IntCriterionInput
                - gender: GenderEnum
                - is_missing: str (what data is missing)
                - name: StringCriterionInput
                - studios: HierarchicalMultiCriterionInput
                - tags: HierarchicalMultiCriterionInput

        Returns:
            FindPerformersResultType containing:
                - count: Total number of matching performers
                - performers: List of Performer objects

        Examples:
            Find all favorite performers:
            ```python
            result = await client.find_performers(
                performer_filter={"favorite": True}
            )
            print(f"Found {result.count} favorite performers")
            for performer in result.performers:
                print(f"- {performer.name}")
            ```

            Find performers with specific tags:
            ```python
            result = await client.find_performers(
                performer_filter={
                    "tags": {
                        "value": ["tag1", "tag2"],
                        "modifier": "INCLUDES_ALL"
                    }
                }
            )
            ```

            Find performers with high rating and sort by name:
            ```python
            result = await client.find_performers(
                filter_={
                    "direction": "ASC",
                    "sort": "name",
                },
                performer_filter={
                    "rating100": {
                        "value": 80,
                        "modifier": "GREATER_THAN"
                    }
                }
            )
            ```

            Paginate results:
            ```python
            result = await client.find_performers(
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
                filter_ = dict(filter_)  # Copy since we have a default
                filter_["q"] = q

            result = await self.execute(
                fragments.FIND_PERFORMERS_QUERY,
                {"filter": filter_, "performer_filter": performer_filter},
            )
            return FindPerformersResultType(**result["findPerformers"])
        except Exception as e:
            self.log.error(f"Failed to find performers: {e}")
            return FindPerformersResultType(count=0, performers=[])

    async def create_performer(self, performer: Performer) -> Performer:
        """Create a new performer in Stash.

        Args:
            performer: Performer object with the data to create. Required fields:
                - name: Performer name

        Returns:
            Created Performer object with ID and any server-generated fields

        Raises:
            ValueError: If the performer data is invalid
            gql.TransportError: If the request fails

        Examples:
            Create a basic performer:
            ```python
            performer = Performer(
                name="Performer Name",
            )
            created = await client.create_performer(performer)
            print(f"Created performer with ID: {created.id}")
            ```

            Create performer with metadata:
            ```python
            performer = Performer(
                name="Performer Name",
                # Add metadata
                gender="FEMALE",
                birthdate="1990-01-01",
                ethnicity="Caucasian",
                country="USA",
                eye_color="Blue",
                height_cm=170,
                measurements="34B-24-36",
                fake_tits="No",
                career_length="2010-2020",
                tattoos="None",
                piercings="Ears",
                url="https://example.com/performer",
                twitter="@performer",
                instagram="@performer",
                details="Performer details",
            )
            created = await client.create_performer(performer)
            ```

            Create performer with relationships:
            ```python
            performer = Performer(
                name="Performer Name",
                # Add relationships
                tags=[tag1, tag2],
                image="https://example.com/image.jpg",
                stash_ids=[stash_id1, stash_id2],
            )
            created = await client.create_performer(performer)
            ```
        """
        try:
            input_data = await performer.to_input()
            result = await self.execute(
                fragments.CREATE_PERFORMER_MUTATION,
                {"input": input_data},
            )
            return self._decode_result(Performer, result["performerCreate"])
        except Exception as e:
            error_message = str(e)
            if (
                "performer with name" in error_message
                and "already exists" in error_message
            ):
                self.log.info(
                    f"Performer '{performer.name}' already exists. Fetching existing performer."
                )
                # Clear both performer caches since we have a new performer
                # Try to find the existing performer with exact name match
                result = await self.find_performers(
                    performer_filter={
                        "name": {"value": performer.name, "modifier": "EQUALS"}
                    },
                )
                if result.count > 0:
                    return result.performers[0]
                raise  # Re-raise if we couldn't find the performer

            self.log.error(f"Failed to create performer: {e}")
            raise

    async def update_performer(self, performer: Performer) -> Performer:
        """Update an existing performer in Stash.

        Args:
            performer: Performer object with updated data. Required fields:
                - id: Performer ID to update
                Any other fields that are set will be updated.
                Fields that are None will be ignored.

        Returns:
            Updated Performer object with any server-generated fields

        Raises:
            ValueError: If the performer data is invalid
            gql.TransportError: If the request fails

        Examples:
            Update performer name and metadata:
            ```python
            performer = await client.find_performer("123")
            if performer:
                performer.name = "New Name"
                performer.gender = "FEMALE"
                performer.birthdate = "1990-01-01"
                updated = await client.update_performer(performer)
                print(f"Updated performer: {updated.name}")
            ```

            Update performer relationships:
            ```python
            performer = await client.find_performer("123")
            if performer:
                # Add new tags
                performer.tags.extend([new_tag1, new_tag2])
                # Update image
                performer.image = "https://example.com/new-image.jpg"
                updated = await client.update_performer(performer)
            ```

            Update performer URLs:
            ```python
            performer = await client.find_performer("123")
            if performer:
                # Replace URLs
                performer.url = "https://example.com/new-url"
                performer.twitter = "@new_twitter"
                performer.instagram = "@new_instagram"
                updated = await client.update_performer(performer)
            ```

            Remove performer relationships:
            ```python
            performer = await client.find_performer("123")
            if performer:
                # Clear tags
                performer.tags = []
                # Clear image
                performer.image = None
                updated = await client.update_performer(performer)
            ```
        """
        try:
            input_data = await performer.to_input()
            result = await self.execute(
                fragments.UPDATE_PERFORMER_MUTATION,
                {"input": input_data},
            )
            return self._decode_result(Performer, result["performerUpdate"])
        except Exception as e:
            self.log.error(f"Failed to update performer: {e}")
            raise

    async def update_performer_image(
        self, performer: Performer, image_url: str
    ) -> Performer:
        """Update a performer's image.

        Args:
            performer: Performer object with at least the ID set
            image_url: URL or data URI of the image to set

        Returns:
            Updated Performer object with the new image

        Raises:
            ValueError: If the performer data is invalid
            gql.TransportError: If the request fails

        Examples:
            Update performer image with a data URI:
            ```python
            performer = await client.find_performer("123")
            if performer:
                # Update with data URI
                image_url = "data:image/jpeg;base64,..."
                updated = await client.update_performer_image(performer, image_url)
            ```

            Update performer image from a file:
            ```python
            performer = await client.find_performer("123")
            if performer:
                # Use the performer's update_avatar method
                updated = await performer.update_avatar(client, "/path/to/image.jpg")
            ```
        """
        try:
            # Create a minimal input with just ID and image
            input_data = {"id": performer.id, "image": image_url}

            result = await self.execute(
                fragments.UPDATE_PERFORMER_MUTATION,
                {"input": input_data},
            )
            return self._decode_result(Performer, result["performerUpdate"])
        except Exception as e:
            self.log.error(f"Failed to update performer image: {e}")
            raise

    async def performer_destroy(
        self,
        input_data: PerformerDestroyInput | dict[str, Any],
    ) -> bool:
        """Delete a performer.

        Args:
            input_data: PerformerDestroyInput object or dictionary containing:
                - id: Performer ID to delete (required)

        Returns:
            True if the performer was successfully deleted

        Raises:
            ValueError: If the performer ID is invalid
            gql.TransportError: If the request fails

        Examples:
            Delete a performer:
            ```python
            result = await client.performer_destroy({"id": "123"})
            print(f"Performer deleted: {result}")
            ```

            Using the input type:
            ```python
            from ...types import PerformerDestroyInput

            input_data = PerformerDestroyInput(id="123")
            result = await client.performer_destroy(input_data)
            ```
        """
        try:
            # Convert PerformerDestroyInput to dict if needed
            if isinstance(input_data, PerformerDestroyInput):
                input_dict = input_data.to_graphql()
            else:
                input_dict = input_data

            result = await self.execute(
                fragments.PERFORMER_DESTROY_MUTATION,
                {"input": input_dict},
            )

            return bool(result.get("performerDestroy", False))
        except Exception as e:
            self.log.error(f"Failed to delete performer: {e}")
            raise

    async def performers_destroy(self, ids: list[str]) -> bool:
        """Delete multiple performers.

        Args:
            ids: List of performer IDs to delete

        Returns:
            True if the performers were successfully deleted

        Raises:
            ValueError: If any performer ID is invalid
            gql.TransportError: If the request fails

        Examples:
            Delete multiple performers:
            ```python
            result = await client.performers_destroy(["123", "456", "789"])
            print(f"Performers deleted: {result}")
            ```
        """
        try:
            result = await self.execute(
                fragments.PERFORMERS_DESTROY_MUTATION,
                {"ids": ids},
            )

            return bool(result.get("performersDestroy", False))
        except Exception as e:
            self.log.error(f"Failed to delete performers: {e}")
            raise

    async def all_performers(self) -> list[Performer]:
        """Get all performers."""
        try:
            result = await self.execute(fragments.ALL_PERFORMERS_QUERY, {})
            performers_data = result.get("allPerformers", [])
            return [self._decode_result(Performer, p) for p in performers_data]
        except Exception as e:
            self.log.error(f"Failed to get all performers: {e}")
            return []

    async def bulk_performer_update(
        self,
        input_data: BulkPerformerUpdateInput | dict[str, Any],
    ) -> list[Performer]:
        """Bulk update performers.

        Args:
            input_data: BulkPerformerUpdateInput object or dictionary containing:
                - ids: List of performer IDs to update (optional)
                - And any fields to update (e.g., gender, birthdate, tags, etc.)

        Returns:
            List of updated Performer objects

        Examples:
            Update multiple performers' gender:
            ```python
            performers = await client.bulk_performer_update({
                "ids": ["1", "2", "3"],
                "gender": "FEMALE"
            })
            ```

            Add tags to multiple performers:
            ```python
            from stash_graphql_client.types import BulkPerformerUpdateInput, BulkUpdateIds

            input_data = BulkPerformerUpdateInput(
                ids=["1", "2", "3"],
                tag_ids=BulkUpdateIds(ids=["tag1", "tag2"], mode="ADD")
            )
            performers = await client.bulk_performer_update(input_data)
            ```
        """
        try:
            # Convert BulkPerformerUpdateInput to dict if needed
            if isinstance(input_data, BulkPerformerUpdateInput):
                input_dict = input_data.to_graphql()
            else:
                input_dict = input_data

            result = await self.execute(
                fragments.BULK_PERFORMER_UPDATE_MUTATION,
                {"input": input_dict},
            )

            performers_data = result.get("bulkPerformerUpdate", [])
            return [self._decode_result(Performer, p) for p in performers_data]
        except Exception as e:
            self.log.error(f"Failed to bulk update performers: {e}")
            raise

    async def map_performer_ids(
        self,
        performers: list[str | dict[str, Any] | Performer],
        create: bool = False,
        on_multiple: OnMultipleMatch = OnMultipleMatch.RETURN_FIRST,
    ) -> list[str]:
        """Convert performer names/objects to IDs, optionally creating missing performers.

        This is a convenience method to resolve performer references to their IDs,
        reducing boilerplate when working with performer relationships.

        Args:
            performers: List of performer references, can be:
                - str: Performer name (searches by name, then aliases)
                - dict: Performer filter criteria (e.g., {"name": "John", "disambiguation": "Actor"})
                - Performer: Performer object (extracts ID if present, otherwise searches by name)
            create: If True, create performers that don't exist. Default is False.
            on_multiple: Strategy when multiple matches found. Default is RETURN_FIRST.

        Returns:
            List of performer IDs. Skips performers that aren't found (unless create=True).

        Examples:
            Map performer names to IDs:
            ```python
            performer_ids = await client.map_performer_ids(["Jane Doe", "John Smith"])
            # Returns: ["1", "2"] (IDs of existing performers)
            ```

            Auto-create missing performers:
            ```python
            performer_ids = await client.map_performer_ids(
                ["Jane Doe", "NewPerformer"],
                create=True
            )
            # Creates "NewPerformer" if it doesn't exist
            ```

            Handle multiple matches:
            ```python
            performer_ids = await client.map_performer_ids(
                ["AmbiguousName"],
                on_multiple=OnMultipleMatch.RETURN_NONE  # Skip ambiguous matches
            )
            ```

            Use in scene creation:
            ```python
            scene = Scene(
                title="My Scene",
                performers=[]  # Will populate with performer IDs
            )
            scene.performers = await client.map_performer_ids(
                ["Jane Doe", "John Smith"],
                create=True
            )
            created_scene = await client.create_scene(scene)
            ```
        """
        performer_ids: list[str] = []

        for performer_input in performers:
            try:
                # Handle Performer objects
                performer_name: str | None = None
                if isinstance(performer_input, Performer):
                    # If performer has a server-assigned ID, use it directly
                    if not performer_input.is_new():
                        performer_ids.append(performer_input.id)
                        continue
                    # Otherwise search by name
                    performer_name = performer_input.name or ""

                # Handle string input (performer name)
                if isinstance(performer_input, str):
                    performer_name = performer_input

                if performer_name:
                    # Search by name first
                    results = await self.find_performers(
                        performer_filter={
                            "name": {"value": performer_name, "modifier": "EQUALS"}
                        }
                    )

                    # If not found by name, try aliases
                    if results.count == 0:
                        results = await self.find_performers(
                            performer_filter={
                                "aliases": {
                                    "value": performer_name,
                                    "modifier": "INCLUDES",
                                }
                            }
                        )

                    if results.count > 1:
                        # Handle multiple matches based on strategy
                        if on_multiple == OnMultipleMatch.RETURN_NONE:
                            self.log.warning(
                                f"Multiple performers matched '{performer_name}', skipping (on_multiple=RETURN_NONE)"
                            )
                            continue
                        if on_multiple == OnMultipleMatch.RETURN_FIRST:
                            self.log.warning(
                                f"Multiple performers matched '{performer_name}', using first match"
                            )
                            performer_ids.append(results.performers[0].id)  # type: ignore[union-attr]
                        # RETURN_LIST not applicable here since we're building a flat ID list
                        else:
                            self.log.warning(
                                f"Multiple performers matched '{performer_name}', using first match"
                            )
                            performer_ids.append(results.performers[0].id)  # type: ignore[union-attr]

                    elif results.count == 1:
                        performer_ids.append(results.performers[0].id)  # type: ignore[union-attr]
                    elif create:
                        # Create new performer
                        self.log.info(f"Creating missing performer: '{performer_name}'")
                        new_performer = await self.create_performer(
                            Performer(name=performer_name)
                        )
                        performer_ids.append(new_performer.id)  # type: ignore[union-attr]
                    else:
                        self.log.warning(
                            f"Performer '{performer_name}' not found and create=False"
                        )

                # Handle dict input (filter criteria)
                elif isinstance(performer_input, dict):
                    name = performer_input.get("name")
                    if name:
                        results = await self.find_performers(
                            performer_filter={
                                "name": {"value": name, "modifier": "EQUALS"}
                            }
                        )

                        if results.count > 1:
                            if on_multiple == OnMultipleMatch.RETURN_NONE:
                                self.log.warning(
                                    f"Multiple performers matched '{name}', skipping (on_multiple=RETURN_NONE)"
                                )
                                continue
                            if on_multiple == OnMultipleMatch.RETURN_FIRST:
                                self.log.warning(
                                    f"Multiple performers matched '{name}', using first match"
                                )
                                performer_ids.append(results.performers[0].id)  # type: ignore[union-attr]
                            else:
                                # Default behavior: use first match
                                self.log.warning(
                                    f"Multiple performers matched '{name}', using first match"
                                )
                                performer_ids.append(results.performers[0].id)  # type: ignore[union-attr]
                        elif results.count == 1:
                            performer_ids.append(results.performers[0].id)  # type: ignore[union-attr]
                        elif create:
                            self.log.info(f"Creating missing performer: '{name}'")
                            new_performer = await self.create_performer(
                                Performer(name=name)
                            )
                            performer_ids.append(new_performer.id)  # type: ignore[union-attr]
                        else:
                            self.log.warning(
                                f"Performer '{name}' not found and create=False"
                            )

            except Exception as e:
                self.log.error(f"Failed to map performer {performer_input}: {e}")
                continue

        return performer_ids
