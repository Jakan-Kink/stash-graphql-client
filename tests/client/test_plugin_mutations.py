"""Unit tests for PluginClientMixin mutation operations.

These tests mock at the HTTP boundary using respx, allowing real code execution
through the entire GraphQL client stack including serialization/deserialization.
"""

import json

import httpx
import pytest
import respx

from stash_graphql_client import StashClient
from stash_graphql_client.errors import StashGraphQLError
from tests.fixtures import create_graphql_response


# =============================================================================
# set_plugins_enabled tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_set_plugins_enabled_single(respx_stash_client: StashClient) -> None:
    """Test enabling/disabling a single plugin."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("setPluginsEnabled", True))
        ]
    )

    result = await respx_stash_client.set_plugins_enabled({"plugin-123": True})

    assert result is True

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "setPluginsEnabled" in req["query"]
    assert req["variables"]["enabledMap"] == {"plugin-123": True}


@pytest.mark.asyncio
@pytest.mark.unit
async def test_set_plugins_enabled_multiple(respx_stash_client: StashClient) -> None:
    """Test enabling/disabling multiple plugins."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("setPluginsEnabled", True))
        ]
    )

    enabled_map = {
        "plugin-1": True,
        "plugin-2": False,
        "plugin-3": True,
    }

    result = await respx_stash_client.set_plugins_enabled(enabled_map)

    assert result is True

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["enabledMap"] == enabled_map


@pytest.mark.asyncio
@pytest.mark.unit
async def test_set_plugins_enabled_error_returns_false(
    respx_stash_client: StashClient,
) -> None:
    """Test that set_plugins_enabled returns False on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    result = await respx_stash_client.set_plugins_enabled({"plugin-123": True})

    assert result is False
    assert len(graphql_route.calls) == 1


# =============================================================================
# run_plugin_task tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_run_plugin_task_minimal(respx_stash_client: StashClient) -> None:
    """Test running a plugin task with only plugin_id."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("runPluginTask", "job-123")
            )
        ]
    )

    job_id = await respx_stash_client.run_plugin_task(plugin_id="my-plugin")

    assert job_id == "job-123"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "runPluginTask" in req["query"]
    assert req["variables"]["plugin_id"] == "my-plugin"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_run_plugin_task_all_parameters(respx_stash_client: StashClient) -> None:
    """Test running a plugin task with all parameters."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("runPluginTask", "job-999")
            )
        ]
    )

    args = {"option1": "value1", "option2": 42}

    job_id = await respx_stash_client.run_plugin_task(
        plugin_id="my-plugin",
        task_name="process",
        description="Processing files",
        args_map=args,
    )

    assert job_id == "job-999"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["plugin_id"] == "my-plugin"
    assert req["variables"]["task_name"] == "process"
    assert req["variables"]["description"] == "Processing files"
    assert req["variables"]["args_map"] == args


@pytest.mark.asyncio
@pytest.mark.unit
async def test_run_plugin_task_no_job_id_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test that run_plugin_task raises when no job ID returned."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("runPluginTask", None))
        ]
    )

    with pytest.raises(ValueError, match="No job ID returned from runPluginTask"):
        await respx_stash_client.run_plugin_task(plugin_id="my-plugin")

    assert len(graphql_route.calls) == 1


# =============================================================================
# run_plugin_operation tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_run_plugin_operation_without_args(
    respx_stash_client: StashClient,
) -> None:
    """Test running a plugin operation without arguments."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "runPluginOperation", {"status": "success", "message": "Complete"}
                ),
            )
        ]
    )

    result = await respx_stash_client.run_plugin_operation(plugin_id="my-plugin")

    assert result == {"status": "success", "message": "Complete"}

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "runPluginOperation" in req["query"]
    assert req["variables"]["plugin_id"] == "my-plugin"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_run_plugin_operation_with_args(respx_stash_client: StashClient) -> None:
    """Test running a plugin operation with arguments."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "runPluginOperation", {"result": "data processed"}
                ),
            )
        ]
    )

    args = {"action": "query", "id": "123", "include_metadata": True}

    result = await respx_stash_client.run_plugin_operation(
        plugin_id="my-plugin",
        args=args,
    )

    assert result == {"result": "data processed"}

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["plugin_id"] == "my-plugin"
    assert req["variables"]["args"] == args


# =============================================================================
# reload_plugins tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_reload_plugins_success(respx_stash_client: StashClient) -> None:
    """Test reloading plugins successfully."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("reloadPlugins", True))
        ]
    )

    result = await respx_stash_client.reload_plugins()

    assert result is True

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "reloadPlugins" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_reload_plugins_error_returns_false(
    respx_stash_client: StashClient,
) -> None:
    """Test that reload_plugins returns False on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    result = await respx_stash_client.reload_plugins()

    assert result is False
    assert len(graphql_route.calls) == 1


# =============================================================================
# configure_plugin tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_configure_plugin(respx_stash_client: StashClient) -> None:
    """Test configuring a plugin."""
    config = {
        "api_key": "secret-key-123",
        "endpoint": "https://api.example.com",
        "enabled_features": ["feature1", "feature2"],
    }

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("configurePlugin", config))
        ]
    )

    result = await respx_stash_client.configure_plugin(
        plugin_id="my-plugin",
        config=config,
    )

    assert result == config

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "configurePlugin" in req["query"]
    assert req["variables"]["plugin_id"] == "my-plugin"
    assert req["variables"]["input"] == config


@pytest.mark.asyncio
@pytest.mark.unit
async def test_configure_plugin_error_raises(respx_stash_client: StashClient) -> None:
    """Test that configure_plugin raises on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    with pytest.raises(StashGraphQLError):
        await respx_stash_client.configure_plugin(
            plugin_id="my-plugin",
            config={"setting": "value"},
        )

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_run_plugin_operation_exception(respx_stash_client: StashClient) -> None:
    """Test run_plugin_operation logs and re-raises exceptions."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=Exception("Network error")
    )

    with pytest.raises(Exception, match="Network error"):
        await respx_stash_client.run_plugin_operation(plugin_id="my-plugin")

    # Verify route was called
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "runPluginOperation" in req["query"]
