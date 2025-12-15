"""Plugin types from schema/types/plugin.graphql."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from .base import FromGraphQLMixin, StashInput
from .unset import UNSET, UnsetType


class PluginSettingTypeEnum(str, Enum):
    """Plugin setting type enum from schema/types/plugin.graphql."""

    STRING = "STRING"
    NUMBER = "NUMBER"
    BOOLEAN = "BOOLEAN"


class PluginSetting(FromGraphQLMixin, BaseModel):
    """Plugin setting type from schema/types/plugin.graphql."""

    name: str | UnsetType = UNSET  # String!
    type: PluginSettingTypeEnum | UnsetType = UNSET  # PluginSettingTypeEnum!
    display_name: str | None | UnsetType = Field(
        default=UNSET, alias="displayName"
    )  # String
    description: str | None | UnsetType = UNSET  # String


class PluginValueInput(StashInput):
    """Input for plugin values from schema/types/plugin.graphql."""

    str_value: str | None | UnsetType = Field(default=UNSET, alias="str")  # String
    i: int | None | UnsetType = UNSET  # Int
    b: bool | None | UnsetType = UNSET  # Boolean
    f: float | None | UnsetType = UNSET  # Float
    o: list[PluginArgInput] | None | UnsetType = UNSET  # [PluginArgInput!]
    a: list[PluginValueInput] | None | UnsetType = UNSET  # [PluginValueInput!]


class PluginArgInput(StashInput):
    """Input for plugin arguments from schema/types/plugin.graphql."""

    key: str | UnsetType = UNSET  # String!
    value: PluginValueInput | None | UnsetType = UNSET  # PluginValueInput


class PluginPaths(FromGraphQLMixin, BaseModel):
    """Plugin paths type from schema/types/plugin.graphql."""

    javascript: list[str] | UnsetType = UNSET  # [String!] (path to javascript files)
    css: list[str] | None | UnsetType = (
        UNSET  # [String!] - nullable list (path to css files)
    )


class PluginTask(FromGraphQLMixin, BaseModel):
    """Plugin task type from schema/types/plugin.graphql."""

    name: str | UnsetType = UNSET  # String!
    plugin: Plugin | UnsetType = UNSET  # Plugin!
    description: str | None | UnsetType = UNSET  # String


class PluginHook(FromGraphQLMixin, BaseModel):
    """Plugin hook type from schema/types/plugin.graphql."""

    name: str | UnsetType = UNSET  # String!
    plugin: Plugin | UnsetType = UNSET  # Plugin!
    description: str | None | UnsetType = UNSET  # String
    hooks: list[str] | None | UnsetType = UNSET  # [String!]


class Plugin(FromGraphQLMixin, BaseModel):
    """Plugin type from schema/types/plugin.graphql."""

    id: str  # ID!
    name: str | UnsetType = UNSET  # String!
    enabled: bool | UnsetType = UNSET  # Boolean!
    paths: PluginPaths | UnsetType = UNSET  # PluginPaths!
    description: str | None | UnsetType = UNSET  # String
    url: str | None | UnsetType = UNSET  # String
    version: str | None | UnsetType = UNSET  # String
    tasks: list[PluginTask] | None | UnsetType = UNSET  # [PluginTask!]
    hooks: list[PluginHook] | None | UnsetType = UNSET  # [PluginHook!]
    settings: list[PluginSetting] | None | UnsetType = UNSET  # [PluginSetting!]
    requires: list[str] | None | UnsetType = (
        UNSET  # [ID!] (Plugin IDs of plugins that this plugin depends on. Applies only for UI plugins to indicate css/javascript load order.)
    )


class PluginResult(FromGraphQLMixin, BaseModel):
    """Plugin result type from schema/types/plugin.graphql."""

    error: str | None | UnsetType = UNSET  # String
    result: str | None | UnsetType = UNSET  # String


# Rebuild models to resolve forward references
PluginValueInput.model_rebuild()
PluginArgInput.model_rebuild()
PluginTask.model_rebuild()
PluginHook.model_rebuild()
Plugin.model_rebuild()
