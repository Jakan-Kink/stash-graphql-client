"""Tests for Group RelationshipMetadata migration.

This module tests the Group type's relationship metadata, including:
- studio: filter_query strategy (many-to-one)
- tags: direct_field strategy (many-to-many)
- containing_groups: complex_object strategy with GroupDescriptionInput transform
- sub_groups: complex_object strategy with GroupDescriptionInput transform

Special focus on self-referential relationships (containing_groups ↔ sub_groups).
"""

from stash_graphql_client.types import RelationshipMetadata
from stash_graphql_client.types.group import (
    Group,
    GroupDescription,
    GroupDescriptionInput,
)


class TestGroupRelationshipMigration:
    """Test that Group.__relationships__ uses RelationshipMetadata."""

    def test_all_relationships_use_metadata(self):
        """Test that all relationship entries use RelationshipMetadata objects."""
        relationships = Group.__relationships__

        # Group should have 4 relationships
        assert len(relationships) == 4
        assert "studio" in relationships
        assert "tags" in relationships
        assert "containing_groups" in relationships
        assert "sub_groups" in relationships

        # All should be RelationshipMetadata instances
        for rel_name, rel_meta in relationships.items():
            assert isinstance(rel_meta, RelationshipMetadata), (
                f"{rel_name} should use RelationshipMetadata"
            )


class TestGroupStudioRelationship:
    """Test Group.studio relationship (Pattern B: filter_query)."""

    def test_studio_relationship_metadata(self):
        """Test studio uses filter_query strategy."""
        rel = Group.__relationships__["studio"]

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
        rel = Group.__relationships__["studio"]

        assert rel.filter_query_hint is not None
        assert "findGroups" in rel.filter_query_hint


class TestGroupTagsRelationship:
    """Test Group.tags relationship (Pattern A: direct_field)."""

    def test_tags_relationship_metadata(self):
        """Test tags uses direct_field strategy."""
        rel = Group.__relationships__["tags"]

        assert isinstance(rel, RelationshipMetadata)
        assert rel.target_field == "tag_ids"
        assert rel.is_list is True
        assert rel.query_field == "tags"
        assert rel.inverse_type == "Tag"
        assert rel.inverse_query_field is None  # Tag has group_count, not groups list
        assert rel.query_strategy == "direct_field"
        assert rel.transform is None
        assert rel.auto_sync is True


class TestGroupContainingGroupsRelationship:
    """Test Group.containing_groups relationship (Pattern C: complex_object)."""

    def test_containing_groups_relationship_metadata(self):
        """Test containing_groups uses complex_object strategy."""
        rel = Group.__relationships__["containing_groups"]

        assert isinstance(rel, RelationshipMetadata)
        assert rel.target_field == "containing_groups"
        assert rel.is_list is True
        assert rel.query_field == "containing_groups"
        assert rel.inverse_type == "Group"
        assert rel.inverse_query_field == "sub_groups"
        assert rel.query_strategy == "complex_object"
        assert rel.transform is not None
        assert rel.auto_sync is True

    def test_containing_groups_transform_function(self):
        """Test transform handles GroupDescription → GroupDescriptionInput."""
        rel = Group.__relationships__["containing_groups"]

        # Create mock GroupDescription
        mock_group = Group(id="group-123", name="Test Group")
        mock_desc = GroupDescription(group=mock_group, description="Parent group")

        # Apply transform
        result = rel.transform(mock_desc)

        # Should produce GroupDescriptionInput
        assert isinstance(result, GroupDescriptionInput)
        assert result.group_id == "group-123"
        assert result.description == "Parent group"


class TestGroupSubGroupsRelationship:
    """Test Group.sub_groups relationship (Pattern C: complex_object)."""

    def test_sub_groups_relationship_metadata(self):
        """Test sub_groups uses complex_object strategy."""
        rel = Group.__relationships__["sub_groups"]

        assert isinstance(rel, RelationshipMetadata)
        assert rel.target_field == "sub_groups"
        assert rel.is_list is True
        assert rel.query_field == "sub_groups"
        assert rel.inverse_type == "Group"
        assert rel.inverse_query_field == "containing_groups"
        assert rel.query_strategy == "complex_object"
        assert rel.transform is not None
        assert rel.auto_sync is True

    def test_sub_groups_transform_function(self):
        """Test transform handles GroupDescription → GroupDescriptionInput."""
        rel = Group.__relationships__["sub_groups"]

        # Create mock GroupDescription
        mock_group = Group(id="subgroup-789", name="Child Group")
        mock_desc = GroupDescription(group=mock_group, description="Child description")

        # Apply transform
        result = rel.transform(mock_desc)

        # Should produce GroupDescriptionInput
        assert isinstance(result, GroupDescriptionInput)
        assert result.group_id == "subgroup-789"
        assert result.description == "Child description"


class TestGroupSelfReferentialRelationships:
    """Test containing_groups ↔ sub_groups inverse relationship."""

    def test_containing_groups_and_sub_groups_are_inverses(self):
        """Test that containing_groups and sub_groups reference each other."""
        containing_rel = Group.__relationships__["containing_groups"]
        sub_rel = Group.__relationships__["sub_groups"]

        # Both should point to Group type (self-referential)
        assert containing_rel.inverse_type == "Group"
        assert sub_rel.inverse_type == "Group"

        # They should reference each other
        assert containing_rel.inverse_query_field == "sub_groups"
        assert sub_rel.inverse_query_field == "containing_groups"


class TestGroupRelationshipBackwardCompatibility:
    """Test backward compatibility with legacy tuple format."""

    def test_studio_to_tuple_conversion(self):
        """Test that studio RelationshipMetadata converts to tuple."""
        rel = Group.__relationships__["studio"]
        legacy_tuple = rel.to_tuple()

        assert isinstance(legacy_tuple, tuple)
        assert len(legacy_tuple) == 3
        assert legacy_tuple[0] == "studio_id"
        assert legacy_tuple[1] is False
        assert legacy_tuple[2] is None
