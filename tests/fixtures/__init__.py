"""Fixture loading utilities for pytest tests.

This module provides utilities for loading and managing test fixtures
for stash-graphql-client. All fixtures are organized in a nested folder
structure for better maintainability.

Fixture Organization:
- stash/type_factories.py - FactoryBoy factories for Stash API types
- stash/graphql_responses.py - GraphQL response generators for respx
- stash/test_objects.py - Test object implementations for base class testing
- client.py - StashClient pytest fixtures for testing
"""

from tests.fixtures.client import (
    mock_gql_ws_connect,
    mock_ws_transport,
    respx_entity_store,
    respx_stash_client,
    stash_cleanup_tracker,
    stash_client,
    stash_context,
    stash_context_with_api_key,
)
from tests.fixtures.stash import (
    # Type factories
    GalleryFactory,
    GroupFactory,
    ImageFactory,
    ImageFileFactory,
    JobFactory,
    PerformerFactory,
    SceneFactory,
    StudioFactory,
    TagFactory,
    VideoFileFactory,
    # Config response generators
    create_config_defaults_result,
    create_config_dlna_result,
    create_config_general_result,
    create_config_interface_result,
    # GraphQL response generators
    create_file_dict,
    create_find_files_result,
    create_find_folders_result,
    create_find_galleries_result,
    create_find_groups_result,
    create_find_images_result,
    create_find_markers_result,
    create_find_performers_result,
    create_find_scenes_result,
    create_find_studios_result,
    create_find_tags_result,
    create_folder_dict,
    create_gallery_dict,
    create_graphql_response,
    create_group_description_dict,
    create_group_dict,
    create_image_dict,
    create_latestversion_dict,
    create_marker_dict,
    create_performer_dict,
    create_scene_dict,
    create_studio_dict,
    create_tag_create_result,
    create_tag_dict,
    create_version_dict,
    enable_scene_creation,
    # Pytest fixtures (real objects, not mocks)
    mock_gallery,
    mock_image,
    mock_image_file,
    mock_performer,
    mock_scene,
    mock_studio,
    mock_tag,
    mock_video_file,
)


__all__ = [
    # Client Fixtures
    "enable_scene_creation",
    "mock_gql_ws_connect",
    "mock_ws_transport",
    "respx_entity_store",
    "respx_stash_client",
    "stash_cleanup_tracker",
    "stash_client",
    "stash_context",
    "stash_context_with_api_key",
    # Type Factories
    "GalleryFactory",
    "GroupFactory",
    "ImageFactory",
    "ImageFileFactory",
    "JobFactory",
    "PerformerFactory",
    "SceneFactory",
    "StudioFactory",
    "TagFactory",
    "VideoFileFactory",
    # Config Response Generators
    "create_config_defaults_result",
    "create_config_dlna_result",
    "create_config_general_result",
    "create_config_interface_result",
    # GraphQL Response Generators
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
    # Pytest Fixtures (real objects)
    "mock_gallery",
    "mock_image",
    "mock_image_file",
    "mock_performer",
    "mock_scene",
    "mock_studio",
    "mock_tag",
    "mock_video_file",
]
