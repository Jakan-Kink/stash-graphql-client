"""Configuration types from schema/types/config.graphql."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from .base import FromGraphQLMixin, StashInput
from .unset import UNSET, UnsetType


if TYPE_CHECKING:
    from .enums import (
        BlobsStorageType,
        HashAlgorithm,
        ImageLightboxDisplayMode,
        ImageLightboxScrollMode,
        PreviewPreset,
        StreamingResolutionEnum,
    )
    from .metadata import (
        AutoTagMetadataInput,
        AutoTagMetadataOptions,
        GenerateMetadataInput,
        GenerateMetadataOptions,
        ScanMetadataInput,
        ScanMetadataOptions,
    )


class SetupInput(StashInput):
    """Input for initial setup."""

    config_location: str | UnsetType = Field(
        default=UNSET, alias="configLocation"
    )  # String!
    stashes: list[StashConfigInput] | UnsetType = UNSET  # [StashConfigInput!]!
    sfw_content_mode: bool | None | UnsetType = Field(
        default=UNSET, alias="sfwContentMode"
    )  # Boolean
    database_file: str | UnsetType = Field(
        default=UNSET, alias="databaseFile"
    )  # String!
    generated_location: str | UnsetType = Field(
        default=UNSET, alias="generatedLocation"
    )  # String!
    cache_location: str | UnsetType = Field(
        default=UNSET, alias="cacheLocation"
    )  # String!
    store_blobs_in_database: bool | UnsetType = Field(
        default=UNSET, alias="storeBlobsInDatabase"
    )  # Boolean!
    blobs_location: str | UnsetType = Field(
        default=UNSET, alias="blobsLocation"
    )  # String!


class ConfigGeneralInput(StashInput):
    """Input for general configuration."""

    stashes: list[StashConfigInput] | None | UnsetType = UNSET  # [StashConfigInput!]
    database_path: str | None | UnsetType = Field(
        default=UNSET, alias="databasePath"
    )  # String
    backup_directory_path: str | None | UnsetType = Field(
        default=UNSET, alias="backupDirectoryPath"
    )  # String
    delete_trash_path: str | None | UnsetType = Field(
        default=UNSET, alias="deleteTrashPath"
    )  # String
    generated_path: str | None | UnsetType = Field(
        default=UNSET, alias="generatedPath"
    )  # String
    metadata_path: str | None | UnsetType = Field(
        default=UNSET, alias="metadataPath"
    )  # String
    scrapers_path: str | None | UnsetType = Field(
        default=UNSET, alias="scrapersPath"
    )  # String
    plugins_path: str | None | UnsetType = Field(
        default=UNSET, alias="pluginsPath"
    )  # String
    cache_path: str | None | UnsetType = Field(
        default=UNSET, alias="cachePath"
    )  # String
    blobs_path: str | None | UnsetType = Field(
        default=UNSET, alias="blobsPath"
    )  # String
    blobs_storage: BlobsStorageType | None | UnsetType = Field(
        default=UNSET, alias="blobsStorage"
    )  # BlobsStorageType
    ffmpeg_path: str | None | UnsetType = Field(
        default=UNSET, alias="ffmpegPath"
    )  # String
    ffprobe_path: str | None | UnsetType = Field(
        default=UNSET, alias="ffprobePath"
    )  # String
    calculate_md5: bool | None | UnsetType = Field(
        default=UNSET, alias="calculateMD5"
    )  # Boolean
    video_file_naming_algorithm: HashAlgorithm | None | UnsetType = Field(
        default=UNSET, alias="videoFileNamingAlgorithm"
    )  # HashAlgorithm
    parallel_tasks: int | None | UnsetType = Field(
        default=UNSET, alias="parallelTasks"
    )  # Int
    preview_audio: bool | None | UnsetType = Field(
        default=UNSET, alias="previewAudio"
    )  # Boolean
    preview_segments: int | None | UnsetType = Field(
        default=UNSET, alias="previewSegments"
    )  # Int
    preview_segment_duration: float | None | UnsetType = Field(
        default=UNSET, alias="previewSegmentDuration"
    )  # Float
    preview_exclude_start: str | None | UnsetType = Field(
        default=UNSET, alias="previewExcludeStart"
    )  # String
    preview_exclude_end: str | None | UnsetType = Field(
        default=UNSET, alias="previewExcludeEnd"
    )  # String
    preview_preset: PreviewPreset | None | UnsetType = Field(
        default=UNSET, alias="previewPreset"
    )  # PreviewPreset
    transcode_hardware_acceleration: bool | None | UnsetType = Field(
        default=UNSET, alias="transcodeHardwareAcceleration"
    )  # Boolean
    max_transcode_size: StreamingResolutionEnum | None | UnsetType = Field(
        default=UNSET, alias="maxTranscodeSize"
    )  # StreamingResolutionEnum
    max_streaming_transcode_size: StreamingResolutionEnum | None | UnsetType = Field(
        default=UNSET, alias="maxStreamingTranscodeSize"
    )  # StreamingResolutionEnum
    transcode_input_args: list[str] | None | UnsetType = Field(
        default=UNSET, alias="transcodeInputArgs"
    )  # [String!]
    transcode_output_args: list[str] | None | UnsetType = Field(
        default=UNSET, alias="transcodeOutputArgs"
    )  # [String!]
    live_transcode_input_args: list[str] | None | UnsetType = Field(
        default=UNSET, alias="liveTranscodeInputArgs"
    )  # [String!]
    live_transcode_output_args: list[str] | None | UnsetType = Field(
        default=UNSET, alias="liveTranscodeOutputArgs"
    )  # [String!]
    draw_funscript_heatmap_range: bool | None | UnsetType = Field(
        default=UNSET, alias="drawFunscriptHeatmapRange"
    )  # Boolean
    write_image_thumbnails: bool | None | UnsetType = Field(
        default=UNSET, alias="writeImageThumbnails"
    )  # Boolean
    create_image_clips_from_videos: bool | None | UnsetType = Field(
        default=UNSET, alias="createImageClipsFromVideos"
    )  # Boolean
    username: str | None | UnsetType = UNSET  # String
    password: str | None | UnsetType = UNSET  # String
    max_session_age: int | None | UnsetType = Field(
        default=UNSET, alias="maxSessionAge"
    )  # Int
    log_file: str | None | UnsetType = Field(default=UNSET, alias="logFile")  # String
    log_out: bool | None | UnsetType = Field(default=UNSET, alias="logOut")  # Boolean
    log_level: str | None | UnsetType = Field(default=UNSET, alias="logLevel")  # String
    log_access: bool | None | UnsetType = Field(
        default=UNSET, alias="logAccess"
    )  # Boolean
    log_file_max_size: int | None | UnsetType = Field(
        default=UNSET, alias="logFileMaxSize"
    )  # Int
    create_galleries_from_folders: bool | None | UnsetType = Field(
        default=UNSET, alias="createGalleriesFromFolders"
    )  # Boolean
    gallery_cover_regex: str | None | UnsetType = Field(
        default=UNSET, alias="galleryCoverRegex"
    )  # String
    video_extensions: list[str] | None | UnsetType = Field(
        default=UNSET, alias="videoExtensions"
    )  # [String!]
    image_extensions: list[str] | None | UnsetType = Field(
        default=UNSET, alias="imageExtensions"
    )  # [String!]
    gallery_extensions: list[str] | None | UnsetType = Field(
        default=UNSET, alias="galleryExtensions"
    )  # [String!]
    excludes: list[str] | None | UnsetType = UNSET  # [String!]
    image_excludes: list[str] | None | UnsetType = Field(
        default=UNSET, alias="imageExcludes"
    )  # [String!]
    custom_performer_image_location: str | None | UnsetType = Field(
        default=UNSET, alias="customPerformerImageLocation"
    )  # String
    stash_boxes: list[Any] | None | UnsetType = Field(
        default=UNSET, alias="stashBoxes"
    )  # [StashBoxInput!]
    python_path: str | None | UnsetType = Field(
        default=UNSET, alias="pythonPath"
    )  # String
    scraper_package_sources: list[Any] | None | UnsetType = Field(
        default=UNSET, alias="scraperPackageSources"
    )  # [PackageSourceInput!]
    plugin_package_sources: list[Any] | None | UnsetType = Field(
        default=UNSET, alias="pluginPackageSources"
    )  # [PackageSourceInput!]


class ConfigGeneralResult(FromGraphQLMixin, BaseModel):
    """Result type for general configuration."""

    stashes: list[StashConfig] | UnsetType = UNSET  # [StashConfig!]!
    database_path: str | UnsetType = Field(
        default=UNSET, alias="databasePath"
    )  # String!
    backup_directory_path: str | UnsetType = Field(
        default=UNSET, alias="backupDirectoryPath"
    )  # String!
    delete_trash_path: str | UnsetType = Field(
        default=UNSET, alias="deleteTrashPath"
    )  # String!
    generated_path: str | UnsetType = Field(
        default=UNSET, alias="generatedPath"
    )  # String!
    metadata_path: str | UnsetType = Field(
        default=UNSET, alias="metadataPath"
    )  # String!
    config_file_path: str | UnsetType = Field(
        default=UNSET, alias="configFilePath"
    )  # String!
    scrapers_path: str | UnsetType = Field(
        default=UNSET, alias="scrapersPath"
    )  # String!
    plugins_path: str | UnsetType = Field(default=UNSET, alias="pluginsPath")  # String!
    cache_path: str | UnsetType = Field(default=UNSET, alias="cachePath")  # String!
    blobs_path: str | UnsetType = Field(default=UNSET, alias="blobsPath")  # String!
    blobs_storage: BlobsStorageType | UnsetType = Field(
        default=UNSET, alias="blobsStorage"
    )  # BlobsStorageType!
    ffmpeg_path: str | UnsetType = Field(default=UNSET, alias="ffmpegPath")  # String!
    ffprobe_path: str | UnsetType = Field(default=UNSET, alias="ffprobePath")  # String!
    calculate_md5: bool | UnsetType = Field(
        default=UNSET, alias="calculateMD5"
    )  # Boolean!
    video_file_naming_algorithm: HashAlgorithm | UnsetType = Field(
        default=UNSET, alias="videoFileNamingAlgorithm"
    )  # HashAlgorithm!
    parallel_tasks: int | UnsetType = Field(
        default=UNSET, alias="parallelTasks"
    )  # Int!
    preview_audio: bool | UnsetType = Field(
        default=UNSET, alias="previewAudio"
    )  # Boolean!
    preview_segments: int | UnsetType = Field(
        default=UNSET, alias="previewSegments"
    )  # Int!
    preview_segment_duration: float | UnsetType = Field(
        default=UNSET, alias="previewSegmentDuration"
    )  # Float!
    preview_exclude_start: str | UnsetType = Field(
        default=UNSET, alias="previewExcludeStart"
    )  # String!
    preview_exclude_end: str | UnsetType = Field(
        default=UNSET, alias="previewExcludeEnd"
    )  # String!
    preview_preset: PreviewPreset | UnsetType = Field(
        default=UNSET, alias="previewPreset"
    )  # PreviewPreset!
    transcode_hardware_acceleration: bool | UnsetType = Field(
        default=UNSET, alias="transcodeHardwareAcceleration"
    )  # Boolean!
    max_transcode_size: StreamingResolutionEnum | None | UnsetType = Field(
        default=UNSET, alias="maxTranscodeSize"
    )  # StreamingResolutionEnum
    max_streaming_transcode_size: StreamingResolutionEnum | None | UnsetType = Field(
        default=UNSET, alias="maxStreamingTranscodeSize"
    )  # StreamingResolutionEnum
    transcode_input_args: list[str] | UnsetType = Field(
        default=UNSET, alias="transcodeInputArgs"
    )  # [String!]!
    transcode_output_args: list[str] | UnsetType = Field(
        default=UNSET, alias="transcodeOutputArgs"
    )  # [String!]!
    live_transcode_input_args: list[str] | UnsetType = Field(
        default=UNSET, alias="liveTranscodeInputArgs"
    )  # [String!]!
    live_transcode_output_args: list[str] | UnsetType = Field(
        default=UNSET, alias="liveTranscodeOutputArgs"
    )  # [String!]!
    draw_funscript_heatmap_range: bool | UnsetType = Field(
        default=UNSET, alias="drawFunscriptHeatmapRange"
    )  # Boolean!
    write_image_thumbnails: bool | UnsetType = Field(
        default=UNSET, alias="writeImageThumbnails"
    )  # Boolean!
    create_image_clips_from_videos: bool | UnsetType = Field(
        default=UNSET, alias="createImageClipsFromVideos"
    )  # Boolean!
    api_key: str | UnsetType = Field(default=UNSET, alias="apiKey")  # String!
    username: str | UnsetType = UNSET  # String!
    password: str | UnsetType = UNSET  # String!
    max_session_age: int | UnsetType = Field(
        default=UNSET, alias="maxSessionAge"
    )  # Int!
    log_file: str | None | UnsetType = Field(default=UNSET, alias="logFile")  # String
    log_out: bool | UnsetType = Field(default=UNSET, alias="logOut")  # Boolean!
    log_level: str | UnsetType = Field(default=UNSET, alias="logLevel")  # String!
    log_access: bool | UnsetType = Field(default=UNSET, alias="logAccess")  # Boolean!
    log_file_max_size: int | UnsetType = Field(
        default=UNSET, alias="logFileMaxSize"
    )  # Int!
    video_extensions: list[str] | UnsetType = Field(
        default=UNSET, alias="videoExtensions"
    )  # [String!]!
    image_extensions: list[str] | UnsetType = Field(
        default=UNSET, alias="imageExtensions"
    )  # [String!]!
    gallery_extensions: list[str] | UnsetType = Field(
        default=UNSET, alias="galleryExtensions"
    )  # [String!]!
    create_galleries_from_folders: bool | UnsetType = Field(
        default=UNSET, alias="createGalleriesFromFolders"
    )  # Boolean!
    gallery_cover_regex: str | UnsetType = Field(
        default=UNSET, alias="galleryCoverRegex"
    )  # String!
    excludes: list[str] | UnsetType = UNSET  # [String!]!
    image_excludes: list[str] | UnsetType = Field(
        default=UNSET, alias="imageExcludes"
    )  # [String!]!
    custom_performer_image_location: str | None | UnsetType = Field(
        default=UNSET, alias="customPerformerImageLocation"
    )  # String
    stash_boxes: list[Any] | UnsetType = Field(
        default=UNSET, alias="stashBoxes"
    )  # [StashBox!]!
    python_path: str | UnsetType = Field(default=UNSET, alias="pythonPath")  # String!
    scraper_package_sources: list[Any] | UnsetType = Field(
        default=UNSET, alias="scraperPackageSources"
    )  # [PackageSource!]!
    plugin_package_sources: list[Any] | UnsetType = Field(
        default=UNSET, alias="pluginPackageSources"
    )  # [PackageSource!]!


class ConfigDisableDropdownCreateInput(StashInput):
    """Input for disabling dropdown create."""

    performer: bool | None | UnsetType = UNSET  # Boolean
    tag: bool | None | UnsetType = UNSET  # Boolean
    studio: bool | None | UnsetType = UNSET  # Boolean
    movie: bool | None | UnsetType = UNSET  # Boolean


class ConfigImageLightboxInput(StashInput):
    """Input for image lightbox configuration."""

    slideshow_delay: int | None | UnsetType = Field(
        default=UNSET, alias="slideshowDelay"
    )  # Int
    display_mode: ImageLightboxDisplayMode | None | UnsetType = Field(
        default=UNSET, alias="displayMode"
    )  # ImageLightboxDisplayMode
    scale_up: bool | None | UnsetType = Field(default=UNSET, alias="scaleUp")  # Boolean
    reset_zoom_on_nav: bool | None | UnsetType = Field(
        default=UNSET, alias="resetZoomOnNav"
    )  # Boolean
    scroll_mode: ImageLightboxScrollMode | None | UnsetType = Field(
        default=UNSET, alias="scrollMode"
    )  # ImageLightboxScrollMode
    scroll_attempts_before_change: int | None | UnsetType = Field(
        default=UNSET, alias="scrollAttemptsBeforeChange"
    )  # Int


class ConfigImageLightboxResult(FromGraphQLMixin, BaseModel):
    """Result type for image lightbox configuration."""

    slideshow_delay: int | None | UnsetType = Field(
        default=UNSET, alias="slideshowDelay"
    )  # Int
    display_mode: ImageLightboxDisplayMode | None | UnsetType = Field(
        default=UNSET, alias="displayMode"
    )  # ImageLightboxDisplayMode
    scale_up: bool | None | UnsetType = Field(default=UNSET, alias="scaleUp")  # Boolean
    reset_zoom_on_nav: bool | None | UnsetType = Field(
        default=UNSET, alias="resetZoomOnNav"
    )  # Boolean
    scroll_mode: ImageLightboxScrollMode | None | UnsetType = Field(
        default=UNSET, alias="scrollMode"
    )  # ImageLightboxScrollMode
    scroll_attempts_before_change: int | UnsetType = Field(
        default=UNSET, alias="scrollAttemptsBeforeChange"
    )  # Int!


class ConfigInterfaceInput(StashInput):
    """Input for interface configuration."""

    sfw_content_mode: bool | None | UnsetType = Field(
        default=UNSET, alias="sfwContentMode"
    )  # Boolean
    menu_items: list[str] | None | UnsetType = Field(
        default=UNSET, alias="menuItems"
    )  # [String!]
    sound_on_preview: bool | None | UnsetType = Field(
        default=UNSET, alias="soundOnPreview"
    )  # Boolean
    wall_show_title: bool | None | UnsetType = Field(
        default=UNSET, alias="wallShowTitle"
    )  # Boolean
    wall_playback: str | None | UnsetType = Field(
        default=UNSET, alias="wallPlayback"
    )  # String
    show_scrubber: bool | None | UnsetType = Field(
        default=UNSET, alias="showScrubber"
    )  # Boolean
    maximum_loop_duration: int | None | UnsetType = Field(
        default=UNSET, alias="maximumLoopDuration"
    )  # Int
    autostart_video: bool | None | UnsetType = Field(
        default=UNSET, alias="autostartVideo"
    )  # Boolean
    autostart_video_on_play_selected: bool | None | UnsetType = Field(
        default=UNSET, alias="autostartVideoOnPlaySelected"
    )  # Boolean
    continue_playlist_default: bool | None | UnsetType = Field(
        default=UNSET, alias="continuePlaylistDefault"
    )  # Boolean
    show_studio_as_text: bool | None | UnsetType = Field(
        default=UNSET, alias="showStudioAsText"
    )  # Boolean
    css: str | None | UnsetType = UNSET  # String
    css_enabled: bool | None | UnsetType = Field(
        default=UNSET, alias="cssEnabled"
    )  # Boolean
    javascript: str | None | UnsetType = UNSET  # String
    javascript_enabled: bool | None | UnsetType = Field(
        default=UNSET, alias="javascriptEnabled"
    )  # Boolean
    custom_locales: str | None | UnsetType = Field(
        default=UNSET, alias="customLocales"
    )  # String
    custom_locales_enabled: bool | None | UnsetType = Field(
        default=UNSET, alias="customLocalesEnabled"
    )  # Boolean
    language: str | None | UnsetType = UNSET  # String
    image_lightbox: ConfigImageLightboxInput | None | UnsetType = Field(
        default=UNSET, alias="imageLightbox"
    )  # ConfigImageLightboxInput
    disable_dropdown_create: ConfigDisableDropdownCreateInput | None | UnsetType = (
        Field(default=UNSET, alias="disableDropdownCreate")
    )  # ConfigDisableDropdownCreateInput
    handy_key: str | None | UnsetType = Field(default=UNSET, alias="handyKey")  # String
    funscript_offset: int | None | UnsetType = Field(
        default=UNSET, alias="funscriptOffset"
    )  # Int
    use_stash_hosted_funscript: bool | None | UnsetType = Field(
        default=UNSET, alias="useStashHostedFunscript"
    )  # Boolean
    no_browser: bool | None | UnsetType = Field(
        default=UNSET, alias="noBrowser"
    )  # Boolean
    notifications_enabled: bool | None | UnsetType = Field(
        default=UNSET, alias="notificationsEnabled"
    )  # Boolean


class ConfigDisableDropdownCreate(FromGraphQLMixin, BaseModel):
    """Result type for disable dropdown create."""

    performer: bool | UnsetType = UNSET  # Boolean!
    tag: bool | UnsetType = UNSET  # Boolean!
    studio: bool | UnsetType = UNSET  # Boolean!
    movie: bool | UnsetType = UNSET  # Boolean!


class ConfigInterfaceResult(FromGraphQLMixin, BaseModel):
    """Result type for interface configuration."""

    sfw_content_mode: bool | UnsetType = Field(
        default=UNSET, alias="sfwContentMode"
    )  # Boolean!
    menu_items: list[str] | None | UnsetType = Field(
        default=UNSET, alias="menuItems"
    )  # [String!]
    sound_on_preview: bool | None | UnsetType = Field(
        default=UNSET, alias="soundOnPreview"
    )  # Boolean
    wall_show_title: bool | None | UnsetType = Field(
        default=UNSET, alias="wallShowTitle"
    )  # Boolean
    wall_playback: str | None | UnsetType = Field(
        default=UNSET, alias="wallPlayback"
    )  # String
    show_scrubber: bool | None | UnsetType = Field(
        default=UNSET, alias="showScrubber"
    )  # Boolean
    maximum_loop_duration: int | None | UnsetType = Field(
        default=UNSET, alias="maximumLoopDuration"
    )  # Int
    no_browser: bool | None | UnsetType = Field(
        default=UNSET, alias="noBrowser"
    )  # Boolean
    notifications_enabled: bool | None | UnsetType = Field(
        default=UNSET, alias="notificationsEnabled"
    )  # Boolean
    autostart_video: bool | None | UnsetType = Field(
        default=UNSET, alias="autostartVideo"
    )  # Boolean
    autostart_video_on_play_selected: bool | None | UnsetType = Field(
        default=UNSET, alias="autostartVideoOnPlaySelected"
    )  # Boolean
    continue_playlist_default: bool | None | UnsetType = Field(
        default=UNSET, alias="continuePlaylistDefault"
    )  # Boolean
    show_studio_as_text: bool | None | UnsetType = Field(
        default=UNSET, alias="showStudioAsText"
    )  # Boolean
    css: str | None | UnsetType = UNSET  # String
    css_enabled: bool | None | UnsetType = Field(
        default=UNSET, alias="cssEnabled"
    )  # Boolean
    javascript: str | None | UnsetType = UNSET  # String
    javascript_enabled: bool | None | UnsetType = Field(
        default=UNSET, alias="javascriptEnabled"
    )  # Boolean
    custom_locales: str | None | UnsetType = Field(
        default=UNSET, alias="customLocales"
    )  # String
    custom_locales_enabled: bool | None | UnsetType = Field(
        default=UNSET, alias="customLocalesEnabled"
    )  # Boolean
    language: str | None | UnsetType = UNSET  # String
    image_lightbox: ConfigImageLightboxResult | UnsetType = Field(
        default=UNSET, alias="imageLightbox"
    )  # ConfigImageLightboxResult!
    disable_dropdown_create: ConfigDisableDropdownCreate | UnsetType = Field(
        default=UNSET, alias="disableDropdownCreate"
    )  # ConfigDisableDropdownCreate!
    handy_key: str | None | UnsetType = Field(default=UNSET, alias="handyKey")  # String
    funscript_offset: int | None | UnsetType = Field(
        default=UNSET, alias="funscriptOffset"
    )  # Int
    use_stash_hosted_funscript: bool | None | UnsetType = Field(
        default=UNSET, alias="useStashHostedFunscript"
    )  # Boolean


class ConfigDLNAInput(StashInput):
    """Input for DLNA configuration."""

    server_name: str | None | UnsetType = Field(
        default=UNSET, alias="serverName"
    )  # String
    enabled: bool | None | UnsetType = UNSET  # Boolean
    port: int | None | UnsetType = UNSET  # Int
    whitelisted_ips: list[str] | None | UnsetType = Field(
        default=UNSET, alias="whitelistedIPs"
    )  # [String!]
    interfaces: list[str] | None | UnsetType = UNSET  # [String!]
    video_sort_order: str | None | UnsetType = Field(
        default=UNSET, alias="videoSortOrder"
    )  # String


class ConfigDLNAResult(FromGraphQLMixin, BaseModel):
    """Result type for DLNA configuration."""

    server_name: str | UnsetType = Field(default=UNSET, alias="serverName")  # String!
    enabled: bool | UnsetType = UNSET  # Boolean!
    port: int | UnsetType = UNSET  # Int!
    whitelisted_ips: list[str] | UnsetType = Field(
        default=UNSET, alias="whitelistedIPs"
    )  # [String!]!
    interfaces: list[str] | UnsetType = UNSET  # [String!]!
    video_sort_order: str | UnsetType = Field(
        default=UNSET, alias="videoSortOrder"
    )  # String!


class ConfigScrapingInput(StashInput):
    """Input for scraping configuration."""

    scraper_user_agent: str | None | UnsetType = Field(
        default=UNSET, alias="scraperUserAgent"
    )  # String
    scraper_cdp_path: str | None | UnsetType = Field(
        default=UNSET, alias="scraperCDPPath"
    )  # String
    scraper_cert_check: bool | None | UnsetType = Field(
        default=UNSET, alias="scraperCertCheck"
    )  # Boolean
    exclude_tag_patterns: list[str] | None | UnsetType = Field(
        default=UNSET, alias="excludeTagPatterns"
    )  # [String!]


class ConfigScrapingResult(BaseModel):
    """Result type for scraping configuration."""

    scraper_user_agent: str | None | UnsetType = Field(
        default=UNSET, alias="scraperUserAgent"
    )  # String
    scraper_cdp_path: str | None | UnsetType = Field(
        default=UNSET, alias="scraperCDPPath"
    )  # String
    scraper_cert_check: bool | UnsetType = Field(
        default=UNSET, alias="scraperCertCheck"
    )  # Boolean!
    exclude_tag_patterns: list[str] | UnsetType = Field(
        default=UNSET, alias="excludeTagPatterns"
    )  # [String!]!


class ConfigDefaultSettingsResult(FromGraphQLMixin, BaseModel):
    """Result type for default settings configuration."""

    scan: ScanMetadataOptions | None | UnsetType = (
        UNSET  # ScanMetadataOptions (nullable)
    )
    identify: Any | UnsetType = UNSET  # IdentifyMetadataTaskOptions
    auto_tag: AutoTagMetadataOptions | None | UnsetType = Field(
        default=UNSET, alias="autoTag"
    )  # AutoTagMetadataOptions (nullable)
    generate: GenerateMetadataOptions | None | UnsetType = (
        UNSET  # GenerateMetadataOptions (nullable)
    )
    delete_file: bool | UnsetType = Field(
        default=UNSET, alias="deleteFile"
    )  # Boolean (If true, delete file checkbox will be checked by default)
    delete_generated: bool | UnsetType = Field(
        default=UNSET, alias="deleteGenerated"
    )  # Boolean (If true, delete generated supporting files checkbox will be checked by default)


class ConfigDefaultSettingsInput(StashInput):
    """Input for default settings configuration."""

    scan: ScanMetadataInput | None | UnsetType = UNSET  # ScanMetadataInput
    identify: Any | None | UnsetType = UNSET  # IdentifyMetadataInput
    auto_tag: AutoTagMetadataInput | None | UnsetType = Field(
        default=UNSET, alias="autoTag"
    )  # AutoTagMetadataInput
    generate: GenerateMetadataInput | None | UnsetType = UNSET  # GenerateMetadataInput
    delete_file: bool | None | UnsetType = Field(
        default=UNSET, alias="deleteFile"
    )  # Boolean
    delete_generated: bool | None | UnsetType = Field(
        default=UNSET, alias="deleteGenerated"
    )  # Boolean


class ConfigResult(FromGraphQLMixin, BaseModel):
    """Result type for all configuration."""

    general: ConfigGeneralResult | UnsetType = UNSET  # ConfigGeneralResult!
    interface: ConfigInterfaceResult | UnsetType = UNSET  # ConfigInterfaceResult!
    dlna: ConfigDLNAResult | UnsetType = UNSET  # ConfigDLNAResult!
    scraping: ConfigScrapingResult | UnsetType = UNSET  # ConfigScrapingResult!
    defaults: ConfigDefaultSettingsResult | UnsetType = (
        UNSET  # ConfigDefaultSettingsResult!
    )
    ui: dict[str, Any] | UnsetType = UNSET  # Map!

    def plugins(self, include: list[str] | None = None) -> dict[str, dict[str, Any]]:
        """Get plugin configuration.

        Args:
            include: Optional list of plugin IDs to include

        Returns:
            Plugin configuration map
        """
        # TODO: Implement plugin filtering
        return {}


class Directory(BaseModel):
    """Directory structure of a path."""

    path: str | UnsetType = UNSET  # String!
    parent: str | None | UnsetType = UNSET  # String
    directories: list[str] | UnsetType = UNSET  # [String!]!


class StashConfigInput(StashInput):
    """Input for stash configuration."""

    path: str | UnsetType = UNSET  # String!
    exclude_video: bool | UnsetType = Field(
        default=UNSET, alias="excludeVideo"
    )  # Boolean!
    exclude_image: bool | UnsetType = Field(
        default=UNSET, alias="excludeImage"
    )  # Boolean!


class StashConfig(FromGraphQLMixin, BaseModel):
    """Result type for stash configuration."""

    path: str | UnsetType = UNSET  # String!
    exclude_video: bool | UnsetType = Field(
        default=UNSET, alias="excludeVideo"
    )  # Boolean!
    exclude_image: bool | UnsetType = Field(
        default=UNSET, alias="excludeImage"
    )  # Boolean!


class GenerateAPIKeyInput(StashInput):
    """Input for generating API key."""

    clear: bool | None | UnsetType = UNSET  # Boolean
