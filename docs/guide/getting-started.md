# Getting Started

This guide will walk you through installing and using stash-graphql-client for the first time.

## Prerequisites

- **Python 3.12 or higher**
- **Stash server** running and accessible (tested with v0.25.0+)
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

### Connection Settings

Create a connection dictionary with your Stash server details:

```python
conn = {
    "Scheme": "http",       # or "https"
    "Host": "localhost",    # Stash server hostname
    "Port": 9999,           # Stash server port
    "ApiKey": "...",        # Optional API key
}
```

### API Key (Optional)

If your Stash instance requires authentication:

1. Open Stash web interface
2. Go to Settings → Security
3. Generate an API Key
4. Add it to your connection config

```python
conn = {
    "Host": "localhost",
    "Port": 9999,
    "ApiKey": "your-api-key-here",  # From Stash settings
}
```

## Your First Script

### Example 1: List All Studios

```python
import asyncio
from stash_graphql_client import StashContext

async def main():
    # Connect using context manager (recommended)
    async with StashContext(conn={
        "Host": "localhost",
        "Port": 9999,
    }) as client:
        # Find all studios
        result = await client.find_studios()

        print(f"Found {result.count} studios:")
        for studio in result.studios:
            print(f"  - {studio.name} (ID: {studio.id})")

# Run the async function
asyncio.run(main())
```

**Output:**

```
Found 25 studios:
  - Acme Productions (ID: 1)
  - Studio B (ID: 2)
  - Example Corp (ID: 3)
  ...
```

### Example 2: Create a New Tag

```python
import asyncio
from stash_graphql_client import StashContext
from stash_graphql_client.types import Tag

async def main():
    async with StashContext(conn={
        "Host": "localhost",
        "Port": 9999,
    }) as client:
        # Create a new tag
        tag = Tag(
            name="Documentary",
            description="Documentary-style content"
        )

        # Save to server
        saved_tag = await tag.save(client)

        print(f"Created tag: {saved_tag.name}")
        print(f"Server assigned ID: {saved_tag.id}")

asyncio.run(main())
```

### Example 3: Find and Update a Scene

```python
import asyncio
from stash_graphql_client import StashContext
from stash_graphql_client.types import UNSET

async def main():
    async with StashContext(conn={
        "Host": "localhost",
        "Port": 9999,
    }) as client:
        # Find a scene by ID
        scene = await client.find_scene("123")

        if scene is None:
            print("Scene not found")
            return

        print(f"Found scene: {scene.title}")
        print(f"Current rating: {scene.rating100}")

        # Update the rating
        scene.rating100 = 95
        scene.details = UNSET  # Don't touch this field

        # Save changes
        await scene.save(client)

        print(f"Updated rating to: {scene.rating100}")

asyncio.run(main())
```

## Core Workflows

### Workflow 1: Find and Update Entity

This is the most common pattern for working with existing entities.

```python
import asyncio
from stash_graphql_client import StashContext

async def update_performer_birthdate():
    async with StashContext(conn={"Host": "localhost", "Port": 9999}) as client:
        # 1. Find the entity
        performer = await client.find_performer("456")

        if performer is None:
            print("Performer not found")
            return

        # 2. Modify fields
        performer.birthdate = "1990-05-15"
        performer.gender = "FEMALE"

        # 3. Save changes
        await performer.save(client)

        print(f"Updated {performer.name}")

asyncio.run(update_performer_birthdate())
```

### Workflow 2: Create and Link Entities

Create new entities and establish relationships.

```python
import asyncio
from stash_graphql_client import StashContext
from stash_graphql_client.types import Scene, Tag

async def create_scene_with_tags():
    async with StashContext(conn={"Host": "localhost", "Port": 9999}) as client:
        # 1. Create or find tags
        tag1 = Tag(name="Action")
        await tag1.save(client)

        tag2 = Tag(name="Adventure")
        await tag2.save(client)

        # 2. Create scene
        scene = Scene(title="Epic Battle", rating100=90)
        await scene.save(client)

        # 3. Link tags to scene
        await scene.add_tag(tag1)
        await scene.add_tag(tag2)

        print(f"Created scene '{scene.title}' with {len(scene.tags)} tags")

asyncio.run(create_scene_with_tags())
```

### Workflow 3: Bulk Processing with Filters

Process multiple entities matching specific criteria.

```python
import asyncio
from stash_graphql_client import StashContext, StashEntityStore
from stash_graphql_client.types import Scene

async def organize_unrated_scenes():
    async with StashContext(conn={"Host": "localhost", "Port": 9999}) as client:
        store = StashEntityStore(client)

        # Find all unrated scenes
        unrated = await store.find(Scene, rating100__null=True, organized=False)

        print(f"Found {len(unrated)} unrated scenes")

        # Process each scene
        for scene in unrated:
            # Apply default rating
            scene.rating100 = 50
            scene.organized = True
            await scene.save(client)

            print(f"  - Organized: {scene.title}")

        print("Done!")

asyncio.run(organize_unrated_scenes())
```

## Using the Entity Store

The `StashEntityStore` provides additional features like caching, Django-style filtering, and field-aware population.

### Basic Store Usage

```python
import asyncio
from stash_graphql_client import StashContext, StashEntityStore
from stash_graphql_client.types import Performer

async def main():
    async with StashContext(conn={"Host": "localhost", "Port": 9999}) as client:
        # Create store with 5-minute cache TTL
        store = StashEntityStore(client, ttl_seconds=300)

        # Read-through caching (fetches if not cached)
        performer1 = await store.get(Performer, "123")
        performer2 = await store.get(Performer, "123")

        # Both references point to same object
        assert performer1 is performer2

        print(f"Performer: {performer1.name}")

asyncio.run(main())
```

### Django-Style Filtering

```python
import asyncio
from stash_graphql_client import StashContext, StashEntityStore
from stash_graphql_client.types import Scene

async def main():
    async with StashContext(conn={"Host": "localhost", "Port": 9999}) as client:
        store = StashEntityStore(client)

        # Find highly-rated scenes
        top_rated = await store.find(Scene, rating100__gte=90)

        print(f"Found {len(top_rated)} highly-rated scenes:")
        for scene in top_rated:
            print(f"  - {scene.title}: {scene.rating100}/100")

asyncio.run(main())
```

## Understanding UNSET

The UNSET pattern is one of the library's key features for precise partial updates.

### Three Field States

```python
from stash_graphql_client.types import Scene, UNSET

scene = Scene(title="Test")

# Three possible states for any field:
scene.title = "Example"     # State 1: Set to value
scene.rating100 = None      # State 2: Explicitly null
scene.details = UNSET       # State 3: Never touched
```

### Why UNSET Matters

```python
import asyncio
from stash_graphql_client import StashContext
from stash_graphql_client.types import UNSET

async def main():
    async with StashContext(conn={"Host": "localhost", "Port": 9999}) as client:
        # Load a scene
        scene = await client.find_scene("123")

        # Only update rating, leave everything else unchanged
        scene.rating100 = 95
        # scene.title stays UNSET - won't be included in mutation
        # scene.details stays UNSET - server keeps existing value

        # Save only sends rating100 field
        await scene.save(client)

        print("Updated only the rating!")

asyncio.run(main())
```

See [UNSET Pattern Guide](unset-pattern.md) for comprehensive examples.

## Working with Relationships

### Accessing Related Entities

```python
import asyncio
from stash_graphql_client import StashContext
from stash_graphql_client.types import is_set

async def main():
    async with StashContext(conn={"Host": "localhost", "Port": 9999}) as client:
        scene = await client.find_scene("123")

        # Always check for UNSET before accessing relationships
        if is_set(scene.studio):
            print(f"Studio: {scene.studio.name}")

        if is_set(scene.performers):
            print(f"Performers: {len(scene.performers)}")
            for performer in scene.performers:
                print(f"  - {performer.name}")

asyncio.run(main())
```

### Setting Relationships

```python
import asyncio
from stash_graphql_client import StashContext

async def main():
    async with StashContext(conn={"Host": "localhost", "Port": 9999}) as client:
        scene = await client.find_scene("123")
        studio = await client.find_studio("456")

        # Set the relationship
        scene.studio = studio
        await scene.save(client)

        print(f"Set studio to: {studio.name}")

asyncio.run(main())
```

### Using Relationship Helpers

```python
import asyncio
from stash_graphql_client import StashContext

async def main():
    async with StashContext(conn={"Host": "localhost", "Port": 9999}) as client:
        scene = await client.find_scene("123")
        performer = await client.find_performer("789")

        # Add to many-to-many relationship
        await scene.add_performer(performer)

        print(f"Added {performer.name} to scene")

        # Remove from relationship
        await scene.remove_performer(performer)

asyncio.run(main())
```

## Error Handling

### Handling Common Errors

```python
import asyncio
from stash_graphql_client import StashContext
from stash_graphql_client.types import Scene
from pydantic import ValidationError
from gql.transport.exceptions import TransportQueryError
from httpx import ConnectError

async def main():
    try:
        async with StashContext(conn={
            "Host": "localhost",
            "Port": 9999,
        }) as client:
            # Validation error example
            try:
                scene = Scene(rating100=150)  # Invalid: must be 0-100
            except ValidationError as e:
                print("Validation error:")
                for error in e.errors():
                    print(f"  {error['loc']}: {error['msg']}")

            # GraphQL query error
            scene = await client.find_scene("invalid-id")
            if scene is None:
                print("Scene not found")

    except ConnectError:
        print("Cannot connect to Stash server - is it running?")
    except TransportQueryError as e:
        print(f"GraphQL error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

asyncio.run(main())
```

## Best Practices

### 1. Use Context Manager

Always use `StashContext` as a context manager to ensure proper cleanup:

```python
# ✅ Good
async with StashContext(conn={...}) as client:
    await client.find_scenes()

# ❌ Avoid
context = StashContext(conn={...})
client = await context.get_client()
# ... might forget to close
```

### 2. Check for UNSET Before Accessing

Always check if a field is UNSET before using it:

```python
from stash_graphql_client.types import is_set

# ✅ Good - using helper method
if is_set(scene.studio):
    print(scene.studio.name)

# ✅ Good - manual check
if scene.studio is not UNSET and scene.studio is not None:
    print(scene.studio.name)

# ❌ Avoid
print(scene.studio.name)  # Might fail if UNSET
```

### 3. Use UNSET for Partial Updates

When updating only specific fields, leave others as UNSET:

```python
# ✅ Good
scene.rating100 = 90
# Other fields stay UNSET
await scene.save(client)

# ❌ Avoid
scene.rating100 = 90
scene.title = scene.title  # Unnecessary
scene.details = scene.details  # Unnecessary
await scene.save(client)
```

### 4. Use Store for Repeated Queries

If querying the same entities multiple times, use StashEntityStore:

```python
# ✅ Good
store = StashEntityStore(client)
performer1 = await store.get(Performer, "123")  # Fetches from server
performer2 = await store.get(Performer, "123")  # Returns cached

# ❌ Less efficient
performer1 = await client.find_performer("123")  # Fetches
performer2 = await client.find_performer("123")  # Fetches again
```

### 5. Handle None Responses

Always check if entities exist before using them:

```python
# ✅ Good
scene = await client.find_scene("123")
if scene is None:
    print("Scene not found")
    return

print(scene.title)

# ❌ Avoid
scene = await client.find_scene("123")
print(scene.title)  # Might crash if scene is None
```

## Common Patterns

### Pattern: Get or Create

```python
async def get_or_create_tag(client, name):
    # Try to find existing tag
    tags_result = await client.find_tags(
        tag_filter={"name": {"value": name, "modifier": "EQUALS"}}
    )

    if tags_result.tags:
        return tags_result.tags[0]

    # Create if not found
    tag = Tag(name=name)
    return await tag.save(client)
```

### Pattern: Batch Processing with Progress

```python
import asyncio
from stash_graphql_client import StashContext, StashEntityStore

async def process_all_scenes():
    async with StashContext(conn={...}) as client:
        store = StashEntityStore(client)

        processed = 0
        async for scene in store.find_iter(Scene, organized=False):
            await process_scene(scene)
            processed += 1

            if processed % 10 == 0:
                print(f"Processed {processed} scenes")

        print(f"Total: {processed} scenes")

asyncio.run(process_all_scenes())
```

## Next Steps

Now that you've completed the getting started guide, explore these topics:

- **[Usage Patterns](usage-patterns.md)** - Common recipes and best practices
- **[UNSET Pattern Guide](unset-pattern.md)** - Deep dive on partial updates
- **[Overview](overview.md)** - Architecture and core concepts
- **[API Reference](../api/client.md)** - Complete method documentation

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
# or
poetry add stash-graphql-client
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
