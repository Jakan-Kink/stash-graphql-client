"""Stash client module."""

from typing import Any

from .. import fragments
from ..logging import client_logger
from .base import StashClientBase
from .mixins.config import ConfigClientMixin
from .mixins.file import FileClientMixin
from .mixins.filter import FilterClientMixin
from .mixins.gallery import GalleryClientMixin
from .mixins.group import GroupClientMixin
from .mixins.image import ImageClientMixin
from .mixins.jobs import JobsClientMixin
from .mixins.marker import MarkerClientMixin
from .mixins.metadata import MetadataClientMixin
from .mixins.not_implemented import NotImplementedClientMixin
from .mixins.package import PackageClientMixin
from .mixins.performer import PerformerClientMixin
from .mixins.plugin import PluginClientMixin
from .mixins.scene import SceneClientMixin
from .mixins.scraper import ScraperClientMixin
from .mixins.studio import StudioClientMixin
from .mixins.subscription import SubscriptionClientMixin
from .mixins.system_query import SystemQueryClientMixin
from .mixins.tag import TagClientMixin
from .mixins.version import VersionClientMixin
from .utils import sanitize_model_data


class StashClient(
    StashClientBase,  # Base class first to provide execute()
    ConfigClientMixin,
    FileClientMixin,
    FilterClientMixin,
    GalleryClientMixin,
    GroupClientMixin,
    ImageClientMixin,
    JobsClientMixin,
    MarkerClientMixin,
    MetadataClientMixin,
    PackageClientMixin,
    PerformerClientMixin,
    PluginClientMixin,
    SceneClientMixin,
    ScraperClientMixin,
    StudioClientMixin,
    SubscriptionClientMixin,
    SystemQueryClientMixin,
    TagClientMixin,
    VersionClientMixin,
    NotImplementedClientMixin,  # LAST: Fallback for unimplemented methods only
):
    """Full Stash client combining all functionality."""

    # Add fragments to satisfy the protocol
    fragments: Any

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
        # Set initial state
        self._initialized = False
        self._init_args = (conn, verify_ssl)

        # Set up logging early
        self.log = conn.get("Logger", client_logger) if conn else client_logger

        # Initialize fragments module
        self.fragments = fragments

        # Set up URL components
        conn = conn or {}
        scheme = conn.get("Scheme", "http")
        host = conn.get("Host", "localhost")
        if host == "0.0.0.0":  # nosec B104  # noqa: S104  # Converting all-interfaces to localhost
            host = "127.0.0.1"
        port = conn.get("Port", 9999)
        self.url = f"{scheme}://{host}:{port}/graphql"

        # Set up HTTP client
        headers = {}
        if api_key := conn.get("ApiKey"):
            self.log.debug("Using API key authentication")
            headers["ApiKey"] = api_key

        # Initialize base class
        super().__init__(conn=conn, verify_ssl=verify_ssl)

        # Initialize all mixins
        NotImplementedClientMixin.__init__(self)
        ConfigClientMixin.__init__(self)
        FileClientMixin.__init__(self)
        FilterClientMixin.__init__(self)
        GalleryClientMixin.__init__(self)
        GroupClientMixin.__init__(self)
        ImageClientMixin.__init__(self)
        JobsClientMixin.__init__(self)
        MarkerClientMixin.__init__(self)
        MetadataClientMixin.__init__(self)
        PackageClientMixin.__init__(self)
        PerformerClientMixin.__init__(self)
        PluginClientMixin.__init__(self)
        SceneClientMixin.__init__(self)
        ScraperClientMixin.__init__(self)
        StudioClientMixin.__init__(self)
        SubscriptionClientMixin.__init__(self)
        TagClientMixin.__init__(self)


__all__ = ["StashClient", "sanitize_model_data"]
