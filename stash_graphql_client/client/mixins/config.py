"""Configuration client functionality."""

from typing import Any

from ... import fragments
from ...types import (
    ConfigDefaultSettingsInput,
    ConfigDefaultSettingsResult,
    ConfigDLNAInput,
    ConfigDLNAResult,
    ConfigGeneralInput,
    ConfigGeneralResult,
    ConfigInterfaceInput,
    ConfigInterfaceResult,
    GenerateAPIKeyInput,
)
from ..protocols import StashClientProtocol
from ..utils import sanitize_model_data


class ConfigClientMixin(StashClientProtocol):
    """Mixin for configuration methods."""

    async def configure_general(
        self,
        input_data: ConfigGeneralInput | dict[str, Any],
    ) -> ConfigGeneralResult:
        """Configure general Stash settings.

        Args:
            input_data: ConfigGeneralInput object or dictionary containing general settings

        Returns:
            ConfigGeneralResult with updated configuration

        Examples:
            Configure database path:
            ```python
            config = await client.configure_general({
                "databasePath": "/path/to/database.db"
            })
            print(f"Database path: {config.database_path}")
            ```

            Using the input type:
            ```python
            from stash_graphql_client.types import ConfigGeneralInput

            input_data = ConfigGeneralInput(
                databasePath="/path/to/database.db",
                generatedPath="/path/to/generated"
            )
            config = await client.configure_general(input_data)
            ```
        """
        try:
            if isinstance(input_data, ConfigGeneralInput):
                input_dict = input_data.model_dump(exclude_none=True)
            else:
                input_dict = input_data

            result = await self.execute(
                fragments.CONFIGURE_GENERAL_MUTATION,
                {"input": input_dict},
            )
            clean_data = sanitize_model_data(result["configureGeneral"])
            return ConfigGeneralResult(**clean_data)
        except Exception as e:
            self.log.error(f"Failed to configure general settings: {e}")
            raise

    async def configure_interface(
        self,
        input_data: ConfigInterfaceInput | dict[str, Any],
    ) -> ConfigInterfaceResult:
        """Configure Stash interface settings.

        Args:
            input_data: ConfigInterfaceInput object or dictionary containing interface settings

        Returns:
            ConfigInterfaceResult with updated configuration

        Examples:
            Configure interface options:
            ```python
            config = await client.configure_interface({
                "soundOnPreview": True,
                "wallShowTitle": False
            })
            ```

            Using the input type:
            ```python
            from stash_graphql_client.types import ConfigInterfaceInput

            input_data = ConfigInterfaceInput(
                soundOnPreview=True,
                wallShowTitle=False,
                autostartVideo=True
            )
            config = await client.configure_interface(input_data)
            ```
        """
        try:
            if isinstance(input_data, ConfigInterfaceInput):
                input_dict = input_data.model_dump(exclude_none=True)
            else:
                input_dict = input_data

            result = await self.execute(
                fragments.CONFIGURE_INTERFACE_MUTATION,
                {"input": input_dict},
            )
            clean_data = sanitize_model_data(result["configureInterface"])
            return ConfigInterfaceResult(**clean_data)
        except Exception as e:
            self.log.error(f"Failed to configure interface settings: {e}")
            raise

    async def configure_dlna(
        self,
        input_data: ConfigDLNAInput | dict[str, Any],
    ) -> ConfigDLNAResult:
        """Configure DLNA server settings.

        Args:
            input_data: ConfigDLNAInput object or dictionary containing DLNA settings

        Returns:
            ConfigDLNAResult with updated configuration

        Examples:
            Enable DLNA server:
            ```python
            config = await client.configure_dlna({
                "enabled": True,
                "port": 1338,
                "serverName": "Stash DLNA"
            })
            print(f"DLNA enabled: {config.enabled}")
            ```

            Using the input type:
            ```python
            from stash_graphql_client.types import ConfigDLNAInput

            input_data = ConfigDLNAInput(
                enabled=True,
                port=1338,
                serverName="Stash DLNA",
                whitelistedIPs=["192.168.1.0/24"]
            )
            config = await client.configure_dlna(input_data)
            ```
        """
        try:
            if isinstance(input_data, ConfigDLNAInput):
                input_dict = input_data.model_dump(exclude_none=True)
            else:
                input_dict = input_data

            result = await self.execute(
                fragments.CONFIGURE_DLNA_MUTATION,
                {"input": input_dict},
            )
            clean_data = sanitize_model_data(result["configureDLNA"])
            return ConfigDLNAResult(**clean_data)
        except Exception as e:
            self.log.error(f"Failed to configure DLNA settings: {e}")
            raise

    async def configure_defaults(
        self,
        input_data: ConfigDefaultSettingsInput | dict[str, Any],
    ) -> ConfigDefaultSettingsResult:
        """Configure default metadata operation settings.

        Args:
            input_data: ConfigDefaultSettingsInput object or dictionary containing default settings

        Returns:
            ConfigDefaultSettingsResult with updated configuration

        Examples:
            Configure default delete behavior:
            ```python
            config = await client.configure_defaults({
                "deleteFile": False,
                "deleteGenerated": True
            })
            ```

            Using the input type:
            ```python
            from stash_graphql_client.types import ConfigDefaultSettingsInput

            input_data = ConfigDefaultSettingsInput(
                deleteFile=False,
                deleteGenerated=True
            )
            config = await client.configure_defaults(input_data)
            ```
        """
        try:
            if isinstance(input_data, ConfigDefaultSettingsInput):
                input_dict = input_data.model_dump(exclude_none=True)
            else:
                input_dict = input_data

            result = await self.execute(
                fragments.CONFIGURE_DEFAULTS_MUTATION,
                {"input": input_dict},
            )
            clean_data = sanitize_model_data(result["configureDefaults"])
            return ConfigDefaultSettingsResult(**clean_data)
        except Exception as e:
            self.log.error(f"Failed to configure default settings: {e}")
            raise

    async def configure_ui(
        self,
        input_data: dict[str, Any] | None = None,
        partial: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Configure UI settings.

        Args:
            input_data: Complete UI configuration dictionary (optional)
            partial: Partial UI configuration to merge (optional)

        Returns:
            Updated UI configuration dictionary

        Examples:
            Update UI configuration:
            ```python
            config = await client.configure_ui(
                partial={"theme": "dark", "language": "en-US"}
            )
            ```

            Replace entire UI config:
            ```python
            config = await client.configure_ui(
                input_data={"theme": "dark", "language": "en-US"}
            )
            ```
        """
        try:
            result = await self.execute(
                fragments.CONFIGURE_UI_MUTATION,
                {"input": input_data, "partial": partial},
            )
            return dict(result.get("configureUI", {}))
        except Exception as e:
            self.log.error(f"Failed to configure UI: {e}")
            raise

    async def configure_ui_setting(
        self,
        key: str,
        value: Any,
    ) -> dict[str, Any]:
        """Configure a single UI setting.

        Args:
            key: Setting key to update
            value: New value for the setting

        Returns:
            Updated UI configuration dictionary

        Examples:
            Update a single UI setting:
            ```python
            config = await client.configure_ui_setting("theme", "dark")
            ```

            Update multiple settings one at a time:
            ```python
            await client.configure_ui_setting("theme", "dark")
            await client.configure_ui_setting("language", "en-US")
            ```
        """
        try:
            result = await self.execute(
                fragments.CONFIGURE_UI_SETTING_MUTATION,
                {"key": key, "value": value},
            )
            return dict(result.get("configureUISetting", {}))
        except Exception as e:
            self.log.error(f"Failed to configure UI setting {key}: {e}")
            raise

    async def generate_api_key(
        self,
        input_data: GenerateAPIKeyInput | dict[str, Any],
    ) -> str:
        """Generate a new API key.

        Args:
            input_data: GenerateAPIKeyInput object or dictionary containing:
                - clear: Whether to clear existing API key (optional)

        Returns:
            Generated API key string

        Examples:
            Generate new API key:
            ```python
            api_key = await client.generate_api_key({"clear": False})
            print(f"New API key: {api_key}")
            ```

            Clear and generate new key:
            ```python
            from stash_graphql_client.types import GenerateAPIKeyInput

            input_data = GenerateAPIKeyInput(clear=True)
            api_key = await client.generate_api_key(input_data)
            ```
        """
        try:
            if isinstance(input_data, GenerateAPIKeyInput):
                input_dict = input_data.model_dump(exclude_none=True)
            else:
                input_dict = input_data

            result = await self.execute(
                fragments.GENERATE_API_KEY_MUTATION,
                {"input": input_dict},
            )
            return str(result.get("generateAPIKey", ""))
        except Exception as e:
            self.log.error(f"Failed to generate API key: {e}")
            raise
