"""Tests for Image RelationshipMetadata migration.

This module tests the Image type's relationship metadata, including:
- studio: filter_query strategy (many-to-one)
- performers: direct_field strategy (many-to-many)
- tags: direct_field strategy (many-to-many)
- galleries: direct_field strategy (many-to-many)

Image relationships follow simpler patterns (no complex_object strategies).
"""

from stash_graphql_client.types import RelationshipMetadata
from stash_graphql_client.types.image import Image


class TestImageRelationshipMigration:
    """Test that Image.__relationships__ uses RelationshipMetadata."""

    def test_all_relationships_use_metadata(self):
        """Test that all relationship entries use RelationshipMetadata objects."""
        relationships = Image.__relationships__

        # Image should have 4 relationships
        assert len(relationships) == 4
        assert "studio" in relationships
        assert "performers" in relationships
        assert "tags" in relationships
        assert "galleries" in relationships

        # All should be RelationshipMetadata instances
        for rel_name, rel_meta in relationships.items():
            assert isinstance(rel_meta, RelationshipMetadata), (
                f"{rel_name} should use RelationshipMetadata"
            )


class TestImageStudioRelationship:
    """Test Image.studio relationship (Pattern B: filter_query)."""

    def test_studio_relationship_metadata(self):
        """Test studio uses filter_query strategy."""
        rel = Image.__relationships__["studio"]

        assert isinstance(rel, RelationshipMetadata)
        assert rel.target_field == "studio_id"
        assert rel.is_list is False
        assert rel.query_field == "studio"
        assert rel.inverse_type == "Studio"
        assert rel.query_strategy == "filter_query"
        assert rel.transform is None
        assert rel.auto_sync is True

    def test_studio_filter_query_hint(self):
        """Test studio relationship provides filter query hint."""
        rel = Image.__relationships__["studio"]
        assert rel.filter_query_hint is not None
        assert "findImages" in rel.filter_query_hint


class TestImagePerformersRelationship:
    """Test Image.performers relationship (Pattern A: direct_field)."""

    def test_performers_relationship_metadata(self):
        """Test performers uses direct_field strategy."""
        rel = Image.__relationships__["performers"]

        assert isinstance(rel, RelationshipMetadata)
        assert rel.target_field == "performer_ids"
        assert rel.is_list is True
        assert rel.query_field == "performers"
        assert rel.inverse_type == "Performer"
        assert (
            rel.inverse_query_field is None
        )  # Performer has image_count, not images list
        assert rel.query_strategy == "direct_field"
        assert rel.transform is None
        assert rel.auto_sync is True


class TestImageTagsRelationship:
    """Test Image.tags relationship (Pattern A: direct_field)."""

    def test_tags_relationship_metadata(self):
        """Test tags uses direct_field strategy."""
        rel = Image.__relationships__["tags"]

        assert isinstance(rel, RelationshipMetadata)
        assert rel.target_field == "tag_ids"
        assert rel.is_list is True
        assert rel.query_field == "tags"
        assert rel.inverse_type == "Tag"
        assert rel.query_strategy == "direct_field"
        assert rel.transform is None
        assert rel.auto_sync is True


class TestImageGalleriesRelationship:
    """Test Image.galleries relationship (Pattern A: direct_field)."""

    def test_galleries_relationship_metadata(self):
        """Test galleries uses direct_field strategy."""
        rel = Image.__relationships__["galleries"]

        assert isinstance(rel, RelationshipMetadata)
        assert rel.target_field == "gallery_ids"
        assert rel.is_list is True
        assert rel.query_field == "galleries"
        assert rel.inverse_type == "Gallery"
        assert (
            rel.inverse_query_field is None
        )  # Gallery has image_count and image(index), not images list
        assert rel.query_strategy == "direct_field"
        assert rel.transform is None
        assert rel.auto_sync is True


class TestImageRelationshipPatterns:
    """Test Image relationship patterns and strategies."""

    def test_only_studio_uses_filter_query(self):
        """Test that only studio uses filter_query strategy."""
        filter_query_rels = [
            name
            for name, rel in Image.__relationships__.items()
            if rel.query_strategy == "filter_query"
        ]

        assert len(filter_query_rels) == 1
        assert filter_query_rels[0] == "studio"

    def test_most_relationships_use_direct_field(self):
        """Test that most relationships use direct_field strategy."""
        direct_field_rels = [
            name
            for name, rel in Image.__relationships__.items()
            if rel.query_strategy == "direct_field"
        ]

        # performers, tags, galleries all use direct_field
        assert len(direct_field_rels) == 3
        assert "performers" in direct_field_rels
        assert "tags" in direct_field_rels
        assert "galleries" in direct_field_rels

    def test_no_complex_object_relationships(self):
        """Test that Image has no complex_object relationships."""
        complex_rels = [
            name
            for name, rel in Image.__relationships__.items()
            if rel.query_strategy == "complex_object"
        ]

        # Image doesn't have any complex relationships like Group does
        assert len(complex_rels) == 0

    def test_no_transform_functions_needed(self):
        """Test that no Image relationships require transforms."""
        for rel_name, rel_meta in Image.__relationships__.items():
            assert rel_meta.transform is None, (
                f"{rel_name} should not need a transform function"
            )


class TestImageRelationshipBackwardCompatibility:
    """Test backward compatibility with legacy tuple format."""

    def test_studio_to_tuple_conversion(self):
        """Test that studio RelationshipMetadata converts to tuple."""
        rel = Image.__relationships__["studio"]
        legacy_tuple = rel.to_tuple()

        assert isinstance(legacy_tuple, tuple)
        assert len(legacy_tuple) == 3
        assert legacy_tuple[0] == "studio_id"
        assert legacy_tuple[1] is False
        assert legacy_tuple[2] is None

    def test_performers_to_tuple_conversion(self):
        """Test that performers RelationshipMetadata converts to tuple."""
        rel = Image.__relationships__["performers"]
        legacy_tuple = rel.to_tuple()

        assert isinstance(legacy_tuple, tuple)
        assert len(legacy_tuple) == 3
        assert legacy_tuple[0] == "performer_ids"
        assert legacy_tuple[1] is True
        assert legacy_tuple[2] is None
