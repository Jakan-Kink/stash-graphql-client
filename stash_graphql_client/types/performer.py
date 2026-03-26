"""Performer type for Stash."""

from __future__ import annotations

import base64
import mimetypes
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, TypeVar

from pydantic import Field, field_validator

from stash_graphql_client.fragments import fragment_store

from .base import (
    BulkUpdateIds,
    BulkUpdateStrings,
    RelationshipMetadata,
    StashInput,
    StashObject,
    StashResult,
)
from .enums import CircumcisedEnum, GenderEnum
from .files import StashID, StashIDInput
from .metadata import CustomFieldsInput
from .scalars import Map
from .unset import UNSET, UnsetType


# if _TYPE_CHECKING_METADATA:
#     from pyloyalfans.metadata.account import Account


if TYPE_CHECKING:
    from stash_graphql_client.client import StashClient

    from .gallery import Gallery
    from .group import Group
    from .image import Image
    from .scene import Scene
    from .tag import Tag

    # Movie type to be implemented by other agents
    class Movie:
        """Placeholder for Movie type."""


T = TypeVar("T", bound="Performer")


class PerformerCreateInput(StashInput):
    """Input for creating performers."""

    # Required fields
    name: str  # String!

    # Optional fields
    disambiguation: str | None | UnsetType = UNSET  # String
    urls: list[str] | None | UnsetType = UNSET  # [String!]
    gender: GenderEnum | None | UnsetType = UNSET  # GenderEnum
    birthdate: str | None | UnsetType = UNSET  # String
    ethnicity: str | None | UnsetType = UNSET  # String
    country: str | None | UnsetType = UNSET  # String
    eye_color: str | None | UnsetType = UNSET  # String
    height_cm: int | None | UnsetType = UNSET  # Int
    measurements: str | None | UnsetType = UNSET  # String
    fake_tits: str | None | UnsetType = UNSET  # String
    penis_length: float | None | UnsetType = UNSET  # Float
    circumcised: CircumcisedEnum | None | UnsetType = UNSET  # CircumcisedEnum
    career_length: str | None | UnsetType = UNSET  # String
    tattoos: str | None | UnsetType = UNSET  # String
    piercings: str | None | UnsetType = UNSET  # String
    alias_list: list[str] | None | UnsetType = UNSET  # [String!]
    favorite: bool | None | UnsetType = UNSET  # Boolean
    tag_ids: list[str] | None | UnsetType = UNSET  # [ID!]
    image: str | None | UnsetType = UNSET  # String (URL or base64)
    stash_ids: list[StashIDInput] | None | UnsetType = UNSET  # [StashIDInput!]
    rating100: int | None | UnsetType = Field(default=UNSET, ge=0, le=100)  # Int
    details: str | None | UnsetType = UNSET  # String
    death_date: str | None | UnsetType = UNSET  # String
    hair_color: str | None | UnsetType = UNSET  # String
    weight: int | None | UnsetType = UNSET  # Int
    ignore_auto_tag: bool | None | UnsetType = UNSET  # Boolean
    custom_fields: dict[str, Any] | None | UnsetType = UNSET  # Map
    career_start: str | None | UnsetType = UNSET  # String (fuzzy date, appSchema >= 78)
    career_end: str | None | UnsetType = UNSET  # String (fuzzy date, appSchema >= 78)

    @field_validator("career_start", "career_end", mode="before")
    @classmethod
    def _coerce_career_date(cls, v: Any) -> Any:
        """Coerce int year to str for backward compat with appSchema 78-84."""
        if isinstance(v, int):
            return str(v)
        return v


class PerformerUpdateInput(StashInput):
    """Input for updating performers."""

    # Required fields
    id: str  # ID!

    # Optional fields
    name: str | None | UnsetType = UNSET  # String
    disambiguation: str | None | UnsetType = UNSET  # String
    urls: list[str] | None | UnsetType = UNSET  # [String!]
    gender: GenderEnum | None | UnsetType = UNSET  # GenderEnum
    birthdate: str | None | UnsetType = UNSET  # String
    ethnicity: str | None | UnsetType = UNSET  # String
    country: str | None | UnsetType = UNSET  # String
    eye_color: str | None | UnsetType = UNSET  # String
    height_cm: int | None | UnsetType = UNSET  # Int
    measurements: str | None | UnsetType = UNSET  # String
    fake_tits: str | None | UnsetType = UNSET  # String
    penis_length: float | None | UnsetType = UNSET  # Float
    circumcised: CircumcisedEnum | None | UnsetType = UNSET  # CircumcisedEnum
    career_length: str | None | UnsetType = UNSET  # String
    tattoos: str | None | UnsetType = UNSET  # String
    piercings: str | None | UnsetType = UNSET  # String
    alias_list: list[str] | None | UnsetType = UNSET  # [String!]
    favorite: bool | None | UnsetType = UNSET  # Boolean
    tag_ids: list[str] | None | UnsetType = UNSET  # [ID!]
    image: str | None | UnsetType = UNSET  # String (URL or base64)
    stash_ids: list[StashIDInput] | None | UnsetType = UNSET  # [StashIDInput!]
    rating100: int | None | UnsetType = Field(default=UNSET, ge=0, le=100)  # Int
    details: str | None | UnsetType = UNSET  # String
    death_date: str | None | UnsetType = UNSET  # String
    hair_color: str | None | UnsetType = UNSET  # String
    weight: int | None | UnsetType = UNSET  # Int
    ignore_auto_tag: bool | None | UnsetType = UNSET  # Boolean
    custom_fields: CustomFieldsInput | None | UnsetType = UNSET  # CustomFieldsInput
    career_start: str | None | UnsetType = UNSET  # String (fuzzy date, appSchema >= 78)
    career_end: str | None | UnsetType = UNSET  # String (fuzzy date, appSchema >= 78)

    @field_validator("career_start", "career_end", mode="before")
    @classmethod
    def _coerce_career_date(cls, v: Any) -> Any:
        """Coerce int year to str for backward compat with appSchema 78-84."""
        if isinstance(v, int):
            return str(v)
        return v


class BulkPerformerUpdateInput(StashInput):
    """Input for bulk updating performers from schema/types/performer.graphql."""

    client_mutation_id: str | None | UnsetType = Field(
        default=UNSET, alias="clientMutationId"
    )  # String
    ids: list[str] | None | UnsetType = UNSET  # [ID!]
    disambiguation: str | None | UnsetType = UNSET  # String
    urls: BulkUpdateStrings | None | UnsetType = UNSET  # BulkUpdateStrings
    gender: GenderEnum | None | UnsetType = UNSET  # GenderEnum
    birthdate: str | None | UnsetType = UNSET  # String
    ethnicity: str | None | UnsetType = UNSET  # String
    country: str | None | UnsetType = UNSET  # String
    eye_color: str | None | UnsetType = UNSET  # String
    height_cm: int | None | UnsetType = UNSET  # Int
    measurements: str | None | UnsetType = UNSET  # String
    fake_tits: str | None | UnsetType = UNSET  # String
    penis_length: float | None | UnsetType = UNSET  # Float
    circumcised: CircumcisedEnum | None | UnsetType = UNSET  # CircumcisedEnum
    career_length: str | None | UnsetType = UNSET  # String
    tattoos: str | None | UnsetType = UNSET  # String
    piercings: str | None | UnsetType = UNSET  # String
    alias_list: BulkUpdateStrings | None | UnsetType = UNSET  # BulkUpdateStrings
    favorite: bool | None | UnsetType = UNSET  # Boolean
    tag_ids: BulkUpdateIds | None | UnsetType = UNSET  # BulkUpdateIds
    rating100: int | None | UnsetType = Field(default=UNSET, ge=0, le=100)  # Int
    details: str | None | UnsetType = UNSET  # String
    death_date: str | None | UnsetType = UNSET  # String
    hair_color: str | None | UnsetType = UNSET  # String
    weight: int | None | UnsetType = UNSET  # Int
    ignore_auto_tag: bool | None | UnsetType = UNSET  # Boolean
    custom_fields: CustomFieldsInput | None | UnsetType = UNSET  # CustomFieldsInput
    career_start: str | None | UnsetType = UNSET  # String (fuzzy date, appSchema >= 78)
    career_end: str | None | UnsetType = UNSET  # String (fuzzy date, appSchema >= 78)

    @field_validator("career_start", "career_end", mode="before")
    @classmethod
    def _coerce_career_date(cls, v: Any) -> Any:
        """Coerce int year to str for backward compat with appSchema 78-84."""
        if isinstance(v, int):
            return str(v)
        return v


class PerformerDestroyInput(StashInput):
    """Input for destroying performers from schema/types/performer.graphql."""

    id: str  # ID!


class PerformerMergeInput(StashInput):
    """Input for merging performers from schema/types/performer.graphql."""

    source: list[str]  # [ID!]!
    destination: str  # ID!
    values: PerformerUpdateInput | None | UnsetType = UNSET  # PerformerUpdateInput


class Performer(StashObject):
    """Performer type from schema/types/performer.graphql."""

    __type_name__ = "Performer"
    __short_repr_fields__ = ("name",)
    __update_input_type__ = PerformerUpdateInput
    __create_input_type__ = PerformerCreateInput
    __destroy_input_type__ = PerformerDestroyInput
    __merge_input_type__ = PerformerMergeInput

    # Fields to track for changes - only fields that can be written via input types
    __tracked_fields__ = {
        "name",  # PerformerCreateInput/PerformerUpdateInput
        "alias_list",  # PerformerCreateInput/PerformerUpdateInput
        "tags",  # mapped to tag_ids
        "disambiguation",  # PerformerCreateInput/PerformerUpdateInput
        "urls",  # PerformerCreateInput/PerformerUpdateInput
        "gender",  # PerformerCreateInput/PerformerUpdateInput
        "birthdate",  # PerformerCreateInput/PerformerUpdateInput
        "ethnicity",  # PerformerCreateInput/PerformerUpdateInput
        "country",  # PerformerCreateInput/PerformerUpdateInput
        "eye_color",  # PerformerCreateInput/PerformerUpdateInput
        "height_cm",  # PerformerCreateInput/PerformerUpdateInput
        "measurements",  # PerformerCreateInput/PerformerUpdateInput
        "fake_tits",  # PerformerCreateInput/PerformerUpdateInput
        "penis_length",  # PerformerCreateInput/PerformerUpdateInput
        "circumcised",  # PerformerCreateInput/PerformerUpdateInput
        "career_length",  # PerformerCreateInput/PerformerUpdateInput
        "tattoos",  # PerformerCreateInput/PerformerUpdateInput
        "piercings",  # PerformerCreateInput/PerformerUpdateInput
        "details",  # PerformerCreateInput/PerformerUpdateInput
        "death_date",  # PerformerCreateInput/PerformerUpdateInput
        "hair_color",  # PerformerCreateInput/PerformerUpdateInput
        "weight",  # PerformerCreateInput/PerformerUpdateInput
        "rating100",  # PerformerCreateInput/PerformerUpdateInput
        "favorite",  # PerformerCreateInput/PerformerUpdateInput
        "ignore_auto_tag",  # PerformerCreateInput/PerformerUpdateInput
        "career_start",  # PerformerUpdateInput (appSchema >= 78)
        "career_end",  # PerformerUpdateInput (appSchema >= 78)
        # Side-mutation fields (excluded from to_input, handled by bulk updates)
        "scenes",  # bulkSceneUpdate with performer_ids
        "galleries",  # bulkGalleryUpdate with performer_ids
        "images",  # bulkImageUpdate with performer_ids
    }

    # Side mutations: scenes/galleries/images are writable via bulk updates on
    # the content entities (PerformerUpdateInput has no scene_ids/gallery_ids/image_ids).
    # Shared handler refs for deduplication are not needed here (1:1 field→handler).
    __side_mutations__: ClassVar[dict] = {
        "scenes": StashObject._make_bulk_relationship_handler(
            "scenes",
            "bulk_scene_update",
            "performer_ids",
        ),
        "galleries": StashObject._make_bulk_relationship_handler(
            "galleries",
            "bulk_gallery_update",
            "performer_ids",
        ),
        "images": StashObject._make_bulk_relationship_handler(
            "images",
            "bulk_image_update",
            "performer_ids",
        ),
    }

    # Required fields from schema
    name: str | UnsetType = UNSET  # String!
    alias_list: list[str] | UnsetType = UNSET  # [String!]!
    tags: list[Tag] | UnsetType = UNSET  # [Tag!]!
    stash_ids: list[StashID] | UnsetType = UNSET  # [StashID!]!
    scenes: list[Scene] | UnsetType = UNSET  # [Scene!]!
    groups: list[Group] | UnsetType = UNSET  # [Group!]!
    galleries: list[Gallery] | UnsetType = UNSET  # queryable via FindGalleries filter
    images: list[Image] | UnsetType = UNSET  # queryable via FindImages filter
    favorite: bool | UnsetType = UNSET  # Boolean!
    ignore_auto_tag: bool | UnsetType = UNSET  # Boolean!
    scene_count: int | UnsetType = Field(default=UNSET, ge=0)  # Int! (Resolver)
    image_count: int | UnsetType = Field(default=UNSET, ge=0)  # Int! (Resolver)
    gallery_count: int | UnsetType = Field(default=UNSET, ge=0)  # Int! (Resolver)
    group_count: int | UnsetType = Field(default=UNSET, ge=0)  # Int! (Resolver)
    performer_count: int | UnsetType = Field(default=UNSET, ge=0)  # Int! (Resolver)
    custom_fields: Map | UnsetType = UNSET  # Map!
    # created_at and updated_at inherited from StashObject

    # Optional fields from schema
    disambiguation: str | None | UnsetType = UNSET  # String
    urls: list[str] | UnsetType = UNSET  # [String!]
    gender: GenderEnum | None | UnsetType = UNSET  # GenderEnum
    birthdate: str | None | UnsetType = UNSET  # String
    rating100: int | None | UnsetType = Field(
        default=UNSET, ge=0, le=100
    )  # Int (0-100)
    ethnicity: str | None | UnsetType = UNSET  # String
    country: str | None | UnsetType = UNSET  # String
    eye_color: str | None | UnsetType = UNSET  # String
    height_cm: int | None | UnsetType = UNSET  # Int
    measurements: str | None | UnsetType = UNSET  # String
    fake_tits: str | None | UnsetType = UNSET  # String
    penis_length: float | None | UnsetType = UNSET  # Float
    circumcised: CircumcisedEnum | None | UnsetType = UNSET  # CircumcisedEnum
    career_length: str | None | UnsetType = UNSET  # String
    tattoos: str | None | UnsetType = UNSET  # String
    piercings: str | None | UnsetType = UNSET  # String
    image_path: str | None | UnsetType = UNSET  # String (Resolver)
    details: str | None | UnsetType = UNSET  # String
    death_date: str | None | UnsetType = UNSET  # String
    hair_color: str | None | UnsetType = UNSET  # String
    weight: int | None | UnsetType = UNSET  # Int
    o_counter: int | None | UnsetType = Field(default=UNSET, ge=0)  # Int (Resolver)

    # Capability-gated fields (appSchema >= 78; str fuzzy date as of appSchema 85)
    career_start: str | None | UnsetType = UNSET  # String (fuzzy date, appSchema >= 78)
    career_end: str | None | UnsetType = UNSET  # String (fuzzy date, appSchema >= 78)

    @field_validator("career_start", "career_end", mode="before")
    @classmethod
    def _coerce_career_date(cls, v: Any) -> Any:
        """Coerce int year to str for backward compat with appSchema 78-84."""
        if isinstance(v, int):
            return str(v)
        return v

    async def update_avatar(
        self, client: StashClient, image_path: str | Path
    ) -> Performer:
        """Update performer's avatar image.

        Args:
            client: "StashClient" instance to use for update
            image_path: Path to image file to use as avatar

        Returns:
            Updated Performer object with the new image

        Raises:
            FileNotFoundError: If image file doesn't exist
            ValueError: If image file can't be read or update fails
        """
        # Convert path to Path object
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {path}")
        if not path.is_file():
            raise ValueError(f"Path is not a file: {path}")

        try:
            # Read and encode image
            with open(path, "rb") as f:
                image_data = f.read()
            image_b64 = base64.b64encode(image_data).decode("utf-8")
            mime = mimetypes.types_map.get(path.suffix.lower())
            if not mime or not mime.startswith("image/"):
                raise ValueError(f"File does not appear to be an image: {path.suffix}")
            image_url = f"data:{mime};base64,{image_b64}"

            # Use client's direct method for updating image
            return await client.update_performer_image(self, image_url)

        except Exception as e:
            raise ValueError(f"Failed to update avatar: {e}") from e

    async def add_tag(self, tag: Tag) -> None:
        """Add tag to performer (syncs inverse automatically, call save() to persist)."""
        await self._add_to_relationship("tags", tag)

    async def remove_tag(self, tag: Tag) -> None:
        """Remove tag from performer (syncs inverse automatically, call save() to persist)."""
        await self._remove_from_relationship("tags", tag)

    # Field definitions with their conversion functions
    __field_conversions__ = {
        "name": str,
        "disambiguation": str,
        "urls": list,
        "gender": lambda g: g.value if g else None,
        "birthdate": str,
        "ethnicity": str,
        "country": str,
        "eye_color": str,
        "height_cm": int,
        "measurements": str,
        "fake_tits": str,
        "penis_length": float,
        "circumcised": lambda c: c.value if c else None,
        "career_length": str,
        "tattoos": str,
        "piercings": str,
        "alias_list": list,
        "details": str,
        "death_date": str,
        "hair_color": str,
        "weight": int,
        "rating100": int,
        "favorite": bool,
        "ignore_auto_tag": bool,
        "career_start": str,
        "career_end": str,
    }

    __relationships__ = {
        "tags": RelationshipMetadata(
            target_field="tag_ids",
            is_list=True,
            query_field="tags",
            inverse_type="Tag",
            inverse_query_field=None,  # Tag has no performers field, only performer_count resolver
            query_strategy="direct_field",
            notes="One-directional: performer.tags queryable, tag→performer only via performer_count or filter query",
        ),
        "stash_ids": RelationshipMetadata(
            target_field="stash_ids",
            is_list=True,
            transform=lambda s: StashIDInput(endpoint=s.endpoint, stash_id=s.stash_id),
            query_field="stash_ids",
            notes="Requires transform to StashIDInput for mutations",
        ),
        # Side-mutation relationships: writable via bulk updates on content entities
        "scenes": RelationshipMetadata(
            target_field="scene_ids",
            is_list=True,
            query_field="scenes",
            inverse_type="Scene",
            inverse_query_field="performers",
            query_strategy="filter_query",
            filter_query_hint="findScenes(scene_filter={performers: {value: [performer_id]}})",
            notes="Writable via bulkSceneUpdate(performer_ids). Direct performers_scenes join table.",
        ),
        "galleries": RelationshipMetadata(
            target_field="gallery_ids",
            is_list=True,
            query_field="galleries",
            inverse_type="Gallery",
            inverse_query_field="performers",
            query_strategy="filter_query",
            filter_query_hint="findGalleries(gallery_filter={performers: {value: [performer_id]}})",
            notes="Writable via bulkGalleryUpdate(performer_ids). No direct Performer.galleries in schema.",
        ),
        "images": RelationshipMetadata(
            target_field="image_ids",
            is_list=True,
            query_field="images",
            inverse_type="Image",
            inverse_query_field="performers",
            query_strategy="filter_query",
            filter_query_hint="findImages(image_filter={performers: {value: [performer_id]}})",
            notes="Writable via bulkImageUpdate(performer_ids). No direct Performer.images in schema.",
        ),
        # Read-only: derived through scenes (performers_scenes → groups_scenes multi-join)
        "groups": RelationshipMetadata(
            target_field="",  # Read-only: no group_ids in PerformerUpdateInput
            is_list=True,
            query_field="groups",
            inverse_type="Group",
            query_strategy="filter_query",
            filter_query_hint="findGroups(group_filter={performers: {value: [performer_id]}})",
            notes="Derived through scenes. Queryable via filter, not directly writable.",
        ),
    }

    # =========================================================================
    # Convenience Helper Methods for Bidirectional Relationships
    # =========================================================================

    async def add_scene(self, scene: Scene) -> None:
        """Add scene (syncs inverse automatically, call save() to persist)."""
        await self._add_to_relationship("scenes", scene)

    async def remove_scene(self, scene: Scene) -> None:
        """Remove scene (syncs inverse automatically, call save() to persist)."""
        await self._remove_from_relationship("scenes", scene)

    async def add_gallery(self, gallery: Gallery) -> None:
        """Add gallery (syncs inverse automatically, call save() to persist)."""
        await self._add_to_relationship("galleries", gallery)

    async def remove_gallery(self, gallery: Gallery) -> None:
        """Remove gallery (syncs inverse automatically, call save() to persist)."""
        await self._remove_from_relationship("galleries", gallery)

    async def add_image(self, image: Image) -> None:
        """Add image (syncs inverse automatically, call save() to persist)."""
        await self._add_to_relationship("images", image)

    async def remove_image(self, image: Image) -> None:
        """Remove image (syncs inverse automatically, call save() to persist)."""
        await self._remove_from_relationship("images", image)

    @classmethod
    async def find_by_name(
        cls: type[T],
        client: StashClient,
        name: str,
    ) -> T | None:
        """Find performer by name.

        Args:
            client: "StashClient" instance
            name: Performer name to search for

        Returns:
            Performer instance if found, None otherwise
        """
        try:
            result = await client.execute(
                fragment_store.FIND_PERFORMERS_QUERY,
                {
                    "filter": None,
                    "performer_filter": {"name": {"value": name, "modifier": "EQUALS"}},
                },
            )
            performers_data = (result.get("findPerformers") or {}).get(
                "performers"
            ) or []
            if performers_data:
                return cls(**performers_data[0])
            return None
        except Exception:
            return None


class FindPerformersResultType(StashResult):
    """Result type for finding performers from schema/types/performer.graphql."""

    count: int | UnsetType = UNSET  # Int!
    performers: list[Performer] | UnsetType = UNSET  # [Performer!]!
