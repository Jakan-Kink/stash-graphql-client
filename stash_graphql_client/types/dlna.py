"""DLNA types from schema/types/dlna.graphql."""

from __future__ import annotations

from pydantic import BaseModel, Field

from .base import FromGraphQLMixin, StashInput
from .scalars import Time
from .unset import UNSET, UnsetType


class DLNAIP(FromGraphQLMixin, BaseModel):
    """DLNA IP address type from schema/types/dlna.graphql."""

    ip_address: str | UnsetType = Field(default=UNSET, alias="ipAddress")  # String!
    until: Time | None | UnsetType = (
        UNSET  # Time (Time until IP will be no longer allowed/disallowed)
    )


class DLNAStatus(FromGraphQLMixin, BaseModel):
    """DLNA status from schema/types/dlna.graphql."""

    running: bool | UnsetType = UNSET  # Boolean!
    until: Time | None | UnsetType = (
        UNSET  # Time (If not currently running, time until it will be started. If running, time until it will be stopped)
    )
    recent_ip_addresses: list[str] | UnsetType = Field(
        default=UNSET, alias="recentIPAddresses"
    )  # [String!]!
    allowed_ip_addresses: list[DLNAIP] | UnsetType = Field(
        default=UNSET, alias="allowedIPAddresses"
    )  # [DLNAIP!]!


class EnableDLNAInput(StashInput):
    """Input for enabling DLNA."""

    duration: int | None | UnsetType = (
        UNSET  # Int (Duration to enable, in minutes. 0 or null for indefinite.)
    )


class DisableDLNAInput(StashInput):
    """Input for disabling DLNA."""

    duration: int | None | UnsetType = (
        UNSET  # Int (Duration to enable, in minutes. 0 or null for indefinite.)
    )


class AddTempDLNAIPInput(StashInput):
    """Input for adding temporary DLNA IP."""

    address: str | UnsetType = UNSET  # String!
    duration: int | None | UnsetType = (
        UNSET  # Int (Duration to enable, in minutes. 0 or null for indefinite.)
    )


class RemoveTempDLNAIPInput(StashInput):
    """Input for removing temporary DLNA IP."""

    address: str | UnsetType = UNSET  # String!
