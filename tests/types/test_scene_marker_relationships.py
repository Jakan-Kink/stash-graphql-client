"""Tests for SceneMarker relationship metadata.

This module validates that SceneMarker uses RelationshipMetadata
for all relationships and verifies the relationship configurations.
"""

from stash_graphql_client.types import RelationshipMetadata, SceneMarker
from stash_graphql_client.types.scene import Scene
from stash_graphql_client.types.tag import Tag


class TestSceneMarkerRelationshipMetadata:
    """Test SceneMarker relationship metadata configuration."""

    def test_has_relationships_dict(self):
        """Test that SceneMarker has __relationships__ attribute."""
        assert hasattr(SceneMarker, "__relationships__")
        assert isinstance(SceneMarker.__relationships__, dict)

    def test_all_relationships_use_metadata(self):
        """Test that all relationships use RelationshipMetadata, not tuples."""
        for rel_name, rel_meta in SceneMarker.__relationships__.items():
            assert isinstance(rel_meta, RelationshipMetadata), (
                f"SceneMarker.{rel_name} should use RelationshipMetadata, got {type(rel_meta).__name__}"
            )

    def test_scene_relationship_metadata(self):
        """Test scene relationship configuration."""
        rel = SceneMarker.__relationships__["scene"]

        assert isinstance(rel, RelationshipMetadata)
        assert rel.target_field == "scene_id"
        assert rel.is_list is False
        assert rel.query_field == "scene"
        assert rel.query_strategy == "direct_field"
        assert rel.transform is None
        assert rel.inverse_type == "Scene"
        assert rel.inverse_query_field == "scene_markers"

    def test_primary_tag_relationship_metadata(self):
        """Test primary_tag relationship configuration."""
        rel = SceneMarker.__relationships__["primary_tag"]

        assert isinstance(rel, RelationshipMetadata)
        assert rel.target_field == "primary_tag_id"
        assert rel.is_list is False
        assert rel.query_field == "primary_tag"
        assert rel.query_strategy == "direct_field"
        assert rel.transform is None
        assert rel.inverse_type == "Tag"

    def test_tags_relationship_metadata(self):
        """Test tags relationship configuration (many-to-many)."""
        rel = SceneMarker.__relationships__["tags"]

        assert isinstance(rel, RelationshipMetadata)
        assert rel.target_field == "tag_ids"
        assert rel.is_list is True
        assert rel.query_field == "tags"
        assert rel.query_strategy == "direct_field"
        assert rel.transform is None
        assert rel.inverse_type == "Tag"

    def test_relationship_count(self):
        """Test that SceneMarker has exactly 3 relationships."""
        assert len(SceneMarker.__relationships__) == 3
        assert "scene" in SceneMarker.__relationships__
        assert "primary_tag" in SceneMarker.__relationships__
        assert "tags" in SceneMarker.__relationships__


class TestSceneMarkerRelationshipUsage:
    """Test SceneMarker relationship functionality in practice."""

    def test_scene_marker_to_scene_relationship(self):
        """Test creating SceneMarker with scene relationship."""
        scene = Scene.model_construct(
            id="scene-1", title="Test Scene", organized=False, urls=[]
        )
        marker = SceneMarker.model_construct(
            id="marker-1", title="Intro", seconds=10.0, scene=scene
        )

        assert marker.scene is scene
        assert marker.scene.id == "scene-1"

    def test_scene_marker_to_primary_tag_relationship(self):
        """Test creating SceneMarker with primary_tag relationship."""
        tag = Tag.model_construct(id="tag-1", name="Action", parents=[], children=[])
        marker = SceneMarker.model_construct(
            id="marker-1", title="Fight Scene", seconds=120.0, primary_tag=tag
        )

        assert marker.primary_tag is tag
        assert marker.primary_tag.name == "Action"

    def test_scene_marker_to_tags_relationship(self):
        """Test creating SceneMarker with multiple tags."""
        tag1 = Tag.model_construct(id="tag-1", name="Action", parents=[], children=[])
        tag2 = Tag.model_construct(id="tag-2", name="Drama", parents=[], children=[])
        marker = SceneMarker.model_construct(
            id="marker-1", title="Climax", seconds=300.0, tags=[tag1, tag2]
        )

        assert len(marker.tags) == 2
        assert tag1 in marker.tags
        assert tag2 in marker.tags


class TestSceneMarkerBackwardCompatibility:
    """Test backward compatibility with legacy tuple format."""

    def test_to_tuple_conversion_scene(self):
        """Test that scene relationship can convert to legacy tuple."""
        rel = SceneMarker.__relationships__["scene"]
        legacy_tuple = rel.to_tuple()

        assert isinstance(legacy_tuple, tuple)
        assert len(legacy_tuple) == 3
        assert legacy_tuple[0] == "scene_id"
        assert legacy_tuple[1] is False
        assert legacy_tuple[2] is None

    def test_to_tuple_conversion_primary_tag(self):
        """Test that primary_tag relationship can convert to legacy tuple."""
        rel = SceneMarker.__relationships__["primary_tag"]
        legacy_tuple = rel.to_tuple()

        assert isinstance(legacy_tuple, tuple)
        assert len(legacy_tuple) == 3
        assert legacy_tuple[0] == "primary_tag_id"
        assert legacy_tuple[1] is False
        assert legacy_tuple[2] is None

    def test_to_tuple_conversion_tags(self):
        """Test that tags relationship can convert to legacy tuple."""
        rel = SceneMarker.__relationships__["tags"]
        legacy_tuple = rel.to_tuple()

        assert isinstance(legacy_tuple, tuple)
        assert len(legacy_tuple) == 3
        assert legacy_tuple[0] == "tag_ids"
        assert legacy_tuple[1] is True
        assert legacy_tuple[2] is None


class TestSceneMarkerRelationshipValidation:
    """Test relationship metadata validation."""

    def test_required_metadata_fields_present(self):
        """Test that all relationships have required metadata fields."""
        for rel_name, rel_meta in SceneMarker.__relationships__.items():
            assert hasattr(rel_meta, "target_field"), f"{rel_name} missing target_field"
            assert hasattr(rel_meta, "is_list"), f"{rel_name} missing is_list"
            assert hasattr(rel_meta, "query_field"), f"{rel_name} missing query_field"
            assert hasattr(rel_meta, "query_strategy"), (
                f"{rel_name} missing query_strategy"
            )

            assert rel_meta.query_strategy in [
                "direct_field",
                "filter_query",
                "complex_object",
            ], f"{rel_name} has invalid query_strategy: {rel_meta.query_strategy}"

    def test_all_use_direct_field_strategy(self):
        """Test that SceneMarker relationships use direct_field strategy."""
        for rel_name, rel_meta in SceneMarker.__relationships__.items():
            assert rel_meta.query_strategy == "direct_field", (
                f"{rel_name} should use direct_field strategy"
            )
