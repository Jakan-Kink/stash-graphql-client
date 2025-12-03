"""GraphQL fragments for Stash queries.

These fragments match the ones defined in schema/fragments.graphql.
"""

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

# Job fragments
JOB_FIELDS = """
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
    id
    path
    basename
    parent_folder {
        id
        path
    }
    zip_file {
        id
        path
    }
    size
    mod_time
    created_at
    updated_at
    fingerprints {
        type
        value
    }
}"""

VIDEO_FILE_FIELDS = """fragment VideoFileFields on VideoFile {
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
    ...FileFields
    format
    width
    height
}"""

GALLERY_FILE_FIELDS = """fragment GalleryFileFields on GalleryFile {
    ...FileFields
}"""

# Scene fragments
SCENE_FIELDS = """
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
        language_code
        caption_type
    }
    files {
        ...VideoFileFields
    }
    studio {
        id
    }
    performers {
        id
    }
    tags {
        id
    }
    stash_ids {
        endpoint
        stash_id
    }
    sceneStreams {
        url
        mime_type
        label
    }
"""

# Performer fragments
PERFORMER_FIELDS = """
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
        endpoint
        stash_id
    }
    tags {
        id
    }
    scenes {
        id
    }
    groups {
        id
    }
"""

# Studio fragments
STUDIO_FIELDS = """
    id
    created_at
    updated_at
    name
    urls
    image_path
    aliases
    details
    tags {
        id
    }
    parent_studio {
        id
    }
"""

# Tag fragments
TAG_FIELDS = """
    id
    created_at
    updated_at
    name
    description
    aliases
    image_path
    stash_ids {
        endpoint
        stash_id
    }
    parents {
        id
    }
    children {
        id
    }
"""

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
GALLERY_FIELDS = """
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
        id
    }
    scenes {
        id
    }
    performers {
        id
        name
    }
    tags {
        id
        name
    }
    files {
        ...GalleryFileFields
    }
"""

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
IMAGE_FIELDS = """
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
        id
    }
    performers {
        id
    }
    tags {
        id
        name
    }
    galleries {
        id
    }
    visual_files {
        ... on ImageFile {
            ...ImageFileFields
        }
        ... on VideoFile {
            ...VideoFileFields
        }
    }
"""

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

# Marker fragments
MARKER_FIELDS = """
    id
    created_at
    updated_at
    title
    seconds
    scene {
        id
    }
    primary_tag {
        id
    }
    tags {
        id
    }
"""

# Marker query templates
FIND_MARKER_QUERY = f"""
query FindMarker($id: ID!) {{
    findSceneMarker(id: $id) {{
        {MARKER_FIELDS}
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
FOLDER_FIELDS = """fragment FolderFields on Folder {
    id
    path
    parent_folder_id
    zip_file_id
    mod_time
    created_at
    updated_at
}"""

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
GROUP_FIELDS = """fragment GroupFields on Group {
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
        id
    }
    tags {
        id
    }
    scenes {
        id
    }
    containing_groups {
        group {
            id
        }
        description
    }
    sub_groups {
        group {
            id
        }
        description
    }
}"""

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
