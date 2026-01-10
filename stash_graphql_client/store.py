"""Entity store with read-through caching for Stash entities.

This module provides an in-memory identity map with caching, selective field loading,
and query capabilities for Stash GraphQL entities.
"""

from __future__ import annotations

import threading
import time
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass, field
from datetime import timedelta
from typing import TYPE_CHECKING, Any, TypeVar

from . import fragments
from .client.utils import sanitize_model_data
from .errors import StashError, StashIntegrationError
from .logging import client_logger as log
from .types.base import StashObject


if TYPE_CHECKING:
    from .client import StashClient

T = TypeVar("T", bound=StashObject)


@dataclass
class CacheEntry[T]:
    """Internal cache entry with TTL tracking using monotonic time."""

    entity: T
    cached_at: float  # time.monotonic() value when cached
    ttl_seconds: float | None = None  # None = never expires

    def is_expired(self) -> bool:
        """Check if this cache entry has expired."""
        if self.ttl_seconds is None:
            return False
        return (time.monotonic() - self.cached_at) > self.ttl_seconds


@dataclass
class FindResult[T]:
    """Result from a find query."""

    items: list[T]
    count: int
    page: int
    per_page: int


@dataclass
class CacheStats:
    """Cache statistics."""

    total_entries: int = 0
    by_type: dict[str, int] = field(default_factory=dict)
    expired_count: int = 0


class StashEntityStore:
    """In-memory identity map with read-through caching for Stash entities.

    Provides caching, selective field loading, and query capabilities for Stash
    GraphQL entities. All fetched entities are cached, and subsequent requests for
    the same entity return the cached version (if not expired).

    All entities can be treated as "stubs" that may have incomplete data. Use
    populate() to selectively load additional fields as needed, avoiding expensive
    queries for data you don't need.

    Example:
        ```python
        async with StashContext(conn=...) as context:
            client = context.client
            store = context.store  # Use context's singleton store

            # Get by ID (cache miss -> fetch, then cached)
            performer = await store.get(Performer, "123")

            # Selectively load expensive fields only when needed
            # Uses _received_fields to determine what's actually missing
            performer = await store.populate(performer, fields=["scenes", "images"])

            # Search (always queries GraphQL, caches results)
            scenes = await store.find(Scene, title__contains="interview")

            # Populate relationships on search results
            for scene in scenes:
                scene = await store.populate(scene, fields=["performers", "studio", "tags"])

            # Populate nested objects directly (identity map pattern)
            scene.studio = await store.populate(scene.studio, fields=["urls", "details"])

            # Check what's missing before fetching
            missing = store.missing_fields(scene.studio, "urls", "details")
            if missing:
                scene.studio = await store.populate(scene.studio, fields=list(missing))

            # Force refresh from server (invalidates cache first)
            scene = await store.populate(scene, fields=["studio"], force_refetch=True)

            # Large result sets: lazy pagination
            async for scene in store.find_iter(Scene, path__contains="/media/"):
                process(scene)
                if done:
                    break  # Won't fetch remaining batches

            # Query cached objects only (no network)
            favorites = store.filter(Performer, lambda p: p.favorite)
        ```
    """

    DEFAULT_QUERY_BATCH = 40
    DEFAULT_TTL = timedelta(minutes=30)
    FIND_LIMIT = 1000  # Max results for find() before requiring find_iter()

    def __init__(
        self,
        client: StashClient,
        default_ttl: timedelta | None = DEFAULT_TTL,
    ) -> None:
        """Initialize entity store.

        Args:
            client: StashClient instance for GraphQL queries
            default_ttl: Default TTL for cached entities. Default is 30 minutes.
                         Pass None explicitly to disable expiration.
        """
        self._client = client
        self._default_ttl = default_ttl
        # Cache keyed by (type_name, id)
        self._cache: dict[tuple[str, str], CacheEntry[Any]] = {}
        # Per-type TTL overrides
        self._type_ttls: dict[str, timedelta | None] = {}
        # Thread-safety lock (reentrant to allow nested calls)
        self._lock = threading.RLock()

    # ─── Read-through by ID ───────────────────────────────────

    async def get(
        self, entity_type: type[T], entity_id: str, fields: list[str] | None = None
    ) -> T | None:
        """Get entity by ID. Checks cache first, fetches if missing/expired (thread-safe).

        Args:
            entity_type: The Stash entity type (e.g., Performer, Scene)
            entity_id: Entity ID
            fields: Optional list of additional fields to fetch beyond base fragment.
                   If provided, bypasses cache and fetches directly with specified fields.

        Returns:
            Entity if found, None otherwise
        """
        type_name = entity_type.__type_name__
        cache_key = (type_name, entity_id)

        # If specific fields requested, bypass cache and fetch directly
        if fields is not None:
            log.debug(f"Fetching {type_name} {entity_id} with fields: {fields}")
            entity = await self._fetch_with_fields(entity_type, entity_id, fields)
            if entity is not None:
                self._cache_entity(entity)  # _cache_entity is thread-safe
            return entity

        # Check cache (lock → check → unlock)
        cache_hit = False
        with self._lock:
            if cache_key in self._cache:
                entry = self._cache[cache_key]
                if not entry.is_expired():
                    log.debug(f"Cache hit: {type_name} {entity_id}")
                    cached_entity = entry.entity
                    cache_hit = True
                else:
                    log.debug(f"Cache expired: {type_name} {entity_id}")
                    del self._cache[cache_key]

        if cache_hit:
            return cached_entity  # type: ignore[return-value]

        # Cache miss - fetch from GraphQL (no lock during await!)
        log.debug(f"Cache miss: {type_name} {entity_id}")
        entity = await entity_type.find_by_id(self._client, entity_id)

        if entity is not None:
            self._cache_entity(entity)  # _cache_entity is thread-safe

        return entity

    async def get_many(self, entity_type: type[T], ids: list[str]) -> list[T]:
        """Batch get entities. Returns cached + fetches missing in single query (thread-safe).

        Args:
            entity_type: The Stash entity type
            ids: List of entity IDs

        Returns:
            List of found entities (order not guaranteed)
        """
        type_name = entity_type.__type_name__
        results: list[T] = []
        missing_ids: list[str] = []

        # Check cache for each ID (lock → check all → unlock)
        with self._lock:
            for eid in ids:
                cache_key = (type_name, eid)
                if cache_key in self._cache:
                    entry = self._cache[cache_key]
                    if not entry.is_expired():
                        results.append(entry.entity)  # type: ignore[arg-type]
                    else:
                        del self._cache[cache_key]
                        missing_ids.append(eid)
                else:
                    missing_ids.append(eid)

        # Fetch missing IDs (no lock during await!)
        if missing_ids:
            log.debug(f"Fetching {len(missing_ids)} missing {type_name} entities")
            fetched = await self._execute_find_by_ids(entity_type, missing_ids)
            for entity in fetched:
                self._cache_entity(entity)  # _cache_entity is thread-safe
                results.append(entity)

        return results

    # ─── Search (queries GraphQL, caches results) ─────────────

    async def find(self, entity_type: type[T], **filters: Any) -> list[T]:
        """Search using Stash filters. Results cached. Max 1000 results.

        Args:
            entity_type: The Stash entity type
            **filters: Search filters (Django-style kwargs or raw dict)

        Returns:
            List of matching entities

        Raises:
            ValueError: If result count exceeds FIND_LIMIT. Use find_iter() instead.

        Filter syntax:
            # Django-style kwargs
            find(Scene, title="exact")              # EQUALS
            find(Scene, title__contains="partial")  # INCLUDES
            find(Scene, title__regex=r"S\\d+")      # MATCHES_REGEX
            find(Scene, rating100__gte=80)          # GREATER_THAN
            find(Scene, rating100__between=(60,90)) # BETWEEN
            find(Scene, studio__null=True)          # IS_NULL

            # Raw dict for complex cases
            find(Scene, title={"value": "x", "modifier": "NOT_EQUALS"})

            # Nested filters
            find(Scene, performers_filter={"name": {"value": "Jane", "modifier": "EQUALS"}})
        """
        # First, get count to check against limit
        result = await self._execute_find(entity_type, filters, page=1, per_page=1)

        if result.count > self.FIND_LIMIT:
            raise StashError(
                f"Query returned {result.count} results, exceeding limit of {self.FIND_LIMIT}. "
                f"Use find_iter() for large result sets."
            )

        # Fetch all results
        if result.count == 0:
            return []

        result = await self._execute_find(
            entity_type, filters, page=1, per_page=result.count
        )

        # Cache all results
        for entity in result.items:
            self._cache_entity(entity)

        return result.items

    async def find_one(self, entity_type: type[T], **filters: Any) -> T | None:
        """Search returning first match. Result cached.

        Args:
            entity_type: The Stash entity type
            **filters: Search filters (same syntax as find())

        Returns:
            First matching entity, or None if no matches
        """
        result = await self._execute_find(entity_type, filters, page=1, per_page=1)

        if result.items:
            entity = result.items[0]
            self._cache_entity(entity)
            return entity

        return None

    async def find_iter(
        self,
        entity_type: type[T],
        query_batch: int = DEFAULT_QUERY_BATCH,
        **filters: Any,
    ) -> AsyncIterator[T]:
        """Lazy search yielding individual items. Batches queries internally.

        Args:
            entity_type: Type to search for
            query_batch: Records to fetch per GraphQL query (default: 40)
            **filters: Search filters (same syntax as find())

        Yields:
            Individual entities as they are fetched

        Example:
            async for scene in store.find_iter(Scene, path__contains="/media/"):
                process(scene)
                if done:
                    break  # Won't fetch remaining batches
        """
        if query_batch < 1:
            raise ValueError("query_batch must be positive")

        page = 1
        while True:
            result = await self._execute_find(
                entity_type, filters, page=page, per_page=query_batch
            )

            for item in result.items:
                self._cache_entity(item)
                yield item

            # Stop if we got fewer than requested (last page)
            if len(result.items) < query_batch:
                break

            page += 1

    # ─── Query cached objects only (no network) ───────────────

    def filter(self, entity_type: type[T], predicate: Callable[[T], bool]) -> list[T]:
        """Filter cached objects with Python lambda. No network call (thread-safe).

        Args:
            entity_type: The Stash entity type
            predicate: Function that returns True for matching entities

        Returns:
            List of matching cached entities
        """
        type_name = entity_type.__type_name__
        results: list[T] = []

        # Snapshot cache entries while holding lock
        with self._lock:
            cache_snapshot = list(self._cache.items())

        # Process snapshot without holding lock (predicate may be slow)
        for (cached_type, _), entry in cache_snapshot:
            if cached_type != type_name:
                continue
            if entry.is_expired():
                continue
            if predicate(entry.entity):
                results.append(entry.entity)

        return results

    def all_cached(self, entity_type: type[T]) -> list[T]:
        """Get all cached objects of a type.

        Args:
            entity_type: The Stash entity type

        Returns:
            List of all cached entities of the specified type
        """
        return self.filter(entity_type, lambda _: True)

    def filter_strict(
        self,
        entity_type: type[T],
        required_fields: set[str] | list[str],
        predicate: Callable[[T], bool],
    ) -> list[T]:
        """Filter cached objects, raising error if required fields are missing.

        This is a fail-fast version of filter() that ensures all cached objects
        have the required fields populated before applying the predicate. If any
        cached object is missing required fields, raises ValueError immediately.

        Supports nested field specifications using Django-style double-underscore syntax:
        - `'files__path'`: Validates that files relationship exists AND path is populated on each File
        - `'studio__parent__name'`: Validates full nested path is populated

        Args:
            entity_type: The Stash entity type
            required_fields: Fields that must be populated on all cached objects.
                           Supports both regular field names ('rating100') and nested
                           field specs ('files__path', 'studio__parent__name').
            predicate: Function that returns True for matching entities

        Returns:
            List of matching cached entities (all guaranteed to have required fields)

        Raises:
            ValueError: If any cached object is missing required fields

        Examples:
            # This will raise if any performer has rating100=UNSET
            high_rated = store.filter_strict(
                Performer,
                required_fields=['rating100', 'favorite'],
                predicate=lambda p: p.rating100 >= 80 and p.favorite
            )

            # Validate nested fields are populated
            large_images = store.filter_strict(
                Image,
                required_fields=['files__path', 'files__size'],
                predicate=lambda i: any(
                    f.size > 10_000_000 for f in i.files if f.size is not None
                )
            )
            # ↑ Raises ValueError if any Image has files=UNSET or any File has path/size=UNSET
        """
        type_name = entity_type.__type_name__
        fields_set = (
            set(required_fields)
            if isinstance(required_fields, list)
            else required_fields
        )
        results: list[T] = []

        # Snapshot cache entries
        with self._lock:
            cache_snapshot = list(self._cache.items())

        for (cached_type, _), entry in cache_snapshot:
            if cached_type != type_name:
                continue
            if entry.is_expired():
                continue

            entity = entry.entity

            # Check for missing fields - fail fast (supports nested field specs)
            missing = self.missing_fields_nested(entity, *fields_set)
            if missing:
                raise ValueError(
                    f"{type_name} {entity.id} is missing required fields: {missing}. "
                    f"Use filter_and_populate() to auto-fetch missing fields, or populate "
                    f"the cache first with store.find() or store.populate()."
                )

            if predicate(entity):
                results.append(entity)

        return results

    async def filter_and_populate(
        self,
        entity_type: type[T],
        required_fields: set[str] | list[str],
        predicate: Callable[[T], bool],
        batch_size: int = 50,
    ) -> list[T]:
        """Filter cached objects, auto-populating missing fields as needed.

        This is a smart hybrid between find() and filter():
        - Gets all cached objects of the type
        - Identifies which ones have UNSET values for required_fields
        - Fetches only the missing fields for incomplete objects (in batches)
        - Applies the predicate to all objects (now with complete data)

        Supports nested field specifications using Django-style double-underscore syntax:
        - `'files__path'`: Ensures files relationship is populated, then path on each File
        - `'studio__parent__name'`: Ensures studio, parent, and name are all populated

        This is much faster than find() when most data is already cached, since
        it only fetches the specific missing fields rather than re-fetching
        entire entities.

        Args:
            entity_type: The Stash entity type
            required_fields: Fields needed by the predicate. Supports both regular
                           field names ('rating100') and nested field specs
                           ('files__path', 'studio__parent__name').
            predicate: Function that returns True for matching entities
            batch_size: Number of entities to populate concurrently (default: 50)

        Returns:
            List of matching entities (all with required fields populated)

        Examples:
            # Cache has 1000 performers, but only 500 have rating100 loaded
            high_rated = await store.filter_and_populate(
                Performer,
                required_fields=['rating100', 'favorite'],
                predicate=lambda p: p.rating100 >= 80 and p.favorite
            )
            # ↓ Fetches rating100+favorite for the 500 that don't have it
            # ↓ Then filters all 1000 with complete data
            # ↓ Network calls: Only for missing data (much faster than find())

            # Filter images by nested file properties
            large_images = await store.filter_and_populate(
                Image,
                required_fields=['files__path', 'files__size'],
                predicate=lambda i: any(
                    f.size > 10_000_000 for f in i.files if f.size is not None
                )
            )
            # ↓ Fetches files relationship + path/size fields on each File object
        """
        type_name = entity_type.__type_name__
        fields_set = (
            set(required_fields)
            if isinstance(required_fields, list)
            else required_fields
        )

        # Get all cached objects
        all_cached = self.all_cached(entity_type)
        if not all_cached:
            return []

        # Identify objects needing population (supports nested field specs)
        to_populate: list[T] = [
            entity
            for entity in all_cached
            if self.missing_fields_nested(entity, *fields_set)
        ]

        # Batch populate for performance
        if to_populate:
            log.debug(
                f"filter_and_populate: populating {len(to_populate)}/{len(all_cached)} "
                f"{type_name} objects with fields {fields_set}"
            )

            # Populate in batches to avoid overwhelming the server
            import asyncio

            for i in range(0, len(to_populate), batch_size):
                batch = to_populate[i : i + batch_size]
                # Populate concurrently within batch
                await asyncio.gather(
                    *[
                        self.populate(entity, fields=list(fields_set))
                        for entity in batch
                    ]
                )

        # Apply predicate to all objects (now with complete data)
        # Get fresh snapshot from cache (populate() may have updated instances)
        with self._lock:
            cache_snapshot = list(self._cache.items())

        results: list[T] = []
        for (cached_type, _), entry in cache_snapshot:
            if cached_type != type_name:
                continue
            if entry.is_expired():
                continue

            entity = entry.entity

            # Verify all required fields are now present (defensive check)
            missing = self.missing_fields_nested(entity, *fields_set)
            if missing:
                log.warning(
                    f"{type_name} {entity.id} still missing {missing} after populate "
                    f"(this shouldn't happen)"
                )
                continue

            if predicate(entity):
                results.append(entity)

        return results

    async def filter_and_populate_with_stats(
        self,
        entity_type: type[T],
        required_fields: set[str] | list[str],
        predicate: Callable[[T], bool],
        batch_size: int = 50,
    ) -> tuple[list[T], dict[str, Any]]:
        """Filter and populate with debug statistics.

        Same as filter_and_populate() but returns detailed statistics about
        what was fetched and filtered. Useful for debugging and optimization.

        Supports nested field specifications using Django-style double-underscore syntax.

        Args:
            entity_type: The Stash entity type
            required_fields: Fields needed by the predicate. Supports both regular
                           field names ('rating100') and nested field specs
                           ('files__path', 'studio__parent__name').
            predicate: Function that returns True for matching entities
            batch_size: Number of entities to populate concurrently

        Returns:
            Tuple of (matching_entities, stats_dict) where stats contains:
            - total_cached: Total objects in cache
            - needed_population: How many needed fields fetched
            - populated_fields: Which fields were fetched
            - matches: How many matched the predicate
            - cache_hit_rate: Percentage with complete data

        Examples:
            results, stats = await store.filter_and_populate_with_stats(
                Performer,
                required_fields=['rating100'],
                predicate=lambda p: p.rating100 >= 80
            )
            print(f"Populated {stats['needed_population']} of {stats['total_cached']}")
            print(f"Cache hit rate: {stats['cache_hit_rate']:.1%}")
            print(f"Found {stats['matches']} matches")

            # With nested fields
            results, stats = await store.filter_and_populate_with_stats(
                Image,
                required_fields=['files__path', 'files__size'],
                predicate=lambda i: any(f.size > 10_000_000 for f in i.files)
            )
        """
        type_name = entity_type.__type_name__
        fields_set = (
            set(required_fields)
            if isinstance(required_fields, list)
            else required_fields
        )

        # Get all cached objects
        all_cached = self.all_cached(entity_type)
        total_cached = len(all_cached)

        if not all_cached:
            return [], {
                "total_cached": 0,
                "needed_population": 0,
                "populated_fields": list(fields_set),
                "matches": 0,
                "cache_hit_rate": 0.0,
            }

        # Identify objects needing population (supports nested field specs)
        to_populate: list[T] = [
            entity
            for entity in all_cached
            if self.missing_fields_nested(entity, *fields_set)
        ]
        needed_population = len(to_populate)

        # Batch populate
        if to_populate:
            log.debug(
                f"filter_and_populate_with_stats: populating {needed_population}/{total_cached} "
                f"{type_name} objects with fields {fields_set}"
            )

            import asyncio

            for i in range(0, len(to_populate), batch_size):
                batch = to_populate[i : i + batch_size]
                await asyncio.gather(
                    *[
                        self.populate(entity, fields=list(fields_set))
                        for entity in batch
                    ]
                )

        # Apply predicate
        with self._lock:
            cache_snapshot = list(self._cache.items())

        results: list[T] = []
        for (cached_type, _), entry in cache_snapshot:
            if cached_type != type_name:
                continue
            if entry.is_expired():
                continue

            entity = entry.entity
            missing = self.missing_fields_nested(entity, *fields_set)
            if missing:
                log.warning(
                    f"{type_name} {entity.id} still missing {missing} after populate"
                )
                continue

            if predicate(entity):
                results.append(entity)

        # Build stats
        cache_hit_rate = (
            (total_cached - needed_population) / total_cached
            if total_cached > 0
            else 0.0
        )
        stats = {
            "total_cached": total_cached,
            "needed_population": needed_population,
            "populated_fields": list(fields_set),
            "matches": len(results),
            "cache_hit_rate": cache_hit_rate,
        }

        return results, stats

    async def populated_filter_iter(
        self,
        entity_type: type[T],
        required_fields: set[str] | list[str],
        predicate: Callable[[T], bool],
        populate_batch: int = 50,
        yield_batch: int = 10,
    ) -> AsyncIterator[T]:
        """Lazy filter with auto-population, yielding results incrementally.

        Like filter_and_populate() but yields results as they become available
        instead of waiting for all entities to be processed. Useful for large
        datasets where you want to start processing matches immediately.

        Supports nested field specifications using Django-style double-underscore syntax.

        Args:
            entity_type: The Stash entity type
            required_fields: Fields needed by the predicate. Supports both regular
                           field names ('rating100') and nested field specs
                           ('files__path', 'studio__parent__name').
            predicate: Function that returns True for matching entities
            populate_batch: How many entities to populate concurrently
            yield_batch: Process this many entities before yielding matches

        Yields:
            Individual matching entities (with required fields populated)

        Examples:
            # Process large dataset incrementally
            async for performer in store.populated_filter_iter(
                Performer,
                required_fields=['rating100', 'scenes'],
                predicate=lambda p: p.rating100 >= 90 and len(p.scenes) > 100
            ):
                # Start processing immediately as matches are found
                await expensive_operation(performer)
                if should_stop:
                    break  # Can stop early without processing all

            # With nested fields
            async for image in store.populated_filter_iter(
                Image,
                required_fields=['files__path', 'files__size'],
                predicate=lambda i: any(f.size > 10_000_000 for f in i.files)
            ):
                await process_large_image(image)
        """
        type_name = entity_type.__type_name__
        fields_set = (
            set(required_fields)
            if isinstance(required_fields, list)
            else required_fields
        )

        # Get all cached objects
        all_cached = self.all_cached(entity_type)
        if not all_cached:
            return

        # Process in batches
        import asyncio

        for i in range(0, len(all_cached), yield_batch):
            batch = all_cached[i : i + yield_batch]

            # Identify which need population (supports nested field specs)
            to_populate = [
                entity
                for entity in batch
                if self.missing_fields_nested(entity, *fields_set)
            ]

            # Populate if needed (in sub-batches for memory efficiency)
            if to_populate:
                for j in range(0, len(to_populate), populate_batch):
                    sub_batch = to_populate[j : j + populate_batch]
                    await asyncio.gather(
                        *[
                            self.populate(entity, fields=list(fields_set))
                            for entity in sub_batch
                        ]
                    )

            # Yield matches from this batch
            for entity in batch:
                # Verify fields are present (supports nested field specs)
                missing = self.missing_fields_nested(entity, *fields_set)
                if missing:
                    log.warning(
                        f"{type_name} {entity.id} missing {missing} after populate"
                    )
                    continue

                # Check predicate
                if predicate(entity):
                    yield entity

    # ─── Field-aware population ─────────────────────────────────

    @staticmethod
    def _get_fetchable_type(entity_type: type[StashObject]) -> type[StashObject] | None:
        """Get the type that should be used for fetching this entity.

        Some types are polymorphic - ImageFile and VideoFile are BaseFile subclasses
        and should be fetched using BaseFile.find_by_id() which uses findFile query.

        Args:
            entity_type: The entity type to check

        Returns:
            The type to use for fetching, or None if not independently fetchable
        """
        # Handle non-class types gracefully (defensive check)
        if not isinstance(entity_type, type):
            return None

        from .types import BaseFile

        # Types with dedicated find queries (from types/base.py query_map)
        fetchable_type_names = {
            "Scene",
            "Performer",
            "Studio",
            "Tag",
            "Gallery",
            "Image",
            "SceneMarker",
            "Group",
            "BaseFile",
        }

        # Check if this type has its own find query
        try:
            type_name = entity_type.__type_name__
            if type_name in fetchable_type_names:
                return entity_type
        except AttributeError:
            return None

        # Check if it's a polymorphic BaseFile subclass (ImageFile, VideoFile, etc.)
        # These should be fetched as BaseFile using findFile query
        # Note: No try/except needed here since isinstance(entity_type, type) check above
        # ensures entity_type is a valid type for issubclass()
        if issubclass(entity_type, BaseFile) and entity_type is not BaseFile:
            return BaseFile

        return None

    def _get_concrete_type(
        self, data: dict[str, Any], requested_type: type[T]
    ) -> type[T]:
        """Get the concrete type to use for deserialization based on __typename.

        For polymorphic types like BaseFile, the GraphQL response includes __typename
        to indicate the concrete type (ImageFile, VideoFile, etc.). This method
        resolves the correct type class to use for construction.

        Args:
            data: The GraphQL response data (must contain __typename)
            requested_type: The type used in the query (e.g., BaseFile)

        Returns:
            The concrete type class to use (e.g., ImageFile if __typename is "ImageFile")
        """
        typename = data.get("__typename")

        # If no __typename or it matches requested type, use requested type
        if not typename or typename == requested_type.__type_name__:
            return requested_type

        # Polymorphic type mapping for known cases
        # Import here to avoid circular imports
        from .types import BaseFile, ImageFile, VideoFile

        type_map: dict[str, type[StashObject]] = {
            "ImageFile": ImageFile,
            "VideoFile": VideoFile,
            "BaseFile": BaseFile,
        }

        concrete_type = type_map.get(typename)
        if concrete_type:
            return concrete_type  # type: ignore[return-value]

        # Fallback to requested type if we don't recognize the typename
        log.warning(
            f"Unknown __typename '{typename}' for {requested_type.__type_name__}, "
            f"using {requested_type.__type_name__}"
        )
        return requested_type

    @staticmethod
    def _get_query_name(entity_type: type[StashObject]) -> str:
        """Get the GraphQL query name for fetching this entity type.

        For most types, the query name is "find{TypeName}", but some types
        use different query names (e.g., BaseFile uses "findFile").

        Args:
            entity_type: The entity type to get query name for

        Returns:
            The GraphQL query name (e.g., "findFile", "findScene")
        """
        type_name = entity_type.__type_name__

        # Special cases where query name differs from type name
        query_name_map = {
            "BaseFile": "findFile",
        }

        return query_name_map.get(type_name, f"find{type_name}")

    @staticmethod
    def _is_independently_fetchable(entity_type: type[StashObject]) -> bool:
        """Check if an entity type can be fetched independently via find query.

        Args:
            entity_type: The entity type to check

        Returns:
            True if the type can be fetched independently (directly or polymorphically)
        """
        return StashEntityStore._get_fetchable_type(entity_type) is not None

    @staticmethod
    def _parse_nested_field(field_spec: str) -> list[str]:
        """Parse nested field specification into path components.

        Supports Django-style double-underscore syntax:
        - 'files__path' → ['files', 'path']
        - 'studio__parent__name' → ['studio', 'parent', 'name']
        - 'rating100' → ['rating100'] (single field)

        Args:
            field_spec: Field specification (e.g., 'files__path')

        Returns:
            List of field path components
        """
        return field_spec.split("__")

    def _check_nested_field_present(
        self, obj: StashObject, field_path: list[str]
    ) -> bool:
        """Check if a nested field path is fully populated (not UNSET).

        Args:
            obj: Root object to check
            field_path: List of field names forming the path (e.g., ['files', 'path'])

        Returns:
            True if the entire path is populated (no UNSET values)
        """
        from .types.unset import UnsetType

        if not field_path:
            return True

        # Check first field in path
        field_name = field_path[0]
        received = getattr(obj, "_received_fields", set())

        if field_name not in received:
            return False  # Field not loaded yet

        # Get the value
        if not hasattr(obj, field_name):
            return False

        value = getattr(obj, field_name)

        # If UNSET, not present
        if isinstance(value, UnsetType):
            return False

        # If None, consider it present (null is a valid value)
        if value is None:
            return True

        # If this is the last field in path, it's present
        if len(field_path) == 1:
            return True

        # Need to recurse into nested object(s)
        remaining_path = field_path[1:]

        if isinstance(value, list):
            # For lists, ALL items must have the nested field
            if not value:  # Empty list is considered present
                return True
            return all(
                isinstance(item, StashObject)
                and self._check_nested_field_present(item, remaining_path)
                for item in value
            )
        if isinstance(value, StashObject):
            # Single nested object
            return self._check_nested_field_present(value, remaining_path)
        # Scalar value - can't recurse further
        return len(remaining_path) == 0

    def missing_fields_nested(self, obj: StashObject, *field_specs: str) -> set[str]:
        """Check which nested field specifications are missing.

        Supports both simple and nested (Django-style) field specifications:
        - Simple: 'rating100', 'favorite'
        - Nested: 'files__path', 'studio__parent__name'

        Args:
            obj: Entity to check
            *field_specs: Field specifications to check

        Returns:
            Set of field specifications that are NOT fully populated

        Example:
            # Check if image has files loaded with path field
            missing = store.missing_fields_nested(
                image,
                'title',           # Simple field
                'files__path'      # Nested field
            )
            # Returns {'files__path'} if files.path is not loaded
        """
        missing = set()

        for field_spec in field_specs:
            field_path = self._parse_nested_field(field_spec)
            if not self._check_nested_field_present(obj, field_path):
                missing.add(field_spec)

        return missing

    async def populate(
        self,
        obj: T,
        fields: list[str] | set[str] | None = None,
        force_refetch: bool = False,
    ) -> T:
        """Populate specific fields on an entity using field-aware fetching.

        This method uses `_received_fields` tracking to determine which fields are
        genuinely missing and need to be fetched. All entities are treated as potentially
        incomplete.

        Supports nested field specifications using Django-style double-underscore syntax:
        - `'files__path'`: Populate files relationship, then path on each File
        - `'studio__parent__name'`: Populate studio, then parent, then name
        - Can be mixed with regular fields: `['rating100', 'files__path']`

        Args:
            obj: Entity to populate. Can be any StashObject, including nested objects
                 like scene.studio or scene.performers[0].
            fields: Fields to populate. Supports both regular field names ('studio')
                   and nested field specifications ('studio__parent__name').
                   If None and force_refetch=False, uses heuristics to determine
                   if object needs more data.
            force_refetch: If True, invalidates cache and re-fetches the specified fields
                          from the server, regardless of whether they're in _received_fields.

        Returns:
            The populated entity (may be a different instance if refetched from cache).

        Examples:
            # Populate specific fields on a scene
            scene = await store.populate(scene, fields=["studio", "performers"])

            # Populate nested fields using __ syntax
            image = await store.populate(image, fields=["files__path", "files__size"])

            # Mix regular and nested fields
            scene = await store.populate(
                scene, fields=["rating100", "studio__parent__name"]
            )

            # Populate nested object directly (identity map pattern)
            scene.studio = await store.populate(scene.studio, fields=["urls", "details"])

            # Force refresh from server (invalidates cache first)
            scene = await store.populate(scene, fields=["studio"], force_refetch=True)

            # Populate performer from a list
            performer = await store.populate(
                scene.performers[0], fields=["scenes", "images"]
            )

            # Check what's missing before populating
            missing = store.missing_fields(scene.studio, "urls", "details", "aliases")
            if missing:
                scene.studio = await store.populate(scene.studio, fields=list(missing))
        """
        # Normalize fields to a set
        if fields is None:
            fields_set: set[str] = set()
        elif isinstance(fields, list):
            fields_set = set(fields)
        else:
            fields_set = fields

        # Separate regular fields from nested field specifications
        regular_fields: set[str] = set()
        nested_specs: dict[
            str, set[list[str]]
        ] = {}  # root_field -> set of remaining paths

        for field_spec in fields_set:
            if "__" in field_spec:
                # Parse nested field: 'files__path' -> ['files', 'path']
                path = self._parse_nested_field(field_spec)
                root = path[0]
                remaining = path[1:]

                # Track the nested path for later processing
                if root not in nested_specs:
                    nested_specs[root] = set()
                # Store as tuple so it's hashable for set
                nested_specs[root].add(tuple(remaining))

                # Also need to fetch the root field
                regular_fields.add(root)
            else:
                # Regular field
                regular_fields.add(field_spec)

        # For the rest of the method, work with regular_fields
        # (nested specs will be handled after root fields are populated)
        fields_set = regular_fields

        # Get currently received fields
        received: set[str] = getattr(obj, "_received_fields", set())

        # Determine which fields genuinely need fetching
        if force_refetch:
            # Force refetch all requested fields - invalidate cache first
            fields_to_fetch = list(fields_set) if fields_set else []
            if fields_to_fetch:
                self.invalidate(type(obj), obj.id)
        else:
            # Only fetch fields not already in _received_fields
            fields_to_fetch = [f for f in fields_set if f not in received]

            # Validate that the fields exist on the model
            for field_name in list(fields_to_fetch):
                if not hasattr(obj, field_name):
                    log.warning(f"{obj.__type_name__} has no field '{field_name}'")
                    fields_to_fetch.remove(field_name)

        # If we have fields to fetch, get fresh data with those fields
        if fields_to_fetch:
            log.debug(
                f"Populating {obj.__type_name__} {obj.id} with fields: {fields_to_fetch}"
            )
            # For polymorphic types (ImageFile, VideoFile), fetch as base type (BaseFile)
            fetch_type = self._get_fetchable_type(type(obj)) or type(obj)
            fresh_obj = await self.get(fetch_type, obj.id, fields=fields_to_fetch)
            if fresh_obj is not None:
                # Merge received fields: keep old + add new
                new_received = received | getattr(fresh_obj, "_received_fields", set())
                object.__setattr__(fresh_obj, "_received_fields", new_received)
                obj = fresh_obj  # type: ignore[assignment]

        # Save merged received fields before processing nested objects
        final_received: set[str] = getattr(obj, "_received_fields", set())

        # Only populate nested objects if we actually fetched new data or if in heuristic mode
        # If user specified fields and they're already present, don't deep-populate nested objects
        should_populate_nested = bool(fields_to_fetch) or not fields_set

        if should_populate_nested:
            # Now populate any nested StashObject relationships
            for field_name in fields_set if fields_set else []:
                if not hasattr(obj, field_name):
                    continue

                value = getattr(obj, field_name)

                if value is None:
                    continue

                if isinstance(value, list):
                    # List of objects -> ensure they're cached/populated
                    populated_list = await self._populate_list(value, force_refetch)
                    setattr(obj, field_name, populated_list)
                elif isinstance(value, StashObject):
                    # Single object -> ensure it's cached/populated
                    populated_single = await self._populate_single(value, force_refetch)
                    if populated_single is not None:
                        setattr(obj, field_name, populated_single)

        # Handle nested field specifications (e.g., 'files__path')
        # This runs after root fields are populated, allowing recursive descent
        if nested_specs:
            for root_field, path_tuples in nested_specs.items():
                if not hasattr(obj, root_field):
                    log.warning(
                        f"{obj.__type_name__} has no field '{root_field}' "
                        f"(from nested spec)"
                    )
                    continue

                value = getattr(obj, root_field)

                if value is None:
                    continue

                # For each remaining path (e.g., ['path'], ['size'])
                for path_tuple in path_tuples:
                    remaining_path = list(path_tuple)  # Convert back to list

                    # Build the field spec for recursive call
                    # If remaining_path is ['path'], field_spec is 'path'
                    # If remaining_path is ['parent', 'name'], field_spec is 'parent__name'
                    nested_field_spec = "__".join(remaining_path)

                    if isinstance(value, list):
                        # Populate each item in the list with the remaining path
                        for item in value:
                            if isinstance(item, StashObject):
                                # Skip types that can only be fetched via their parent
                                # (e.g., ImageFile, PluginTask, PluginPaths)
                                # The parent query should have already included these fields
                                if not self._is_independently_fetchable(type(item)):
                                    continue
                                await self.populate(
                                    item,
                                    fields=[nested_field_spec],
                                    force_refetch=force_refetch,
                                )
                    elif isinstance(
                        value, StashObject
                    ) and self._is_independently_fetchable(type(value)):
                        # Populate single object with the remaining path
                        # (skips types that can only be fetched via their parent)
                        await self.populate(
                            value,
                            fields=[nested_field_spec],
                            force_refetch=force_refetch,
                        )

        # Restore received fields after nested processing (setattr might have changed them)
        object.__setattr__(obj, "_received_fields", final_received)

        return obj

    async def _populate_single(
        self, obj: StashObject, force_refetch: bool = False
    ) -> StashObject | None:
        """Populate a single object by fetching from cache/GraphQL.

        Always attempts to get a fuller version from cache/GraphQL, treating
        all objects as potentially incomplete.
        """
        if force_refetch or self._needs_population(obj):
            # Use get() with fields=[] to bypass cache and fetch, but identity map will merge into cached object
            return await self.get(type(obj), obj.id, fields=[])
        return obj

    async def _populate_list(
        self, objects: list[Any], force_refetch: bool = False
    ) -> list[Any]:
        """Populate a list of objects by fetching from cache/GraphQL."""
        if not objects:
            return objects

        # Check if first item is a StashObject
        if not isinstance(objects[0], StashObject):
            return objects

        entity_type = type(objects[0])

        # Collect IDs that need fetching and fetch them individually to bypass cache
        # Using get() with fields=[] bypasses cache but identity map still merges
        ids_to_fetch = [
            obj.id for obj in objects if force_refetch or self._needs_population(obj)
        ]

        if ids_to_fetch:
            # Fetch each object individually with fields=[] to bypass cache
            for obj_id in ids_to_fetch:
                await self.get(entity_type, obj_id, fields=[])

        # Return populated list from cache (identity map updated the cached objects)
        result = []
        for obj in objects:
            cached = await self.get(type(obj), obj.id)
            result.append(cached if cached is not None else obj)

        return result

    def _needs_population(
        self, obj: StashObject, fields: set[str] | None = None
    ) -> bool:
        """Check if an object needs more data loaded.

        Uses `_received_fields` tracking when available for precise detection,
        falling back to heuristics for objects not created through this store.

        Args:
            obj: Entity to check
            fields: Optional specific fields to check. If provided, returns True
                   if ANY of these fields are missing from _received_fields.
                   If None, uses heuristic based on received field count.

        Returns:
            True if the object likely needs population.
        """
        received = getattr(obj, "_received_fields", None)

        if received is not None:
            # Precise detection using field tracking
            if fields is not None:
                # Check if any requested fields are missing
                return bool(fields - received)
            # Heuristic: if only got basic fields, needs more data
            # Consider "incomplete" if received <= 2 fields (just id + name/title)
            return len(received) <= 2
        # Fallback heuristic for objects without field tracking
        model_dump = obj.model_dump(exclude_defaults=True)
        non_id_fields = {
            k for k in model_dump if k not in ("id", "created_at", "updated_at")
        }
        return len(non_id_fields) <= 1  # id + maybe name

    def has_fields(self, obj: StashObject, *fields: str) -> bool:
        """Check if an object has specific fields populated.

        Uses `_received_fields` tracking when available.

        Args:
            obj: Entity to check
            *fields: Field names to check for

        Returns:
            True if ALL specified fields are in _received_fields
        """
        received: set[str] = getattr(obj, "_received_fields", set())
        return all(f in received for f in fields)

    def missing_fields(self, obj: StashObject, *fields: str) -> set[str]:
        """Get which of the specified fields are missing from an object.

        Args:
            obj: Entity to check
            *fields: Field names to check

        Returns:
            Set of field names that are NOT in _received_fields
        """
        received: set[str] = getattr(obj, "_received_fields", set())
        return set(fields) - received

    # ─── Cache control ────────────────────────────────────────

    def invalidate(self, entity_type: type[T], entity_id: str) -> None:
        """Remove specific object from cache (thread-safe).

        Args:
            entity_type: The Stash entity type
            entity_id: Entity ID to invalidate
        """
        type_name = entity_type.__type_name__
        cache_key = (type_name, entity_id)
        with self._lock:
            if cache_key in self._cache:
                del self._cache[cache_key]
                log.debug(f"Invalidated: {type_name} {entity_id}")

    def invalidate_type(self, entity_type: type[T]) -> None:
        """Remove all objects of a type from cache (thread-safe).

        Args:
            entity_type: The Stash entity type to clear
        """
        type_name = entity_type.__type_name__
        with self._lock:
            keys_to_delete = [key for key in self._cache if key[0] == type_name]
            for key in keys_to_delete:
                del self._cache[key]
        log.debug(f"Invalidated all {type_name}: {len(keys_to_delete)} entries")

    def invalidate_all(self) -> None:
        """Clear entire cache (thread-safe)."""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
        log.debug(f"Invalidated all cache: {count} entries")

    def set_ttl(self, entity_type: type[T], ttl: timedelta | None) -> None:
        """Set TTL for a type. None = use default (or never expire if no default).

        Args:
            entity_type: The Stash entity type
            ttl: TTL for this type, or None to use default
        """
        type_name = entity_type.__type_name__
        self._type_ttls[type_name] = ttl
        log.debug(f"Set TTL for {type_name}: {ttl}")

    # ─── Object lifecycle management ──────────────────────────

    def add(self, obj: StashObject) -> None:
        """Add object to cache (for new objects with temp UUIDs).

        This is typically used with objects created via ClassName.new()
        that have temporary UUID IDs. After calling obj.save() or store.save(),
        the cache entry will be updated with the real ID from Stash.

        Args:
            obj: Object to cache (usually created with .new())

        Example:
            ```python
            # Create new tag with temp UUID
            tag = Tag.new(name="Action")

            # Cache it
            store.add(tag)

            # Save to Stash (updates ID and cache)
            await store.save(tag)
            # OR: await tag.save(client) + manual cache update
            ```
        """
        self._cache_entity(obj)
        log.debug(f"Added {obj.__type_name__} {obj.id} to cache")

    async def save(self, obj: StashObject, _cascade_depth: int = 0) -> None:
        """Save object to Stash and update cache.

        Handles both new objects (create) and existing objects (update).
        For new objects, updates cache key from temp UUID to real Stash ID.

        Automatically cascades saves for unsaved related objects (with warning).
        Preferred pattern: explicitly save related objects before parent.

        Args:
            obj: Object to save
            _cascade_depth: Internal tracking for cascade recursion depth

        Raises:
            ValueError: If save fails or object has unsaved UUIDs after cascade

        Example:
            ```python
            # Create and save new tag
            tag = Tag.new(name="Action")
            store.add(tag)  # Cache with temp UUID
            await store.save(tag)  # Save to Stash, update cache with real ID

            # Modify existing tag
            tag.description = "Action movies"
            await store.save(tag)  # Update in Stash

            # With related objects (auto-cascade with warning)
            scene.performers.append(new_performer)  # new_performer has UUID
            await store.save(scene)  # Warns, cascades save(new_performer), then saves scene

            # Preferred pattern: explicit saves
            await store.save(new_performer)  # Gets real ID
            scene.performers.append(new_performer)  # Has real ID
            await store.save(scene)  # No cascade needed
            ```
        """
        # Check for unsaved related objects (have UUIDs, not real Stash IDs)
        unsaved_related = self._find_unsaved_related_objects(obj)

        # If cascading, warn about anti-pattern (like deprecation warning)
        if unsaved_related and _cascade_depth == 0:
            unsaved_desc = ", ".join(
                f"{o.__type_name__}({o.id[:8]}...)" for o in unsaved_related[:3]
            )
            if len(unsaved_related) > 3:
                unsaved_desc += f" and {len(unsaved_related) - 3} more"
            log.warning(
                f"Cascading save for unsaved related object(s): {unsaved_desc}. "
                f"This pattern is deprecated. Preferred: explicitly save related objects "
                f"before saving parent (e.g., 'await store.save(performer); await store.save(scene)'). "
                f"Auto-cascade may be removed in future versions."
            )

            # Cascade save unsaved related objects
            for related_obj in unsaved_related:
                log.debug(
                    f"Cascade saving {related_obj.__type_name__} {related_obj.id}"
                )
                await self.save(related_obj, _cascade_depth=_cascade_depth + 1)

        # Capture old state BEFORE save modifies the object
        was_new = getattr(obj, "_is_new", False)
        old_id = obj.id

        # Save to Stash (this will call obj.save() which updates obj.id via update_id())
        await obj.save(self._client)

        # After save, verify no UUIDs remain in related objects
        if was_new:
            remaining_unsaved = self._find_unsaved_related_objects(obj)
            if remaining_unsaved:
                unsaved_desc = ", ".join(
                    f"{o.__type_name__}({o.id})" for o in remaining_unsaved[:3]
                )
                raise StashIntegrationError(
                    f"Cannot save {obj.__type_name__} {obj.id}: related objects still have UUIDs "
                    f"after cascade: {unsaved_desc}. This indicates cascade failed."
                )

        # If it was a new object, update cache key from temp UUID to real ID (thread-safe)
        if was_new and old_id != obj.id:
            old_key = (obj.__type_name__, old_id)
            new_key = (obj.__type_name__, obj.id)

            with self._lock:
                if old_key in self._cache:
                    # Add new key FIRST (both keys point to same object during transition)
                    entry = self._cache[old_key]
                    self._cache[new_key] = entry
                    log.debug(
                        f"Added new cache key: {obj.__type_name__} {obj.id} (old: {old_id[:8]}...)"
                    )

                    # Now remove old UUID key
                    del self._cache[old_key]
                    log.debug(
                        f"Removed old cache key: {obj.__type_name__} {old_id[:8]}..."
                    )
                else:
                    # Not in cache - add it now with real ID
                    self._cache_entity(obj)
                    log.debug(f"Cached {obj.__type_name__} {obj.id} after save")

    def _find_unsaved_related_objects(self, obj: StashObject) -> list[StashObject]:
        """Find related StashObjects that have UUID IDs (unsaved).

        Scans relationship fields on the object to find any related objects
        that have UUIDs instead of real Stash IDs, indicating they haven't
        been saved to Stash yet.

        Args:
            obj: Object to scan for unsaved related objects

        Returns:
            List of unsaved StashObject instances
        """
        unsaved: list[StashObject] = []

        # Check all relationship fields defined in __relationships__
        relationships = getattr(obj.__class__, "__relationships__", {})
        for field_name in relationships:
            if not hasattr(obj, field_name):
                continue

            value = getattr(obj, field_name)
            if value is None:
                continue

            if isinstance(value, list):
                # List of objects
                unsaved.extend(
                    item
                    for item in value
                    if isinstance(item, StashObject) and self._is_uuid(item.id)
                )
            elif isinstance(value, StashObject) and self._is_uuid(value.id):
                # Single object
                unsaved.append(value)

        return unsaved

    def _is_uuid(self, id_str: str) -> bool:
        """Check if an ID string is a UUID (32 hex chars).

        Args:
            id_str: ID string to check

        Returns:
            True if it's a UUID format (32 hex digits)
        """
        # UUIDs generated by uuid.uuid4().hex are 32 hexadecimal characters
        # Real Stash IDs are typically numeric strings like "123", "456"
        if len(id_str) != 32:
            return False
        try:
            int(id_str, 16)  # Valid hex string?
            return True
        except ValueError:
            return False

    # ─── Get-or-Create ────────────────────────────────────────

    async def get_or_create(
        self, entity_type: type[T], create_if_missing: bool = True, **search_params: Any
    ) -> T:
        """Get entity by search criteria, optionally create if not found.

        Searches for an entity matching the provided criteria. If found, returns
        the existing entity (from cache or fetched). If not found and create_if_missing
        is True, creates a new entity with the search params as initial data.

        Note: New entities are created with UUID IDs and are NOT automatically saved.
        Call store.save() or entity.save() to persist to Stash.

        Args:
            entity_type: The Stash entity type
            create_if_missing: If True, creates new entity if not found. Default: True.
            **search_params: Search criteria (also used as creation data if not found)

        Returns:
            Existing or newly created entity

        Raises:
            ValueError: If not found and create_if_missing=False

        Example:
            ```python
            # Get existing or create new performer
            performer = await store.get_or_create(Performer, name="Alice")
            if performer._is_new:
                # New performer - save it
                await store.save(performer)

            # Link to scene
            scene.performers.append(performer)
            await store.save(scene)

            # Get existing, error if not found
            tag = await store.get_or_create(Tag, create_if_missing=False, name="Action")
            ```
        """
        # Try to find existing entity
        try:
            existing = await self.find_one(entity_type, **search_params)
            if existing is not None:
                log.debug(
                    f"get_or_create: found existing {entity_type.__type_name__} {existing.id}"
                )
                return existing
        except Exception as e:
            log.debug(f"get_or_create: find_one failed: {e}")
            # Continue to creation if allowed

        # Not found - create if allowed
        if not create_if_missing:
            raise StashIntegrationError(
                f"{entity_type.__type_name__} not found with criteria: {search_params}"
            )

        # Create new entity with search params as initial data
        # Will get UUID ID and _is_new=True
        new_entity = entity_type(**search_params)
        log.debug(
            f"get_or_create: created new {entity_type.__type_name__} {new_entity.id} (unsaved)"
        )

        # Add to cache (with UUID key)
        self.add(new_entity)

        return new_entity

    # ─── Cache inspection ─────────────────────────────────────

    def is_cached(self, entity_type: type[T], entity_id: str) -> bool:
        """Check if object is in cache and not expired (thread-safe).

        Args:
            entity_type: The Stash entity type
            entity_id: Entity ID

        Returns:
            True if cached and not expired
        """
        type_name = entity_type.__type_name__
        cache_key = (type_name, entity_id)

        with self._lock:
            if cache_key not in self._cache:
                return False
            return not self._cache[cache_key].is_expired()

    def cache_stats(self) -> CacheStats:
        """Get cache statistics (thread-safe).

        Returns:
            CacheStats with total entries, by-type counts, and expired count
        """
        stats = CacheStats()

        with self._lock:
            stats.total_entries = len(self._cache)

            for (type_name, _), entry in self._cache.items():
                stats.by_type[type_name] = stats.by_type.get(type_name, 0) + 1
                if entry.is_expired():
                    stats.expired_count += 1

        return stats

    @property
    def cache_size(self) -> int:
        """Get number of entities in cache (deprecated, use cache_stats) (thread-safe).

        Returns:
            Number of cached entities
        """
        with self._lock:
            return len(self._cache)

    # ─── Internal helpers ─────────────────────────────────────

    def _cache_entity(self, entity: StashObject) -> None:
        """Add entity to cache with appropriate TTL (thread-safe)."""
        type_name = entity.__type_name__
        cache_key = (type_name, entity.id)

        # Determine TTL
        ttl = self._type_ttls.get(type_name, self._default_ttl)
        ttl_seconds = ttl.total_seconds() if ttl is not None else None

        with self._lock:
            self._cache[cache_key] = CacheEntry(
                entity=entity,
                cached_at=time.monotonic(),
                ttl_seconds=ttl_seconds,
            )

    def _get_ttl_for_type(self, type_name: str) -> timedelta | None:
        """Get TTL for a type, falling back to default."""
        return self._type_ttls.get(type_name, self._default_ttl)

    async def _fetch_with_fields(
        self, entity_type: type[T], entity_id: str, fields: list[str]
    ) -> T | None:
        """Fetch an entity with specific fields included in the query.

        Args:
            entity_type: The Stash entity type
            entity_id: Entity ID
            fields: List of field names to include in the query

        Returns:
            Entity if found, None otherwise
        """
        type_name = entity_type.__type_name__

        # Get the query name (may differ from type name for some types)
        query_name = self._get_query_name(entity_type)

        # Build field selection from requested fields
        field_selection = self._build_field_selection(fields)

        # Build the query
        query = f"""
            query Find{type_name}($id: ID!) {{
                {query_name}(id: $id) {{
                    {field_selection}
                }}
            }}
        """

        try:
            result = await self._client.execute(query, {"id": entity_id})
            data = result.get(query_name)
            if data:
                # Handle polymorphic types - check __typename BEFORE sanitization
                # (sanitize_model_data removes fields starting with _)
                concrete_type = self._get_concrete_type(data, entity_type)

                clean = sanitize_model_data(data)

                # Use Pydantic's from_graphql for deserialization (identity map via validator)
                entity = concrete_type.from_graphql(clean)
                self._cache_entity(entity)
                return entity
            return None
        except Exception as e:
            log.error(
                f"Failed to fetch {type_name} {entity_id} with fields {fields}: {e}"
            )
            return None

    def _build_field_selection(self, fields: list[str]) -> str:
        """Build GraphQL field selection string from field list.

        Handles both scalar fields and nested object/list fields by including
        appropriate sub-selections for relationships.

        Args:
            fields: List of field names

        Returns:
            GraphQL field selection string with nested selections for objects
        """
        # Always include __typename, id, and timestamps
        base_fields = ["__typename", "id", "created_at", "updated_at"]
        all_fields = list(set(base_fields + fields))

        # Map of relationship fields that need nested selections
        # Format: field_name -> nested fields to include
        relationship_fields = {
            # Common relationship fields across types
            "studio": "__typename id name",
            "parent_studio": "__typename id name",
            "parent": "__typename id name",
            "tags": "__typename id name",
            "performers": "__typename id name gender",
            "scenes": "__typename id title",
            "galleries": "__typename id title",
            "images": "__typename id title",
            "groups": "__typename id name",
            "scene_markers": "__typename id title",
            "stash_ids": "__typename endpoint stash_id",
            # File relationship fields (ImageFile, VideoFile, etc.)
            "files": "__typename id path size width height format fingerprints { __typename type value }",
            "visual_files": "__typename id path size width height format fingerprints { __typename type value }",
        }

        selections = []
        for field_name in all_fields:
            if field_name in relationship_fields:
                # Nested object/list - include sub-selection
                nested = relationship_fields[field_name]
                selections.append(f"{field_name} {{ {nested} }}")
            else:
                # Scalar field
                selections.append(field_name)

        return "\n                    ".join(selections)

    async def _execute_find(
        self,
        entity_type: type[T],
        filters: dict[str, Any],
        page: int,
        per_page: int,
    ) -> FindResult[T]:
        """Execute a find query against the GraphQL API.

        This method translates the filter kwargs to GraphQL filter format
        and executes the appropriate query.
        """
        type_name = entity_type.__type_name__

        # Translate filters to GraphQL format
        graphql_filter, entity_filter = self._translate_filters(type_name, filters)

        # Add pagination
        graphql_filter["page"] = page
        graphql_filter["per_page"] = per_page

        # Execute query based on entity type
        return await self._execute_find_query(
            entity_type, graphql_filter, entity_filter
        )

    async def _execute_find_by_ids(
        self, entity_type: type[T], ids: list[str]
    ) -> list[T]:
        """Fetch multiple entities by their IDs.

        Note: Currently fetches individually. Could be optimized with batch queries
        using findScenes/findPerformers with id filter, but this requires careful
        handling of pagination and result ordering.
        """
        results = []
        for eid in ids:
            entity = await entity_type.find_by_id(self._client, eid)
            if entity is not None:
                results.append(entity)
        return results

    def _translate_filters(
        self, type_name: str, filters: dict[str, Any]
    ) -> tuple[dict[str, Any], dict[str, Any] | None]:
        """Translate Django-style kwargs to GraphQL filter format.

        Args:
            type_name: Entity type name
            filters: Django-style filter kwargs

        Returns:
            Tuple of (FindFilterType dict, EntityFilterType dict or None)
        """
        graphql_filter: dict[str, Any] = {}
        entity_filter: dict[str, Any] = {}

        for key, value in filters.items():
            # Check if it's already a raw dict (pass through)
            if isinstance(value, dict) and "modifier" in value:
                entity_filter[key] = value
                continue

            # Check for nested filters (e.g., performers_filter)
            if key.endswith("_filter"):
                entity_filter[key] = value
                continue

            # Parse Django-style lookup
            field, modifier = self._parse_lookup(key)

            # Build criterion input
            criterion = self._build_criterion(field, modifier, value)

            if criterion is not None:
                entity_filter[field] = criterion

        return graphql_filter, entity_filter if entity_filter else None

    def _parse_lookup(self, key: str) -> tuple[str, str]:
        """Parse Django-style lookup into field and modifier.

        Examples:
            "title" -> ("title", "EQUALS")
            "title__contains" -> ("title", "INCLUDES")
            "rating100__gte" -> ("rating100", "GREATER_THAN")
        """
        lookup_map = {
            "contains": "INCLUDES",
            "icontains": "INCLUDES",  # Case-insensitive not directly supported
            "exact": "EQUALS",
            "iexact": "EQUALS",
            "regex": "MATCHES_REGEX",
            "iregex": "MATCHES_REGEX",
            "gt": "GREATER_THAN",
            "gte": "GREATER_THAN",  # GraphQL doesn't have >=, use > with value-1
            "lt": "LESS_THAN",
            "lte": "LESS_THAN",
            "between": "BETWEEN",
            "null": "IS_NULL",
            "notnull": "NOT_NULL",
            "in": "INCLUDES",
            "includes": "INCLUDES",
            "includes_all": "INCLUDES_ALL",
            "excludes": "EXCLUDES",
            "ne": "NOT_EQUALS",
            "not": "NOT_EQUALS",
        }

        if "__" in key:
            parts = key.rsplit("__", 1)
            field = parts[0]
            lookup = parts[1].lower()
            modifier = lookup_map.get(lookup, "EQUALS")
        else:
            field = key
            modifier = "EQUALS"

        return field, modifier

    def _build_criterion(
        self, field: str, modifier: str, value: Any
    ) -> dict[str, Any] | None:
        """Build a GraphQL criterion input from field, modifier, and value.

        Note: The INCLUDES modifier has different meanings for different field types:
        - String fields (path, title, aliases, url): INCLUDES = "contains substring" → single string
        - Multi-value fields (tags, performers, etc.): INCLUDES = "includes in list" → list of IDs

        IMPORTANT: Fields that are lists on entities but use StringCriterionInput for filtering
        (like aliases, urls, captions) should NOT be in multi_value_fields. They search for
        substring matches WITHIN the list items, not for ID membership.
        """
        # Multi-value relationship fields that expect lists of IDs
        # These use MultiCriterionInput or HierarchicalMultiCriterionInput for filtering.
        # Do NOT include string list fields (aliases, urls, captions) which use StringCriterionInput.
        multi_value_fields = {
            # Core entity relationship filters (MultiCriterionInput)
            "performers",
            "galleries",
            "images",
            "scenes",
            # Hierarchical entity relationship filters (HierarchicalMultiCriterionInput)
            "tags",
            "studios",
            "groups",
            "performer_tags",
            # Hierarchical parent/child filters (map to 'parents'/'children' in filter types)
            "parent_tags",
            "child_tags",
            "parent_studios",
        }

        if modifier == "IS_NULL":
            if value:
                return {"value": "", "modifier": "IS_NULL"}
            return {"value": "", "modifier": "NOT_NULL"}

        if modifier == "BETWEEN":
            if isinstance(value, (list, tuple)) and len(value) == 2:
                return {
                    "value": value[0],
                    "value2": value[1],
                    "modifier": "BETWEEN",
                }
            return None

        if modifier in ("INCLUDES", "INCLUDES_ALL", "EXCLUDES"):
            # Check if this is a multi-value field (expects list) or string field (expects single value)
            if field in multi_value_fields:
                # Multi-value criterion (tags, performers, etc.) - wrap in list
                if isinstance(value, (list, tuple)):
                    return {"value": list(value), "modifier": modifier}
                return {"value": [value], "modifier": modifier}
            # String criterion (path, title, etc.) - keep as single value
            # For StringCriterionInput, INCLUDES means "contains substring"
            return {"value": value, "modifier": modifier}

        # Standard criterion
        return {"value": value, "modifier": modifier}

    async def _execute_find_query(
        self,
        entity_type: type[T],
        graphql_filter: dict[str, Any],
        entity_filter: dict[str, Any] | None,
    ) -> FindResult[T]:
        """Execute the actual GraphQL find query."""
        type_name = entity_type.__type_name__

        # Map type names to their query info
        query_map: dict[str, tuple[str, str, str]] = {
            "Scene": (
                fragments.FIND_SCENES_QUERY,
                "findScenes",
                "scene_filter",
            ),
            "Performer": (
                fragments.FIND_PERFORMERS_QUERY,
                "findPerformers",
                "performer_filter",
            ),
            "Studio": (
                fragments.FIND_STUDIOS_QUERY,
                "findStudios",
                "studio_filter",
            ),
            "Tag": (
                fragments.FIND_TAGS_QUERY,
                "findTags",
                "tag_filter",
            ),
            "Gallery": (
                fragments.FIND_GALLERIES_QUERY,
                "findGalleries",
                "gallery_filter",
            ),
            "Image": (
                fragments.FIND_IMAGES_QUERY,
                "findImages",
                "image_filter",
            ),
        }

        if type_name not in query_map:
            raise ValueError(f"Unsupported entity type: {type_name}")

        query, result_key, filter_key = query_map[type_name]

        # Build variables
        variables: dict[str, Any] = {"filter": graphql_filter}
        if entity_filter:
            variables[filter_key] = entity_filter

        # Execute query
        result = await self._client.execute(query, variables)

        # Parse result
        data = result.get(result_key, {})
        count = data.get("count", 0)

        # Get items key (pluralized type name, lowercase)
        items_key = type_name.lower() + "s"
        if type_name == "Gallery":
            items_key = "galleries"
        elif type_name == "Image":
            items_key = "images"

        raw_items = data.get(items_key, [])

        # Convert to entity objects using Pydantic's from_graphql (identity map via validator)
        items: list[T] = []
        for raw in raw_items:
            clean = sanitize_model_data(raw)
            entity = entity_type.from_graphql(clean)
            # Cache the entity
            self._cache_entity(entity)
            items.append(entity)

        return FindResult(
            items=items,
            count=count,
            page=graphql_filter.get("page", 1),
            per_page=graphql_filter.get("per_page", self.DEFAULT_QUERY_BATCH),
        )
