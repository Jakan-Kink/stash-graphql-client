"""Enum types from schema."""

from __future__ import annotations

from enum import Enum


# Core enums
class GenderEnum(str, Enum):
    """Gender enum from schema."""

    MALE = "MALE"
    FEMALE = "FEMALE"
    TRANSGENDER_MALE = "TRANSGENDER_MALE"
    TRANSGENDER_FEMALE = "TRANSGENDER_FEMALE"
    INTERSEX = "INTERSEX"
    NON_BINARY = "NON_BINARY"


class CircumisedEnum(str, Enum):
    """Circumcision enum from schema."""

    CUT = "CUT"
    UNCUT = "UNCUT"


class BulkUpdateIdMode(str, Enum):
    """Bulk update mode enum from schema."""

    SET = "SET"
    ADD = "ADD"
    REMOVE = "REMOVE"


# Filter enums
class SortDirectionEnum(str, Enum):
    """Sort direction enum from schema."""

    ASC = "ASC"
    DESC = "DESC"


class ResolutionEnum(str, Enum):
    """Resolution enum from schema."""

    VERY_LOW = "VERY_LOW"  # 144p
    LOW = "LOW"  # 240p
    R360P = "R360P"  # 360p
    STANDARD = "STANDARD"  # 480p
    WEB_HD = "WEB_HD"  # 540p
    STANDARD_HD = "STANDARD_HD"  # 720p
    FULL_HD = "FULL_HD"  # 1080p
    QUAD_HD = "QUAD_HD"  # 1440p
    FOUR_K = "FOUR_K"  # 4K
    FIVE_K = "FIVE_K"  # 5K
    SIX_K = "SIX_K"  # 6K
    SEVEN_K = "SEVEN_K"  # 7K
    EIGHT_K = "EIGHT_K"  # 8K
    HUGE = "HUGE"  # 8K+


class OrientationEnum(str, Enum):
    """Orientation enum from schema."""

    LANDSCAPE = "LANDSCAPE"
    PORTRAIT = "PORTRAIT"
    SQUARE = "SQUARE"


class CriterionModifier(str, Enum):
    """Criterion modifier enum from schema."""

    EQUALS = "EQUALS"  # =
    NOT_EQUALS = "NOT_EQUALS"  # !=
    GREATER_THAN = "GREATER_THAN"  # >
    LESS_THAN = "LESS_THAN"  # <
    IS_NULL = "IS_NULL"  # IS NULL
    NOT_NULL = "NOT_NULL"  # IS NOT NULL
    INCLUDES_ALL = "INCLUDES_ALL"  # INCLUDES ALL
    INCLUDES = "INCLUDES"
    EXCLUDES = "EXCLUDES"
    MATCHES_REGEX = "MATCHES_REGEX"  # MATCHES REGEX
    NOT_MATCHES_REGEX = "NOT_MATCHES_REGEX"  # NOT MATCHES REGEX
    BETWEEN = "BETWEEN"  # >= AND <=
    NOT_BETWEEN = "NOT_BETWEEN"  # < OR >


class FilterMode(str, Enum):
    """Filter mode enum from schema."""

    SCENES = "SCENES"
    PERFORMERS = "PERFORMERS"
    STUDIOS = "STUDIOS"
    GALLERIES = "GALLERIES"
    SCENE_MARKERS = "SCENE_MARKERS"
    MOVIES = "MOVIES"
    GROUPS = "GROUPS"
    TAGS = "TAGS"
    IMAGES = "IMAGES"


# Config enums
class StreamingResolutionEnum(str, Enum):
    """Streaming resolution enum from schema."""

    LOW = "LOW"  # 240p
    STANDARD = "STANDARD"  # 480p
    STANDARD_HD = "STANDARD_HD"  # 720p
    FULL_HD = "FULL_HD"  # 1080p
    FOUR_K = "FOUR_K"  # 4k
    ORIGINAL = "ORIGINAL"  # Original


class PreviewPreset(str, Enum):
    """Preview preset enum from schema."""

    ULTRAFAST = "ultrafast"  # X264_ULTRAFAST
    VERYFAST = "veryfast"  # X264_VERYFAST
    FAST = "fast"  # X264_FAST
    MEDIUM = "medium"  # X264_MEDIUM
    SLOW = "slow"  # X264_SLOW
    SLOWER = "slower"  # X264_SLOWER
    VERYSLOW = "veryslow"  # X264_VERYSLOW


class HashAlgorithm(str, Enum):
    """Hash algorithm enum from schema."""

    MD5 = "MD5"
    OSHASH = "OSHASH"  # oshash


class BlobsStorageType(str, Enum):
    """Blobs storage type enum from schema."""

    DATABASE = "DATABASE"  # Database
    FILESYSTEM = "FILESYSTEM"  # Filesystem


class ImageLightboxDisplayMode(str, Enum):
    """Image lightbox display mode enum from schema."""

    ORIGINAL = "ORIGINAL"
    FIT_XY = "FIT_XY"
    FIT_X = "FIT_X"


class ImageLightboxScrollMode(str, Enum):
    """Image lightbox scroll mode enum from schema."""

    ZOOM = "ZOOM"
    PAN_Y = "PAN_Y"


# Metadata enums
class IdentifyFieldStrategy(str, Enum):
    """Strategy for identifying fields from schema/types/metadata.graphql."""

    IGNORE = "IGNORE"  # Never sets the field value
    MERGE = "MERGE"  # For multi-value fields, merge with existing. For single-value fields, ignore if already set
    OVERWRITE = "OVERWRITE"  # Always replaces the value if a value is found


class ImportDuplicateEnum(str, Enum):
    """Import duplicate behavior from schema/types/metadata.graphql."""

    IGNORE = "IGNORE"
    OVERWRITE = "OVERWRITE"
    FAIL = "FAIL"


class ImportMissingRefEnum(str, Enum):
    """Import missing reference behavior from schema/types/metadata.graphql."""

    IGNORE = "IGNORE"
    FAIL = "FAIL"
    CREATE = "CREATE"


class SystemStatusEnum(str, Enum):
    """System status enum from schema/types/metadata.graphql."""

    SETUP = "SETUP"
    NEEDS_MIGRATION = "NEEDS_MIGRATION"
    OK = "OK"


# Job enums
class JobStatus(str, Enum):
    """Job status enum from schema/types/job.graphql."""

    READY = "READY"
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"
    STOPPING = "STOPPING"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class JobStatusUpdateType(str, Enum):
    """Job status update type enum from schema/types/job.graphql."""

    ADD = "ADD"
    REMOVE = "REMOVE"
    UPDATE = "UPDATE"


# Logging enums
class LogLevel(str, Enum):
    """Log level enum from schema/types/logging.graphql."""

    TRACE = "Trace"
    DEBUG = "Debug"
    INFO = "Info"
    PROGRESS = "Progress"
    WARNING = "Warning"
    ERROR = "Error"


# Plugin enums
class PluginSettingTypeEnum(str, Enum):
    """Plugin setting type enum from schema/types/plugin.graphql."""

    STRING = "STRING"
    NUMBER = "NUMBER"
    BOOLEAN = "BOOLEAN"


# Scraper enums
class ScrapeContentType(str, Enum):
    """Scrape content type enum from schema/types/scraper.graphql."""

    GALLERY = "GALLERY"
    IMAGE = "IMAGE"
    MOVIE = "MOVIE"
    GROUP = "GROUP"
    PERFORMER = "PERFORMER"
    SCENE = "SCENE"


class ScrapeType(str, Enum):
    """Scrape type enum from schema/types/scraper.graphql."""

    NAME = "NAME"
    FRAGMENT = "FRAGMENT"
    URL = "URL"


# Package enums
class PackageType(str, Enum):
    """Package type enum from schema."""

    SCRAPER = "Scraper"
    PLUGIN = "Plugin"


class OnMultipleMatch(Enum):
    RETURN_NONE = 0
    RETURN_LIST = 1
    RETURN_FIRST = 2
