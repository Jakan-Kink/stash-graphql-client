"""Tests for Performer RelationshipMetadata migration.

This module tests that Performer's __relationships__ dict properly defines
RelationshipMetadata instances with complete bidirectional information.
"""

from stash_graphql_client.types import RelationshipMetadata
from stash_graphql_client.types.files import StashID, StashIDInput
from stash_graphql_client.types.performer import Performer


class TestPerformerRelationshipMetadata:
    """Test Performer __relationships__ metadata definitions."""

    def test_performer_has_relationships_dict(self):
        """Test that Performer defines __relationships__ class variable."""
        assert hasattr(Performer, "__relationships__")
        assert isinstance(Performer.__relationships__, dict)

    def test_performer_relationships_count(self):
        """Test that Performer has expected number of relationships."""
        # Performer has 2 relationships: tags, stash_ids
        assert len(Performer.__relationships__) == 2

    def test_performer_relationships_keys(self):
        """Test that Performer has expected relationship keys."""
        expected_keys = {"tags", "stash_ids"}
        assert set(Performer.__relationships__.keys()) == expected_keys


class TestPerformerTagsRelationship:
    """Test Performer tags relationship metadata."""

    def test_tags_relationship_exists(self):
        """Test that tags relationship is defined."""
        assert "tags" in Performer.__relationships__

    def test_tags_target_field(self):
        """Test that tags maps to tag_ids in PerformerUpdateInput."""
        rel = Performer.__relationships__["tags"]
        assert rel.target_field == "tag_ids"

    def test_tags_is_list(self):
        """Test that tags is a many-to-many relationship."""
        rel = Performer.__relationships__["tags"]
        assert rel.is_list is True

    def test_tags_no_transform(self):
        """Test that tags doesn't require a transform function."""
        rel = Performer.__relationships__["tags"]
        assert rel.transform is None

    def test_tags_metadata_format(self):
        """Test tags RelationshipMetadata attributes."""
        rel = Performer.__relationships__["tags"]

        assert rel.target_field == "tag_ids"
        assert rel.is_list is True
        assert rel.query_field == "tags"
        assert rel.inverse_type == "Tag"
        assert rel.inverse_query_field == "performers"
        assert rel.query_strategy == "direct_field"
        assert rel.auto_sync is True
        assert rel.transform is None


class TestPerformerStashIDsRelationship:
    """Test Performer stash_ids relationship metadata with transform."""

    def test_stash_ids_relationship_exists(self):
        """Test that stash_ids relationship is defined."""
        assert "stash_ids" in Performer.__relationships__

    def test_stash_ids_has_transform_function(self):
        """Test that stash_ids has a transform function.

        StashID objects must be converted to StashIDInput for mutations.
        """
        rel = Performer.__relationships__["stash_ids"]
        assert rel.transform is not None
        assert callable(rel.transform)

    def test_stash_ids_transform_converts_to_input(self):
        """Test that transform converts StashID to StashIDInput."""
        rel = Performer.__relationships__["stash_ids"]

        # Create a mock StashID object
        mock_stash_id = StashID(endpoint="https://stashdb.org", stash_id="123abc")

        # Transform it
        result = rel.transform(mock_stash_id)

        # Verify it's a StashIDInput
        assert isinstance(result, StashIDInput)
        assert result.endpoint == "https://stashdb.org"
        assert result.stash_id == "123abc"

    def test_stash_ids_target_field(self):
        """Test that stash_ids maps to stash_ids in PerformerUpdateInput."""
        rel = Performer.__relationships__["stash_ids"]
        assert rel.target_field == "stash_ids"

    def test_stash_ids_is_list(self):
        """Test that stash_ids is a many-to-many relationship."""
        rel = Performer.__relationships__["stash_ids"]
        assert rel.is_list is True


class TestPerformerRelationshipBackwardCompatibility:
    """Test backward compatibility with legacy tuple format."""

    def test_to_tuple_conversion(self):
        """Test that RelationshipMetadata can convert back to tuple format."""
        rel = Performer.__relationships__["tags"]
        legacy_tuple = rel.to_tuple()

        assert isinstance(legacy_tuple, tuple)
        assert len(legacy_tuple) == 3
        assert legacy_tuple[0] == "tag_ids"
        assert legacy_tuple[1] is True
        assert legacy_tuple[2] is None


class TestPerformerRelationshipUsage:
    """Test that Performer relationships work correctly in practice."""

    def test_relationships_used_in_to_input(self):
        """Test that __relationships__ is used during to_input() conversion."""
        assert hasattr(Performer, "_process_relationships")

    def test_all_relationships_have_valid_structure(self):
        """Test that all Performer relationships have valid structure."""
        for rel_name, rel in Performer.__relationships__.items():
            assert isinstance(rel, RelationshipMetadata), (
                f"Relationship {rel_name} has invalid type: {type(rel)}"
            )
            assert isinstance(rel.target_field, str)
            assert isinstance(rel.is_list, bool)
            assert isinstance(rel.query_field, str)
