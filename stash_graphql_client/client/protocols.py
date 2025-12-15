"""Protocol definitions for Stash client."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, TypeVar, overload

from gql import Client
from gql.client import AsyncClientSession, ReconnectingAsyncClientSession
from gql.transport.httpx import HTTPXAsyncTransport
from gql.transport.websockets import WebsocketsTransport

from ..types import (
    ConfigDefaultSettingsResult,
    GenerateMetadataInput,
    GenerateMetadataOptions,
    Job,
    JobStatus,
    ScanMetadataInput,
    ScanMetadataOptions,
)
from ..types.metadata import SystemStatus


if TYPE_CHECKING:
    from loguru import Logger


T = TypeVar("T")


class StashClientProtocol(Protocol):
    """Protocol defining the interface expected by Stash client mixins.

    This protocol defines all attributes and methods that mixin classes
    can expect to be available on the client instance.
    """

    # Properties
    log: Logger
    url: str
    fragments: Any  # Module containing GraphQL fragments
    schema: Any  # GraphQL schema (None if disabled)

    # GQL clients (kept open for persistent connections)
    client: Client  # Backward compatibility alias for gql_client
    gql_client: Client | None
    gql_ws_client: Client | None

    # Sessions (persistent connections)
    _session: AsyncClientSession | ReconnectingAsyncClientSession | None
    _ws_session: ReconnectingAsyncClientSession | AsyncClientSession | None

    # Transports
    http_transport: HTTPXAsyncTransport
    ws_transport: WebsocketsTransport

    # Initialization
    async def initialize(self) -> None:
        """Initialize the client."""
        ...

    async def close(self) -> None:
        """Close the client and cleanup resources."""
        ...

    # Core execution methods
    async def execute(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
        result_type: type[T] | None = None,
    ) -> dict[str, Any] | T:
        """Execute a GraphQL query or mutation.

        Args:
            query: GraphQL query or mutation string
            variables: Optional query variables dictionary
            result_type: Optional type to deserialize result to

        Returns:
            Query response data dictionary or typed object
        """
        ...

    # Helper methods used by mixins
    def _parse_obj_for_ID(self, param: Any, str_key: str = "name") -> Any:
        """Parse an object into an ID.

        Args:
            param: Object to parse (str, int, dict)
            str_key: Key to use when converting string to dict

        Returns:
            Parsed ID or filter dict
        """
        ...

    @overload
    def _decode_result(self, type_: type[T], data: dict[str, Any]) -> T:
        """Decode GraphQL result dict to typed object (non-None data)."""
        ...

    @overload
    def _decode_result(self, type_: type[T], data: None) -> None:
        """Decode GraphQL result dict to typed object (None data)."""
        ...

    @overload
    def _decode_result(self, type_: type[T], data: dict[str, Any] | None) -> T | None:
        """Decode GraphQL result dict to typed object (optional data)."""
        ...

    def _decode_result(self, type_: type[T], data: dict[str, Any] | None) -> T | None:
        """Decode GraphQL result dict to typed object.

        Args:
            type_: Target type to decode to
            data: GraphQL response data dict (or None)

        Returns:
            Typed object instance, or None if data is None
        """
        ...

    def _convert_datetime(self, obj: Any) -> Any:
        """Convert datetime objects in data structure.

        Args:
            obj: Object to convert

        Returns:
            Converted object
        """
        ...

    # Configuration methods
    async def get_configuration_defaults(self) -> ConfigDefaultSettingsResult:
        """Get default configuration settings.

        Returns:
            Configuration defaults
        """
        ...

    # Metadata methods
    async def metadata_generate(
        self,
        options: GenerateMetadataOptions | dict[str, Any] | None = None,
        input_data: GenerateMetadataInput | dict[str, Any] | None = None,
    ) -> str:
        """Generate metadata.

        Args:
            options: Generation options
            input_data: Input data specifying what to process

        Returns:
            Job ID for the generation task
        """
        ...

    async def metadata_scan(
        self,
        options: ScanMetadataOptions | dict[str, Any] | None = None,
        input_data: ScanMetadataInput | dict[str, Any] | None = None,
    ) -> str:
        """Scan for new/changed media.

        Args:
            options: Scan options
            input_data: Input data specifying what to scan

        Returns:
            Job ID for the scan task
        """
        ...

    # Job methods
    async def find_job(self, job_id: str) -> Job | None:
        """Find a job by ID.

        Args:
            job_id: Job ID to find

        Returns:
            Job object if found, None otherwise
        """
        ...

    async def wait_for_job(
        self,
        job_id: str,
        status: JobStatus = JobStatus.FINISHED,
        period: float = 1.5,
        timeout: float = 120,
    ) -> bool | None:
        """Wait for a job to reach a specific status.

        Args:
            job_id: Job ID to wait for
            status: Status to wait for (default: JobStatus.FINISHED)
            period: Time between checks in seconds
            timeout: Maximum time to wait in seconds

        Returns:
            True if job reached desired status
            False if job finished with different status
            None if job not found
        """
        ...

    # System methods
    async def get_system_status(self) -> SystemStatus | None:
        """Get the current Stash system status.

        Returns:
            SystemStatus object or None if query fails
        """
        ...

    async def check_system_ready(self) -> None:
        """Check if the Stash system is ready for processing.

        Raises:
            StashSystemNotReadyError: If system is not ready
            RuntimeError: If status cannot be determined
        """
        ...
