"""Tests for GalleryChapter relationship migration to RelationshipMetadata.

These tests verify that GalleryChapter has migrated from tuple-based relationship
mappings to RelationshipMetadata objects while maintaining backward compatibility.
"""

from stash_graphql_client.types.gallery import GalleryChapter, RelationshipMetadata


class TestGalleryChapterRelationshipMetadata:
    """Test GalleryChapter.__relationships__ uses RelationshipMetadata."""

    def test_gallery_chapter_has_relationships_dict(self):
        """Test that GalleryChapter has __relationships__ class variable."""
        assert hasattr(GalleryChapter, "__relationships__")
        assert isinstance(GalleryChapter.__relationships__, dict)

    def test_all_relationships_use_metadata(self):
        """Test that all GalleryChapter relationships use RelationshipMetadata, not tuples."""
        for rel_name, rel_meta in GalleryChapter.__relationships__.items():
            assert isinstance(rel_meta, RelationshipMetadata), (
                f"GalleryChapter.{rel_name} should be RelationshipMetadata, not {type(rel_meta)}"
            )

    def test_gallery_chapter_has_one_relationship(self):
        """Test that GalleryChapter has exactly 1 relationship."""
        expected_relationships = {"gallery"}
        actual_relationships = set(GalleryChapter.__relationships__.keys())

        assert actual_relationships == expected_relationships, (
            f"GalleryChapter relationships mismatch. "
            f"Expected: {expected_relationships}, Got: {actual_relationships}"
        )


class TestGalleryChapterGalleryRelationship:
    """Test GalleryChapter.gallery relationship metadata."""

    def test_gallery_relationship_exists(self):
        """Test that gallery relationship is defined."""
        assert "gallery" in GalleryChapter.__relationships__

    def test_gallery_target_field(self):
        """Test gallery relationship targets gallery_id."""
        rel = GalleryChapter.__relationships__["gallery"]
        assert rel.target_field == "gallery_id"

    def test_gallery_is_not_list(self):
        """Test gallery is a single object (many-to-one)."""
        rel = GalleryChapter.__relationships__["gallery"]
        assert rel.is_list is False

    def test_gallery_query_strategy(self):
        """Test gallery uses direct_field strategy."""
        rel = GalleryChapter.__relationships__["gallery"]
        assert rel.query_strategy == "direct_field"

    def test_gallery_query_field(self):
        """Test gallery query field is 'gallery'."""
        rel = GalleryChapter.__relationships__["gallery"]
        assert rel.query_field == "gallery"

    def test_gallery_inverse_metadata(self):
        """Test gallery has inverse relationship metadata."""
        rel = GalleryChapter.__relationships__["gallery"]
        assert rel.inverse_type == "Gallery"
        assert rel.inverse_query_field == "chapters"

    def test_gallery_auto_sync(self):
        """Test gallery relationship has auto_sync enabled."""
        rel = GalleryChapter.__relationships__["gallery"]
        assert rel.auto_sync is True

    def test_gallery_backward_compatibility(self):
        """Test gallery RelationshipMetadata can convert to legacy tuple."""
        rel = GalleryChapter.__relationships__["gallery"]
        legacy_tuple = rel.to_tuple()

        assert legacy_tuple == ("gallery_id", False, None)


class TestGalleryChapterRelationshipMetadataIntegration:
    """Integration tests for GalleryChapter relationship metadata."""

    def test_all_relationships_have_required_fields(self):
        """Test that all relationships have required metadata fields."""
        for rel_name, rel_meta in GalleryChapter.__relationships__.items():
            # Required fields
            assert hasattr(rel_meta, "target_field"), f"{rel_name} missing target_field"
            assert hasattr(rel_meta, "is_list"), f"{rel_name} missing is_list"
            assert hasattr(rel_meta, "query_field"), f"{rel_name} missing query_field"
            assert hasattr(rel_meta, "query_strategy"), (
                f"{rel_name} missing query_strategy"
            )

            # Optional but expected fields
            assert hasattr(rel_meta, "inverse_type"), f"{rel_name} missing inverse_type"
            assert hasattr(rel_meta, "auto_sync"), f"{rel_name} missing auto_sync"

    def test_relationship_repr(self):
        """Test RelationshipMetadata __repr__ for debugging."""
        rel = GalleryChapter.__relationships__["gallery"]
        repr_str = repr(rel)

        assert "RelationshipMetadata" in repr_str
        assert "gallery_id" in repr_str
        assert "direct_field" in repr_str

    def test_query_field_auto_derivation(self):
        """Test that query_field is auto-derived from target_field."""
        # gallery_id → gallery
        assert GalleryChapter.__relationships__["gallery"].query_field == "gallery"

    def test_no_transform_function(self):
        """Test that GalleryChapter.gallery uses default ID extraction (no custom transform)."""
        rel = GalleryChapter.__relationships__["gallery"]
        assert rel.transform is None, "gallery should not have custom transform"

    def test_bidirectional_sync_with_gallery(self):
        """Test that GalleryChapter → Gallery relationship is bidirectional."""
        rel = GalleryChapter.__relationships__["gallery"]

        # Verify forward relationship
        assert rel.target_field == "gallery_id"
        assert rel.query_field == "gallery"

        # Verify inverse relationship metadata
        assert rel.inverse_type == "Gallery"
        assert rel.inverse_query_field == "chapters"

        # Verify auto-sync is enabled
        assert rel.auto_sync is True
