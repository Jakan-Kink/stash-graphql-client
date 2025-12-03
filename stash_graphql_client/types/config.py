"""Configuration types from schema/types/config.graphql."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field


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


class ConfigDLNAInput(BaseModel):
    """Input for DLNA configuration."""

    server_name: str | None = Field(None, alias="serverName")  # String
    enabled: bool | None = None  # Boolean
    port: int | None = None  # Int
    whitelisted_ips: list[str] | None = Field(None, alias="whitelistedIPs")  # [String!]
    interfaces: list[str] | None = None  # [String!]
    video_sort_order: str | None = Field(None, alias="videoSortOrder")  # String


class ConfigDLNAResult(BaseModel):
    """Result type for DLNA configuration."""

    server_name: str = Field(alias="serverName")  # String!
    enabled: bool  # Boolean!
    port: int  # Int!
    whitelisted_ips: list[str] = Field(alias="whitelistedIPs")  # [String!]!
    interfaces: list[str]  # [String!]!
    video_sort_order: str = Field(alias="videoSortOrder")  # String!


class ConfigDefaultSettingsInput(BaseModel):
    """Input for default settings configuration."""

    scan: ScanMetadataInput | None = None  # ScanMetadataInput
    auto_tag: AutoTagMetadataInput | None = Field(
        None, alias="autoTag"
    )  # AutoTagMetadataInput
    generate: GenerateMetadataInput | None = None  # GenerateMetadataInput
    delete_file: bool | None = Field(None, alias="deleteFile")  # Boolean
    delete_generated: bool | None = Field(None, alias="deleteGenerated")  # Boolean


class ConfigDefaultSettingsResult(BaseModel):
    """Result type for default settings configuration."""

    scan: ScanMetadataOptions  # ScanMetadataOptions
    auto_tag: AutoTagMetadataOptions = Field(alias="autoTag")  # AutoTagMetadataOptions
    generate: GenerateMetadataOptions  # GenerateMetadataOptions
    delete_file: bool = Field(
        alias="deleteFile"
    )  # Boolean (If true, delete file checkbox will be checked by default)
    delete_generated: bool = Field(
        alias="deleteGenerated"
    )  # Boolean (If true, delete generated supporting files checkbox will be checked by default)


class ConfigDisableDropdownCreate(BaseModel):
    """Result type for disable dropdown create."""

    performer: bool  # Boolean!
    tag: bool  # Boolean!
    studio: bool  # Boolean!
    movie: bool  # Boolean!


class ConfigDisableDropdownCreateInput(BaseModel):
    """Input for disabling dropdown create."""

    performer: bool | None = None  # Boolean
    tag: bool | None = None  # Boolean
    studio: bool | None = None  # Boolean
    movie: bool | None = None  # Boolean


class ConfigGeneralInput(BaseModel):
    """Input for general configuration."""

    stashes: list[StashConfigInput] | None = None  # [StashConfigInput!]
    database_path: str | None = Field(None, alias="databasePath")  # String
    backup_directory_path: str | None = Field(
        None, alias="backupDirectoryPath"
    )  # String
    generated_path: str | None = Field(None, alias="generatedPath")  # String
    metadata_path: str | None = Field(None, alias="metadataPath")  # String
    cache_path: str | None = Field(None, alias="cachePath")  # String
    blobs_path: str | None = Field(None, alias="blobsPath")  # String
    blobs_storage: BlobsStorageType | None = Field(
        None, alias="blobsStorage"
    )  # BlobsStorageType
    ffmpeg_path: str | None = Field(None, alias="ffmpegPath")  # String
    ffprobe_path: str | None = Field(None, alias="ffprobePath")  # String
    calculate_md5: bool | None = Field(None, alias="calculateMD5")  # Boolean
    video_file_naming_algorithm: HashAlgorithm | None = Field(
        None, alias="videoFileNamingAlgorithm"
    )  # HashAlgorithm
    parallel_tasks: int | None = Field(None, alias="parallelTasks")  # Int
    preview_audio: bool | None = Field(None, alias="previewAudio")  # Boolean
    preview_segments: int | None = Field(None, alias="previewSegments")  # Int
    preview_segment_duration: float | None = Field(
        None, alias="previewSegmentDuration"
    )  # Float
    preview_exclude_start: str | None = Field(
        None, alias="previewExcludeStart"
    )  # String
    preview_exclude_end: str | None = Field(None, alias="previewExcludeEnd")  # String
    preview_preset: PreviewPreset | None = Field(
        None, alias="previewPreset"
    )  # PreviewPreset
    transcode_hardware_acceleration: bool | None = Field(
        None, alias="transcodeHardwareAcceleration"
    )  # Boolean
    max_transcode_size: StreamingResolutionEnum | None = Field(
        None, alias="maxTranscodeSize"
    )  # StreamingResolutionEnum
    max_streaming_transcode_size: StreamingResolutionEnum | None = Field(
        None,
        alias="maxStreamingTranscodeSize",  # StreamingResolutionEnum
    )
    transcode_input_args: list[str] | None = Field(
        None, alias="transcodeInputArgs"
    )  # [String!]
    transcode_output_args: list[str] | None = Field(
        None, alias="transcodeOutputArgs"
    )  # [String!]
    live_transcode_input_args: list[str] | None = Field(
        None, alias="liveTranscodeInputArgs"
    )  # [String!]
    live_transcode_output_args: list[str] | None = Field(
        None, alias="liveTranscodeOutputArgs"
    )  # [String!]
    draw_funscript_heatmap_range: bool | None = Field(
        None, alias="drawFunscriptHeatmapRange"
    )  # Boolean
    write_image_thumbnails: bool | None = Field(
        None, alias="writeImageThumbnails"
    )  # Boolean
    create_image_clips_from_videos: bool | None = Field(
        None, alias="createImageClipsFromVideos"
    )  # Boolean
    username: str | None = None  # String
    password: str | None = None  # String
    max_session_age: int | None = Field(None, alias="maxSessionAge")  # Int
    log_file: str | None = Field(None, alias="logFile")  # String
    log_out: bool | None = Field(None, alias="logOut")  # Boolean
    log_level: str | None = Field(None, alias="logLevel")  # String
    log_access: bool | None = Field(None, alias="logAccess")  # Boolean
    create_galleries_from_folders: bool | None = Field(
        None, alias="createGalleriesFromFolders"
    )  # Boolean
    gallery_cover_regex: str | None = Field(None, alias="galleryCoverRegex")  # String
    video_extensions: list[str] | None = Field(
        None, alias="videoExtensions"
    )  # [String!]
    image_extensions: list[str] | None = Field(
        None, alias="imageExtensions"
    )  # [String!]
    gallery_extensions: list[str] | None = Field(
        None, alias="galleryExtensions"
    )  # [String!]
    excludes: list[str] | None = None  # [String!]
    image_excludes: list[str] | None = Field(None, alias="imageExcludes")  # [String!]
    custom_performer_image_location: str | None = Field(
        None, alias="customPerformerImageLocation"
    )  # String


class ConfigGeneralResult(BaseModel):
    """Result type for general configuration."""

    # Only require the most commonly used/returned fields
    database_path: str = Field(alias="databasePath")  # String!
    parallel_tasks: int = Field(alias="parallelTasks")  # Int!

    # Make all other fields optional since GraphQL fragments may not request all fields
    stashes: list[StashConfig] | None = None  # [StashConfig!]!
    backup_directory_path: str | None = Field(
        None, alias="backupDirectoryPath"
    )  # String!
    generated_path: str | None = Field(None, alias="generatedPath")  # String!
    metadata_path: str | None = Field(None, alias="metadataPath")  # String!
    config_file_path: str | None = Field(None, alias="configFilePath")  # String!
    cache_path: str | None = Field(None, alias="cachePath")  # String!
    blobs_path: str | None = Field(None, alias="blobsPath")  # String!
    blobs_storage: BlobsStorageType | None = Field(
        None, alias="blobsStorage"
    )  # BlobsStorageType!
    ffmpeg_path: str | None = Field(None, alias="ffmpegPath")  # String!
    ffprobe_path: str | None = Field(None, alias="ffprobePath")  # String!
    calculate_md5: bool | None = Field(None, alias="calculateMD5")  # Boolean!
    video_file_naming_algorithm: HashAlgorithm | None = Field(
        None, alias="videoFileNamingAlgorithm"
    )  # HashAlgorithm!
    preview_audio: bool | None = Field(None, alias="previewAudio")  # Boolean!
    preview_segments: int | None = Field(None, alias="previewSegments")  # Int!
    preview_segment_duration: float | None = Field(
        None, alias="previewSegmentDuration"
    )  # Float!
    preview_exclude_start: str | None = Field(
        None, alias="previewExcludeStart"
    )  # String!
    preview_exclude_end: str | None = Field(None, alias="previewExcludeEnd")  # String!
    preview_preset: PreviewPreset | None = Field(
        None, alias="previewPreset"
    )  # PreviewPreset!
    transcode_hardware_acceleration: bool | None = Field(
        None, alias="transcodeHardwareAcceleration"
    )  # Boolean!
    max_transcode_size: StreamingResolutionEnum | None = Field(
        None, alias="maxTranscodeSize"
    )  # StreamingResolutionEnum
    max_streaming_transcode_size: StreamingResolutionEnum | None = Field(
        None, alias="maxStreamingTranscodeSize"
    )  # StreamingResolutionEnum
    transcode_input_args: list[str] | None = Field(
        None, alias="transcodeInputArgs"
    )  # [String!]!
    transcode_output_args: list[str] | None = Field(
        None, alias="transcodeOutputArgs"
    )  # [String!]!
    live_transcode_input_args: list[str] | None = Field(
        None, alias="liveTranscodeInputArgs"
    )  # [String!]!
    live_transcode_output_args: list[str] | None = Field(
        None, alias="liveTranscodeOutputArgs"
    )  # [String!]!
    draw_funscript_heatmap_range: bool | None = Field(
        None, alias="drawFunscriptHeatmapRange"
    )  # Boolean!
    write_image_thumbnails: bool | None = Field(
        None, alias="writeImageThumbnails"
    )  # Boolean!
    create_image_clips_from_videos: bool | None = Field(
        None, alias="createImageClipsFromVideos"
    )  # Boolean!
    api_key: str | None = Field(None, alias="apiKey")  # String!
    username: str | None = None  # String!
    password: str | None = None  # String!
    max_session_age: int | None = Field(None, alias="maxSessionAge")  # Int!
    log_file: str | None = Field(None, alias="logFile")  # String
    log_out: bool | None = Field(None, alias="logOut")  # Boolean!
    log_level: str | None = Field(None, alias="logLevel")  # String!
    log_access: bool | None = Field(None, alias="logAccess")  # Boolean!
    video_extensions: list[str] | None = Field(
        None, alias="videoExtensions"
    )  # [String!]!
    image_extensions: list[str] | None = Field(
        None, alias="imageExtensions"
    )  # [String!]!
    gallery_extensions: list[str] | None = Field(
        None, alias="galleryExtensions"
    )  # [String!]!
    create_galleries_from_folders: bool | None = Field(
        None, alias="createGalleriesFromFolders"
    )  # Boolean!
    gallery_cover_regex: str | None = Field(None, alias="galleryCoverRegex")  # String!
    excludes: list[str] | None = None  # [String!]!
    image_excludes: list[str] | None = Field(None, alias="imageExcludes")  # [String!]!
    custom_performer_image_location: str | None = Field(
        None, alias="customPerformerImageLocation"
    )  # String


class ConfigImageLightboxInput(BaseModel):
    """Input for image lightbox configuration."""

    slideshow_delay: int | None = Field(None, alias="slideshowDelay")  # Int
    display_mode: ImageLightboxDisplayMode | None = Field(
        None, alias="displayMode"
    )  # ImageLightboxDisplayMode
    scale_up: bool | None = Field(None, alias="scaleUp")  # Boolean
    reset_zoom_on_nav: bool | None = Field(None, alias="resetZoomOnNav")  # Boolean
    scroll_mode: ImageLightboxScrollMode | None = Field(
        None, alias="scrollMode"
    )  # ImageLightboxScrollMode
    scroll_attempts_before_change: int | None = Field(
        None, alias="scrollAttemptsBeforeChange"
    )  # Int


class ConfigImageLightboxResult(BaseModel):
    """Result type for image lightbox configuration."""

    slideshow_delay: int | None = Field(None, alias="slideshowDelay")  # Int
    display_mode: ImageLightboxDisplayMode | None = Field(
        None, alias="displayMode"
    )  # ImageLightboxDisplayMode
    scale_up: bool | None = Field(None, alias="scaleUp")  # Boolean
    reset_zoom_on_nav: bool | None = Field(None, alias="resetZoomOnNav")  # Boolean
    scroll_mode: ImageLightboxScrollMode | None = Field(
        None, alias="scrollMode"
    )  # ImageLightboxScrollMode
    scroll_attempts_before_change: int = Field(
        alias="scrollAttemptsBeforeChange"
    )  # Int!


class ConfigInterfaceInput(BaseModel):
    """Input for interface configuration."""

    menu_items: list[str] | None = Field(None, alias="menuItems")  # [String!]
    sound_on_preview: bool | None = Field(None, alias="soundOnPreview")  # Boolean
    wall_show_title: bool | None = Field(None, alias="wallShowTitle")  # Boolean
    wall_playback: str | None = Field(None, alias="wallPlayback")  # String
    show_scrubber: bool | None = Field(None, alias="showScrubber")  # Boolean
    maximum_loop_duration: int | None = Field(None, alias="maximumLoopDuration")  # Int
    autostart_video: bool | None = Field(None, alias="autostartVideo")  # Boolean
    autostart_video_on_play_selected: bool | None = Field(
        None, alias="autostartVideoOnPlaySelected"
    )  # Boolean
    continue_playlist_default: bool | None = Field(
        None, alias="continuePlaylistDefault"
    )  # Boolean
    show_studio_as_text: bool | None = Field(None, alias="showStudioAsText")  # Boolean
    css: str | None = None  # String
    css_enabled: bool | None = Field(None, alias="cssEnabled")  # Boolean
    javascript: str | None = None  # String
    javascript_enabled: bool | None = Field(None, alias="javascriptEnabled")  # Boolean
    custom_locales: str | None = Field(None, alias="customLocales")  # String
    custom_locales_enabled: bool | None = Field(
        None, alias="customLocalesEnabled"
    )  # Boolean
    language: str | None = None  # String
    image_lightbox: ConfigImageLightboxInput | None = Field(
        None, alias="imageLightbox"
    )  # ConfigImageLightboxInput
    disable_dropdown_create: ConfigDisableDropdownCreateInput | None = Field(
        None,
        alias="disableDropdownCreate",  # ConfigDisableDropdownCreateInput
    )
    handy_key: str | None = Field(None, alias="handyKey")  # String
    funscript_offset: int | None = Field(None, alias="funscriptOffset")  # Int
    use_stash_hosted_funscript: bool | None = Field(
        None, alias="useStashHostedFunscript"
    )  # Boolean
    no_browser: bool | None = Field(None, alias="noBrowser")  # Boolean
    notifications_enabled: bool | None = Field(
        None, alias="notificationsEnabled"
    )  # Boolean


class ConfigInterfaceResult(BaseModel):
    """Result type for interface configuration."""

    menu_items: list[str] | None = Field(None, alias="menuItems")  # [String!]
    sound_on_preview: bool | None = Field(None, alias="soundOnPreview")  # Boolean
    wall_show_title: bool | None = Field(None, alias="wallShowTitle")  # Boolean
    wall_playback: str | None = Field(None, alias="wallPlayback")  # String
    show_scrubber: bool | None = Field(None, alias="showScrubber")  # Boolean
    maximum_loop_duration: int | None = Field(None, alias="maximumLoopDuration")  # Int
    no_browser: bool | None = Field(None, alias="noBrowser")  # Boolean
    notifications_enabled: bool | None = Field(
        None, alias="notificationsEnabled"
    )  # Boolean
    autostart_video: bool | None = Field(None, alias="autostartVideo")  # Boolean
    autostart_video_on_play_selected: bool | None = Field(
        None, alias="autostartVideoOnPlaySelected"
    )  # Boolean
    continue_playlist_default: bool | None = Field(
        None, alias="continuePlaylistDefault"
    )  # Boolean
    show_studio_as_text: bool | None = Field(None, alias="showStudioAsText")  # Boolean
    css: str | None = None  # String
    css_enabled: bool | None = Field(None, alias="cssEnabled")  # Boolean
    javascript: str | None = None  # String
    javascript_enabled: bool | None = Field(None, alias="javascriptEnabled")  # Boolean
    custom_locales: str | None = Field(None, alias="customLocales")  # String
    custom_locales_enabled: bool | None = Field(
        None, alias="customLocalesEnabled"
    )  # Boolean
    language: str | None = None  # String
    image_lightbox: ConfigImageLightboxResult = Field(
        alias="imageLightbox"
    )  # ConfigImageLightboxResult!
    disable_dropdown_create: ConfigDisableDropdownCreate = Field(
        alias="disableDropdownCreate"
    )  # ConfigDisableDropdownCreate!
    handy_key: str | None = Field(None, alias="handyKey")  # String
    funscript_offset: int | None = Field(None, alias="funscriptOffset")  # Int
    use_stash_hosted_funscript: bool | None = Field(
        None, alias="useStashHostedFunscript"
    )  # Boolean


class ConfigResult(BaseModel):
    """Result type for all configuration."""

    general: ConfigGeneralResult  # ConfigGeneralResult!
    interface: ConfigInterfaceResult  # ConfigInterfaceResult!
    dlna: ConfigDLNAResult  # ConfigDLNAResult!
    defaults: ConfigDefaultSettingsResult  # ConfigDefaultSettingsResult!
    ui: dict[str, Any]  # Map!

    def plugins(self, include: list[str] | None = None) -> dict[str, dict[str, Any]]:
        """Get plugin configuration.

        Args:
            include: Optional list of plugin IDs to include

        Returns:
            Plugin configuration map
        """
        # TODO: Implement plugin filtering
        return {}


class DLNAIP(BaseModel):
    """DLNA IP address with expiration from schema/types/dlna.graphql."""

    ip_address: str = Field(alias="ipAddress")  # String!
    until: str | None = None  # Time


class DLNAStatus(BaseModel):
    """DLNA status from schema/types/dlna.graphql."""

    running: bool  # Boolean!
    until: str | None = None  # Time
    recent_ip_addresses: list[str] = Field(alias="recentIPAddresses")  # [String!]!
    allowed_ip_addresses: list[DLNAIP] = Field(alias="allowedIPAddresses")  # [DLNAIP!]!


class Directory(BaseModel):
    """Directory structure of a path."""

    path: str  # String!
    parent: str | None = None  # String
    directories: list[str]  # [String!]!


class GenerateAPIKeyInput(BaseModel):
    """Input for generating API key."""

    clear: bool | None = None  # Boolean


class SetupInput(BaseModel):
    """Input for initial setup."""

    config_location: str = Field(alias="configLocation")  # String!
    stashes: list[StashConfigInput]  # [StashConfigInput!]!
    database_file: str = Field(alias="databaseFile")  # String!
    generated_location: str = Field(alias="generatedLocation")  # String!
    cache_location: str = Field(alias="cacheLocation")  # String!
    store_blobs_in_database: bool = Field(alias="storeBlobsInDatabase")  # Boolean!
    blobs_location: str = Field(alias="blobsLocation")  # String!


class StashBox(BaseModel):
    """StashBox configuration from schema/types/stash-box.graphql."""

    endpoint: str  # String!
    api_key: str = Field(alias="apiKey")  # String!
    name: str  # String!
    max_requests_per_minute: int = Field(alias="maxRequestsPerMinute")  # Int!


class StashBoxValidationResult(BaseModel):
    """Result of stash-box validation from schema/types/config.graphql."""

    valid: bool  # Boolean!
    status: str  # String!


class StashConfig(BaseModel):
    """Result type for stash configuration."""

    path: str  # String!
    exclude_video: bool = Field(alias="excludeVideo")  # Boolean!
    exclude_image: bool = Field(alias="excludeImage")  # Boolean!


class StashConfigInput(BaseModel):
    """Input for stash configuration."""

    path: str  # String!
    exclude_video: bool = Field(alias="excludeVideo")  # Boolean!
    exclude_image: bool = Field(alias="excludeImage")  # Boolean!
