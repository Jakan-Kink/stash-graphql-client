"""Base Stash client class."""

import asyncio
import time
from datetime import datetime
from types import TracebackType
from typing import Any, TypedDict, TypeVar

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

from .. import fragments
from ..errors import StashSystemNotReadyError
from ..logging import client_logger
from ..types import (
    AutoTagMetadataOptions,
    ConfigDefaultSettingsResult,
    FindJobInput,
    GenerateMetadataInput,
    GenerateMetadataOptions,
    Job,
    JobStatus,
    ScanMetadataInput,
    ScanMetadataOptions,
)
from ..types.enums import SystemStatusEnum
from ..types.metadata import SystemStatus


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
        if host == "0.0.0.0":  # nosec B104  # Converting all-interfaces to localhost
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
        """Handle gql errors with appropriate error messages."""
        if isinstance(e, TransportQueryError):
            # GraphQL query error (e.g. validation error)
            raise ValueError(f"GraphQL query error: {e.errors}")
        if isinstance(e, TransportServerError):
            # Server error (e.g. 500)
            raise ValueError(f"GraphQL server error: {e}")
        if isinstance(e, TransportError):
            # Network/connection error
            raise ValueError(f"Failed to connect to {self.url}: {e}")
        if isinstance(e, asyncio.TimeoutError):
            raise ValueError(f"Request to {self.url} timed out")
        raise ValueError(f"Unexpected error during request ({type(e).__name__}): {e}")

    async def execute(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute GraphQL query with proper initialization and error handling.

        Args:
            query: GraphQL query string
            variables: Optional variables for query

        Returns:
            Query result as dictionary

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

            # Execute using the persistent session
            # The session maintains a single connection for all queries
            # Set variable_values on the operation (gql 4.0+ pattern)
            operation.variable_values = processed_vars
            result = await self._session.execute(operation)
            return dict(result)

        except Exception as e:
            self._handle_gql_error(e)  # This will raise ValueError
            raise RuntimeError("Unexpected execution path")  # pragma: no cover

    def _convert_datetime(self, obj: Any) -> Any:
        """Convert datetime objects to ISO format strings."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, dict):
            return {k: self._convert_datetime(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [self._convert_datetime(x) for x in obj]
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

    async def get_configuration_defaults(self) -> ConfigDefaultSettingsResult:
        """Get default configuration settings."""
        try:
            result = await self.execute(fragments.CONFIG_DEFAULTS_QUERY)

            if not result:
                self.log.warning(
                    "No result from configuration query, using hardcoded defaults"
                )
                return ConfigDefaultSettingsResult(
                    scan=ScanMetadataOptions(
                        rescan=False,
                        scan_generate_covers=True,
                        scan_generate_previews=True,
                        scan_generate_image_previews=True,
                        scan_generate_sprites=True,
                        scan_generate_phashes=True,
                        scan_generate_thumbnails=True,
                        scan_generate_clip_previews=True,
                    ),
                    auto_tag=AutoTagMetadataOptions(),
                    generate=GenerateMetadataOptions(),
                    delete_file=False,
                    delete_generated=False,
                )

            if defaults := result.get("configuration", {}).get("defaults"):
                # Pydantic automatically handles camelCase → snake_case mapping via Field aliases
                # and deserializes nested dicts to nested models
                return ConfigDefaultSettingsResult(**defaults)

            self.log.warning("No defaults in response, using hardcoded values")
            return ConfigDefaultSettingsResult(
                scan=ScanMetadataOptions(
                    rescan=False,
                    scan_generate_covers=True,
                    scan_generate_previews=True,
                    scan_generate_image_previews=True,
                    scan_generate_sprites=True,
                    scan_generate_phashes=True,
                    scan_generate_thumbnails=True,
                    scan_generate_clip_previews=True,
                ),
                auto_tag=AutoTagMetadataOptions(),
                generate=GenerateMetadataOptions(),
                delete_file=False,
                delete_generated=False,
            )
        except Exception as e:
            self.log.error(f"Failed to get configuration defaults: {e}")
            raise

    async def metadata_generate(
        self,
        options: GenerateMetadataOptions | dict[str, Any] | None = None,
        input_data: GenerateMetadataInput | dict[str, Any] | None = None,
    ) -> str:
        """Generate metadata.

        Args:
            options: GenerateMetadataOptions object or dictionary of what to generate:
                - covers: bool - Generate covers
                - sprites: bool - Generate sprites
                - previews: bool - Generate previews
                - imagePreviews: bool - Generate image previews
                - previewOptions: GeneratePreviewOptionsInput
                    - previewSegments: int - Number of segments in a preview file
                    - previewSegmentDuration: float - Duration of each segment in seconds
                    - previewExcludeStart: str - Duration to exclude from start
                    - previewExcludeEnd: str - Duration to exclude from end
                    - previewPreset: PreviewPreset - Preset when generating preview
                - markers: bool - Generate markers
                - markerImagePreviews: bool - Generate marker image previews
                - markerScreenshots: bool - Generate marker screenshots
                - transcodes: bool - Generate transcodes
                - forceTranscodes: bool - Generate transcodes even if not required
                - phashes: bool - Generate phashes
                - interactiveHeatmapsSpeeds: bool - Generate interactive heatmaps speeds
                - imageThumbnails: bool - Generate image thumbnails
                - clipPreviews: bool - Generate clip previews
            input_data: Optional GenerateMetadataInput object or dictionary to specify what to process:
                - sceneIDs: list[str] - List of scene IDs to generate for (default: all)
                - markerIDs: list[str] - List of marker IDs to generate for (default: all)
                - overwrite: bool - Overwrite existing media (default: False)

        Returns:
            Job ID for the generation task

        Raises:
            ValueError: If the input data is invalid
            gql.TransportError: If the request fails
        """
        try:
            # Convert GenerateMetadataOptions to dict if needed
            options_dict = {}
            if options is not None:
                if isinstance(options, GenerateMetadataOptions):
                    options_dict = {
                        k: v for k, v in vars(options).items() if v is not None
                    }
                else:
                    options_dict = options

            # Convert GenerateMetadataInput to dict if needed
            input_dict = {}
            if input_data is not None:
                if isinstance(input_data, GenerateMetadataInput):
                    input_dict = {
                        k: v for k, v in vars(input_data).items() if v is not None
                    }
                else:
                    input_dict = input_data

            # Combine options and input data
            variables = {"input": {**options_dict, **input_dict}}

            # Execute mutation with combined input
            result = await self.execute(fragments.METADATA_GENERATE_MUTATION, variables)

            if not isinstance(result, dict):
                raise ValueError("Invalid response format from server")

            job_id = result.get("metadataGenerate")
            if not job_id:
                raise ValueError("No job ID returned from server")

            return str(job_id)

        except Exception as e:
            self.log.error(f"Failed to generate metadata: {e}")
            raise

    async def metadata_scan(
        self,
        paths: list[str] | None = None,
        flags: dict[str, Any] | None = None,
    ) -> str:
        """Start a metadata scan job.

        Args:
            paths: List of paths to scan (empty for all paths)
            flags: Optional scan flags matching ScanMetadataInput schema:
                - rescan: bool
                - scanGenerateCovers: bool
                - scanGeneratePreviews: bool
                - scanGenerateImagePreviews: bool
                - scanGenerateSprites: bool
                - scanGeneratePhashes: bool
                - scanGenerateThumbnails: bool
                - scanGenerateClipPreviews: bool
                - filter: ScanMetaDataFilterInput

        Returns:
            Job ID for the scan operation
        """
        # Get scan input object with defaults from config
        if flags is None:
            flags = {}
        if paths is None:
            paths = []
        try:
            defaults = await self.get_configuration_defaults()
            scan_input = ScanMetadataInput(
                paths=paths,
                rescan=getattr(defaults.scan, "rescan", False),
                scan_generate_covers=getattr(
                    defaults.scan, "scan_generate_covers", True
                ),
                scan_generate_previews=getattr(
                    defaults.scan, "scan_generate_previews", True
                ),
                scan_generate_image_previews=getattr(
                    defaults.scan, "scan_generate_image_previews", True
                ),
                scan_generate_sprites=getattr(
                    defaults.scan, "scan_generate_sprites", True
                ),
                scan_generate_phashes=getattr(
                    defaults.scan, "scan_generate_phashes", True
                ),
                scan_generate_thumbnails=getattr(
                    defaults.scan, "scan_generate_thumbnails", True
                ),
                scan_generate_clip_previews=getattr(
                    defaults.scan, "scan_generate_clip_previews", True
                ),
            )
        except Exception as e:
            self.log.warning(
                f"Failed to get scan defaults: {e}, using hardcoded defaults"
            )
            scan_input = ScanMetadataInput(
                paths=paths,
                rescan=False,
                scan_generate_covers=True,
                scan_generate_previews=True,
                scan_generate_image_previews=True,
                scan_generate_sprites=True,
                scan_generate_phashes=True,
                scan_generate_thumbnails=True,
                scan_generate_clip_previews=True,
            )

        # Override with any provided flags
        if flags:
            for key, value in flags.items():
                setattr(scan_input, key, value)

        # Convert to dict for GraphQL
        variables = {"input": scan_input.__dict__}
        try:
            result = await self.execute(fragments.METADATA_SCAN_MUTATION, variables)
            job_id = result.get("metadataScan")
            if not job_id:
                raise ValueError("Failed to start metadata scan - no job ID returned")
            return str(job_id)
        except Exception as e:
            self.log.error(f"Failed to start metadata scan: {e}")
            raise ValueError(f"Failed to start metadata scan: {e}")

    async def find_job(self, job_id: str) -> Job | None:
        """Find a job by ID.

        Args:
            job_id: Job ID to find

        Returns:
            Job object if found, None otherwise

        Examples:
            Find a job and check its status:
            ```python
            job = await client.find_job("123")
            if job:
                print(f"Job status: {job.status}")
            ```
        """
        if not job_id:
            return None

        try:
            result = await self.execute(
                fragments.FIND_JOB_QUERY,
                {"input": FindJobInput(id=job_id).__dict__},
            )
            # First check if there are any GraphQL errors
            if "errors" in result:
                return None
            # Then check if we got a valid job back
            if job_data := result.get("findJob"):
                return Job(**job_data)
            return None
        except Exception as e:
            self.log.error(f"Failed to find job {job_id}: {e}")
            return None

    async def wait_for_job(
        self,
        job_id: str | int,
        status: JobStatus = JobStatus.FINISHED,
        period: float = 1.5,
        timeout: float = 120.0,
    ) -> bool | None:
        """Wait for a job to reach a specific status.

        Args:
            job_id: Job ID to wait for
            status: Status to wait for (default: JobStatus.FINISHED)
            period: Time between checks in seconds (default: 1.5)
            timeout: Maximum time to wait in seconds (default: 120)

        Returns:
            True if job reached desired status
            False if job finished with different status
            None if job not found

        Raises:
            TimeoutError: If timeout is reached
            ValueError: If job is not found
        """
        if not job_id:
            return None

        timeout_value = time.time() + timeout
        while time.time() < timeout_value:
            job = await self.find_job(str(job_id))
            if not isinstance(job, Job):
                raise ValueError(f"Job {job_id} not found")

            # Only log through stash's logger
            self.log.info(
                f"Job {job_id} - Status: {job.status}, Progress: {job.progress}%"
            )

            # Check for desired state
            if job.status == status:
                return True
            if job.status in [JobStatus.FINISHED, JobStatus.CANCELLED]:
                return False

            await asyncio.sleep(period)

        raise TimeoutError(f"Timeout waiting for job {job_id} to reach status {status}")

    async def get_system_status(self) -> SystemStatus | None:
        """Get the current Stash system status.

        Returns:
            SystemStatus object containing system information and status
            None if the query fails

        Examples:
            Check system status:
            ```python
            status = await client.get_system_status()
            if status:
                print(f"System status: {status.status}")
                print(f"Database path: {status.database_path}")
            ```
        """
        try:
            result = await self.execute(fragments.SYSTEM_STATUS_QUERY)
            if status_data := result.get("systemStatus"):
                return SystemStatus(**status_data)
            return None
        except Exception as e:
            self.log.error(f"Failed to get system status: {e}")
            return None

    async def check_system_ready(self) -> None:
        """Check if the Stash system is ready for processing.

        This method queries the system status and raises an exception if the
        system is not in OK status. It should be called before starting any
        processing operations.

        Raises:
            StashSystemNotReadyError: If system status is SETUP or NEEDS_MIGRATION
            RuntimeError: If system status cannot be determined

        Examples:
            Validate system before processing:
            ```python
            try:
                await client.check_system_ready()
                # Safe to proceed with processing
                await client.metadata_scan()
            except StashSystemNotReadyError as e:
                print(f"System not ready: {e}")
                # Handle migration or setup
            ```
        """
        status = await self.get_system_status()

        if status is None:
            raise RuntimeError(
                "Unable to determine Stash system status. "
                "Cannot proceed with processing."
            )

        # Check for blocking states
        if status.status == SystemStatusEnum.NEEDS_MIGRATION:
            raise StashSystemNotReadyError(
                status="NEEDS_MIGRATION",
                message=(
                    "Stash database requires migration. "
                    "Please run the database migration before starting processing. "
                    "All processing is blocked until migration is completed."
                ),
            )

        if status.status == SystemStatusEnum.SETUP:
            raise StashSystemNotReadyError(
                status="SETUP",
                message=(
                    "Stash requires initial setup. "
                    "Please complete the setup wizard before starting processing."
                ),
            )

        # System is OK, log status for debugging
        self.log.debug(
            f"Stash system ready - Status: {status.status}, "
            f"Database: {status.database_path}, "
            f"App Schema: {status.app_schema}"
        )

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
