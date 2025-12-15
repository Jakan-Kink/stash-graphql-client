"""Tests for RelationshipMetadata class.

This module tests the RelationshipMetadata class which documents
bidirectional relationships between Stash entity types.
"""

from stash_graphql_client.types import RelationshipMetadata
from stash_graphql_client.types.files import StashIDInput


class TestRelationshipMetadataBasics:
    """Test basic RelationshipMetadata functionality."""

    def test_simple_many_to_many(self):
        """Test simple many-to-many relationship with direct field."""
        rel = RelationshipMetadata(
            target_field="gallery_ids",
            is_list=True,
            query_field="galleries",
            inverse_type="Gallery",
            inverse_query_field="scenes",
            query_strategy="direct_field",
        )

        assert rel.target_field == "gallery_ids"
        assert rel.is_list is True
        assert rel.query_field == "galleries"
        assert rel.inverse_type == "Gallery"
        assert rel.inverse_query_field == "scenes"
        assert rel.query_strategy == "direct_field"
        assert rel.auto_sync is True  # Default
        assert rel.transform is None

    def test_many_to_one_relationship(self):
        """Test many-to-one relationship (single object)."""
        rel = RelationshipMetadata(
            target_field="studio_id",
            is_list=False,
            query_field="studio",
            inverse_type="Studio",
            query_strategy="filter_query",
        )

        assert rel.target_field == "studio_id"
        assert rel.is_list is False
        assert rel.query_field == "studio"
        assert rel.inverse_type == "Studio"
        assert rel.query_strategy == "filter_query"

    def test_with_transform_function(self):
        """Test relationship with custom transform function."""

        def transform_fn(s):
            return StashIDInput(endpoint=s.endpoint, stash_id=s.stash_id)

        rel = RelationshipMetadata(
            target_field="stash_ids",
            is_list=True,
            transform=transform_fn,
            query_field="stash_ids",
        )

        assert rel.transform is transform_fn
        assert rel.target_field == "stash_ids"
        assert rel.is_list is True

    def test_with_notes(self):
        """Test relationship with documentation notes."""
        rel = RelationshipMetadata(
            target_field="gallery_ids",
            is_list=True,
            notes="Both scene.galleries and gallery.scenes auto-sync",
        )

        assert rel.notes == "Both scene.galleries and gallery.scenes auto-sync"


class TestRelationshipMetadataQueryFieldDefaults:
    """Test automatic query_field derivation."""

    def test_auto_derive_from_ids_suffix(self):
        """Test query_field derived from _ids suffix.

        Note: Auto-derivation uses simple rules. For irregular plurals
        like gallery→galleries, users should provide query_field explicitly.
        """
        # Regular plural: performer_ids → performers
        rel = RelationshipMetadata(
            target_field="performer_ids",
            is_list=True,
        )

        # performer_ids → performers (simple +s)
        assert rel.query_field == "performers"

    def test_auto_derive_from_id_suffix(self):
        """Test query_field derived from _id suffix."""
        rel = RelationshipMetadata(
            target_field="studio_id",
            is_list=False,
        )

        # studio_id → studio
        assert rel.query_field == "studio"

    def test_auto_derive_no_suffix(self):
        """Test query_field when target ends with _ids but should stay same."""
        # For fields like stash_ids, the auto-derivation will add 's'
        # Users should provide query_field explicitly for these cases
        rel = RelationshipMetadata(
            target_field="stash_ids",
            is_list=True,
            query_field="stash_ids",  # Explicitly provided
        )

        assert rel.query_field == "stash_ids"

    def test_explicit_query_field_overrides_default(self):
        """Test that explicit query_field overrides auto-derivation."""
        rel = RelationshipMetadata(
            target_field="performer_ids",
            is_list=True,
            query_field="custom_performers",
        )

        assert rel.query_field == "custom_performers"


class TestRelationshipMetadataQueryStrategies:
    """Test different query strategy patterns."""

    def test_direct_field_strategy(self):
        """Test Pattern A: direct nested field."""
        rel = RelationshipMetadata(
            target_field="performer_ids",
            is_list=True,
            query_strategy="direct_field",
            inverse_type="Performer",
            inverse_query_field="scenes",
        )

        assert rel.query_strategy == "direct_field"
        assert rel.filter_query_hint is None  # Not needed for direct fields

    def test_filter_query_strategy(self):
        """Test Pattern B: filter-based query."""
        rel = RelationshipMetadata(
            target_field="studio_id",
            is_list=False,
            query_strategy="filter_query",
            filter_query_hint="findScenes(scene_filter={studios: {value: [studio_id]}})",
        )

        assert rel.query_strategy == "filter_query"
        assert rel.filter_query_hint is not None
        assert "findScenes" in rel.filter_query_hint

    def test_complex_object_strategy(self):
        """Test Pattern C: complex objects with metadata."""
        rel = RelationshipMetadata(
            target_field="sub_groups",
            is_list=True,
            query_strategy="complex_object",
            inverse_type="Group",
            inverse_query_field="containing_groups",
            notes="Uses GroupDescription wrapper with nested group + description",
        )

        assert rel.query_strategy == "complex_object"
        assert "GroupDescription" in rel.notes

    def test_default_strategy_is_direct_field(self):
        """Test that direct_field is the default query strategy."""
        rel = RelationshipMetadata(
            target_field="tag_ids",
            is_list=True,
        )

        assert rel.query_strategy == "direct_field"


class TestRelationshipMetadataBackwardCompatibility:
    """Test backward compatibility with legacy tuple format."""

    def test_to_tuple_conversion(self):
        """Test conversion to legacy (target_field, is_list, transform) tuple."""
        rel = RelationshipMetadata(
            target_field="gallery_ids",
            is_list=True,
            transform=None,
        )

        legacy_tuple = rel.to_tuple()

        assert isinstance(legacy_tuple, tuple)
        assert len(legacy_tuple) == 3
        assert legacy_tuple[0] == "gallery_ids"
        assert legacy_tuple[1] is True
        assert legacy_tuple[2] is None

    def test_to_tuple_with_transform(self):
        """Test to_tuple() preserves transform function."""

        def transform_fn(x):
            return x

        rel = RelationshipMetadata(
            target_field="stash_ids",
            is_list=True,
            transform=transform_fn,
        )

        legacy_tuple = rel.to_tuple()

        assert legacy_tuple[2] is transform_fn


class TestRelationshipMetadataRepresentation:
    """Test string representation for debugging."""

    def test_repr_basic(self):
        """Test __repr__ output format."""
        rel = RelationshipMetadata(
            target_field="gallery_ids",
            is_list=True,
            query_field="galleries",
            query_strategy="direct_field",
        )

        repr_str = repr(rel)

        assert "RelationshipMetadata" in repr_str
        assert "gallery_ids" in repr_str
        assert "galleries" in repr_str
        assert "direct_field" in repr_str

    def test_repr_filter_query_strategy(self):
        """Test __repr__ with filter_query strategy."""
        rel = RelationshipMetadata(
            target_field="studio_id",
            is_list=False,
            query_strategy="filter_query",
        )

        repr_str = repr(rel)

        assert "filter_query" in repr_str


class TestRelationshipMetadataRealWorldExamples:
    """Test real-world relationship examples from Stash schema."""

    def test_scene_galleries_relationship(self):
        """Test Scene → Gallery many-to-many relationship."""
        rel = RelationshipMetadata(
            target_field="gallery_ids",
            is_list=True,
            query_field="galleries",
            inverse_type="Gallery",
            inverse_query_field="scenes",
            query_strategy="direct_field",
            notes="Both scene.galleries and gallery.scenes auto-sync",
        )

        assert rel.target_field == "gallery_ids"
        assert rel.query_field == "galleries"
        assert rel.is_list is True
        assert rel.query_strategy == "direct_field"
        assert rel.auto_sync is True

    def test_scene_studio_relationship(self):
        """Test Scene → Studio many-to-one with filter query."""
        rel = RelationshipMetadata(
            target_field="studio_id",
            is_list=False,
            query_field="studio",
            inverse_type="Studio",
            inverse_query_field=None,  # No direct scenes field
            query_strategy="filter_query",
            filter_query_hint="findScenes(scene_filter={studios: {value: [studio_id]}})",
            notes="Studio has scene_count and filter queries, not direct scenes field",
        )

        assert rel.target_field == "studio_id"
        assert rel.is_list is False
        assert rel.inverse_query_field is None
        assert rel.query_strategy == "filter_query"
        assert rel.filter_query_hint is not None

    def test_group_sub_groups_relationship(self):
        """Test Group hierarchy with complex objects."""

        def transform_fn(g):
            return {
                "group_id": g.id,
                "description": getattr(g, "description", None),
            }

        rel = RelationshipMetadata(
            target_field="sub_groups",
            is_list=True,
            transform=transform_fn,
            query_field="sub_groups",
            inverse_type="Group",
            inverse_query_field="containing_groups",
            query_strategy="complex_object",
            notes="Uses GroupDescription wrapper with nested group + description",
        )

        assert rel.query_strategy == "complex_object"
        assert rel.transform is not None
        assert rel.inverse_type == "Group"

    def test_scene_stash_ids_relationship(self):
        """Test StashID relationship with transform."""

        def transform_fn(s):
            return StashIDInput(endpoint=s.endpoint, stash_id=s.stash_id)

        rel = RelationshipMetadata(
            target_field="stash_ids",
            is_list=True,
            transform=transform_fn,
            query_field="stash_ids",
            notes="Requires transform to StashIDInput",
        )

        assert rel.transform is transform_fn
        assert "StashIDInput" in rel.notes

    def test_tag_parent_child_relationship(self):
        """Test Tag self-referential hierarchy."""
        rel = RelationshipMetadata(
            target_field="parent_ids",
            is_list=True,
            query_field="parents",
            inverse_type="Tag",
            inverse_query_field="children",
            query_strategy="direct_field",
            notes="Backend auto-syncs both parent_ids and child_ids",
        )

        assert rel.inverse_type == "Tag"  # Self-referential
        assert rel.auto_sync is True


class TestRelationshipMetadataValidation:
    """Test validation and edge cases."""

    def test_minimal_required_fields(self):
        """Test creating RelationshipMetadata with only required fields."""
        rel = RelationshipMetadata(
            target_field="tag_ids",
            is_list=True,
        )

        # Should have sensible defaults
        assert rel.target_field == "tag_ids"
        assert rel.is_list is True
        assert rel.query_field == "tags"  # Auto-derived
        assert rel.query_strategy == "direct_field"  # Default
        assert rel.auto_sync is True  # Default
        assert rel.transform is None
        assert rel.notes == ""

    def test_type_annotation_flexibility(self):
        """Test that inverse_type accepts both string and type."""
        # String (avoids circular imports)
        rel1 = RelationshipMetadata(
            target_field="studio_id",
            is_list=False,
            inverse_type="Studio",
        )

        # Type object (when import is available)
        from stash_graphql_client.types.studio import Studio

        rel2 = RelationshipMetadata(
            target_field="studio_id",
            is_list=False,
            inverse_type=Studio,
        )

        assert rel1.inverse_type == "Studio"
        assert rel2.inverse_type is Studio

    def test_optional_fields_remain_none(self):
        """Test that optional fields remain None when not provided."""
        rel = RelationshipMetadata(
            target_field="tag_ids",
            is_list=True,
        )

        assert rel.inverse_type is None
        assert rel.inverse_query_field is None
        assert rel.filter_query_hint is None
        assert rel.transform is None


class TestRelationshipMetadataDocumentation:
    """Test that metadata provides good documentation value."""

    def test_auto_sync_always_true_for_stash(self):
        """Test that auto_sync defaults to True (empirically verified for Stash)."""
        rel = RelationshipMetadata(
            target_field="gallery_ids",
            is_list=True,
        )

        assert rel.auto_sync is True

    def test_can_override_auto_sync_if_needed(self):
        """Test that auto_sync can be overridden (for future use cases)."""
        rel = RelationshipMetadata(
            target_field="custom_field",
            is_list=True,
            auto_sync=False,
        )

        assert rel.auto_sync is False

    def test_notes_provide_context(self):
        """Test that notes field provides valuable context."""
        rel = RelationshipMetadata(
            target_field="studio_id",
            is_list=False,
            query_strategy="filter_query",
            notes="Studio uses filter-based queries, not direct scenes field. "
            "Use findScenes(scene_filter) to query inverse relationship.",
        )

        assert len(rel.notes) > 0
        assert "filter-based queries" in rel.notes
        assert "findScenes" in rel.notes
