"""Client mixins."""

from .config import ConfigClientMixin
from .file import FileClientMixin
from .filter import FilterClientMixin
from .gallery import GalleryClientMixin
from .group import GroupClientMixin
from .image import ImageClientMixin
from .jobs import JobsClientMixin
from .marker import MarkerClientMixin
from .metadata import MetadataClientMixin
from .not_implemented import NotImplementedClientMixin
from .package import PackageClientMixin
from .performer import PerformerClientMixin
from .plugin import PluginClientMixin
from .protocols import StashClientProtocol
from .scene import SceneClientMixin
from .scraper import ScraperClientMixin
from .studio import StudioClientMixin
from .subscription import AsyncIteratorWrapper, SubscriptionClientMixin
from .system_query import SystemQueryClientMixin
from .tag import TagClientMixin
from .version import VersionClientMixin


__all__ = [
    "AsyncIteratorWrapper",
    "ConfigClientMixin",
    "FileClientMixin",
    "FilterClientMixin",
    "GalleryClientMixin",
    "GroupClientMixin",
    "ImageClientMixin",
    "JobsClientMixin",
    "MarkerClientMixin",
    "MetadataClientMixin",
    "NotImplementedClientMixin",
    "PackageClientMixin",
    "PerformerClientMixin",
    "PluginClientMixin",
    "SceneClientMixin",
    "ScraperClientMixin",
    "StashClientProtocol",
    "StudioClientMixin",
    "SubscriptionClientMixin",
    "SystemQueryClientMixin",
    "TagClientMixin",
    "VersionClientMixin",
]
