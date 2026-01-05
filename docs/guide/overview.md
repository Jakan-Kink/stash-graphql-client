# Overview

## Why This Library Exists

Interacting with GraphQL APIs typically requires:

- **Manually constructing query and mutation strings** - Error-prone string building with no compile-time validation
- **Building complex nested filter objects** - GraphQL filter syntax can be verbose and difficult to construct
- **Tracking which fields have been fetched** - No automatic way to know which fields are available vs which need to be queried
- **Managing object identity across responses** - The same entity ID may appear in different responses as different object instances, leading to stale data
- **Implementing change tracking** - No built-in way to avoid overwriting unmodified fields in mutations

**stash-graphql-client** provides an ORM-like abstraction layer over Stash's GraphQL API, implementing patterns from:

- **SQLAlchemy** - Identity map pattern, session management, relationship tracking
- **Django ORM** - Filter syntax (`field__modifier`), model validation, query building
- **Rails ActiveRecord** - Entity-centric CRUD operations (`.save()`, `.delete()`), relationship helpers

This allows developers to work with typed Python objects and high-level operations rather than raw GraphQL primitives.

## Core Architectural Patterns

### Identity Map Pattern

Same entity ID always returns the same Python object reference across your entire application. This prevents stale data and eliminates the need for manual cache synchronization.

```python
from stash_graphql_client import StashEntityStore
from stash_graphql_client.types import Scene

store = StashEntityStore(client)

# First query loads a scene
scene1 = await store.get(Scene, "123")

# Later query for same ID returns same object
scene2 = await store.get(Scene, "123")

assert scene1 is scene2  # True - same Python object!

# Update in one place, visible everywhere
scene1.title = "Updated Title"
print(scene2.title)  # "Updated Title" - same reference
```

**Implementation**: Uses Pydantic v2 wrap validators that check the cache before model construction. See [Identity Map Architecture](../architecture/identity-map.md) for details.

### UNSET Sentinel Pattern

Three-state field system distinguishes between:

1. **Value** - Field has been set to an actual value
2. **None** - Field has been explicitly set to null
3. **UNSET** - Field has never been queried or touched

This enables precise partial updates where only modified fields are sent in mutations.

```python
from stash_graphql_client.types import Scene, UNSET

# Load a scene
scene = await client.find_scene("123")

# Three distinct states
scene.title = "New Title"    # State 1: Set to value
scene.rating100 = None       # State 2: Explicitly null
scene.details = UNSET        # State 3: Never touched

# Save sends only non-UNSET fields
await scene.save(client)
# GraphQL mutation: { id: "123", title: "New Title", rating100: null }
# Note: "details" field NOT included - server preserves existing value
```

**Use cases**:

- **Partial queries** - Load only needed fields, leave rest as UNSET
- **Partial updates** - Modify specific fields without affecting others
- **Avoiding race conditions** - Update one field without overwriting concurrent changes to other fields
- **Sparse field selection** - Match GraphQL's sparse field semantics in Python objects

See [UNSET Pattern Guide](unset-pattern.md) for comprehensive examples.

### Type Safety with Pydantic v2

All GraphQL types are Pydantic `BaseModel` subclasses with full runtime validation:

```python
from stash_graphql_client.types import Scene, Performer
from pydantic import ValidationError

# Field validation catches errors before GraphQL requests
try:
    scene = Scene(rating100=150)  # Invalid: must be 0-100
except ValidationError as e:
    print(e.errors())
    # [{'loc': ('rating100',), 'msg': 'Input should be less than or equal to 100'}]

# Type coercion where appropriate
scene = Scene(rating100="85")  # str -> int coercion
assert scene.rating100 == 85

# Nested model validation
performer = Performer(
    name="Jane Doe",
    stash_ids=[{"endpoint": "example.com", "stash_id": "123"}]
)
# StashID objects validated recursively
```

**Benefits**:

- Catch errors at development time (not runtime)
- IDE autocomplete for all fields
- Runtime validation ensures data integrity
- Alias mapping handles GraphQL naming conventions (camelCase ↔ snake_case)

### Relationship Metadata

Relationships are documented via `RelationshipMetadata` objects that specify:

- **target_field** - Field name in mutation input (e.g., `"studio_id"`)
- **query_field** - Field name in query response (e.g., `"studio"`)
- **inverse_type** - Related entity type name
- **inverse_query_field** - Inverse field name for bidirectional sync
- **query_strategy** - How to query the relationship (`"direct_field"`, `"filter_query"`, or `"complex_object"`)

```python
from stash_graphql_client.types import Scene, Studio

# Set a relationship
scene.studio = studio_obj

# Inverse relationship automatically updated
assert scene in studio_obj.scenes  # True - bidirectional sync!

# Helper methods
await scene.add_performer(performer)    # Updates both sides
await scene.remove_tag(tag)             # Syncs inverse
```

See [Bidirectional Relationships](../architecture/bidirectional-relationships.md) for implementation details.

### Field-Aware Population

Track which fields have been fetched and load missing fields on demand:

```python
from stash_graphql_client import StashEntityStore

store = StashEntityStore(client)

# Initial query fetches only specified fields
performer = await client.find_performer("123")
print(performer._received_fields)  # {"id", "name", "birthdate"}

# Check which fields are missing
missing = store.missing_fields(performer, "scenes", "images", "tags")
# Returns: {"scenes", "images", "tags"}

# Populate only missing fields
await store.populate(performer, fields=["scenes", "images"])
print(performer._received_fields)  # {"id", "name", "birthdate", "scenes", "images"}
```

**Benefits**:

- Load expensive fields (large lists) only when needed
- Avoid re-fetching data already in memory
- Progressive data loading
- Optimize network usage for large result sets

## Architecture Layers

This library follows a three-layer architecture:

### Layer 1: StashClient (GraphQL Transport)

Located in `stash_graphql_client/client/`, the client provides direct access to Stash's GraphQL API through typed mixin methods.

**Responsibilities**:

- Execute GraphQL queries and mutations
- Handle HTTP/WebSocket transports
- Manage retries and connection pooling
- Deserialize responses to Pydantic models

**Example usage**:

```python
from stash_graphql_client import StashContext

async with StashContext(conn={...}) as client:
    # Direct GraphQL operations
    scenes = await client.find_scenes()
    performer = await client.create_performer(Performer(name="Alice"))
    job_id = await client.metadata_scan()
```

**Mixin architecture**: Client composed of 20+ mixins, one per entity type (SceneClientMixin, PerformerClientMixin, etc.). This provides clear separation of concerns and makes the codebase maintainable.

### Layer 2: Pydantic Types (Schema/ORM Layer)

Located in `stash_graphql_client/types/`, all Stash entities are Pydantic v2 models with:

**Features**:

- **UNSET Pattern** - Three-state fields distinguish "set to value", "set to null", and "never touched"
- **UUID4 Auto-generation** - New objects get temporary IDs replaced with server IDs on save
- **Bidirectional Relationships** - Automatic sync between related entities
- **Tracked Fields** - `__tracked_fields__` and `__field_conversions__` for change detection
- **Relationship Metadata** - `__relationships__` documents query strategies and inverse fields

**Example usage**:

```python
from stash_graphql_client.types import Scene, UNSET

# Create with partial data - UUID4 auto-generated
scene = Scene(title="My Scene", rating100=85)
print(f"New object ID: {scene.id}")  # UUID4 hex string (32 chars)
print(f"Is new: {scene.is_new()}")   # True

# Save sends only non-UNSET fields
await scene.save(client)
print(f"Server ID: {scene.id}")      # Server-assigned ID
print(f"Is new: {scene.is_new()}")   # False

# Update tracks changes
scene.rating100 = 90
changed = scene.get_changed_fields()  # {"rating100": 90}
await scene.save(client)  # Only sends changed fields
```

### Layer 3: StashEntityStore (Identity Map & Caching)

Located in `stash_graphql_client/store.py`, provides SQLAlchemy/ActiveRecord-style data access with:

**Features**:

- **Identity Map** - Same entity ID → same object reference
- **Read-Through Caching** - Fetch from cache or query on miss
- **TTL Support** - Optional cache expiration
- **Field-Aware Population** - Load missing fields on demand
- **Django-Style Filtering** - `field__modifier` kwargs
- **Lazy Iteration** - Paginate large result sets efficiently
- **Thread-Safe** - Uses `RLock` for concurrent access

**Example usage**:

```python
from stash_graphql_client import StashEntityStore
from stash_graphql_client.types import Scene, Performer

store = StashEntityStore(client, ttl_seconds=300)

# Read-through caching
performer = await store.get(Performer, "123")

# Django-style filtering
top_rated = await store.find(Scene, rating100__gte=80)
unrated = await store.find(Scene, rating100__null=True)

# Field-aware population
await store.populate(performer, fields=["scenes", "images"])

# Get-or-create pattern
tag = await store.get_or_create(Tag, name="Action")
```

## When to Use Each Layer

### Use StashClient when:

- ✅ Making one-off queries
- ✅ Need direct control over GraphQL queries
- ✅ Working with entity types that don't need caching
- ✅ Executing mutations that return complex results

### Use Pydantic Types when:

- ✅ Creating new entities with validation
- ✅ Need ORM-like `.save()` / `.delete()` methods
- ✅ Working with entity relationships
- ✅ Need change tracking for partial updates

### Use StashEntityStore when:

- ✅ Need object identity across queries
- ✅ Making repeated queries for same entities
- ✅ Using Django-style filtering
- ✅ Need field-aware population
- ✅ Processing large result sets with pagination

## Design Philosophy

### Principle 1: Explicit Over Implicit

Operations like `.save()` and `.delete()` require passing the client explicitly:

```python
await scene.save(client)  # Explicit client reference
```

This makes it clear where network operations occur and avoids hidden global state.

### Principle 2: Type Safety by Default

All GraphQL types are Pydantic models with runtime validation. Field typos and type mismatches are caught immediately:

```python
scene.ratting100 = 85  # ❌ IDE/mypy catches typo
scene.rating100 = "invalid"  # ❌ Pydantic validation error
```

### Principle 3: Progressive Enhancement

Start with simple client methods, add caching when needed, use advanced features as required:

```python
# Simple: Direct client usage
scene = await client.find_scene("123")

# Enhanced: Add identity map
store = StashEntityStore(client)
scene = await store.get(Scene, "123")

# Advanced: Field-aware population + filtering
await store.populate(scene, fields=["performers"])
top_rated = await store.find(Scene, rating100__gte=90)
```

### Principle 4: Match GraphQL Semantics

The UNSET pattern matches GraphQL's sparse field selection. Partial updates work exactly like GraphQL input objects:

```python
# Only include fields you want to update
scene.title = "New"
scene.details = UNSET  # GraphQL mutation won't include this field
```

## Next Steps

- **[Getting Started Guide](getting-started.md)** - Step-by-step tutorials
- **[Usage Patterns](usage-patterns.md)** - Common recipes and best practices
- **[Identity Map Architecture](../architecture/identity-map.md)** - Implementation deep dive
- **[Library Comparisons](../architecture/comparison.md)** - How this compares to alternatives
- **[API Reference](../api/client.md)** - Complete API documentation
