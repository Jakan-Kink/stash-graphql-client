"""Image-related client functionality."""

from typing import Any

from ... import fragments
from ...types import (
    BulkImageUpdateInput,
    FindImagesResultType,
    Image,
    ImageDestroyInput,
    ImagesDestroyInput,
    ImageUpdateInput,
)
from ..protocols import StashClientProtocol


class ImageClientMixin(StashClientProtocol):
    """Mixin for image-related client methods."""

    async def find_image(self, id: str) -> Image | None:
        """Find an image by its ID.

        Args:
            id: The ID of the image to find

        Returns:
            Image object if found, None otherwise
        """
        try:
            result = await self.execute(
                fragments.FIND_IMAGE_QUERY,
                {"id": id},
            )
            if result and result.get("findImage"):
                return self._decode_result(Image, result["findImage"])
            return None
        except Exception as e:
            self.log.error(f"Failed to find image {id}: {e}")
            return None

    async def find_images(
        self,
        filter_: dict[str, Any] | None = None,
        image_filter: dict[str, Any] | None = None,
        q: str | None = None,
    ) -> FindImagesResultType:
        """Find images matching the given filters.

        Args:
            filter_: Optional general filter parameters:
                - q: str (search query)
                - direction: SortDirectionEnum (ASC/DESC)
                - page: int
                - per_page: int
                - sort: str (field to sort by)
            image_filter: Optional image-specific filter
            q: Optional search query (alternative to filter_["q"])

        Returns:
            FindImagesResultType containing:
                - count: Total number of matching images
                - images: List of Image objects
        """
        if filter_ is None:
            filter_ = {"per_page": -1}
        try:
            # Add q to filter if provided
            if q is not None:
                filter_ = dict(filter_ or {})
                filter_["q"] = q

            result = await self.execute(
                fragments.FIND_IMAGES_QUERY,
                {"filter": filter_, "image_filter": image_filter},
            )
            return self._decode_result(FindImagesResultType, result["findImages"])
        except Exception as e:
            self.log.error(f"Failed to find images: {e}")
            return FindImagesResultType(
                count=0, images=[], megapixels=0.0, filesize=0.0
            )

    async def create_image(self, image: Image) -> Image:
        """Create a new image in Stash.

        Args:
            image: Image object with the data to create. Required fields:
                - title: Image title

        Returns:
            Created Image object with ID and any server-generated fields

        Raises:
            ValueError: If the image data is invalid
            gql.TransportError: If the request fails
        """
        try:
            input_data = await image.to_input()
            result = await self.execute(
                fragments.CREATE_IMAGE_MUTATION,
                {"input": input_data},
            )
            return self._decode_result(Image, result["imageCreate"])
        except Exception as e:
            self.log.error(f"Failed to create image: {e}")
            raise

    async def update_image(self, image: Image) -> Image:
        """Update an existing image in Stash.

        Args:
            image: Image object with updated data. Required fields:
                - id: Image ID to update
                Any other fields that are set will be updated.
                Fields that are None will be ignored.

        Returns:
            Updated Image object with any server-generated fields

        Raises:
            ValueError: If the image data is invalid
            gql.TransportError: If the request fails
        """
        try:
            input_data = await image.to_input()
            result = await self.execute(
                fragments.UPDATE_IMAGE_MUTATION,
                {"input": input_data},
            )
            return self._decode_result(Image, result["imageUpdate"])
        except Exception as e:
            self.log.error(f"Failed to update image: {e}")
            raise

    async def image_destroy(
        self,
        input_data: ImageDestroyInput | dict[str, Any],
    ) -> bool:
        """Delete an image.

        Args:
            input_data: ImageDestroyInput object or dictionary containing:
                - id: Image ID to delete (required)
                - delete_file: Whether to delete the image's file (optional, default: False)
                - delete_generated: Whether to delete generated files (optional, default: True)

        Returns:
            True if the image was successfully deleted

        Raises:
            ValueError: If the image ID is invalid
            gql.TransportError: If the request fails
        """
        try:
            if isinstance(input_data, ImageDestroyInput):
                input_dict = input_data.to_graphql()
            else:
                input_dict = input_data

            result = await self.execute(
                fragments.IMAGE_DESTROY_MUTATION,
                {"input": input_dict},
            )

            return bool(result.get("imageDestroy", False))
        except Exception as e:
            self.log.error(f"Failed to delete image: {e}")
            raise

    async def images_destroy(
        self,
        input_data: ImagesDestroyInput | dict[str, Any],
    ) -> bool:
        """Delete multiple images.

        Args:
            input_data: ImagesDestroyInput object or dictionary containing:
                - ids: List of image IDs to delete (required)
                - delete_file: Whether to delete the images' files (optional, default: False)
                - delete_generated: Whether to delete generated files (optional, default: True)

        Returns:
            True if the images were successfully deleted

        Raises:
            ValueError: If any image ID is invalid
            gql.TransportError: If the request fails
        """
        try:
            if isinstance(input_data, ImagesDestroyInput):
                input_dict = input_data.to_graphql()
            else:
                input_dict = input_data

            result = await self.execute(
                fragments.IMAGES_DESTROY_MUTATION,
                {"input": input_dict},
            )

            return bool(result.get("imagesDestroy", False))
        except Exception as e:
            self.log.error(f"Failed to delete images: {e}")
            raise

    async def bulk_image_update(
        self,
        input_data: BulkImageUpdateInput | dict[str, Any],
    ) -> list[Image]:
        """Bulk update images.

        Args:
            input_data: BulkImageUpdateInput object or dictionary containing:
                - ids: List of image IDs to update (optional)
                - And any fields to update (e.g., organized, rating100, etc.)

        Returns:
            List of updated Image objects

        Examples:
            Mark multiple images as organized:
            ```python
            images = await client.bulk_image_update({
                "ids": ["1", "2", "3"],
                "organized": True
            })
            ```

            Add tags to multiple images:
            ```python
            from stash_graphql_client.types import BulkImageUpdateInput, BulkUpdateIds

            input_data = BulkImageUpdateInput(
                ids=["1", "2", "3"],
                tag_ids=BulkUpdateIds(ids=["tag1", "tag2"], mode="ADD")
            )
            images = await client.bulk_image_update(input_data)
            ```
        """
        try:
            # Convert BulkImageUpdateInput to dict if needed
            if isinstance(input_data, BulkImageUpdateInput):
                input_dict = input_data.to_graphql()
            else:
                input_dict = input_data

            result = await self.execute(
                fragments.BULK_IMAGE_UPDATE_MUTATION,
                {"input": input_dict},
            )

            images_data = result.get("bulkImageUpdate", [])
            return [self._decode_result(Image, img) for img in images_data]
        except Exception as e:
            self.log.error(f"Failed to bulk update images: {e}")
            raise

    async def images_update(
        self,
        updates: list[ImageUpdateInput] | list[dict[str, Any]],
    ) -> list[Image]:
        """Update multiple images with individual update data.

        This is different from bulk_image_update which applies the same updates to all images.
        This method allows updating each image with different values.

        Args:
            updates: List of ImageUpdateInput objects or dictionaries, each containing:
                - id: Image ID to update (required)
                - Any other fields to update for that specific image

        Returns:
            List of updated Image objects (may contain None for failed updates)

        Examples:
            Update multiple images with different values:
            ```python
            from stash_graphql_client.types import ImageUpdateInput

            updates = [
                ImageUpdateInput(id="1", title="First Image", organized=True),
                ImageUpdateInput(id="2", title="Second Image", rating100=90),
            ]
            images = await client.images_update(updates)
            ```

            Using dictionaries:
            ```python
            updates = [
                {"id": "1", "organized": True},
                {"id": "2", "rating100": 75},
            ]
            images = await client.images_update(updates)
            ```
        """
        try:
            # Convert ImageUpdateInput objects to dicts if needed
            input_list = []
            for update in updates:
                if isinstance(update, ImageUpdateInput):
                    input_list.append(update.to_graphql())
                else:
                    input_list.append(update)

            result = await self.execute(
                fragments.IMAGES_UPDATE_MUTATION,
                {"input": input_list},
            )

            images_data = result.get("imagesUpdate", [])
            return [
                self._decode_result(Image, img) if img else None for img in images_data
            ]
        except Exception as e:
            self.log.error(f"Failed to update images: {e}")
            raise

    # Image O-Count Operations

    async def image_increment_o(self, id: str) -> int:
        """Increment the O-counter for an image.

        Args:
            id: Image ID

        Returns:
            New O-count value after incrementing

        Example:
            ```python
            new_count = await client.image_increment_o("123")
            print(f"New O-count: {new_count}")
            ```
        """
        try:
            result = await self.execute(
                fragments.IMAGE_INCREMENT_O_MUTATION,
                {"id": id},
            )
            return int(result["imageIncrementO"])
        except Exception as e:
            self.log.error(f"Failed to increment O-count for image {id}: {e}")
            raise

    async def image_decrement_o(self, id: str) -> int:
        """Decrement the O-counter for an image.

        Args:
            id: Image ID

        Returns:
            New O-count value after decrementing

        Example:
            ```python
            new_count = await client.image_decrement_o("123")
            print(f"New O-count: {new_count}")
            ```
        """
        try:
            result = await self.execute(
                fragments.IMAGE_DECREMENT_O_MUTATION,
                {"id": id},
            )
            return int(result["imageDecrementO"])
        except Exception as e:
            self.log.error(f"Failed to decrement O-count for image {id}: {e}")
            raise

    async def image_reset_o(self, id: str) -> int:
        """Reset the O-counter for an image to 0.

        Args:
            id: Image ID

        Returns:
            New O-count value (0)

        Example:
            ```python
            count = await client.image_reset_o("123")
            print(f"O-count reset to: {count}")
            ```
        """
        try:
            result = await self.execute(
                fragments.IMAGE_RESET_O_MUTATION,
                {"id": id},
            )
            return int(result["imageResetO"])
        except Exception as e:
            self.log.error(f"Failed to reset O-count for image {id}: {e}")
            raise
