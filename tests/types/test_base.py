"""Tests for stash_graphql_client.types.base module.

Tests the StashObject base class methods including:
- Initialization and model_post_init
- Dirty tracking (is_dirty, mark_clean, mark_dirty, get_changed_fields)
- Hash and equality
- Field name resolution

Uses real Pydantic types (Performer, Studio, Tag) rather than mocks.
"""

from datetime import UTC, datetime

import pytest

from stash_graphql_client.types import Performer, Studio, Tag
from stash_graphql_client.types.base import (
    BulkUpdateIds,
    BulkUpdateStrings,
    StashObject,
)
from stash_graphql_client.types.enums import BulkUpdateIdMode


class TestStashObjectInitialization:
    """Tests for StashObject initialization."""

    @pytest.mark.unit
    def test_basic_initialization(self) -> None:
        """Test basic StashObject initialization with required fields."""
        performer = Performer(id="123", name="Test Performer")

        assert performer.id == "123"
        assert performer.name == "Test Performer"
        assert performer.created_at is None
        assert performer.updated_at is None

    @pytest.mark.unit
    def test_initialization_with_timestamps(self) -> None:
        """Test initialization with timestamp fields."""
        now = datetime.now(UTC)
        performer = Performer(
            id="123",
            name="Test Performer",
            created_at=now,
            updated_at=now,
        )

        assert performer.created_at == now
        assert performer.updated_at == now

    @pytest.mark.unit
    def test_initialization_with_all_fields(self) -> None:
        """Test initialization with multiple optional fields."""
        studio = Studio(
            id="456",
            name="Test Studio",
            details="A test studio description",
            urls=["https://example.com"],
            aliases=["Alias 1", "Alias 2"],
        )

        assert studio.id == "456"
        assert studio.name == "Test Studio"
        assert studio.details == "A test studio description"
        assert studio.urls == ["https://example.com"]
        assert studio.aliases == ["Alias 1", "Alias 2"]

    @pytest.mark.unit
    def test_model_post_init_creates_snapshot(self) -> None:
        """Test that model_post_init creates a snapshot for dirty tracking."""
        performer = Performer(id="123", name="Test Performer")

        # Snapshot should exist after init
        assert hasattr(performer, "_snapshot")
        assert performer._snapshot is not None
        assert performer._snapshot["id"] == "123"
        assert performer._snapshot["name"] == "Test Performer"


class TestDirtyTracking:
    """Tests for dirty tracking functionality."""

    @pytest.mark.unit
    def test_initially_clean(self) -> None:
        """Test that objects are initially clean."""
        performer = Performer(id="123", name="Test Performer")
        assert not performer.is_dirty()

    @pytest.mark.unit
    def test_is_dirty_after_change(self) -> None:
        """Test is_dirty returns True after field change."""
        performer = Performer(id="123", name="Test Performer")
        performer.name = "Changed Name"

        assert performer.is_dirty()

    @pytest.mark.unit
    def test_is_dirty_with_list_change(self) -> None:
        """Test is_dirty detects list changes."""
        studio = Studio(id="123", name="Test Studio", aliases=[])
        studio.aliases = ["New Alias"]

        assert studio.is_dirty()

    @pytest.mark.unit
    def test_mark_clean_resets_dirty_state(self) -> None:
        """Test mark_clean resets dirty state."""
        performer = Performer(id="123", name="Test Performer")
        performer.name = "Changed Name"

        assert performer.is_dirty()

        performer.mark_clean()

        assert not performer.is_dirty()
        # Snapshot should be updated
        assert performer._snapshot["name"] == "Changed Name"

    @pytest.mark.unit
    def test_mark_dirty_makes_object_dirty(self) -> None:
        """Test mark_dirty makes object dirty."""
        performer = Performer(id="123", name="Test Performer")

        assert not performer.is_dirty()

        performer.mark_dirty()

        assert performer.is_dirty()

    @pytest.mark.unit
    def test_get_changed_fields_empty_when_clean(self) -> None:
        """Test get_changed_fields returns empty dict when clean."""
        performer = Performer(id="123", name="Test Performer")

        changed = performer.get_changed_fields()

        assert changed == {}

    @pytest.mark.unit
    def test_get_changed_fields_returns_changes(self) -> None:
        """Test get_changed_fields returns only changed tracked fields."""
        # Create a performer with tracked fields
        performer = Performer(id="123", name="Test Performer", details="Original")
        performer.name = "Changed Name"

        changed = performer.get_changed_fields()

        # Only tracked fields that changed should be included
        assert "name" in changed
        assert changed["name"] == "Changed Name"
        # id is not tracked, so shouldn't be in changed fields

    @pytest.mark.unit
    def test_get_changed_fields_multiple_changes(self) -> None:
        """Test get_changed_fields with multiple field changes."""
        studio = Studio(
            id="123",
            name="Original Name",
            details="Original Details",
            urls=["http://original.com"],
        )

        studio.name = "New Name"
        studio.details = "New Details"

        changed = studio.get_changed_fields()

        assert "name" in changed
        assert "details" in changed


class TestHashAndEquality:
    """Tests for __hash__ and __eq__ methods."""

    @pytest.mark.unit
    def test_hash_based_on_type_and_id(self) -> None:
        """Test that hash is based on type name and id."""
        performer1 = Performer(id="123", name="Performer 1")
        performer2 = Performer(id="123", name="Performer 2")  # Same ID, different name

        # Same type and ID should have same hash
        assert hash(performer1) == hash(performer2)

    @pytest.mark.unit
    def test_hash_different_ids(self) -> None:
        """Test that different IDs produce different hashes."""
        performer1 = Performer(id="123", name="Test")
        performer2 = Performer(id="456", name="Test")

        assert hash(performer1) != hash(performer2)

    @pytest.mark.unit
    def test_hash_different_types(self) -> None:
        """Test that different types produce different hashes."""
        performer = Performer(id="123", name="Test")
        studio = Studio(id="123", name="Test")

        # Different types, same ID should have different hash
        assert hash(performer) != hash(studio)

    @pytest.mark.unit
    def test_equality_same_type_and_id(self) -> None:
        """Test equality for objects with same type and ID."""
        performer1 = Performer(id="123", name="Performer 1")
        performer2 = Performer(id="123", name="Performer 2")

        assert performer1 == performer2

    @pytest.mark.unit
    def test_equality_different_ids(self) -> None:
        """Test inequality for objects with different IDs."""
        performer1 = Performer(id="123", name="Test")
        performer2 = Performer(id="456", name="Test")

        assert performer1 != performer2

    @pytest.mark.unit
    def test_equality_different_types(self) -> None:
        """Test inequality for different types with same ID."""
        performer = Performer(id="123", name="Test")
        studio = Studio(id="123", name="Test")

        assert performer != studio

    @pytest.mark.unit
    def test_equality_with_non_stash_object(self) -> None:
        """Test equality returns NotImplemented for non-StashObject."""
        performer = Performer(id="123", name="Test")

        result = performer.__eq__("not a stash object")

        assert result is NotImplemented

    @pytest.mark.unit
    def test_hashable_in_set(self) -> None:
        """Test that StashObjects can be used in sets."""
        performer1 = Performer(id="123", name="Test 1")
        performer2 = Performer(id="123", name="Test 2")  # Same ID
        performer3 = Performer(id="456", name="Test 3")

        # Set should deduplicate by ID
        performer_set = {performer1, performer2, performer3}

        assert len(performer_set) == 2

    @pytest.mark.unit
    def test_hashable_in_dict(self) -> None:
        """Test that StashObjects can be used as dict keys."""
        performer = Performer(id="123", name="Test")

        d = {performer: "value"}

        assert d[performer] == "value"


class TestGetFieldNames:
    """Tests for _get_field_names class method."""

    @pytest.mark.unit
    def test_get_field_names_returns_set(self) -> None:
        """Test _get_field_names returns a set."""
        field_names = Performer._get_field_names()

        assert isinstance(field_names, set)

    @pytest.mark.unit
    def test_get_field_names_includes_id(self) -> None:
        """Test _get_field_names always includes 'id'."""
        field_names = Performer._get_field_names()

        assert "id" in field_names

    @pytest.mark.unit
    def test_get_field_names_includes_model_fields(self) -> None:
        """Test _get_field_names includes Pydantic model fields."""
        field_names = Performer._get_field_names()

        # Should include common Performer fields
        assert "name" in field_names
        assert "id" in field_names


class TestBulkUpdateTypes:
    """Tests for BulkUpdateIds and BulkUpdateStrings."""

    @pytest.mark.unit
    def test_bulk_update_ids_initialization(self) -> None:
        """Test BulkUpdateIds initialization."""
        bulk = BulkUpdateIds(
            ids=["1", "2", "3"],
            mode=BulkUpdateIdMode.ADD,
        )

        assert bulk.ids == ["1", "2", "3"]
        assert bulk.mode == BulkUpdateIdMode.ADD

    @pytest.mark.unit
    def test_bulk_update_strings_initialization(self) -> None:
        """Test BulkUpdateStrings initialization."""
        bulk = BulkUpdateStrings(
            values=["value1", "value2"],
            mode=BulkUpdateIdMode.SET,
        )

        assert bulk.values == ["value1", "value2"]
        assert bulk.mode == BulkUpdateIdMode.SET

    @pytest.mark.unit
    def test_bulk_update_ids_remove_mode(self) -> None:
        """Test BulkUpdateIds with REMOVE mode."""
        bulk = BulkUpdateIds(
            ids=["1"],
            mode=BulkUpdateIdMode.REMOVE,
        )

        assert bulk.mode == BulkUpdateIdMode.REMOVE


class TestTypeNameAndClassVars:
    """Tests for class variables like __type_name__."""

    @pytest.mark.unit
    def test_performer_type_name(self) -> None:
        """Test Performer has correct __type_name__."""
        assert Performer.__type_name__ == "Performer"

    @pytest.mark.unit
    def test_studio_type_name(self) -> None:
        """Test Studio has correct __type_name__."""
        assert Studio.__type_name__ == "Studio"

    @pytest.mark.unit
    def test_tag_type_name(self) -> None:
        """Test Tag has correct __type_name__."""
        assert Tag.__type_name__ == "Tag"

    @pytest.mark.unit
    def test_performer_has_tracked_fields(self) -> None:
        """Test Performer has __tracked_fields__ defined."""
        assert hasattr(Performer, "__tracked_fields__")
        assert isinstance(Performer.__tracked_fields__, set)

    @pytest.mark.unit
    def test_performer_has_update_input_type(self) -> None:
        """Test Performer has __update_input_type__ defined."""
        assert hasattr(Performer, "__update_input_type__")
        assert Performer.__update_input_type__ is not None


class TestStashObjectIsSubclass:
    """Tests verifying StashObject inheritance."""

    @pytest.mark.unit
    def test_performer_is_stash_object(self) -> None:
        """Test Performer is a StashObject."""
        assert issubclass(Performer, StashObject)

    @pytest.mark.unit
    def test_studio_is_stash_object(self) -> None:
        """Test Studio is a StashObject."""
        assert issubclass(Studio, StashObject)

    @pytest.mark.unit
    def test_tag_is_stash_object(self) -> None:
        """Test Tag is a StashObject."""
        assert issubclass(Tag, StashObject)

    @pytest.mark.unit
    def test_stash_object_is_base_model(self) -> None:
        """Test StashObject inherits from Pydantic BaseModel."""
        from pydantic import BaseModel

        assert issubclass(StashObject, BaseModel)
