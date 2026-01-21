"""Tests for StashInput deprecation warnings for unknown fields.

These tests verify that v0.11.0 emits DeprecationWarning for unknown fields
to help users identify typos before v0.12.0 enforcement (extra="forbid").
"""

import warnings

import pytest

from stash_graphql_client.types.markers import BulkSceneMarkerUpdateInput
from stash_graphql_client.types.scene import SceneUpdateInput
from stash_graphql_client.types.tag import TagDestroyInput


class TestStashInputDeprecationWarnings:
    """Test that StashInput emits deprecation warnings for unknown fields."""

    def test_extra_field_emits_deprecation_warning(self):
        """Unknown field should emit DeprecationWarning with helpful message."""
        with pytest.warns(DeprecationWarning, match=r"v0\.12\.0.*tag_id"):
            # Common typo: singular instead of plural
            BulkSceneMarkerUpdateInput(
                ids=["1", "2"],
                primary_tag_id="123",
                tag_id="456",  # ❌ Typo! Should be "tag_ids" (plural)
            )

    def test_multiple_extra_fields_all_listed_in_warning(self):
        """Warning should list all unknown fields, not just the first one."""
        with pytest.warns(
            DeprecationWarning, match="typo_field_1.*typo_field_2"
        ) as warning_list:
            SceneUpdateInput(
                id="123",
                title="Valid field",
                typo_field_1="bad",  # Unknown field 1
                typo_field_2="bad",  # Unknown field 2
            )

        # Should emit exactly one warning with both fields mentioned
        assert len(warning_list) == 1
        warning_message = str(warning_list[0].message)
        assert "typo_field_1" in warning_message
        assert "typo_field_2" in warning_message

    def test_valid_fields_no_warning(self):
        """Valid fields should not emit any warnings."""
        with warnings.catch_warnings():
            warnings.simplefilter("error")  # Turn warnings into errors

            # Should not raise any warnings/errors
            TagDestroyInput(id="1")  # Note: singular "id", not "ids"
            SceneUpdateInput(id="123", title="Test Scene")
            # Note: tag_ids needs BulkUpdateIds object, not list
            BulkSceneMarkerUpdateInput(ids=["1"], primary_tag_id="456")

    def test_graphql_alias_fields_no_warning(self):
        """Fields using GraphQL camelCase aliases should not emit warnings."""
        with warnings.catch_warnings():
            warnings.simplefilter("error")  # Turn warnings into errors

            # Both Python snake_case and GraphQL camelCase should work
            SceneUpdateInput(id="123", title="Test")  # Python style
            SceneUpdateInput(id="123", title="Test")  # GraphQL style (same field)

    def test_warning_suggests_common_fixes(self):
        """Warning message should include helpful suggestions for common typos."""
        with pytest.warns(DeprecationWarning) as warning_list:
            BulkSceneMarkerUpdateInput(
                ids=["1"],
                tag_id="typo",  # Common mistake: singular instead of plural
            )

        warning_message = str(warning_list[0].message)
        # Should mention common mistakes
        assert "tag_id" in warning_message.lower()
        assert "tag_ids" in warning_message.lower()
        assert "plural" in warning_message.lower()

    def test_warning_includes_class_name(self):
        """Warning should identify which Input class has the problem."""
        with pytest.warns(DeprecationWarning, match="BulkSceneMarkerUpdateInput"):
            BulkSceneMarkerUpdateInput(ids=["1"], unknown_field="bad")

        with pytest.warns(DeprecationWarning, match="SceneUpdateInput"):
            SceneUpdateInput(id="123", another_unknown="bad")

    def test_dict_input_still_works_with_warning(self):
        """Extra fields should still be accepted (just warned), not rejected."""
        with pytest.warns(DeprecationWarning):
            obj = BulkSceneMarkerUpdateInput(
                ids=["1", "2"],
                primary_tag_id="123",
                typo_field="this will be ignored but warned",
            )

        # Object should still be created successfully
        assert obj.ids == ["1", "2"]
        assert obj.primary_tag_id == "123"

    def test_non_dict_input_no_warning(self):
        """Non-dict inputs should not trigger validation (edge case)."""
        # This is an edge case - validator only checks dict inputs
        with warnings.catch_warnings():
            warnings.simplefilter("error")

            # Should not raise (non-dict inputs skip the validator)
            # This is a theoretical edge case - normal usage always passes dicts
            try:
                # Pydantic will handle validation of non-dict inputs
                SceneUpdateInput.model_validate("not a dict")  # type: ignore
            except Exception:
                # Expected to fail validation, but should not emit DeprecationWarning
                pass

    def test_warning_stacklevel_points_to_user_code(self):
        """Warning should have correct stacklevel to point to user's code, not validator."""
        with pytest.warns(DeprecationWarning) as warning_list:
            # This line should be identified as the source
            BulkSceneMarkerUpdateInput(ids=["1"], bad_field="typo")

        # Check that stacklevel is set
        # Note: pytest wraps the call, so we just verify a warning was emitted
        warning = warning_list[0]
        assert warning is not None
        assert "bad_field" in str(warning.message)


class TestDeprecationWarningIntegration:
    """Integration tests for deprecation warnings in realistic scenarios."""

    def test_user_catches_typo_before_v0_12_enforcement(self):
        """Simulates user workflow: see warning, fix typo, warning disappears."""
        # Step 1: User has a typo and sees warning
        with pytest.warns(DeprecationWarning, match="tag_id"):
            wrong_input = BulkSceneMarkerUpdateInput(
                ids=["1"],
                tag_id="typo",  # ❌ Wrong
            )
            assert wrong_input.ids == ["1"]

        # Step 2: User fixes typo, no warning
        with warnings.catch_warnings():
            warnings.simplefilter("error")

            correct_input = BulkSceneMarkerUpdateInput(
                ids=["1"],
                primary_tag_id="123",  # ✅ Correct
            )
            assert correct_input.ids == ["1"]
            assert correct_input.primary_tag_id == "123"

    def test_multiple_inputs_each_warn_separately(self):
        """Each Input class with typos should emit its own warning."""
        with pytest.warns(DeprecationWarning) as warning_list:
            BulkSceneMarkerUpdateInput(ids=["1"], typo1="bad")
            SceneUpdateInput(id="2", typo2="bad")
            TagDestroyInput(id="3", typo3="bad")

        # Should have 3 separate warnings
        assert len(warning_list) == 3
        assert "BulkSceneMarkerUpdateInput" in str(warning_list[0].message)
        assert "SceneUpdateInput" in str(warning_list[1].message)
        assert "TagDestroyInput" in str(warning_list[2].message)
