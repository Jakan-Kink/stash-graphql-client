import functools
import json
import re
import string
from collections.abc import Awaitable, Callable
from typing import Any, Protocol, TypeVar, cast

from .logging import debug_print


# For type hints in the async_lru_cache decorator
T = TypeVar("T")
R = TypeVar("R")


class AsyncCachedFunction(Protocol):
    """Protocol for async functions decorated with async_lru_cache."""

    def __call__(self, *args: Any, **kwargs: Any) -> Awaitable[Any]:
        """Call the cached function."""
        ...

    def cache_clear(self) -> None:
        """Clear the cache."""
        ...

    def cache_info(self) -> dict[str, int]:
        """Get cache information."""
        ...


def normalize_str(string_in: str) -> str:
    # remove punctuation
    punctuation = re.compile(f"[{string.punctuation}]")
    string_in = re.sub(punctuation, " ", string_in)

    # normalize whitespace
    whitespace = re.compile(f"[{string.whitespace}]+")
    string_in = re.sub(whitespace, " ", string_in)

    # remove leading and trailing whitespace
    return string_in.strip(string.whitespace)


def str_compare(s1: str, s2: str, ignore_case: bool = True) -> bool:
    s1 = normalize_str(s1)
    s2 = normalize_str(s2)
    if ignore_case:
        s1 = s1.lower()
        s2 = s2.lower()
    return s1 == s2


def async_lru_cache(
    maxsize: int = 128, exclude_arg_indices: list[int] | None = None
) -> Callable[[Callable[..., Awaitable[R]]], AsyncCachedFunction]:
    """Decorator to add LRU caching to an async function.

    Args:
        maxsize: Maximum size of the cache. Once this size is reached,
                the least recently used items will be evicted.
        exclude_arg_indices: List of argument indices to exclude from the cache key.

    Returns:
        Decorated async function with caching.

    The cache key is based on the function arguments. For mutable arguments
    like dictionaries, they are converted to JSON strings with sorted keys
    to ensure consistent cache keys regardless of dict key order.

    The decorated function gets two additional methods:
    - cache_clear(): Clear the cache
    - cache_info(): Get info about cache size and capacity
    """

    def decorator(func: Callable[..., Awaitable[R]]) -> AsyncCachedFunction:
        # Create cache
        cache: dict[Any, R] = {}

        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> R:
            # Create cache key from args and kwargs
            # Convert any dicts to sorted JSON for consistent keys
            def make_key_part(arg: Any) -> Any:
                if isinstance(arg, dict):
                    return json.dumps(arg, sort_keys=True)
                if isinstance(arg, (list, tuple)):
                    return tuple(make_key_part(x) for x in arg)
                return arg

            # Filter out excluded args
            excluded = exclude_arg_indices or []
            filtered_args = [arg for i, arg in enumerate(args) if i not in excluded]

            key = (
                tuple(make_key_part(arg) for arg in filtered_args),
                tuple(sorted((k, make_key_part(v)) for k, v in kwargs.items())),
            )

            # Check cache
            if key in cache:
                debug_print(
                    {
                        "method": "async_lru_cache",
                        "status": "cache_hit",
                        "func": func.__name__,
                        "args": args,
                        "kwargs": kwargs,
                    },
                    "processing",
                )
                return cache[key]

            # Call function and cache result
            result = await func(*args, **kwargs)
            cache[key] = result

            # Maintain cache size
            if len(cache) > maxsize:
                # Remove least recently used item
                cache.pop(next(iter(cache)))

            debug_print(
                {
                    "method": "async_lru_cache",
                    "status": "cache_miss",
                    "func": func.__name__,
                    "args": args,
                    "kwargs": kwargs,
                },
                "processing",
            )
            return result

        # Add cache management methods
        def cache_clear() -> None:
            cache.clear()

        def cache_info() -> dict[str, int]:
            return {"maxsize": maxsize, "currsize": len(cache)}

        wrapper.cache_clear = cache_clear  # type: ignore
        wrapper.cache_info = cache_info  # type: ignore

        return cast("AsyncCachedFunction", wrapper)

    return decorator
