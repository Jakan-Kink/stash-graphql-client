"""Unit tests for BaseFile interface and VisualFile union type discrimination.

These tests verify that __typename-based discrimination works correctly for:
- BaseFile interface (BasicFile, VideoFile, ImageFile, GalleryFile)
- VisualFile union (VideoFile, ImageFile)
"""

import pytest

from stash_graphql_client.types import (
    BaseFile,
    BasicFile,
    FindFilesResultType,
    GalleryFile,
    Image,
    ImageFile,
    VideoFile,
)


# =============================================================================
# FindFilesResultType tests (BaseFile interface discrimination)
# =============================================================================


def test_find_files_result_discriminates_video_file():
    """Test that VideoFile is correctly discriminated from BaseFile."""
    data = {
        "count": 1,
        "megapixels": 0.0,
        "duration": 120.5,
        "size": 1000000,
        "files": [
            {
                "__typename": "VideoFile",
                "id": "1",
                "path": "/videos/test.mp4",
                "basename": "test.mp4",
                "parent_folder": {"id": "folder1", "path": "/videos"},
                "zip_file": None,
                "size": 1000000,
                "mod_time": "2024-01-01T12:00:00Z",
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z",
                "fingerprints": [],
                # VideoFile-specific fields
                "format": "mp4",
                "width": 1920,
                "height": 1080,
                "duration": 120.5,
                "video_codec": "h264",
                "audio_codec": "aac",
                "frame_rate": 30.0,
                "bit_rate": 5000000,
            }
        ],
    }

    result = FindFilesResultType.model_validate(data)

    assert len(result.files) == 1
    assert isinstance(result.files[0], VideoFile)
    assert result.files[0].format == "mp4"
    assert result.files[0].duration == 120.5
    assert result.files[0].video_codec == "h264"


def test_find_files_result_discriminates_image_file():
    """Test that ImageFile is correctly discriminated from BaseFile."""
    data = {
        "count": 1,
        "megapixels": 2.0,
        "duration": 0.0,
        "size": 500000,
        "files": [
            {
                "__typename": "ImageFile",
                "id": "2",
                "path": "/images/photo.jpg",
                "basename": "photo.jpg",
                "parent_folder": {"id": "folder2", "path": "/images"},
                "zip_file": None,
                "size": 500000,
                "mod_time": "2024-01-01T12:00:00Z",
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z",
                "fingerprints": [],
                # ImageFile-specific fields
                "format": "jpg",
                "width": 1920,
                "height": 1080,
            }
        ],
    }

    result = FindFilesResultType.model_validate(data)

    assert len(result.files) == 1
    assert isinstance(result.files[0], ImageFile)
    assert result.files[0].format == "jpg"
    assert result.files[0].width == 1920
    assert result.files[0].height == 1080


def test_find_files_result_discriminates_gallery_file():
    """Test that GalleryFile is correctly discriminated from BaseFile."""
    data = {
        "count": 1,
        "megapixels": 0.0,
        "duration": 0.0,
        "size": 50000,
        "files": [
            {
                "__typename": "GalleryFile",
                "id": "3",
                "path": "/galleries/archive.zip",
                "basename": "archive.zip",
                "parent_folder": {"id": "folder3", "path": "/galleries"},
                "zip_file": None,
                "size": 50000,
                "mod_time": "2024-01-01T12:00:00Z",
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z",
                "fingerprints": [],
            }
        ],
    }

    result = FindFilesResultType.model_validate(data)

    assert len(result.files) == 1
    assert isinstance(result.files[0], GalleryFile)
    assert result.files[0].basename == "archive.zip"


def test_find_files_result_discriminates_basic_file():
    """Test that BasicFile is correctly discriminated from BaseFile."""
    data = {
        "count": 1,
        "megapixels": 0.0,
        "duration": 0.0,
        "size": 1024,
        "files": [
            {
                "__typename": "BasicFile",
                "id": "4",
                "path": "/docs/readme.txt",
                "basename": "readme.txt",
                "parent_folder": {"id": "folder4", "path": "/docs"},
                "zip_file": None,
                "size": 1024,
                "mod_time": "2024-01-01T12:00:00Z",
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z",
                "fingerprints": [],
            }
        ],
    }

    result = FindFilesResultType.model_validate(data)

    assert len(result.files) == 1
    assert isinstance(result.files[0], BasicFile)
    assert result.files[0].basename == "readme.txt"


def test_find_files_result_handles_multiple_file_types():
    """Test that mixed file types are correctly discriminated."""
    data = {
        "count": 3,
        "megapixels": 2.0,
        "duration": 120.5,
        "size": 1551024,
        "files": [
            {
                "__typename": "VideoFile",
                "id": "1",
                "path": "/test.mp4",
                "basename": "test.mp4",
                "parent_folder": {"id": "f1", "path": "/"},
                "zip_file": None,
                "size": 1000000,
                "mod_time": "2024-01-01T12:00:00Z",
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z",
                "fingerprints": [],
                "format": "mp4",
                "width": 1920,
                "height": 1080,
                "duration": 120.5,
                "video_codec": "h264",
                "audio_codec": "aac",
                "frame_rate": 30.0,
                "bit_rate": 5000000,
            },
            {
                "__typename": "ImageFile",
                "id": "2",
                "path": "/photo.jpg",
                "basename": "photo.jpg",
                "parent_folder": {"id": "f2", "path": "/"},
                "zip_file": None,
                "size": 500000,
                "mod_time": "2024-01-01T12:00:00Z",
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z",
                "fingerprints": [],
                "format": "jpg",
                "width": 1920,
                "height": 1080,
            },
            {
                "__typename": "GalleryFile",
                "id": "3",
                "path": "/archive.zip",
                "basename": "archive.zip",
                "parent_folder": {"id": "f3", "path": "/"},
                "zip_file": None,
                "size": 50000,
                "mod_time": "2024-01-01T12:00:00Z",
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z",
                "fingerprints": [],
            },
            {
                "__typename": "BasicFile",
                "id": "4",
                "path": "/readme.txt",
                "basename": "readme.txt",
                "parent_folder": {"id": "f4", "path": "/"},
                "zip_file": None,
                "size": 1024,
                "mod_time": "2024-01-01T12:00:00Z",
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z",
                "fingerprints": [],
            },
        ],
    }

    result = FindFilesResultType.model_validate(data)

    assert len(result.files) == 4
    assert isinstance(result.files[0], VideoFile)
    assert isinstance(result.files[1], ImageFile)
    assert isinstance(result.files[2], GalleryFile)
    assert isinstance(result.files[3], BasicFile)


# =============================================================================
# Image.visual_files tests (VisualFile union discrimination)
# =============================================================================


def test_image_visual_files_discriminates_image_file():
    """Test that visual_files correctly discriminates ImageFile."""
    data = {
        "id": "img1",
        "created_at": "2024-01-01T12:00:00Z",
        "updated_at": "2024-01-01T12:00:00Z",
        "urls": [],
        "organized": False,
        "visual_files": [
            {
                "__typename": "ImageFile",
                "id": "file1",
                "path": "/images/photo.jpg",
                "basename": "photo.jpg",
                "parent_folder": {"id": "folder1", "path": "/images"},
                "zip_file": None,
                "size": 500000,
                "mod_time": "2024-01-01T12:00:00Z",
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z",
                "fingerprints": [],
                "format": "jpg",
                "width": 1920,
                "height": 1080,
            }
        ],
        "paths": {"thumbnail": None, "preview": None, "image": None},
        "galleries": [],
        "tags": [],
        "performers": [],
    }

    image = Image.model_validate(data)

    assert len(image.visual_files) == 1
    assert isinstance(image.visual_files[0], ImageFile)
    assert image.visual_files[0].format == "jpg"


def test_image_visual_files_discriminates_video_file():
    """Test that visual_files correctly discriminates VideoFile (for animated GIFs)."""
    data = {
        "id": "img2",
        "created_at": "2024-01-01T12:00:00Z",
        "updated_at": "2024-01-01T12:00:00Z",
        "urls": [],
        "organized": False,
        "visual_files": [
            {
                "__typename": "VideoFile",
                "id": "file2",
                "path": "/images/animated.gif",
                "basename": "animated.gif",
                "parent_folder": {"id": "folder2", "path": "/images"},
                "zip_file": None,
                "size": 1000000,
                "mod_time": "2024-01-01T12:00:00Z",
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z",
                "fingerprints": [],
                "format": "gif",
                "width": 800,
                "height": 600,
                "duration": 5.0,
                "video_codec": "gif",
                "audio_codec": "",
                "frame_rate": 24.0,
                "bit_rate": 1000000,
            }
        ],
        "paths": {"thumbnail": None, "preview": None, "image": None},
        "galleries": [],
        "tags": [],
        "performers": [],
    }

    image = Image.model_validate(data)

    assert len(image.visual_files) == 1
    assert isinstance(image.visual_files[0], VideoFile)
    assert image.visual_files[0].format == "gif"
    assert image.visual_files[0].duration == 5.0


def test_image_visual_files_handles_mixed_types():
    """Test that visual_files handles both ImageFile and VideoFile."""
    data = {
        "id": "img3",
        "created_at": "2024-01-01T12:00:00Z",
        "updated_at": "2024-01-01T12:00:00Z",
        "urls": [],
        "organized": False,
        "visual_files": [
            {
                "__typename": "ImageFile",
                "id": "file1",
                "path": "/photo.jpg",
                "basename": "photo.jpg",
                "parent_folder": {"id": "f1", "path": "/"},
                "zip_file": None,
                "size": 500000,
                "mod_time": "2024-01-01T12:00:00Z",
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z",
                "fingerprints": [],
                "format": "jpg",
                "width": 1920,
                "height": 1080,
            },
            {
                "__typename": "VideoFile",
                "id": "file2",
                "path": "/animated.gif",
                "basename": "animated.gif",
                "parent_folder": {"id": "f2", "path": "/"},
                "zip_file": None,
                "size": 1000000,
                "mod_time": "2024-01-01T12:00:00Z",
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z",
                "fingerprints": [],
                "format": "gif",
                "width": 800,
                "height": 600,
                "duration": 5.0,
                "video_codec": "gif",
                "audio_codec": "",
                "frame_rate": 24.0,
                "bit_rate": 1000000,
            },
        ],
        "paths": {"thumbnail": None, "preview": None, "image": None},
        "galleries": [],
        "tags": [],
        "performers": [],
    }

    image = Image.model_validate(data)

    assert len(image.visual_files) == 2
    assert isinstance(image.visual_files[0], ImageFile)
    assert isinstance(image.visual_files[1], VideoFile)


def test_image_visual_files_handles_empty_list():
    """Test that visual_files handles empty list correctly."""
    data = {
        "id": "img4",
        "created_at": "2024-01-01T12:00:00Z",
        "updated_at": "2024-01-01T12:00:00Z",
        "urls": [],
        "organized": False,
        "visual_files": [],
        "paths": {"thumbnail": None, "preview": None, "image": None},
        "galleries": [],
        "tags": [],
        "performers": [],
    }

    image = Image.model_validate(data)

    assert len(image.visual_files) == 0


@pytest.mark.unit
def test_typename_in_file_fields_enables_discrimination():
    """Test that __typename field is essential for discrimination."""
    # Without __typename, discrimination cannot occur
    data_without_typename = {
        "count": 1,
        "megapixels": 0.0,
        "duration": 0.0,
        "size": 1000000,
        "files": [
            {
                # Missing __typename!
                "id": "1",
                "path": "/test.mp4",
                "basename": "test.mp4",
                "parent_folder": {"id": "f1", "path": "/"},
                "zip_file": None,
                "size": 1000000,
                "mod_time": "2024-01-01T12:00:00Z",
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z",
                "fingerprints": [],
                "format": "mp4",
                "width": 1920,
                "height": 1080,
                "duration": 120.5,
                "video_codec": "h264",
                "audio_codec": "aac",
                "frame_rate": 30.0,
                "bit_rate": 5000000,
            }
        ],
    }

    result = FindFilesResultType.model_validate(data_without_typename)

    # Without __typename, the validator cannot discriminate to the correct subclass,
    # so Pydantic validates it as BaseFile (the base type) instead of VideoFile
    assert len(result.files) == 1
    assert isinstance(result.files[0], BaseFile)
    # The file is NOT a VideoFile because discrimination didn't occur
    assert not isinstance(result.files[0], VideoFile)
    # But it still has the extra fields from the dict
    assert result.files[0].path == "/test.mp4"
