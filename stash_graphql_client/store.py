"""Entity store with read-through caching for Stash entities.

This module provides an in-memory identity map with caching, lazy loading,
and query capabilities for Stash GraphQL entities.
"""

from __future__ import annotations

import time
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass, field
from datetime import timedelta
from typing import TYPE_CHECKING, Any, TypeVar

from .errors import StashError
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

    Provides caching, lazy loading, and query capabilities for Stash GraphQL
    entities. All fetched entities are cached, and subsequent requests for
    the same entity return the cached version (if not expired).

    Example:
        ```python
        async with StashContext(conn=...) as client:
            store = StashEntityStore(client)

            # Get by ID (cache miss -> fetch, then cached)
            performer = await store.get(Performer, "123")

            # Search (always queries GraphQL, caches results)
            scenes = await store.find(Scene, title__contains="interview")

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

    # ─── Read-through by ID ───────────────────────────────────

    async def get(self, entity_type: type[T], entity_id: str) -> T | None:
        """Get entity by ID. Checks cache first, fetches if missing/expired.

        Args:
            entity_type: The Stash entity type (e.g., Performer, Scene)
            entity_id: Entity ID

        Returns:
            Entity if found, None otherwise
        """
        type_name = entity_type.__type_name__
        cache_key = (type_name, entity_id)

        # Check cache
        if cache_key in self._cache:
            entry = self._cache[cache_key]
            if not entry.is_expired():
                log.debug(f"Cache hit: {type_name} {entity_id}")
                return entry.entity  # type: ignore[return-value]
            log.debug(f"Cache expired: {type_name} {entity_id}")
            del self._cache[cache_key]

        # Cache miss - fetch from GraphQL
        log.debug(f"Cache miss: {type_name} {entity_id}")
        entity = await entity_type.find_by_id(self._client, entity_id)

        if entity is not None:
            self._cache_entity(entity)

        return entity

    async def get_many(self, entity_type: type[T], ids: list[str]) -> list[T]:
        """Batch get entities. Returns cached + fetches missing in single query.

        Args:
            entity_type: The Stash entity type
            ids: List of entity IDs

        Returns:
            List of found entities (order not guaranteed)
        """
        type_name = entity_type.__type_name__
        results: list[T] = []
        missing_ids: list[str] = []

        # Check cache for each ID
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

        # Fetch missing IDs
        if missing_ids:
            log.debug(f"Fetching {len(missing_ids)} missing {type_name} entities")
            # Use find with ID filter for batch fetch
            fetched = await self._execute_find_by_ids(entity_type, missing_ids)
            for entity in fetched:
                self._cache_entity(entity)
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
        """Filter cached objects with Python lambda. No network call.

        Args:
            entity_type: The Stash entity type
            predicate: Function that returns True for matching entities

        Returns:
            List of matching cached entities
        """
        type_name = entity_type.__type_name__
        results: list[T] = []

        for (cached_type, _), entry in self._cache.items():
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

    # ─── Stub population ──────────────────────────────────────

    async def populate(self, obj: T, *fields: str) -> T:
        """Populate stub relationships with full objects from cache/GraphQL.

        When GraphQL returns nested objects as stubs (e.g., {id: "1"}), this
        method fetches the full objects and replaces the stubs.

        Args:
            obj: Entity with stub relationships
            *fields: Field names to populate (e.g., "performers", "studio", "tags")

        Returns:
            The same entity with populated relationships

        Example:
            scene = await store.get(Scene, "1")
            scene = await store.populate(scene, "performers", "studio", "tags")
            # scene.performers now contains full Performer objects
        """
        for field_name in fields:
            if not hasattr(obj, field_name):
                log.warning(f"{obj.__type_name__} has no field '{field_name}'")
                continue

            value = getattr(obj, field_name)

            if value is None:
                continue

            if isinstance(value, list):
                # List of stubs -> list of full objects
                populated_list = await self._populate_list(value)
                setattr(obj, field_name, populated_list)
            elif isinstance(value, StashObject):
                # Single stub -> full object
                populated_single = await self._populate_single(value)
                if populated_single is not None:
                    setattr(obj, field_name, populated_single)

        return obj

    async def _populate_single(self, stub: StashObject) -> StashObject | None:
        """Populate a single stub object."""
        # Check if it's actually a stub (only has id, minimal other fields)
        if self._is_stub(stub):
            return await self.get(type(stub), stub.id)
        return stub

    async def _populate_list(self, stubs: list[Any]) -> list[Any]:
        """Populate a list of stub objects."""
        if not stubs:
            return stubs

        # Check if first item is a StashObject
        if not isinstance(stubs[0], StashObject):
            return stubs

        # Collect IDs of stubs that need fetching
        entity_type = type(stubs[0])
        stub_ids = [s.id for s in stubs if self._is_stub(s)]

        if stub_ids:
            # Batch fetch all stubs
            await self.get_many(entity_type, stub_ids)

        # Return populated list from cache
        result = []
        for stub in stubs:
            cached = await self.get(type(stub), stub.id)
            result.append(cached if cached is not None else stub)

        return result

    def _is_stub(self, obj: StashObject) -> bool:
        """Check if an object is a stub (minimal data, needs population).

        A stub typically only has 'id' and maybe a few other fields populated,
        while most fields are at their default values.
        """
        # Get non-default fields
        model_dump = obj.model_dump(exclude_defaults=True)
        # If only 'id' (and maybe timestamps), it's likely a stub
        non_id_fields = {
            k for k in model_dump if k not in ("id", "created_at", "updated_at")
        }
        return len(non_id_fields) <= 1  # id + maybe name

    # ─── Cache control ────────────────────────────────────────

    def invalidate(self, entity_type: type[T], entity_id: str) -> None:
        """Remove specific object from cache.

        Args:
            entity_type: The Stash entity type
            entity_id: Entity ID to invalidate
        """
        type_name = entity_type.__type_name__
        cache_key = (type_name, entity_id)
        if cache_key in self._cache:
            del self._cache[cache_key]
            log.debug(f"Invalidated: {type_name} {entity_id}")

    def invalidate_type(self, entity_type: type[T]) -> None:
        """Remove all objects of a type from cache.

        Args:
            entity_type: The Stash entity type to clear
        """
        type_name = entity_type.__type_name__
        keys_to_delete = [key for key in self._cache if key[0] == type_name]
        for key in keys_to_delete:
            del self._cache[key]
        log.debug(f"Invalidated all {type_name}: {len(keys_to_delete)} entries")

    def invalidate_all(self) -> None:
        """Clear entire cache."""
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

    # ─── Cache inspection ─────────────────────────────────────

    def is_cached(self, entity_type: type[T], entity_id: str) -> bool:
        """Check if object is in cache and not expired.

        Args:
            entity_type: The Stash entity type
            entity_id: Entity ID

        Returns:
            True if cached and not expired
        """
        type_name = entity_type.__type_name__
        cache_key = (type_name, entity_id)

        if cache_key not in self._cache:
            return False

        return not self._cache[cache_key].is_expired()

    def cache_stats(self) -> CacheStats:
        """Get cache statistics.

        Returns:
            CacheStats with total entries, by-type counts, and expired count
        """
        stats = CacheStats()
        stats.total_entries = len(self._cache)

        for (type_name, _), entry in self._cache.items():
            stats.by_type[type_name] = stats.by_type.get(type_name, 0) + 1
            if entry.is_expired():
                stats.expired_count += 1

        return stats

    # ─── Internal helpers ─────────────────────────────────────

    def _cache_entity(self, entity: StashObject) -> None:
        """Add entity to cache with appropriate TTL."""
        type_name = entity.__type_name__
        cache_key = (type_name, entity.id)

        # Determine TTL
        ttl = self._type_ttls.get(type_name, self._default_ttl)
        ttl_seconds = ttl.total_seconds() if ttl is not None else None

        self._cache[cache_key] = CacheEntry(
            entity=entity,
            cached_at=time.monotonic(),
            ttl_seconds=ttl_seconds,
        )

    def _get_ttl_for_type(self, type_name: str) -> timedelta | None:
        """Get TTL for a type, falling back to default."""
        return self._type_ttls.get(type_name, self._default_ttl)

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
        """Fetch multiple entities by their IDs."""
        # For now, fetch individually (batch not supported uniformly by all types)
        # TODO: Optimize with batch queries where supported
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
        """Build a GraphQL criterion input from field, modifier, and value."""
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
            # Multi-value criterion
            if isinstance(value, (list, tuple)):
                return {"value": list(value), "modifier": modifier}
            return {"value": [value], "modifier": modifier}

        # Standard criterion
        return {"value": value, "modifier": modifier}

    async def _execute_find_query(
        self,
        entity_type: type[T],
        graphql_filter: dict[str, Any],
        entity_filter: dict[str, Any] | None,
    ) -> FindResult[T]:
        """Execute the actual GraphQL find query."""
        from . import fragments
        from .client.utils import sanitize_model_data

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

        # Convert to entity objects
        items: list[T] = []
        for raw in raw_items:
            clean = sanitize_model_data(raw)
            items.append(entity_type(**clean))

        return FindResult(
            items=items,
            count=count,
            page=graphql_filter.get("page", 1),
            per_page=graphql_filter.get("per_page", self.DEFAULT_QUERY_BATCH),
        )
