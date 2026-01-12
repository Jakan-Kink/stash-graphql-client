"""Unit tests for StashClient initialization.

These tests cover the initialization logic in client/__init__.py,
particularly the host conversion and API key handling branches.
"""

import pytest

from stash_graphql_client import StashClient


@pytest.mark.unit
class TestStashClientInit:
    """Tests for StashClient.__init__ method."""

    def test_init_with_default_host(self) -> None:
        """Test initialization with default localhost."""
        client = StashClient()

        assert client.url == "http://localhost:9999/graphql"

    def test_init_with_custom_host(self) -> None:
        """Test initialization with custom host."""
        client = StashClient(conn={"Host": "stash.example.com", "Port": 8080})

        assert client.url == "http://stash.example.com:8080/graphql"

    def test_init_with_all_interfaces_host_converts_to_localhost(self) -> None:
        """Test that 0.0.0.0 host is converted to 127.0.0.1.

        This covers line 71: if host == "0.0.0.0"
        """
        client = StashClient(conn={"Host": "0.0.0.0"})  # nosec B104  # noqa: S104

        # 0.0.0.0 should be converted to 127.0.0.1
        assert client.url == "http://127.0.0.1:9999/graphql"

    def test_init_with_api_key(self) -> None:
        """Test initialization with API key.

        This covers lines 78-79: if api_key := conn.get("ApiKey")
        """
        client = StashClient(conn={"ApiKey": "test-api-key-12345"})

        # The client should be created successfully with the API key
        # We can't directly check headers here, but we verify initialization works
        assert client.url == "http://localhost:9999/graphql"
        assert client._init_args[0] is not None
        assert client._init_args[0]["ApiKey"] == "test-api-key-12345"

    def test_init_with_https_scheme(self) -> None:
        """Test initialization with HTTPS scheme."""
        client = StashClient(conn={"Scheme": "https", "Host": "secure.example.com"})

        assert client.url == "https://secure.example.com:9999/graphql"

    def test_init_with_all_options(self) -> None:
        """Test initialization with all connection options."""
        client = StashClient(
            conn={
                "Scheme": "https",
                "Host": "stash.example.com",
                "Port": 9998,
                "ApiKey": "my-secret-key",
            },
            verify_ssl=False,
        )

        assert client.url == "https://stash.example.com:9998/graphql"
        assert client._init_args[1] is False  # verify_ssl

    def test_init_with_none_conn(self) -> None:
        """Test initialization with None connection dict."""
        client = StashClient(conn=None)

        assert client.url == "http://localhost:9999/graphql"

    def test_init_sets_initialized_flag_to_false(self) -> None:
        """Test that __init__ sets _initialized to False."""
        client = StashClient()

        # Client should not be initialized until initialize() is called
        assert client._initialized is False

    def test_init_with_invalid_port_string_raises_typeerror(self) -> None:
        """Test initialization rejects non-numeric port strings."""
        with pytest.raises(TypeError, match="Port must be an int or numeric string"):
            StashClient(conn={"Host": "localhost", "Port": "not-a-number"})
