# Migration Guide

This guide covers changes when upgrading between major versions of stash-graphql-client.

---

## 0.11.x → 0.12.0

v0.12.0 has **no breaking changes** for existing 0.11.x code. The minimum server
requirement remains **Stash appSchema ≥ 75 (Stash v0.30.0+)**. All features added
since v0.30.0 are capability-gated — either by `appSchema` version or by runtime
introspection — so the same client works against both older and newer Stash servers.

### What's New

#### Batched GraphQL Mutations

Collapse N individual mutations into a single aliased HTTP request:

```python
from stash_graphql_client import BatchOperation, BatchResult

# Low-level: explicit batch operations
ops = [BatchOperation(mutation=..., variables=...) for item in items]
result: BatchResult = await client.execute_batch(ops, max_batch_size=250)

# Entity-aware: batch save with cascade
await store.save_batch([scene1, scene2, tag1])

# ORM-style flush: save everything dirty in the identity map
await store.save_all()
```

#### Side Mutations

Entity fields that require dedicated GraphQL mutations (e.g., `sceneSaveActivity`,
`sceneIncrementO`, `addGalleryImages`) are now handled automatically by `save()`:

```python
scene = await client.find_scene("123")
scene.resume_time = 42.5
await scene.save(client)  # Fires sceneSaveActivity automatically
```

Fields with side mutation handlers:

| Entity  | Fields                         | Mutation                                              |
| ------- | ------------------------------ | ----------------------------------------------------- |
| Scene   | `resume_time`, `play_duration` | `sceneSaveActivity`                                   |
| Scene   | `o_counter`, `o_history`       | `sceneAddO` / `sceneDeleteO`                          |
| Scene   | `play_count`, `play_history`   | `sceneAddPlay` / `sceneDeletePlay`                    |
| Gallery | `cover`, `images`              | `addGalleryImages` / `removeGalleryImages`            |
| Image   | `o_counter`                    | `imageIncrementO` / `imageDecrementO` / `imageResetO` |

The existing dedicated client methods (`scene_save_activity()`, `scene_add_play()`,
etc.) continue to work as before.

#### ActiveRecord-Style Relationship DSL

Entity relationship declarations use new factory helpers with auto-derived fields:

```python
# Cleaner declarations (internal — no change to public API)
__relationships__ = {
    "studio": belongs_to("Studio", inverse_query_field="scenes"),
    "tags": habtm("Tag", inverse_query_field="scenes"),
    "performers": habtm("Performer", inverse_query_field="scenes"),
}
```

#### `populate()` Filter-Query Resolution

`StashEntityStore.populate()` now supports filter-query strategy relationships
(e.g., `Tag.scenes`, `Studio.scenes`) via lightweight `find*` queries resolved
through the identity map.

#### Configurable Client Timeout

```python
conn = {"scheme": "http", "host": "localhost", "port": 9999, "Timeout": 60}
async with StashContext(conn=conn) as ctx:
    client = await ctx.get_client()  # 60s timeout on all transports
```

#### `plugins` Field on `ConfigResult`

`get_configuration()` now returns the `plugins` map — per-plugin configuration
data previously only accessible via the GraphQL playground.

#### Introspection-Gated Fields

New server fields are automatically included in queries when detected via
introspection, so the client adapts to your Stash version without code changes:

- `Folder.sub_folders` (Stash v0.31.0+)
- `ScrapedTag.parent` (stashapp/stash#6620)

### StashInput Extra Fields (Correction)

The v0.11.0 migration guide stated that v0.12.0 would reject unknown fields with
`ValidationError`. This enforcement has been **deferred to v0.13.0**. In v0.12.0,
unknown fields still emit a `DeprecationWarning` and are accepted.

---

## 0.10.x → 0.11.0

This section covers breaking changes when upgrading from stash-graphql-client 0.10.x to 0.11.0.

### Minimum Stash Server Version

**v0.11.0 requires Stash appSchema ≥ 75 (Stash v0.30.0+).**

On connection, `StashContext` now runs a `__schema` introspection query and raises
`StashVersionError` if the server is too old. If you need to catch this:

```python
from stash_graphql_client import StashContext, StashVersionError

try:
    async with StashContext(conn=conn) as ctx:
        client = await ctx.get_client()
except StashVersionError as e:
    print(f"Server too old: {e}")
```

### StashEntityStore API Renames

Two parameters/methods were renamed for clarity:

| 0.10.x                                     | 0.11.0                                     |
| ------------------------------------------ | ------------------------------------------ |
| `StashEntityStore(client, ttl_seconds=60)` | `StashEntityStore(client, default_ttl=60)` |
| `store.clear_type(Scene)`                  | `store.invalidate_type(Scene)`             |

### Fragment Store

Client mixins now use a dynamic `FragmentStore` rebuilt at connect time based on detected
server capabilities. Module-level `fragments.*` constants are no longer used internally.

**If you were importing fragments directly**, the constants still exist but are static
defaults that may not match your server's schema. The live fragments are on
`client.fragment_store.*`.

### StashInput Extra Fields Warning

Passing unknown field names in dict inputs (e.g., typos like `"tag_id"` instead of
`"tag_ids"`) now emits a `DeprecationWarning`. This is a two-phase deprecation:

- **v0.11.0–v0.12.0**: `DeprecationWarning` emitted, extra fields still accepted
- **v0.13.0+**: Unknown fields will be rejected with `ValidationError`

Review your code for typos or outdated field names in dict-based inputs.

Additionally, `StashObject` emits a `StashUnmappedFieldWarning` when it receives fields
from the server that aren't declared in the model (server newer than client). This is
purely informational — extra data is preserved in `__pydantic_extra__`.

### Relationship Metadata Corrections

Several `inverse_query_field` values on relationship metadata were corrected or removed
where the inverse field didn't actually exist on the target type:

- `Image.performers`: removed `inverse_query_field="images"` (Performer only has `image_count`)
- `Image.galleries`: removed `inverse_query_field="images"` (Gallery has `image_count`, not a list)
- `Gallery.performers`: removed `inverse_query_field="galleries"` (Performer only has `gallery_count`)
- `Group.tags`: removed `inverse_query_field="groups"` (Tag only has `group_count`)

If you were relying on these inverse fields for bidirectional relationship traversal,
note that the inverse side was never queryable — only the count resolver existed.

### StrEnum Migration

All 33 string enum classes migrated from `(str, Enum)` to Python 3.11+ `StrEnum`.
This is functionally identical but if you were subclassing any of these enums, `StrEnum`
has slightly different MRO behavior.

### New Exports

The following are now exported from `stash_graphql_client`:

- `StashError` — base exception for all Stash errors
- `StashVersionError` — raised when server appSchema is below minimum
- `ServerCapabilities` — detected server capabilities (queries, mutations, types, fields)

### New Features (Non-Breaking)

#### Entity Lifecycle Methods

New methods on `StashObject` replace manual mutation calls:

```python
# Delete
await scene.delete(client)

# Bulk destroy
await Scene.bulk_destroy(client, ["id1", "id2"])

# Merge
await Performer.merge(client, source_ids=["id1", "id2"], destination_id="id3")
```

If you had custom wrappers around the raw mutations, consider migrating to these for
automatic cache invalidation.

#### Server Capability Detection

`ServerCapabilities` provides dynamic lookup methods for checking what the connected
server supports:

```python
caps = ctx.capabilities
caps.has_query("findScenes")
caps.has_mutation("destroyFiles")
caps.has_type("SomeType")
caps.type_has_field("Scene", "someField")
caps.input_has_field("SceneUpdateInput", "someField")
```

#### `__safe_to_eat__` Input Gating

`StashInput` subclasses can declare fields that may be absent on older servers.
`to_graphql()` silently strips unsupported fields when the server doesn't have them,
and raises `ValueError` for unlisted unsupported fields.
