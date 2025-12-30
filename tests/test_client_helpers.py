"""Tests for stash_graphql_client.client_helpers module.

Tests utility functions including normalize_str, str_compare, and async_lru_cache decorator.
"""

import asyncio

import pytest

from stash_graphql_client.client_helpers import (
    async_lru_cache,
    normalize_str,
    str_compare,
)


class TestNormalizeStr:
    """Test normalize_str() function."""

    @pytest.mark.unit
    def test_removes_punctuation(self) -> None:
        """Test that punctuation is removed and replaced with spaces."""
        assert normalize_str("hello,world!") == "hello world"
        assert normalize_str("test.string") == "test string"
        assert normalize_str("foo-bar_baz") == "foo bar baz"
        assert normalize_str("a!b@c#d$e%f^g&h*i") == "a b c d e f g h i"

    @pytest.mark.unit
    def test_normalizes_whitespace(self) -> None:
        """Test that multiple whitespace chars are collapsed to single space."""
        assert normalize_str("hello    world") == "hello world"
        assert normalize_str("foo\t\tbar") == "foo bar"
        assert normalize_str("a\n\n\nb") == "a b"
        assert normalize_str("test  \t\n  string") == "test string"

    @pytest.mark.unit
    def test_strips_leading_trailing_whitespace(self) -> None:
        """Test that leading/trailing whitespace is removed."""
        assert normalize_str("  hello  ") == "hello"
        assert normalize_str("\t\nworld\n\t") == "world"
        assert normalize_str("   test string   ") == "test string"

    @pytest.mark.unit
    def test_combined_normalization(self) -> None:
        """Test combination of punctuation removal and whitespace normalization."""
        assert normalize_str("  Hello, World!  ") == "Hello World"
        assert (
            normalize_str("test-string_with.punctuation")
            == "test string with punctuation"
        )
        assert normalize_str("\t\tFoo,  Bar!!  \n") == "Foo Bar"

    @pytest.mark.unit
    def test_empty_string(self) -> None:
        """Test that empty string remains empty."""
        assert normalize_str("") == ""
        assert normalize_str("   ") == ""

    @pytest.mark.unit
    def test_no_changes_needed(self) -> None:
        """Test strings that don't need normalization."""
        assert normalize_str("hello world") == "hello world"
        assert normalize_str("test") == "test"


class TestStrCompare:
    """Test str_compare() function."""

    @pytest.mark.unit
    def test_case_insensitive_by_default(self) -> None:
        """Test that comparison is case-insensitive by default."""
        assert str_compare("Hello", "hello") is True
        assert str_compare("WORLD", "world") is True
        assert str_compare("TeSt", "test") is True

    @pytest.mark.unit
    def test_case_sensitive_when_specified(self) -> None:
        """Test case-sensitive comparison when ignore_case=False."""
        assert str_compare("Hello", "hello", ignore_case=False) is False
        assert str_compare("WORLD", "WORLD", ignore_case=False) is True
        assert str_compare("test", "test", ignore_case=False) is True

    @pytest.mark.unit
    def test_normalizes_before_comparing(self) -> None:
        """Test that strings are normalized before comparison."""
        assert str_compare("Hello, World!", "hello world") is True
        assert str_compare("test-string", "test_string") is True
        assert str_compare("  foo  bar  ", "foo bar") is True

    @pytest.mark.unit
    def test_punctuation_ignored(self) -> None:
        """Test that punctuation is removed before comparison."""
        # Punctuation is replaced with spaces, so "don't" becomes "don t"
        assert str_compare("don't", "don t") is True
        assert str_compare("hello!", "hello") is True
        # Hyphens become spaces
        assert str_compare("foo-bar", "foo bar") is True

    @pytest.mark.unit
    def test_whitespace_normalized(self) -> None:
        """Test that whitespace differences are normalized."""
        assert str_compare("hello  world", "hello world") is True
        assert str_compare("test\n\nstring", "test string") is True

    @pytest.mark.unit
    def test_different_strings_return_false(self) -> None:
        """Test that different strings return False."""
        assert str_compare("hello", "world") is False
        assert str_compare("foo", "bar") is False

    @pytest.mark.unit
    def test_empty_strings(self) -> None:
        """Test comparison of empty strings."""
        assert str_compare("", "") is True
        assert str_compare("   ", "") is True
        assert str_compare("", "test") is False


class TestAsyncLruCache:
    """Test async_lru_cache() decorator."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_basic_caching(self) -> None:
        """Test that function results are cached."""
        call_count = 0

        @async_lru_cache(maxsize=10)
        async def expensive_operation(x: int) -> int:
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.001)  # Simulate async work
            return x * 2

        # First call - should execute function
        result1 = await expensive_operation(5)
        assert result1 == 10
        assert call_count == 1

        # Second call with same args - should use cache
        result2 = await expensive_operation(5)
        assert result2 == 10
        assert call_count == 1  # Should not increase

        # Different args - should execute function
        result3 = await expensive_operation(10)
        assert result3 == 20
        assert call_count == 2

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_cache_with_dict_args(self) -> None:
        """Test caching with dictionary arguments (converted to sorted JSON)."""
        call_count = 0

        @async_lru_cache(maxsize=10)
        async def process_data(data: dict) -> str:
            nonlocal call_count
            call_count += 1
            return f"processed_{data['key']}"

        # Call with dict - keys in different order should cache the same
        result1 = await process_data({"key": "value", "other": "data"})
        assert result1 == "processed_value"
        assert call_count == 1

        # Same dict, different key order - should hit cache
        result2 = await process_data({"other": "data", "key": "value"})
        assert result2 == "processed_value"
        assert call_count == 1  # Should use cache

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_cache_with_list_args(self) -> None:
        """Test caching with list arguments."""
        call_count = 0

        @async_lru_cache(maxsize=10)
        async def sum_list(items: list) -> int:
            nonlocal call_count
            call_count += 1
            return sum(items)

        result1 = await sum_list([1, 2, 3])
        assert result1 == 6
        assert call_count == 1

        # Same list - should hit cache
        result2 = await sum_list([1, 2, 3])
        assert result2 == 6
        assert call_count == 1

        # Different list - should execute
        result3 = await sum_list([4, 5, 6])
        assert result3 == 15
        assert call_count == 2

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_cache_with_kwargs(self) -> None:
        """Test caching with keyword arguments."""
        call_count = 0

        @async_lru_cache(maxsize=10)
        async def greet(name: str, greeting: str = "Hello") -> str:
            nonlocal call_count
            call_count += 1
            return f"{greeting}, {name}!"

        result1 = await greet("Alice", greeting="Hi")
        assert result1 == "Hi, Alice!"
        assert call_count == 1

        # Same kwargs - should hit cache
        result2 = await greet("Alice", greeting="Hi")
        assert result2 == "Hi, Alice!"
        assert call_count == 1

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_cache_clear(self) -> None:
        """Test cache_clear() method."""
        call_count = 0

        @async_lru_cache(maxsize=10)
        async def get_value(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2

        # Populate cache
        await get_value(5)
        assert call_count == 1

        # Use cache
        await get_value(5)
        assert call_count == 1

        # Clear cache
        get_value.cache_clear()

        # Should execute again after clear
        await get_value(5)
        assert call_count == 2

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_cache_info(self) -> None:
        """Test cache_info() method."""

        @async_lru_cache(maxsize=5)
        async def compute(x: int) -> int:
            return x * 2

        # Check initial state
        info = compute.cache_info()
        assert info["maxsize"] == 5
        assert info["currsize"] == 0

        # Add items to cache
        await compute(1)
        await compute(2)
        await compute(3)

        info = compute.cache_info()
        assert info["maxsize"] == 5
        assert info["currsize"] == 3

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_cache_maxsize_eviction(self) -> None:
        """Test that cache evicts least recently used items when maxsize is exceeded."""
        call_count = 0

        @async_lru_cache(maxsize=2)
        async def get_item(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2

        # Fill cache to maxsize
        await get_item(1)  # Cache: {1}
        await get_item(2)  # Cache: {1, 2}
        assert call_count == 2

        # Add one more - should evict first item
        await get_item(3)  # Cache: {2, 3} (1 evicted)
        assert call_count == 3

        # Accessing evicted item should re-execute
        await get_item(1)  # Cache: {3, 1} (2 evicted)
        assert call_count == 4

        # Accessing cached item should not re-execute
        await get_item(3)
        assert call_count == 4  # No increase

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_exclude_arg_indices(self) -> None:
        """Test exclude_arg_indices parameter to exclude args from cache key."""
        call_count = 0

        # Exclude second argument (index 1) from cache key
        @async_lru_cache(maxsize=10, exclude_arg_indices=[1])
        async def process(data: str, timestamp: float) -> str:
            nonlocal call_count
            call_count += 1
            return f"processed_{data}"

        # Different timestamps but same data - should hit cache
        result1 = await process("test", 1.0)
        assert result1 == "processed_test"
        assert call_count == 1

        result2 = await process("test", 2.0)  # Different timestamp
        assert result2 == "processed_test"
        assert call_count == 1  # Should hit cache (timestamp excluded)

        # Different data - should execute
        result3 = await process("other", 1.0)
        assert result3 == "processed_other"
        assert call_count == 2

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_complex_nested_structures(self) -> None:
        """Test caching with nested lists and dicts."""
        call_count = 0

        @async_lru_cache(maxsize=10)
        async def process_nested(data: dict) -> str:
            nonlocal call_count
            call_count += 1
            return str(data)

        nested1 = {"key": [1, 2, {"nested": "value"}]}
        nested2 = {"key": [1, 2, {"nested": "value"}]}

        result1 = await process_nested(nested1)
        assert call_count == 1
        assert result1 == str(nested1)

        # Same structure - should hit cache
        result2 = await process_nested(nested2)
        assert call_count == 1
        assert result2 == str(nested2)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_functools_wraps_preserves_metadata(self) -> None:
        """Test that @functools.wraps preserves function metadata."""

        @async_lru_cache(maxsize=10)
        async def documented_function(x: int) -> int:
            """This function has documentation."""
            return x * 2

        assert documented_function.__name__ == "documented_function"
        docstring = documented_function.__doc__
        assert docstring is not None
        assert "documentation" in docstring
