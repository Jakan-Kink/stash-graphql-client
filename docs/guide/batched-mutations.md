# Batched Mutations

When working with large collections of entities, sending individual GraphQL mutations is inefficient. Each mutation is a separate HTTP round-trip, and the server resolves the full response fragment for each one. For 500 scene updates, that's 500 HTTP requests with full relationship resolution on every response.

Batched mutations solve this by combining multiple operations into a single aliased GraphQL document, collapsing N round-trips into `ceil(N / max_batch_size)`.

## Three Layers

The batching system has three layers, each building on the one below:

| Layer | Method | Use case |
|-------|--------|----------|
| **Low-level** | `client.execute_batch()` | Raw aliased GraphQL — full control over mutations |
| **Mid-level** | `store.save_batch()` | Save a list of dirty entities with cache integration |
| **High-level** | `store.save_all()` | Flush all dirty entities in the identity map |

## Low-Level: `execute_batch()`

Combines a list of `BatchOperation` objects into one aliased GraphQL document and sends it as a single HTTP request.

```python
from stash_graphql_client import BatchOperation

ops = [
    BatchOperation(
        mutation_name="sceneUpdate",
        input_type_name="SceneUpdateInput!",
        variables={"input": {"id": "1", "title": "Updated Title"}},
    ),
    BatchOperation(
        mutation_name="tagCreate",
        input_type_name="TagCreateInput!",
        variables={"input": {"name": "Action"}},
    ),
]

result = await client.execute_batch(ops)

# Each operation's result is available by index
print(result[0].result)  # {"id": "1", "__typename": "Scene"}
print(result[1].result)  # {"id": "42", "__typename": "Tag"}
```

This generates the following GraphQL:

```graphql
mutation Batch($input0: SceneUpdateInput!, $input1: TagCreateInput!) {
  op0: sceneUpdate(input: $input0) { id __typename }
  op1: tagCreate(input: $input1) { id __typename }
}
```

### Chunking

When the number of operations exceeds `max_batch_size` (default 250), they are automatically split into sequential chunks. Each chunk is a separate HTTP request, but results are aggregated into a single `BatchResult`.

```python
# 300 operations → 2 HTTP requests (250 + 50)
result = await client.execute_batch(ops_list_of_300)

# Or tune the chunk size
result = await client.execute_batch(ops, max_batch_size=100)
```

### `BatchResult`

The return value provides convenient access to results:

```python
result = await client.execute_batch(ops)

result.all_succeeded    # True if every operation succeeded
result.succeeded        # List of operations that succeeded
result.failed           # List of operations that had errors
len(result)             # Total number of operations
result[0].result        # Response dict for first operation
result[0].error         # Exception for first operation (None on success)
```

## Mid-Level: `store.save_batch()`

Saves a list of dirty `StashObject` instances through the entity store, with full cache integration.

```python
from stash_graphql_client import StashContext

async with StashContext(conn={...}) as client:
    store = client.store

    # Modify some entities
    scene1 = await client.find_scene("1")
    scene2 = await client.find_scene("2")
    tag = await client.find_tag("10")

    scene1.title = "New Title"
    scene2.rating100 = 85
    tag.description = "Updated description"

    # Save all three in one HTTP request
    result = await store.save_batch([scene1, scene2, tag])
```

**Key behaviors**:

- **Non-dirty objects are skipped** -- clean entities in the list are silently excluded
- **Creates before updates** -- new objects are ordered first in the alias list so GraphQL's sequential execution assigns server IDs before updates that might reference them
- **Cascade saves** -- unsaved related objects (UUID IDs) are automatically saved before the batch, with a deprecation warning encouraging explicit saves
- **Side mutations fire** -- field-based side mutation handlers and queued operations execute sequentially per-entity after the main batch succeeds
- **Cache key remapping** -- new objects get their UUID replaced with the server-assigned ID in the identity map

### Mixed Creates and Updates

```python
# New tag (has UUID, not yet saved)
new_tag = Tag.new(name="Horror")
store.add(new_tag)

# Existing scene (update)
scene = await client.find_scene("1")
scene.tags.append(new_tag)

# save_batch handles both -- creates the tag first, then updates the scene
await store.save_batch([new_tag, scene])
```

## High-Level: `store.save_all()`

Scans the identity map cache for all dirty or new entities and batch-saves them. This is an ORM-style "flush" operation.

```python
# Make changes to various entities
scene.title = "Updated"
performer.name = "New Name"
new_tag = Tag.new(name="Comedy")
store.add(new_tag)

# Flush everything in one call
result = await store.save_all()
```

`save_all()` partitions entities into new objects first, then updates, before delegating to `save_batch()`.

## Error Handling

`StashBatchError` is raised when **any** operation in a batch fails. The exception carries the full `BatchResult` so you can inspect partial successes:

```python
from stash_graphql_client.errors import StashBatchError

try:
    result = await client.execute_batch(ops)
except StashBatchError as e:
    batch_result = e.batch_result

    print(f"{len(batch_result.succeeded)} succeeded")
    print(f"{len(batch_result.failed)} failed")

    for op in batch_result.failed:
        print(f"  {op.mutation_name}: {op.error}")

    # Succeeded operations still have their results
    for op in batch_result.succeeded:
        print(f"  {op.mutation_name}: {op.result['id']}")
```

For `store.save_batch()`, partial failure handling is automatic:

- **Succeeded objects** get their side mutations fired and `mark_clean()` called
- **Failed objects** remain dirty and can be retried
- The `StashBatchError` is re-raised after processing partial successes

## Performance: `return_fields` on Bulk Methods

All bulk update methods (`bulk_image_update`, `bulk_scene_update`, etc.) support an optional `return_fields` parameter. By default, these methods request the full entity fragment in the response, which causes the server to resolve every relationship for every entity in the batch.

For fire-and-forget updates where you don't need the response data, pass `return_fields="id"` to use a minimal inline mutation:

```python
# Default: full fragment response (slower -- resolves all relationships)
images = await client.bulk_image_update({
    "ids": image_ids,
    "studio_id": "42",
})

# Minimal: only returns IDs (much faster for large batches)
await client.bulk_image_update(
    {"ids": image_ids, "studio_id": "42"},
    return_fields="id",
)
```

The side mutation handlers (`__side_mutations__`) automatically use `return_fields="id __typename"` for all bulk calls, avoiding the full fragment resolution overhead.

**Impact**: For a bulk studio assignment of 32,000 images at 500/batch, this eliminates ~160,000 unnecessary relationship SELECT queries on the server.
