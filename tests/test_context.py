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
        """Test interface property raises RuntimeError when client not initialized.

        This tests lines 81-84: the error path in the interface property.
        """
        context = StashContext()

        with pytest.raises(RuntimeError, match="Client not initialized"):
            _ = context.interface

    @pytest.mark.unit
    def test_client_raises_when_not_initialized(self) -> None:
        """Test client property raises RuntimeError when client not initialized.

        This tests lines 134-140: the error path in the client property.
        """
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
        """Test get_client returns a StashClient instance.

        Also covers client/base.py lines 132-133:
        - if self._initialized:
        -     return

        Verifies that calling initialize() on an already-initialized client
        returns early without re-initializing.
        """
        context = StashContext(conn={"Host": "localhost", "Port": 9999})

        with respx.mock:
            respx.post("http://localhost:9999/graphql").mock(
                side_effect=[httpx.Response(200, json={"data": {}})]
            )

            client = await context.get_client()
            assert isinstance(client, StashClient)
            assert context._client is client

            # Test re-initialization guard (lines 132-133)
            # Client is already initialized, so this should return immediately
            assert client._initialized is True
            await client.initialize()  # Should return early, no error
            assert client._initialized is True  # Still initialized

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
                side_effect=[httpx.Response(200, json={"data": {}})]
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
                side_effect=[httpx.Response(200, json={"data": {}})]
            )

            client = await context.get_client()
            assert client._initialized is True

            await context.close()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_client_initialization_failure(
        self, mock_ws_transport, mock_gql_ws_connect
    ) -> None:
        """Test get_client raises RuntimeError on initialization failure.

        This tests lines 118-121: exception handling in get_client where
        client initialization fails and _client is set back to None.
        """
        context = StashContext(conn={"Host": "localhost", "Port": 9999})

        # Make connect_async raise an exception
        mock_gql_ws_connect.side_effect = Exception("Connection failed")

        with pytest.raises(RuntimeError, match="Failed to initialize Stash client"):
            await context.get_client()

        # Client should be None after failure (line 121)
        assert context._client is None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_client_initializes_store(
        self, mock_ws_transport, mock_gql_ws_connect
    ) -> None:
        """Test get_client initializes entity store and wires it to StashObject."""
        context = StashContext(conn={"Host": "localhost", "Port": 9999})

        with respx.mock:
            respx.post("http://localhost:9999/graphql").mock(
                side_effect=[httpx.Response(200, json={"data": {}})]
            )

            await context.get_client()

            # Store should be initialized
            assert context._store is not None

            # Store should be wired to StashObject
            from stash_graphql_client.types.base import StashObject

            assert StashObject._store is context._store

            await context.close()


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
        """Test close properly cleans up the client.

        This tests lines 184-189: cleanup of client and store when closing.
        """
        context = StashContext(conn={"Host": "localhost", "Port": 9999})

        with respx.mock:
            respx.post("http://localhost:9999/graphql").mock(
                side_effect=[httpx.Response(200, json={"data": {}})]
            )

            await context.get_client()
            assert context._client is not None
            assert context._store is not None

            await context.close()

            # Lines 186-189: Client and store should be cleaned up
            assert context._client is None
            assert context._store is None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_close_unwires_store_from_stash_object(
        self, mock_ws_transport, mock_gql_ws_connect
    ) -> None:
        """Test close unwires entity store from StashObject.

        This tests the store cleanup and unwiring in close().
        """
        context = StashContext(conn={"Host": "localhost", "Port": 9999})

        with respx.mock:
            respx.post("http://localhost:9999/graphql").mock(
                side_effect=[httpx.Response(200, json={"data": {}})]
            )

            await context.get_client()

            from stash_graphql_client.types.base import StashObject

            # Store should be wired
            assert StashObject._store is context._store

            await context.close()

            # Store should be unwired
            assert StashObject._store is None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_close_deferred_with_active_refs(
        self, mock_ws_transport, mock_gql_ws_connect
    ) -> None:
        """Test close is deferred when there are active references.

        This tests lines 167-179: early return when ref_count > 0 and not forced.
        """
        context = StashContext(conn={"Host": "localhost", "Port": 9999})

        with respx.mock:
            respx.post("http://localhost:9999/graphql").mock(
                side_effect=[httpx.Response(200, json={"data": {}})]
            )

            # Simulate entering context manager
            async with context._ref_lock:
                context._ref_count = 1

            await context.get_client()
            client = context._client

            # Close without force - should be deferred (line 174-179)
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
        """Test close logs warning when called with active references.

        This tests lines 167-179: warning log when close is called with active refs.
        """
        import logging

        caplog.set_level(logging.WARNING)

        context = StashContext(conn={"Host": "localhost", "Port": 9999})

        with respx.mock:
            respx.post("http://localhost:9999/graphql").mock(
                side_effect=[httpx.Response(200, json={"data": {}})]
            )

            await context.get_client()

            # Simulate active references
            async with context._ref_lock:
                context._ref_count = 2

            # Call close manually (not from __aexit__)
            await context.close()

            # Verify warning was logged (line 167-172)
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
        """Test close with force=True closes even with active refs.

        This tests the force=True path that bypasses the ref_count check.
        """
        context = StashContext(conn={"Host": "localhost", "Port": 9999})

        with respx.mock:
            respx.post("http://localhost:9999/graphql").mock(
                side_effect=[httpx.Response(200, json={"data": {}})]
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
        """Test close with _internal=True for __aexit__ calls.

        This tests lines 149 and 191->196: the internal close path.
        """
        context = StashContext(conn={"Host": "localhost", "Port": 9999})

        with respx.mock:
            respx.post("http://localhost:9999/graphql").mock(
                side_effect=[httpx.Response(200, json={"data": {}})]
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

        # Should return early without error (line 149)
        await context.close(_internal=True)
        assert context._client is None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_close_internal_with_store_cleanup(
        self, mock_ws_transport, mock_gql_ws_connect
    ) -> None:
        """Test close with _internal=True cleans up store.

        This tests the store cleanup path in the _internal branch.
        """
        context = StashContext(conn={"Host": "localhost", "Port": 9999})

        with respx.mock:
            respx.post("http://localhost:9999/graphql").mock(
                side_effect=[httpx.Response(200, json={"data": {}})]
            )

            await context.get_client()
            assert context._store is not None

            await context.close(_internal=True)

            # Store should be cleaned up
            assert context._store is None

            from stash_graphql_client.types.base import StashObject

            # Store should be unwired from StashObject
            assert StashObject._store is None


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
                side_effect=[httpx.Response(200, json={"data": {}})]
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
                side_effect=[httpx.Response(200, json={"data": {}})]
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
                side_effect=[httpx.Response(200, json={"data": {}})]
            )

            async with context:
                assert context.ref_count == 1

            assert context.ref_count == 0

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_aexit_closes_client_when_ref_zero(
        self, mock_ws_transport, mock_gql_ws_connect
    ) -> None:
        """Test __aexit__ closes client when ref count reaches 0.

        This tests lines 230-242: the path where ref_count reaches 0 and client is closed.
        """
        context = StashContext(conn={"Host": "localhost", "Port": 9999})

        with respx.mock:
            respx.post("http://localhost:9999/graphql").mock(
                side_effect=[httpx.Response(200, json={"data": {}})]
            )

            async with context as client:
                assert context._client is not None
                assert client is context._client

            # After exit, ref_count should be 0 and client closed (lines 234-238)
            assert context._client is None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_aexit_keeps_client_open_with_active_refs(
        self, mock_ws_transport, mock_gql_ws_connect
    ) -> None:
        """Test __aexit__ keeps client open when other refs are active.

        This tests lines 211-216: the path where ref_count > 0 after decrement,
        so the client stays open.
        """
        context = StashContext(conn={"Host": "localhost", "Port": 9999})

        with respx.mock:
            respx.post("http://localhost:9999/graphql").mock(
                side_effect=[httpx.Response(200, json={"data": {}})]
            )

            async with context:
                async with context:
                    assert context.ref_count == 2

                # First exit, but ref_count is still 1 (line 240-242)
                assert context.ref_count == 1
                assert context._client is not None  # Client should still be open

            # Now client should be closed
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
                side_effect=[httpx.Response(200, json={"data": {}})]
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
                side_effect=[httpx.Response(200, json={"data": {}})]
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
                side_effect=[httpx.Response(200, json={"data": {}})]
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
                side_effect=[httpx.Response(200, json={"data": {}})]
            )

            initialized_client = await context.get_client()
            assert context.client is initialized_client

            await context.close()


class TestStashContextEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_multiple_close_calls_safe(
        self, mock_ws_transport, mock_gql_ws_connect
    ) -> None:
        """Test that calling close multiple times is safe."""
        context = StashContext(conn={"Host": "localhost", "Port": 9999})

        with respx.mock:
            respx.post("http://localhost:9999/graphql").mock(
                side_effect=[httpx.Response(200, json={"data": {}})]
            )

            await context.get_client()
            await context.close()

            # Second close should be safe (no client to close)
            await context.close()
            assert context._client is None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_close_with_only_store_no_client(
        self, mock_ws_transport, mock_gql_ws_connect
    ) -> None:
        """Test close when store exists but client is None.

        This tests the branch where _store is not None but _client is None.
        """
        context = StashContext(conn={"Host": "localhost", "Port": 9999})

        with respx.mock:
            respx.post("http://localhost:9999/graphql").mock(
                side_effect=[httpx.Response(200, json={"data": {}})]
            )

            await context.get_client()

            # Manually set client to None but keep store
            context._client = None

            # Close should still clean up store
            await context.close()
            assert context._store is None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_context_manager_with_exception(
        self, mock_ws_transport, mock_gql_ws_connect
    ) -> None:
        """Test that context manager properly cleans up even when exception occurs."""
        context = StashContext(conn={"Host": "localhost", "Port": 9999})

        with respx.mock:
            respx.post("http://localhost:9999/graphql").mock(
                side_effect=[httpx.Response(200, json={"data": {}})]
            )

            # Verify client is initialized and exception is raised
            async with context:
                assert context._client is not None

            # Now test exception handling
            with pytest.raises(ValueError, match="Test error"):
                async with context:
                    raise ValueError("Test error")

            # Client should still be cleaned up after exception
            assert context._client is None
            assert context.ref_count == 0

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_client_with_none_conn(
        self, mock_ws_transport, mock_gql_ws_connect
    ) -> None:
        """Test get_client works with None connection dict."""
        context = StashContext(conn=None)

        with respx.mock:
            # Default URL when no conn is provided
            respx.post("http://localhost:9999/graphql").mock(
                side_effect=[httpx.Response(200, json={"data": {}})]
            )

            client = await context.get_client()
            assert isinstance(client, StashClient)

            await context.close()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_close_internal_with_no_store(self) -> None:
        """Test close with _internal=True when store is None.

        This tests the branch in _internal close where _store is None.
        """
        context = StashContext()

        # Neither client nor store initialized
        assert context._client is None
        assert context._store is None

        # Should complete without error
        await context.close(_internal=True)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_close_manual_with_no_store(
        self, mock_ws_transport, mock_gql_ws_connect
    ) -> None:
        """Test manual close when store is None but client exists.

        This tests the branch in manual close where _store is None.
        """
        context = StashContext(conn={"Host": "localhost", "Port": 9999})

        with respx.mock:
            respx.post("http://localhost:9999/graphql").mock(
                side_effect=[httpx.Response(200, json={"data": {}})]
            )

            await context.get_client()

            # Manually set store to None
            context._store = None

            # Close should still work (only closes client)
            await context.close()
            assert context._client is None
