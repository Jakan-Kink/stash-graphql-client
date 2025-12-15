"""Unit tests for PluginClientMixin query operations.

These tests mock at the HTTP boundary using respx, allowing real code execution
through the entire GraphQL client stack including serialization/deserialization.
"""

import json

import httpx
import pytest
import respx

from stash_graphql_client import StashClient
from tests.fixtures import create_graphql_response


# =============================================================================
# Helper functions for creating plugin test data
# =============================================================================


def create_plugin_paths_dict(
    javascript: list[str] | None = None,
    css: list[str] | None = None,
) -> dict:
    """Create a PluginPaths dictionary for testing."""
    return {
        "javascript": javascript or ["/plugins/my-plugin/script.js"],
        "css": css or ["/plugins/my-plugin/style.css"],
    }


def create_plugin_task_dict(
    name: str = "test_task",
    description: str | None = "Test task description",
) -> dict:
    """Create a PluginTask dictionary for testing."""
    return {
        "name": name,
        "description": description,
    }


def create_plugin_dict(
    id: str = "plugin-123",
    name: str = "Test Plugin",
    enabled: bool = True,
    description: str | None = "A test plugin",
    url: str | None = "https://example.com/plugin",
    version: str | None = "1.0.0",
    paths: dict | None = None,
    tasks: list[dict] | None = None,
    hooks: list[dict] | None = None,
    settings: list[dict] | None = None,
    requires: list[str] | None = None,
) -> dict:
    """Create a Plugin dictionary for testing."""
    return {
        "id": id,
        "name": name,
        "enabled": enabled,
        "description": description,
        "url": url,
        "version": version,
        "paths": paths or create_plugin_paths_dict(),
        "tasks": tasks or [create_plugin_task_dict()],
        "hooks": hooks or [],
        "settings": settings or [],
        "requires": requires or [],
    }


def create_plugin_task_full_dict(
    name: str = "test_task",
    description: str | None = "Test task description",
    plugin: dict | None = None,
) -> dict:
    """Create a full PluginTask dictionary (with plugin reference) for testing."""
    return {
        "name": name,
        "description": description,
        "plugin": plugin
        or {
            "id": "plugin-123",
            "name": "Test Plugin",
            "version": "1.0.0",
        },
    }


# =============================================================================
# get_plugins tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_plugins(respx_stash_client: StashClient) -> None:
    """Test getting all plugins."""
    plugin_data = create_plugin_dict(id="plugin-1", name="Plugin One")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("plugins", [plugin_data]))
        ]
    )

    plugins = await respx_stash_client.get_plugins()

    assert len(plugins) == 1
    assert plugins[0].id == "plugin-1"
    assert plugins[0].name == "Plugin One"
    assert plugins[0].enabled is True

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "plugins" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_plugins_multiple(respx_stash_client: StashClient) -> None:
    """Test getting multiple plugins."""
    plugins_data = [
        create_plugin_dict(id="plugin-1", name="Plugin One", enabled=True),
        create_plugin_dict(id="plugin-2", name="Plugin Two", enabled=False),
        create_plugin_dict(id="plugin-3", name="Plugin Three", enabled=True),
    ]

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("plugins", plugins_data))
        ]
    )

    plugins = await respx_stash_client.get_plugins()

    assert len(plugins) == 3
    assert plugins[0].id == "plugin-1"
    assert plugins[0].enabled is True
    assert plugins[1].id == "plugin-2"
    assert plugins[1].enabled is False
    assert plugins[2].id == "plugin-3"
    assert plugins[2].enabled is True

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_plugins_empty(respx_stash_client: StashClient) -> None:
    """Test getting plugins when none exist."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(200, json=create_graphql_response("plugins", []))]
    )

    plugins = await respx_stash_client.get_plugins()

    assert len(plugins) == 0
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_plugins_error_returns_empty(
    respx_stash_client: StashClient,
) -> None:
    """Test that get_plugins returns empty list on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    plugins = await respx_stash_client.get_plugins()

    assert len(plugins) == 0
    assert len(graphql_route.calls) == 1


# =============================================================================
# get_plugin_tasks tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_plugin_tasks(respx_stash_client: StashClient) -> None:
    """Test getting all plugin tasks."""
    task_data = create_plugin_task_full_dict(
        name="scan_library",
        description="Scan the library",
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("pluginTasks", [task_data])
            )
        ]
    )

    tasks = await respx_stash_client.get_plugin_tasks()

    assert len(tasks) == 1
    assert tasks[0].name == "scan_library"
    assert tasks[0].description == "Scan the library"
    assert tasks[0].plugin.id == "plugin-123"
    assert tasks[0].plugin.name == "Test Plugin"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "pluginTasks" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_plugin_tasks_multiple(respx_stash_client: StashClient) -> None:
    """Test getting multiple plugin tasks."""
    tasks_data = [
        create_plugin_task_full_dict(
            name="scan",
            description="Scan library",
            plugin={"id": "plugin-1", "name": "Scanner", "version": "1.0.0"},
        ),
        create_plugin_task_full_dict(
            name="clean",
            description="Clean library",
            plugin={"id": "plugin-2", "name": "Cleaner", "version": "2.0.0"},
        ),
    ]

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("pluginTasks", tasks_data))
        ]
    )

    tasks = await respx_stash_client.get_plugin_tasks()

    assert len(tasks) == 2
    assert tasks[0].name == "scan"
    assert tasks[0].plugin.id == "plugin-1"
    assert tasks[1].name == "clean"
    assert tasks[1].plugin.id == "plugin-2"

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_plugin_tasks_empty(respx_stash_client: StashClient) -> None:
    """Test getting plugin tasks when none exist."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("pluginTasks", []))
        ]
    )

    tasks = await respx_stash_client.get_plugin_tasks()

    assert len(tasks) == 0
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_plugin_tasks_error_returns_empty(
    respx_stash_client: StashClient,
) -> None:
    """Test that get_plugin_tasks returns empty list on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    tasks = await respx_stash_client.get_plugin_tasks()

    assert len(tasks) == 0
    assert len(graphql_route.calls) == 1
