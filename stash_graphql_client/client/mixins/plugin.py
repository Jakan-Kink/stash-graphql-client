"""Plugin operations client functionality."""

from typing import Any

from ...types import BoolMap, Map, Plugin, PluginTask
from ..protocols import StashClientProtocol


class PluginClientMixin(StashClientProtocol):
    """Mixin for plugin-related client methods."""

    async def get_plugins(self) -> list[Plugin]:
        """Get all loaded plugins.

        Returns:
            List of Plugin objects representing all loaded plugins

        Examples:
            Get all plugins:
            ```python
            plugins = await client.get_plugins()
            for plugin in plugins:
                print(f"Plugin: {plugin.name} (enabled={plugin.enabled})")
            ```

            Filter enabled plugins:
            ```python
            plugins = await client.get_plugins()
            enabled = [p for p in plugins if p.enabled]
            print(f"Enabled plugins: {len(enabled)}")
            ```
        """
        try:
            result = await self.execute(
                """
                query Plugins {
                    plugins {
                        id
                        name
                        description
                        url
                        version
                        enabled
                        paths {
                            javascript
                            css
                        }
                        tasks {
                            name
                            description
                        }
                        hooks {
                            name
                            description
                            hooks
                        }
                        settings {
                            name
                            displayName
                            description
                            type
                        }
                        requires
                    }
                }
                """
            )
            plugin_data_list = result.get("plugins", [])
            return [
                self._decode_result(Plugin, plugin_data)
                for plugin_data in plugin_data_list
            ]
        except Exception as e:
            self.log.error(f"Failed to get plugins: {e}")
            return []

    async def get_plugin_tasks(self) -> list[PluginTask]:
        """Get all available plugin tasks.

        Returns:
            List of PluginTask objects representing all available plugin operations

        Examples:
            Get all plugin tasks:
            ```python
            tasks = await client.get_plugin_tasks()
            for task in tasks:
                print(f"Task: {task.name} - {task.description}")
                print(f"  Plugin: {task.plugin.name}")
            ```

            Find tasks for a specific plugin:
            ```python
            tasks = await client.get_plugin_tasks()
            plugin_tasks = [t for t in tasks if t.plugin.id == "my-plugin-id"]
            ```
        """
        try:
            result = await self.execute(
                """
                query PluginTasks {
                    pluginTasks {
                        name
                        description
                        plugin {
                            id
                            name
                            version
                        }
                    }
                }
                """
            )
            task_data_list = result.get("pluginTasks", [])
            return [
                self._decode_result(PluginTask, task_data)
                for task_data in task_data_list
            ]
        except Exception as e:
            self.log.error(f"Failed to get plugin tasks: {e}")
            return []

    async def set_plugins_enabled(self, enabled_map: BoolMap | dict[str, bool]) -> bool:
        """Enable or disable plugins.

        Args:
            enabled_map: Dictionary mapping plugin IDs to enabled status (True/False).
                        Plugins not in the map are not affected.

        Returns:
            True if the operation was successful, False otherwise

        Examples:
            Enable a plugin:
            ```python
            success = await client.set_plugins_enabled({
                "my-plugin-id": True
            })
            ```

            Disable multiple plugins:
            ```python
            success = await client.set_plugins_enabled({
                "plugin-1": False,
                "plugin-2": False,
                "plugin-3": True
            })
            ```
        """
        try:
            result = await self.execute(
                """
                mutation SetPluginsEnabled($enabledMap: BoolMap!) {
                    setPluginsEnabled(enabledMap: $enabledMap)
                }
                """,
                {"enabledMap": enabled_map},
            )
            return bool(result.get("setPluginsEnabled", False))
        except Exception as e:
            self.log.error(f"Failed to set plugins enabled: {e}")
            return False

    async def run_plugin_task(
        self,
        plugin_id: str,
        task_name: str | None = None,
        description: str | None = None,
        args_map: Map | dict[str, Any] | None = None,
    ) -> str:
        """Run a plugin task asynchronously via the job queue.

        If task_name is provided, the task must exist in the plugin config and the task's
        configuration will be used. If no task_name is provided, the plugin will be executed
        with the arguments provided only.

        Args:
            plugin_id: ID of the plugin to run
            task_name: Optional name of the task to run (uses task's default config)
            description: Optional description for the job queue
            args_map: Optional arguments to pass to the plugin (as a dictionary)

        Returns:
            Job ID for the plugin task

        Raises:
            ValueError: If the operation fails or no job ID is returned

        Examples:
            Run a plugin task with a task name:
            ```python
            job_id = await client.run_plugin_task(
                plugin_id="my-plugin",
                task_name="scan",
                description="Scanning library"
            )
            await client.wait_for_job(job_id)
            ```

            Run a plugin with custom arguments:
            ```python
            job_id = await client.run_plugin_task(
                plugin_id="my-plugin",
                args_map={"path": "/videos", "recursive": True}
            )
            ```

            Run with both task name and additional arguments:
            ```python
            job_id = await client.run_plugin_task(
                plugin_id="my-plugin",
                task_name="process",
                description="Processing files",
                args_map={"overwrite": True}
            )
            ```
        """
        try:
            variables: dict[str, Any] = {"plugin_id": plugin_id}

            if task_name is not None:
                variables["task_name"] = task_name

            if description is not None:
                variables["description"] = description

            if args_map is not None:
                variables["args_map"] = args_map

            result = await self.execute(
                """
                mutation RunPluginTask(
                    $plugin_id: ID!
                    $task_name: String
                    $description: String
                    $args_map: Map
                ) {
                    runPluginTask(
                        plugin_id: $plugin_id
                        task_name: $task_name
                        description: $description
                        args_map: $args_map
                    )
                }
                """,
                variables,
            )

            job_id = result.get("runPluginTask")
            if not job_id:
                raise ValueError("No job ID returned from runPluginTask")

            return str(job_id)
        except Exception as e:
            self.log.error(f"Failed to run plugin task: {e}")
            raise

    async def run_plugin_operation(
        self,
        plugin_id: str,
        args: Map | dict[str, Any] | None = None,
    ) -> Any:
        """Run a plugin operation synchronously (not via job queue).

        The operation is run immediately and does not use the job queue.
        Returns the result directly from the plugin.

        Args:
            plugin_id: ID of the plugin to run
            args: Optional arguments to pass to the plugin (as a dictionary)

        Returns:
            The result from the plugin operation (type depends on the plugin)

        Examples:
            Run a plugin operation:
            ```python
            result = await client.run_plugin_operation(
                plugin_id="my-plugin",
                args={"action": "query", "id": "123"}
            )
            print(f"Plugin returned: {result}")
            ```

            Run without arguments:
            ```python
            result = await client.run_plugin_operation(plugin_id="my-plugin")
            ```
        """
        try:
            variables: dict[str, Any] = {"plugin_id": plugin_id}

            if args is not None:
                variables["args"] = args

            result = await self.execute(
                """
                mutation RunPluginOperation($plugin_id: ID!, $args: Map) {
                    runPluginOperation(plugin_id: $plugin_id, args: $args)
                }
                """,
                variables,
            )

            return result.get("runPluginOperation")
        except Exception as e:
            self.log.error(f"Failed to run plugin operation: {e}")
            raise

    async def reload_plugins(self) -> bool:
        """Reload all plugins.

        Returns:
            True if plugins were reloaded successfully, False otherwise

        Examples:
            Reload all plugins:
            ```python
            success = await client.reload_plugins()
            if success:
                print("Plugins reloaded successfully")
            ```
        """
        try:
            result = await self.execute(
                """
                mutation ReloadPlugins {
                    reloadPlugins
                }
                """
            )
            return bool(result.get("reloadPlugins", False))
        except Exception as e:
            self.log.error(f"Failed to reload plugins: {e}")
            return False

    async def configure_plugin(
        self,
        plugin_id: str,
        config: Map | dict[str, Any],
    ) -> Map:
        """Configure a plugin's settings.

        Overwrites the entire plugin configuration for the given plugin.

        Args:
            plugin_id: ID of the plugin to configure
            config: Configuration dictionary to set for the plugin

        Returns:
            The updated plugin configuration

        Examples:
            Configure a plugin:
            ```python
            config = await client.configure_plugin(
                plugin_id="my-plugin",
                config={
                    "api_key": "secret-key",
                    "endpoint": "https://api.example.com",
                    "enabled_features": ["feature1", "feature2"]
                }
            )
            print(f"Updated config: {config}")
            ```

            Update specific settings:
            ```python
            # Get current config first
            plugins = await client.get_plugins()
            my_plugin = next(p for p in plugins if p.id == "my-plugin")

            # Modify and save
            config = await client.configure_plugin(
                plugin_id="my-plugin",
                config={"setting1": "value1", "setting2": True}
            )
            ```
        """
        try:
            result = await self.execute(
                """
                mutation ConfigurePlugin($plugin_id: ID!, $input: Map!) {
                    configurePlugin(plugin_id: $plugin_id, input: $input)
                }
                """,
                {"plugin_id": plugin_id, "input": config},
            )

            return result.get("configurePlugin", {})
        except Exception as e:
            self.log.error(f"Failed to configure plugin: {e}")
            raise
