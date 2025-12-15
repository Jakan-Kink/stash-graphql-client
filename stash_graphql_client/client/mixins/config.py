"""Configuration client functionality."""

from typing import Any

from ... import fragments
from ...types import (
    AddTempDLNAIPInput,
    ConfigDefaultSettingsInput,
    ConfigDefaultSettingsResult,
    ConfigDLNAInput,
    ConfigDLNAResult,
    ConfigGeneralInput,
    ConfigGeneralResult,
    ConfigInterfaceInput,
    ConfigInterfaceResult,
    ConfigScrapingInput,
    ConfigScrapingResult,
    DisableDLNAInput,
    EnableDLNAInput,
    FilterMode,
    GenerateAPIKeyInput,
    RemoveTempDLNAIPInput,
    SavedFilter,
    StashBoxInput,
    StashBoxValidationResult,
)
from ..protocols import StashClientProtocol


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
                input_dict = input_data.to_graphql()
            else:
                input_dict = input_data

            return await self.execute(
                fragments.CONFIGURE_GENERAL_MUTATION,
                {"input": input_dict},
                result_type=ConfigGeneralResult,
            )
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
                input_dict = input_data.to_graphql()
            else:
                input_dict = input_data

            return await self.execute(
                fragments.CONFIGURE_INTERFACE_MUTATION,
                {"input": input_dict},
                result_type=ConfigInterfaceResult,
            )
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
                input_dict = input_data.to_graphql()
            else:
                input_dict = input_data

            return await self.execute(
                fragments.CONFIGURE_DLNA_MUTATION,
                {"input": input_dict},
                result_type=ConfigDLNAResult,
            )
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
                input_dict = input_data.to_graphql()
            else:
                input_dict = input_data

            return await self.execute(
                fragments.CONFIGURE_DEFAULTS_MUTATION,
                {"input": input_dict},
                result_type=ConfigDefaultSettingsResult,
            )
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
                input_dict = input_data.to_graphql()
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

    async def find_saved_filter(self, id: str) -> SavedFilter | None:
        """Find a saved filter by ID.

        Args:
            id: Filter ID

        Returns:
            SavedFilter object if found, None otherwise
        """
        try:
            result = await self.execute(
                fragments.FIND_SAVED_FILTER_QUERY,
                {"id": id},
            )
            if result and result.get("findSavedFilter"):
                return self._decode_result(SavedFilter, result["findSavedFilter"])
            return None
        except Exception as e:
            self.log.error(f"Failed to find saved filter {id}: {e}")
            return None

    async def find_saved_filters(
        self,
        mode: FilterMode | None = None,
    ) -> list[SavedFilter]:
        """Find all saved filters, optionally filtered by mode.

        Args:
            mode: Optional filter mode to filter by

        Returns:
            List of SavedFilter objects
        """
        try:
            result = await self.execute(
                fragments.FIND_SAVED_FILTERS_QUERY,
                {"mode": mode.value if mode else None},
            )
            filters_data = result.get("findSavedFilters", [])
            return [self._decode_result(SavedFilter, f) for f in filters_data]
        except Exception as e:
            self.log.error(f"Failed to find saved filters: {e}")
            return []

    async def configure_scraping(
        self,
        input_data: ConfigScrapingInput | dict[str, Any],
    ) -> ConfigScrapingResult:
        """Configure scraping settings.

        Args:
            input_data: ConfigScrapingInput object or dictionary

        Returns:
            ConfigScrapingResult with updated configuration
        """
        try:
            if isinstance(input_data, ConfigScrapingInput):
                input_dict = input_data.to_graphql()
            else:
                input_dict = input_data

            result = await self.execute(
                fragments.CONFIGURE_SCRAPING_MUTATION,
                {"input": input_dict},
            )
            return self._decode_result(
                ConfigScrapingResult, result["configureScraping"]
            )
        except Exception as e:
            self.log.error(f"Failed to configure scraping: {e}")
            raise

    async def validate_stashbox_credentials(
        self,
        input_data: StashBoxInput | dict[str, Any],
    ) -> StashBoxValidationResult:
        """Validate StashBox credentials.

        Args:
            input_data: StashBoxInput object or dictionary containing endpoint and api_key

        Returns:
            StashBoxValidationResult with validation status
        """
        try:
            if isinstance(input_data, StashBoxInput):
                input_dict = input_data.to_graphql()
            else:
                input_dict = input_data

            result = await self.execute(
                fragments.VALIDATE_STASHBOX_CREDENTIALS_QUERY,
                {"input": input_dict},
            )
            return self._decode_result(
                StashBoxValidationResult, result["validateStashBoxCredentials"]
            )
        except Exception as e:
            self.log.error(f"Failed to validate StashBox credentials: {e}")
            raise

    async def enable_dlna(
        self,
        input_data: EnableDLNAInput | dict[str, Any],
    ) -> bool:
        """Enable DLNA server.

        Args:
            input_data: EnableDLNAInput object or dictionary

        Returns:
            True if successful
        """
        try:
            if isinstance(input_data, EnableDLNAInput):
                input_dict = input_data.to_graphql()
            else:
                input_dict = input_data

            result = await self.execute(
                fragments.ENABLE_DLNA_MUTATION,
                {"input": input_dict},
            )
            return bool(result.get("enableDLNA", False))
        except Exception as e:
            self.log.error(f"Failed to enable DLNA: {e}")
            raise

    async def disable_dlna(
        self,
        input_data: DisableDLNAInput | dict[str, Any],
    ) -> bool:
        """Disable DLNA server.

        Args:
            input_data: DisableDLNAInput object or dictionary

        Returns:
            True if successful
        """
        try:
            if isinstance(input_data, DisableDLNAInput):
                input_dict = input_data.to_graphql()
            else:
                input_dict = input_data

            result = await self.execute(
                fragments.DISABLE_DLNA_MUTATION,
                {"input": input_dict},
            )
            return bool(result.get("disableDLNA", False))
        except Exception as e:
            self.log.error(f"Failed to disable DLNA: {e}")
            raise

    async def add_temp_dlna_ip(
        self,
        input_data: AddTempDLNAIPInput | dict[str, Any],
    ) -> bool:
        """Add temporary DLNA IP whitelist.

        Args:
            input_data: AddTempDLNAIPInput object or dictionary

        Returns:
            True if successful
        """
        try:
            if isinstance(input_data, AddTempDLNAIPInput):
                input_dict = input_data.to_graphql()
            else:
                input_dict = input_data

            result = await self.execute(
                fragments.ADD_TEMP_DLNA_IP_MUTATION,
                {"input": input_dict},
            )
            return bool(result.get("addTempDLNAIP", False))
        except Exception as e:
            self.log.error(f"Failed to add temp DLNA IP: {e}")
            raise

    async def remove_temp_dlna_ip(
        self,
        input_data: RemoveTempDLNAIPInput | dict[str, Any],
    ) -> bool:
        """Remove temporary DLNA IP from whitelist.

        Args:
            input_data: RemoveTempDLNAIPInput object or dictionary

        Returns:
            True if successful
        """
        try:
            if isinstance(input_data, RemoveTempDLNAIPInput):
                input_dict = input_data.to_graphql()
            else:
                input_dict = input_data

            result = await self.execute(
                fragments.REMOVE_TEMP_DLNA_IP_MUTATION,
                {"input": input_dict},
            )
            return bool(result.get("removeTempDLNAIP", False))
        except Exception as e:
            self.log.error(f"Failed to remove temp DLNA IP: {e}")
            raise
