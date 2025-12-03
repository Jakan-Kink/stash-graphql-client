"""Unit tests for client_helpers.py string utilities."""

import pytest

from stash_graphql_client.client_helpers import normalize_str, str_compare


@pytest.mark.unit
class TestNormalizeStr:
    """Tests for normalize_str function."""

    def test_removes_punctuation(self) -> None:
        """Test that punctuation is removed and replaced with spaces."""
        result = normalize_str("hello, world!")
        assert result == "hello world"

    def test_normalizes_multiple_whitespace(self) -> None:
        """Test that multiple whitespace characters are collapsed to single space."""
        result = normalize_str("hello    world")
        assert result == "hello world"

    def test_strips_leading_trailing_whitespace(self) -> None:
        """Test that leading and trailing whitespace is stripped."""
        result = normalize_str("  hello world  ")
        assert result == "hello world"

    def test_handles_tabs_and_newlines(self) -> None:
        """Test that tabs and newlines are normalized to spaces."""
        result = normalize_str("hello\t\nworld")
        assert result == "hello world"

    def test_handles_mixed_punctuation_and_whitespace(self) -> None:
        """Test handling of mixed punctuation and whitespace."""
        result = normalize_str("  Hello,  World!  How's it going?  ")
        assert result == "Hello World How s it going"

    def test_handles_empty_string(self) -> None:
        """Test handling of empty string."""
        result = normalize_str("")
        assert result == ""

    def test_handles_only_punctuation(self) -> None:
        """Test handling of string with only punctuation."""
        result = normalize_str("!@#$%")
        assert result == ""

    def test_preserves_alphanumeric(self) -> None:
        """Test that alphanumeric characters are preserved."""
        result = normalize_str("abc123XYZ")
        assert result == "abc123XYZ"


@pytest.mark.unit
class TestStrCompare:
    """Tests for str_compare function."""

    def test_equal_strings_case_insensitive(self) -> None:
        """Test that equal strings match case-insensitively by default."""
        assert str_compare("Hello", "hello") is True

    def test_equal_strings_case_sensitive(self) -> None:
        """Test case-sensitive comparison when ignore_case=False."""
        assert str_compare("Hello", "hello", ignore_case=False) is False
        assert str_compare("Hello", "Hello", ignore_case=False) is True

    def test_different_strings(self) -> None:
        """Test that different strings don't match."""
        assert str_compare("hello", "world") is False

    def test_ignores_punctuation_differences(self) -> None:
        """Test that punctuation differences are ignored."""
        assert str_compare("Hello, World!", "Hello World") is True

    def test_ignores_whitespace_differences(self) -> None:
        """Test that whitespace differences are ignored."""
        assert str_compare("hello   world", "hello world") is True

    def test_empty_strings(self) -> None:
        """Test comparison of empty strings."""
        assert str_compare("", "") is True

    def test_normalized_comparison(self) -> None:
        """Test that strings are normalized before comparison."""
        assert str_compare("  Hello,  World!  ", "hello world") is True
