# Getting Started

This guide walks you through installing `stash-graphql-client` and using it the way it's meant to be used: through the **EntityStore**. The store is what turns this library from "a typed GraphQL client" into an ORM-like layer — an identity map so the same entity ID is always the same Python object, read-through caching, selective field loading, Django-style filtering, and batched saves that figure out create-before-update ordering for you.

You can always drop down to raw client calls (covered near the end), but reach for the store first.

## Prerequisites

- **Python 3.12 or higher**
- **Stash server** v0.30.0 or later (appSchema 75+). Newer features are gated via introspection; currently tracking v0.31.x.
- **Poetry** (optional, for development)

## Installation

### Option 1: Install from PyPI (Recommended)

```bash
pip install stash-graphql-client
```

### Option 2: Install with Poetry

```bash
poetry add stash-graphql-client
```

### Option 3: Install from Source

```bash
git clone https://github.com/Jakan-Kink/stash-graphql-client.git
cd stash-graphql-client
poetry install
```

### Verify Installation

```python
import stash_graphql_client
print(stash_graphql_client.__version__)
```

## Configuration

Create a connection dictionary with your Stash server details:

```python
conn = {
    "Scheme": "http",       # or "https"
    "Host": "localhost",    # Stash server hostname
    "Port": 9999,           # Stash server port
    "ApiKey": "...",        # Optional API key
}
```

If your Stash instance requires authentication, generate an API key in the Stash web interface under **Settings → Security**, and add it as `ApiKey` above.

## Your First Script

`StashContext` is an async context manager. Entering it yields a ready-to-use `StashClient`, and the context exposes a single **store singleton** (`context.store`) wired to the identity map. This is the pattern you'll use most:

```python
import asyncio
from stash_graphql_client import StashContext
from stash_graphql_client.types import Scene

async def main():
    context = StashContext(conn={"Host": "localhost", "Port": 9999})
    async with context as client:
        store = context.store

        # Django-style filtering — find highly-rated scenes
        top_rated = await store.find(Scene, rating100__gte=90)

        print(f"Found {len(top_rated)} highly-rated scenes:")
        for scene in top_rated:
            print(f"  - {scene.title}: {scene.rating100}/100")

asyncio.run(main())
```

!!! note
    Keep a reference to the `context` (don't write `async with StashContext(...) as client:` if you need the store) — `context.store` is the identity-map-wired singleton, and it's only initialized once the context is entered.

## Working with the EntityStore

The store is the recommended entry point for everything: reads, searches, and writes.

### Identity Map + Caching

`store.get()` checks the cache first and fetches on a miss. Because of the identity map, the **same entity ID always returns the same object reference**, so a change made anywhere is visible everywhere:

```python
from stash_graphql_client.types import Performer

performer1 = await store.get(Performer, "123")   # cache miss → fetch
performer2 = await store.get(Performer, "123")   # cache hit → no network

assert performer1 is performer2                  # same object, guaranteed
```

### Django-Style Filtering

`store.find()` accepts familiar `field__lookup` filters instead of hand-built GraphQL filter objects:

```python
from stash_graphql_client.types import Scene

unrated = await store.find(Scene, rating100__null=True, organized=False)
recent = await store.find(Scene, title__contains="interview")
```

### Selective Field Loading

Entities may arrive as "stubs" with only base fields. `store.populate()` fetches **only** the fields you actually need (it tracks what's already present), and supports nested `field__subfield` specs:

```python
scene = await store.get(Scene, "123")

# Load just the relationships you need, when you need them
scene = await store.populate(scene, fields=["performers", "studio", "tags"])

# Nested population — files, then the path on each file
scene = await store.populate(scene, fields=["files__path", "studio__parent__name"])
```

### Saving Changes

Modify entities in place, then persist. `store.save()` saves one entity; `store.save_all()` flushes every dirty or new entity the store is tracking in a single batched request (handling create-before-update ordering automatically):

```python
scene = await store.get(Scene, "123")
scene.rating100 = 95
scene.organized = True

await store.save(scene)            # save this one entity
# ...or, after editing many entities:
result = await store.save_all()    # batch-save everything dirty
```

### Lazy Iteration Over Large Sets

For large result sets, `store.find_iter()` yields entities as it pages through them, so you never hold the whole set in memory:

```python
async for scene in store.find_iter(Scene, organized=False):
    process(scene)
```

### Get or Create

`store.get_or_create()` finds an entity by search criteria or builds a new one from those same criteria. New entities are **not** auto-saved — persist them with `store.save()`:

```python
from stash_graphql_client.types import Tag

tag = await store.get_or_create(Tag, name="Documentary")
await store.save(tag)   # persist if it was newly created
```

## Core Workflows

These are the same workflows you'll reach for daily — expressed store-first.

### Workflow 1: Find and Update

```python
import asyncio
from stash_graphql_client import StashContext
from stash_graphql_client.types import Performer

async def update_performer_birthdate():
    context = StashContext(conn={"Host": "localhost", "Port": 9999})
    async with context as client:
        store = context.store

        performer = await store.get(Performer, "456")
        if performer is None:
            print("Performer not found")
            return

        performer.birthdate = "1990-05-15"
        performer.gender = "FEMALE"

        await store.save_all()       # flush the change
        print(f"Updated {performer.name}")

asyncio.run(update_performer_birthdate())
```

### Workflow 2: Create and Link Entities

Build several entities, link them, and let `save_all()` persist everything in one batch with correct ordering (new tags get server IDs before the scene that references them):

```python
import asyncio
from stash_graphql_client import StashContext
from stash_graphql_client.types import Scene, Tag

async def create_scene_with_tags():
    context = StashContext(conn={"Host": "localhost", "Port": 9999})
    async with context as client:
        store = context.store

        action = await store.get_or_create(Tag, name="Action")
        adventure = await store.get_or_create(Tag, name="Adventure")

        scene = Scene(title="Epic Battle", rating100=90)
        store.add(scene)             # track the new entity
        await scene.add_tag(action)
        await scene.add_tag(adventure)

        result = await store.save_all()   # one batched, correctly-ordered write
        print(f"Created '{scene.title}' with {len(scene.tags)} tags")

asyncio.run(create_scene_with_tags())
```

### Workflow 3: Bulk Processing with Progress

```python
import asyncio
from stash_graphql_client import StashContext
from stash_graphql_client.types import Scene

async def organize_unrated_scenes():
    context = StashContext(conn={"Host": "localhost", "Port": 9999})
    async with context as client:
        store = context.store

        processed = 0
        async for scene in store.find_iter(Scene, rating100__null=True, organized=False):
            scene.rating100 = 50
            scene.organized = True
            processed += 1
            if processed % 10 == 0:
                print(f"Processed {processed} scenes")

        result = await store.save_all()   # batch-save every change at the end
        print(f"Organized {processed} scenes")

asyncio.run(organize_unrated_scenes())
```

## Understanding UNSET

The UNSET pattern is how the library does precise partial updates: a field is either set to a value, explicitly `None`, or `UNSET` (never touched, so it's excluded from mutations).

```python
from stash_graphql_client.types import Scene, UNSET

scene = Scene(title="Test")

scene.title = "Example"     # State 1: set to a value
scene.rating100 = None      # State 2: explicitly null
scene.details = UNSET       # State 3: never touched → omitted from the mutation
```

Because saves only send fields you actually changed, you can load an entity, set one field, and save without clobbering anything else:

```python
scene = await store.get(Scene, "123")
scene.rating100 = 95         # only this field is dirty
await store.save(scene)      # mutation sends rating100 only
```

See [UNSET Pattern Guide](unset-pattern.md) for comprehensive examples.

## Working with Relationships

Relationships may be UNSET until populated. Use `store.populate()` to load them, and `is_set()` before accessing:

```python
from stash_graphql_client.types import Scene, is_set

scene = await store.get(Scene, "123")
scene = await store.populate(scene, fields=["studio", "performers"])

if is_set(scene.studio):
    print(f"Studio: {scene.studio.name}")

if is_set(scene.performers):
    for performer in scene.performers:
        print(f"  - {performer.name}")
```

Many-to-many helpers register local changes; persist them with a save:

```python
from stash_graphql_client.types import Performer

performer = await store.get(Performer, "789")
await scene.add_performer(performer)
await store.save(scene)

await scene.remove_performer(performer)
await store.save(scene)
```

## Lower-Level: Using the Client Directly

The store is built on top of `StashClient`, and you can use the client directly when you don't need caching, the identity map, or batching — for example a one-off lookup or a quick script. Entities save against the client with `entity.save(client)`:

```python
import asyncio
from stash_graphql_client import StashContext
from stash_graphql_client.types import Tag, UNSET

async def main():
    async with StashContext(conn={"Host": "localhost", "Port": 9999}) as client:
        # Direct create
        tag = Tag(name="Documentary", description="Documentary-style content")
        await tag.save(client)
        print(f"Created tag: {tag.name} (ID: {tag.id})")

        # Direct find + partial update
        scene = await client.find_scene("123")
        if scene is None:
            return
        scene.rating100 = 95
        scene.details = UNSET        # leave other fields untouched
        await scene.save(client)

asyncio.run(main())
```

!!! tip
    Prefer the store when you touch the same entities more than once, batch writes, or rely on relationships staying consistent. Reach for the raw client for simple one-shot reads or writes.

## Error Handling

```python
import asyncio
from stash_graphql_client import StashContext
from stash_graphql_client.types import Scene
from pydantic import ValidationError
from gql.transport.exceptions import TransportQueryError
from httpx import ConnectError

async def main():
    try:
        context = StashContext(conn={"Host": "localhost", "Port": 9999})
        async with context as client:
            store = context.store

            # Validation happens at construction time
            try:
                scene = Scene(rating100=150)  # invalid: must be 0–100
            except ValidationError as e:
                for error in e.errors():
                    print(f"  {error['loc']}: {error['msg']}")

            scene = await store.get(Scene, "invalid-id")
            if scene is None:
                print("Scene not found")

    except ConnectError:
        print("Cannot connect to Stash server — is it running?")
    except TransportQueryError as e:
        print(f"GraphQL error: {e}")

asyncio.run(main())
```

## Best Practices

### 1. Use the store singleton

Access the store via `context.store` so every part of your code shares one identity map and cache:

```python
# ✅ Good — one shared, identity-map-wired store
context = StashContext(conn={...})
async with context as client:
    store = context.store
    ...

# ❌ Avoid — a detached store won't share the context's identity map
store = StashEntityStore(client)
```

### 2. Batch your writes

Make all your edits, then flush once:

```python
# ✅ Good
for scene in scenes:
    scene.organized = True
await store.save_all()

# ❌ Less efficient — a round-trip per entity
for scene in scenes:
    scene.organized = True
    await store.save(scene)
```

### 3. Populate only what you need

```python
# ✅ Good — fetch just these fields
scene = await store.populate(scene, fields=["performers", "studio"])

# ❌ Avoid — over-fetching everything you might never read
```

### 4. Check for UNSET before accessing

```python
from stash_graphql_client.types import is_set

if is_set(scene.studio):
    print(scene.studio.name)
```

### 5. Handle None responses

```python
scene = await store.get(Scene, "123")
if scene is None:
    print("Scene not found")
    return
```

## Common Patterns

### Pattern: Get or Create

```python
from stash_graphql_client.types import Tag

async def get_or_create_tag(store, name):
    tag = await store.get_or_create(Tag, name=name)
    await store.save(tag)   # no-op if it already existed
    return tag
```

### Pattern: Batch Processing with the Store

```python
import asyncio
from stash_graphql_client import StashContext
from stash_graphql_client.types import Scene

async def process_all_scenes():
    context = StashContext(conn={"Host": "localhost", "Port": 9999})
    async with context as client:
        store = context.store

        async for scene in store.find_iter(Scene, organized=False):
            await process_scene(scene)

        await store.save_all()

asyncio.run(process_all_scenes())
```

## Next Steps

Now that you've completed the getting started guide, explore these topics:

- **[Usage Patterns](usage-patterns.md)** - Common recipes and best practices
- **[UNSET Pattern Guide](unset-pattern.md)** - Deep dive on partial updates
- **[Overview](overview.md)** - Architecture and core concepts
- **[Entity Store API](../api/store.md)** - Complete store method reference

## Troubleshooting

### Connection Issues

**Problem:** `ConnectError: Cannot connect to server`

**Solution:**

- Verify Stash is running
- Check host and port in connection config
- Try accessing Stash web interface manually

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'stash_graphql_client'`

**Solution:**

```bash
pip install stash-graphql-client
```

### Type Errors

**Problem:** IDE shows type errors for entity fields

**Solution:**

- Ensure Python 3.12+ is being used
- Check that Pydantic v2 is installed
- May need to restart IDE/language server

## Getting Help

- **Documentation**: [https://jakan-kink.github.io/stash-graphql-client/](https://jakan-kink.github.io/stash-graphql-client/)
- **GitHub Issues**: [https://github.com/Jakan-Kink/stash-graphql-client/issues](https://github.com/Jakan-Kink/stash-graphql-client/issues)
- **Stash Community**: [https://discord.gg/stash](https://discord.gg/stash)
