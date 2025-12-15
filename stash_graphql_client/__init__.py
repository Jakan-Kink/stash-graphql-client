"""Stash GraphQL Client - Async Python client for Stash media server.

This library provides a fully async GraphQL client for interacting with
Stash (https://stashapp.cc), a self-hosted media organizer.

Features:
- Async-first design with gql + HTTPXAsyncTransport + WebsocketsTransport
- Pydantic types for all Stash GraphQL schema objects
- Full CRUD operations for all entity types
- Job management and metadata scanning
- GraphQL subscription support for real-time updates

Example:
    >>> from stash_graphql_client import StashClient, StashContext
    >>>
    >>> async with StashContext(conn={"Host": "localhost", "Port": 9999}) as client:
    ...     studios = await client.find_studios()
    ...     print(f"Found {studios.count} studios")
"""

from stash_graphql_client.client import StashClient
from stash_graphql_client.context import StashContext
from stash_graphql_client.logging import (
    client_logger,
    configure_logging,
    processing_logger,
    stash_logger,
)
from stash_graphql_client.store import CacheEntry, StashEntityStore

# Re-export commonly used types
from stash_graphql_client.types import (
    # Base types
    BulkUpdateIds,
    BulkUpdateStrings,
    # Core types
    Gallery,
    GalleryCreateInput,
    GalleryUpdateInput,
    # Metadata types
    GenerateMetadataInput,
    GenerateMetadataOptions,
    Group,
    GroupCreateInput,
    GroupUpdateInput,
    Image,
    Job,
    JobStatus,
    Performer,
    PerformerCreateInput,
    PerformerUpdateInput,
    ScanMetadataInput,
    ScanMetadataOptions,
    Scene,
    SceneCreateInput,
    SceneUpdateInput,
    StashObject,
    Studio,
    StudioCreateInput,
    StudioUpdateInput,
    Tag,
    TagCreateInput,
    TagUpdateInput,
)
from stash_graphql_client.utils import ScrapeParser


__version__ = "0.1.0"

__all__ = [
    # Version
    "__version__",
    # Client
    "StashClient",
    "StashContext",
    # Store
    "StashEntityStore",
    "CacheEntry",
    # Utils
    "ScrapeParser",
    # Logging
    "stash_logger",
    "client_logger",
    "processing_logger",
    "configure_logging",
    # Core types
    "Gallery",
    "GalleryCreateInput",
    "GalleryUpdateInput",
    "Group",
    "GroupCreateInput",
    "GroupUpdateInput",
    "Image",
    "Job",
    "JobStatus",
    "Performer",
    "PerformerCreateInput",
    "PerformerUpdateInput",
    "Scene",
    "SceneCreateInput",
    "SceneUpdateInput",
    "Studio",
    "StudioCreateInput",
    "StudioUpdateInput",
    "Tag",
    "TagCreateInput",
    "TagUpdateInput",
    # Base types
    "BulkUpdateIds",
    "BulkUpdateStrings",
    "StashObject",
    # Metadata types
    "GenerateMetadataInput",
    "GenerateMetadataOptions",
    "ScanMetadataInput",
    "ScanMetadataOptions",
]
