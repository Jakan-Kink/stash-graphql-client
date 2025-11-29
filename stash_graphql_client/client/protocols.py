"""Protocol definitions for Stash client."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

from gql import Client
from gql.client import AsyncClientSession, ReconnectingAsyncClientSession
from gql.transport.httpx import HTTPXAsyncTransport
from gql.transport.websockets import WebsocketsTransport

from ..types import Job, JobStatus


if TYPE_CHECKING:
    from loguru import Logger


class StashClientProtocol(Protocol):
    """Protocol defining the interface expected by Stash client mixins.

    This protocol defines all attributes and methods that mixin classes
    can expect to be available on the client instance.
    """

    # Properties
    log: Logger
    fragments: Any  # Module containing GraphQL fragments    # GQL clients (kept open for persistent connections)
    client: Client  # Backward compatibility alias for gql_client
    gql_client: Client | None
    gql_ws_client: Client | None

    # Sessions (persistent connections)
    _session: AsyncClientSession | ReconnectingAsyncClientSession | None
    _ws_session: ReconnectingAsyncClientSession | AsyncClientSession | None

    # Transports
    http_transport: HTTPXAsyncTransport
    ws_transport: WebsocketsTransport

    # Core methods
    async def execute(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a GraphQL query or mutation.

        Args:
            query: GraphQL query or mutation string
            variables: Optional query variables dictionary

        Returns:
            Query response data dictionary
        """
        ...

    def _parse_obj_for_ID(self, param: Any, str_key: str = "name") -> Any:
        """Parse an object into an ID.

        Args:
            param: Object to parse (str, int, dict)
            str_key: Key to use when converting string to dict

        Returns:
            Parsed ID or filter dict
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
