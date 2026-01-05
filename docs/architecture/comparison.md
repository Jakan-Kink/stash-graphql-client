# Library Comparisons

This document compares stash-graphql-client to alternative approaches and libraries to help you understand when and why to use it.

## vs Raw GraphQL with gql

### Side-by-Side Example

**Raw gql approach:**

```python
from gql import gql, Client
from gql.transport.httpx import HTTPXAsyncTransport

# Setup client
transport = HTTPXAsyncTransport(url="http://localhost:9999/graphql")
client = Client(transport=transport)

# Define query string (error-prone, no validation)
query = gql("""
    query FindScene($id: ID!) {
        findScene(id: $id) {
            id
            title
            rating100
            studio { id name }
            performers { id name }
        }
    }
""")

# Execute query
result = await client.execute(query, variable_values={"id": "123"})

# Navigate dict (no type safety)
scene_data = result["findScene"]
title = scene_data["title"]  # Typo in key? Runtime error!
rating = scene_data.get("rating100")  # Optional chaining

# Update requires manual mutation
mutation = gql("""
    mutation UpdateScene($input: SceneUpdateInput!) {
        sceneUpdate(input: $input) {
            id
            title
            rating100
        }
    }
""")

# Build input dict (must include all fields or risk overwriting)
update_result = await client.execute(mutation, variable_values={
    "input": {
        "id": "123",
        "title": "New Title",
        "rating100": 90,
        # Did we forget any fields? Hope not!
    }
})
```

**stash-graphql-client approach:**

```python
from stash_graphql_client import StashContext
from stash_graphql_client.types import UNSET, is_set

# Setup with context manager
async with StashContext(conn={"Host": "localhost", "Port": 9999}) as client:
    # Find scene (type-safe, IDE autocomplete)
    scene = await client.find_scene("123")

    # Access properties (validated Pydantic models)
    title = scene.title  # Type-checked, autocomplete works
    rating = scene.rating100  # Optional fields handled automatically

    # Related objects
    if is_set(scene.studio):
        print(f"Studio: {scene.studio.name}")

    # Update (only changed fields sent)
    scene.title = "New Title"
    scene.rating100 = 90
    scene.details = UNSET  # Don't touch this field
    await scene.save(client)  # Mutation generated automatically
```

### Feature Comparison

| Feature | Raw gql | stash-graphql-client |
|---------|---------|---------------------|
| **Query construction** | Manual string building | Method calls (`client.find_scene()`) |
| **Type safety** | None (runtime dicts) | Full Pydantic validation |
| **IDE autocomplete** | No | Yes (all fields, methods) |
| **Response parsing** | Dict navigation | Pydantic models |
| **Mutation building** | Manual GraphQL strings | `.save()` / `.delete()` methods |
| **Partial updates** | Include all fields or manual tracking | UNSET pattern (automatic) |
| **Object identity** | Manual tracking | Automatic identity map |
| **Relationship handling** | Manual dict navigation | Pydantic models with bidirectional sync |
| **Error detection** | Runtime (wrong keys, types) | Development time (Pydantic validation) |
| **Code volume** | ~40-50 lines for basic CRUD | ~5-10 lines for same operations |

### When to Use Raw gql

✅ Use raw gql when:

- Making a few simple queries
- Need maximum control over GraphQL
- Working with non-Stash GraphQL APIs
- Building a custom abstraction layer

❌ Avoid raw gql when:

- Building tools with complex entity relationships
- Need type safety and validation
- Making many queries for same entities
- Want ORM-like convenience

---

## vs Apollo Client (JavaScript)

Apollo Client is the most popular GraphQL client for JavaScript/TypeScript. Here's how stash-graphql-client compares:

### Architecture Comparison

| Component | Apollo Client | stash-graphql-client |
|-----------|--------------|---------------------|
| **Language** | JavaScript/TypeScript | Python |
| **Type system** | TypeScript (compile-time) | Pydantic (runtime validation) |
| **Caching** | InMemoryCache (separate layer) | Wrap validators (integrated) |
| **Cache normalization** | Refs to normalized objects | Direct object references |
| **Cache writes** | `cache.writeQuery()` | Automatic in constructor |
| **Cache reads** | `cache.readQuery()` | Automatic object reuse |
| **Optimistic updates** | Manual configuration | Not built-in (manual for now) |
| **Subscriptions** | Via graphql-ws | Via websockets transport |

### Cache Implementation

**Apollo Client:**

```javascript
// Separate cache layer
const cache = new InMemoryCache({
  typePolicies: {
    Scene: {
      keyFields: ["id"],
      fields: {
        studio: {
          merge(existing, incoming) {
            return incoming;
          }
        }
      }
    }
  }
});

// Manual cache writes
cache.writeQuery({
  query: SCENE_QUERY,
  data: { findScene: updatedScene }
});

// Manual cache reads
const scene = cache.readQuery({
  query: SCENE_QUERY,
  variables: { id: "123" }
});
```

**stash-graphql-client:**

```python
# Caching built into model construction
scene1 = Scene.from_dict({"id": "123", "title": "Test"})
scene2 = Scene.from_dict({"id": "123", "title": "Test"})
assert scene1 is scene2  # Automatic caching!

# No manual cache API needed
```

### Type Safety

**Apollo with TypeScript:**

```typescript
// Generated types from schema
interface Scene {
  id: string;
  title: string;
  rating100?: number;
}

// Compile-time checking only
const scene: Scene = await client.query({...});
scene.title = "New";  // ✅ TypeScript happy
// Runtime: No validation that server actually sent the right shape
```

**stash-graphql-client:**

```python
# Pydantic models with runtime validation
scene = Scene(title="New", rating100=150)  # ❌ Validation error at runtime!
# rating100 must be 0-100

# Runtime type coercion
scene = Scene(title="New", rating100="85")  # ✅ Converts str -> int
assert scene.rating100 == 85
```

### When to Use Apollo vs stash-graphql-client

**Use Apollo when:**

- Building web applications in JavaScript/TypeScript
- Need React integration (React Query, hooks)
- Working with any GraphQL API
- Need optimistic UI updates
- Want community plugins/extensions

**Use stash-graphql-client when:**

- Building Python tools/scripts
- Working specifically with Stash
- Need runtime type validation
- Want ORM-like entity management
- Prefer identity map over normalized cache

---

## vs SQLAlchemy

SQLAlchemy is Python's most popular ORM for SQL databases. stash-graphql-client borrows patterns from SQLAlchemy but applies them to GraphQL.

### Conceptual Mapping

| SQLAlchemy Concept | stash-graphql-client Equivalent |
|-------------------|-------------------------------|
| **Session** | StashEntityStore |
| **Session.identity_map** | Wrap validator cache |
| **Model.query.filter()** | `store.find(Type, field__modifier=value)` |
| **relationship()** | RelationshipMetadata + auto-sync |
| **back_populates** | inverse_query_field |
| **Lazy loading** | Field-aware population |
| **session.add()** | Automatic in constructor |
| **session.commit()** | `.save(client)` |
| **session.flush()** | No direct equivalent (saves immediately) |

### Side-by-Side Example

**SQLAlchemy:**

```python
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import Session, relationship, declarative_base

Base = declarative_base()

class Scene(Base):
    __tablename__ = 'scenes'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    rating100 = Column(Integer)
    studio_id = Column(Integer, ForeignKey('studios.id'))

    # Relationship with backref
    studio = relationship("Studio", back_populates="scenes")

# Usage
engine = create_engine("sqlite:///stash.db")
session = Session(engine)

# Query
scene = session.query(Scene).filter(Scene.id == 123).first()
top_rated = session.query(Scene).filter(Scene.rating100 >= 80).all()

# Update
scene.title = "Updated"
session.commit()

# Identity map
scene1 = session.query(Scene).filter(Scene.id == 123).first()
scene2 = session.query(Scene).filter(Scene.id == 123).first()
assert scene1 is scene2  # True - same object!
```

**stash-graphql-client:**

```python
from stash_graphql_client import StashContext, StashEntityStore
from stash_graphql_client.types import Scene

async with StashContext(conn={...}) as client:
    store = StashEntityStore(client)

    # Query
    scene = await store.get(Scene, "123")
    top_rated = await store.find(Scene, rating100__gte=80)

    # Update
    scene.title = "Updated"
    await scene.save(client)

    # Identity map
    scene1 = await store.get(Scene, "123")
    scene2 = await store.get(Scene, "123")
    assert scene1 is scene2  # True - same object!
```

### Key Differences

| Aspect | SQLAlchemy | stash-graphql-client |
|--------|-----------|---------------------|
| **Backend** | SQL databases (Postgres, MySQL, SQLite) | GraphQL API (Stash) |
| **Query language** | SQLAlchemy expressions / SQL | GraphQL / Django-style kwargs |
| **Identity map** | `Session.identity_map` dict | Pydantic wrap validators |
| **Async** | `async_scoped_session` (extension) | Native async throughout |
| **Type validation** | Optional (via type hints) | Required (Pydantic runtime) |
| **Relationships** | Foreign keys + `relationship()` | `RelationshipMetadata` + query strategies |
| **Lazy loading** | Database query when accessed | Field-aware populate |
| **Transactions** | session.begin() / commit() / rollback() | No transactions (GraphQL mutations) |
| **Schema changes** | Alembic migrations | N/A (server handles schema) |

### Advantages of stash-graphql-client

✅ **Runtime type validation** - Pydantic catches errors immediately
✅ **UNSET pattern** - Distinguish unqueried from null (SQL can't do this)
✅ **Async-first** - Not retrofitted like SQLAlchemy's async support
✅ **No ORM impedance mismatch** - GraphQL already returns objects

### Advantages of SQLAlchemy

✅ **Transactions** - ACID guarantees, rollback support
✅ **Complex queries** - Joins, subqueries, window functions
✅ **Database portability** - Works with any SQL database
✅ **Mature ecosystem** - 15+ years of development

---

## vs Django ORM

Django ORM is built into the Django web framework but can be used standalone.

### Filter Syntax Comparison

**Django ORM:**

```python
from myapp.models import Scene

# Django double-underscore syntax
top_rated = Scene.objects.filter(rating100__gte=80)
unrated = Scene.objects.filter(rating100__isnull=True)
search = Scene.objects.filter(title__icontains="test")
date_range = Scene.objects.filter(
    date__range=("2024-01-01", "2024-12-31")
)

# Chaining filters
results = Scene.objects.filter(
    rating100__gte=80,
    organized=True
).exclude(title__startswith="OLD")
```

**stash-graphql-client:**

```python
from stash_graphql_client import StashEntityStore
from stash_graphql_client.types import Scene

store = StashEntityStore(client)

# Same double-underscore syntax!
top_rated = await store.find(Scene, rating100__gte=80)
unrated = await store.find(Scene, rating100__null=True)
search = await store.find(Scene, title__contains="test")
date_range = await store.find(Scene, date__between=("2024-01-01", "2024-12-31"))

# Multiple filters (no exclude yet)
results = await store.find(
    Scene,
    rating100__gte=80,
    organized=True
)
```

### Key Differences

| Feature | Django ORM | stash-graphql-client |
|---------|-----------|---------------------|
| **Filter syntax** | `field__modifier` | Same! `field__modifier` |
| **Query chaining** | `.filter().filter().exclude()` | Single `find()` call |
| **Identity map** | Implicit (QuerySet caching) | Explicit (StashEntityStore) |
| **Async support** | Limited (`sync_to_async`) | Native async |
| **Type validation** | Model field types | Pydantic runtime validation |
| **Partial updates** | `save(update_fields=[...])` | UNSET pattern |
| **Relationships** | ForeignKey / ManyToMany | RelationshipMetadata |
| **Database** | SQL (Postgres, MySQL, SQLite) | GraphQL (Stash) |

### When to Use Django ORM vs stash-graphql-client

**Use Django ORM when:**

- Building Django web applications
- Working with SQL databases
- Need transactions and complex joins
- Want admin interface for free

**Use stash-graphql-client when:**

- Working specifically with Stash
- Building Python tools/scripts (not web apps)
- Want GraphQL flexibility
- Need UNSET pattern for sparse updates

---

## When to Use This Library

### ✅ Use stash-graphql-client when:

1. **Building tools that interact with Stash**
   - Media organization scripts
   - Batch processing tools
   - Data migration utilities
   - Custom integrations

2. **You need type safety and validation**
   - Catch errors at development time
   - IDE autocomplete for all fields
   - Runtime validation of server responses

3. **You want ORM-like convenience**
   - `.save()` / `.delete()` methods
   - Relationship helpers
   - Change tracking for partial updates

4. **Working with complex entity relationships**
   - Scenes with performers, studios, tags
   - Need bidirectional relationship sync
   - Want object identity across queries

5. **Making many queries for same entities**
   - Identity map prevents duplicate objects
   - Read-through caching reduces network requests
   - Field-aware population loads only what's needed

### ❌ Don't use stash-graphql-client when:

1. **Just need a few simple queries**
   - Use raw `gql` library directly
   - Simpler for one-off operations

2. **Not using Python**
   - Use GraphQL client for your language
   - Apollo (JS), graphql-ruby (Ruby), etc.

3. **Need to work with multiple GraphQL APIs**
   - This is specialized for Stash's schema
   - Use general-purpose GraphQL client

4. **Memory constrained environment**
   - Identity map keeps objects in memory
   - May not be suitable for very large datasets

5. **Need optimistic updates / offline support**
   - Not built-in (would need manual implementation)
   - Apollo Client better for this use case

---

## Migration Guide

### From Raw gql

**Before:**

```python
query = gql("query { findScene(id: $id) { ... } }")
result = await client.execute(query, {"id": "123"})
scene_data = result["findScene"]
```

**After:**

```python
scene = await client.find_scene("123")
```

**Effort**: Low - mostly replacing string queries with method calls

### From Apollo Client (JS → Python)

**Before (JavaScript):**

```javascript
const { data } = await client.query({
  query: FIND_SCENE,
  variables: { id: "123" }
});
const scene = data.findScene;
```

**After (Python):**

```python
scene = await client.find_scene("123")
```

**Effort**: Medium - language switch + learning Pydantic patterns

### From SQLAlchemy

**Before:**

```python
session = Session(engine)
scene = session.query(Scene).filter(Scene.id == 123).first()
```

**After:**

```python
store = StashEntityStore(client)
scene = await store.get(Scene, "123")
```

**Effort**: Low - very similar patterns, main change is async

### From Django ORM

**Before:**

```python
from myapp.models import Scene
scene = Scene.objects.get(id=123)
```

**After:**

```python
from stash_graphql_client.types import Scene
scene = await client.find_scene("123")
```

**Effort**: Low - filter syntax nearly identical

---

## Summary

**stash-graphql-client combines the best patterns from:**

- **Apollo Client** - GraphQL caching and query management
- **SQLAlchemy** - Identity map and session pattern
- **Django ORM** - Filter syntax and query building
- **Pydantic** - Runtime type validation and models

**It's specifically designed for:**

- Python developers
- Building tools that interact with Stash
- Need type safety + ORM convenience + GraphQL flexibility

**It's NOT designed for:**

- General-purpose GraphQL APIs
- Web applications (use Apollo + React)
- Maximum control over every GraphQL query

## Next Steps

- **[Overview Guide](../guide/overview.md)** - Architecture and core concepts
- **[Identity Map Architecture](identity-map.md)** - Deep dive on caching
- **[Usage Patterns](../guide/usage-patterns.md)** - Common recipes
- **[API Reference](../api/client.md)** - Complete method documentation
