"""Tests for Gallery relationship migration to RelationshipMetadata.

These tests verify that Gallery has migrated from tuple-based relationship
mappings to RelationshipMetadata objects while maintaining backward compatibility.
"""

from stash_graphql_client.types import Gallery, RelationshipMetadata


class TestGalleryRelationshipMetadata:
    """Test Gallery.__relationships__ uses RelationshipMetadata."""

    def test_gallery_has_relationships_dict(self):
        """Test that Gallery has __relationships__ class variable."""
        assert hasattr(Gallery, "__relationships__")
        assert isinstance(Gallery.__relationships__, dict)

    def test_all_relationships_use_metadata(self):
        """Test that all Gallery relationships use RelationshipMetadata, not tuples."""
        for rel_name, rel_meta in Gallery.__relationships__.items():
            assert isinstance(rel_meta, RelationshipMetadata), (
                f"Gallery.{rel_name} should be RelationshipMetadata, not {type(rel_meta)}"
            )

    def test_gallery_has_four_relationships(self):
        """Test that Gallery has exactly 4 relationships."""
        expected_relationships = {"studio", "performers", "tags", "scenes"}
        actual_relationships = set(Gallery.__relationships__.keys())

        assert actual_relationships == expected_relationships, (
            f"Gallery relationships mismatch. "
            f"Expected: {expected_relationships}, Got: {actual_relationships}"
        )


class TestGalleryStudioRelationship:
    """Test Gallery.studio relationship metadata."""

    def test_studio_relationship_exists(self):
        """Test that studio relationship is defined."""
        assert "studio" in Gallery.__relationships__

    def test_studio_target_field(self):
        """Test studio relationship targets studio_id."""
        rel = Gallery.__relationships__["studio"]
        assert rel.target_field == "studio_id"

    def test_studio_is_not_list(self):
        """Test studio is a single object (many-to-one)."""
        rel = Gallery.__relationships__["studio"]
        assert rel.is_list is False

    def test_studio_query_strategy(self):
        """Test studio uses filter_query strategy."""
        rel = Gallery.__relationships__["studio"]
        assert rel.query_strategy == "filter_query"

    def test_studio_query_field(self):
        """Test studio query field is 'studio'."""
        rel = Gallery.__relationships__["studio"]
        assert rel.query_field == "studio"

    def test_studio_inverse_metadata(self):
        """Test studio has inverse relationship metadata."""
        rel = Gallery.__relationships__["studio"]
        assert rel.inverse_type == "Studio"
        # Studio doesn't have a direct 'galleries' field, uses filter query
        assert rel.query_strategy == "filter_query"

    def test_studio_auto_sync(self):
        """Test studio relationship has auto_sync enabled."""
        rel = Gallery.__relationships__["studio"]
        assert rel.auto_sync is True


class TestGalleryPerformersRelationship:
    """Test Gallery.performers relationship metadata."""

    def test_performers_relationship_exists(self):
        """Test that performers relationship is defined."""
        assert "performers" in Gallery.__relationships__

    def test_performers_target_field(self):
        """Test performers relationship targets performer_ids."""
        rel = Gallery.__relationships__["performers"]
        assert rel.target_field == "performer_ids"

    def test_performers_is_list(self):
        """Test performers is a list (many-to-many)."""
        rel = Gallery.__relationships__["performers"]
        assert rel.is_list is True

    def test_performers_query_strategy(self):
        """Test performers uses direct_field strategy."""
        rel = Gallery.__relationships__["performers"]
        assert rel.query_strategy == "direct_field"

    def test_performers_query_field(self):
        """Test performers query field is 'performers'."""
        rel = Gallery.__relationships__["performers"]
        assert rel.query_field == "performers"

    def test_performers_inverse_metadata(self):
        """Test performers has inverse relationship metadata."""
        rel = Gallery.__relationships__["performers"]
        assert rel.inverse_type == "Performer"
        assert (
            rel.inverse_query_field is None
        )  # Performer has gallery_count, not galleries list

    def test_performers_auto_sync(self):
        """Test performers relationship has auto_sync enabled."""
        rel = Gallery.__relationships__["performers"]
        assert rel.auto_sync is True


class TestGalleryTagsRelationship:
    """Test Gallery.tags relationship metadata."""

    def test_tags_relationship_exists(self):
        """Test that tags relationship is defined."""
        assert "tags" in Gallery.__relationships__

    def test_tags_target_field(self):
        """Test tags relationship targets tag_ids."""
        rel = Gallery.__relationships__["tags"]
        assert rel.target_field == "tag_ids"

    def test_tags_is_list(self):
        """Test tags is a list (many-to-many)."""
        rel = Gallery.__relationships__["tags"]
        assert rel.is_list is True

    def test_tags_query_strategy(self):
        """Test tags uses direct_field strategy."""
        rel = Gallery.__relationships__["tags"]
        assert rel.query_strategy == "direct_field"

    def test_tags_query_field(self):
        """Test tags query field is 'tags'."""
        rel = Gallery.__relationships__["tags"]
        assert rel.query_field == "tags"

    def test_tags_inverse_metadata(self):
        """Test tags has inverse relationship metadata."""
        rel = Gallery.__relationships__["tags"]
        assert rel.inverse_type == "Tag"

    def test_tags_auto_sync(self):
        """Test tags relationship has auto_sync enabled."""
        rel = Gallery.__relationships__["tags"]
        assert rel.auto_sync is True


class TestGalleryScenesRelationship:
    """Test Gallery.scenes relationship metadata."""

    def test_scenes_relationship_exists(self):
        """Test that scenes relationship is defined."""
        assert "scenes" in Gallery.__relationships__

    def test_scenes_target_field(self):
        """Test scenes relationship targets scene_ids."""
        rel = Gallery.__relationships__["scenes"]
        assert rel.target_field == "scene_ids"

    def test_scenes_is_list(self):
        """Test scenes is a list (many-to-many)."""
        rel = Gallery.__relationships__["scenes"]
        assert rel.is_list is True

    def test_scenes_query_strategy(self):
        """Test scenes uses direct_field strategy."""
        rel = Gallery.__relationships__["scenes"]
        assert rel.query_strategy == "direct_field"

    def test_scenes_query_field(self):
        """Test scenes query field is 'scenes'."""
        rel = Gallery.__relationships__["scenes"]
        assert rel.query_field == "scenes"

    def test_scenes_inverse_metadata(self):
        """Test scenes has inverse relationship metadata."""
        rel = Gallery.__relationships__["scenes"]
        assert rel.inverse_type == "Scene"
        assert rel.inverse_query_field == "galleries"

    def test_scenes_auto_sync(self):
        """Test scenes relationship has auto_sync enabled."""
        rel = Gallery.__relationships__["scenes"]
        assert rel.auto_sync is True


class TestGalleryRelationshipMetadataIntegration:
    """Integration tests for Gallery relationship metadata."""

    def test_all_relationships_have_required_fields(self):
        """Test that all relationships have required metadata fields."""
        for rel_name, rel_meta in Gallery.__relationships__.items():
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
        rel = Gallery.__relationships__["studio"]
        repr_str = repr(rel)

        assert "RelationshipMetadata" in repr_str
        assert "studio_id" in repr_str
        assert "filter_query" in repr_str

    def test_query_field_auto_derivation(self):
        """Test that query_field is auto-derived from target_field."""
        # studio_id → studio
        assert Gallery.__relationships__["studio"].query_field == "studio"

        # performer_ids → performers
        assert Gallery.__relationships__["performers"].query_field == "performers"

        # tag_ids → tags
        assert Gallery.__relationships__["tags"].query_field == "tags"

        # scene_ids → scenes
        assert Gallery.__relationships__["scenes"].query_field == "scenes"

    def test_no_transform_functions(self):
        """Test that all Gallery relationships use default ID extraction (no custom transform)."""
        for rel_name, rel_meta in Gallery.__relationships__.items():
            assert rel_meta.transform is None, (
                f"{rel_name} should not have custom transform"
            )
