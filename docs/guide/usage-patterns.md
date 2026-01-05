# Common Usage Patterns

This guide shows common patterns for working with stash-graphql-client. These patterns are designed to be clear for both human developers and LLM agents reading the documentation.

## Pattern 1: Basic CRUD Operations

### Creating Entities

```python
from stash_graphql_client import StashContext
from stash_graphql_client.types import Scene, Performer, Tag

async with StashContext(conn={"Host": "localhost", "Port": 9999}) as client:
    # Create a new scene
    scene = Scene(title="My Scene", rating100=85)
    await scene.save(client)
    print(f"Created scene with ID: {scene.id}")

    # Create a performer
    performer = Performer(
        name="Jane Doe",
        birthdate="1990-05-15",
        gender="FEMALE"
    )
    await performer.save(client)

    # Create a tag
    tag = Tag(name="Action", description="Action scenes")
    await tag.save(client)
```

**Key points**:

- New entities get automatic UUID4 IDs (32-char hex strings)
- `.save(client)` executes the appropriate GraphQL mutation
- Server-assigned ID replaces the UUID4 after save
- Use `entity.is_new()` to check if entity has been saved

### Reading/Querying Entities

```python
from stash_graphql_client import StashContext

async with StashContext(conn={...}) as client:
    # Find by ID
    scene = await client.find_scene("123")
    performer = await client.find_performer("456")

    # Find with filters
    scenes_result = await client.find_scenes(
        scene_filter={"rating100": {"value": 80, "modifier": "GREATER_THAN"}}
    )
    print(f"Found {scenes_result.count} scenes")
    for scene in scenes_result.scenes:
        print(f"  {scene.title}: {scene.rating100}")

    # Find all (with pagination)
    studios_result = await client.find_studios()
    for studio in studios_result.studios:
        print(studio.name)
```

**Key points**:

- `find_X(id)` methods return single entity or None
- `find_Xs(filter)` methods return result objects with count and items
- Result objects have entity-specific list names (e.g., `scenes`, `performers`)
- Pagination handled via `page` and `per_page` parameters

### Updating Entities

```python
from stash_graphql_client.types import UNSET

async with StashContext(conn={...}) as client:
    # Load entity
    scene = await client.find_scene("123")

    # Modify fields
    scene.title = "Updated Title"
    scene.rating100 = 90
    scene.details = UNSET  # Don't touch this field

    # Save only sends changed fields
    await scene.save(client)

    # Check what changed
    changed = scene.get_changed_fields()
    print(f"Changed fields: {changed}")
```

**Key points**:

- Only modified fields are sent in update mutations
- Use `UNSET` to explicitly not modify a field
- `get_changed_fields()` shows what will be sent
- Entity `.save()` automatically chooses create vs update mutation

### Deleting Entities

```python
async with StashContext(conn={...}) as client:
    scene = await client.find_scene("123")

    # Delete entity
    await scene.delete(client)

    # Or use client method directly
    await client.destroy_scene("456")
```

**Key points**:

- `.delete(client)` method available on all entity types
- Client also has `destroy_X(id)` methods
- Deletion is permanent - no undo

## Pattern 2: Working with Relationships

### Setting Single Relationships (Many-to-One)

```python
from stash_graphql_client.types import Scene, Studio, is_set

async with StashContext(conn={...}) as client:
    scene = await client.find_scene("123")
    studio = await client.find_studio("456")

    # Set the relationship
    scene.studio = studio

    # Save to persist
    await scene.save(client)

    # Inverse relationship automatically updated
    if is_set(studio.scenes):
        assert scene in studio.scenes  # True!
```

**Key points**:

- Set relationship by assigning entity object
- Bidirectional sync happens automatically
- Save the entity to persist the relationship
- Inverse field only synced if it was loaded

### Setting Many-to-Many Relationships

```python
from stash_graphql_client.types import Scene, Performer, Tag

async with StashContext(conn={...}) as client:
    scene = await client.find_scene("123")

    # Load related entities
    performer1 = await client.find_performer("p1")
    performer2 = await client.find_performer("p2")

    # Set entire list
    scene.performers = [performer1, performer2]
    await scene.save(client)

    # Or use helper methods
    performer3 = await client.find_performer("p3")
    await scene.add_performer(performer3)  # Adds to list

    # Remove from list
    await scene.remove_performer(performer1)
```

**Key points**:

- Many-to-many relationships are lists
- Can assign entire list or use `add_X()` / `remove_X()` helpers
- Helper methods automatically sync inverse relationships
- Changes persist only after `.save(client)`

### Querying Related Entities

```python
from stash_graphql_client.types import is_set

async with StashContext(conn={...}) as client:
    # Get scene with related entities loaded
    scene = await client.find_scene("123")

    # Access related entities
    if is_set(scene.studio):
        print(f"Studio: {scene.studio.name}")

    if is_set(scene.performers):
        for performer in scene.performers:
            print(f"Performer: {performer.name}")

    # Note: Related entities use same identity map
    if is_set(scene.studio):
        studio = await client.find_studio(scene.studio.id)
        assert studio is scene.studio  # Same object reference!
```

**Key points**:

- Always check for UNSET before accessing relationships using `is_set()`
- Related entities automatically cached in identity map
- Same entity ID = same object reference everywhere

## Pattern 3: Using the Entity Store

### Basic Store Operations

```python
from stash_graphql_client import StashContext, StashEntityStore
from stash_graphql_client.types import Scene, Performer

async with StashContext(conn={...}) as client:
    store = StashEntityStore(client, ttl_seconds=300)

    # Read-through caching (fetches if not cached)
    scene = await store.get(Scene, "123")

    # Get without fetch (returns None if not cached)
    cached_scene = store.get_cached(Scene, "123")

    # Save entity through store
    scene.title = "Updated"
    await store.save(scene)

    # Delete through store
    await store.delete(scene)
```

**Key points**:

- `get()` fetches from server if not in cache
- `get_cached()` only checks cache, never queries
- Store methods wrap client methods with caching
- TTL optional (None = never expire)

### Django-Style Filtering

```python
from stash_graphql_client import StashEntityStore
from stash_graphql_client.types import Scene, Performer

store = StashEntityStore(client)

# Comparison operators
top_rated = await store.find(Scene, rating100__gte=80)
low_rated = await store.find(Scene, rating100__lt=50)

# Null checks
unrated = await store.find(Scene, rating100__null=True)
rated = await store.find(Scene, rating100__null=False)

# String matching
search = await store.find(Performer, name__contains="Jane")
exact = await store.find(Performer, name__exact="Jane Doe")

# Range queries
date_range = await store.find(Scene, date__between=("2024-01-01", "2024-12-31"))

# Combine multiple filters
results = await store.find(
    Scene,
    rating100__gte=80,
    organized=True,
    title__contains="test"
)
```

**Supported modifiers**:

- `__exact` - Exact match
- `__contains` - String contains
- `__regex` - Regular expression match
- `__gte`, `__gt` - Greater than (or equal)
- `__lte`, `__lt` - Less than (or equal)
- `__between` - Range (tuple of min/max)
- `__null` - Null check (boolean)
- `__in` - List membership

### Field-Aware Population

```python
from stash_graphql_client import StashEntityStore
from stash_graphql_client.types import Performer

store = StashEntityStore(client)

# Initial query fetches basic fields
performer = await client.find_performer("123")
print(performer._received_fields)  # {"id", "name", "birthdate"}

# Check what's missing
missing = store.missing_fields(performer, "scenes", "images", "tags")
print(f"Missing fields: {missing}")  # {"scenes", "images", "tags"}

# Populate only missing fields
await store.populate(performer, fields=["scenes", "images"])
print(performer._received_fields)  # {"id", "name", "birthdate", "scenes", "images"}

# Force refetch (invalidate cache)
await store.populate(performer, fields=["name"], force_refetch=True)
```

**Key points**:

- `_received_fields` tracks which fields were loaded
- `missing_fields()` returns set of fields not yet loaded
- `populate()` fetches only missing fields
- Use `force_refetch=True` to invalidate cache and reload

### Lazy Iteration for Large Result Sets

```python
from stash_graphql_client import StashEntityStore
from stash_graphql_client.types import Scene

store = StashEntityStore(client)

# Lazy iteration - fetches pages on demand
async for scene in store.find_iter(Scene, organized=False, query_batch=50):
    await organize_scene(scene)

    # Can break early - remaining pages never fetched
    if done_condition:
        break

# Compare to find() which loads all results
all_scenes = await store.find(Scene, organized=False)  # Loads everything!
```

**Key points**:

- `find_iter()` yields items one at a time
- Pages fetched on demand (not all upfront)
- Can break early to save network requests
- `query_batch` controls page size (default 40)

## Pattern 4: Advanced Queries

### Using Raw GraphQL Filters

```python
async with StashContext(conn={...}) as client:
    # Complex filter with nested conditions
    scenes = await client.find_scenes(
        scene_filter={
            "performers": {
                "value": ["performer-id-1", "performer-id-2"],
                "modifier": "INCLUDES_ALL"  # Must have ALL performers
            },
            "rating100": {
                "value": 80,
                "modifier": "GREATER_THAN"
            },
            "tags": {
                "value": ["tag-id-1"],
                "modifier": "INCLUDES"  # Has at least one tag
            }
        }
    )
```

**Key points**:

- Raw filters give full control over GraphQL query
- Use when Django-style syntax is insufficient
- Filter structure matches Stash's GraphQL schema
- See API reference for available modifiers

### Pagination

```python
async with StashContext(conn={...}) as client:
    page = 1
    per_page = 100

    while True:
        result = await client.find_scenes(
            scene_filter={...},
            page=page,
            per_page=per_page
        )

        print(f"Processing page {page}: {len(result.scenes)} scenes")

        for scene in result.scenes:
            await process_scene(scene)

        # Stop if we got fewer results than requested
        if len(result.scenes) < per_page:
            break

        page += 1
```

**Key points**:

- `page` is 1-indexed (first page = 1)
- `per_page` defaults to 40 (max typically 1000)
- Check `len(result.items) < per_page` to detect last page
- Result object includes `.count` for total items

## Pattern 5: Bulk Operations

### Concurrent Fetches

```python
import asyncio
from stash_graphql_client import StashContext

async with StashContext(conn={...}) as client:
    # Fetch multiple entities concurrently
    scenes, performers, studios = await asyncio.gather(
        client.find_scenes(),
        client.find_performers(),
        client.find_studios(),
    )

    # Process results
    print(f"Found {scenes.count} scenes")
    print(f"Found {performers.count} performers")
    print(f"Found {studios.count} studios")
```

### Concurrent Updates

```python
import asyncio
from stash_graphql_client import StashContext

async with StashContext(conn={...}) as client:
    # Load scenes
    scenes = await client.find_scenes(
        scene_filter={"organized": {"value": False, "modifier": "EQUALS"}}
    )

    # Update all concurrently
    for scene in scenes.scenes[:10]:  # First 10
        scene.organized = True

    await asyncio.gather(*[
        scene.save(client) for scene in scenes.scenes[:10]
    ])
```

**Key points**:

- Use `asyncio.gather()` for concurrent operations
- Be mindful of rate limits (don't send 1000 concurrent requests)
- Consider batching (process 10-50 at a time)

### Batch Processing with Progress Tracking

```python
import asyncio
from stash_graphql_client import StashContext, StashEntityStore
from stash_graphql_client.types import Scene

async with StashContext(conn={...}) as client:
    store = StashEntityStore(client)

    # Process in batches
    batch_size = 25
    processed = 0

    async for scene in store.find_iter(Scene, organized=False):
        await process_scene(scene)
        processed += 1

        # Progress update every batch
        if processed % batch_size == 0:
            print(f"Processed {processed} scenes")

    print(f"Total processed: {processed}")
```

## Pattern 6: Job Management

### Starting and Monitoring Jobs

```python
from stash_graphql_client import StashContext

async with StashContext(conn={...}) as client:
    # Start a metadata scan job
    job_id = await client.metadata_scan(
        paths=["/media/videos"],
        options={
            "scanGeneratePreviews": False,
            "scanGenerateImagePreviews": False,
            "scanGenerateSprites": False,
        }
    )

    print(f"Started job {job_id}")

    # Wait for completion (blocking)
    result = await client.wait_for_job(job_id, timeout=300)  # 5 min timeout
    print(f"Job finished with status: {result.status}")
```

### Polling Job Status

```python
import asyncio
from stash_graphql_client import StashContext

async with StashContext(conn={...}) as client:
    job_id = await client.metadata_scan(paths=["/media"])

    # Poll until complete
    while True:
        job = await client.find_job(job_id)

        if job is None:
            print("Job not found")
            break

        print(f"Status: {job.status}, Progress: {job.progress}%")

        if job.status in ["FINISHED", "FAILED", "CANCELLED"]:
            break

        await asyncio.sleep(5)  # Check every 5 seconds
```

### Using Subscriptions for Real-Time Updates

```python
from stash_graphql_client import StashContext

async with StashContext(conn={...}) as client:
    # Subscribe to job updates
    async for update in client.subscribe_job_updates():
        job = update.job
        print(f"Job {job.id}: {job.status} - {job.progress}%")

        if job.status == "FINISHED":
            print(f"Job {job.id} completed!")
            break
```

**Key points**:

- `metadata_scan()`, `metadata_generate()` return job IDs
- `wait_for_job()` blocks until completion (with timeout)
- Manual polling gives more control over progress updates
- Subscriptions provide real-time updates via WebSocket

## Pattern 7: ID Mapping and Utilities

### Converting Names to IDs (with Auto-Create)

```python
from stash_graphql_client import StashContext
from stash_graphql_client.types import Performer

async with StashContext(conn={...}) as client:
    # Convert performer names to IDs, creating if they don't exist
    performer_names = ["Jane Doe", "John Smith", "Alice Wonder"]
    performer_ids = await client.map_performer_ids(performer_names, create=True)

    print(f"Mapped {len(performer_names)} names to {len(performer_ids)} IDs")

    # Use IDs in scene update
    scene = await client.find_scene("123")
    scene.performer_ids = performer_ids
    await scene.save(client)
```

**Available mapping methods**:

- `map_performer_ids(items, create=False)`
- `map_studio_ids(items, create=False)`
- `map_tag_ids(items, create=False)`

**Key points**:

- Pass list of strings (names) or entity objects
- `create=True` creates missing entities
- Returns list of IDs in same order as input
- Mixed types supported (strings and objects)

### Studio Hierarchy Navigation

```python
from stash_graphql_client import StashContext

async with StashContext(conn={...}) as client:
    # Get full parent chain from root to target
    hierarchy = await client.find_studio_hierarchy("studio-123")

    print("Studio hierarchy:")
    for i, studio in enumerate(hierarchy):
        indent = "  " * i
        print(f"{indent}{studio.name}")

    # Get just the root studio
    root = await client.find_studio_root("studio-123")
    print(f"Root studio: {root.name}")
```

## Pattern 8: Error Handling

### Handling GraphQL Errors

```python
from stash_graphql_client import StashContext
from stash_graphql_client.errors import GraphQLError
from gql.transport.exceptions import TransportQueryError

async with StashContext(conn={...}) as client:
    try:
        scene = await client.find_scene("invalid-id")
    except TransportQueryError as e:
        print(f"GraphQL query error: {e}")
        # Handle specific GraphQL errors
    except Exception as e:
        print(f"Unexpected error: {e}")
```

### Handling Validation Errors

```python
from stash_graphql_client.types import Scene
from pydantic import ValidationError

try:
    scene = Scene(
        title="Test",
        rating100=150  # Invalid: must be 0-100
    )
except ValidationError as e:
    print("Validation errors:")
    for error in e.errors():
        print(f"  {error['loc']}: {error['msg']}")
```

### Handling Connection Errors

```python
from stash_graphql_client import StashContext
from httpx import ConnectError, TimeoutException

try:
    async with StashContext(conn={...}) as client:
        scenes = await client.find_scenes()
except ConnectError:
    print("Cannot connect to Stash server")
except TimeoutException:
    print("Request timed out")
```

## Next Steps

- **[Overview Guide](overview.md)** - Architecture and core concepts
- **[UNSET Pattern Guide](unset-pattern.md)** - Deep dive on partial updates
- **[API Reference](../api/client.md)** - Complete method documentation
- **[Architecture Details](../architecture/identity-map.md)** - Implementation deep dives
