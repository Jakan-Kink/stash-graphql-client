"""Tests for stash_graphql_client.types.gallery module."""

import pytest

from stash_graphql_client.types.gallery import GalleryPathsType


class TestGalleryPathsType:
    """Tests for GalleryPathsType class."""

    @pytest.mark.unit
    def test_create_default_returns_instance(self) -> None:
        """Test that create_default() returns a GalleryPathsType instance."""
        result = GalleryPathsType.create_default()
        assert isinstance(result, GalleryPathsType)

    @pytest.mark.unit
    def test_create_default_has_empty_strings(self) -> None:
        """Test that create_default() creates instance with empty string defaults."""
        result = GalleryPathsType.create_default()
        assert result.cover == ""
        assert result.preview == ""

    @pytest.mark.unit
    def test_create_default_is_valid_instance(self) -> None:
        """Test that create_default() returns a valid pydantic model instance."""
        result = GalleryPathsType.create_default()
        # Verify it can be serialized (validates the model)
        dumped = result.model_dump()
        assert dumped == {"cover": "", "preview": ""}
