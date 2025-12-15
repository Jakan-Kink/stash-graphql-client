"""Integration test to verify isinstance() type guards work with __typename discrimination.

This test verifies that the pattern shown in the file.py docstring actually works.
"""

import pytest

from stash_graphql_client.types import (
    BaseFile,
    FindFilesResultType,
    ImageFile,
    VideoFile,
)


def test_isinstance_type_guard_with_video_file():
    """Test that isinstance() type guard works after discrimination."""
    data = {
        "count": 1,
        "megapixels": 0.0,
        "duration": 120.5,
        "size": 1000000,
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
            }
        ],
    }

    result = FindFilesResultType.model_validate(data)
    file = result.files[0]

    # This is the pattern from the docstring - it should work!
    if isinstance(file, VideoFile):
        # Type checker knows this is VideoFile now
        assert file.duration == 120.5  # ✅ VideoFile has duration
        assert file.video_codec == "h264"  # ✅ VideoFile has video_codec
    else:
        pytest.fail("File should be VideoFile")


def test_isinstance_type_guard_with_image_file():
    """Test that isinstance() type guard works for ImageFile."""
    data = {
        "count": 1,
        "megapixels": 2.0,
        "duration": 0.0,
        "size": 500000,
        "files": [
            {
                "__typename": "ImageFile",
                "id": "2",
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
            }
        ],
    }

    result = FindFilesResultType.model_validate(data)
    file = result.files[0]

    # This is the pattern from the docstring
    if isinstance(file, ImageFile):
        assert file.width == 1920  # ✅ ImageFile has width
        assert file.height == 1080  # ✅ ImageFile has height
        assert file.format == "jpg"  # ✅ ImageFile has format
    else:
        pytest.fail("File should be ImageFile")


def test_type_narrowing_with_polymorphic_handling():
    """Test type narrowing pattern for handling different file types."""
    data = {
        "count": 2,
        "megapixels": 2.0,
        "duration": 120.5,
        "size": 1500000,
        "files": [
            {
                "__typename": "VideoFile",
                "id": "1",
                "path": "/video.mp4",
                "basename": "video.mp4",
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
        ],
    }

    result = FindFilesResultType.model_validate(data)

    # Pattern: iterate and handle each type appropriately
    for file in result.files:
        assert isinstance(file, BaseFile)  # All files are BaseFile

        if isinstance(file, VideoFile):
            # Handle video-specific logic
            assert hasattr(file, "duration")
            assert file.duration > 0
        elif isinstance(file, ImageFile):
            # Handle image-specific logic
            assert hasattr(file, "width")
            assert file.width > 0


def test_isinstance_returns_false_for_wrong_type():
    """Test that isinstance correctly returns False for mismatched types."""
    data = {
        "count": 1,
        "megapixels": 0.0,
        "duration": 120.5,
        "size": 1000000,
        "files": [
            {
                "__typename": "VideoFile",
                "id": "1",
                "path": "/video.mp4",
                "basename": "video.mp4",
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

    result = FindFilesResultType.model_validate(data)
    file = result.files[0]

    # VideoFile should NOT be ImageFile
    assert isinstance(file, VideoFile)
    assert not isinstance(file, ImageFile)
