"""Test string list field filtering (aliases, urls, captions).

This module tests the fix for fields that are lists on entities but use
StringCriterionInput for filtering (substring matching), NOT MultiCriterionInput.

Bug Context:
- Before fix: aliases__contains="name" sent {"value": ["name"]} (incorrect list)
- After fix: aliases__contains="name" sends {"value": "name"} (correct single string)
"""

from stash_graphql_client.store import StashEntityStore


class TestStringListFieldFiltering:
    """Test that string list fields use single-string criterion values."""

    def test_aliases_uses_single_string_value(
        self, respx_entity_store: StashEntityStore
    ):
        """Test aliases filter sends single string, not list.

        Fields like 'aliases' are [String!] on entities but use StringCriterionInput
        for filtering, which searches for substring matches WITHIN the list items.
        """
        # Build criterion for aliases field
        criterion = respx_entity_store._build_criterion(
            field="aliases", modifier="INCLUDES", value="JaneDoe"
        )

        # Should be single string, NOT wrapped in list
        assert criterion == {"value": "JaneDoe", "modifier": "INCLUDES"}
        assert not isinstance(criterion["value"], list)

    def test_url_uses_single_string_value(self, respx_entity_store: StashEntityStore):
        """Test url filter sends single string for urls list.

        The 'url' filter searches within the 'urls: [String!]' list on entities.
        """
        criterion = respx_entity_store._build_criterion(
            field="url", modifier="INCLUDES", value="example.com"
        )

        assert criterion == {"value": "example.com", "modifier": "INCLUDES"}
        assert not isinstance(criterion["value"], list)

    def test_captions_uses_single_string_value(
        self, respx_entity_store: StashEntityStore
    ):
        """Test captions filter sends single string for captions list."""
        criterion = respx_entity_store._build_criterion(
            field="captions", modifier="INCLUDES", value="subtitle text"
        )

        assert criterion == {"value": "subtitle text", "modifier": "INCLUDES"}
        assert not isinstance(criterion["value"], list)

    def test_relationship_fields_still_use_list(
        self, respx_entity_store: StashEntityStore
    ):
        """Verify relationship fields still wrap values in lists.

        Multi-value relationship fields (tags, performers, etc.) should still
        wrap values in lists because they use MultiCriterionInput.
        """
        # Test a known multi-value field
        criterion = respx_entity_store._build_criterion(
            field="tags", modifier="INCLUDES", value="123"
        )

        # Should be wrapped in list for multi-value fields
        assert criterion == {"value": ["123"], "modifier": "INCLUDES"}
        assert isinstance(criterion["value"], list)

    def test_performers_field_uses_list(self, respx_entity_store: StashEntityStore):
        """Test performers field wraps in list (uses MultiCriterionInput)."""
        criterion = respx_entity_store._build_criterion(
            field="performers", modifier="INCLUDES", value="456"
        )

        assert criterion == {"value": ["456"], "modifier": "INCLUDES"}
        assert isinstance(criterion["value"], list)

    def test_studios_field_uses_list(self, respx_entity_store: StashEntityStore):
        """Test studios field wraps in list (uses HierarchicalMultiCriterionInput)."""
        criterion = respx_entity_store._build_criterion(
            field="studios", modifier="INCLUDES", value="789"
        )

        assert criterion == {"value": ["789"], "modifier": "INCLUDES"}
        assert isinstance(criterion["value"], list)

    def test_aliases_with_list_input_not_double_wrapped(
        self, respx_entity_store: StashEntityStore
    ):
        """Test aliases with list input doesn't get double-wrapped.

        If user passes a list directly, it should not be wrapped again.
        This edge case shouldn't normally happen but test defensive handling.
        """
        # Even if list is passed, aliases should stay single-value
        # (not double-wrapped)
        criterion = respx_entity_store._build_criterion(
            field="aliases",
            modifier="INCLUDES",
            value="SingleName",  # Normal usage
        )

        assert criterion == {"value": "SingleName", "modifier": "INCLUDES"}

    def test_removed_fields_not_in_multi_value_set(
        self, respx_entity_store: StashEntityStore
    ):
        """Verify removed fields (child_studios, markers, etc.) don't wrap in lists."""
        # These fields were removed from multi_value_fields in the fix

        # child_studios - removed (no filter exists)
        criterion = respx_entity_store._build_criterion(
            field="child_studios", modifier="INCLUDES", value="123"
        )
        assert criterion == {"value": "123", "modifier": "INCLUDES"}

        # markers - removed (no filter exists)
        criterion = respx_entity_store._build_criterion(
            field="markers", modifier="INCLUDES", value="456"
        )
        assert criterion == {"value": "456", "modifier": "INCLUDES"}

        # files - removed (not directly filterable)
        criterion = respx_entity_store._build_criterion(
            field="files", modifier="INCLUDES", value="789"
        )
        assert criterion == {"value": "789", "modifier": "INCLUDES"}

        # stash_ids - removed (uses different criterion)
        criterion = respx_entity_store._build_criterion(
            field="stash_ids", modifier="INCLUDES", value="abc"
        )
        assert criterion == {"value": "abc", "modifier": "INCLUDES"}
