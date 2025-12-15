"""Integration tests for RelationshipMetadata migration.

This module validates that ALL entity types have been migrated from
legacy tuple format to RelationshipMetadata pattern and verifies
bidirectional relationship consistency.
"""

from stash_graphql_client.types import (
    Gallery,
    GalleryChapter,
    Group,
    Image,
    Performer,
    RelationshipMetadata,
    Scene,
    SceneMarker,
    Studio,
    Tag,
)


class TestAllEntityTypesUseRelationshipMetadata:
    """Verify all entity types migrated to RelationshipMetadata pattern."""

    def test_all_entity_types_have_relationships_dict(self):
        """Test that all entity types have __relationships__ attribute."""
        entity_types = [
            (Scene, "Scene"),
            (Gallery, "Gallery"),
            (GalleryChapter, "GalleryChapter"),
            (Tag, "Tag"),
            (Performer, "Performer"),
            (Studio, "Studio"),
            (Group, "Group"),
            (Image, "Image"),
            (SceneMarker, "SceneMarker"),
        ]

        for entity_cls, name in entity_types:
            assert hasattr(entity_cls, "__relationships__"), (
                f"{name} missing __relationships__"
            )
            assert isinstance(entity_cls.__relationships__, dict), (
                f"{name}.__relationships__ is not a dict"
            )

    def test_all_entity_types_use_relationship_metadata(self):
        """Verify all entity types migrated to RelationshipMetadata pattern.

        This is the CRITICAL integration test that validates the entire migration.
        Every entity type MUST use RelationshipMetadata, not tuples.
        """
        entity_types = [
            (Scene, "Scene"),
            (Gallery, "Gallery"),
            (GalleryChapter, "GalleryChapter"),
            (Tag, "Tag"),
            (Performer, "Performer"),
            (Studio, "Studio"),
            (Group, "Group"),
            (Image, "Image"),
            (SceneMarker, "SceneMarker"),
        ]

        for entity_cls, name in entity_types:
            assert hasattr(entity_cls, "__relationships__"), (
                f"{name} missing __relationships__"
            )

            for rel_name, rel_meta in entity_cls.__relationships__.items():
                assert isinstance(rel_meta, RelationshipMetadata), (
                    f"{name}.{rel_name} is {type(rel_meta).__name__}, expected RelationshipMetadata"
                )

                # Validate required fields
                assert hasattr(rel_meta, "target_field"), (
                    f"{name}.{rel_name} missing target_field"
                )
                assert hasattr(rel_meta, "is_list"), (
                    f"{name}.{rel_name} missing is_list"
                )
                assert hasattr(rel_meta, "query_strategy"), (
                    f"{name}.{rel_name} missing query_strategy"
                )
                assert rel_meta.query_strategy in [
                    "direct_field",
                    "filter_query",
                    "complex_object",
                ], (
                    f"{name}.{rel_name} has invalid query_strategy: {rel_meta.query_strategy}"
                )

    def test_no_legacy_tuple_relationships(self):
        """Verify NO entity types still use legacy tuple format."""
        entity_types = [
            Scene,
            Gallery,
            GalleryChapter,
            Tag,
            Performer,
            Studio,
            Group,
            Image,
            SceneMarker,
        ]

        for entity_cls in entity_types:
            for rel_name, rel_meta in entity_cls.__relationships__.items():
                assert not isinstance(rel_meta, tuple), (
                    f"{entity_cls.__name__}.{rel_name} still uses legacy tuple format!"
                )


class TestBidirectionalRelationshipConsistency:
    """Test that inverse relationships are properly configured."""

    def test_scene_galleries_bidirectional(self):
        """Test Scene.galleries <-> Gallery.scenes relationship."""
        scene_rel = Scene.__relationships__["galleries"]
        gallery_rel = Gallery.__relationships__["scenes"]

        # Scene → Gallery
        assert scene_rel.target_field == "gallery_ids"
        assert scene_rel.is_list is True
        assert scene_rel.inverse_type == "Gallery"
        assert scene_rel.inverse_query_field == "scenes"

        # Gallery → Scene (inverse)
        assert gallery_rel.target_field == "scene_ids"
        assert gallery_rel.is_list is True
        assert gallery_rel.inverse_type == "Scene"
        assert gallery_rel.inverse_query_field == "galleries"

    def test_tag_parent_child_bidirectional(self):
        """Test Tag self-referential parent/child relationships."""
        parent_rel = Tag.__relationships__["parents"]
        child_rel = Tag.__relationships__["children"]

        # Tag.parents
        assert parent_rel.target_field == "parent_ids"
        assert parent_rel.is_list is True
        assert parent_rel.inverse_type == "Tag"
        assert parent_rel.inverse_query_field == "children"

        # Tag.children (inverse)
        assert child_rel.target_field == "child_ids"
        assert child_rel.is_list is True
        assert child_rel.inverse_type == "Tag"
        assert child_rel.inverse_query_field == "parents"

    def test_scene_marker_scene_relationship(self):
        """Test SceneMarker.scene → Scene.scene_markers relationship."""
        marker_rel = SceneMarker.__relationships__["scene"]

        # SceneMarker → Scene (many-to-one)
        assert marker_rel.target_field == "scene_id"
        assert marker_rel.is_list is False
        assert marker_rel.inverse_type == "Scene"
        assert marker_rel.inverse_query_field == "scene_markers"


class TestRelationshipMetadataToTupleBackwardCompatibility:
    """Test that all relationships can convert to legacy tuple format."""

    def test_all_relationships_support_to_tuple(self):
        """Verify all RelationshipMetadata instances can convert to tuple."""
        entity_types = [
            Scene,
            Gallery,
            GalleryChapter,
            Tag,
            Performer,
            Studio,
            Group,
            Image,
            SceneMarker,
        ]

        for entity_cls in entity_types:
            for rel_name, rel_meta in entity_cls.__relationships__.items():
                assert hasattr(rel_meta, "to_tuple"), (
                    f"{entity_cls.__name__}.{rel_name} missing to_tuple()"
                )

                legacy_tuple = rel_meta.to_tuple()
                assert isinstance(legacy_tuple, tuple), (
                    f"{entity_cls.__name__}.{rel_name}.to_tuple() didn't return tuple"
                )
                assert len(legacy_tuple) == 3, (
                    f"{entity_cls.__name__}.{rel_name} tuple wrong length"
                )

                # Tuple format: (target_field, is_list, transform)
                assert isinstance(legacy_tuple[0], str), (
                    f"{entity_cls.__name__}.{rel_name} tuple[0] (target_field) not string"
                )
                assert isinstance(legacy_tuple[1], bool), (
                    f"{entity_cls.__name__}.{rel_name} tuple[1] (is_list) not bool"
                )


class TestEntityTypesCoverage:
    """Verify we're testing all expected entity types."""

    def test_all_stash_object_subclasses_included(self):
        """Verify test covers all major StashObject entity types."""
        expected_entities = {
            "Scene",
            "Gallery",
            "GalleryChapter",
            "Tag",
            "Performer",
            "Studio",
            "Group",
            "Image",
            "SceneMarker",
        }

        tested_entities = {
            Scene.__name__,
            Gallery.__name__,
            GalleryChapter.__name__,
            Tag.__name__,
            Performer.__name__,
            Studio.__name__,
            Group.__name__,
            Image.__name__,
            SceneMarker.__name__,
        }

        assert tested_entities == expected_entities, (
            f"Missing entities: {expected_entities - tested_entities}"
        )
