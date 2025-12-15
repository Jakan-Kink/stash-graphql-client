"""Tests for in-memory inverse relationship syncing.

This module tests that when you set a relationship field on one object,
the inverse relationship is automatically updated on related objects
in the same identity map.
"""

from stash_graphql_client.types import Tag


class TestTagSelfReferentialSync:
    """Test self-referential relationship auto-sync for Tag parent/child."""

    def test_parent_child_traversal(self):
        """Test the user's exact example: tag_parent.children[0].children[0] == tag_child."""
        # Create tags with empty relationship lists
        tag_parent = Tag(name="Parent", parents=[], children=[])
        tag_base = Tag(name="Base", parents=[], children=[])
        tag_child = Tag(name="Child", parents=[], children=[])

        # Set relationships on tag_base
        tag_base.parents = [tag_parent]
        tag_base.children = [tag_child]

        # Verify inverse relationships were auto-synced
        assert tag_base in tag_parent.children, (
            "tag_parent.children should include tag_base"
        )
        assert tag_base in tag_child.parents, (
            "tag_child.parents should include tag_base"
        )

        # Verify the traversal works
        assert tag_parent.children[0] == tag_base
        assert tag_parent.children[0].children[0] == tag_child

    def test_add_parent_syncs_inverse(self):
        """Test that setting parents automatically updates parent.children."""
        parent = Tag(name="Parent", parents=[], children=[])
        child = Tag(name="Child", parents=[], children=[])

        # Set parent on child
        child.parents = [parent]

        # Verify parent's children includes child
        assert child in parent.children

    def test_add_child_syncs_inverse(self):
        """Test that setting children automatically updates child.parents."""
        parent = Tag(name="Parent", parents=[], children=[])
        child = Tag(name="Child", parents=[], children=[])

        # Set child on parent
        parent.children = [child]

        # Verify child's parents includes parent
        assert parent in child.parents

    def test_multiple_parents(self):
        """Test syncing with multiple parents."""
        parent1 = Tag(name="Parent1", parents=[], children=[])
        parent2 = Tag(name="Parent2", parents=[], children=[])
        child = Tag(name="Child", parents=[], children=[])

        # Set multiple parents
        child.parents = [parent1, parent2]

        # Verify both parents have child
        assert child in parent1.children
        assert child in parent2.children

    def test_multiple_children(self):
        """Test syncing with multiple children."""
        parent = Tag(name="Parent", parents=[], children=[])
        child1 = Tag(name="Child1", parents=[], children=[])
        child2 = Tag(name="Child2", parents=[], children=[])

        # Set multiple children
        parent.children = [child1, child2]

        # Verify both children have parent
        assert parent in child1.parents
        assert parent in child2.parents

    def test_deep_hierarchy(self):
        """Test syncing in a deep tag hierarchy."""
        grandparent = Tag(name="Grandparent", parents=[], children=[])
        parent = Tag(name="Parent", parents=[], children=[])
        child = Tag(name="Child", parents=[], children=[])
        grandchild = Tag(name="Grandchild", parents=[], children=[])

        # Build hierarchy
        parent.parents = [grandparent]
        child.parents = [parent]
        grandchild.parents = [child]

        # Verify entire chain
        assert grandparent.children[0] == parent
        assert grandparent.children[0].children[0] == child
        assert grandparent.children[0].children[0].children[0] == grandchild

        # Verify inverse chain
        assert grandchild.parents[0] == child
        assert grandchild.parents[0].parents[0] == parent
        assert grandchild.parents[0].parents[0].parents[0] == grandparent

    def test_unset_relationships_not_synced(self):
        """Test that UNSET relationships don't trigger sync."""

        parent = Tag(name="Parent")  # parents/children default to UNSET
        child = Tag(name="Child", parents=[])  # Explicitly set to empty list

        # This should not crash even though parent.children is UNSET
        child.parents = [parent]

        # parent.children is still UNSET, so sync is skipped
        # (This is expected behavior - can't sync to UNSET fields)
        from stash_graphql_client.types.unset import UnsetType

        assert isinstance(parent.children, UnsetType)

    def test_duplicate_prevention(self):
        """Test that setting the same relationship twice doesn't create duplicates."""
        parent = Tag(name="Parent", parents=[], children=[])
        child = Tag(name="Child", parents=[], children=[])

        # Set relationship twice
        child.parents = [parent]
        child.parents = [parent]  # Set again

        # Should only have one entry
        assert len(parent.children) == 1
        assert parent.children[0] == child


class TestSceneRelationshipSync:
    """Test relationship auto-sync for Scene."""

    def test_scene_gallery_sync(self):
        """Test that setting scene.galleries updates gallery.scenes."""
        from stash_graphql_client.types import Gallery, Scene

        scene = Scene(title="Test Scene", galleries=[], performers=[], tags=[])
        gallery = Gallery(title="Test Gallery", scenes=[])

        # Set gallery on scene
        scene.galleries = [gallery]

        # Verify inverse
        assert scene in gallery.scenes

    def test_scene_performer_sync(self):
        """Test that setting scene.performers updates performer.scenes."""
        from stash_graphql_client.types import Performer, Scene

        scene = Scene(title="Test Scene", galleries=[], performers=[], tags=[])
        performer = Performer(name="Test Performer", scenes=[])

        # Set performer on scene
        scene.performers = [performer]

        # Verify inverse
        assert scene in performer.scenes


class TestSingleObjectRelationshipSync:
    """Test relationship auto-sync for many-to-one relationships."""

    def test_scene_studio_sync(self):
        """Test that setting scene.studio would sync inverse if Studio had scenes field."""
        from stash_graphql_client.types import Scene, Studio

        # Note: Studio doesn't have a direct 'scenes' field, so this won't sync
        # This test documents the current behavior
        scene = Scene(title="Test Scene", galleries=[], performers=[], tags=[])
        studio = Studio(name="Test Studio")

        # Set studio on scene
        scene.studio = studio

        # Studio.scenes doesn't exist (uses filter queries instead)
        # So no inverse sync occurs - this is expected
        assert not hasattr(studio, "scenes") or studio.scenes is studio.__dict__.get(
            "scenes", None
        )


class TestInverseSyncEdgeCases:
    """Test edge cases in inverse relationship syncing."""

    def test_sync_with_non_relationship_field(self):
        """Test that setting non-relationship fields doesn't crash.

        This covers line 490: early return when field_name not in __relationships__.
        """
        from stash_graphql_client.types import Tag

        tag = Tag(name="Test Tag", parents=[], children=[])

        # Set a non-relationship field - should not crash
        tag.description = "This is not a relationship field"

        # Verify the field was set
        assert tag.description == "This is not a relationship field"

    def test_sync_with_mixed_list_types(self):
        """Test that list with non-StashObject items skips those items.

        This covers line 505: continue when isinstance(related_obj, StashObject) is False.
        """
        from stash_graphql_client.types import Tag

        # Create tags with explicit parents/children to enable inverse sync
        child = Tag(id="child-1", name="Child", parents=[], children=[])

        # Create a mixed list with StashObject and non-StashObject items
        mixed_list = [
            child,  # Valid StashObject
            "not a tag",  # String - should be skipped at line 505
            123,  # Int - should be skipped at line 505
        ]

        tag_with_mixed = Tag(id="mixed-1", name="Mixed", parents=[], children=[])

        # Manually call _sync_inverse_relationship (singular!) to test line 505
        tag_with_mixed._sync_inverse_relationship("children", mixed_list)

        # Child should have tag_with_mixed as parent (inverse synced for valid object)
        # String and int should have been skipped (line 505 continue)
        assert tag_with_mixed in child.parents

    def test_sync_single_object_relationship(self):
        """Test syncing single object relationships (not lists).

        This covers lines 509-510: elif branch for single object relationships.
        """
        from stash_graphql_client.types import Gallery, Scene
        from stash_graphql_client.types.base import RelationshipMetadata

        # We need to test a single-object relationship with inverse metadata
        # Scene.studio has is_list=False but inverse_query_field=None
        # So let's create a custom scenario by directly manipulating metadata

        # Create mock Gallery with scenes list
        gallery = Gallery(id="gal-1", title="Gallery", scenes=[])

        # Create Scene and manually trigger single-object sync
        scene = Scene(id="scene-1", title="Scene", galleries=[], performers=[], tags=[])

        # Temporarily modify Scene's relationship metadata to treat galleries as single-object
        # Save original metadata
        original_metadata = scene.__relationships__.get("galleries")

        try:
            # Create single-object metadata
            single_obj_metadata = RelationshipMetadata(
                target_field="gallery_ids",
                is_list=False,  # Make it single-object!
                query_field="galleries",
                inverse_type="Gallery",
                inverse_query_field="scenes",
                query_strategy="direct_field",
            )

            # Temporarily replace metadata
            scene.__relationships__["galleries"] = single_obj_metadata

            # Manually call _sync_inverse_relationship with a single object (not list)
            scene._sync_inverse_relationship("galleries", gallery)

            # This should trigger lines 509-510 (elif branch for single objects)
            # Gallery.scenes should now contain scene
            assert scene in gallery.scenes

        finally:
            # Restore original metadata
            if original_metadata:
                scene.__relationships__["galleries"] = original_metadata

    def test_add_to_inverse_single_object_field(self):
        """Test _add_to_inverse when inverse field is a single object (not list).

        This covers line 533: setting single object inverse field.
        """
        from stash_graphql_client.types import Scene

        # Create scenes with IDs
        scene1 = Scene.model_construct(
            id="scene-1", title="Scene 1", galleries=[], performers=[], tags=[]
        )
        scene2 = Scene.model_construct(
            id="scene-2", title="Scene 2", galleries=[], performers=[], tags=[]
        )

        # Manually set scene1.studio to a non-list value (simulating single-object inverse)
        # First, use object.__setattr__ to set studio to a non-list value on scene2
        object.__setattr__(scene2, "studio", None)  # Start with None (not UNSET)

        # Now manually call _add_to_inverse to set scene2.studio = scene1
        # This should trigger line 533 (the else branch for single object fields)
        scene1._add_to_inverse(scene2, "studio")

        # Verify that scene2.studio was set to scene1
        assert scene2.studio == scene1

    def test_sync_with_unset_value(self):
        """Test that UNSET values trigger early return.

        This covers line 490: early return when isinstance(new_value, UnsetType).
        """
        from stash_graphql_client.types import Tag
        from stash_graphql_client.types.unset import UNSET

        parent = Tag(name="Parent", parents=[], children=[])

        # Set a field to UNSET explicitly - should trigger early return
        parent.parents = UNSET  # type: ignore[assignment]

        # Should not crash, UNSET is preserved
        from stash_graphql_client.types.unset import UnsetType

        assert isinstance(parent.parents, UnsetType)

    def test_sync_single_object_set_to_none(self):
        """Test that setting single-object relationship to None skips inverse sync.

        This covers line 509->exit: when new_value is None for single-object relationship.
        """
        from stash_graphql_client.types import Gallery, Scene
        from stash_graphql_client.types.base import RelationshipMetadata

        # Create Gallery with scenes list
        gallery = Gallery(id="gal-1", title="Gallery", scenes=[])

        # Create Scene with a single-object relationship metadata
        scene = Scene(id="scene-1", title="Scene", galleries=[], performers=[], tags=[])

        # Save original metadata
        original_metadata = scene.__relationships__.get("galleries")

        try:
            # Create single-object metadata (is_list=False)
            single_obj_metadata = RelationshipMetadata(
                target_field="gallery_ids",
                is_list=False,  # Single object!
                query_field="galleries",
                inverse_type="Gallery",
                inverse_query_field="scenes",
                query_strategy="direct_field",
            )

            # Replace metadata temporarily
            scene.__relationships__["galleries"] = single_obj_metadata

            # Call _sync_inverse_relationship with None (clearing the relationship)
            # This should hit line 509->exit (elif condition is False because new_value is None)
            scene._sync_inverse_relationship("galleries", None)

            # Gallery.scenes should remain empty (no inverse sync happened)
            assert scene not in gallery.scenes

        finally:
            # Restore original metadata
            if original_metadata:
                scene.__relationships__["galleries"] = original_metadata

    def test_sync_with_non_relationship_metadata_mapping(self):
        """Test that non-RelationshipMetadata mappings trigger early return.

        This covers line 497: early return when mapping is not RelationshipMetadata.
        This tests the defensive code that handles legacy tuple format or invalid mappings.
        """
        from stash_graphql_client.types import Tag

        # Create a tag with valid relationships
        tag = Tag(name="Test Tag", parents=[], children=[])

        # Save original relationships
        original_relationships = tag.__relationships__.copy()

        try:
            # Replace a relationship with a non-RelationshipMetadata object (e.g., tuple or string)
            # This simulates legacy code or an invalid relationship definition
            tag.__relationships__["parents"] = (
                "parent_ids",
                True,
                None,
            )  # Legacy tuple format

            # Create another tag to attempt sync with
            parent = Tag(name="Parent Tag", parents=[], children=[])

            # Attempt to sync - this should trigger line 497 early return (no crash)
            tag._sync_inverse_relationship("parents", [parent])

            # No inverse sync should occur because the mapping is not RelationshipMetadata
            # parent.children should still be empty
            assert len(parent.children) == 0

        finally:
            # Restore original relationships
            tag.__relationships__.clear()
            tag.__relationships__.update(original_relationships)
