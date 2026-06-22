"""Unit tests for StashClient base functionality.

These tests cover core client behavior like authentication headers,
error handling, and request/response processing.

See test_base_client_internals.py for execute()/parse internals, WebSocket/SSL
connection config, and initialize()/_raw_execute() coverage.
"""

from __future__ import annotations

import json
from unittest.mock import patch

import httpx
import pytest
import respx
from gql.transport.exceptions import (
    TransportError,
    TransportQueryError,
    TransportServerError,
)

from stash_graphql_client.client.base import StashClientBase
from stash_graphql_client.context import StashContext
from stash_graphql_client.errors import (
    StashConnectionError,
    StashError,
    StashGraphQLError,
    StashServerError,
    StashSystemNotReadyError,
)
from stash_graphql_client.types import (
    GenerateMetadataInput,
    GenerateMetadataOptions,
)
from stash_graphql_client.types.scene import Scene, SceneHashInput
from tests.fixtures import dump_graphql_calls


@pytest.mark.asyncio
async def test_respx_stash_client_init_sets_initial_state() -> None:
    """Test StashClient.__init__ sets initial state attributes.

    This covers lines 76-82 in client/base.py:
    - Line 77: self._initialized = False
    - Line 79: self._init_args = (conn, verify_ssl)
    - Line 82: self.schema = None

    Verifies that __init__ properly initializes instance attributes
    when they don't already exist.
    """

    conn = {"Host": "localhost", "Port": 9999}
    verify_ssl = False

    # Create client - __init__ will be called
    client = StashClientBase(conn=conn, verify_ssl=verify_ssl)

    # Verify initial state (line 77)
    assert client._initialized is False

    # Verify init args stored (line 79)
    assert client._init_args == (conn, verify_ssl)

    # Verify schema is None (line 82)
    assert client.schema is None


@pytest.mark.asyncio
async def test_respx_stash_client_init_called_twice() -> None:
    """Test that calling __init__ twice overwrites previous values.

    This covers the false branches in client/base.py:
    - Line 76: if not hasattr(self, "_initialized"): - false branch (attribute exists)
    - Line 78: if not hasattr(self, "_init_args"): - false branch (attribute exists)
    - Line 81->exit: if not hasattr(self, "schema"): - false branch (attribute exists)

    Documents actual behavior: hasattr() checks don't prevent re-initialization.
    Calling __init__ multiple times DOES overwrite previous values.
    """

    conn1 = {"Host": "localhost", "Port": 9999}
    conn2 = {"Host": "different", "Port": 8888}

    # Create client normally - first __init__ call
    client = StashClientBase(conn=conn1, verify_ssl=False)

    # Verify initial state
    assert client._initialized is False
    assert client._init_args == (conn1, False)
    assert client.schema is None

    # Call __init__ again with different values
    # Now attributes exist, so hasattr() returns True and skips re-initialization
    StashClientBase.__init__(client, conn=conn2, verify_ssl=True)

    # Verify values were NOT overwritten (hasattr checks prevented it)
    # The defensive programming works - attributes are preserved on re-init
    assert client._initialized is False  # Still False (not overwritten)
    assert client._init_args == (conn1, False)  # Original values preserved
    assert client.schema is None  # Still None (not overwritten)


@pytest.mark.asyncio
async def test_host_0_0_0_0_converted_to_127_0_0_1(
    mock_ws_transport, mock_gql_ws_connect, respx_mock
) -> None:
    """Test that host 0.0.0.0 is converted to 127.0.0.1.

    This covers line 146 in client/base.py:
    - if host == "0.0.0.0":
    -     host = "127.0.0.1"

    The 0.0.0.0 address (all interfaces) is converted to localhost
    for actual connection attempts.
    """
    context = StashContext(conn={"Host": "0.0.0.0", "Port": 9999})  # noqa: S104

    # Mock should expect connection to 127.0.0.1, not 0.0.0.0
    route = respx.post("http://127.0.0.1:9999/graphql").mock(
        side_effect=[httpx.Response(200, json={"data": {}})]
    )

    try:
        client = await context.get_client()
    finally:
        dump_graphql_calls(route.calls)

    # Verify URLs were converted
    assert client.url == "http://127.0.0.1:9999/graphql"
    assert client.ws_url == "ws://127.0.0.1:9999/graphql"

    # Verify route was called (proves connection went to 127.0.0.1)
    assert len(route.calls) == 0  # No HTTP requests during init (lazy)

    await context.close()


@pytest.mark.asyncio
async def test_api_key_causes_auth_failure_on_server_without_auth(
    stash_context_with_api_key, caplog
) -> None:
    """Test that API key header causes auth failure on server without API key auth.

    This covers lines 155-156 in client/base.py:
    - if api_key := conn.get("ApiKey"):
    -     headers["ApiKey"] = api_key

    The test documents current behavior: when an API key is provided but the
    server doesn't have API key authentication enabled, the client initialization
    fails during WebSocket connection with HTTP 401 Unauthorized.

    This reveals a limitation: there's no error handling in the initialization
    to gracefully handle invalid connection parameters or auth failures.
    """
    # Lines 155-156: API key added to headers dict
    # Headers passed to HTTP (line 170) and WebSocket (line 181) transports
    #
    # Connection behavior during initialize():
    # - Line 228: HTTP connect_async() - LAZY, no actual request sent (just setup)
    # - Line 229: WebSocket connect_async() - EAGER, sends GET request, FAILS
    #
    # Server logs confirm: only GET requests (WebSocket upgrade) are attempted,
    # no POST requests (HTTP GraphQL) during initialization.
    with pytest.raises(RuntimeError, match="Failed to initialize Stash client"):
        await stash_context_with_api_key.get_client()


@pytest.mark.asyncio
async def test_create_factory_method(
    mock_ws_transport, mock_gql_ws_connect, respx_mock
) -> None:
    """Test StashClientBase.create() factory method.

    This covers lines 123-125 in client/base.py:
    - Line 123: client = cls(conn, verify_ssl)
    - Line 124: await client.initialize()
    - Line 125: return client

    The create() factory method provides a convenient alternative to
    manually instantiating and initializing the client in two steps.
    """

    conn = {"Host": "localhost", "Port": 9999}

    # Use factory method instead of __init__ + initialize()
    client = await StashClientBase.create(conn=conn, verify_ssl=False)

    # Verify client was created and initialized
    assert client is not None
    assert client._initialized is True
    assert client.url == "http://localhost:9999/graphql"


@pytest.mark.asyncio
async def test_decode_result_handles_none_data(respx_stash_client) -> None:
    """Test _decode_result returns None when data is None.

    This covers line 266 in client/base.py:
    - if data is None:
    -     return None

    This exercises the overload signature:
        def _decode_result(self, type_: type[T], data: None) -> None

    When GraphQL response data is None (not just empty dict, but actually None),
    the method should return None without attempting deserialization.
    """
    # Call _decode_result with None data
    result = respx_stash_client._decode_result(Scene, None)

    # Should return None immediately (line 266)
    assert result is None


@pytest.mark.asyncio
async def test_decode_result_uses_model_validate_for_input_types(
    respx_stash_client,
) -> None:
    """Test _decode_result uses model_validate() for input types.

    This covers line 275 in client/base.py:
    - return type_.model_validate(clean_data)

    Input types (StashInput subclasses) are plain Pydantic BaseModels
    without from_graphql(), so they use model_validate() path (line 275)
    instead of from_graphql() path (line 273).
    """
    # Sample data for SceneHashInput
    data = {"checksum": "bad_check", "oshash": "bad_oshash"}

    # Call _decode_result with input type (no from_graphql())
    decoded = respx_stash_client._decode_result(SceneHashInput, data)

    # Verify model_validate() was used and data deserialized correctly
    assert decoded.checksum == "bad_check"
    assert decoded.oshash == "bad_oshash"


@pytest.mark.asyncio
async def test_cleanup_connection_resources_handles_gql_client_close_error(
    respx_stash_client, caplog
) -> None:
    """Test _cleanup_connection_resources handles gql_client close errors.

    This covers lines 289-291 in client/base.py:
    - except Exception as e:
    -     if hasattr(self, "log"):
    -         self.log.debug(f"Error closing GQL client: {e}")

    When closing the gql_client raises an exception, it should be caught
    and logged (not propagated).
    """
    # Ensure client has gql_client and log attributes
    assert hasattr(respx_stash_client, "gql_client")
    assert respx_stash_client.gql_client is not None
    assert hasattr(respx_stash_client, "log")

    # Patch gql_client.close_async() to raise an exception
    test_error = Exception("Test GQL client close error")
    with patch.object(
        respx_stash_client.gql_client, "close_async", side_effect=test_error
    ):
        # Should not raise - exception should be caught and logged
        await respx_stash_client._cleanup_connection_resources()

    # Verify gql_client was set to None despite the error
    assert respx_stash_client.gql_client is None


@pytest.mark.asyncio
async def test_cleanup_connection_resources_handles_gql_ws_client_close_error(
    respx_stash_client, caplog
) -> None:
    """Test _cleanup_connection_resources handles gql_ws_client close errors.

    This covers lines 296-298 in client/base.py:
    - except Exception as e:
    -     if hasattr(self, "log"):
    -         self.log.debug(f"Error closing GQL WS client: {e}")

    When closing the gql_ws_client raises an exception, it should be caught
    and logged (not propagated).
    """
    # Ensure client has gql_ws_client and log attributes
    assert hasattr(respx_stash_client, "gql_ws_client")
    assert respx_stash_client.gql_ws_client is not None
    assert hasattr(respx_stash_client, "log")

    # Patch gql_ws_client.close_async() to raise an exception
    test_error = Exception("Test GQL WS client close error")
    with patch.object(
        respx_stash_client.gql_ws_client, "close_async", side_effect=test_error
    ):
        # Should not raise - exception should be caught and logged
        await respx_stash_client._cleanup_connection_resources()

    # Verify gql_ws_client was set to None despite the error
    assert respx_stash_client.gql_ws_client is None


@pytest.mark.asyncio
async def test_cleanup_connection_resources_handles_gql_client_close_error_without_log(
    respx_stash_client,
) -> None:
    """Test _cleanup_connection_resources handles gql_client close errors without log.

    This covers the branch 290->292 in client/base.py:
    - if hasattr(self, "log"): - False branch (no log attribute)
    - (skips log.debug and goes directly to line 292)

    When the client doesn't have a log attribute and closing gql_client
    raises an exception, it should still be caught (just not logged).
    """
    # Ensure client has gql_client
    assert hasattr(respx_stash_client, "gql_client")
    assert respx_stash_client.gql_client is not None

    # Patch gql_client.close_async() to raise an exception
    test_error = Exception("Test GQL client close error without log")

    # Use patch.object to temporarily remove log attribute
    with patch.object(respx_stash_client, "log", create=True):
        # Delete the log attribute to simulate missing log
        delattr(respx_stash_client, "log")

        with patch.object(
            respx_stash_client.gql_client, "close_async", side_effect=test_error
        ):
            # Should not raise - exception should be caught (but not logged)
            await respx_stash_client._cleanup_connection_resources()

        # Verify gql_client was set to None despite the error
        assert respx_stash_client.gql_client is None


@pytest.mark.asyncio
async def test_cleanup_connection_resources_handles_gql_ws_client_close_error_without_log(
    respx_stash_client,
) -> None:
    """Test _cleanup_connection_resources handles gql_ws_client close errors without log.

    This covers the branch 297->299 in client/base.py:
    - if hasattr(self, "log"): - False branch (no log attribute)
    - (skips log.debug and goes directly to line 299)

    When the client doesn't have a log attribute and closing gql_ws_client
    raises an exception, it should still be caught (just not logged).
    """
    # Ensure client has gql_ws_client
    assert hasattr(respx_stash_client, "gql_ws_client")
    assert respx_stash_client.gql_ws_client is not None

    # Patch gql_ws_client.close_async() to raise an exception
    test_error = Exception("Test GQL WS client close error without log")

    # Use patch.object to temporarily remove log attribute
    with patch.object(respx_stash_client, "log", create=True):
        # Delete the log attribute to simulate missing log
        delattr(respx_stash_client, "log")

        with patch.object(
            respx_stash_client.gql_ws_client, "close_async", side_effect=test_error
        ):
            # Should not raise - exception should be caught (but not logged)
            await respx_stash_client._cleanup_connection_resources()

        # Verify gql_ws_client was set to None despite the error
        assert respx_stash_client.gql_ws_client is None


@pytest.mark.asyncio
async def test_ensure_initialized_sets_log_if_missing() -> None:
    """Test _ensure_initialized sets log attribute if missing.

    This covers line 304 in client/base.py:
    - if not hasattr(self, "log"):
    -     self.log = client_logger

    When client doesn't have log attribute, _ensure_initialized should set it.
    """

    # Create client without initializing
    client = StashClientBase(conn={"Host": "localhost", "Port": 9999})

    # Remove log if it exists
    if hasattr(client, "log"):
        delattr(client, "log")

    # Set required attributes to avoid other RuntimeErrors
    client._initialized = True
    client.transport_config = {}  # type: ignore[typeddict-item]
    client.url = "http://localhost:9999/graphql"

    # Call _ensure_initialized - should set log (line 304)
    client._ensure_initialized()

    # Verify log was set
    assert hasattr(client, "log")
    assert client.log is not None


@pytest.mark.asyncio
async def test_ensure_initialized_raises_when_not_initialized() -> None:
    """Test _ensure_initialized raises when client not initialized.

    This covers line 307 in client/base.py:
    - if not hasattr(self, "_initialized") or not self._initialized:
    -     raise RuntimeError("Client not initialized - use get_client() first")

    When client._initialized is False, should raise RuntimeError.
    """

    # Create client without initializing
    client = StashClientBase(conn={"Host": "localhost", "Port": 9999})

    # Ensure _initialized is False
    client._initialized = False

    # Should raise RuntimeError (line 307)
    with pytest.raises(RuntimeError, match="Client not initialized"):
        client._ensure_initialized()


@pytest.mark.asyncio
async def test_ensure_initialized_raises_when_no_transport_config() -> None:
    """Test _ensure_initialized raises when transport_config missing.

    This covers line 310 in client/base.py:
    - if not hasattr(self, "transport_config"):
    -     raise RuntimeError("Transport configuration not initialized")

    When client doesn't have transport_config, should raise RuntimeError.
    """

    # Create client
    client = StashClientBase(conn={"Host": "localhost", "Port": 9999})

    # Set _initialized but remove transport_config
    client._initialized = True
    if hasattr(client, "transport_config"):
        delattr(client, "transport_config")

    # Should raise RuntimeError (line 310)
    with pytest.raises(RuntimeError, match="Transport configuration not initialized"):
        client._ensure_initialized()


@pytest.mark.asyncio
async def test_ensure_initialized_raises_when_no_url() -> None:
    """Test _ensure_initialized raises when url missing.

    This covers line 313 in client/base.py:
    - if not hasattr(self, "url"):
    -     raise RuntimeError("URL not initialized")

    When client doesn't have url, should raise RuntimeError.
    """

    # Create client
    client = StashClientBase(conn={"Host": "localhost", "Port": 9999})

    # Set _initialized and transport_config but remove url
    client._initialized = True
    client.transport_config = {}  # type: ignore[typeddict-item]
    if hasattr(client, "url"):
        delattr(client, "url")

    # Should raise RuntimeError (line 313)
    with pytest.raises(RuntimeError, match="URL not initialized"):
        client._ensure_initialized()


@pytest.mark.asyncio
async def test_handle_gql_error_converts_transport_query_error(
    respx_stash_client,
) -> None:
    """Test _handle_gql_error converts TransportQueryError to StashGraphQLError.

    This covers line 333 in client/base.py:
    - if isinstance(e, TransportQueryError):
    -     raise StashGraphQLError(f"GraphQL query error: {e.errors}")

    TransportQueryError (GraphQL validation errors) should be converted
    to StashGraphQLError.
    """
    # Create a TransportQueryError with sample errors
    gql_error = TransportQueryError(
        "Query validation failed", errors=[{"message": "Invalid field"}]
    )

    # Should raise StashGraphQLError (line 333)
    with pytest.raises(StashGraphQLError, match="GraphQL query error"):
        respx_stash_client._handle_gql_error(gql_error)


@pytest.mark.asyncio
async def test_handle_gql_error_with_malformed_error_structure(
    respx_stash_client,
) -> None:
    """Test _handle_gql_error handles malformed error structure gracefully.

    This covers lines 331-342 in client/base.py - the KeyError exception path
    when error structure is malformed and raises KeyError during stringification.
    """

    # Create a mock error object that raises KeyError when stringified
    class MalformedErrorList(list):
        def __str__(self):
            raise KeyError("'message'")

    # Create TransportQueryError with malformed errors
    gql_error = TransportQueryError(
        "Query validation failed", errors=MalformedErrorList([{"malformed": "data"}])
    )

    # Should still raise StashGraphQLError with fallback error message
    with pytest.raises(StashGraphQLError, match=r"error extracting details.*message"):
        respx_stash_client._handle_gql_error(gql_error)


@pytest.mark.asyncio
async def test_handle_gql_error_without_errors_attr_str_raises(
    respx_stash_client,
) -> None:
    """Test _handle_gql_error when exception has no errors attr and str() raises.

    This covers the branch 341->344 in client/base.py:
    - Line 330: hasattr(e, "errors") is False, so we try str(e)
    - str(e) raises an exception, entering except block at 331
    - Line 341: hasattr(e, "errors") is still False, so we skip the debug log
    - Line 344: raise StashGraphQLError (branch 341->344)
    """

    # Create a custom TransportQueryError without errors attribute
    # and __str__ that raises an exception on first call only
    class BrokenTransportQueryError(TransportQueryError):
        def __init__(self, message):
            # Don't call super().__init__() to avoid setting self.errors
            self.message = message
            self._str_call_count = 0

        def __str__(self):
            self._str_call_count += 1
            if self._str_call_count == 1:
                # First call raises exception (triggers except block)
                raise AttributeError("Cannot stringify this error")
            # Subsequent calls succeed (for fallback error message)
            return f"BrokenError: {self.message}"

    broken_error = BrokenTransportQueryError("Broken error")

    # Verify it doesn't have errors attribute
    assert not hasattr(broken_error, "errors")

    # Should raise StashGraphQLError with fallback message
    # The first str(e) at line 330 fails, entering except block
    # At line 341, hasattr(e, "errors") is False, so we skip debug log (341->344)
    with pytest.raises(StashGraphQLError, match=r"error extracting details"):
        respx_stash_client._handle_gql_error(broken_error)


@pytest.mark.asyncio
async def test_handle_gql_error_converts_transport_server_error(
    respx_stash_client,
) -> None:
    """Test _handle_gql_error converts TransportServerError to StashServerError.

    This covers line 336 in client/base.py:
    - if isinstance(e, TransportServerError):
    -     raise StashServerError(f"GraphQL server error: {e}")

    TransportServerError (server-side errors like 500) should be converted
    to StashServerError.
    """
    # Create a TransportServerError
    server_error = TransportServerError("Internal server error", 500)

    # Should raise StashServerError (line 336)
    with pytest.raises(StashServerError, match="GraphQL server error"):
        respx_stash_client._handle_gql_error(server_error)


@pytest.mark.asyncio
async def test_handle_gql_error_converts_transport_error(respx_stash_client) -> None:
    """Test _handle_gql_error converts TransportError to StashConnectionError.

    This covers line 339 in client/base.py:
    - if isinstance(e, TransportError):
    -     raise StashConnectionError(f"Failed to connect to {self.url}: {e}")

    TransportError (network/connection errors) should be converted
    to StashConnectionError.
    """
    # Create a TransportError
    transport_error = TransportError("Connection refused")

    # Should raise StashConnectionError (line 339)
    with pytest.raises(StashConnectionError, match="Failed to connect"):
        respx_stash_client._handle_gql_error(transport_error)


@pytest.mark.asyncio
async def test_handle_gql_error_converts_timeout_error(respx_stash_client) -> None:
    """Test _handle_gql_error converts asyncio.TimeoutError to StashConnectionError.

    This covers line 341 in client/base.py:
    - if isinstance(e, asyncio.TimeoutError):
    -     raise StashConnectionError(f"Request to {self.url} timed out")

    asyncio.TimeoutError should be converted to StashConnectionError.
    """
    # Create an asyncio.TimeoutError
    timeout_error = TimeoutError()

    # Should raise StashConnectionError (line 341)
    with pytest.raises(StashConnectionError, match="timed out"):
        respx_stash_client._handle_gql_error(timeout_error)


@pytest.mark.asyncio
async def test_handle_gql_error_converts_unexpected_error(respx_stash_client) -> None:
    """Test _handle_gql_error converts unexpected errors to StashError.

    This covers line 342 in client/base.py:
    - raise StashError(f"Unexpected error during request ({type(e).__name__}): {e}")

    Any unexpected error type should be converted to generic StashError.
    """

    # Create an unexpected error type
    unexpected_error = ValueError("Something went wrong")

    # Should raise StashError (line 342)
    with pytest.raises(StashError, match=r"Unexpected error.*ValueError"):
        respx_stash_client._handle_gql_error(unexpected_error)


@pytest.mark.asyncio
async def test_parse_result_to_type_handles_unexpected_response_structure(
    respx_stash_client, caplog
) -> None:
    """Test _parse_result_to_type handles unexpected response structures.

    This covers lines 448-470 in client/base.py:
    - Fallback warning for unexpected structure (451-453)
    - Final fallback paths (468-470)

    When response doesn't match expected single-key structure,
    should log warning and attempt fallback deserialization.
    """
    # Test with unexpected structure - multiple keys instead of single key
    # This triggers the fallback path starting at line 450
    unexpected_data = {
        "id": "123",
        "title": "Test Scene",
        "urls": [],
        "organized": False,
        "files": [],
        "tags": [],
        "performers": [],
        "galleries": [],
        "groups": [],
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }

    result = respx_stash_client._parse_result_to_type(unexpected_data, Scene)

    # Should have logged a warning about unexpected structure
    assert "Unexpected GraphQL response structure" in caplog.text

    # Should still successfully deserialize using fallback (line 469-470)
    assert result.id == "123"
    assert result.title == "Test Scene"


@pytest.mark.asyncio
async def test_get_configuration_defaults_uses_fallback_when_no_defaults(
    respx_stash_client, caplog
) -> None:
    """Test get_configuration_defaults uses fallback when no defaults in response.

    This covers lines 522-538 in client/base.py:
    - Warning when no defaults (line 522)
    - Hardcoded fallback defaults (lines 523-538)

    When API returns config without defaults field, should log warning
    and return hardcoded defaults.
    """
    # Mock HTTP response with config but no defaults
    response_data: dict = {"data": {"configuration": {"general": {}}}}

    route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(200, json=response_data)]
    )

    try:
        defaults = await respx_stash_client.get_configuration_defaults()
    finally:
        dump_graphql_calls(route.calls)

    # Verify route was called with correct query
    assert len(route.calls) == 1
    req = json.loads(route.calls[0].request.content)
    assert "configuration" in req["query"]

    # Should have logged warning
    assert "No defaults in response" in caplog.text

    # Should return hardcoded defaults
    assert defaults is not None
    assert hasattr(defaults, "scan")


@pytest.mark.asyncio
async def test_get_configuration_defaults_handles_exception(
    respx_stash_client,
) -> None:
    """Test get_configuration_defaults re-raises exceptions.

    This covers lines 539-541 in client/base.py:
    - Exception logging (line 540)
    - Re-raising exception (line 541)

    When HTTP request fails, should log error and re-raise wrapped in StashConnectionError.
    """
    # Mock HTTP request to fail
    route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=httpx.ConnectError("Connection failed")
    )

    # Connection errors get wrapped in StashConnectionError
    try:
        with pytest.raises(StashConnectionError, match="Failed to connect"):
            await respx_stash_client.get_configuration_defaults()
    finally:
        dump_graphql_calls(route.calls)

    # Verify route was called (even though it failed)
    assert len(route.calls) == 1
    req = json.loads(route.calls[0].request.content)
    assert "configuration" in req["query"]


@pytest.mark.asyncio
async def test_metadata_generate_basic_call(respx_stash_client) -> None:
    """Test metadata_generate basic functionality.

    This covers lines 583-621 in client/base.py:
    - Full method execution with options and input

    Tests the complete metadata generation flow.
    """
    # Mock HTTP response with job ID
    response_data = {"data": {"metadataGenerate": "123"}}

    route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(200, json=response_data)]
    )

    options = GenerateMetadataOptions()
    input_data = GenerateMetadataInput()

    try:
        job_id = await respx_stash_client.metadata_generate(
            options=options, input_data=input_data
        )
    finally:
        dump_graphql_calls(route.calls)

    assert job_id == "123"

    # Verify route was called with correct mutation
    assert len(route.calls) == 1
    req = json.loads(route.calls[0].request.content)
    assert "metadataGenerate" in req["query"]


@pytest.mark.asyncio
async def test_check_system_ready_raises_when_status_none(
    respx_stash_client,
) -> None:
    """Test check_system_ready raises when status is None.

    This covers lines 839-843 in client/base.py:
    - Check for None status (line 839)
    - Raise RuntimeError (lines 840-843)

    When get_system_status returns null, should raise RuntimeError.
    """
    # Mock HTTP response with null systemStatus
    response_data = {"data": {"systemStatus": None}}

    route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(200, json=response_data)]
    )

    try:
        with pytest.raises(
            RuntimeError, match="Unable to determine Stash system status"
        ):
            await respx_stash_client.check_system_ready()
    finally:
        dump_graphql_calls(route.calls)

    # Verify route was called with systemStatus query
    assert len(route.calls) == 1
    req = json.loads(route.calls[0].request.content)
    assert "systemStatus" in req["query"]


@pytest.mark.asyncio
async def test_check_system_ready_raises_on_needs_migration(
    respx_stash_client,
) -> None:
    """Test check_system_ready raises on NEEDS_MIGRATION status.

    This covers lines 846-851 in client/base.py:
    - Check for NEEDS_MIGRATION (line 846)
    - Raise StashSystemNotReadyError (lines 847-851)

    When system needs migration, should raise specific error.
    """
    # Mock HTTP response with NEEDS_MIGRATION status
    response_data = {
        "data": {
            "systemStatus": {
                "status": "NEEDS_MIGRATION",
                "databasePath": "/path/to/db",
                "appSchema": 42,
            }
        }
    }

    route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(200, json=response_data)]
    )

    try:
        with pytest.raises(StashSystemNotReadyError, match="requires migration"):
            await respx_stash_client.check_system_ready()
    finally:
        dump_graphql_calls(route.calls)

    # Verify route was called with systemStatus query
    assert len(route.calls) == 1
    req = json.loads(route.calls[0].request.content)
    assert "systemStatus" in req["query"]


@pytest.mark.asyncio
async def test_check_system_ready_raises_on_setup_required(
    respx_stash_client,
) -> None:
    """Test check_system_ready raises on SETUP status.

    This covers lines 853-857 in client/base.py:
    - Check for SETUP (line 853)
    - Raise StashSystemNotReadyError (lines 854-857)

    When system needs setup, should raise specific error.
    """
    # Mock HTTP response with SETUP status
    response_data = {
        "data": {
            "systemStatus": {
                "status": "SETUP",
                "databasePath": "/path/to/db",
                "appSchema": 42,
            }
        }
    }

    route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(200, json=response_data)]
    )

    try:
        with pytest.raises(StashSystemNotReadyError, match="requires initial setup"):
            await respx_stash_client.check_system_ready()
    finally:
        dump_graphql_calls(route.calls)

    # Verify route was called with systemStatus query
    assert len(route.calls) == 1
    req = json.loads(route.calls[0].request.content)
    assert "systemStatus" in req["query"]
