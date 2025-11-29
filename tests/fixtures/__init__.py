"""Fixture loading utilities for pytest tests.

This module provides utilities for loading and managing test fixtures
for stash-graphql-client. All fixtures are organized in a nested folder
structure for better maintainability.

Fixture Organization:
- stash/type_factories.py - FactoryBoy factories for Stash API types
- stash/graphql_responses.py - GraphQL response generators for respx
- stash/test_objects.py - Test object implementations for base class testing
"""

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
    # GraphQL response generators
    create_find_galleries_result,
    create_find_images_result,
    create_find_performers_result,
    create_find_scenes_result,
    create_find_studios_result,
    create_find_tags_result,
    create_gallery_dict,
    create_graphql_response,
    create_image_dict,
    create_performer_dict,
    create_scene_dict,
    create_studio_dict,
    create_tag_create_result,
    create_tag_dict,
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
    # GraphQL Response Generators
    "create_find_galleries_result",
    "create_find_images_result",
    "create_find_performers_result",
    "create_find_scenes_result",
    "create_find_studios_result",
    "create_find_tags_result",
    "create_gallery_dict",
    "create_graphql_response",
    "create_image_dict",
    "create_performer_dict",
    "create_scene_dict",
    "create_studio_dict",
    "create_tag_create_result",
    "create_tag_dict",
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
