"""Studio type from schema/types/studio.graphql."""

from __future__ import annotations

# TODO: Re-enable once metadata module is implemented
# from pyloyalfans.metadata import Account
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field, model_validator

from .base import StashObject
from .files import StashID, StashIDInput


# if _TYPE_CHECKING_METADATA:
#     from pyloyalfans.metadata import Account


if TYPE_CHECKING:
    from .tag import Tag

    # Account type - placeholder until metadata module is implemented
    Account = Any


class StudioCreateInput(BaseModel):
    """Input for creating studios."""

    # Required fields
    name: str  # String!

    # Optional fields
    urls: list[str] | None = None  # [String!]
    parent_id: str | None = None  # ID
    image: str | None = None  # String (URL or base64)
    stash_ids: list[StashIDInput] | None = None  # [StashIDInput!]
    rating100: int | None = None  # Int
    favorite: bool | None = None  # Boolean
    details: str | None = None  # String
    aliases: list[str] | None = None  # [String!]
    tag_ids: list[str] | None = None  # [ID!]
    ignore_auto_tag: bool | None = None  # Boolean


class StudioUpdateInput(BaseModel):
    """Input for updating studios."""

    # Required fields
    id: str  # ID!

    # Optional fields
    name: str | None = None  # String
    urls: list[str] | None = None  # [String!]
    parent_id: str | None = None  # ID
    image: str | None = None  # String (URL or base64)
    stash_ids: list[StashIDInput] | None = None  # [StashIDInput!]
    rating100: int | None = None  # Int
    favorite: bool | None = None  # Boolean
    details: str | None = None  # String
    aliases: list[str] | None = None  # [String!]
    tag_ids: list[str] | None = None  # [ID!]
    ignore_auto_tag: bool | None = None  # Boolean


class Studio(StashObject):
    """Studio type from schema/types/studio.graphql."""

    __type_name__ = "Studio"
    __update_input_type__ = StudioUpdateInput
    __create_input_type__ = StudioCreateInput

    # Fields to track for changes - only fields that can be written via input types
    __tracked_fields__ = {
        "name",  # StudioCreateInput/StudioUpdateInput
        "aliases",  # StudioCreateInput/StudioUpdateInput
        "tags",  # mapped to tag_ids
        "stash_ids",  # StudioCreateInput/StudioUpdateInput
        "urls",  # StudioCreateInput/StudioUpdateInput
        "parent_studio",  # mapped to parent_id
        "details",  # StudioCreateInput/StudioUpdateInput
    }

    # Required fields
    name: str  # String!
    aliases: list[str] = Field(default_factory=list)  # [String!]!
    tags: list[Tag] = Field(default_factory=list)  # [Tag!]!
    stash_ids: list[StashID] = Field(default_factory=list)  # [StashID!]!
    urls: list[str] = Field(default_factory=list)  # [String!]!

    # Optional fields
    parent_studio: Studio | None = None  # Studio
    details: str | None = None  # String
    image_path: str | None = None  # String (Resolver)

    @model_validator(mode="before")
    @classmethod
    def handle_deprecated_url(cls, data: Any) -> Any:
        """Convert deprecated 'url' field to 'urls' list for backward compatibility."""
        if isinstance(data, dict):
            # Handle deprecated single url field
            if data.get("url"):
                if "urls" not in data or not data["urls"]:
                    # Migrate url to urls
                    data["urls"] = [data["url"]]
                elif data["url"] not in data["urls"]:
                    # Ensure url is in urls
                    data["urls"].insert(0, data["url"])
                # Remove the deprecated field
                data.pop("url", None)
            elif "url" in data:
                # url exists but is None/empty, just remove it
                data.pop("url", None)
        return data

    @classmethod
    async def from_account(cls, account: Account) -> Studio:
        """Create studio from account.

        Args:
            account: Account to convert

        Returns:
            New studio instance
        """
        # Get name from account or fallback options
        studio_name = account.display_name or account.username or "Unknown"

        # Build URLs list based on site_url
        urls = []
        if hasattr(account, "site_url") and account.site_url:
            urls = [account.site_url]

        # Get details from account bio or default
        details = account.bio or ""

        # Use studio name from site config if available
        # Safely check for studio_name attribute
        if hasattr(account, "studio_name") and getattr(account, "studio_name", None):
            studio_name = getattr(account, "studio_name", studio_name)

        # Debug print removed for production code

        return cls(
            id="new",  # Will be replaced on save
            name=studio_name,
            urls=urls,
            details=details,
            # Required fields with defaults
            aliases=[],
            tags=[],
            stash_ids=[],
        )

    # Field definitions with their conversion functions
    __field_conversions__ = {
        "name": str,
        "urls": list,
        "aliases": list,
        "details": str,
    }

    __relationships__ = {
        # Standard ID relationships
        "parent_studio": (
            "parent_id",
            False,
            None,
        ),  # (target_field, is_list, transform)
        "tags": ("tag_ids", True, None),
        # Special case with custom transform
        "stash_ids": (
            "stash_ids",
            True,
            lambda s: StashIDInput(endpoint=s.endpoint, stash_id=s.stash_id),
        ),
    }


class StudioDestroyInput(BaseModel):
    """Input for destroying a studio from schema/types/studio.graphql."""

    id: str  # ID!


class FindStudiosResultType(BaseModel):
    """Result type for finding studios from schema/types/studio.graphql."""

    count: int  # Int!
    studios: list[Studio]  # [Studio!]!
