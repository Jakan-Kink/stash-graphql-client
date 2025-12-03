"""Tests for stash_graphql_client.context module.

Tests the StashContext class which provides connection management
and async context manager support for StashClient.
"""

import asyncio

import httpx
import pytest
import respx

from stash_graphql_client import StashClient
from stash_graphql_client.context import StashContext


class TestStashContextInit:
    """Tests for StashContext initialization."""

    @pytest.mark.unit
    def test_default_initialization(self) -> None:
        """Test StashContext can be initialized with defaults."""
        context = StashContext()
        assert context.conn is not None
        assert context.verify_ssl is True
        assert context._client is None
        assert context._ref_count == 0

    @pytest.mark.unit
    def test_initialization_with_conn(self) -> None:
        """Test StashContext can be initialized with connection dict."""
        conn = {
            "Scheme": "https",
            "Host": "stash.example.com",
            "Port": 9999,
            "ApiKey": "test-api-key",
        }
        context = StashContext(conn=conn, verify_ssl=False)

        assert context.conn["Scheme"] == "https"
        assert context.conn["Host"] == "stash.example.com"
        assert context.conn["Port"] == 9999
        assert context.conn["ApiKey"] == "test-api-key"
        assert context.verify_ssl is False

    @pytest.mark.unit
    def test_case_insensitive_conn_dict(self) -> None:
        """Test that connection dict is case-insensitive."""
        conn = {"scheme": "http", "HOST": "localhost", "Port": 9999}
        context = StashContext(conn=conn)

        # CIMultiDict allows case-insensitive access
        assert context.conn["scheme"] == "http"
        assert context.conn["SCHEME"] == "http"


class TestStashContextProperties:
    """Tests for StashContext properties."""

    @pytest.mark.unit
    def test_interface_raises_when_not_initialized(self) -> None:
        """Test interface property raises RuntimeError when client not initialized."""
        context = StashContext()

        with pytest.raises(RuntimeError, match="Client not initialized"):
            _ = context.interface

    @pytest.mark.unit
    def test_client_raises_when_not_initialized(self) -> None:
        """Test client property raises RuntimeError when client not initialized."""
        context = StashContext()

        with pytest.raises(RuntimeError, match="Client not initialized"):
            _ = context.client

    @pytest.mark.unit
    def test_ref_count_initially_zero(self) -> None:
        """Test ref_count property returns 0 initially."""
        context = StashContext()
        assert context.ref_count == 0


class TestStashContextGetClient:
    """Tests for StashContext.get_client() method."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_client_returns_stash_client(
        self, mock_ws_transport, mock_gql_ws_connect
    ) -> None:
        """Test get_client returns a StashClient instance."""
        context = StashContext(conn={"Host": "localhost", "Port": 9999})

        with respx.mock:
            respx.post("http://localhost:9999/graphql").mock(
                return_value=httpx.Response(200, json={"data": {}})
            )

            client = await context.get_client()
            assert isinstance(client, StashClient)
            assert context._client is client

            await context.close()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_client_returns_same_instance(
        self, mock_ws_transport, mock_gql_ws_connect
    ) -> None:
        """Test get_client returns the same client instance on subsequent calls."""
        context = StashContext(conn={"Host": "localhost", "Port": 9999})

        with respx.mock:
            respx.post("http://localhost:9999/graphql").mock(
                return_value=httpx.Response(200, json={"data": {}})
            )

            client1 = await context.get_client()
            client2 = await context.get_client()

            assert client1 is client2

            await context.close()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_client_initializes_client(
        self, mock_ws_transport, mock_gql_ws_connect
    ) -> None:
        """Test get_client properly initializes the client."""
        context = StashContext(conn={"Host": "localhost", "Port": 9999})

        with respx.mock:
            respx.post("http://localhost:9999/graphql").mock(
                return_value=httpx.Response(200, json={"data": {}})
            )

            client = await context.get_client()
            assert client._initialized is True

            await context.close()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_client_initialization_failure(
        self, mock_ws_transport, mock_gql_ws_connect
    ) -> None:
        """Test get_client raises RuntimeError on initialization failure."""
        context = StashContext(conn={"Host": "localhost", "Port": 9999})

        # Make connect_async raise an exception
        mock_gql_ws_connect.side_effect = Exception("Connection failed")

        with pytest.raises(RuntimeError, match="Failed to initialize Stash client"):
            await context.get_client()

        # Client should be None after failure
        assert context._client is None


class TestStashContextClose:
    """Tests for StashContext.close() method."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_close_with_no_client(self) -> None:
        """Test close works when no client was ever created."""
        context = StashContext()
        await context.close()
        assert context._client is None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_close_cleans_up_client(
        self, mock_ws_transport, mock_gql_ws_connect
    ) -> None:
        """Test close properly cleans up the client."""
        context = StashContext(conn={"Host": "localhost", "Port": 9999})

        with respx.mock:
            respx.post("http://localhost:9999/graphql").mock(
                return_value=httpx.Response(200, json={"data": {}})
            )

            await context.get_client()
            assert context._client is not None

            await context.close()
            assert context._client is None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_close_deferred_with_active_refs(
        self, mock_ws_transport, mock_gql_ws_connect
    ) -> None:
        """Test close is deferred when there are active references."""
        context = StashContext(conn={"Host": "localhost", "Port": 9999})

        with respx.mock:
            respx.post("http://localhost:9999/graphql").mock(
                return_value=httpx.Response(200, json={"data": {}})
            )

            # Simulate entering context manager
            async with context._ref_lock:
                context._ref_count = 1

            await context.get_client()
            client = context._client

            # Close without force - should be deferred
            await context.close()

            # Client should still be there (deferred close)
            assert context._client is client

            # Clean up
            context._ref_count = 0
            await context.close()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_close_warning_with_active_refs(
        self, mock_ws_transport, mock_gql_ws_connect, caplog
    ) -> None:
        """Test close logs warning when called with active references."""
        import logging

        caplog.set_level(logging.WARNING)

        context = StashContext(conn={"Host": "localhost", "Port": 9999})

        with respx.mock:
            respx.post("http://localhost:9999/graphql").mock(
                return_value=httpx.Response(200, json={"data": {}})
            )

            await context.get_client()

            # Simulate active references
            async with context._ref_lock:
                context._ref_count = 2

            # Call close manually (not from __aexit__)
            await context.close()

            # Verify warning was logged
            assert any(
                "active references" in record.message
                for record in caplog.records
                if record.levelname == "WARNING"
            )

            # Client should still exist due to active refs
            assert context._client is not None

            # Clean up
            context._ref_count = 0
            await context.close(force=True)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_close_forced_with_active_refs(
        self, mock_ws_transport, mock_gql_ws_connect
    ) -> None:
        """Test close with force=True closes even with active refs."""
        context = StashContext(conn={"Host": "localhost", "Port": 9999})

        with respx.mock:
            respx.post("http://localhost:9999/graphql").mock(
                return_value=httpx.Response(200, json={"data": {}})
            )

            async with context._ref_lock:
                context._ref_count = 1

            await context.get_client()

            await context.close(force=True)
            assert context._client is None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_close_internal_flag(
        self, mock_ws_transport, mock_gql_ws_connect
    ) -> None:
        """Test close with _internal=True for __aexit__ calls."""
        context = StashContext(conn={"Host": "localhost", "Port": 9999})

        with respx.mock:
            respx.post("http://localhost:9999/graphql").mock(
                return_value=httpx.Response(200, json={"data": {}})
            )

            await context.get_client()

            # _internal=True skips lock and ref_count check (used by __aexit__)
            await context.close(_internal=True)
            assert context._client is None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_close_internal_flag_with_no_client(self) -> None:
        """Test close with _internal=True when client was never initialized.

        This exercises the branch where _internal=True but _client is None,
        which can happen if __aexit__ is called on a context where initialization
        failed or the client was already closed.
        """
        context = StashContext()

        # Client was never initialized
        assert context._client is None

        # Should return early without error
        await context.close(_internal=True)
        assert context._client is None


class TestStashContextAsyncContextManager:
    """Tests for StashContext async context manager protocol."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_aenter_returns_client(
        self, mock_ws_transport, mock_gql_ws_connect
    ) -> None:
        """Test __aenter__ returns the StashClient."""
        context = StashContext(conn={"Host": "localhost", "Port": 9999})

        with respx.mock:
            respx.post("http://localhost:9999/graphql").mock(
                return_value=httpx.Response(200, json={"data": {}})
            )

            async with context as client:
                assert isinstance(client, StashClient)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_aenter_increments_ref_count(
        self, mock_ws_transport, mock_gql_ws_connect
    ) -> None:
        """Test __aenter__ increments the reference count."""
        context = StashContext(conn={"Host": "localhost", "Port": 9999})

        with respx.mock:
            respx.post("http://localhost:9999/graphql").mock(
                return_value=httpx.Response(200, json={"data": {}})
            )

            assert context.ref_count == 0

            async with context:
                assert context.ref_count == 1

            assert context.ref_count == 0

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_aexit_decrements_ref_count(
        self, mock_ws_transport, mock_gql_ws_connect
    ) -> None:
        """Test __aexit__ decrements the reference count."""
        context = StashContext(conn={"Host": "localhost", "Port": 9999})

        with respx.mock:
            respx.post("http://localhost:9999/graphql").mock(
                return_value=httpx.Response(200, json={"data": {}})
            )

            async with context:
                assert context.ref_count == 1

            assert context.ref_count == 0

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_aexit_closes_client_when_ref_zero(
        self, mock_ws_transport, mock_gql_ws_connect
    ) -> None:
        """Test __aexit__ closes client when ref count reaches 0."""
        context = StashContext(conn={"Host": "localhost", "Port": 9999})

        with respx.mock:
            respx.post("http://localhost:9999/graphql").mock(
                return_value=httpx.Response(200, json={"data": {}})
            )

            async with context as client:
                assert context._client is not None
                assert client is context._client

            assert context._client is None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_concurrent_context_managers(
        self, mock_ws_transport, mock_gql_ws_connect
    ) -> None:
        """Test multiple concurrent context managers share the same client."""
        context = StashContext(conn={"Host": "localhost", "Port": 9999})

        with respx.mock:
            respx.post("http://localhost:9999/graphql").mock(
                return_value=httpx.Response(200, json={"data": {}})
            )

            async def use_context() -> StashClient:
                async with context as client:
                    await asyncio.sleep(0.01)
                    return client

            clients = await asyncio.gather(use_context(), use_context())

            # Both should have gotten the same client instance
            assert clients[0] is clients[1]
            assert context.ref_count == 0

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_nested_context_managers(
        self, mock_ws_transport, mock_gql_ws_connect
    ) -> None:
        """Test nested context managers properly increment/decrement ref count."""
        context = StashContext(conn={"Host": "localhost", "Port": 9999})

        with respx.mock:
            respx.post("http://localhost:9999/graphql").mock(
                return_value=httpx.Response(200, json={"data": {}})
            )

            async with context:
                assert context.ref_count == 1

                async with context:
                    assert context.ref_count == 2

                    async with context:
                        assert context.ref_count == 3

                    assert context.ref_count == 2

                assert context.ref_count == 1

            assert context.ref_count == 0
            assert context._client is None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_aexit_keeps_client_open_with_active_refs(
        self, mock_ws_transport, mock_gql_ws_connect
    ) -> None:
        """Test __aexit__ keeps client open when other refs are active."""
        context = StashContext(conn={"Host": "localhost", "Port": 9999})

        with respx.mock:
            respx.post("http://localhost:9999/graphql").mock(
                return_value=httpx.Response(200, json={"data": {}})
            )

            async with context:
                async with context:
                    assert context.ref_count == 2
                # First exit, but ref_count is still 1
                assert context.ref_count == 1
                assert context._client is not None  # Client should still be open

            # Now client should be closed
            assert context._client is None


class TestStashContextInterfaceProperty:
    """Tests for interface property after initialization."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_interface_returns_client(
        self, mock_ws_transport, mock_gql_ws_connect
    ) -> None:
        """Test interface property returns client after initialization."""
        context = StashContext(conn={"Host": "localhost", "Port": 9999})

        with respx.mock:
            respx.post("http://localhost:9999/graphql").mock(
                return_value=httpx.Response(200, json={"data": {}})
            )

            client = await context.get_client()
            assert context.interface is client

            await context.close()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_client_property_returns_client(
        self, mock_ws_transport, mock_gql_ws_connect
    ) -> None:
        """Test client property returns client after initialization."""
        context = StashContext(conn={"Host": "localhost", "Port": 9999})

        with respx.mock:
            respx.post("http://localhost:9999/graphql").mock(
                return_value=httpx.Response(200, json={"data": {}})
            )

            initialized_client = await context.get_client()
            assert context.client is initialized_client

            await context.close()
