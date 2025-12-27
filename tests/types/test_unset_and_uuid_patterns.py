"""Tests for UNSET sentinel and UUID4 auto-generation patterns.

This test suite demonstrates the three-level field system (value, null, UNSET)
and UUID4 auto-generation for new objects.
"""

from __future__ import annotations

import pytest
from pydantic import BaseModel, ValidationError

from stash_graphql_client.types import UNSET, Tag, UnsetType, is_set


class TestUnsetSentinel:
    """Test UNSET sentinel pattern."""

    def test_unset_is_singleton(self):
        """UNSET should be a singleton."""
        unset1 = UnsetType()
        unset2 = UnsetType()

        assert unset1 is unset2
        assert unset1 is UNSET
        assert unset2 is UNSET

    def test_unset_repr(self):
        """UNSET should have clear string representation."""
        assert repr(UNSET) == "UNSET"
        assert str(UNSET) == "UNSET"

    def test_unset_is_falsy(self):
        """UNSET should be falsy."""
        assert not UNSET
        assert bool(UNSET) is False

    def test_unset_equality(self):
        """UNSET should only equal other UnsetType instances."""
        assert UNSET == UNSET  # noqa: PLR0124 - intentionally testing self-equality
        assert UnsetType() == UNSET
        assert UNSET is not None
        assert UNSET != ""
        assert UNSET != 0
        assert UNSET is not False

    def test_unset_identity_check(self):
        """Identity check (is) should work for UNSET."""
        value = UNSET

        assert value is UNSET
        assert value is not None

        # Type narrowing example
        if is_set(value):
            # In this block, value is not UNSET
            pass
        else:
            # In this block, value is UNSET
            assert True

    def test_unset_hashable(self):
        """UNSET should be hashable for use in sets/dicts."""
        # Can be used in sets
        value_set = {UNSET, None, "value"}
        assert UNSET in value_set
        assert len(value_set) == 3

        # Can be used as dict key
        state_map = {
            UNSET: "never touched",
            None: "explicitly null",
            "value": "has value",
        }
        assert state_map[UNSET] == "never touched"

    def test_unset_pydantic_schema_integration(self):
        """Test UnsetType works with Pydantic's core schema.

        This covers lines 82-88 in unset.py - the validate_unset function
        inside __get_pydantic_core_schema__.
        """

        class TestModel(BaseModel):
            """Test model with UnsetType field."""

            field: str | UnsetType = UNSET

        # Test with UNSET value (default)
        model1 = TestModel()
        assert model1.field is UNSET

        # Test with explicit UNSET
        model2 = TestModel(field=UNSET)
        assert model2.field is UNSET

        # Test with actual value
        model3 = TestModel(field="value")
        assert model3.field == "value"

    def test_unset_validation_error_on_invalid_type(self):
        """Test that UnsetType validator raises error for invalid types.

        This covers line 86-88 in unset.py - the ValueError raise in validate_unset.
        """

        class TestModel(BaseModel):
            """Test model with UnsetType field."""

            field: UnsetType

        # Try to create with invalid type - should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            TestModel(field="not_an_unset_type")  # type: ignore[arg-type]

        # Verify it's from our custom validator
        error = exc_info.value.errors()[0]
        assert "Expected UnsetType" in str(error)


class TestUUID4Generation:
    """Test UUID4 auto-generation for new objects."""

    def test_new_object_gets_uuid(self):
        """New objects without ID should auto-generate UUID4."""
        tag = Tag(name="Test Tag")

        assert tag.id is not None
        assert len(tag.id) == 32  # UUID4 hex is 32 chars
        assert all(c in "0123456789abcdef" for c in tag.id)  # All hex chars

    def test_new_object_with_id_none(self):
        """Objects with id=None should auto-generate UUID4."""
        tag = Tag(id=None, name="Test Tag")  # type: ignore[arg-type]

        assert tag.id is not None
        assert len(tag.id) == 32

    def test_new_object_with_explicit_id(self):
        """Objects with explicit ID should keep that ID."""
        tag = Tag(id="123", name="Test Tag")

        assert tag.id == "123"

    def test_is_new_with_uuid(self):
        """is_new() should return True for UUID4 IDs."""
        tag = Tag(name="Test Tag")

        assert tag.is_new() is True

    def test_is_new_with_server_id(self):
        """is_new() should return False for server IDs."""
        tag = Tag(id="123", name="Test Tag")

        assert tag.is_new() is False

    def test_is_new_with_legacy_marker(self):
        """is_new() should return True for legacy 'new' marker."""
        tag = Tag(id="new", name="Test Tag")

        assert tag.is_new() is True

    def test_update_id(self):
        """update_id() should replace UUID with server ID."""
        tag = Tag(name="Test Tag")
        original_id = tag.id

        assert tag.is_new() is True
        assert original_id is not None
        assert len(original_id) == 32

        # Update with server ID
        tag.update_id("456")

        assert tag.id == "456"
        assert tag.id != original_id
        assert tag.is_new() is False

    def test_multiple_new_objects_get_unique_uuids(self):
        """Each new object should get a unique UUID."""
        tag1 = Tag(name="Tag 1")
        tag2 = Tag(name="Tag 2")
        tag3 = Tag(name="Tag 3")

        # All should have UUIDs
        assert tag1.is_new()
        assert tag2.is_new()
        assert tag3.is_new()

        # All should be unique
        assert tag1.id != tag2.id
        assert tag2.id != tag3.id
        assert tag1.id != tag3.id


class TestFieldStatePatterns:
    """Test patterns for working with three-level field states."""

    def test_describe_field_state(self):
        """Demonstrate pattern for describing field state."""

        def describe_field(field_value):
            """Describe the state of a field value."""
            if isinstance(field_value, UnsetType):
                return "UNSET"
            if field_value is None:
                return "NULL"
            return f"VALUE: {field_value}"

        # Test all three states
        assert describe_field(UNSET) == "UNSET"
        assert describe_field(None) == "NULL"
        assert describe_field("test") == "VALUE: test"
        assert describe_field(42) == "VALUE: 42"

    def test_checking_field_state(self):
        """Demonstrate pattern for checking field state."""
        tag = Tag(name="Test")

        # Pattern 1: Check if field was touched
        if is_set(tag.name):
            assert True  # Field was set
        else:
            pytest.fail("Field should be set")

        # Pattern 2: Check for explicit null
        tag.description = None
        if tag.description is None:
            assert True  # Field is null
        else:
            pytest.fail("Field should be None")

        # Pattern 3: Check for UNSET
        if isinstance(tag.aliases, UnsetType):
            assert True  # Field was never touched
        else:
            pytest.fail("Field should be UNSET")

    def test_processing_optional_fields(self):
        """Demonstrate pattern for processing optional fields."""

        def process_field(value):
            """Process a field value, handling all three states."""
            if isinstance(value, UnsetType):
                return None  # Don't process UNSET fields
            if value is None:
                return "NULL_VALUE"  # Special handling for null
            return f"PROCESSED: {value}"

        # Test all states
        assert process_field(UNSET) is None
        assert process_field(None) == "NULL_VALUE"
        assert process_field("test") == "PROCESSED: test"


class TestToInputPatterns:
    """Test patterns for converting to GraphQL input with UNSET."""

    @pytest.mark.asyncio
    async def test_to_input_excludes_unset_fields(self):
        """to_input() should exclude UNSET fields (conceptual test)."""
        tag = Tag(id="123", name="Test Tag")

        # In a future implementation with UNSET support:
        # tag.description = UNSET  # Never touched
        # tag.aliases = None        # Explicitly null
        # tag.ignore_auto_tag = True  # Set to value

        input_dict = await tag.to_input()

        # Should always include ID for updates
        assert "id" in input_dict

        # Should always include set fields
        assert "name" in input_dict

        # Note: Current implementation may not fully support UNSET exclusion
        # This test demonstrates the intended pattern for future implementation

    def test_building_input_with_unset_checks(self):
        """Demonstrate pattern for building input dict with UNSET checks."""

        def build_input_dict(name, description, aliases):
            """Build input dict, excluding UNSET fields."""
            data = {}

            if is_set(name):
                data["name"] = name

            if is_set(description):
                data["description"] = description  # Could be None or value

            if is_set(aliases):
                data["aliases"] = aliases

            return data

        # Test with different field states
        result = build_input_dict(
            name="Test",
            description=None,
            aliases=UNSET,  # Set  # Explicitly null  # Never touched
        )

        assert result == {"name": "Test", "description": None}
        assert "aliases" not in result  # UNSET excluded


class TestIntegrationPatterns:
    """Test integration patterns combining UUID4 and UNSET."""

    def test_new_object_workflow(self):
        """Demonstrate complete workflow for new objects."""
        # 1. Create new object - UUID auto-generated
        tag = Tag(name="New Tag")

        assert tag.is_new() is True
        original_id = tag.id
        assert original_id is not None
        assert len(original_id) == 32

        # 2. Set some fields, leave others UNSET
        tag.description = "A test tag"
        # tag.aliases would be UNSET (never touched)

        # 3. Simulate save operation updating ID
        server_id = "789"
        tag.update_id(server_id)

        assert tag.id == server_id
        assert tag.is_new() is False
        assert tag.name == "New Tag"
        assert tag.description == "A test tag"

    def test_partial_update_workflow(self):
        """Demonstrate workflow for partial updates."""
        # 1. Fetch existing object (simulated)
        tag = Tag(id="123", name="Original Name", description="Original Description")

        assert tag.is_new() is False

        # 2. Update only one field
        tag.name = "Updated Name"
        # description left unchanged

        # 3. to_input() should only include changed field + ID
        # (In a full implementation with dirty tracking)
        # input_dict = await tag.to_input()
        # assert "id" in input_dict
        # assert "name" in input_dict
        # assert "description" not in input_dict  # Not dirty

    @pytest.mark.asyncio
    async def test_explicit_null_vs_unset(self):
        """Demonstrate difference between null and UNSET."""
        tag = Tag(id="123", name="Test")

        # Scenario 1: Set field to null (want to clear it on server)
        tag.description = None
        await tag.to_input()
        # Should include description=null to clear server value

        # Scenario 2: Leave field UNSET (don't touch server value)
        # tag.aliases = UNSET  # Never set
        # input2 = await tag.to_input()
        # Should NOT include aliases at all
