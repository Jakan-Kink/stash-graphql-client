"""Tests for stash_graphql_client.types.gallery module.

Tests gallery types including GalleryPathsType.create_default().
"""

import pytest

from stash_graphql_client.types.gallery import GalleryPathsType


@pytest.mark.unit
def test_gallery_paths_type_create_default() -> None:
    """Test GalleryPathsType.create_default() creates instance with empty strings.

    This covers line 33 in gallery.py - the return statement.
    """
    paths = GalleryPathsType.create_default()

    assert isinstance(paths, GalleryPathsType)
    assert paths.cover == ""
    assert paths.preview == ""
