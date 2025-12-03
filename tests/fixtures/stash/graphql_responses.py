"""Fixtures for Stash GraphQL responses using respx for edge mocking.

This module provides helper functions and fixtures for creating GraphQL response
data that matches the stash/types/*ResultType format. Use these with respx to mock
HTTP responses at the edge.

Key Principles:
- NO MagicMock for internal functions
- Use respx to mock GraphQL HTTP POST requests
- Provide real JSON responses matching Stash GraphQL schema
- Return data in the format that gql.Client.execute() returns

Usage:
    import respx
    import httpx
    from tests.fixtures.stash import create_graphql_response, create_find_tags_result

    @respx.mock
    async def test_find_tags(tag_mixin):
        # Create response data
        tags_data = create_find_tags_result(count=1, tags=[
            {"id": "123", "name": "test", "aliases": [], "parents": [], "children": []}
        ])

        # Mock the GraphQL HTTP endpoint
        respx.post("http://localhost:9999/graphql").mock(
            return_value=httpx.Response(
                200,
                json=create_graphql_response("findTags", tags_data)
            )
        )

        # Initialize client and test
        await tag_mixin.context.get_client()
        result = await tag_mixin.context.client.find_tags(tag_filter={"name": {"value": "test"}})
        assert result.count == 1
"""

from typing import Any


def create_graphql_response(
    operation: str, data: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Create a GraphQL response envelope.

    GraphQL responses have the format: {"data": {operationName: resultData}}

    Args:
        operation: The GraphQL operation name (e.g., "findTags", "tagCreate")
        data: The operation result data

    Returns:
        Complete GraphQL response dict

    Example:
        response = create_graphql_response("findTags", {
            "count": 1,
            "tags": [{"id": "123", "name": "test"}]
        })
        # Returns: {"data": {"findTags": {"count": 1, "tags": [...]}}}
    """
    if data is None:
        data = {}

    return {"data": {operation: data}}


def create_find_tags_result(
    count: int = 0, tags: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    """Create a findTags query result matching FindTagsResultType.

    Args:
        count: Total number of tags
        tags: List of tag dicts with fields: id, name, aliases, parents, children, description, image_path

    Returns:
        Dict matching FindTagsResultType schema

    Example:
        result = create_find_tags_result(count=2, tags=[
            {"id": "1", "name": "tag1", "aliases": [], "parents": [], "children": []},
            {"id": "2", "name": "tag2", "aliases": ["alias"], "parents": [], "children": []},
        ])
    """
    if tags is None:
        tags = []

    return {"count": count, "tags": tags}


def create_tag_dict(
    id: str,
    name: str,
    aliases: list[str] | None = None,
    parents: list[dict] | None = None,
    children: list[dict] | None = None,
    description: str | None = None,
    image_path: str | None = None,
    **kwargs,
) -> dict[str, Any]:
    """Create a Tag dict matching the Tag type schema.

    Args:
        id: Tag ID
        name: Tag name
        aliases: List of alias strings
        parents: List of parent tag dicts (recursive)
        children: List of child tag dicts (recursive)
        description: Tag description
        image_path: Path to tag image
        **kwargs: Additional tag fields (sort_name, favorite, ignore_auto_tag, stash_ids)

    Returns:
        Dict matching Tag type

    Example:
        tag = create_tag_dict(
            id="123",
            name="test_tag",
            aliases=["alias1", "alias2"],
            description="A test tag",
            favorite=True,
            ignore_auto_tag=False,
        )
    """
    base = {
        "id": id,
        "name": name,
        "aliases": aliases or [],
        "parents": parents or [],
        "children": children or [],
        "description": description,
        "image_path": image_path,
    }
    base.update(kwargs)
    return base


def create_tag_create_result(tag: dict[str, Any]) -> dict[str, Any]:
    """Create a tagCreate mutation result.

    Args:
        tag: Tag dict created with create_tag_dict()

    Returns:
        Dict matching the tagCreate mutation result

    Example:
        tag = create_tag_dict(id="123", name="new_tag")
        result = create_tag_create_result(tag)
        # Use with: create_graphql_response("tagCreate", result)
    """
    return tag


def create_find_performers_result(
    count: int = 0, performers: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    """Create a findPerformers query result matching FindPerformersResultType.

    Args:
        count: Total number of performers
        performers: List of performer dicts

    Returns:
        Dict matching FindPerformersResultType schema
    """
    if performers is None:
        performers = []

    return {"count": count, "performers": performers}


def create_performer_dict(
    id: str,
    name: str,
    urls: list[str] | None = None,
    gender: str | None = None,
    tags: list[dict] | None = None,
    stash_ids: list[dict] | None = None,
    **kwargs,
) -> dict[str, Any]:
    """Create a Performer dict matching the Performer type schema.

    Args:
        id: Performer ID
        name: Performer name
        urls: List of URL strings
        gender: Gender enum value
        tags: List of tag dicts
        stash_ids: List of StashID dicts
        **kwargs: Additional performer fields

    Returns:
        Dict matching Performer type
    """
    base = {
        "id": id,
        "name": name,
        "alias_list": [],
        "urls": urls or [],
        "gender": gender,
        "tags": tags or [],
        "stash_ids": stash_ids or [],
        "scenes": [],
        "groups": [],
    }
    base.update(kwargs)
    return base


def create_find_studios_result(
    count: int = 0, studios: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    """Create a findStudios query result matching FindStudiosResultType.

    Args:
        count: Total number of studios
        studios: List of studio dicts

    Returns:
        Dict matching FindStudiosResultType schema
    """
    if studios is None:
        studios = []

    return {"count": count, "studios": studios}


def create_studio_dict(
    id: str,
    name: str,
    urls: list[str] | None = None,
    parent_studio: dict | None = None,
    aliases: list[str] | None = None,
    tags: list[dict] | None = None,
    stash_ids: list[dict] | None = None,
    details: str | None = None,
    **kwargs,
) -> dict[str, Any]:
    """Create a Studio dict matching the Studio type schema.

    Args:
        id: Studio ID
        name: Studio name
        urls: List of studio URLs
        parent_studio: Parent studio dict (recursive)
        aliases: List of alias strings
        tags: List of tag dicts
        stash_ids: List of StashID dicts
        details: Studio details
        **kwargs: Additional studio fields (child_studios, groups, rating100, favorite, ignore_auto_tag)

    Returns:
        Dict matching Studio type
    """
    base = {
        "id": id,
        "name": name,
        "urls": urls or [],
        "parent_studio": parent_studio,
        "aliases": aliases or [],
        "tags": tags or [],
        "stash_ids": stash_ids or [],
        "details": details,
    }
    base.update(kwargs)
    return base


def create_find_scenes_result(
    count: int = 0,
    scenes: list[dict[str, Any]] | None = None,
    duration: float = 0.0,
    filesize: float = 0.0,
) -> dict[str, Any]:
    """Create a findScenes query result matching FindScenesResultType.

    Args:
        count: Total number of scenes
        scenes: List of scene dicts
        duration: Total duration of all scenes in seconds
        filesize: Total file size of all scenes in bytes

    Returns:
        Dict matching FindScenesResultType schema
    """
    if scenes is None:
        scenes = []

    return {
        "count": count,
        "scenes": scenes,
        "duration": duration,
        "filesize": filesize,
    }


def create_scene_dict(
    id: str,
    title: str,
    studio: dict | None = None,
    performers: list[dict] | None = None,
    tags: list[dict] | None = None,
    **kwargs,
) -> dict[str, Any]:
    """Create a Scene dict matching the Scene type schema.

    Args:
        id: Scene ID
        title: Scene title
        studio: Studio dict
        performers: List of performer dicts
        tags: List of tag dicts
        **kwargs: Additional scene fields

    Returns:
        Dict matching Scene type
    """
    base = {
        "id": id,
        "title": title,
        "studio": studio,
        "performers": performers or [],
        "tags": tags or [],
        "files": [],
        "urls": [],
        "stash_ids": [],
        "groups": [],
        "galleries": [],
        "scene_markers": [],
        "sceneStreams": [],
        "captions": [],
        "organized": False,
    }
    base.update(kwargs)
    return base


def create_find_images_result(
    count: int = 0,
    images: list[dict[str, Any]] | None = None,
    megapixels: float = 0.0,
    filesize: float = 0.0,
) -> dict[str, Any]:
    """Create a findImages query result matching FindImagesResultType.

    Args:
        count: Total number of images
        images: List of image dicts
        megapixels: Total megapixels of all images
        filesize: Total file size of all images in bytes

    Returns:
        Dict matching FindImagesResultType schema
    """
    if images is None:
        images = []

    return {
        "count": count,
        "images": images,
        "megapixels": megapixels,
        "filesize": filesize,
    }


def create_image_dict(
    id: str,
    title: str | None = None,
    studio: dict | None = None,
    performers: list[dict] | None = None,
    tags: list[dict] | None = None,
    **kwargs,
) -> dict[str, Any]:
    """Create an Image dict matching the Image type schema.

    Args:
        id: Image ID
        title: Image title
        studio: Studio dict
        performers: List of performer dicts
        tags: List of tag dicts
        **kwargs: Additional image fields

    Returns:
        Dict matching Image type
    """
    base = {
        "id": id,
        "title": title,
        "studio": studio,
        "performers": performers or [],
        "tags": tags or [],
        "visual_files": [],
        "urls": [],
        "galleries": [],
        "organized": False,
    }
    base.update(kwargs)
    return base


def create_find_galleries_result(
    count: int = 0, galleries: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    """Create a findGalleries query result matching FindGalleriesResultType.

    Args:
        count: Total number of galleries
        galleries: List of gallery dicts

    Returns:
        Dict matching FindGalleriesResultType schema
    """
    if galleries is None:
        galleries = []

    return {"count": count, "galleries": galleries}


def create_gallery_dict(
    id: str,
    title: str | None = None,
    code: str | None = None,
    urls: list[str] | None = None,
    studio: dict | None = None,
    performers: list[dict] | None = None,
    tags: list[dict] | None = None,
    scenes: list[dict] | None = None,
    images: list[dict] | None = None,
    **kwargs,
) -> dict[str, Any]:
    """Create a Gallery dict matching the Gallery type schema.

    Args:
        id: Gallery ID
        title: Gallery title
        code: Gallery code
        urls: List of URL strings
        studio: Studio dict
        performers: List of performer dicts
        tags: List of tag dicts
        scenes: List of scene dicts
        images: List of image dicts
        **kwargs: Additional gallery fields

    Returns:
        Dict matching Gallery type
    """
    base = {
        "id": id,
        "title": title,
        "code": code,
        "urls": urls or [],
        "studio": studio,
        "performers": performers or [],
        "tags": tags or [],
        "scenes": scenes or [],
        "images": images or [],
        "files": [],
        "organized": False,
    }
    base.update(kwargs)
    return base


def create_version_dict(
    version: str | None = None,
    hash: str = "abcdef1234567890",
    build_time: str = "2024-01-15T10:30:00Z",
) -> dict[str, Any]:
    """Create a Version dict matching the Version type schema.

    Args:
        version: Version string (optional, can be None)
        hash: Git commit hash (required)
        build_time: Build timestamp (required)

    Returns:
        Dict matching Version type

    Example:
        version = create_version_dict(
            version="v0.26.2",
            hash="abc123",
            build_time="2024-01-15T10:30:00Z"
        )
    """
    return {
        "version": version,
        "hash": hash,
        "build_time": build_time,
    }


def create_latestversion_dict(
    version: str = "v0.27.0",
    shorthash: str = "abc123",
    release_date: str = "2024-02-01",
    url: str = "https://github.com/stashapp/stash/releases/tag/v0.27.0",
) -> dict[str, Any]:
    """Create a LatestVersion dict matching the LatestVersion type schema.

    Args:
        version: Latest version string (required)
        shorthash: Short git commit hash (required)
        release_date: Release date (required)
        url: Download URL (required)

    Returns:
        Dict matching LatestVersion type

    Example:
        latest = create_latestversion_dict(
            version="v0.27.0",
            shorthash="abc123",
            release_date="2024-02-01",
            url="https://github.com/stashapp/stash/releases"
        )
    """
    return {
        "version": version,
        "shorthash": shorthash,
        "release_date": release_date,
        "url": url,
    }


def create_find_markers_result(
    count: int = 0, scene_markers: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    """Create a findSceneMarkers query result matching FindSceneMarkersResultType.

    Args:
        count: Total number of scene markers
        scene_markers: List of scene marker dicts

    Returns:
        Dict matching FindSceneMarkersResultType schema
    """
    if scene_markers is None:
        scene_markers = []

    return {"count": count, "scene_markers": scene_markers}


def create_marker_dict(
    id: str,
    title: str,
    seconds: float = 0.0,
    scene: dict | None = None,
    primary_tag: dict | None = None,
    tags: list[dict] | None = None,
    stream: str = "/stream/marker",
    preview: str = "/preview/marker.jpg",
    screenshot: str = "/screenshot/marker.jpg",
    **kwargs,
) -> dict[str, Any]:
    """Create a SceneMarker dict matching the SceneMarker type schema.

    Args:
        id: Marker ID
        title: Marker title
        seconds: Time in seconds where the marker occurs
        scene: Scene dict (required - SceneMarker.scene is not optional)
        primary_tag: Primary tag dict (required - SceneMarker.primary_tag is not optional)
        tags: List of tag dicts
        stream: Path to stream marker (required)
        preview: Path to preview image (required)
        screenshot: Path to screenshot image (required)
        **kwargs: Additional marker fields

    Returns:
        Dict matching SceneMarker type

    Example:
        marker = create_marker_dict(
            id="123",
            title="Chapter 1",
            seconds=30.5,
            scene={"id": "scene_1", "title": "Test Scene"},
            primary_tag={"id": "tag_1", "name": "Intro"},
        )
    """
    # Provide defaults for required nested objects if not provided
    if scene is None:
        scene = {
            "id": f"scene_for_{id}",
            "title": "Default Scene",
            "performers": [],
            "tags": [],
            "files": [],
            "urls": [],
            "stash_ids": [],
            "groups": [],
            "galleries": [],
            "scene_markers": [],
            "sceneStreams": [],
            "captions": [],
            "organized": False,
        }
    if primary_tag is None:
        primary_tag = {
            "id": f"tag_for_{id}",
            "name": "Default Tag",
            "aliases": [],
            "parents": [],
            "children": [],
        }

    base = {
        "id": id,
        "title": title,
        "seconds": seconds,
        "scene": scene,
        "primary_tag": primary_tag,
        "tags": tags or [],
        "screenshot": screenshot,
        "stream": stream,
        "preview": preview,
    }
    base.update(kwargs)
    return base


def create_find_files_result(
    count: int = 0,
    files: list[dict[str, Any]] | None = None,
    megapixels: float = 0.0,
    duration: float = 0.0,
    size: int = 0,
) -> dict[str, Any]:
    """Create a findFiles query result matching FindFilesResultType.

    Args:
        count: Total number of files
        files: List of file dicts
        megapixels: Total megapixels of image files
        duration: Total duration of video files in seconds
        size: Total size of all files in bytes

    Returns:
        Dict matching FindFilesResultType schema
    """
    if files is None:
        files = []

    return {
        "count": count,
        "files": files,
        "megapixels": megapixels,
        "duration": duration,
        "size": size,
    }


def create_file_dict(
    id: str,
    path: str,
    basename: str | None = None,
    size: int = 1024,
    mod_time: str = "2024-01-15T10:30:00Z",
    parent_folder: dict | None = None,
    fingerprints: list[dict] | None = None,
    **kwargs,
) -> dict[str, Any]:
    """Create a BaseFile dict matching the BaseFile type schema.

    Args:
        id: File ID
        path: Full file path
        basename: File basename (auto-derived from path if not provided)
        size: File size in bytes
        mod_time: Modification time as ISO string
        parent_folder: Parent folder dict
        fingerprints: List of fingerprint dicts
        **kwargs: Additional file fields (width, height, duration for video/image files)

    Returns:
        Dict matching BaseFile type

    Example:
        file = create_file_dict(
            id="123",
            path="/videos/scene.mp4",
            size=1024000000,
        )
    """
    if basename is None:
        basename = path.split("/")[-1] if "/" in path else path

    if parent_folder is None:
        parent_path = "/".join(path.split("/")[:-1]) or "/"
        parent_folder = {
            "id": f"folder_for_{id}",
            "path": parent_path,
            "mod_time": mod_time,  # Folder requires mod_time
        }

    base = {
        "id": id,
        "path": path,
        "basename": basename,
        "size": size,
        "mod_time": mod_time,
        "parent_folder": parent_folder,
        "fingerprints": fingerprints or [],
    }
    base.update(kwargs)
    return base


def create_folder_dict(
    id: str,
    path: str = "/default/path",
    mod_time: str = "2024-01-15T10:30:00Z",
    **kwargs,
) -> dict[str, Any]:
    """Create a Folder dict matching the Folder type schema.

    Args:
        id: Folder ID
        path: Folder path
        mod_time: Modification time
        **kwargs: Additional folder fields

    Returns:
        Dict matching Folder type
    """
    base = {
        "id": id,
        "path": path,
        "mod_time": mod_time,
    }
    base.update(kwargs)
    return base


def create_find_folders_result(
    count: int = 0,
    folders: list[dict] | None = None,
) -> dict[str, Any]:
    """Create a FindFoldersResultType dict.

    Args:
        count: Total number of folders
        folders: List of folder dicts

    Returns:
        Dict matching FindFoldersResultType schema
    """
    if folders is None:
        folders = []

    return {"count": count, "folders": folders}


# =============================================================================
# Configuration fixtures
# =============================================================================


def create_config_general_result(
    database_path: str = "/root/.stash/stash-go.sqlite",
    parallel_tasks: int = 1,
    generated_path: str = "/root/.stash/generated",
    metadata_path: str = "/root/.stash/metadata",
    cache_path: str = "/root/.stash/cache",
    blobs_path: str = "/root/.stash/blobs",
    config_file_path: str = "/root/.stash/config.yml",
    backup_directory_path: str = "/root/.stash/backups",
    ffmpeg_path: str = "/usr/bin/ffmpeg",
    ffprobe_path: str = "/usr/bin/ffprobe",
    **kwargs,
) -> dict[str, Any]:
    """Create a ConfigGeneralResult dict.

    Note: Returns camelCase keys to match GraphQL response format.
    Pydantic Field(alias=) converts these to snake_case Python attributes.

    Args:
        database_path: Path to database file
        parallel_tasks: Number of parallel tasks
        generated_path: Path to generated files
        metadata_path: Path to metadata
        cache_path: Path to cache
        blobs_path: Path to blobs storage
        config_file_path: Path to config file
        backup_directory_path: Path to backup directory
        ffmpeg_path: Path to ffmpeg binary
        ffprobe_path: Path to ffprobe binary
        **kwargs: Additional config fields

    Returns:
        Dict matching ConfigGeneralResult type with camelCase keys
    """
    base = {
        "databasePath": database_path,
        "parallelTasks": parallel_tasks,
    }
    base.update(kwargs)
    return base


def create_config_interface_result(
    language: str = "en-US",
    css_enabled: bool = False,
    javascript_enabled: bool = False,
    **kwargs,
) -> dict[str, Any]:
    """Create a ConfigInterfaceResult dict.

    Note: Returns camelCase keys to match GraphQL response format.
    Pydantic Field(alias=) converts these to snake_case Python attributes.

    Args:
        language: Interface language
        css_enabled: Whether custom CSS is enabled
        javascript_enabled: Whether custom JavaScript is enabled
        **kwargs: Additional interface config fields

    Returns:
        Dict matching ConfigInterfaceResult type with camelCase keys
    """
    base = {
        "menuItems": None,
        "soundOnPreview": True,
        "wallShowTitle": True,
        "wallPlayback": "video",
        "showScrubber": True,
        "maximumLoopDuration": 0,
        "noBrowser": False,
        "notificationsEnabled": True,
        "autostartVideo": False,
        "autostartVideoOnPlaySelected": True,
        "continuePlaylistDefault": False,
        "showStudioAsText": False,
        "css": None,
        "cssEnabled": css_enabled,
        "javascript": None,
        "javascriptEnabled": javascript_enabled,
        "customLocales": None,
        "customLocalesEnabled": False,
        "language": language,
        "imageLightbox": {
            "slideshowDelay": 5000,
            "displayMode": "FIT_XY",
            "scaleUp": False,
            "resetZoomOnNav": True,
            "scrollMode": "ZOOM",
            "scrollAttemptsBeforeChange": 3,
        },
        "disableDropdownCreate": {
            "performer": False,
            "tag": False,
            "studio": False,
            "movie": False,
        },
        "handyKey": None,
        "funscriptOffset": None,
        "useStashHostedFunscript": False,
    }
    base.update(kwargs)
    return base


def create_config_dlna_result(
    enabled: bool = False,
    server_name: str = "stash",
    port: int = 1338,
    whitelisted_ips: list[str] | None = None,
    interfaces: list[str] | None = None,
    video_sort_order: str = "title",
) -> dict[str, Any]:
    """Create a ConfigDLNAResult dict.

    Note: Returns camelCase keys to match GraphQL response format.
    Pydantic Field(alias=) converts these to snake_case Python attributes.

    Args:
        enabled: Whether DLNA is enabled
        server_name: DLNA server name
        port: DLNA port
        whitelisted_ips: List of whitelisted IPs
        interfaces: List of network interfaces
        video_sort_order: Video sort order

    Returns:
        Dict matching ConfigDLNAResult type with camelCase keys
    """
    return {
        "enabled": enabled,
        "serverName": server_name,
        "port": port,
        "whitelistedIPs": whitelisted_ips or [],
        "interfaces": interfaces or [],
        "videoSortOrder": video_sort_order,
    }


def create_config_defaults_result(
    delete_file: bool = False,
    delete_generated: bool = True,
) -> dict[str, Any]:
    """Create a ConfigDefaultSettingsResult dict.

    Args:
        delete_file: Default delete file checkbox value
        delete_generated: Default delete generated checkbox value

    Returns:
        Dict matching ConfigDefaultSettingsResult type
    """
    return {
        "scan": {
            "rescan": False,
            "scanGenerateCovers": False,
            "scanGeneratePreviews": False,
            "scanGenerateImagePreviews": False,
            "scanGenerateSprites": False,
            "scanGeneratePhashes": False,
            "scanGenerateThumbnails": False,
            "scanGenerateClipPreviews": False,
        },
        "autoTag": {
            "performers": None,
            "studios": None,
            "tags": None,
        },
        "generate": {
            "covers": False,
            "sprites": False,
            "previews": False,
            "imagePreviews": False,
            "previewOptions": None,
            "markers": False,
            "markerImagePreviews": False,
            "markerScreenshots": False,
            "transcodes": False,
            "phashes": False,
            "interactiveHeatmapsSpeeds": False,
            "imageThumbnails": False,
            "clipPreviews": False,
        },
        "deleteFile": delete_file,
        "deleteGenerated": delete_generated,
    }


# =============================================================================
# Group fixtures (Step 11)
# =============================================================================


def create_group_dict(
    id: str,
    name: str,
    urls: list[str] | None = None,
    aliases: str | None = None,
    duration: int | None = None,
    date: str | None = None,
    rating100: int | None = None,
    studio: dict | None = None,
    director: str | None = None,
    synopsis: str | None = None,
    front_image_path: str | None = None,
    back_image_path: str | None = None,
    tags: list[dict] | None = None,
    scenes: list[dict] | None = None,
    containing_groups: list[dict] | None = None,
    sub_groups: list[dict] | None = None,
    **kwargs,
) -> dict[str, Any]:
    """Create a Group dict for GraphQL responses.

    Args:
        id: Group ID
        name: Group name (required)
        urls: List of URLs associated with the group
        aliases: Comma-separated aliases
        duration: Duration in seconds
        date: Date string (YYYY-MM-DD)
        rating100: Rating (1-100)
        studio: Studio dict with at least id field
        director: Director name
        synopsis: Synopsis/description
        front_image_path: Path to front cover image
        back_image_path: Path to back cover image
        tags: List of tag dicts
        scenes: List of scene dicts
        containing_groups: List of group description dicts (parent groups)
        sub_groups: List of group description dicts (child groups)
        **kwargs: Additional fields to include

    Returns:
        Dict matching Group GraphQL type
    """
    base = {
        "id": id,
        "name": name,
        "urls": urls or [],
        "aliases": aliases,
        "duration": duration,
        "date": date,
        "rating100": rating100,
        "studio": studio,
        "director": director,
        "synopsis": synopsis,
        "front_image_path": front_image_path,
        "back_image_path": back_image_path,
        "tags": tags or [],
        "scenes": scenes or [],
        "containing_groups": containing_groups or [],
        "sub_groups": sub_groups or [],
    }
    base.update(kwargs)
    return base


def create_find_groups_result(
    count: int = 0, groups: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    """Create a findGroups query result matching FindGroupsResultType.

    Args:
        count: Total number of groups
        groups: List of group dicts

    Returns:
        Dict matching FindGroupsResultType schema
    """
    if groups is None:
        groups = []

    return {"count": count, "groups": groups}


def create_group_description_dict(
    group: dict[str, Any],
    description: str | None = None,
) -> dict[str, Any]:
    """Create a GroupDescription dict for sub_groups and containing_groups.

    Args:
        group: Group dict with at least id field
        description: Optional description for this group relationship

    Returns:
        Dict matching GroupDescription GraphQL type
    """
    return {
        "group": group,
        "description": description,
    }


__all__ = [
    # Config fixtures
    "create_config_defaults_result",
    "create_config_dlna_result",
    "create_config_general_result",
    "create_config_interface_result",
    # Entity fixtures
    "create_file_dict",
    "create_find_files_result",
    "create_find_folders_result",
    "create_find_galleries_result",
    "create_find_groups_result",
    "create_find_images_result",
    "create_find_markers_result",
    "create_find_performers_result",
    "create_find_scenes_result",
    "create_find_studios_result",
    "create_find_tags_result",
    "create_folder_dict",
    "create_gallery_dict",
    "create_graphql_response",
    "create_group_description_dict",
    "create_group_dict",
    "create_image_dict",
    "create_latestversion_dict",
    "create_marker_dict",
    "create_performer_dict",
    "create_scene_dict",
    "create_studio_dict",
    "create_tag_create_result",
    "create_tag_dict",
    "create_version_dict",
]
