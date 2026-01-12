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
    AddTempDLNAIPInput,
    ConfigDefaultSettingsInput,
    ConfigDLNAInput,
    ConfigGeneralInput,
    ConfigInterfaceInput,
    ConfigScrapingInput,
    DisableDLNAInput,
    EnableDLNAInput,
    FilterMode,
    GenerateAPIKeyInput,
    RemoveTempDLNAIPInput,
    StashBoxInput,
)
from stash_graphql_client.types.unset import is_set
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
    # Add camelCase keys for non-protected fields
    config_data["parallelTasks"] = 8
    config_data["previewSegmentDuration"] = 5
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("configureGeneral", config_data)
            )
        ]
    )

    input_data = ConfigGeneralInput(parallel_tasks=8, preview_segment_duration=5)
    result = await respx_stash_client.configure_general(input_data)

    assert result is not None
    assert result.parallel_tasks == 8
    assert result.preview_segment_duration == 5
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
    assert is_set(result.whitelisted_ips)
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
    new_api_key = "sk-test-api-key-12345"  # nosec B105
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
    new_api_key = "sk-new-api-key-67890"  # nosec B105
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


# =============================================================================
# find_saved_filter tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_saved_filter_success(respx_stash_client: StashClient) -> None:
    """Test finding a saved filter by ID."""
    filter_data = {
        "id": "filter-123",
        "mode": "SCENES",
        "name": "My Saved Filter",
        "find_filter": {"q": "test"},
        "ui_options": {"displayModeFilter": "WALL"},
    }
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("findSavedFilter", filter_data)
            )
        ]
    )

    result = await respx_stash_client.find_saved_filter("filter-123")

    assert result is not None
    assert result.id == "filter-123"
    assert result.mode == "SCENES"
    assert result.name == "My Saved Filter"
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "findSavedFilter" in req["query"]
    assert req["variables"]["id"] == "filter-123"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_saved_filter_not_found(respx_stash_client: StashClient) -> None:
    """Test finding a saved filter that doesn't exist."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("findSavedFilter", None))
        ]
    )

    result = await respx_stash_client.find_saved_filter("nonexistent")

    assert result is None
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_saved_filter_error_returns_none(
    respx_stash_client: StashClient,
) -> None:
    """Test find_saved_filter returns None on error."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    result = await respx_stash_client.find_saved_filter("filter-123")

    assert result is None


# =============================================================================
# find_saved_filters tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_saved_filters_no_mode(respx_stash_client: StashClient) -> None:
    """Test finding all saved filters without mode filter."""
    filters_data = [
        {
            "id": "filter-1",
            "mode": "SCENES",
            "name": "Filter 1",
            "find_filter": {},
            "ui_options": {},
        },
        {
            "id": "filter-2",
            "mode": "IMAGES",
            "name": "Filter 2",
            "find_filter": {},
            "ui_options": {},
        },
    ]
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("findSavedFilters", filters_data)
            )
        ]
    )

    result = await respx_stash_client.find_saved_filters()

    assert len(result) == 2
    assert result[0].id == "filter-1"
    assert result[1].id == "filter-2"
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "findSavedFilters" in req["query"]
    assert req["variables"]["mode"] is None


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_saved_filters_with_mode(respx_stash_client: StashClient) -> None:
    """Test finding saved filters filtered by mode."""
    filters_data = [
        {
            "id": "filter-1",
            "mode": "SCENES",
            "name": "Scene Filter",
            "find_filter": {},
            "ui_options": {},
        }
    ]
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("findSavedFilters", filters_data)
            )
        ]
    )

    result = await respx_stash_client.find_saved_filters(mode=FilterMode.SCENES)

    assert len(result) == 1
    assert result[0].mode == "SCENES"
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["mode"] == "SCENES"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_saved_filters_error_returns_empty(
    respx_stash_client: StashClient,
) -> None:
    """Test find_saved_filters returns empty list on error."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    result = await respx_stash_client.find_saved_filters()

    assert result == []


# =============================================================================
# configure_scraping tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_configure_scraping_with_dict(respx_stash_client: StashClient) -> None:
    """Test configuring scraping settings with dict input."""
    config_data = {
        "scraperUserAgent": "CustomAgent/1.0",
        "scraperCertCheck": True,
        "scraperCDPPath": "/usr/bin/chromium",
        "excludeTagPatterns": ["exclude.*"],
    }
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("configureScraping", config_data)
            )
        ]
    )

    result = await respx_stash_client.configure_scraping(
        {"scraperUserAgent": "CustomAgent/1.0"}
    )

    assert result is not None
    assert result.scraper_user_agent == "CustomAgent/1.0"
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "configureScraping" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_configure_scraping_with_model(respx_stash_client: StashClient) -> None:
    """Test configuring scraping settings with ConfigScrapingInput model."""
    config_data = {
        "scraperUserAgent": "MyAgent/2.0",
        "scraperCertCheck": False,
        "scraperCDPPath": None,
        "excludeTagPatterns": [],
    }
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("configureScraping", config_data)
            )
        ]
    )

    input_data = ConfigScrapingInput(
        scraperUserAgent="MyAgent/2.0", scraperCertCheck=False
    )
    result = await respx_stash_client.configure_scraping(input_data)

    assert result is not None
    assert result.scraper_user_agent == "MyAgent/2.0"
    assert result.scraper_cert_check is False
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_configure_scraping_error_raises(respx_stash_client: StashClient) -> None:
    """Test configure_scraping raises on error."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    with pytest.raises(StashGraphQLError, match="Server error"):
        await respx_stash_client.configure_scraping({})


# =============================================================================
# validate_stashbox_credentials tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_validate_stashbox_credentials_with_dict(
    respx_stash_client: StashClient,
) -> None:
    """Test validating StashBox credentials with dict input."""
    validation_result = {"valid": True, "status": "Valid credentials"}
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "validateStashBoxCredentials", validation_result
                ),
            )
        ]
    )

    result = await respx_stash_client.validate_stashbox_credentials(
        {
            "endpoint": "https://stashdb.org/graphql",
            "api_key": "test-key",
            "name": "StashDB",
        }
    )

    assert result is not None
    assert result.valid is True
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "validateStashBoxCredentials" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_validate_stashbox_credentials_with_model(
    respx_stash_client: StashClient,
) -> None:
    """Test validating StashBox credentials with StashBoxInput model."""
    validation_result = {"valid": False, "status": "Invalid API key"}
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "validateStashBoxCredentials", validation_result
                ),
            )
        ]
    )

    input_data = StashBoxInput(
        endpoint="https://stashdb.org/graphql",
        api_key="invalid-key",
        name="StashDB",
    )
    result = await respx_stash_client.validate_stashbox_credentials(input_data)

    assert result is not None
    assert result.valid is False
    assert result.status == "Invalid API key"
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_validate_stashbox_credentials_error_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test validate_stashbox_credentials raises on error."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    with pytest.raises(StashGraphQLError, match="Server error"):
        await respx_stash_client.validate_stashbox_credentials(
            {
                "endpoint": "https://stashdb.org/graphql",
                "api_key": "test",
                "name": "StashDB",
            }
        )


# =============================================================================
# enable_dlna tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_enable_dlna_with_dict(respx_stash_client: StashClient) -> None:
    """Test enabling DLNA with dict input."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("enableDLNA", True))
        ]
    )

    result = await respx_stash_client.enable_dlna({})

    assert result is True
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "enableDLNA" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_enable_dlna_with_model(respx_stash_client: StashClient) -> None:
    """Test enabling DLNA with EnableDLNAInput model."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("enableDLNA", True))
        ]
    )

    input_data = EnableDLNAInput()
    result = await respx_stash_client.enable_dlna(input_data)

    assert result is True
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_enable_dlna_error_raises(respx_stash_client: StashClient) -> None:
    """Test enable_dlna raises on error."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    with pytest.raises(StashGraphQLError, match="Server error"):
        await respx_stash_client.enable_dlna({})


# =============================================================================
# disable_dlna tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_disable_dlna_with_dict(respx_stash_client: StashClient) -> None:
    """Test disabling DLNA with dict input."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("disableDLNA", True))
        ]
    )

    result = await respx_stash_client.disable_dlna({})

    assert result is True
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "disableDLNA" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_disable_dlna_with_model(respx_stash_client: StashClient) -> None:
    """Test disabling DLNA with DisableDLNAInput model."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("disableDLNA", True))
        ]
    )

    input_data = DisableDLNAInput()
    result = await respx_stash_client.disable_dlna(input_data)

    assert result is True
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_disable_dlna_error_raises(respx_stash_client: StashClient) -> None:
    """Test disable_dlna raises on error."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    with pytest.raises(StashGraphQLError, match="Server error"):
        await respx_stash_client.disable_dlna({})


# =============================================================================
# add_temp_dlna_ip tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_add_temp_dlna_ip_with_dict(respx_stash_client: StashClient) -> None:
    """Test adding temp DLNA IP with dict input."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("addTempDLNAIP", True))
        ]
    )

    result = await respx_stash_client.add_temp_dlna_ip(
        {"address": "192.168.1.100", "duration": 3600}
    )

    assert result is True
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "addTempDLNAIP" in req["query"]
    assert req["variables"]["input"]["address"] == "192.168.1.100"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_add_temp_dlna_ip_with_model(respx_stash_client: StashClient) -> None:
    """Test adding temp DLNA IP with AddTempDLNAIPInput model."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("addTempDLNAIP", True))
        ]
    )

    input_data = AddTempDLNAIPInput(address="10.0.0.5", duration=7200)
    result = await respx_stash_client.add_temp_dlna_ip(input_data)

    assert result is True
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_add_temp_dlna_ip_error_raises(respx_stash_client: StashClient) -> None:
    """Test add_temp_dlna_ip raises on error."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    with pytest.raises(StashGraphQLError, match="Server error"):
        await respx_stash_client.add_temp_dlna_ip(
            {"address": "192.168.1.100", "duration": 3600}
        )


# =============================================================================
# remove_temp_dlna_ip tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_remove_temp_dlna_ip_with_dict(respx_stash_client: StashClient) -> None:
    """Test removing temp DLNA IP with dict input."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("removeTempDLNAIP", True))
        ]
    )

    result = await respx_stash_client.remove_temp_dlna_ip({"address": "192.168.1.100"})

    assert result is True
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "removeTempDLNAIP" in req["query"]
    assert req["variables"]["input"]["address"] == "192.168.1.100"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_remove_temp_dlna_ip_with_model(respx_stash_client: StashClient) -> None:
    """Test removing temp DLNA IP with RemoveTempDLNAIPInput model."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("removeTempDLNAIP", True))
        ]
    )

    input_data = RemoveTempDLNAIPInput(address="10.0.0.5")
    result = await respx_stash_client.remove_temp_dlna_ip(input_data)

    assert result is True
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_remove_temp_dlna_ip_error_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test remove_temp_dlna_ip raises on error."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    with pytest.raises(StashGraphQLError, match="Server error"):
        await respx_stash_client.remove_temp_dlna_ip({"address": "192.168.1.100"})


# =============================================================================
# get_configuration tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_configuration(respx_stash_client: StashClient) -> None:
    """Test getting full configuration."""
    from tests.fixtures.stash.config_responses import create_config_result

    config_data = create_config_result()
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("configuration", config_data)
            )
        ]
    )

    result = await respx_stash_client.get_configuration()

    assert result is not None
    assert result.general is not None
    assert result.interface is not None
    assert result.dlna is not None
    assert result.scraping is not None
    assert result.defaults is not None
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "configuration" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_configuration_error_raises(respx_stash_client: StashClient) -> None:
    """Test get_configuration raises on error."""
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    with pytest.raises(StashGraphQLError, match="Server error"):
        await respx_stash_client.get_configuration()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_configuration_calls_itself_a_teapot(
    respx_stash_client: StashClient,
) -> None:
    """Test get_configuration when server identifies as a teapot (RFC 2324/HTCPCP).

    While Stash is definitely not a coffee pot, we should handle this status
    gracefully in case someone's running Stash on IoT coffee pot hardware. ☕
    """
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                418,
                json={"error": "I'm a teapot"},
                headers={"Content-Type": "application/tea+json"},
            )
        ]
    )

    # Teapots can't serve GraphQL, so we expect an error
    with pytest.raises(
        Exception, match=r"I'm a teapot"
    ):  # Will raise transport/HTTP error
        await respx_stash_client.get_configuration()
