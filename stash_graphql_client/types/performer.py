"""Performer type for Stash."""

from __future__ import annotations

import base64
import mimetypes
from pathlib import Path

# TODO: Re-enable once metadata module is implemented
# from pyloyalfans.metadata.account import Account
from typing import TYPE_CHECKING, Any, TypeVar

from pydantic import Field

from stash_graphql_client.fragments import FIND_PERFORMERS_QUERY

from .base import (
    BulkUpdateIds,
    BulkUpdateStrings,
    RelationshipMetadata,
    StashInput,
    StashObject,
    StashResult,
)
from .enums import CircumisedEnum, GenderEnum
from .files import StashID, StashIDInput
from .metadata import CustomFieldsInput
from .scalars import Map
from .unset import UNSET, UnsetType


# if _TYPE_CHECKING_METADATA:
#     from pyloyalfans.metadata.account import Account


if TYPE_CHECKING:
    from stash_graphql_client.client import StashClient

    from .group import Group
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
    circumcised: CircumisedEnum | None | UnsetType = UNSET  # CircumisedEnum
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
    circumcised: CircumisedEnum | None | UnsetType = UNSET  # CircumisedEnum
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
    circumcised: CircumisedEnum | None | UnsetType = UNSET  # CircumisedEnum
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


class PerformerDestroyInput(StashInput):
    """Input for destroying performers from schema/types/performer.graphql."""

    id: str  # ID!


class Performer(StashObject):
    """Performer type from schema/types/performer.graphql."""

    __type_name__ = "Performer"
    __update_input_type__ = PerformerUpdateInput
    __create_input_type__ = PerformerCreateInput

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
    }

    # Required fields from schema
    name: str | UnsetType = UNSET  # String!
    alias_list: list[str] | UnsetType = UNSET  # [String!]!
    tags: list[Tag] | UnsetType = UNSET  # [Tag!]!
    stash_ids: list[StashID] | UnsetType = UNSET  # [StashID!]!
    scenes: list[Scene] | UnsetType = UNSET  # [Scene!]!
    groups: list[Group] | UnsetType = UNSET  # [Group!]!
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
    circumcised: CircumisedEnum | None | UnsetType = UNSET  # CircumisedEnum
    career_length: str | None | UnsetType = UNSET  # String
    tattoos: str | None | UnsetType = UNSET  # String
    piercings: str | None | UnsetType = UNSET  # String
    image_path: str | None | UnsetType = UNSET  # String (Resolver)
    details: str | None | UnsetType = UNSET  # String
    death_date: str | None | UnsetType = UNSET  # String
    hair_color: str | None | UnsetType = UNSET  # String
    weight: int | None | UnsetType = UNSET  # Int
    o_counter: int | None | UnsetType = Field(default=UNSET, ge=0)  # Int (Resolver)

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

        try:
            # Read and encode image
            with open(path, "rb") as f:
                image_data = f.read()
            image_b64 = base64.b64encode(image_data).decode("utf-8")
            mime = mimetypes.types_map.get(path.suffix, "image/jpeg")
            image_url = f"data:{mime};base64,{image_b64}"

            # Use client's direct method for updating image
            return await client.update_performer_image(self, image_url)

        except Exception as e:
            raise ValueError(f"Failed to update avatar: {e}") from e

    # @classmethod
    # def from_account(cls, account: "Account") -> "Performer":
    #     """Create performer from account.

    #     Args:
    #         account: Account to convert

    #     Returns:
    #         New performer instance
    #     """
    #     # Ensure we have a name (fallback to "Unknown" if all are None)
    #     performer_name = (
    #         account.display_name or account.username or account.screen_name or "Unknown"
    #     )

    #     # Handle alias list with proper None checking
    #     alias_list = []
    #     if (
    #         account.display_name is not None
    #         and account.username is not None
    #         and account.display_name.lower() != account.username.lower()
    #     ):
    #         alias_list = [account.username]

    #     # Build URLs list - Account objects don't have direct URLs
    #     urls: list[str] = []

    #     return cls(
    #         id="new",  # Will be replaced on save
    #         name=performer_name,
    #         alias_list=alias_list,  # Only add username as alias if using display_name and it's different (case-insensitive)
    #         urls=urls,
    #         country="",
    #         details=account.bio or "",
    #         gender=GenderEnum.FEMALE,  # Default assumption for missF content creators
    #         # Required fields with defaults
    #         tags=[],  # Empty list of tags to start
    #         scenes=[],
    #         groups=[],  # Required relationship
    #         stash_ids=[],  # Required relationship
    #     )

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
    }

    __relationships__ = {
        "tags": RelationshipMetadata(
            target_field="tag_ids",
            is_list=True,
            query_field="tags",
            inverse_type="Tag",
            inverse_query_field="performers",
            query_strategy="direct_field",
            notes="Backend auto-syncs performer.tags and tag.performers",
        ),
        "stash_ids": RelationshipMetadata(
            target_field="stash_ids",
            is_list=True,
            transform=lambda s: StashIDInput(endpoint=s.endpoint, stash_id=s.stash_id),
            query_field="stash_ids",
            notes="Requires transform to StashIDInput for mutations",
        ),
    }

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
                FIND_PERFORMERS_QUERY,
                {
                    "filter": None,
                    "performer_filter": {"name": {"value": name, "modifier": "EQUALS"}},
                },
            )
            performers_data = result.get("findPerformers", {}).get("performers", [])
            if performers_data:
                return cls(**performers_data[0])
            return None
        except Exception:
            return None


class FindPerformersResultType(StashResult):
    """Result type for finding performers from schema/types/performer.graphql."""

    count: int | UnsetType = UNSET  # Int!
    performers: list[Performer] | UnsetType = UNSET  # [Performer!]!
