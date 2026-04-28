"""Image types from schema/types/image.graphql."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, ClassVar

from pydantic import BaseModel, Field, field_validator

from .base import (
    BulkUpdateIds,
    BulkUpdateStrings,
    StashInput,
    StashObject,
    StashResult,
    belongs_to,
    habtm,
)
from .files import ImageFile, VideoFile
from .metadata import CustomFieldsInput
from .scalars import Map
from .unset import UNSET, UnsetType, is_set


if TYPE_CHECKING:
    from stash_graphql_client.client import StashClient

    from .gallery import Gallery
    from .performer import Performer
    from .studio import Studio
    from .tag import Tag

# VisualFile union type (VideoFile | ImageFile)
VisualFile = VideoFile | ImageFile


class ImageFileType(BaseModel):
    """Image file type from schema/types/image.graphql."""

    mod_time: datetime | UnsetType = UNSET  # Time!
    size: int | UnsetType = UNSET  # Int!
    width: int | UnsetType = UNSET  # Int!
    height: int | UnsetType = UNSET  # Int!


class ImagePathsType(BaseModel):
    """Image paths type from schema/types/image.graphql."""

    thumbnail: str | None | UnsetType = UNSET  # String (Resolver)
    preview: str | None | UnsetType = UNSET  # String (Resolver)
    image: str | None | UnsetType = UNSET  # String (Resolver)


class ImageUpdateInput(StashInput):
    """Input for updating images."""

    # Required fields
    id: str  # ID!

    # Optional fields
    client_mutation_id: str | None | UnsetType = Field(
        default=UNSET, alias="clientMutationId"
    )  # String
    title: str | None | UnsetType = UNSET  # String
    code: str | None | UnsetType = UNSET  # String
    rating100: int | None | UnsetType = UNSET  # Int (1-100)
    organized: bool | None | UnsetType = UNSET  # Boolean
    urls: list[str] | None | UnsetType = UNSET  # [String!]
    date: str | None | UnsetType = UNSET  # String
    details: str | None | UnsetType = UNSET  # String
    photographer: str | None | UnsetType = UNSET  # String
    studio_id: str | None | UnsetType = UNSET  # ID
    performer_ids: list[str] | None | UnsetType = UNSET  # [ID!]
    tag_ids: list[str] | None | UnsetType = UNSET  # [ID!]
    gallery_ids: list[str] | None | UnsetType = UNSET  # [ID!]
    primary_file_id: str | None | UnsetType = UNSET  # ID
    custom_fields: CustomFieldsInput | None | UnsetType = (
        UNSET  # CustomFieldsInput (appSchema >= 83)
    )


class ImageDestroyInput(StashInput):
    """Input for destroying images from schema/types/image.graphql."""

    id: str  # ID!
    delete_file: bool | None | UnsetType = UNSET  # Boolean
    delete_generated: bool | None | UnsetType = UNSET  # Boolean
    destroy_file_entry: bool | None | UnsetType = UNSET  # Boolean (appSchema >= 84)


class ImagesDestroyInput(StashInput):
    """Input for destroying multiple images from schema/types/image.graphql."""

    ids: list[str] | UnsetType = UNSET  # [ID!]!
    delete_file: bool | None | UnsetType = UNSET  # Boolean
    delete_generated: bool | None | UnsetType = UNSET  # Boolean
    destroy_file_entry: bool | None | UnsetType = UNSET  # Boolean (appSchema >= 84)


class Image(StashObject):
    """A single image or video-as-image file managed by Stash.

    ``visual_files`` holds the underlying files as ``list[VisualFile]`` — a
    discriminated union of ``VideoFile | ImageFile``.

    ``o_counter`` uses a side-mutation handler (``_save_o_counter``). Set it
    to a new value and call ``save()``; the client fires
    ``imageIncrementO`` / ``imageDecrementO`` / ``imageResetO`` mutations to
    reach the target value.

    Images are created by Stash's scanner, not this client — there is no
    ``ImageCreateInput``, only updates and destroys.
    """

    __type_name__ = "Image"
    __short_repr_fields__ = ("title",)
    __update_input_type__ = ImageUpdateInput
    __destroy_input_type__ = ImageDestroyInput
    __bulk_destroy_input_type__ = ImagesDestroyInput
    # No __create_input_type__ - images can only be updated

    # Fields to track for changes
    __tracked_fields__ = {
        "title",  # ImageUpdateInput
        "code",  # ImageUpdateInput
        "urls",  # ImageUpdateInput
        "date",  # ImageUpdateInput
        "details",  # ImageUpdateInput
        "photographer",  # ImageUpdateInput
        "studio",  # mapped to studio_id
        "organized",  # ImageUpdateInput
        "galleries",  # mapped to gallery_ids
        "tags",  # mapped to tag_ids
        "performers",  # mapped to performer_ids
        # Side-mutation field
        "o_counter",  # imageIncrementO/imageDecrementO/imageResetO
        "custom_fields",  # imageUpdate via CustomFieldsInput diff (appSchema >= 83)
    }

    # Side mutations: o_counter is managed via increment/decrement/reset mutations
    __side_mutations__: ClassVar[dict] = {
        "o_counter": lambda client, obj: Image._save_o_counter(client, obj),  # noqa: PLW0108
        "custom_fields": StashObject._make_custom_fields_handler(
            capability_attr="has_image_custom_fields",
            update_method_name="update_image",
        ),
    }

    # Optional fields
    title: str | None | UnsetType = UNSET  # String
    code: str | None | UnsetType = UNSET  # String
    date: str | None | UnsetType = UNSET  # String
    rating100: int | None | UnsetType = Field(
        default=UNSET, ge=0, le=100
    )  # Int (0-100)
    details: str | None | UnsetType = UNSET  # String
    photographer: str | None | UnsetType = UNSET  # String
    studio: Studio | None | UnsetType = UNSET  # Studio
    o_counter: int | None | UnsetType = Field(default=UNSET, ge=0)  # Int (Resolver)

    # Required fields
    urls: list[str] | UnsetType = Field(default=UNSET)  # [String!]!
    organized: bool | UnsetType = UNSET  # Boolean!
    visual_files: list[VisualFile] | UnsetType = Field(
        default=UNSET
    )  # [VisualFile!]! - The image files (union of VideoFile | ImageFile)
    paths: ImagePathsType | UnsetType = Field(
        default=UNSET
    )  # ImagePathsType! (Resolver)
    galleries: list[Gallery] | UnsetType = Field(default=UNSET)  # [Gallery!]!
    tags: list[Tag] | UnsetType = Field(default=UNSET)  # [Tag!]!
    performers: list[Performer] | UnsetType = Field(default=UNSET)  # [Performer!]!

    # Capability-gated fields (appSchema >= 83)
    custom_fields: Map | UnsetType = UNSET  # Map! (appSchema >= 83)

    # Relationship definitions with their mappings
    __relationships__ = {
        "studio": belongs_to("Studio", inverse_query_field="images"),
        "performers": habtm("Performer", inverse_query_field="images"),
        "tags": habtm("Tag", inverse_query_field="images"),
        "galleries": habtm("Gallery", inverse_query_field="images"),
    }

    # Field definitions with their conversion functions
    __field_conversions__ = {
        "title": str,
        "code": str,
        "urls": list,
        "details": str,
        "photographer": str,
        "rating100": int,
        "organized": bool,
        "date": lambda d: (
            d.strftime("%Y-%m-%d")
            if isinstance(d, datetime)
            else (
                datetime.fromisoformat(d).strftime("%Y-%m-%d")
                if isinstance(d, str)
                else None
            )
        ),
    }

    @staticmethod
    async def _save_o_counter(client: StashClient, image: Image) -> None:
        """Side-mutation handler for o_counter.

        Computes delta between current and snapshot o_counter, then fires
        the appropriate client mixin methods. Updates the local o_counter
        from the mutation's returned Int!.
        """
        current = image.o_counter if is_set(image.o_counter) else 0
        snapshot = image._snapshot.get("o_counter", 0)
        # Treat UNSET/None snapshot as 0
        if not isinstance(snapshot, int):
            snapshot = 0
        if not isinstance(current, int):
            current = 0

        # Reset takes priority if current is explicitly 0
        if current == 0 and snapshot != 0:
            image.o_counter = await client.image_reset_o(image.id)
            return

        delta = current - snapshot
        if delta > 0:
            new_count = current
            for _ in range(delta):
                new_count = await client.image_increment_o(image.id)
            image.o_counter = new_count
        elif delta < 0:
            new_count = current
            for _ in range(abs(delta)):
                new_count = await client.image_decrement_o(image.id)
            image.o_counter = new_count

    async def add_performer(self, performer: Performer) -> None:
        """Add performer (syncs inverse automatically, call save() to persist)."""
        await self._add_to_relationship("performers", performer)

    async def remove_performer(self, performer: Performer) -> None:
        """Remove performer (syncs inverse automatically, call save() to persist)."""
        await self._remove_from_relationship("performers", performer)

    async def add_to_gallery(self, gallery: Gallery) -> None:
        """Add gallery (syncs inverse automatically, call save() to persist)."""
        await self._add_to_relationship("galleries", gallery)

    async def remove_from_gallery(self, gallery: Gallery) -> None:
        """Remove gallery (syncs inverse automatically, call save() to persist)."""
        await self._remove_from_relationship("galleries", gallery)

    async def add_tag(self, tag: Tag) -> None:
        """Add tag (syncs inverse automatically, call save() to persist)."""
        await self._add_to_relationship("tags", tag)

    async def remove_tag(self, tag: Tag) -> None:
        """Remove tag (syncs inverse automatically, call save() to persist)."""
        await self._remove_from_relationship("tags", tag)

    @field_validator("visual_files", mode="before")
    @classmethod
    def _discriminate_visual_file_types(cls, value: Any) -> Any:
        """Discriminate VisualFile union types based on __typename.

        Converts raw dicts to the appropriate VisualFile type (VideoFile or ImageFile)
        based on __typename field.
        """
        if value is None or isinstance(value, type(UNSET)):
            return value

        if not isinstance(value, list):
            return value

        # Type mapping for VisualFile union
        type_map: dict[str, type[VideoFile] | type[ImageFile]] = {
            "VideoFile": VideoFile,
            "ImageFile": ImageFile,
        }

        result = []
        for item in value:
            if isinstance(item, dict) and "__typename" in item:
                typename = item["__typename"]
                file_type = type_map.get(typename)
                if file_type:
                    # Construct with from_graphql context so _received_fields
                    # is populated (fallback path when _process_nested_graphql
                    # didn't handle the item, e.g. via validate_assignment)
                    result.append(
                        file_type.model_validate(item, context={"from_graphql": True})
                    )
                else:
                    # Unknown typename, skip
                    continue
            else:
                # Already constructed or no typename
                result.append(item)

        return result


class BulkImageUpdateInput(StashInput):
    """Input for bulk updating images."""

    # Optional fields
    client_mutation_id: str | None | UnsetType = Field(
        default=UNSET, alias="clientMutationId"
    )  # String
    ids: list[str] | UnsetType = UNSET  # [ID!]
    title: str | None | UnsetType = UNSET  # String
    code: str | None | UnsetType = UNSET  # String
    rating100: int | None | UnsetType = Field(
        default=UNSET, ge=0, le=100
    )  # Int (0-100)
    organized: bool | None | UnsetType = UNSET  # Boolean
    urls: BulkUpdateStrings | None | UnsetType = UNSET  # BulkUpdateStrings
    date: str | None | UnsetType = UNSET  # String
    details: str | None | UnsetType = UNSET  # String
    photographer: str | None | UnsetType = UNSET  # String
    studio_id: str | None | UnsetType = UNSET  # ID
    performer_ids: BulkUpdateIds | None | UnsetType = UNSET  # BulkUpdateIds
    tag_ids: BulkUpdateIds | None | UnsetType = UNSET  # BulkUpdateIds
    gallery_ids: BulkUpdateIds | None | UnsetType = UNSET  # BulkUpdateIds
    custom_fields: CustomFieldsInput | None | UnsetType = (
        UNSET  # CustomFieldsInput (appSchema >= 83)
    )


class FindImagesResultType(StashResult):
    """Result type for finding images from schema/types/image.graphql."""

    count: int | UnsetType = UNSET  # Int!
    megapixels: float | UnsetType = UNSET  # Float! (Total megapixels of the images)
    filesize: float | UnsetType = UNSET  # Float! (Total file size in bytes)
    images: list[Image] | UnsetType = Field(default=UNSET)  # [Image!]!
