"""Unit tests for ConfigClientMixin.

These tests mock at the HTTP boundary using respx, allowing real code execution
through the entire GraphQL client stack including serialization/deserialization.

NOTE: This test file is written BEFORE the mixin implementation exists.
The tests define the expected API contract for the configuration mixin.
"""

import json
from typing import Any

import httpx
import pytest
import respx

from stash_graphql_client import StashClient
from stash_graphql_client.errors import StashGraphQLError
from stash_graphql_client.types import (
    ConfigDefaultSettingsInput,
    ConfigDLNAInput,
    ConfigGeneralInput,
    ConfigInterfaceInput,
    GenerateAPIKeyInput,
)
from tests.fixtures import (
    create_config_defaults_result,
    create_config_dlna_result,
    create_config_general_result,
    create_config_interface_result,
    create_graphql_response,
)


# =============================================================================
# configure_general tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_configure_general_with_dict(respx_stash_client: StashClient) -> None:
    """Test configuring general settings with dict input."""
    config_data = create_config_general_result(parallel_tasks=4)
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("configureGeneral", config_data)
            )
        ]
    )

    result = await respx_stash_client.configure_general({"parallelTasks": 4})

    assert result is not None
    assert result.parallel_tasks == 4
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "configureGeneral" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_configure_general_with_model(respx_stash_client: StashClient) -> None:
    """Test configuring general settings with ConfigGeneralInput model."""
    config_data = create_config_general_result()
    # Add camelCase keys for fields beyond required minimum
    config_data["ffmpegPath"] = "/custom/ffmpeg"
    config_data["ffprobePath"] = "/custom/ffprobe"
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("configureGeneral", config_data)
            )
        ]
    )

    input_data = ConfigGeneralInput(
        ffmpegPath="/custom/ffmpeg", ffprobePath="/custom/ffprobe"
    )
    result = await respx_stash_client.configure_general(input_data)

    assert result is not None
    assert result.ffmpeg_path == "/custom/ffmpeg"
    assert result.ffprobe_path == "/custom/ffprobe"
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_configure_general_error_raises(respx_stash_client: StashClient) -> None:
    """Test configure_general raises on error."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    with pytest.raises(StashGraphQLError, match="Server error"):
        await respx_stash_client.configure_general({"parallelTasks": 4})


# =============================================================================
# configure_interface tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_configure_interface_with_dict(respx_stash_client: StashClient) -> None:
    """Test configuring interface settings with dict input."""
    config_data = create_config_interface_result(language="de-DE")
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("configureInterface", config_data)
            )
        ]
    )

    result = await respx_stash_client.configure_interface({"language": "de-DE"})

    assert result is not None
    assert result.language == "de-DE"
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "configureInterface" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_configure_interface_with_model(respx_stash_client: StashClient) -> None:
    """Test configuring interface settings with ConfigInterfaceInput model."""
    config_data = create_config_interface_result(
        css_enabled=True, javascript_enabled=True
    )
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("configureInterface", config_data)
            )
        ]
    )

    input_data = ConfigInterfaceInput(cssEnabled=True, javascriptEnabled=True)
    result = await respx_stash_client.configure_interface(input_data)

    assert result is not None
    assert result.css_enabled is True
    assert result.javascript_enabled is True
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_configure_interface_error_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test configure_interface raises on error."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    with pytest.raises(StashGraphQLError, match="Server error"):
        await respx_stash_client.configure_interface({"language": "en-US"})


# =============================================================================
# configure_dlna tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_configure_dlna_with_dict(respx_stash_client: StashClient) -> None:
    """Test configuring DLNA settings with dict input."""
    config_data = create_config_dlna_result(enabled=True, port=1339)
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("configureDLNA", config_data)
            )
        ]
    )

    result = await respx_stash_client.configure_dlna({"enabled": True, "port": 1339})

    assert result is not None
    assert result.enabled is True
    assert result.port == 1339
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "configureDLNA" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_configure_dlna_with_model(respx_stash_client: StashClient) -> None:
    """Test configuring DLNA settings with ConfigDLNAInput model."""
    config_data = create_config_dlna_result(
        server_name="my-stash", whitelisted_ips=["192.168.1.100"]
    )
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("configureDLNA", config_data)
            )
        ]
    )

    input_data = ConfigDLNAInput(
        serverName="my-stash", whitelistedIPs=["192.168.1.100"]
    )
    result = await respx_stash_client.configure_dlna(input_data)

    assert result is not None
    assert result.server_name == "my-stash"
    assert "192.168.1.100" in result.whitelisted_ips
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_configure_dlna_error_raises(respx_stash_client: StashClient) -> None:
    """Test configure_dlna raises on error."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    with pytest.raises(StashGraphQLError, match="Server error"):
        await respx_stash_client.configure_dlna({"enabled": False})


# =============================================================================
# configure_defaults tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_configure_defaults_with_dict(respx_stash_client: StashClient) -> None:
    """Test configuring default settings with dict input."""
    config_data = create_config_defaults_result(delete_file=True, delete_generated=True)
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("configureDefaults", config_data)
            )
        ]
    )

    result = await respx_stash_client.configure_defaults(
        {"deleteFile": True, "deleteGenerated": True}
    )

    assert result is not None
    assert result.delete_file is True
    assert result.delete_generated is True
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "configureDefaults" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_configure_defaults_with_model(respx_stash_client: StashClient) -> None:
    """Test configuring default settings with ConfigDefaultSettingsInput model."""
    config_data = create_config_defaults_result(
        delete_file=False, delete_generated=False
    )
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("configureDefaults", config_data)
            )
        ]
    )

    input_data = ConfigDefaultSettingsInput(deleteFile=False, deleteGenerated=False)
    result = await respx_stash_client.configure_defaults(input_data)

    assert result is not None
    assert result.delete_file is False
    assert result.delete_generated is False
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_configure_defaults_error_raises(respx_stash_client: StashClient) -> None:
    """Test configure_defaults raises on error."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    with pytest.raises(StashGraphQLError, match="Server error"):
        await respx_stash_client.configure_defaults({"deleteFile": True})


# =============================================================================
# configure_ui tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_configure_ui_with_full_input(respx_stash_client: StashClient) -> None:
    """Test configuring UI with full input dict (overwrites entire config)."""
    ui_config: dict[str, Any] = {"theme": "dark", "customSetting": "value"}
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("configureUI", ui_config))
        ]
    )

    result = await respx_stash_client.configure_ui(input_data=ui_config)

    assert result == ui_config
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "configureUI" in req["query"]
    assert req["variables"]["input"] == ui_config


@pytest.mark.asyncio
@pytest.mark.unit
async def test_configure_ui_with_partial_input(respx_stash_client: StashClient) -> None:
    """Test configuring UI with partial input dict (merges with existing)."""
    partial_config: dict[str, Any] = {"theme": "light"}
    merged_result: dict[str, Any] = {"theme": "light", "existingSetting": "preserved"}
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("configureUI", merged_result)
            )
        ]
    )

    result = await respx_stash_client.configure_ui(partial=partial_config)

    assert result == merged_result
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["partial"] == partial_config


@pytest.mark.asyncio
@pytest.mark.unit
async def test_configure_ui_error_raises(respx_stash_client: StashClient) -> None:
    """Test configure_ui raises on error."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    with pytest.raises(StashGraphQLError, match="Server error"):
        await respx_stash_client.configure_ui(input_data={"theme": "dark"})


# =============================================================================
# configure_ui_setting tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_configure_ui_setting_string_value(
    respx_stash_client: StashClient,
) -> None:
    """Test configuring a single UI setting with string value."""
    result_config: dict[str, Any] = {"theme": "dark", "otherSetting": "value"}
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("configureUISetting", result_config)
            )
        ]
    )

    result = await respx_stash_client.configure_ui_setting("theme", "dark")

    assert result == result_config
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "configureUISetting" in req["query"]
    assert req["variables"]["key"] == "theme"
    assert req["variables"]["value"] == "dark"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_configure_ui_setting_bool_value(respx_stash_client: StashClient) -> None:
    """Test configuring a single UI setting with boolean value."""
    result_config: dict[str, Any] = {"showAdvanced": True}
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("configureUISetting", result_config)
            )
        ]
    )

    result = await respx_stash_client.configure_ui_setting("showAdvanced", True)

    assert result == result_config
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["value"] is True


@pytest.mark.asyncio
@pytest.mark.unit
async def test_configure_ui_setting_null_value(respx_stash_client: StashClient) -> None:
    """Test configuring a single UI setting with null to delete it."""
    result_config: dict[str, Any] = {}  # Setting removed
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("configureUISetting", result_config)
            )
        ]
    )

    result = await respx_stash_client.configure_ui_setting("oldSetting", None)

    assert result == result_config
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["value"] is None


@pytest.mark.asyncio
@pytest.mark.unit
async def test_configure_ui_setting_error_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test configure_ui_setting raises on error."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    with pytest.raises(StashGraphQLError, match="Server error"):
        await respx_stash_client.configure_ui_setting("theme", "dark")


# =============================================================================
# generate_api_key tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_generate_api_key_with_dict(respx_stash_client: StashClient) -> None:
    """Test generating API key with dict input."""
    new_api_key = "sk-test-api-key-12345"
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("generateAPIKey", new_api_key)
            )
        ]
    )

    result = await respx_stash_client.generate_api_key({})

    assert result == new_api_key
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "generateAPIKey" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_generate_api_key_with_model(respx_stash_client: StashClient) -> None:
    """Test generating API key with GenerateAPIKeyInput model."""
    new_api_key = "sk-new-api-key-67890"
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("generateAPIKey", new_api_key)
            )
        ]
    )

    input_data = GenerateAPIKeyInput(clear=False)
    result = await respx_stash_client.generate_api_key(input_data)

    assert result == new_api_key
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_generate_api_key_clear(respx_stash_client: StashClient) -> None:
    """Test clearing API key by setting clear=True."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("generateAPIKey", ""))
        ]
    )

    input_data = GenerateAPIKeyInput(clear=True)
    result = await respx_stash_client.generate_api_key(input_data)

    assert result == ""
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["input"]["clear"] is True


@pytest.mark.asyncio
@pytest.mark.unit
async def test_generate_api_key_error_raises(respx_stash_client: StashClient) -> None:
    """Test generate_api_key raises on error."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    with pytest.raises(StashGraphQLError, match="Server error"):
        await respx_stash_client.generate_api_key({})
