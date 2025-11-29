"""Stash fixtures for testing stash-graphql-client.

This module provides:
- FactoryBoy factories for all Stash API types (Performer, Studio, Scene, etc.)
- GraphQL response generators for use with respx HTTP mocking
- Pytest fixtures that return real objects (NOT MagicMock)
"""

from tests.fixtures.stash.graphql_responses import (
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
)
from tests.fixtures.stash.type_factories import (
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
