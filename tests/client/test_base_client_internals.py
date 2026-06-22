"""Unit tests for StashClient internals, connection config, and initialize().

Split from test_base_client.py for size. Covers:
- execute()/_decode helpers, _parse_obj_for_ID, _normalize_sort_direction,
  _convert_datetime, close()/__aexit__ internals (respx_stash_client)
- WebSocket ws:// vs wss:// SSL config, port/scheme/verify_ssl validation
- initialize() idempotency and _raw_execute() guards
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import respx
from gql import Client

from stash_graphql_client import StashClient
from stash_graphql_client.client.base import StashClientBase
from stash_graphql_client.context import StashContext
from stash_graphql_client.errors import StashError
from stash_graphql_client.types import Studio
from stash_graphql_client.types.enums import SortDirectionEnum
from stash_graphql_client.types.unset import UNSET
from tests.fixtures import dump_graphql_calls


# =============================================================================
# Additional coverage for missing branches
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_execute_with_invalid_graphql_syntax_error(respx_stash_client) -> None:
    """Test execute handles invalid GraphQL syntax."""

    # Invalid GraphQL - missing closing brace
    invalid_query = 'query { findScene(id: "123") { id'

    with pytest.raises(StashError, match=r"Unexpected error.*ValueError"):
        await respx_stash_client.execute(invalid_query, {})


@pytest.mark.asyncio
@pytest.mark.unit
async def test_execute_without_initialized_session(respx_stash_client) -> None:
    """Test execute raises RuntimeError when session not initialized."""
    # Force _session to None to test the session check
    respx_stash_client._session = None

    with pytest.raises(RuntimeError, match="GQL session not initialized"):
        await respx_stash_client.execute("query { version { version } }", {})


@pytest.mark.asyncio
@pytest.mark.unit
async def test_convert_datetime_with_unset(respx_stash_client) -> None:
    """Test _convert_datetime returns None for UNSET values."""
    result = respx_stash_client._convert_datetime(UNSET)
    assert result is None


@pytest.mark.asyncio
@pytest.mark.unit
async def test_convert_datetime_with_datetime(respx_stash_client) -> None:
    """Test _convert_datetime converts datetime to ISO format."""
    dt = datetime(2024, 6, 15, 14, 30, 0, tzinfo=UTC)
    result = respx_stash_client._convert_datetime(dt)
    assert result == "2024-06-15T14:30:00+00:00"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_parse_obj_for_id_with_non_numeric_string(respx_stash_client) -> None:
    """Test _parse_obj_for_ID with non-numeric string."""
    result = respx_stash_client._parse_obj_for_ID("not-a-number")
    assert result == {"name": "not-a-number"}


@pytest.mark.asyncio
@pytest.mark.unit
async def test_parse_obj_for_id_with_dict_having_stored_id(respx_stash_client) -> None:
    """Test _parse_obj_for_ID with dict containing stored_id."""
    result = respx_stash_client._parse_obj_for_ID({"stored_id": "789"})
    assert result == 789


@pytest.mark.asyncio
@pytest.mark.unit
async def test_parse_obj_for_id_with_dict_having_id(respx_stash_client) -> None:
    """Test _parse_obj_for_ID with dict containing id."""
    result = respx_stash_client._parse_obj_for_ID({"id": "456"})
    assert result == 456


@pytest.mark.asyncio
@pytest.mark.unit
async def test_parse_obj_for_id_with_negative_string_raises(
    respx_stash_client,
) -> None:
    """Test _parse_obj_for_ID raises on non-positive string IDs."""
    with pytest.raises(ValueError, match="ID must be positive"):
        respx_stash_client._parse_obj_for_ID("-1")


@pytest.mark.asyncio
@pytest.mark.unit
async def test_parse_obj_for_id_with_invalid_dict_value_raises(
    respx_stash_client,
) -> None:
    """Test _parse_obj_for_ID raises on non-numeric dict values."""
    with pytest.raises(ValueError, match="Invalid id"):
        respx_stash_client._parse_obj_for_ID({"id": "not-a-number"})


@pytest.mark.asyncio
@pytest.mark.unit
async def test_parse_obj_for_id_with_non_positive_dict_value_raises(
    respx_stash_client,
) -> None:
    """Test _parse_obj_for_ID raises on non-positive dict IDs."""
    with pytest.raises(ValueError, match="id must be positive"):
        respx_stash_client._parse_obj_for_ID({"id": 0})


@pytest.mark.asyncio
@pytest.mark.unit
async def test_normalize_sort_direction_with_enum(respx_stash_client) -> None:
    """Test _normalize_sort_direction converts enum to string."""
    result = respx_stash_client._normalize_sort_direction(
        {"direction": SortDirectionEnum.ASC, "page": 1}
    )
    assert result["direction"] == "ASC"
    assert result["page"] == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_normalize_sort_direction_none_returns_filter(
    respx_stash_client,
) -> None:
    """Test _normalize_sort_direction returns filter when direction is None."""
    filter_ = {"direction": None, "page": 1}
    result = respx_stash_client._normalize_sort_direction(filter_)
    assert result is filter_


@pytest.mark.asyncio
@pytest.mark.unit
async def test_normalize_sort_direction_invalid_type_raises(
    respx_stash_client,
) -> None:
    """Test _normalize_sort_direction rejects non-str/non-enum values."""
    with pytest.raises(TypeError, match="direction must be SortDirectionEnum or str"):
        respx_stash_client._normalize_sort_direction({"direction": 123})


@pytest.mark.asyncio
@pytest.mark.unit
async def test_normalize_sort_direction_invalid_string_raises(
    respx_stash_client,
) -> None:
    """Test _normalize_sort_direction rejects invalid string values."""
    with pytest.raises(ValueError, match="direction must be 'ASC' or 'DESC'"):
        respx_stash_client._normalize_sort_direction({"direction": "DOWN"})


@pytest.mark.asyncio
@pytest.mark.unit
async def test_context_manager_exit_calls_close(respx_stash_client) -> None:
    """Test __aexit__ calls close() method."""
    # Patch close to verify it's called
    with patch.object(
        respx_stash_client, "close", new_callable=AsyncMock
    ) as mock_close:
        async with respx_stash_client:
            pass

        # Verify close was called during __aexit__
        mock_close.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_close_handles_client_close_async_error(respx_stash_client) -> None:
    """Test close() handles client.close_async errors gracefully."""
    # Create a mock client with close_async that raises
    mock_client = MagicMock()
    mock_client.close_async = AsyncMock(side_effect=Exception("Close error"))

    with patch.object(respx_stash_client, "client", mock_client):
        # Should not propagate the exception
        await respx_stash_client.close()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_close_with_transports_present(respx_stash_client) -> None:
    """Test close() closes http and ws transports."""
    # Mock transports
    mock_http = AsyncMock()
    mock_http.close = AsyncMock()
    mock_ws = AsyncMock()
    mock_ws.close = AsyncMock()

    with (
        patch.object(respx_stash_client, "http_transport", mock_http),
        patch.object(respx_stash_client, "ws_transport", mock_ws),
    ):
        await respx_stash_client.close()

        # Verify both transports were closed
        mock_http.close.assert_called_once()
        mock_ws.close.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_execute_with_list_type_but_non_list_data(respx_stash_client) -> None:
    """Test execute with list[Type] but GraphQL returns non-list data - hits line 426."""
    # Mock GraphQL response with a string instead of a list
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json={"data": {"someQuery": "not-a-list-string"}})
        ]
    )

    # Call execute with list[Studio] but data is not a list
    # This triggers the fallback at line 426: return field_data
    try:
        result = await respx_stash_client.execute(
            "query { someQuery }",
            {},
            result_type=list[Studio],  # Expects list but data is a string
        )
    finally:
        dump_graphql_calls(graphql_route.calls)

    # Should return field_data as-is when it's not a list
    assert result == "not-a-list-string"
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_execute_with_bare_list_result_type_raises_error(
    respx_stash_client,
) -> None:
    """Test execute with bare list type raises error when hitting model_validate - covers line 432."""

    # Mock GraphQL response
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(200, json={"data": {"someQuery": "string-value"}})]
    )

    # Bare list doesn't have model_validate, so this will hit line 432 and raise
    try:
        with pytest.raises(
            StashError, match="type object 'list' has no attribute 'model_validate'"
        ):
            await respx_stash_client.execute(
                "query { someQuery }", {}, result_type=list
            )
    finally:
        dump_graphql_calls(graphql_route.calls)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_execute_with_unexpected_response_structure_raises_error(
    respx_stash_client,
) -> None:
    """Test execute with unexpected response structure triggers fallback and fails - hits lines 441-444."""
    # Mock GraphQL response with unexpected structure (multiple root keys)
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json={"data": {"query1": {"id": "1"}, "query2": {"id": "2"}}}
            )
        ]
    )

    # The fallback path tries to iterate over result_dict items as if they're Studios
    # This will fail because the dict keys are strings, not Studio data
    try:
        with pytest.raises(StashError, match="Unexpected error"):
            await respx_stash_client.execute(
                "query { query1 { id } query2 { id } }", {}, result_type=list[Studio]
            )
    finally:
        dump_graphql_calls(graphql_route.calls)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_execute_fallback_with_typing_list_no_params(respx_stash_client) -> None:
    """Test fallback with typing.List (no type params) - hits branch 442->452."""

    # Mock response with unexpected multi-key structure to trigger fallback
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json={"data": {"key1": "val1", "key2": "val2"}})
        ]
    )

    # typing.List without params: origin is list but args is empty
    # Hits true at 440, false at 442, skips to 452
    try:
        with pytest.raises(StashError, match="type object 'list' has no attribute"):
            await respx_stash_client.execute(
                "query { key1 key2 }",
                {},
                result_type=list,  # typing.List without type parameter
            )
    finally:
        dump_graphql_calls(graphql_route.calls)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_parse_obj_for_id_with_non_string_non_dict(respx_stash_client) -> None:
    """Test _parse_obj_for_ID with param that's neither string nor dict - hits branch 484->489."""
    # Pass an int - not a string, not a dict, so skips both if/elif
    result = respx_stash_client._parse_obj_for_ID(123)

    # Should return param unchanged
    assert result == 123


@pytest.mark.asyncio
@pytest.mark.unit
async def test_close_skips_client_when_client_is_falsy(respx_stash_client) -> None:
    """Test close() skips client closing when client is falsy - hits branch 517->531."""
    # Set client to False to make the condition at line 517 False
    respx_stash_client.client = False

    # Also set gql_client and gql_ws_client to None so cleanup doesn't call close_async
    respx_stash_client.gql_client = None
    respx_stash_client.gql_ws_client = None

    # Track if close_async was called
    call_count = 0

    async def wrapper(*args, **kwargs):
        nonlocal call_count
        call_count += 1

    # Patch Client.close_async to track calls
    with patch.object(
        Client, "close_async", new_callable=AsyncMock, side_effect=wrapper
    ):
        await respx_stash_client.close()

    # Verify close_async was never called since client was falsy
    assert call_count == 0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_close_skips_transports_when_falsy(respx_stash_client) -> None:
    """Test close() skips both transports when falsy - hits branches 531->535 and 535->539."""
    # Set client and transports to None to skip all closing blocks
    respx_stash_client.client = None
    respx_stash_client.http_transport = None
    respx_stash_client.ws_transport = None
    respx_stash_client.gql_client = None
    respx_stash_client.gql_ws_client = None

    # Track if cleanup was called
    cleanup_called = False

    async def spy_cleanup():
        nonlocal cleanup_called
        cleanup_called = True

    # Spy on _cleanup_connection_resources to verify it's still called
    with patch.object(
        respx_stash_client, "_cleanup_connection_resources", side_effect=spy_cleanup
    ):
        await respx_stash_client.close()

    # Verify cleanup was called even though client and transports were skipped
    assert cleanup_called


@pytest.mark.asyncio
@pytest.mark.unit
async def test_aenter_initializes_when_not_initialized() -> None:
    """Test __aenter__ calls initialize() when not initialized - hits line 548."""
    # Create client without initializing, verify_ssl=False to avoid connection errors
    client = StashClient({"Host": "localhost", "Port": 9999}, verify_ssl=False)
    assert not client._initialized

    # Spy on initialize - let it run but track the call
    original_initialize = client.initialize
    init_called = False

    async def spy_initialize():
        nonlocal init_called
        init_called = True
        await original_initialize()  # Actually run the real initialize

    with patch.object(client, "initialize", side_effect=spy_initialize):
        async with client:
            pass

    # Verify initialize was called and client is now initialized
    assert init_called
    assert client._initialized


# =============================================================================
# WebSocket SSL Configuration Tests (Bug Fix for ws:// vs wss://)
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_http_websocket_does_not_pass_ssl_parameter(
    mock_ws_transport, mock_gql_ws_connect, respx_mock
) -> None:
    """Test that HTTP (ws://) connections do NOT pass ssl parameter to WebsocketsTransport.

    This covers the bug fix in lines 169-185 in client/base.py:
    - For HTTP connections (scheme="http"), ws_url uses "ws://" scheme
    - The ssl parameter MUST NOT be passed to WebsocketsTransport for ws:// URLs
    - The websockets library (v15.0.1+) raises ValueError if ssl is passed for ws://

    Bug Context:
    - Before fix: Always passed ssl=verify_ssl (even for ws://)
    - After fix: Only pass ssl parameter for wss:// URLs

    See: https://websockets.readthedocs.io/en/stable/howto/encryption.html
    """
    # Create context with HTTP scheme (should use ws:// for WebSocket)
    context = StashContext(
        conn={
            "Scheme": "http",  # HTTP → ws:// WebSocket
            "Host": "localhost",
            "Port": 9999,
        },
        verify_ssl=False,
    )

    client = await context.get_client()

    # Verify WebSocket URL uses ws:// scheme
    assert client.ws_url == "ws://localhost:9999/graphql"

    # Verify WebsocketsTransport was called WITHOUT ssl parameter
    assert mock_ws_transport.called
    call_kwargs = mock_ws_transport.call_args.kwargs

    # CRITICAL: ssl parameter MUST NOT be present for ws:// URLs
    assert "ssl" not in call_kwargs, (
        "ssl parameter should NOT be passed for ws:// URLs - "
        "this causes ValueError in websockets library"
    )

    # Verify other parameters are correctly passed
    assert call_kwargs["url"] == "ws://localhost:9999/graphql"
    assert call_kwargs["headers"] is not None
    assert "max_size" in call_kwargs["connect_args"]

    await context.close()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_https_websocket_passes_ssl_parameter(
    mock_ws_transport, mock_gql_ws_connect, respx_mock
) -> None:
    """Test that HTTPS (wss://) connections DO pass ssl parameter to WebsocketsTransport.

    This covers the bug fix in lines 169-185 in client/base.py:
    - For HTTPS connections (scheme="https"), ws_url uses "wss://" scheme
    - The ssl parameter MUST be passed to WebsocketsTransport for wss:// URLs
    - The ssl parameter enables SSL certificate validation

    Bug Context:
    - Before fix: Always passed ssl=verify_ssl (correct for HTTPS)
    - After fix: Only pass ssl parameter for wss:// URLs (same behavior preserved)
    """
    # Create context with HTTPS scheme (should use wss:// for WebSocket)
    context = StashContext(
        conn={
            "Scheme": "https",  # HTTPS → wss:// WebSocket
            "Host": "localhost",
            "Port": 9999,
        },
        verify_ssl=True,  # Enable SSL verification
    )

    client = await context.get_client()

    # Verify WebSocket URL uses wss:// scheme
    assert client.ws_url == "wss://localhost:9999/graphql"

    # Verify WebsocketsTransport was called WITH ssl parameter
    assert mock_ws_transport.called
    call_kwargs = mock_ws_transport.call_args.kwargs

    # CRITICAL: ssl parameter MUST be present for wss:// URLs
    assert "ssl" in call_kwargs, "ssl parameter is required for wss:// URLs"
    assert call_kwargs["ssl"] is True  # verify_ssl=True

    # Verify other parameters are correctly passed
    assert call_kwargs["url"] == "wss://localhost:9999/graphql"
    assert call_kwargs["headers"] is not None
    assert "max_size" in call_kwargs["connect_args"]

    await context.close()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_https_websocket_with_verify_ssl_false(
    mock_ws_transport, mock_gql_ws_connect, respx_mock
) -> None:
    """Test that HTTPS with verify_ssl=False still passes ssl parameter.

    This covers the bug fix in lines 169-185 in client/base.py:
    - For HTTPS connections with verify_ssl=False (self-signed certs)
    - The ssl parameter is still passed, but set to False
    - This allows connections to servers with self-signed certificates
    """
    # Create context with HTTPS scheme but SSL verification disabled
    context = StashContext(
        conn={
            "Scheme": "https",  # HTTPS → wss:// WebSocket
            "Host": "localhost",
            "Port": 9999,
        },
        verify_ssl=False,  # Disable SSL verification (self-signed certs)
    )

    client = await context.get_client()

    # Verify WebSocket URL uses wss:// scheme
    assert client.ws_url == "wss://localhost:9999/graphql"

    # Verify WebsocketsTransport was called WITH ssl=False
    assert mock_ws_transport.called
    call_kwargs = mock_ws_transport.call_args.kwargs

    # CRITICAL: ssl parameter MUST be present for wss:// URLs
    assert "ssl" in call_kwargs, "ssl parameter is required for wss:// URLs"
    assert call_kwargs["ssl"] is False  # verify_ssl=False

    await context.close()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scheme_attribute_stored_during_init(
    mock_ws_transport, mock_gql_ws_connect, respx_mock
) -> None:
    """Test that client stores scheme as instance attribute during initialization.

    This verifies line 132 in client/base.py:
    - self.scheme = conn.get("Scheme", "http")

    The scheme is now stored as an instance attribute so it can be used
    when configuring WebSocket transport.
    """
    # Test with HTTP
    context_http = StashContext(
        conn={"Scheme": "http", "Host": "localhost", "Port": 9999},
        verify_ssl=False,
    )

    client_http = await context_http.get_client()
    assert client_http.scheme == "http"
    await context_http.close()

    # Test with HTTPS
    context_https = StashContext(
        conn={"Scheme": "https", "Host": "localhost", "Port": 9999},
        verify_ssl=True,
    )

    client_https = await context_https.get_client()
    assert client_https.scheme == "https"
    await context_https.close()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_port_string_converted_to_int(
    mock_ws_transport, mock_gql_ws_connect, respx_mock
) -> None:
    """Test that port parameter as string is converted to int."""
    context = StashContext(
        conn={"Host": "localhost", "Port": "9999"},  # Port as string
        verify_ssl=False,
    )

    client = await context.get_client()
    # URL should have int port
    assert client.url == "http://localhost:9999/graphql"
    await context.close()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_port_int_works_normally(
    mock_ws_transport, mock_gql_ws_connect, respx_mock
) -> None:
    """Test that port parameter as int works normally."""
    context = StashContext(
        conn={"Host": "localhost", "Port": 8080},  # Port as int
        verify_ssl=False,
    )

    client = await context.get_client()
    assert client.url == "http://localhost:8080/graphql"
    await context.close()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_port_invalid_string_raises_typeerror() -> None:
    """Test that invalid port string raises TypeError."""

    client = StashClientBase(
        conn={"Host": "localhost", "Port": "invalid"},
        verify_ssl=False,
    )

    with pytest.raises(TypeError, match="Port must be an int or numeric string"):
        await client.initialize()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_port_out_of_range_raises_valueerror() -> None:
    """Test that port out of valid range raises ValueError."""

    client_negative = StashClientBase(
        conn={"Host": "localhost", "Port": -1},
        verify_ssl=False,
    )

    with pytest.raises(ValueError, match="Port must be 0-65535"):
        await client_negative.initialize()

    # Test port > 65535
    client_large = StashClientBase(
        conn={"Host": "localhost", "Port": 99999},
        verify_ssl=False,
    )

    with pytest.raises(ValueError, match="Port must be 0-65535"):
        await client_large.initialize()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_port_edge_cases_valid(
    mock_ws_transport, mock_gql_ws_connect, respx_mock
) -> None:
    """Test that port edge cases (0, 65535) are valid."""
    # Port 0 (let OS assign)
    context_zero = StashContext(
        conn={"Host": "localhost", "Port": 0},
        verify_ssl=False,
    )

    client_zero = await context_zero.get_client()
    assert client_zero.url == "http://localhost:0/graphql"
    await context_zero.close()

    # Port 65535 (max valid)
    context_max = StashContext(
        conn={"Host": "localhost", "Port": 65535},
        verify_ssl=False,
    )

    client_max = await context_max.get_client()
    assert client_max.url == "http://localhost:65535/graphql"
    await context_max.close()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_verify_ssl_string_variants(
    mock_ws_transport, mock_gql_ws_connect, respx_mock
) -> None:
    """Test that verify_ssl accepts various string representations of true/false."""
    # Test "true" string
    context_true = StashContext(
        conn={"Host": "localhost", "Port": 9999, "Scheme": "https"},
        verify_ssl="true",
    )
    client = await context_true.get_client()
    # Should be converted to True
    assert client.transport_config["ssl"] is True
    await context_true.close()

    # Test "1" string
    context_one = StashContext(
        conn={"Host": "localhost", "Port": 9999, "Scheme": "https"},
        verify_ssl="1",
    )
    client = await context_one.get_client()
    assert client.transport_config["ssl"] is True
    await context_one.close()

    # Test "yes" string
    context_yes = StashContext(
        conn={"Host": "localhost", "Port": 9999, "Scheme": "https"},
        verify_ssl="yes",
    )
    client = await context_yes.get_client()
    assert client.transport_config["ssl"] is True
    await context_yes.close()

    # Test "false" string (should be False)
    context_false = StashContext(
        conn={"Host": "localhost", "Port": 9999},
        verify_ssl="false",
    )
    client = await context_false.get_client()
    assert client.transport_config["ssl"] is False
    await context_false.close()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_verify_ssl_invalid_type_raises_typeerror() -> None:
    """Test that verify_ssl rejects non-bool, non-string types."""
    context = StashContext(
        conn={"Host": "localhost", "Port": 9999},
        verify_ssl=123,  # type: ignore[arg-type]
    )

    with pytest.raises(RuntimeError, match="verify_ssl must be bool or string"):
        await context.get_client()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_stash_client_verify_ssl_string_conversion(respx_mock) -> None:
    """Test StashClient directly handles string verify_ssl values.

    This test covers the string-to-bool conversion in StashClient.initialize() (base.py:130-131).
    The conversion happens during initialize(), not __init__.
    """
    # Mock the GraphQL endpoint (capability detection happens during initialize)
    graphql_route = respx_mock.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "data": {
                        "version": {"version": "v0.30.0"},
                        "systemStatus": {"appSchema": 75, "status": "OK"},
                        "_dup": None,
                    }
                },
            ),
            httpx.Response(
                200,
                json={
                    "data": {
                        "version": {"version": "v0.30.0"},
                        "systemStatus": {"appSchema": 75, "status": "OK"},
                        "_dup": None,
                    }
                },
            ),
        ]
    )

    # Test "false" string - ensures the False branch of line 131 is covered
    client_false = StashClient(
        conn={"Host": "localhost", "Port": 9999},
        verify_ssl="false",  # type: ignore[arg-type]
    )
    try:
        await client_false.initialize()  # This is where the conversion happens
        # Test "true" string - ensures the True branch is also covered
        client_true = StashClient(
            conn={"Host": "localhost", "Port": 9999},
            verify_ssl="true",  # type: ignore[arg-type]
        )
        await client_true.initialize()  # This is where the conversion happens
    finally:
        dump_graphql_calls(graphql_route.calls)
    assert client_false._initialized  # Verify initialization completed
    assert client_true._initialized  # Verify initialization completed


@pytest.mark.asyncio
@pytest.mark.unit
async def test_invalid_scheme_raises_valueerror() -> None:
    """Test that invalid scheme raises ValueError."""
    context = StashContext(
        conn={"Host": "localhost", "Port": 9999, "Scheme": "ftp"},
        verify_ssl=False,
    )

    with pytest.raises(RuntimeError, match="Scheme must be 'http' or 'https'"):
        await context.get_client()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_port_negative_raises_valueerror() -> None:
    """Test that negative port raises ValueError."""
    context = StashContext(
        conn={"Host": "localhost", "Port": -1},
        verify_ssl=False,
    )

    with pytest.raises(ValueError, match="Port must be 0-65535"):
        await context.get_client()


# =============================================================================
# initialize() idempotency and _raw_execute() guard tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_base_initialize_is_idempotent(
    mock_ws_transport, mock_gql_ws_connect
) -> None:
    """Calling StashClientBase.initialize() twice is a no-op the second time (covers base.py L124).

    StashClient overrides initialize() with its own early-return guard,
    so we call through the base class explicitly to hit L124 in base.py.
    """
    context = StashContext(
        conn={"Host": "localhost", "Port": 9999},
        verify_ssl=False,
    )
    client = await context.get_client()
    try:
        assert client._initialized

        # Call the *base class* initialize() directly — should early-return at L124
        await StashClientBase.initialize(client)

        # Still initialized, no error
        assert client._initialized
    finally:
        await client.close()
        await context.close()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_raw_execute_no_session_raises() -> None:
    """_raw_execute() raises RuntimeError when session is not connected (covers L285).

    _session is set to None during initialize() at L217 and only becomes
    truthy after connect_async succeeds at L255.  We simulate the "session
    not yet connected" state by setting the attribute directly.
    """
    client = StashClient({"Host": "localhost", "Port": 9999}, verify_ssl=False)
    # Simulate the state after L217 but before L255 (session created but not connected)
    client._session = None

    with pytest.raises(RuntimeError, match="GQL session not available"):
        await client._raw_execute("{ version { version } }")


@pytest.mark.asyncio
@pytest.mark.unit
async def test_raw_execute_with_variables(
    mock_ws_transport, mock_gql_ws_connect
) -> None:
    """_raw_execute() sets operation.variable_values when variables are provided (covers L291)."""
    context = StashContext(
        conn={"Host": "localhost", "Port": 9999},
        verify_ssl=False,
    )
    client = await context.get_client()
    try:
        variables = {"id": "123"}
        result = await client._raw_execute(
            "query FindScene($id: ID!) { findScene(id: $id) { id } }",
            variables=variables,
        )
        # The mock session returns the capability response for any execute call,
        # but the important thing is that it didn't raise
        assert isinstance(result, dict)
    finally:
        await client.close()
        await context.close()
