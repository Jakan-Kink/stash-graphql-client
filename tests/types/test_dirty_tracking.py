"""Tests for StashObject dirty tracking functionality.

Tests the snapshot system that detects changes to tracked fields,
including proper handling of mutable list fields.
"""

from stash_graphql_client.types import Gallery, Performer, Scene, Studio, Tag
from stash_graphql_client.types.unset import UNSET


class TestDirtyTrackingBasics:
    """Test basic dirty tracking functionality."""

    def test_new_object_not_dirty(self):
        """Test newly created object is not dirty."""
        performer = Performer(id="1", name="Test")
        assert not performer.is_dirty()

    def test_field_change_makes_dirty(self):
        """Test changing a tracked field marks object as dirty."""
        performer = Performer(id="1", name="Test")
        performer.name = "Changed"
        assert performer.is_dirty()

    def test_non_tracked_field_change_not_dirty(self):
        """Test changing a non-tracked field doesn't mark as dirty."""
        performer = Performer(id="1", name="Test", birthdate="2000-01-01")
        # created_at is not in __tracked_fields__
        performer.created_at = "2024-01-01T00:00:00Z"
        assert not performer.is_dirty()

    def test_mark_clean_clears_dirty_state(self):
        """Test mark_clean() clears dirty state."""
        performer = Performer(id="1", name="Test")
        performer.name = "Changed"
        assert performer.is_dirty()

        performer.mark_clean()
        assert not performer.is_dirty()

    def test_mark_dirty_forces_dirty_state(self):
        """Test mark_dirty() forces dirty state even without changes."""
        performer = Performer(id="1", name="Test")
        assert not performer.is_dirty()

        performer.mark_dirty()
        assert performer.is_dirty()

    def test_get_changed_fields_single_field(self):
        """Test get_changed_fields() returns changed fields."""
        performer = Performer(id="1", name="Test")
        performer.name = "Changed"

        changed = performer.get_changed_fields()
        assert "name" in changed
        assert changed["name"] == "Changed"

    def test_get_changed_fields_multiple_fields(self):
        """Test get_changed_fields() with multiple changes."""
        performer = Performer(id="1", name="Test", disambiguation="Original")
        performer.name = "Changed"
        performer.disambiguation = "New"

        changed = performer.get_changed_fields()
        assert len(changed) == 2
        assert changed["name"] == "Changed"
        assert changed["disambiguation"] == "New"


class TestListDirtyTracking:
    """Test dirty tracking with mutable list fields."""

    def test_list_append_detected(self):
        """Test list.append() is detected as dirty."""
        performer = Performer(id="1", name="Test", urls=["url1"])
        assert not performer.is_dirty()

        performer.urls.append("url2")
        assert performer.is_dirty()
        assert performer.urls == ["url1", "url2"]

    def test_list_extend_detected(self):
        """Test list.extend() is detected as dirty."""
        performer = Performer(id="1", name="Test", urls=["url1"])
        assert not performer.is_dirty()

        performer.urls.extend(["url2", "url3"])
        assert performer.is_dirty()
        assert performer.urls == ["url1", "url2", "url3"]

    def test_list_remove_detected(self):
        """Test list.remove() is detected as dirty."""
        performer = Performer(id="1", name="Test", urls=["url1", "url2"])
        assert not performer.is_dirty()

        performer.urls.remove("url1")
        assert performer.is_dirty()
        assert performer.urls == ["url2"]

    def test_list_pop_detected(self):
        """Test list.pop() is detected as dirty."""
        performer = Performer(id="1", name="Test", urls=["url1", "url2"])
        assert not performer.is_dirty()

        performer.urls.pop()
        assert performer.is_dirty()
        assert performer.urls == ["url1"]

    def test_list_clear_detected(self):
        """Test list.clear() is detected as dirty."""
        performer = Performer(id="1", name="Test", urls=["url1", "url2"])
        assert not performer.is_dirty()

        performer.urls.clear()
        assert performer.is_dirty()
        assert performer.urls == []

    def test_list_item_assignment_detected(self):
        """Test list[index] = value is detected as dirty."""
        performer = Performer(id="1", name="Test", urls=["url1", "url2"])
        assert not performer.is_dirty()

        performer.urls[0] = "new_url"
        assert performer.is_dirty()
        assert performer.urls == ["new_url", "url2"]

    def test_list_replacement_detected(self):
        """Test replacing entire list is detected as dirty."""
        performer = Performer(id="1", name="Test", urls=["url1"])
        assert not performer.is_dirty()

        performer.urls = ["new_url"]
        assert performer.is_dirty()
        assert performer.urls == ["new_url"]

    def test_list_mark_clean_resets_snapshot(self):
        """Test mark_clean() creates new snapshot of modified list."""
        performer = Performer(id="1", name="Test", urls=["url1"])
        performer.urls.append("url2")
        assert performer.is_dirty()

        performer.mark_clean()
        assert not performer.is_dirty()

        # Further modifications should be detected
        performer.urls.append("url3")
        assert performer.is_dirty()

    def test_empty_list_not_dirty(self):
        """Test empty list doesn't cause false dirty detection."""
        performer = Performer(id="1", name="Test", urls=[])
        assert not performer.is_dirty()

    def test_none_list_to_empty_list_detected(self):
        """Test changing from empty list to having items is detected."""
        performer = Performer(id="1", name="Test", urls=[])
        performer.urls = ["url1"]
        assert performer.is_dirty()

    def test_unset_list_not_dirty(self):
        """Test UNSET list value doesn't cause false dirty detection."""
        performer = Performer(id="1", name="Test")
        # urls defaults to UNSET
        assert performer.urls is UNSET
        assert not performer.is_dirty()


class TestMultipleListFieldTypes:
    """Test dirty tracking works across different entity types with lists."""

    def test_studio_urls_list_modification(self):
        """Test Studio.urls list modification detected."""
        studio = Studio(id="1", name="Test Studio", urls=["url1"])
        studio.urls.append("url2")
        assert studio.is_dirty()

    def test_studio_aliases_list_modification(self):
        """Test Studio.aliases list modification detected."""
        studio = Studio(id="1", name="Test Studio", aliases=["alias1"])
        studio.aliases.append("alias2")
        assert studio.is_dirty()

    def test_tag_aliases_list_modification(self):
        """Test Tag.aliases list modification detected."""
        tag = Tag(id="1", name="Test Tag", aliases=["alias1"])
        tag.aliases.append("alias2")
        assert tag.is_dirty()

    def test_performer_alias_list_modification(self):
        """Test Performer.alias_list modification detected."""
        performer = Performer(id="1", name="Test", alias_list=["alias1"])
        performer.alias_list.append("alias2")
        assert performer.is_dirty()


class TestRelationshipListDirtyTracking:
    """Test dirty tracking with relationship lists (StashObject lists)."""

    def test_performer_list_append_detected(self):
        """Test appending to performer list is detected."""
        scene = Scene(id="1", title="Test")
        performer1 = Performer(id="1", name="Performer 1")
        performer2 = Performer(id="2", name="Performer 2")

        scene.performers = [performer1]
        scene.mark_clean()
        assert not scene.is_dirty()

        scene.performers.append(performer2)
        assert scene.is_dirty()

    def test_tag_list_remove_detected(self):
        """Test removing from tag list is detected."""
        performer = Performer(id="1", name="Test")
        tag1 = Tag(id="1", name="Tag 1")
        tag2 = Tag(id="2", name="Tag 2")

        performer.tags = [tag1, tag2]
        performer.mark_clean()
        assert not performer.is_dirty()

        performer.tags.remove(tag1)
        assert performer.is_dirty()

    def test_relationship_list_replacement_detected(self):
        """Test replacing entire relationship list is detected."""
        performer = Performer(id="1", name="Test")
        tag1 = Tag(id="1", name="Tag 1")
        tag2 = Tag(id="2", name="Tag 2")

        performer.tags = [tag1]
        performer.mark_clean()
        assert not performer.is_dirty()

        performer.tags = [tag2]
        assert performer.is_dirty()


class TestEdgeCases:
    """Test edge cases in dirty tracking."""

    def test_setting_same_value_not_dirty(self):
        """Test setting field to same value doesn't mark as dirty."""
        performer = Performer(id="1", name="Test")
        performer.name = "Test"
        # Strings are compared by value in Python, so same value = not dirty
        assert not performer.is_dirty()

    def test_list_same_content_different_object_not_dirty(self):
        """Test replacing list with same content isn't detected (value equality)."""
        performer = Performer(id="1", name="Test", urls=["url1"])
        performer.urls = ["url1"]  # New list with same content
        # Lists are compared by value (__eq__), not identity
        assert not performer.is_dirty()

    def test_multiple_changes_then_mark_clean(self):
        """Test multiple changes then mark_clean()."""
        performer = Performer(id="1", name="Test", urls=["url1"], alias_list=["a1"])
        performer.name = "Changed"
        performer.urls.append("url2")
        performer.alias_list.append("a2")

        assert performer.is_dirty()
        changed = performer.get_changed_fields()
        assert len(changed) == 3

        performer.mark_clean()
        assert not performer.is_dirty()
        assert performer.get_changed_fields() == {}


class TestSelectiveSnapshotUpdate:
    """Test _update_snapshot_for_fields() for identity map merge and populate().

    When a StashObject stub is later populated with server data (via identity map
    merge or store.populate()), the snapshot should be updated for the merged fields
    so they don't appear dirty. User modifications to fields NOT in the merge
    should be preserved as dirty.
    """

    def test_stub_then_full_merge_is_clean(self):
        """After merging full data into a stub, object should not be dirty."""
        # Simulate a stub with only id + title (like from a nested Performer response)
        scene = Scene(id="1", title="Original")
        assert not scene.is_dirty()

        # Simulate identity map merge: set fields as the validator would
        scene.organized = False
        scene.rating100 = 85
        scene.details = "Some details"

        # Before selective snapshot update — these fields are dirty
        assert scene.is_dirty()

        # Simulate what _identity_map_validator now does after merge
        merged_fields = {"organized", "rating100", "details"}
        scene._update_snapshot_for_fields(merged_fields)

        # Merged fields should now be clean
        assert not scene.is_dirty()
        assert scene.get_changed_fields() == {}

    def test_user_modification_survives_partial_merge(self):
        """User modifications to fields NOT in the merge should stay dirty."""
        performer = Performer(id="1", name="Original", disambiguation="Original D")

        # User modifies title
        performer.name = "User Modified"
        assert performer.is_dirty()
        assert "name" in performer.get_changed_fields()

        # Simulate a partial merge that includes disambiguation but NOT name
        performer.disambiguation = "Server Value"
        merged_fields = {"disambiguation"}
        performer._update_snapshot_for_fields(merged_fields)

        # name should STILL be dirty (user's change preserved)
        assert performer.is_dirty()
        changed = performer.get_changed_fields()
        assert "name" in changed
        assert changed["name"] == "User Modified"
        # disambiguation should be clean (snapshotted by selective update)
        assert "disambiguation" not in changed

    def test_selective_update_only_touches_tracked_fields(self):
        """_update_snapshot_for_fields should only update tracked fields."""
        performer = Performer(id="1", name="Test")

        # created_at is NOT in __tracked_fields__
        assert "created_at" not in performer.__tracked_fields__
        # name IS in __tracked_fields__
        assert "name" in performer.__tracked_fields__

        performer.name = "Changed"
        performer._update_snapshot_for_fields({"name", "created_at"})

        # name should be clean now
        assert not performer.is_dirty()

    def test_user_modification_then_same_field_merge(self):
        """If user modifies a field and merge overwrites it, it should be clean."""
        performer = Performer(id="1", name="Original")

        # User modifies
        performer.name = "User Value"
        assert performer.is_dirty()

        # Server merge overwrites the same field
        performer.name = "Server Value"
        performer._update_snapshot_for_fields({"name"})

        # Should be clean — server value is now the baseline
        assert not performer.is_dirty()
        assert performer.name == "Server Value"

    def test_empty_field_set_is_noop(self):
        """Calling with empty set shouldn't change anything."""
        performer = Performer(id="1", name="Original")
        performer.name = "Changed"
        assert performer.is_dirty()

        performer._update_snapshot_for_fields(set())
        assert performer.is_dirty()

    def test_unset_to_value_merge_is_clean(self):
        """Merging from UNSET to a real value should be clean after snapshot update."""
        # Start with a stub where most fields are UNSET
        scene = Scene(id="1")
        assert scene.title is UNSET
        assert not scene.is_dirty()

        # Simulate merge: set title from UNSET to actual value
        scene.title = "From Server"
        # This would normally be dirty (UNSET → "From Server")
        assert scene.is_dirty()

        # Selective snapshot update
        scene._update_snapshot_for_fields({"title"})
        assert not scene.is_dirty()


class TestPrivateAttrSurvival:
    """Regression tests: private attrs must survive validate_assignment __dict__ rebuilds.

    Pydantic v2's validate_assignment=True replaces __dict__ on every field assignment.
    Private attributes stored via object.__setattr__() (in __dict__) are silently lost.
    Using PrivateAttr (stored in __pydantic_private__) prevents this.
    """

    def test_snapshot_survives_identity_map_merge_then_assignment(self):
        """Regression: _snapshot must survive validate_assignment __dict__ rebuild.

        When a Gallery goes through the identity map cache-hit path (fields set
        via setattr), then mark_clean(), then field assignment — the snapshot
        must retain the mark_clean values, not revert to model_post_init defaults.
        """
        gallery = Gallery(id="123")
        gallery.title = "Real Title"
        gallery.organized = False
        gallery.photographer = ""
        gallery.urls = ["https://example.com"]
        gallery.performers = []
        gallery.tags = []
        gallery.files = []
        gallery.scenes = []

        # mark_clean should capture real values
        gallery.mark_clean()
        assert not gallery.is_dirty(), "Gallery should be clean after mark_clean"

        # Assign one field — triggers validate_assignment __dict__ rebuild
        gallery.title = "Updated Title"

        # Only title should be dirty — NOT organized, files, scenes, etc.
        changed = gallery.get_changed_fields()
        assert set(changed.keys()) == {"title"}, (
            f"Only 'title' should be dirty, but got: {set(changed.keys())}"
        )
        assert changed["title"] == "Updated Title"

    def test_is_new_survives_field_assignment(self):
        """Regression: _is_new must survive validate_assignment __dict__ rebuild."""
        gallery = Gallery()  # No id → auto UUID → _is_new=True
        assert gallery.is_new()

        gallery.title = "Something"  # Triggers validate_assignment
        assert gallery.is_new(), "_is_new was lost after field assignment"

    def test_received_fields_survives_field_assignment(self):
        """Regression: _received_fields must survive validate_assignment __dict__ rebuild."""
        gallery = Gallery(id="123")
        gallery._received_fields = {"id", "title", "organized"}

        gallery.title = "New"  # Triggers validate_assignment
        assert gallery._received_fields == {"id", "title", "organized"}, (
            "_received_fields was lost after field assignment"
        )

    def test_snapshot_survives_multiple_assignments(self):
        """_snapshot must survive across multiple consecutive field assignments."""
        performer = Performer(id="1", name="Original", disambiguation="Test")
        performer.mark_clean()

        performer.name = "Changed"
        performer.disambiguation = "Also Changed"

        changed = performer.get_changed_fields()
        assert set(changed.keys()) == {"name", "disambiguation"}
        assert changed["name"] == "Changed"
        assert changed["disambiguation"] == "Also Changed"

    def test_is_new_false_survives_field_assignment(self):
        """_is_new=False must also survive (not just True)."""
        performer = Performer(id="1", name="Test")
        assert not performer.is_new()

        performer.name = "Changed"  # Triggers validate_assignment
        assert not performer.is_new(), (
            "_is_new changed from False after field assignment"
        )
