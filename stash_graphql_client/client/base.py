"""Base Stash client class."""

import asyncio
from datetime import datetime
from types import TracebackType
from typing import Any, TypedDict, TypeVar, get_args, get_origin, overload

import httpx
from gql import Client, gql
from gql.transport.exceptions import (
    TransportError,
    TransportQueryError,
    TransportServerError,
)
from gql.transport.httpx import HTTPXAsyncTransport
from gql.transport.websockets import WebsocketsTransport
from httpx_retries import Retry, RetryTransport

from ..errors import (
    StashConnectionError,
    StashError,
    StashGraphQLError,
    StashServerError,
)
from ..logging import client_logger
from ..types.unset import UnsetType
from .utils import sanitize_model_data


T = TypeVar("T")


class TransportConfig(TypedDict):
    """Type definition for transport configuration."""

    url: str
    headers: dict[str, str] | None
    ssl: bool
    timeout: int | None


class StashClientBase:
    """Base GraphQL client for Stash."""

    # Type annotations for instance attributes
    client: (
        Client  # Backward compatibility alias for gql_client (set after initialize())
    )

    def __init__(
        self,
        conn: dict[str, Any] | None = None,
        verify_ssl: bool = True,
    ) -> None:
        """Initialize client.

        Args:
            conn: Connection details dictionary with:
                - Scheme: Protocol (default: "http")
                - Host: Hostname (default: "localhost")
                - Port: Port number (default: 9999)
                - ApiKey: Optional API key
                - Logger: Optional logger instance
            verify_ssl: Whether to verify SSL certificates
        """
        if not hasattr(self, "_initialized"):
            self._initialized = False
        if not hasattr(self, "_init_args"):
            self._init_args = (conn, verify_ssl)
        # Schema is always None (disabled due to Stash's deprecated required arguments)
        if not hasattr(self, "schema"):
            self.schema = None

    @staticmethod
    def _create_retry_policy() -> Retry:
        """
        Create a retry policy with exponential backoff for GraphQL requests.

        Retry Strategy:
        - Retries on network errors, timeouts, and 5xx server errors (500-599)
        - Default retryable status codes: 429, 502, 503, 504 (from httpx-retries)
        - Custom additional status codes: 500, 501 (other 5xx errors)
        - 4xx errors are NOT retried (client errors like 400, 401, 404)
        - Uses exponential backoff with jitter: base delay 0.5s
        - Max 3 retries

        Returns:
            Retry: Configured retry policy
        """
        return Retry(
            total=3,  # Max 3 retry attempts
            backoff_factor=0.5,  # Start with 500ms delay, exponential backoff
            status_forcelist=[500, 501, 502, 503, 504],  # 5xx server errors
            respect_retry_after_header=True,  # Honor server Retry-After header
            backoff_jitter=0.25,  # Add jitter to prevent thundering herd
        )

    @classmethod
    async def create(
        cls,
        conn: dict[str, Any] | None = None,
        verify_ssl: bool = True,
    ) -> "StashClientBase":
        """Create and initialize a new client.

        Args:
            conn: Connection details dictionary
            verify_ssl: Whether to verify SSL certificates

        Returns:
            Initialized client instance
        """
        client = cls(conn, verify_ssl)
        await client.initialize()
        return client

    async def initialize(self) -> None:
        """Initialize the client.

        This is called by the context manager if not already initialized.
        """
        if self._initialized:
            return

        conn, verify_ssl = self._init_args
        conn = conn or {}

        # Set up logging - use fansly.stash.client hierarchy
        self.log = conn.get("Logger", client_logger)

        # Build URLs
        scheme = conn.get("Scheme", "http")
        ws_scheme = "ws" if scheme == "http" else "wss"
        host = conn.get("Host", "localhost")
        if host == "0.0.0.0":  # nosec B104  # noqa: S104  # Converting all-interfaces to localhost
            host = "127.0.0.1"
        port = conn.get("Port", 9999)

        self.url = f"{scheme}://{host}:{port}/graphql"
        self.ws_url = f"{ws_scheme}://{host}:{port}/graphql"

        # Set up headers
        headers = {}
        if api_key := conn.get("ApiKey"):
            self.log.debug("Using API key authentication")
            headers["ApiKey"] = api_key
        else:
            self.log.warning("No API key provided")

        # Create retry transport for resilient GraphQL requests
        # This wraps the HTTP client to provide automatic retry on transient failures
        retry_policy = self._create_retry_policy()
        retry_transport = RetryTransport(retry=retry_policy)

        # HTTPXAsyncTransport with retry support and HTTP/2
        # The kwargs are passed to httpx.AsyncClient() when connecting
        self.http_transport = HTTPXAsyncTransport(
            url=self.url,
            transport=retry_transport,  # Add retry support to the transport
            headers=headers,  # Pass API key and other headers
            verify=verify_ssl,  # httpx uses 'verify' instead of 'ssl'
            timeout=30,
            http2=True,  # Enable HTTP/2 for better performance
            limits=httpx.Limits(
                max_connections=100,  # Allow concurrent connections
                max_keepalive_connections=20,  # Keep connections alive for reuse
            ),
        )
        self.ws_transport = WebsocketsTransport(
            url=self.ws_url,
            headers=headers,
            ssl=verify_ssl,
        )

        # Create persistent GQL client that manages the transport lifecycle
        # This avoids "already connected" errors by keeping client alive
        self.gql_client: Client | None = None
        self.gql_ws_client: Client | None = None
        # Session for maintaining persistent connection
        self._session = None
        self._ws_session = None

        # Store transport configuration for creating clients
        self.transport_config: TransportConfig = {
            "url": str(self.url),
            "headers": headers,
            "ssl": bool(verify_ssl),
            "timeout": 30,
        }

        self.log.debug(f"Using Stash endpoint at {self.url}")
        self.log.debug(f"Using WebSocket endpoint at {self.ws_url}")
        self.log.debug(f"Client headers: {headers}")
        self.log.debug(f"SSL verification: {verify_ssl}")

        # Create persistent GQL client
        # Note: Schema fetching is disabled due to Stash's deprecated required arguments
        # which violate GraphQL spec and cause validation errors in the gql library.
        # See: https://github.com/stashapp/stash/issues
        self.log.debug("Creating persistent GQL client (schema validation disabled)...")

        # Create client with schema fetching DISABLED to avoid Stash's
        # deprecated required arguments validation errors
        self.gql_client = Client(
            transport=self.http_transport,
            fetch_schema_from_transport=False,  # Disabled due to Stash schema issues
        )
        self.gql_ws_client = Client(
            transport=self.ws_transport,
            fetch_schema_from_transport=False,  # Disabled due to Stash schema issues
        )

        # Schema is intentionally not fetched to avoid validation errors
        self.schema = None

        # Create a persistent session for the client
        # This maintains a single connection across multiple queries
        self._session = await self.gql_client.connect_async(reconnecting=False)
        self._ws_session = await self.gql_ws_client.connect_async(reconnecting=False)
        self.log.debug("GQL client session established")

        # Set backward compatibility alias (same object, not a new client)
        if self.gql_client is None:
            raise RuntimeError("GQL client initialization failed")  # pragma: no cover
        self.client = self.gql_client

        self._initialized = True

    @overload
    def _decode_result(self, type_: type[T], data: dict[str, Any]) -> T:
        """Decode GraphQL result dict to typed object (non-None data)."""

    @overload
    def _decode_result(self, type_: type[T], data: None) -> None:
        """Decode GraphQL result dict to typed object (None data)."""

    def _decode_result(self, type_: type[T], data: dict[str, Any] | None) -> T | None:
        """Decode GraphQL result dict to typed object, handling nested entities.

        This method automatically sanitizes GraphQL data and uses Pydantic's from_graphql()
        to properly construct nested entity types, triggering the identity map validator
        for entity caching.

        Args:
            type_: The target type to decode to
            data: Dictionary from GraphQL response (will be sanitized automatically)

        Returns:
            Typed instance with all nested entities properly constructed, or None if data is None

        Example:
            result = await self.execute(FIND_GROUPS_QUERY, {...})
            return self._decode_result(FindGroupsResultType, result["findGroups"])
        """
        if data is None:
            return None

        # Sanitize the data first (handles __typename removal, etc.)
        clean_data = sanitize_model_data(data)

        # Use from_graphql() for StashObject types, model_validate() for others
        if hasattr(type_, "from_graphql"):
            return type_.from_graphql(clean_data)  # type: ignore[attr-defined]
        # For non-StashObject types (like result types), use model_validate
        return type_.model_validate(clean_data)  # type: ignore[attr-defined]

    async def _cleanup_connection_resources(self) -> None:
        """Clean up persistent connection resources."""
        # Close the persistent GQL session first
        if hasattr(self, "_session") and self._session:
            self._session = None
        if hasattr(self, "_ws_session") and self._ws_session:
            self._ws_session = None

        # Close the persistent GQL client if it exists
        if hasattr(self, "gql_client") and self.gql_client:
            try:
                await self.gql_client.close_async()
            except Exception as e:
                if hasattr(self, "log"):
                    self.log.debug(f"Error closing GQL client: {e}")
            self.gql_client = None
        if hasattr(self, "gql_ws_client") and self.gql_ws_client:
            try:
                await self.gql_ws_client.close_async()
            except Exception as e:
                if hasattr(self, "log"):
                    self.log.debug(f"Error closing GQL WS client: {e}")
            self.gql_ws_client = None

    def _ensure_initialized(self) -> None:
        """Ensure transport configuration is properly initialized."""
        if not hasattr(self, "log"):
            self.log = client_logger

        if not hasattr(self, "_initialized") or not self._initialized:
            raise RuntimeError("Client not initialized - use get_client() first")

        if not hasattr(self, "transport_config"):
            raise RuntimeError("Transport configuration not initialized")

        if not hasattr(self, "url"):
            raise RuntimeError("URL not initialized")

    def _handle_gql_error(self, e: Exception) -> None:
        """Handle gql errors with appropriate error messages.

        Raises:
            StashGraphQLError: For GraphQL query/validation errors
            StashServerError: For server-side errors (500, 503, etc.)
            StashConnectionError: For network/connection errors
            StashError: For unexpected errors
        """
        if isinstance(e, TransportQueryError):
            # GraphQL query error (e.g. validation error)
            raise StashGraphQLError(f"GraphQL query error: {e.errors}")
        if isinstance(e, TransportServerError):
            # Server error (e.g. 500)
            raise StashServerError(f"GraphQL server error: {e}")
        if isinstance(e, TransportError):
            # Network/connection error
            raise StashConnectionError(f"Failed to connect to {self.url}: {e}")
        if isinstance(e, asyncio.TimeoutError):
            raise StashConnectionError(f"Request to {self.url} timed out")
        raise StashError(f"Unexpected error during request ({type(e).__name__}): {e}")

    async def execute(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
        result_type: type[T] | None = None,
    ) -> dict[str, Any] | T:
        """Execute GraphQL query with proper initialization and error handling.

        Args:
            query: GraphQL query string
            variables: Optional variables for query
            result_type: Optional type to deserialize result to using Pydantic's from_graphql()

        Returns:
            Query result as dictionary, or typed object if result_type provided

        Raises:
            ValueError: If query validation fails or execution fails
        """
        self._ensure_initialized()
        try:
            # Process variables first
            processed_vars = self._convert_datetime(variables or {})

            # Parse query to catch basic syntax errors
            # Note: Schema validation is disabled due to Stash's deprecated required arguments
            try:
                operation = gql(query)
            except Exception as e:
                self.log.error(f"GraphQL syntax error: {e}")
                self.log.error(f"Failed query: \n{query}")
                self.log.error(f"Variables: {processed_vars}")
                raise ValueError(f"Invalid GraphQL query syntax: {e}")

            # Use persistent GQL session with connection pooling
            # This allows HTTP/2 multiplexing and avoids "already connected" errors
            if not self._session:
                raise RuntimeError(
                    "GQL session not initialized - call initialize() first"
                )

            # Set variable_values on the query object (gql 4.x pattern)
            # This avoids deprecation warning for passing variable_values to execute()
            operation.variable_values = processed_vars

            # Execute using the persistent session
            # The session maintains a single connection for all queries
            result = await self._session.execute(operation)
            result_dict = dict(result)

            # If result_type is specified, deserialize to that type
            if result_type is not None:
                return self._parse_result_to_type(result_dict, result_type)

            return result_dict

        except Exception as e:
            self._handle_gql_error(e)  # This will raise ValueError
            raise RuntimeError("Unexpected execution path")  # pragma: no cover

    def _parse_result_to_type(
        self, result_dict: dict[str, Any], result_type: type[T]
    ) -> T:
        """Parse GraphQL result dictionary to specified type.

        Args:
            result_dict: GraphQL response dictionary
            result_type: Type to deserialize result to (can be Model, list[Model], etc.)

        Returns:
            Deserialized instance of result_type
        """
        # GraphQL response structure: result contains one key (query/mutation name)
        # Extract the single field data (e.g., result["findScenes"])
        if isinstance(result_dict, dict) and len(result_dict) == 1:
            field_name = next(iter(result_dict.keys()))
            field_data = result_dict[field_name]

            # If GraphQL returned None, return None (don't create empty object)
            if field_data is None:
                return None  # type: ignore[return-value]

            # Check if result_type is a list type (e.g., list[Studio])
            origin = get_origin(result_type)
            if origin is list:
                # Extract the element type from list[ElementType]
                args = get_args(result_type)
                if args and isinstance(field_data, list):
                    element_type = args[0]
                    # Deserialize each item in the list
                    return [
                        (
                            element_type.from_graphql(item)
                            if hasattr(element_type, "from_graphql")
                            else element_type.model_validate(item)
                        )
                        for item in field_data
                    ]  # type: ignore[return-value]
                return field_data  # type: ignore[return-value]

            # Use from_graphql() for StashObject types, model_validate() for others
            if hasattr(result_type, "from_graphql"):
                return result_type.from_graphql(field_data)  # type: ignore[attr-defined]
            # For non-StashObject types (like result types), use model_validate
            return result_type.model_validate(field_data)  # type: ignore[attr-defined]

        # Fallback for unexpected response structure
        self.log.warning(
            f"Unexpected GraphQL response structure: {list(result_dict.keys())}"
        )
        if hasattr(result_type, "from_graphql"):
            return result_type.from_graphql(result_dict)  # type: ignore[attr-defined]
        return result_type.model_validate(result_dict)  # type: ignore[attr-defined]

    def _convert_datetime(self, obj: Any) -> Any:
        """Convert datetime objects to ISO format strings and filter out UNSET values."""
        # Filter out UNSET sentinel values (should not be sent to GraphQL)
        if isinstance(obj, UnsetType):
            return None  # Or skip entirely in dict comprehension
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, dict):
            # Filter out UNSET values from dictionaries
            return {
                k: self._convert_datetime(v)
                for k, v in obj.items()
                if not isinstance(v, UnsetType)
            }
        if isinstance(obj, (list, tuple)):
            return [
                self._convert_datetime(x) for x in obj if not isinstance(x, UnsetType)
            ]
        return obj

    def _parse_obj_for_ID(self, param: Any, str_key: str = "name") -> Any:
        if isinstance(param, str):
            try:
                return int(param)
            except ValueError:
                return {str_key: param.strip()}
        elif isinstance(param, dict):
            if param.get("stored_id"):
                return int(param["stored_id"])
            if param.get("id"):
                return int(param["id"])
        return param

    async def close(self) -> None:
        """Close the HTTP client and clean up resources.

        This method attempts to clean up all resources but continues even if errors occur.
        Any errors during cleanup are logged but not propagated.

        Examples:
            Manual cleanup:
            ```python
            client = StashClient("http://localhost:9999/graphql")
            try:
                # Use client...
                scene = await client.find_scene("123")
            finally:
                await client.close()
            ```

            Using async context manager:
            ```python
            async with StashClient("http://localhost:9999/graphql") as client:
                # Client will be automatically closed after this block
                scene = await client.find_scene("123")
            ```
        """
        try:
            # Close GQL client first
            if (
                hasattr(self, "client")
                and self.client
                and hasattr(self.client, "close_async")
            ):
                try:
                    await self.client.close_async()
                except Exception as e:
                    # Just log any errors during client.close_async and continue
                    self.log.debug(
                        f"Non-critical error during client.close_async(): {e}"
                    )

            # Close transports
            if hasattr(self, "http_transport") and hasattr(
                self.http_transport, "close"
            ):
                await self.http_transport.close()
            if hasattr(self, "ws_transport") and hasattr(self.ws_transport, "close"):
                await self.ws_transport.close()

            # Clean up persistent connection resources
            await self._cleanup_connection_resources()

        except Exception as e:
            # Just log the error and continue
            self.log.warning(f"Non-critical error during client cleanup: {e}")

    async def __aenter__(self) -> "StashClientBase":
        """Enter async context manager."""
        if not self._initialized:
            await self.initialize()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit async context manager."""
        await self.close()
