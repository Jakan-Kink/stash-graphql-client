# Advanced Filtering with Field-Aware Repository

The `StashEntityStore` provides advanced filtering methods that combine local caching with smart field-level population. These methods enable high-performance queries by minimizing network traffic while ensuring data completeness.

## Overview

The advanced filtering system builds on the [UNSET Pattern](unset-pattern.md) and [Identity Map](../architecture/identity-map.md) to provide:

- **Field-level granularity**: Track which fields are loaded vs unqueried
- **Smart population**: Automatically fetch only missing fields
- **Local filtering**: Query cached data without network calls
- **Fail-fast validation**: Ensure required fields are present before filtering

## Method Comparison

| Method                             | Network Calls           | Returns            | Use Case                          |
| ---------------------------------- | ----------------------- | ------------------ | --------------------------------- |
| `filter()`                         | Never                   | `list[T]`          | Fast local query (existing)       |
| `filter_strict()`                  | Never                   | `list[T]`          | Fail-fast if fields missing       |
| `filter_and_populate()`            | Only for missing fields | `list[T]`          | Smart hybrid (main workhorse)     |
| `filter_and_populate_with_stats()` | Only for missing fields | `(list[T], dict)`  | Performance debugging             |
| `populated_filter_iter()`          | Only for missing fields | `AsyncIterator[T]` | Large datasets, early exit        |
| `find()`                           | Always                  | `list[T]`          | Fresh data from server (existing) |

## `filter_strict()` - Fail-Fast Filtering

Filters cached objects, raising an error if any required fields are missing. Useful when you MUST have complete data.

### Signature

```python
def filter_strict(
    self,
    entity_type: type[T],
    required_fields: set[str] | list[str],
    predicate: Callable[[T], bool],
) -> list[T]:
```

### Example

```python
from stash_graphql_client import StashContext, Performer

async with StashContext(conn=conn) as context:
    store = context.store

    # Pre-populate cache with find()
    await store.find(Performer, favorite=True)

    # Strict filtering - raises if any performer missing rating100
    try:
        high_rated = store.filter_strict(
            Performer,
            required_fields=['rating100', 'favorite'],
            predicate=lambda p: p.rating100 >= 80 and p.favorite
        )
        print(f"Found {len(high_rated)} high-rated favorites")
    except ValueError as e:
        # "Performer 123 is missing required fields: {'rating100'}"
        print(f"Cache incomplete: {e}")
        # Fix: warm cache with missing fields
        await store.find(Performer, favorite=True)  # Re-fetch with all fields
```

### When to Use

- **Data validation**: Ensure cache is complete before processing
- **Debugging**: Identify incomplete cache population
- **Critical operations**: Operations that require guaranteed field presence

## `filter_and_populate()` - Smart Hybrid Filtering

The main workhorse method. Filters cached objects, automatically fetching missing fields as needed. Much faster than `find()` when most data is cached.

### Signature

```python
async def filter_and_populate(
    self,
    entity_type: type[T],
    required_fields: set[str] | list[str],
    predicate: Callable[[T], bool],
    batch_size: int = 50,
) -> list[T]:
```

### Example

```python
from stash_graphql_client import StashContext, Performer

async with StashContext(conn=conn) as context:
    store = context.store

    # Day 1: User browses performers (basic info only)
    async for performer in store.find_iter(Performer, query_batch=100):
        # Cache now has 5000 performers with: id, name, gender
        # But rating100, favorite, scenes are UNSET
        display_in_ui(performer)

    # Day 2: User wants to filter by rating (cache is partial)
    high_rated = await store.filter_and_populate(
        Performer,
        required_fields=['rating100', 'favorite'],
        predicate=lambda p: p.rating100 >= 80 and p.favorite
    )
    # ✓ Only fetches rating100+favorite for the 5000 performers
    # ✓ Much smaller payload than re-fetching full performer data
    # ✓ Results: All matching performers with complete data
```

### Performance Benefits

**Scenario**: Cache has 1000 performers with basic info, need to filter by `rating100`

| Approach                | Network Payload | Time           | Description                   |
| ----------------------- | --------------- | -------------- | ----------------------------- |
| `find()`                | ~500KB          | ~500ms         | Re-fetch all 1000 × full data |
| `filter_and_populate()` | ~50KB           | ~50ms          | Fetch 1000 × 1 field only     |
| **Speedup**             | **10x smaller** | **10x faster** | Field-level fetching wins     |

### Batch Size Parameter

Controls how many entities are populated concurrently:

```python
# Default: 50 concurrent populates
results = await store.filter_and_populate(
    Performer,
    required_fields=['rating100'],
    predicate=lambda p: p.rating100 >= 80
)

# Smaller batches (gentler on server)
results = await store.filter_and_populate(
    Performer,
    required_fields=['rating100'],
    predicate=lambda p: p.rating100 >= 80,
    batch_size=10  # Only 10 concurrent requests
)
```

## `filter_and_populate_with_stats()` - Debug Variant

Same as `filter_and_populate()` but returns detailed statistics. Useful for performance optimization.

### Signature

```python
async def filter_and_populate_with_stats(
    self,
    entity_type: type[T],
    required_fields: set[str] | list[str],
    predicate: Callable[[T], bool],
    batch_size: int = 50,
) -> tuple[list[T], dict[str, Any]]:
```

### Example

```python
from stash_graphql_client import StashContext, Performer

async with StashContext(conn=conn) as context:
    store = context.store

    # Filter with statistics
    results, stats = await store.filter_and_populate_with_stats(
        Performer,
        required_fields=['rating100', 'favorite'],
        predicate=lambda p: p.rating100 >= 80 and p.favorite
    )

    # Analyze cache performance
    print(f"Total cached: {stats['total_cached']}")
    print(f"Needed population: {stats['needed_population']}")
    print(f"Cache hit rate: {stats['cache_hit_rate']:.1%}")
    print(f"Found matches: {stats['matches']}")

    # Example output:
    # Total cached: 1000
    # Needed population: 500
    # Cache hit rate: 50.0%
    # Found matches: 237
```

### Statistics Dictionary

```python
{
    "total_cached": 1000,           # Total objects in cache
    "needed_population": 500,       # How many needed fields fetched
    "populated_fields": ["rating100", "favorite"],  # Which fields
    "matches": 237,                 # How many matched predicate
    "cache_hit_rate": 0.5           # 50% had complete data
}
```

### When to Use

- **Performance analysis**: Identify cache inefficiencies
- **Optimization**: Determine if cache warming is needed
- **Debugging**: Understand why queries are slow

## `populated_filter_iter()` - Lazy Async Iterator

Lazy version of `filter_and_populate()` that yields results incrementally. Great for large datasets where you want to start processing immediately or can short-circuit early.

### Signature

```python
async def populated_filter_iter(
    self,
    entity_type: type[T],
    required_fields: set[str] | list[str],
    predicate: Callable[[T], bool],
    populate_batch: int = 50,
    yield_batch: int = 10,
) -> AsyncIterator[T]:
```

### Example: Early Exit

```python
from stash_graphql_client import StashContext, Performer

async with StashContext(conn=conn) as context:
    store = context.store

    # Find first 10 high-rated performers from 10,000 cached
    count = 0
    async for performer in store.populated_filter_iter(
        Performer,
        required_fields=['rating100', 'scenes'],
        predicate=lambda p: p.rating100 >= 90 and len(p.scenes) > 100,
        populate_batch=50,   # Fetch 50 at a time
        yield_batch=10       # Yield after processing each 10
    ):
        # Start processing immediately as matches are found
        await expensive_operation(performer)
        count += 1

        # Early exit - don't process all 10,000
        if count >= 10:
            break  # Only processed ~100-200 performers
```

### Example: Incremental Processing

```python
from stash_graphql_client import StashContext, Scene

async with StashContext(conn=conn) as context:
    store = context.store

    # Process large dataset incrementally
    processed = 0
    async for scene in store.populated_filter_iter(
        Scene,
        required_fields=['file', 'performers'],
        predicate=lambda s: s.file.size > 1_000_000_000,  # > 1GB
        populate_batch=50,
        yield_batch=10
    ):
        # Yields results as they're ready (doesn't wait for all)
        await process_large_scene(scene)
        processed += 1

        # Update progress bar
        if processed % 10 == 0:
            print(f"Processed {processed} large scenes...")
```

### Batch Parameters

```python
async for item in store.populated_filter_iter(
    Performer,
    required_fields=['rating100'],
    predicate=lambda p: p.rating100 >= 80,
    populate_batch=50,  # Concurrent populates per sub-batch
    yield_batch=10      # Process 10 entities before yielding matches
):
    process(item)
```

- **`populate_batch`**: How many to populate concurrently (default: 50)
- **`yield_batch`**: How many to process before yielding (default: 10)

### When to Use

- **Large datasets**: Process 10,000+ entities incrementally
- **Early exit**: Stop processing when you find enough matches
- **Memory efficiency**: Don't load all results into memory
- **Progress reporting**: Update UI as results stream in

## Real-World Workflow Example

```python
from stash_graphql_client import StashContext, Performer

async with StashContext(conn=conn) as context:
    store = context.store

    # Step 1: Initial cache population (lightweight)
    print("Loading performers...")
    async for performer in store.find_iter(Performer, query_batch=100):
        # Loads: id, name, gender (minimal fields)
        cache_performer(performer)
    print(f"Cached {len(store.all_cached(Performer))} performers")

    # Step 2: User filters by rating (partial data in cache)
    print("\nFinding high-rated performers...")
    results, stats = await store.filter_and_populate_with_stats(
        Performer,
        required_fields=['rating100', 'favorite'],
        predicate=lambda p: p.rating100 >= 80 and p.favorite
    )

    print(f"Cache hit rate: {stats['cache_hit_rate']:.1%}")
    print(f"Fetched fields for: {stats['needed_population']} performers")
    print(f"Found: {len(results)} matches")

    # Step 3: Verify cache before expensive operation
    try:
        verified = store.filter_strict(
            Performer,
            required_fields=['rating100', 'favorite', 'scenes'],
            predicate=lambda p: p in results
        )
        # All performers now guaranteed to have scenes field
        for performer in verified:
            process_with_scenes(performer)
    except ValueError:
        # Some performers missing 'scenes' field - populate it
        for performer in results:
            if not store.has_fields(performer, 'scenes'):
                await store.populate(performer, fields=['scenes'])
```

## Best Practices

### 1. Choose the Right Method

```python
# ✓ Fast local query, data already complete
results = store.filter(Performer, lambda p: p.rating100 >= 80)

# ✓ Smart hybrid, auto-populate missing fields
results = await store.filter_and_populate(
    Performer,
    required_fields=['rating100'],
    predicate=lambda p: p.rating100 >= 80
)

# ✓ Fail-fast validation before critical operation
results = store.filter_strict(
    Performer,
    required_fields=['rating100', 'scenes'],
    predicate=lambda p: p.rating100 >= 80
)

# ✓ Large dataset with early exit
async for item in store.populated_filter_iter(
    Performer,
    required_fields=['rating100'],
    predicate=lambda p: p.rating100 >= 95
):
    if found_enough():
        break
```

### 2. Cache Warming Strategy

```python
# Strategy 1: Minimal initial load
async for performer in store.find_iter(Performer):
    # Loads minimal fields
    pass

# Later: Populate on-demand
results = await store.filter_and_populate(
    Performer,
    required_fields=['rating100'],
    predicate=lambda p: p.rating100 >= 80
)

# Strategy 2: Pre-load common fields
await store.find(
    Performer,
    # Specify fields in GraphQL query (if supported by client method)
)
```

### 3. Performance Monitoring

```python
# Use stats variant to optimize
for _ in range(10):
    results, stats = await store.filter_and_populate_with_stats(
        Performer,
        required_fields=['rating100'],
        predicate=lambda p: p.rating100 >= 80
    )

    if stats['cache_hit_rate'] < 0.5:
        print(f"Warning: Low cache hit rate ({stats['cache_hit_rate']:.1%})")
        print("Consider cache warming or adjusting TTL")
```

### 4. Field Dependencies

```python
# If predicate needs multiple fields, list them all
results = await store.filter_and_populate(
    Scene,
    required_fields=['rating100', 'performers', 'tags', 'studio'],
    predicate=lambda s: (
        s.rating100 >= 80 and
        len(s.performers) > 2 and
        any(t.name == "Action" for t in s.tags) and
        s.studio.name == "Acme Studios"
    )
)
```

## Integration with UNSET Pattern

The advanced filter methods work seamlessly with the [UNSET Pattern](unset-pattern.md):

```python
from stash_graphql_client.types.unset import UNSET

# Manual check for UNSET fields
if performer.rating100 is UNSET:
    # Field not queried - use filter_and_populate
    results = await store.filter_and_populate(
        Performer,
        required_fields=['rating100'],
        predicate=lambda p: p.id == performer.id
    )
else:
    # Field is loaded (None or value) - safe to use
    if performer.rating100 and performer.rating100 >= 80:
        process(performer)

# Or use filter_strict to enforce
try:
    results = store.filter_strict(
        Performer,
        required_fields=['rating100'],
        predicate=lambda p: p.rating100 >= 80
    )
except ValueError:
    # Some performers have rating100=UNSET
    results = await store.filter_and_populate(
        Performer,
        required_fields=['rating100'],
        predicate=lambda p: p.rating100 >= 80
    )
```

## See Also

- [UNSET Pattern](unset-pattern.md): Understanding unqueried vs null fields
- [Identity Map](../architecture/identity-map.md): Object caching and identity
- [Entity Store API](../api/store.md): Full API reference
- [Usage Patterns](usage-patterns.md): Common usage scenarios
