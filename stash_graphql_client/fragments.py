"""GraphQL fragments for Stash queries.

These fragments match the ones defined in schema/fragments.graphql.
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .capabilities import ServerCapabilities

# Configuration fragments
SCAN_METADATA_OPTIONS = """
    rescan
    scanGenerateCovers
    scanGeneratePreviews
    scanGenerateImagePreviews
    scanGenerateSprites
    scanGeneratePhashes
    scanGenerateThumbnails
    scanGenerateClipPreviews
"""

AUTO_TAG_METADATA_OPTIONS = """
    performers
    studios
    tags
"""

GENERATE_METADATA_OPTIONS = """
    covers
    sprites
    previews
    imagePreviews
    markers
    markerImagePreviews
    markerScreenshots
    transcodes
    phashes
    interactiveHeatmapsSpeeds
    imageThumbnails
    clipPreviews
"""

CONFIG_DEFAULTS_QUERY = f"""
query ConfigurationDefaults {{
    configuration {{
        defaults {{
            scan {{
                {SCAN_METADATA_OPTIONS}
            }}
            autoTag {{
                {AUTO_TAG_METADATA_OPTIONS}
            }}
            generate {{
                {GENERATE_METADATA_OPTIONS}
            }}
            deleteFile
            deleteGenerated
        }}
    }}
}}
"""

# Configuration sub-fragments
CONFIG_GENERAL_FIELDS = """
    databasePath
    generatedPath
    metadataPath
    scrapersPath
    cachePath
    blobsPath
    blobsStorage
    calculateMD5
    videoFileNamingAlgorithm
    parallelTasks
    previewAudio
    previewSegments
    previewSegmentDuration
    previewExcludeStart
    previewExcludeEnd
    previewPreset
    maxTranscodeSize
    maxStreamingTranscodeSize
    writeImageThumbnails
    apiKey
    username
    password
    maxSessionAge
    logFile
    logOut
    logLevel
    logAccess
    createGalleriesFromFolders
    galleryCoverRegex
    videoExtensions
    imageExtensions
    galleryExtensions
    excludes
    imageExcludes
    customPerformerImageLocation
    pythonPath
    transcodeInputArgs
    transcodeOutputArgs
    liveTranscodeInputArgs
    liveTranscodeOutputArgs
    drawFunscriptHeatmapRange
    stashes {
        path
        excludeVideo
        excludeImage
    }
    stashBoxes {
        name
        endpoint
        api_key
    }
    scraperPackageSources {
        name
        url
        local_path
    }
    pluginPackageSources {
        name
        url
        local_path
    }
"""

CONFIG_INTERFACE_FIELDS = """
    menuItems
    soundOnPreview
    wallShowTitle
    wallPlayback
    showScrubber
    maximumLoopDuration
    noBrowser
    notificationsEnabled
    autostartVideo
    autostartVideoOnPlaySelected
    continuePlaylistDefault
    showStudioAsText
    css
    cssEnabled
    javascript
    javascriptEnabled
    customLocales
    customLocalesEnabled
    language
    imageLightbox {
        slideshowDelay
        displayMode
        scaleUp
        resetZoomOnNav
        scrollMode
        scrollAttemptsBeforeChange
    }
    disableDropdownCreate {
        performer
        tag
        studio
    }
    handyKey
    funscriptOffset
    useStashHostedFunscript
"""

CONFIG_DLNA_FIELDS = """
    serverName
    enabled
    port
    whitelistedIPs
    interfaces
    videoSortOrder
"""

CONFIG_SCRAPING_FIELDS = """
    scraperUserAgent
    scraperCertCheck
    scraperCDPPath
    excludeTagPatterns
"""

# Full configuration query with all sub-fragments
CONFIGURATION_QUERY = f"""
query Configuration {{
    configuration {{
        general {{
            {CONFIG_GENERAL_FIELDS}
        }}
        interface {{
            {CONFIG_INTERFACE_FIELDS}
        }}
        dlna {{
            {CONFIG_DLNA_FIELDS}
        }}
        scraping {{
            {CONFIG_SCRAPING_FIELDS}
        }}
        defaults {{
            scan {{
                {SCAN_METADATA_OPTIONS}
            }}
            autoTag {{
                {AUTO_TAG_METADATA_OPTIONS}
            }}
            generate {{
                {GENERATE_METADATA_OPTIONS}
            }}
            deleteFile
            deleteGenerated
        }}
        ui
    }}
}}
"""

# Job fragments
JOB_FIELDS = """
    __typename
    id
    status
    subTasks
    description
    progress
    startTime
    endTime
    addTime
    error
"""

FIND_JOB_QUERY = f"""
query FindJob($input: FindJobInput!) {{
    findJob(input: $input) {{
        {JOB_FIELDS}
    }}
}}
"""

# Metadata scan fragments
METADATA_SCAN_MUTATION = """
mutation MetadataScan($input: ScanMetadataInput!) {
    metadataScan(input: $input)
}
"""

# File fragments
FILE_FIELDS = """fragment FileFields on BaseFile {
    __typename
    id
    path
    basename
    parent_folder {
        __typename
        id
        path
    }
    zip_file {
        __typename
        id
        path
    }
    size
    mod_time
    created_at
    updated_at
    fingerprints {
        __typename
        type
        value
    }
}"""

VIDEO_FILE_FIELDS = """fragment VideoFileFields on VideoFile {
    __typename
    ...FileFields
    format
    width
    height
    duration
    video_codec
    audio_codec
    frame_rate
    bit_rate
}"""

IMAGE_FILE_FIELDS = """fragment ImageFileFields on ImageFile {
    __typename
    ...FileFields
    format
    width
    height
}"""

GALLERY_FILE_FIELDS = """fragment GalleryFileFields on GalleryFile {
    __typename
    ...FileFields
}"""

# Scene fragments
_BASE_SCENE_FIELDS = """
    __typename
    id
    created_at
    updated_at
    title
    code
    details
    urls
    date
    organized
    captions {
        __typename
        language_code
        caption_type
    }
    files {
        ...VideoFileFields
    }
    studio {
        __typename
        id
    }
    performers {
        __typename
        id
    }
    tags {
        __typename
        id
    }
    stash_ids {
        __typename
        endpoint
        stash_id
    }
    sceneStreams {
        __typename
        url
        mime_type
        label
    }
"""
SCENE_FIELDS = _BASE_SCENE_FIELDS

# Performer fragments
_BASE_PERFORMER_FIELDS = """
    __typename
    id
    created_at
    updated_at
    name
    disambiguation
    urls
    gender
    birthdate
    ethnicity
    country
    eye_color
    measurements
    fake_tits
    penis_length
    circumcised
    tattoos
    piercings
    alias_list
    image_path
    details
    hair_color
    stash_ids {
        __typename
        endpoint
        stash_id
    }
    tags {
        __typename
        id
    }
    scenes {
        __typename
        id
    }
    groups {
        __typename
        id
    }
    custom_fields
"""
# NOTE: custom_fields is a base field (no capability gate needed).
# It was added in Stash migration 71 — below the library's MIN_SUPPORTED_APP_SCHEMA of 75,
# so it is present on every server this library supports.
PERFORMER_FIELDS = _BASE_PERFORMER_FIELDS

# Studio fragments
_BASE_STUDIO_FIELDS = """
    __typename
    id
    created_at
    updated_at
    name
    urls
    image_path
    aliases
    details
    tags {
        __typename
        id
    }
    parent_studio {
        __typename
        id
    }
"""
STUDIO_FIELDS = _BASE_STUDIO_FIELDS

# Tag fragments
_BASE_TAG_FIELDS = """
    __typename
    id
    created_at
    updated_at
    name
    description
    aliases
    image_path
    stash_ids {
        __typename
        endpoint
        stash_id
    }
    parents {
        __typename
        id
    }
    children {
        __typename
        id
    }
"""
TAG_FIELDS = _BASE_TAG_FIELDS

# Scene query templates
SCENE_QUERY_FRAGMENTS = f"""
{FILE_FIELDS}
{VIDEO_FILE_FIELDS}
fragment SceneFragment on Scene {{
    {SCENE_FIELDS}
}}
"""

FIND_SCENE_QUERY = f"""
{SCENE_QUERY_FRAGMENTS}
query FindScene($id: ID!) {{
    findScene(id: $id) {{
        ...SceneFragment
    }}
}}
"""

FIND_SCENES_QUERY = f"""
{SCENE_QUERY_FRAGMENTS}
query FindScenes($filter: FindFilterType, $scene_filter: SceneFilterType) {{
    findScenes(filter: $filter, scene_filter: $scene_filter) {{
        count
        duration
        filesize
        scenes {{
            ...SceneFragment
        }}
    }}
}}
"""

CREATE_SCENE_MUTATION = f"""
{SCENE_QUERY_FRAGMENTS}
mutation CreateScene($input: SceneCreateInput!) {{
    sceneCreate(input: $input) {{
        ...SceneFragment
    }}
}}
"""

UPDATE_SCENE_MUTATION = f"""
{SCENE_QUERY_FRAGMENTS}
mutation UpdateScene($input: SceneUpdateInput!) {{
    sceneUpdate(input: $input) {{
        ...SceneFragment
    }}
}}
"""

FIND_DUPLICATE_SCENES_QUERY = f"""
{SCENE_QUERY_FRAGMENTS}
query FindDuplicateScenes($distance: Int, $duration_diff: Float) {{
    findDuplicateScenes(distance: $distance, duration_diff: $duration_diff) {{
        ...SceneFragment
    }}
}}
"""

PARSE_SCENE_FILENAMES_QUERY = """
query ParseSceneFilenames($filter: FindFilterType, $config: SceneParserInput!) {
    parseSceneFilenames(filter: $filter, config: $config)
}
"""

SCENE_WALL_QUERY = f"""
{SCENE_QUERY_FRAGMENTS}
query SceneWall($q: String) {{
    sceneWall(q: $q) {{
        ...SceneFragment
    }}
}}
"""

BULK_SCENE_UPDATE_MUTATION = f"""
{SCENE_QUERY_FRAGMENTS}
mutation BulkSceneUpdate($input: BulkSceneUpdateInput!) {{
    bulkSceneUpdate(input: $input) {{
        ...SceneFragment
    }}
}}
"""

SCENES_UPDATE_MUTATION = f"""
{SCENE_QUERY_FRAGMENTS}
mutation ScenesUpdate($input: [SceneUpdateInput!]!) {{
    scenesUpdate(input: $input) {{
        ...SceneFragment
    }}
}}
"""

SCENE_GENERATE_SCREENSHOT_MUTATION = """
mutation SceneGenerateScreenshot($id: ID!, $at: Float) {
    sceneGenerateScreenshot(id: $id, at: $at)
}
"""

SCENE_MERGE_MUTATION = f"""
{SCENE_QUERY_FRAGMENTS}
mutation SceneMerge($input: SceneMergeInput!) {{
    sceneMerge(input: $input) {{
        ...SceneFragment
    }}
}}
"""

# Performer query templates
FIND_PERFORMER_QUERY = f"""
query FindPerformer($id: ID!) {{
    findPerformer(id: $id) {{
        {PERFORMER_FIELDS}
    }}
}}
"""

FIND_PERFORMERS_QUERY = f"""
query FindPerformers($filter: FindFilterType, $performer_filter: PerformerFilterType) {{
    findPerformers(filter: $filter, performer_filter: $performer_filter) {{
        count
        performers {{
            {PERFORMER_FIELDS}
        }}
    }}
}}
"""

CREATE_PERFORMER_MUTATION = f"""
mutation CreatePerformer($input: PerformerCreateInput!) {{
    performerCreate(input: $input) {{
        {PERFORMER_FIELDS}
    }}
}}
"""

UPDATE_PERFORMER_MUTATION = f"""
mutation UpdatePerformer($input: PerformerUpdateInput!) {{
    performerUpdate(input: $input) {{
        {PERFORMER_FIELDS}
    }}
}}
"""

# Studio query templates
FIND_STUDIO_QUERY = f"""
query FindStudio($id: ID!) {{
    findStudio(id: $id) {{
        {STUDIO_FIELDS}
    }}
}}
"""

FIND_STUDIOS_QUERY = f"""
query FindStudios($filter: FindFilterType, $studio_filter: StudioFilterType) {{
    findStudios(filter: $filter, studio_filter: $studio_filter) {{
        count
        studios {{
            {STUDIO_FIELDS}
        }}
    }}
}}
"""

CREATE_STUDIO_MUTATION = f"""
mutation CreateStudio($input: StudioCreateInput!) {{
    studioCreate(input: $input) {{
        {STUDIO_FIELDS}
    }}
}}
"""

UPDATE_STUDIO_MUTATION = f"""
mutation UpdateStudio($input: StudioUpdateInput!) {{
    studioUpdate(input: $input) {{
        {STUDIO_FIELDS}
    }}
}}
"""

# Tag query templates
FIND_TAG_QUERY = f"""
query FindTag($id: ID!) {{
    findTag(id: $id) {{
        {TAG_FIELDS}
    }}
}}
"""

FIND_TAGS_QUERY = f"""
query FindTags($filter: FindFilterType, $tag_filter: TagFilterType) {{
    findTags(filter: $filter, tag_filter: $tag_filter) {{
        count
        tags {{
            {TAG_FIELDS}
        }}
    }}
}}
"""

CREATE_TAG_MUTATION = f"""
mutation CreateTag($input: TagCreateInput!) {{
    tagCreate(input: $input) {{
        {TAG_FIELDS}
    }}
}}
"""

UPDATE_TAG_MUTATION = f"""
mutation UpdateTag($input: TagUpdateInput!) {{
    tagUpdate(input: $input) {{
        {TAG_FIELDS}
    }}
}}
"""

# Gallery fragments
_BASE_GALLERY_FIELDS = """
    __typename
    id
    created_at
    updated_at
    title
    code
    date
    urls
    details
    photographer
    organized
    studio {
        __typename
        id
    }
    scenes {
        __typename
        id
    }
    performers {
        __typename
        id
        name
    }
    tags {
        __typename
        id
        name
    }
    files {
        ...GalleryFileFields
    }
"""
GALLERY_FIELDS = _BASE_GALLERY_FIELDS

# Gallery query templates
GALLERY_QUERY_FRAGMENTS = f"""
{FILE_FIELDS}
{GALLERY_FILE_FIELDS}
fragment GalleryFragment on Gallery {{
    {GALLERY_FIELDS}
}}
"""

FIND_GALLERY_QUERY = f"""
{GALLERY_QUERY_FRAGMENTS}
query FindGallery($id: ID!) {{
    findGallery(id: $id) {{
        ...GalleryFragment
    }}
}}
"""

FIND_GALLERIES_QUERY = f"""
{GALLERY_QUERY_FRAGMENTS}
query FindGalleries($filter: FindFilterType, $gallery_filter: GalleryFilterType) {{
    findGalleries(filter: $filter, gallery_filter: $gallery_filter) {{
        count
        galleries {{
            ...GalleryFragment
        }}
    }}
}}
"""

CREATE_GALLERY_MUTATION = f"""
{GALLERY_QUERY_FRAGMENTS}
mutation CreateGallery($input: GalleryCreateInput!) {{
    galleryCreate(input: $input) {{
        ...GalleryFragment
    }}
}}
"""

UPDATE_GALLERY_MUTATION = f"""
{GALLERY_QUERY_FRAGMENTS}
mutation UpdateGallery($input: GalleryUpdateInput!) {{
    galleryUpdate(input: $input) {{
        ...GalleryFragment
    }}
}}
"""

GALLERIES_UPDATE_MUTATION = f"""
{GALLERY_QUERY_FRAGMENTS}
mutation GalleriesUpdate($input: [GalleryUpdateInput!]!) {{
    galleriesUpdate(input: $input) {{
        ...GalleryFragment
    }}
}}
"""

GALLERY_DESTROY_MUTATION = """
mutation GalleryDestroy($input: GalleryDestroyInput!) {
    galleryDestroy(input: $input)
}
"""

REMOVE_GALLERY_IMAGES_MUTATION = """
mutation RemoveGalleryImages($input: GalleryRemoveInput!) {
    removeGalleryImages(input: $input)
}
"""

SET_GALLERY_COVER_MUTATION = """
mutation SetGalleryCover($input: GallerySetCoverInput!) {
    setGalleryCover(input: $input)
}
"""

RESET_GALLERY_COVER_MUTATION = """
mutation ResetGalleryCover($input: GalleryResetCoverInput!) {
    resetGalleryCover(input: $input)
}
"""

GALLERY_CHAPTER_CREATE_MUTATION = f"""
{GALLERY_QUERY_FRAGMENTS}
mutation GalleryChapterCreate($input: GalleryChapterCreateInput!) {{
    galleryChapterCreate(input: $input) {{
        id
        title
        image_index
        gallery {{
            ...GalleryFragment
        }}
    }}
}}
"""

GALLERY_CHAPTER_UPDATE_MUTATION = f"""
{GALLERY_QUERY_FRAGMENTS}
mutation GalleryChapterUpdate($input: GalleryChapterUpdateInput!) {{
    galleryChapterUpdate(input: $input) {{
        id
        title
        image_index
        gallery {{
            ...GalleryFragment
        }}
    }}
}}
"""

GALLERY_CHAPTER_DESTROY_MUTATION = """
mutation GalleryChapterDestroy($id: ID!) {
    galleryChapterDestroy(id: $id)
}
"""

GALLERY_ADD_IMAGES_MUTATION = """
mutation AddGalleryImages($input: GalleryAddInput!) {
    addGalleryImages(input: $input)
}
"""

# Image fragments
# NOTE: visual_files is a union type (VisualFile = VideoFile | ImageFile)
# GIF images are returned as VideoFile since they contain animation/video data
_BASE_IMAGE_FIELDS = """
    __typename
    id
    created_at
    updated_at
    title
    code
    organized
    date
    urls
    details
    photographer
    studio {
        __typename
        id
    }
    performers {
        __typename
        id
    }
    tags {
        __typename
        id
        name
    }
    galleries {
        __typename
        id
    }
    visual_files {
        __typename
        ... on ImageFile {
            ...ImageFileFields
        }
        ... on VideoFile {
            ...VideoFileFields
        }
    }
"""
IMAGE_FIELDS = _BASE_IMAGE_FIELDS

# Image query templates
# NOTE: Must include VIDEO_FILE_FIELDS because visual_files can contain VideoFile (for GIFs)
IMAGE_QUERY_FRAGMENTS = f"""
{FILE_FIELDS}
{IMAGE_FILE_FIELDS}
{VIDEO_FILE_FIELDS}
fragment ImageFragment on Image {{
    {IMAGE_FIELDS}
}}
"""

FIND_IMAGE_QUERY = f"""
{IMAGE_QUERY_FRAGMENTS}
query FindImage($id: ID!) {{
    findImage(id: $id) {{
        ...ImageFragment
    }}
}}
"""

FIND_IMAGES_QUERY = f"""
{IMAGE_QUERY_FRAGMENTS}
query FindImages($filter: FindFilterType, $image_filter: ImageFilterType) {{
    findImages(filter: $filter, image_filter: $image_filter) {{
        count
        megapixels
        filesize
        images {{
            ...ImageFragment
        }}
    }}
}}
"""

CREATE_IMAGE_MUTATION = f"""
{IMAGE_QUERY_FRAGMENTS}
mutation CreateImage($input: ImageCreateInput!) {{
    imageCreate(input: $input) {{
        ...ImageFragment
    }}
}}
"""

UPDATE_IMAGE_MUTATION = f"""
{IMAGE_QUERY_FRAGMENTS}
mutation UpdateImage($input: ImageUpdateInput!) {{
    imageUpdate(input: $input) {{
        ...ImageFragment
    }}
}}
"""

# Image O-count mutations
IMAGE_INCREMENT_O_MUTATION = """
mutation ImageIncrementO($id: ID!) {
    imageIncrementO(id: $id)
}
"""

IMAGE_DECREMENT_O_MUTATION = """
mutation ImageDecrementO($id: ID!) {
    imageDecrementO(id: $id)
}
"""

IMAGE_RESET_O_MUTATION = """
mutation ImageResetO($id: ID!) {
    imageResetO(id: $id)
}
"""

# Marker fragments
MARKER_FIELDS = """
    __typename
    id
    created_at
    updated_at
    title
    seconds
    scene {
        __typename
        id
    }
    primary_tag {
        __typename
        id
    }
    tags {
        __typename
        id
    }
"""

# Marker query templates
FIND_MARKER_QUERY = f"""
query FindMarker($id: ID!) {{
    findSceneMarkers(ids: [$id]) {{
        scene_markers {{
            {MARKER_FIELDS}
        }}
    }}
}}
"""

FIND_MARKERS_QUERY = f"""
query FindMarkers($filter: FindFilterType, $marker_filter: SceneMarkerFilterType) {{
    findSceneMarkers(filter: $filter, scene_marker_filter: $marker_filter) {{
        count
        scene_markers {{
            {MARKER_FIELDS}
        }}
    }}
}}
"""

CREATE_MARKER_MUTATION = f"""
mutation CreateMarker($input: SceneMarkerCreateInput!) {{
    sceneMarkerCreate(input: $input) {{
        {MARKER_FIELDS}
    }}
}}
"""

UPDATE_MARKER_MUTATION = f"""
mutation UpdateMarker($input: SceneMarkerUpdateInput!) {{
    sceneMarkerUpdate(input: $input) {{
        {MARKER_FIELDS}
    }}
}}
"""

# Scene marker tag query
SCENE_MARKER_TAG_QUERY = f"""
query FindSceneMarkerTags($scene_id: ID!) {{
    sceneMarkerTags(scene_id: $scene_id) {{
        tag {{
            {TAG_FIELDS}
        }}
        scene_markers {{
            {MARKER_FIELDS}
        }}
    }}
}}
"""

# Tag mutations
TAGS_MERGE_MUTATION = f"""
mutation TagsMerge($input: TagsMergeInput!) {{
    tagsMerge(input: $input) {{
        {TAG_FIELDS}
    }}
}}
"""

BULK_TAG_UPDATE_MUTATION = f"""
mutation BulkTagUpdate($input: BulkTagUpdateInput!) {{
    bulkTagUpdate(input: $input) {{
        {TAG_FIELDS}
    }}
}}
"""

# Metadata mutations
METADATA_GENERATE_MUTATION = """
mutation MetadataGenerate($input: GenerateMetadataInput!) {
    metadataGenerate(input: $input)
}
"""

METADATA_CLEAN_MUTATION = """
mutation MetadataClean($input: CleanMetadataInput!) {
    metadataClean(input: $input)
}
"""

METADATA_CLEAN_GENERATED_MUTATION = """
mutation MetadataCleanGenerated($input: CleanGeneratedInput!) {
    metadataCleanGenerated(input: $input)
}
"""

METADATA_AUTO_TAG_MUTATION = """
mutation MetadataAutoTag($input: AutoTagMetadataInput!) {
    metadataAutoTag(input: $input)
}
"""

METADATA_IDENTIFY_MUTATION = """
mutation MetadataIdentify($input: IdentifyMetadataInput!) {
    metadataIdentify(input: $input)
}
"""

METADATA_IMPORT_MUTATION = """
mutation MetadataImport {
    metadataImport
}
"""

METADATA_EXPORT_MUTATION = """
mutation MetadataExport {
    metadataExport
}
"""

EXPORT_OBJECTS_MUTATION = """
mutation ExportObjects($input: ExportObjectsInput!) {
    exportObjects(input: $input)
}
"""

IMPORT_OBJECTS_MUTATION = """
mutation ImportObjects($input: ImportObjectsInput!) {
    importObjects(input: $input)
}
"""

BACKUP_DATABASE_MUTATION = """
mutation BackupDatabase($input: BackupDatabaseInput!) {
    backupDatabase(input: $input)
}
"""

ANONYMISE_DATABASE_MUTATION = """
mutation AnonymiseDatabase($input: AnonymiseDatabaseInput!) {
    anonymiseDatabase(input: $input)
}
"""

# Migration mutations
MIGRATE_MUTATION = """
mutation Migrate($input: MigrateInput!) {
    migrate(input: $input)
}
"""

MIGRATE_HASH_NAMING_MUTATION = """
mutation MigrateHashNaming {
    migrateHashNaming
}
"""

MIGRATE_SCENE_SCREENSHOTS_MUTATION = """
mutation MigrateSceneScreenshots($input: MigrateSceneScreenshotsInput!) {
    migrateSceneScreenshots(input: $input)
}
"""

MIGRATE_BLOBS_MUTATION = """
mutation MigrateBlobs($input: MigrateBlobsInput!) {
    migrateBlobs(input: $input)
}
"""

# Configuration mutations
CONFIGURE_GENERAL_MUTATION = """
mutation ConfigureGeneral($input: ConfigGeneralInput!) {
    configureGeneral(input: $input) {
        databasePath
        parallelTasks
    }
}
"""

CONFIGURE_INTERFACE_MUTATION = """
mutation ConfigureInterface($input: ConfigInterfaceInput!) {
    configureInterface(input: $input) {
        menuItems
        soundOnPreview
        wallShowTitle
        wallPlayback
        maximumLoopDuration
        autostartVideo
        autostartVideoOnPlaySelected
        continuePlaylistDefault
        showStudioAsText
        noBrowser
        notificationsEnabled
        language
    }
}
"""

CONFIGURE_DLNA_MUTATION = """
mutation ConfigureDLNA($input: ConfigDLNAInput!) {
    configureDLNA(input: $input) {
        serverName
        enabled
        port
        whitelistedIPs
        interfaces
        videoSortOrder
    }
}
"""

CONFIGURE_DEFAULTS_MUTATION = """
mutation ConfigureDefaults($input: ConfigDefaultSettingsInput!) {
    configureDefaults(input: $input) {
        deleteFile
        deleteGenerated
    }
}
"""

CONFIGURE_UI_MUTATION = """
mutation ConfigureUI($input: Map, $partial: Map) {
    configureUI(input: $input, partial: $partial)
}
"""

CONFIGURE_UI_SETTING_MUTATION = """
mutation ConfigureUISetting($key: String!, $value: Any) {
    configureUISetting(key: $key, value: $value)
}
"""

GENERATE_API_KEY_MUTATION = """
mutation GenerateAPIKey($input: GenerateAPIKeyInput!) {
    generateAPIKey(input: $input)
}
"""

# System status query
SYSTEM_STATUS_FIELDS = """
    __typename
    databaseSchema
    databasePath
    configPath
    appSchema
    status
    os
    workingDir
    homeDir
    ffmpegPath
    ffprobePath
"""

SYSTEM_STATUS_QUERY = f"""
query SystemStatus {{
    systemStatus {{
        {SYSTEM_STATUS_FIELDS}
    }}
}}
"""

# File query templates
FIND_FILE_QUERY = f"""
{FILE_FIELDS}
{VIDEO_FILE_FIELDS}
{IMAGE_FILE_FIELDS}
{GALLERY_FILE_FIELDS}
query FindFile($id: ID, $path: String) {{
    findFile(id: $id, path: $path) {{
        __typename
        ...FileFields
        ... on VideoFile {{
            ...VideoFileFields
        }}
        ... on ImageFile {{
            ...ImageFileFields
        }}
        ... on GalleryFile {{
            ...GalleryFileFields
        }}
    }}
}}
"""

FIND_FILES_QUERY = f"""
{FILE_FIELDS}
{VIDEO_FILE_FIELDS}
{IMAGE_FILE_FIELDS}
{GALLERY_FILE_FIELDS}
query FindFiles($file_filter: FileFilterType, $filter: FindFilterType, $ids: [ID!]) {{
    findFiles(file_filter: $file_filter, filter: $filter, ids: $ids) {{
        count
        megapixels
        duration
        size
        files {{
            __typename
            ...FileFields
            ... on VideoFile {{
                ...VideoFileFields
            }}
            ... on ImageFile {{
                ...ImageFileFields
            }}
            ... on GalleryFile {{
                ...GalleryFileFields
            }}
        }}
    }}
}}
"""

MOVE_FILES_MUTATION = """
mutation MoveFiles($input: MoveFilesInput!) {
    moveFiles(input: $input)
}
"""

FILE_SET_FINGERPRINTS_MUTATION = """
mutation FileSetFingerprints($input: FileSetFingerprintsInput!) {
    fileSetFingerprints(input: $input)
}
"""

# Scene file operations
SCENE_ASSIGN_FILE_MUTATION = """
mutation SceneAssignFile($input: AssignSceneFileInput!) {
    sceneAssignFile(input: $input)
}
"""

FIND_SCENE_BY_HASH_QUERY = f"""
{SCENE_QUERY_FRAGMENTS}
query FindSceneByHash($input: SceneHashInput!) {{
    findSceneByHash(input: $input) {{
        ...SceneFragment
    }}
}}
"""

# Version query templates
VERSION_QUERY = """
query Version {
    version {
        version
        hash
        build_time
    }
}
"""

LATEST_VERSION_QUERY = """
query LatestVersion {
    latestversion {
        version
        shorthash
        release_date
        url
    }
}
"""

# Deletion mutations
# Scene deletions
SCENE_DESTROY_MUTATION = """
mutation SceneDestroy($input: SceneDestroyInput!) {
    sceneDestroy(input: $input)
}
"""

SCENES_DESTROY_MUTATION = """
mutation ScenesDestroy($input: ScenesDestroyInput!) {
    scenesDestroy(input: $input)
}
"""

# Image deletions
IMAGE_DESTROY_MUTATION = """
mutation ImageDestroy($input: ImageDestroyInput!) {
    imageDestroy(input: $input)
}
"""

IMAGES_DESTROY_MUTATION = """
mutation ImagesDestroy($input: ImagesDestroyInput!) {
    imagesDestroy(input: $input)
}
"""

# Performer deletions
PERFORMER_DESTROY_MUTATION = """
mutation PerformerDestroy($input: PerformerDestroyInput!) {
    performerDestroy(input: $input)
}
"""

PERFORMERS_DESTROY_MUTATION = """
mutation PerformersDestroy($ids: [ID!]!) {
    performersDestroy(ids: $ids)
}
"""

# Studio deletions
STUDIO_DESTROY_MUTATION = """
mutation StudioDestroy($input: StudioDestroyInput!) {
    studioDestroy(input: $input)
}
"""

STUDIOS_DESTROY_MUTATION = """
mutation StudiosDestroy($ids: [ID!]!) {
    studiosDestroy(ids: $ids)
}
"""

# Tag deletions
TAG_DESTROY_MUTATION = """
mutation TagDestroy($input: TagDestroyInput!) {
    tagDestroy(input: $input)
}
"""

TAGS_DESTROY_MUTATION = """
mutation TagsDestroy($ids: [ID!]!) {
    tagsDestroy(ids: $ids)
}
"""

# Scene Marker deletions
SCENE_MARKER_DESTROY_MUTATION = """
mutation SceneMarkerDestroy($id: ID!) {
    sceneMarkerDestroy(id: $id)
}
"""

SCENE_MARKERS_DESTROY_MUTATION = """
mutation SceneMarkersDestroy($ids: [ID!]!) {
    sceneMarkersDestroy(ids: $ids)
}
"""

# File deletion
DELETE_FILES_MUTATION = """
mutation DeleteFiles($ids: [ID!]!) {
    deleteFiles(ids: $ids)
}
"""

# Bulk update mutations
BULK_PERFORMER_UPDATE_MUTATION = f"""
mutation BulkPerformerUpdate($input: BulkPerformerUpdateInput!) {{
    bulkPerformerUpdate(input: $input) {{
        {PERFORMER_FIELDS}
    }}
}}
"""

PERFORMER_MERGE_MUTATION = f"""
mutation PerformerMerge($input: PerformerMergeInput!) {{
    performerMerge(input: $input) {{
        {PERFORMER_FIELDS}
    }}
}}
"""

BULK_STUDIO_UPDATE_MUTATION = f"""
mutation BulkStudioUpdate($input: BulkStudioUpdateInput!) {{
    bulkStudioUpdate(input: $input) {{
        {STUDIO_FIELDS}
    }}
}}
"""

BULK_IMAGE_UPDATE_MUTATION = f"""
mutation BulkImageUpdate($input: BulkImageUpdateInput!) {{
    bulkImageUpdate(input: $input) {{
        {IMAGE_FIELDS}
    }}
}}
"""

BULK_SCENE_MARKER_UPDATE_MUTATION = f"""
mutation BulkSceneMarkerUpdate($input: BulkSceneMarkerUpdateInput!) {{
    bulkSceneMarkerUpdate(input: $input) {{
        {MARKER_FIELDS}
    }}
}}
"""

# Folder fragments and queries
_BASE_FOLDER_FIELDS = """fragment FolderFields on Folder {
    __typename
    id
    path
    parent_folder {
        __typename
        id
        path
    }
    zip_file {
        __typename
        id
        path
    }
    mod_time
    created_at
    updated_at
}"""
FOLDER_FIELDS = _BASE_FOLDER_FIELDS

FIND_FOLDER_QUERY = f"""
{FOLDER_FIELDS}
query FindFolder($id: ID, $path: String) {{
    findFolder(id: $id, path: $path) {{
        ...FolderFields
    }}
}}
"""

FIND_FOLDERS_QUERY = f"""
{FOLDER_FIELDS}
query FindFolders($folder_filter: FolderFilterType, $filter: FindFilterType, $ids: [ID!]) {{
    findFolders(folder_filter: $folder_filter, filter: $filter, ids: $ids) {{
        count
        folders {{
            ...FolderFields
        }}
    }}
}}
"""

# Group fragments
_BASE_GROUP_FIELDS = """fragment GroupFields on Group {
    __typename
    id
    created_at
    updated_at
    name
    aliases
    duration
    date
    rating100
    director
    synopsis
    urls
    front_image_path
    back_image_path
    studio {
        __typename
        id
    }
    tags {
        __typename
        id
    }
    scenes {
        __typename
        id
    }
    containing_groups {
        __typename
        group {
            __typename
            id
        }
        description
    }
    sub_groups {
        __typename
        group {
            __typename
            id
        }
        description
    }
}"""
GROUP_FIELDS = _BASE_GROUP_FIELDS

FIND_GROUP_QUERY = f"""
{GROUP_FIELDS}
query FindGroup($id: ID!) {{
    findGroup(id: $id) {{
        ...GroupFields
    }}
}}
"""

FIND_GROUPS_QUERY = f"""
{GROUP_FIELDS}
query FindGroups($filter: FindFilterType, $group_filter: GroupFilterType, $ids: [ID!]) {{
    findGroups(filter: $filter, group_filter: $group_filter, ids: $ids) {{
        count
        groups {{
            ...GroupFields
        }}
    }}
}}
"""

CREATE_GROUP_MUTATION = f"""
{GROUP_FIELDS}
mutation CreateGroup($input: GroupCreateInput!) {{
    groupCreate(input: $input) {{
        ...GroupFields
    }}
}}
"""

UPDATE_GROUP_MUTATION = f"""
{GROUP_FIELDS}
mutation UpdateGroup($input: GroupUpdateInput!) {{
    groupUpdate(input: $input) {{
        ...GroupFields
    }}
}}
"""

GROUP_DESTROY_MUTATION = """
mutation GroupDestroy($input: GroupDestroyInput!) {
    groupDestroy(input: $input)
}
"""

GROUPS_DESTROY_MUTATION = """
mutation GroupsDestroy($ids: [ID!]!) {
    groupsDestroy(ids: $ids)
}
"""

BULK_GROUP_UPDATE_MUTATION = f"""
{GROUP_FIELDS}
mutation BulkGroupUpdate($input: BulkGroupUpdateInput!) {{
    bulkGroupUpdate(input: $input) {{
        ...GroupFields
    }}
}}
"""

ADD_GROUP_SUB_GROUPS_MUTATION = """
mutation AddGroupSubGroups($input: GroupSubGroupAddInput!) {
    addGroupSubGroups(input: $input)
}
"""

REMOVE_GROUP_SUB_GROUPS_MUTATION = """
mutation RemoveGroupSubGroups($input: GroupSubGroupRemoveInput!) {
    removeGroupSubGroups(input: $input)
}
"""

REORDER_SUB_GROUPS_MUTATION = """
mutation ReorderSubGroups($input: ReorderSubGroupsInput!) {
    reorderSubGroups(input: $input)
}
"""

# System Statistics and Logging queries
STATS_QUERY = """
query Stats {
    stats {
        scene_count
        scenes_size
        scenes_duration
        image_count
        images_size
        gallery_count
        performer_count
        studio_count
        group_count
        tag_count
        total_o_count
        total_play_duration
        total_play_count
        scenes_played
    }
}
"""

LOGS_QUERY = """
query Logs {
    logs {
        time
        level
        message
    }
}
"""

# Marker query methods
MARKER_WALL_QUERY = f"""
query MarkerWall($q: String) {{
    markerWall(q: $q) {{
        {MARKER_FIELDS}
    }}
}}
"""

MARKER_STRINGS_QUERY = """
query MarkerStrings($q: String, $sort: String) {
    markerStrings(q: $q, sort: $sort) {
        count
        id
        title
    }
}
"""

# Scene query and mutation methods
SCENE_STREAMS_QUERY = """
query SceneStreams($id: ID!) {
    sceneStreams(id: $id) {
        url
        mime_type
        label
    }
}
"""

SCENE_ADD_O_MUTATION = """
mutation SceneAddO($id: ID!, $times: [Timestamp!]) {
    sceneAddO(id: $id, times: $times) {
        count
        history
    }
}
"""

SCENE_DELETE_O_MUTATION = """
mutation SceneDeleteO($id: ID!, $times: [Timestamp!]) {
    sceneDeleteO(id: $id, times: $times) {
        count
        history
    }
}
"""

SCENE_RESET_O_MUTATION = """
mutation SceneResetO($id: ID!) {
    sceneResetO(id: $id)
}
"""

SCENE_SAVE_ACTIVITY_MUTATION = """
mutation SceneSaveActivity($id: ID!, $resume_time: Float, $playDuration: Float) {
    sceneSaveActivity(id: $id, resume_time: $resume_time, playDuration: $playDuration)
}
"""

SCENE_RESET_ACTIVITY_MUTATION = """
mutation SceneResetActivity($id: ID!, $reset_resume: Boolean!, $reset_duration: Boolean!) {
    sceneResetActivity(id: $id, reset_resume: $reset_resume, reset_duration: $reset_duration)
}
"""

SCENE_ADD_PLAY_MUTATION = """
mutation SceneAddPlay($id: ID!, $times: [Timestamp!]) {
    sceneAddPlay(id: $id, times: $times) {
        count
        history
    }
}
"""

SCENE_DELETE_PLAY_MUTATION = """
mutation SceneDeletePlay($id: ID!, $times: [Timestamp!]) {
    sceneDeletePlay(id: $id, times: $times) {
        count
        history
    }
}
"""

SCENE_RESET_PLAY_COUNT_MUTATION = """
mutation SceneResetPlayCount($id: ID!) {
    sceneResetPlayCount(id: $id)
}
"""

# =============================================================================
# Image Operations
# =============================================================================

IMAGES_UPDATE_MUTATION = f"""
{IMAGE_QUERY_FRAGMENTS}
mutation ImagesUpdate($input: [ImageUpdateInput!]!) {{
    imagesUpdate(input: $input) {{
        ...ImageFragment
    }}
}}
"""

# =============================================================================
# Gallery Operations
# =============================================================================

BULK_GALLERY_UPDATE_MUTATION = f"""
{GALLERY_QUERY_FRAGMENTS}
mutation BulkGalleryUpdate($input: BulkGalleryUpdateInput!) {{
    bulkGalleryUpdate(input: $input) {{
        ...GalleryFragment
    }}
}}
"""

# =============================================================================
# Filter Operations
# =============================================================================

SAVED_FILTER_FIELDS = """
    __typename
    id
    mode
    name
    find_filter {
        __typename
        q
        page
        per_page
        sort
        direction
    }
    object_filter
    ui_options
"""

FIND_SAVED_FILTER_QUERY = f"""
query FindSavedFilter($id: ID!) {{
    findSavedFilter(id: $id) {{
        {SAVED_FILTER_FIELDS}
    }}
}}
"""

FIND_SAVED_FILTERS_QUERY = f"""
query FindSavedFilters($mode: FilterMode) {{
    findSavedFilters(mode: $mode) {{
        {SAVED_FILTER_FIELDS}
    }}
}}
"""

SAVE_FILTER_MUTATION = f"""
mutation SaveFilter($input: SaveFilterInput!) {{
    saveFilter(input: $input) {{
        {SAVED_FILTER_FIELDS}
    }}
}}
"""

DESTROY_SAVED_FILTER_MUTATION = """
mutation DestroySavedFilter($input: DestroyFilterInput!) {
    destroySavedFilter(input: $input)
}
"""

# =============================================================================
# Database Operations
# =============================================================================

OPTIMISE_DATABASE_MUTATION = """
mutation OptimiseDatabase {
    optimiseDatabase
}
"""

# =============================================================================
# Performer Operations
# =============================================================================

ALL_PERFORMERS_QUERY = f"""
query AllPerformers {{
    allPerformers {{
        {PERFORMER_FIELDS}
    }}
}}
"""

# =============================================================================
# Scene Path Regex Query
# =============================================================================

FIND_SCENES_BY_PATH_REGEX_QUERY = f"""
{SCENE_QUERY_FRAGMENTS}
query FindScenesByPathRegex($filter: FindFilterType) {{
    findScenesByPathRegex(filter: $filter) {{
        count
        duration
        filesize
        scenes {{
            ...SceneFragment
        }}
    }}
}}
"""

# =============================================================================
# StashBox Operations
# =============================================================================

VALIDATE_STASHBOX_CREDENTIALS_QUERY = """
query ValidateStashBoxCredentials($input: StashBoxInput!) {
    validateStashBoxCredentials(input: $input) {
        valid
        status
    }
}
"""

SUBMIT_STASHBOX_FINGERPRINTS_MUTATION = """
mutation SubmitStashBoxFingerprints($input: StashBoxFingerprintSubmissionInput!) {
    submitStashBoxFingerprints(input: $input)
}
"""

SUBMIT_STASHBOX_SCENE_DRAFT_MUTATION = """
mutation SubmitStashBoxSceneDraft($input: StashBoxDraftSubmissionInput!) {
    submitStashBoxSceneDraft(input: $input)
}
"""

SUBMIT_STASHBOX_PERFORMER_DRAFT_MUTATION = """
mutation SubmitStashBoxPerformerDraft($input: StashBoxDraftSubmissionInput!) {
    submitStashBoxPerformerDraft(input: $input)
}
"""

STASHBOX_BATCH_PERFORMER_TAG_MUTATION = """
mutation StashBoxBatchPerformerTag($input: StashBoxBatchTagInput!) {
    stashBoxBatchPerformerTag(input: $input)
}
"""

STASHBOX_BATCH_STUDIO_TAG_MUTATION = """
mutation StashBoxBatchStudioTag($input: StashBoxBatchTagInput!) {
    stashBoxBatchStudioTag(input: $input)
}
"""

STASHBOX_BATCH_TAG_TAG_MUTATION = """
mutation StashBoxBatchTagTag($input: StashBoxBatchTagInput!) {
    stashBoxBatchTagTag(input: $input)
}
"""

DESTROY_FILES_MUTATION = """
mutation DestroyFiles($ids: [ID!]!) {
    destroyFiles(ids: $ids)
}
"""

REVEAL_FILE_IN_FILE_MANAGER_MUTATION = """
mutation RevealFileInFileManager($id: ID!) {
    revealFileInFileManager(id: $id)
}
"""

REVEAL_FOLDER_IN_FILE_MANAGER_MUTATION = """
mutation RevealFolderInFileManager($id: ID!) {
    revealFolderInFileManager(id: $id)
}
"""

# =============================================================================
# DLNA Operations
# =============================================================================

DLNA_STATUS_QUERY = """
query DLNAStatus {
    dlnaStatus {
        running
        until
        recentIPAddresses
        allowedIPAddresses {
            __typename
            ipAddress
            until
        }
    }
}
"""

ENABLE_DLNA_MUTATION = """
mutation EnableDLNA($input: EnableDLNAInput!) {
    enableDLNA(input: $input)
}
"""

DISABLE_DLNA_MUTATION = """
mutation DisableDLNA($input: DisableDLNAInput!) {
    disableDLNA(input: $input)
}
"""

ADD_TEMP_DLNA_IP_MUTATION = """
mutation AddTempDLNAIP($input: AddTempDLNAIPInput!) {
    addTempDLNAIP(input: $input)
}
"""

REMOVE_TEMP_DLNA_IP_MUTATION = """
mutation RemoveTempDLNAIP($input: RemoveTempDLNAIPInput!) {
    removeTempDLNAIP(input: $input)
}
"""

# =============================================================================
# Directory Operations
# =============================================================================

DIRECTORY_QUERY = """
query Directory($path: String, $locale: String) {
    directory(path: $path, locale: $locale) {
        path
        parent
        directories
    }
}
"""

# =============================================================================
# System Setup Operations
# =============================================================================

SETUP_MUTATION = """
mutation Setup($input: SetupInput!) {
    setup(input: $input)
}
"""

DOWNLOAD_FFMPEG_MUTATION = """
mutation DownloadFFMpeg {
    downloadFFMpeg
}
"""

CONFIGURE_SCRAPING_MUTATION = """
mutation ConfigureScraping($input: ConfigScrapingInput!) {
    configureScraping(input: $input) {
        scraperUserAgent
        scraperCDPPath
        scraperCertCheck
        excludeTagPatterns
        scraperPackageSources
    }
}
"""

# SQL query mutations
SQL_QUERY_MUTATION = """
mutation QuerySQL($sql: String!, $args: [Any]) {
    querySQL(sql: $sql, args: $args) {
        columns
        rows
    }
}
"""

SQL_EXEC_MUTATION = """
mutation ExecSQL($sql: String!, $args: [Any]) {
    execSQL(sql: $sql, args: $args) {
        rows_affected
        last_insert_id
    }
}
"""


# =============================================================================
# FragmentStore — capability-aware fragment and query builder
# =============================================================================


def _inject_named_fragment_fields(base: str, extra_fields: str) -> str:
    """Insert extra fields into a named GraphQL fragment before the closing brace.

    Named fragments have the form ``fragment Xxx on Yyy { ... }``.
    This helper finds the *last* ``}`` and inserts the extra fields before it.
    """
    idx = base.rfind("}")
    if idx == -1:
        return base + extra_fields
    return base[:idx] + extra_fields + "\n" + base[idx:]


class FragmentStore:
    """Capability-aware store for GraphQL field fragments and query strings.

    On construction (or when ``rebuild()`` is called) the store assembles the
    correct field-strings for the connected Stash server and rebuilds every
    query / mutation that embeds those fields.

    Attributes set on the instance mirror the module-level constants but may
    contain additional fields gated behind ``ServerCapabilities`` checks.
    """

    def __init__(self) -> None:
        self._capabilities: ServerCapabilities | None = None
        self._build_base()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def rebuild(self, capabilities: ServerCapabilities) -> None:
        """Rebuild all fields and queries for the given server capabilities."""
        self._capabilities = capabilities
        self._build_fields()
        self._build_queries()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_base(self) -> None:
        """Initialise with the base (minimum-version) field strings."""
        self.SCENE_FIELDS = _BASE_SCENE_FIELDS
        self.PERFORMER_FIELDS = _BASE_PERFORMER_FIELDS
        self.STUDIO_FIELDS = _BASE_STUDIO_FIELDS
        self.TAG_FIELDS = _BASE_TAG_FIELDS
        self.GALLERY_FIELDS = _BASE_GALLERY_FIELDS
        self.IMAGE_FIELDS = _BASE_IMAGE_FIELDS
        self.GROUP_FIELDS = _BASE_GROUP_FIELDS
        self.FOLDER_FIELDS = _BASE_FOLDER_FIELDS
        self._build_queries()

    def _build_fields(self) -> None:
        """Build capability-aware field strings from base constants."""
        caps = self._capabilities
        if caps is None:
            self._build_base()
            return

        # -- Scene --
        scene = _BASE_SCENE_FIELDS
        if caps.has_scene_custom_fields:
            scene += "    custom_fields\n"
        self.SCENE_FIELDS = scene

        # -- Performer --
        performer = _BASE_PERFORMER_FIELDS
        if caps.has_performer_career_start_end:
            performer += "    career_start\n    career_end\n"
        self.PERFORMER_FIELDS = performer

        # -- Studio --
        studio = _BASE_STUDIO_FIELDS
        extras = ""
        if caps.has_studio_custom_fields:
            extras += "    custom_fields\n"
        if caps.has_studio_organized:
            extras += "    organized\n"
        self.STUDIO_FIELDS = studio + extras

        # -- Tag --
        tag = _BASE_TAG_FIELDS
        if caps.has_tag_custom_fields:
            tag += "    custom_fields\n"
        self.TAG_FIELDS = tag

        # -- Gallery --
        gallery = _BASE_GALLERY_FIELDS
        if caps.has_gallery_custom_fields:
            gallery += "    custom_fields\n"
        self.GALLERY_FIELDS = gallery

        # -- Image --
        image = _BASE_IMAGE_FIELDS
        if caps.has_image_custom_fields:
            image += "    custom_fields\n"
        self.IMAGE_FIELDS = image

        # -- Group (named fragment — inject before closing brace) --
        group = _BASE_GROUP_FIELDS
        if caps.has_group_custom_fields:
            group = _inject_named_fragment_fields(group, "    custom_fields")
        self.GROUP_FIELDS = group

        # -- Folder (named fragment — inject before closing brace) --
        folder = _BASE_FOLDER_FIELDS
        if caps.has_folder_basename:
            folder = _inject_named_fragment_fields(folder, "    basename")
            folder = _inject_named_fragment_fields(
                folder,
                "    parent_folders {\n        __typename\n        id\n        path\n    }",
            )
        self.FOLDER_FIELDS = folder

    def _build_queries(self) -> None:
        """Rebuild all query strings from the current field strings.

        This mirrors the module-level f-string constants but uses
        ``self.<FIELD>`` so the queries pick up capability-gated fields.
        """
        # ---- Scene queries ----
        self.SCENE_QUERY_FRAGMENTS = f"""
{FILE_FIELDS}
{VIDEO_FILE_FIELDS}
fragment SceneFragment on Scene {{
    {self.SCENE_FIELDS}
}}
"""

        self.FIND_SCENE_QUERY = f"""
{self.SCENE_QUERY_FRAGMENTS}
query FindScene($id: ID!) {{
    findScene(id: $id) {{
        ...SceneFragment
    }}
}}
"""

        self.FIND_SCENES_QUERY = f"""
{self.SCENE_QUERY_FRAGMENTS}
query FindScenes($filter: FindFilterType, $scene_filter: SceneFilterType) {{
    findScenes(filter: $filter, scene_filter: $scene_filter) {{
        count
        duration
        filesize
        scenes {{
            ...SceneFragment
        }}
    }}
}}
"""

        self.CREATE_SCENE_MUTATION = f"""
{self.SCENE_QUERY_FRAGMENTS}
mutation CreateScene($input: SceneCreateInput!) {{
    sceneCreate(input: $input) {{
        ...SceneFragment
    }}
}}
"""

        self.UPDATE_SCENE_MUTATION = f"""
{self.SCENE_QUERY_FRAGMENTS}
mutation UpdateScene($input: SceneUpdateInput!) {{
    sceneUpdate(input: $input) {{
        ...SceneFragment
    }}
}}
"""

        self.FIND_DUPLICATE_SCENES_QUERY = f"""
{self.SCENE_QUERY_FRAGMENTS}
query FindDuplicateScenes($distance: Int, $duration_diff: Float) {{
    findDuplicateScenes(distance: $distance, duration_diff: $duration_diff) {{
        ...SceneFragment
    }}
}}
"""

        self.SCENE_WALL_QUERY = f"""
{self.SCENE_QUERY_FRAGMENTS}
query SceneWall($q: String) {{
    sceneWall(q: $q) {{
        ...SceneFragment
    }}
}}
"""

        self.BULK_SCENE_UPDATE_MUTATION = f"""
{self.SCENE_QUERY_FRAGMENTS}
mutation BulkSceneUpdate($input: BulkSceneUpdateInput!) {{
    bulkSceneUpdate(input: $input) {{
        ...SceneFragment
    }}
}}
"""

        self.SCENES_UPDATE_MUTATION = f"""
{self.SCENE_QUERY_FRAGMENTS}
mutation ScenesUpdate($input: [SceneUpdateInput!]!) {{
    scenesUpdate(input: $input) {{
        ...SceneFragment
    }}
}}
"""

        self.SCENE_MERGE_MUTATION = f"""
{self.SCENE_QUERY_FRAGMENTS}
mutation SceneMerge($input: SceneMergeInput!) {{
    sceneMerge(input: $input) {{
        ...SceneFragment
    }}
}}
"""

        self.FIND_SCENE_BY_HASH_QUERY = f"""
{self.SCENE_QUERY_FRAGMENTS}
query FindSceneByHash($input: SceneHashInput!) {{
    findSceneByHash(input: $input) {{
        ...SceneFragment
    }}
}}
"""

        self.FIND_SCENES_BY_PATH_REGEX_QUERY = f"""
{self.SCENE_QUERY_FRAGMENTS}
query FindScenesByPathRegex($filter: FindFilterType) {{
    findScenesByPathRegex(filter: $filter) {{
        count
        duration
        filesize
        scenes {{
            ...SceneFragment
        }}
    }}
}}
"""

        # ---- Performer queries ----
        self.FIND_PERFORMER_QUERY = f"""
query FindPerformer($id: ID!) {{
    findPerformer(id: $id) {{
        {self.PERFORMER_FIELDS}
    }}
}}
"""

        self.FIND_PERFORMERS_QUERY = f"""
query FindPerformers($filter: FindFilterType, $performer_filter: PerformerFilterType) {{
    findPerformers(filter: $filter, performer_filter: $performer_filter) {{
        count
        performers {{
            {self.PERFORMER_FIELDS}
        }}
    }}
}}
"""

        self.CREATE_PERFORMER_MUTATION = f"""
mutation CreatePerformer($input: PerformerCreateInput!) {{
    performerCreate(input: $input) {{
        {self.PERFORMER_FIELDS}
    }}
}}
"""

        self.UPDATE_PERFORMER_MUTATION = f"""
mutation UpdatePerformer($input: PerformerUpdateInput!) {{
    performerUpdate(input: $input) {{
        {self.PERFORMER_FIELDS}
    }}
}}
"""

        self.BULK_PERFORMER_UPDATE_MUTATION = f"""
mutation BulkPerformerUpdate($input: BulkPerformerUpdateInput!) {{
    bulkPerformerUpdate(input: $input) {{
        {self.PERFORMER_FIELDS}
    }}
}}
"""

        self.PERFORMER_MERGE_MUTATION = f"""
mutation PerformerMerge($input: PerformerMergeInput!) {{
    performerMerge(input: $input) {{
        {self.PERFORMER_FIELDS}
    }}
}}
"""

        self.ALL_PERFORMERS_QUERY = f"""
query AllPerformers {{
    allPerformers {{
        {self.PERFORMER_FIELDS}
    }}
}}
"""

        # ---- Studio queries ----
        self.FIND_STUDIO_QUERY = f"""
query FindStudio($id: ID!) {{
    findStudio(id: $id) {{
        {self.STUDIO_FIELDS}
    }}
}}
"""

        self.FIND_STUDIOS_QUERY = f"""
query FindStudios($filter: FindFilterType, $studio_filter: StudioFilterType) {{
    findStudios(filter: $filter, studio_filter: $studio_filter) {{
        count
        studios {{
            {self.STUDIO_FIELDS}
        }}
    }}
}}
"""

        self.CREATE_STUDIO_MUTATION = f"""
mutation CreateStudio($input: StudioCreateInput!) {{
    studioCreate(input: $input) {{
        {self.STUDIO_FIELDS}
    }}
}}
"""

        self.UPDATE_STUDIO_MUTATION = f"""
mutation UpdateStudio($input: StudioUpdateInput!) {{
    studioUpdate(input: $input) {{
        {self.STUDIO_FIELDS}
    }}
}}
"""

        self.BULK_STUDIO_UPDATE_MUTATION = f"""
mutation BulkStudioUpdate($input: BulkStudioUpdateInput!) {{
    bulkStudioUpdate(input: $input) {{
        {self.STUDIO_FIELDS}
    }}
}}
"""

        # ---- Tag queries ----
        self.FIND_TAG_QUERY = f"""
query FindTag($id: ID!) {{
    findTag(id: $id) {{
        {self.TAG_FIELDS}
    }}
}}
"""

        self.FIND_TAGS_QUERY = f"""
query FindTags($filter: FindFilterType, $tag_filter: TagFilterType) {{
    findTags(filter: $filter, tag_filter: $tag_filter) {{
        count
        tags {{
            {self.TAG_FIELDS}
        }}
    }}
}}
"""

        self.CREATE_TAG_MUTATION = f"""
mutation CreateTag($input: TagCreateInput!) {{
    tagCreate(input: $input) {{
        {self.TAG_FIELDS}
    }}
}}
"""

        self.UPDATE_TAG_MUTATION = f"""
mutation UpdateTag($input: TagUpdateInput!) {{
    tagUpdate(input: $input) {{
        {self.TAG_FIELDS}
    }}
}}
"""

        self.TAGS_MERGE_MUTATION = f"""
mutation TagsMerge($input: TagsMergeInput!) {{
    tagsMerge(input: $input) {{
        {self.TAG_FIELDS}
    }}
}}
"""

        self.BULK_TAG_UPDATE_MUTATION = f"""
mutation BulkTagUpdate($input: BulkTagUpdateInput!) {{
    bulkTagUpdate(input: $input) {{
        {self.TAG_FIELDS}
    }}
}}
"""

        self.SCENE_MARKER_TAG_QUERY = f"""
query FindSceneMarkerTags($scene_id: ID!) {{
    sceneMarkerTags(scene_id: $scene_id) {{
        tag {{
            {self.TAG_FIELDS}
        }}
        scene_markers {{
            {MARKER_FIELDS}
        }}
    }}
}}
"""

        # ---- Gallery queries ----
        self.GALLERY_QUERY_FRAGMENTS = f"""
{FILE_FIELDS}
{GALLERY_FILE_FIELDS}
fragment GalleryFragment on Gallery {{
    {self.GALLERY_FIELDS}
}}
"""

        self.FIND_GALLERY_QUERY = f"""
{self.GALLERY_QUERY_FRAGMENTS}
query FindGallery($id: ID!) {{
    findGallery(id: $id) {{
        ...GalleryFragment
    }}
}}
"""

        self.FIND_GALLERIES_QUERY = f"""
{self.GALLERY_QUERY_FRAGMENTS}
query FindGalleries($filter: FindFilterType, $gallery_filter: GalleryFilterType) {{
    findGalleries(filter: $filter, gallery_filter: $gallery_filter) {{
        count
        galleries {{
            ...GalleryFragment
        }}
    }}
}}
"""

        self.CREATE_GALLERY_MUTATION = f"""
{self.GALLERY_QUERY_FRAGMENTS}
mutation CreateGallery($input: GalleryCreateInput!) {{
    galleryCreate(input: $input) {{
        ...GalleryFragment
    }}
}}
"""

        self.UPDATE_GALLERY_MUTATION = f"""
{self.GALLERY_QUERY_FRAGMENTS}
mutation UpdateGallery($input: GalleryUpdateInput!) {{
    galleryUpdate(input: $input) {{
        ...GalleryFragment
    }}
}}
"""

        self.GALLERIES_UPDATE_MUTATION = f"""
{self.GALLERY_QUERY_FRAGMENTS}
mutation GalleriesUpdate($input: [GalleryUpdateInput!]!) {{
    galleriesUpdate(input: $input) {{
        ...GalleryFragment
    }}
}}
"""

        self.GALLERY_CHAPTER_CREATE_MUTATION = f"""
{self.GALLERY_QUERY_FRAGMENTS}
mutation GalleryChapterCreate($input: GalleryChapterCreateInput!) {{
    galleryChapterCreate(input: $input) {{
        id
        title
        image_index
        gallery {{
            ...GalleryFragment
        }}
    }}
}}
"""

        self.GALLERY_CHAPTER_UPDATE_MUTATION = f"""
{self.GALLERY_QUERY_FRAGMENTS}
mutation GalleryChapterUpdate($input: GalleryChapterUpdateInput!) {{
    galleryChapterUpdate(input: $input) {{
        id
        title
        image_index
        gallery {{
            ...GalleryFragment
        }}
    }}
}}
"""

        self.BULK_GALLERY_UPDATE_MUTATION = f"""
{self.GALLERY_QUERY_FRAGMENTS}
mutation BulkGalleryUpdate($input: BulkGalleryUpdateInput!) {{
    bulkGalleryUpdate(input: $input) {{
        ...GalleryFragment
    }}
}}
"""

        # ---- Image queries ----
        self.IMAGE_QUERY_FRAGMENTS = f"""
{FILE_FIELDS}
{IMAGE_FILE_FIELDS}
{VIDEO_FILE_FIELDS}
fragment ImageFragment on Image {{
    {self.IMAGE_FIELDS}
}}
"""

        self.FIND_IMAGE_QUERY = f"""
{self.IMAGE_QUERY_FRAGMENTS}
query FindImage($id: ID!) {{
    findImage(id: $id) {{
        ...ImageFragment
    }}
}}
"""

        self.FIND_IMAGES_QUERY = f"""
{self.IMAGE_QUERY_FRAGMENTS}
query FindImages($filter: FindFilterType, $image_filter: ImageFilterType) {{
    findImages(filter: $filter, image_filter: $image_filter) {{
        count
        megapixels
        filesize
        images {{
            ...ImageFragment
        }}
    }}
}}
"""

        self.CREATE_IMAGE_MUTATION = f"""
{self.IMAGE_QUERY_FRAGMENTS}
mutation CreateImage($input: ImageCreateInput!) {{
    imageCreate(input: $input) {{
        ...ImageFragment
    }}
}}
"""

        self.UPDATE_IMAGE_MUTATION = f"""
{self.IMAGE_QUERY_FRAGMENTS}
mutation UpdateImage($input: ImageUpdateInput!) {{
    imageUpdate(input: $input) {{
        ...ImageFragment
    }}
}}
"""

        self.BULK_IMAGE_UPDATE_MUTATION = f"""
{self.IMAGE_QUERY_FRAGMENTS}
mutation BulkImageUpdate($input: BulkImageUpdateInput!) {{
    bulkImageUpdate(input: $input) {{
        ...ImageFragment
    }}
}}
"""

        self.IMAGES_UPDATE_MUTATION = f"""
{self.IMAGE_QUERY_FRAGMENTS}
mutation ImagesUpdate($input: [ImageUpdateInput!]!) {{
    imagesUpdate(input: $input) {{
        ...ImageFragment
    }}
}}
"""

        # ---- Group queries ----
        self.FIND_GROUP_QUERY = f"""
{self.GROUP_FIELDS}
query FindGroup($id: ID!) {{
    findGroup(id: $id) {{
        ...GroupFields
    }}
}}
"""

        self.FIND_GROUPS_QUERY = f"""
{self.GROUP_FIELDS}
query FindGroups($filter: FindFilterType, $group_filter: GroupFilterType, $ids: [ID!]) {{
    findGroups(filter: $filter, group_filter: $group_filter, ids: $ids) {{
        count
        groups {{
            ...GroupFields
        }}
    }}
}}
"""

        self.CREATE_GROUP_MUTATION = f"""
{self.GROUP_FIELDS}
mutation CreateGroup($input: GroupCreateInput!) {{
    groupCreate(input: $input) {{
        ...GroupFields
    }}
}}
"""

        self.UPDATE_GROUP_MUTATION = f"""
{self.GROUP_FIELDS}
mutation UpdateGroup($input: GroupUpdateInput!) {{
    groupUpdate(input: $input) {{
        ...GroupFields
    }}
}}
"""

        self.BULK_GROUP_UPDATE_MUTATION = f"""
{self.GROUP_FIELDS}
mutation BulkGroupUpdate($input: BulkGroupUpdateInput!) {{
    bulkGroupUpdate(input: $input) {{
        ...GroupFields
    }}
}}
"""

        # ---- Folder queries ----
        self.FIND_FOLDER_QUERY = f"""
{self.FOLDER_FIELDS}
query FindFolder($id: ID, $path: String) {{
    findFolder(id: $id, path: $path) {{
        ...FolderFields
    }}
}}
"""

        self.FIND_FOLDERS_QUERY = f"""
{self.FOLDER_FIELDS}
query FindFolders($folder_filter: FolderFilterType, $filter: FindFilterType, $ids: [ID!]) {{
    findFolders(folder_filter: $folder_filter, filter: $filter, ids: $ids) {{
        count
        folders {{
            ...FolderFields
        }}
    }}
}}
"""


# Module-level singleton — used by all client mixins
fragment_store = FragmentStore()
