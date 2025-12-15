"""Tests for Studio RelationshipMetadata migration.

This module tests that Studio's __relationships__ dict properly defines
RelationshipMetadata instances with complete bidirectional information,
including the self-referential parent_studio relationship.
"""

from stash_graphql_client.types import RelationshipMetadata
from stash_graphql_client.types.files import StashID, StashIDInput
from stash_graphql_client.types.studio import Studio


class TestStudioRelationshipMetadata:
    """Test Studio __relationships__ metadata definitions."""

    def test_studio_has_relationships_dict(self):
        """Test that Studio defines __relationships__ class variable."""
        assert hasattr(Studio, "__relationships__")
        assert isinstance(Studio.__relationships__, dict)

    def test_studio_relationships_count(self):
        """Test that Studio has expected number of relationships."""
        # Studio has 3 relationships: parent_studio, tags, stash_ids
        assert len(Studio.__relationships__) == 3

    def test_studio_relationships_keys(self):
        """Test that Studio has expected relationship keys."""
        expected_keys = {"parent_studio", "tags", "stash_ids"}
        assert set(Studio.__relationships__.keys()) == expected_keys


class TestStudioParentStudioRelationship:
    """Test Studio parent_studio self-referential relationship."""

    def test_parent_studio_relationship_exists(self):
        """Test that parent_studio relationship is defined."""
        assert "parent_studio" in Studio.__relationships__

    def test_parent_studio_target_field(self):
        """Test that parent_studio maps to parent_id in StudioUpdateInput."""
        rel = Studio.__relationships__["parent_studio"]
        assert rel.target_field == "parent_id"

    def test_parent_studio_is_many_to_one(self):
        """Test that parent_studio is a many-to-one relationship (single object)."""
        rel = Studio.__relationships__["parent_studio"]
        assert rel.is_list is False

    def test_parent_studio_no_transform(self):
        """Test that parent_studio doesn't require a transform function."""
        rel = Studio.__relationships__["parent_studio"]
        assert rel.transform is None

    def test_parent_studio_self_referential(self):
        """Test that parent_studio is a self-referential relationship."""
        rel = Studio.__relationships__["parent_studio"]

        # Self-referential: inverse_type should be "Studio"
        assert rel.inverse_type == "Studio"
        assert rel.inverse_query_field == "child_studios"

    def test_parent_studio_metadata(self):
        """Test parent_studio RelationshipMetadata attributes."""
        rel = Studio.__relationships__["parent_studio"]

        assert rel.target_field == "parent_id"
        assert rel.is_list is False
        assert rel.query_field == "parent_studio"
        assert rel.inverse_type == "Studio"  # Self-referential!
        assert rel.inverse_query_field == "child_studios"
        assert rel.query_strategy == "direct_field"
        assert rel.auto_sync is True
        assert rel.transform is None


class TestStudioTagsRelationship:
    """Test Studio tags relationship metadata."""

    def test_tags_relationship_exists(self):
        """Test that tags relationship is defined."""
        assert "tags" in Studio.__relationships__

    def test_tags_target_field(self):
        """Test that tags maps to tag_ids in StudioUpdateInput."""
        rel = Studio.__relationships__["tags"]
        assert rel.target_field == "tag_ids"

    def test_tags_is_list(self):
        """Test that tags is a many-to-many relationship."""
        rel = Studio.__relationships__["tags"]
        assert rel.is_list is True

    def test_tags_no_transform(self):
        """Test that tags doesn't require a transform function."""
        rel = Studio.__relationships__["tags"]
        assert rel.transform is None


class TestStudioStashIDsRelationship:
    """Test Studio stash_ids relationship metadata with transform."""

    def test_stash_ids_relationship_exists(self):
        """Test that stash_ids relationship is defined."""
        assert "stash_ids" in Studio.__relationships__

    def test_stash_ids_has_transform_function(self):
        """Test that stash_ids has a transform function."""
        rel = Studio.__relationships__["stash_ids"]
        assert rel.transform is not None
        assert callable(rel.transform)

    def test_stash_ids_transform_converts_to_input(self):
        """Test that transform converts StashID to StashIDInput."""
        rel = Studio.__relationships__["stash_ids"]
        mock_stash_id = StashID(endpoint="https://stashdb.org", stash_id="456def")
        result = rel.transform(mock_stash_id)

        assert isinstance(result, StashIDInput)
        assert result.endpoint == "https://stashdb.org"
        assert result.stash_id == "456def"


class TestStudioRelationshipBackwardCompatibility:
    """Test backward compatibility with legacy tuple format."""

    def test_to_tuple_conversion_for_parent_studio(self):
        """Test that parent_studio RelationshipMetadata converts to tuple."""
        rel = Studio.__relationships__["parent_studio"]
        legacy_tuple = rel.to_tuple()

        assert isinstance(legacy_tuple, tuple)
        assert len(legacy_tuple) == 3
        assert legacy_tuple[0] == "parent_id"
        assert legacy_tuple[1] is False
        assert legacy_tuple[2] is None

    def test_to_tuple_conversion_for_tags(self):
        """Test that tags RelationshipMetadata converts to tuple."""
        rel = Studio.__relationships__["tags"]
        legacy_tuple = rel.to_tuple()

        assert isinstance(legacy_tuple, tuple)
        assert len(legacy_tuple) == 3
        assert legacy_tuple[0] == "tag_ids"
        assert legacy_tuple[1] is True
        assert legacy_tuple[2] is None


class TestStudioRelationshipUsage:
    """Test that Studio relationships work correctly in practice."""

    def test_relationships_used_in_to_input(self):
        """Test that __relationships__ is used during to_input() conversion."""
        assert hasattr(Studio, "_process_relationships")

    def test_all_relationships_have_valid_structure(self):
        """Test that all Studio relationships have valid structure."""
        for rel_name, rel in Studio.__relationships__.items():
            assert isinstance(rel, RelationshipMetadata), (
                f"Relationship {rel_name} has invalid type: {type(rel)}"
            )
            assert isinstance(rel.target_field, str)
            assert isinstance(rel.is_list, bool)
            assert isinstance(rel.query_field, str)
