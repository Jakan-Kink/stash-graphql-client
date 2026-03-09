# Migration Guide: 0.10.x → 0.11.0

This guide covers breaking changes when upgrading from stash-graphql-client 0.10.x to 0.11.0.

## Minimum Stash Server Version

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

## StashEntityStore API Renames

Two parameters/methods were renamed for clarity:

| 0.10.x                                     | 0.11.0                                     |
| ------------------------------------------ | ------------------------------------------ |
| `StashEntityStore(client, ttl_seconds=60)` | `StashEntityStore(client, default_ttl=60)` |
| `store.clear_type(Scene)`                  | `store.invalidate_type(Scene)`             |

## Fragment Store

Client mixins now use a dynamic `FragmentStore` rebuilt at connect time based on detected
server capabilities. Module-level `fragments.*` constants are no longer used internally.

**If you were importing fragments directly**, the constants still exist but are static
defaults that may not match your server's schema. The live fragments are on
`client.fragment_store.*`.

## StashInput Extra Fields Warning

Passing unknown field names in dict inputs (e.g., typos like `"tag_id"` instead of
`"tag_ids"`) now emits a `DeprecationWarning`. This is a two-phase deprecation:

- **v0.11.0**: `DeprecationWarning` emitted, extra fields still accepted
- **v0.12.0+**: Unknown fields will be rejected with `ValidationError`

Review your code for typos or outdated field names in dict-based inputs.

Additionally, `StashObject` emits a `StashUnmappedFieldWarning` when it receives fields
from the server that aren't declared in the model (server newer than client). This is
purely informational — extra data is preserved in `__pydantic_extra__`.

## Relationship Metadata Corrections

Several `inverse_query_field` values on relationship metadata were corrected or removed
where the inverse field didn't actually exist on the target type:

- `Image.performers`: removed `inverse_query_field="images"` (Performer only has `image_count`)
- `Image.galleries`: removed `inverse_query_field="images"` (Gallery has `image_count`, not a list)
- `Gallery.performers`: removed `inverse_query_field="galleries"` (Performer only has `gallery_count`)
- `Group.tags`: removed `inverse_query_field="groups"` (Tag only has `group_count`)

If you were relying on these inverse fields for bidirectional relationship traversal,
note that the inverse side was never queryable — only the count resolver existed.

## StrEnum Migration

All 33 string enum classes migrated from `(str, Enum)` to Python 3.11+ `StrEnum`.
This is functionally identical but if you were subclassing any of these enums, `StrEnum`
has slightly different MRO behavior.

## New Exports

The following are now exported from `stash_graphql_client`:

- `StashError` — base exception for all Stash errors
- `StashVersionError` — raised when server appSchema is below minimum
- `ServerCapabilities` — detected server capabilities (queries, mutations, types, fields)

## New Features (Non-Breaking)

### Entity Lifecycle Methods

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

### Server Capability Detection

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

### `__safe_to_eat__` Input Gating

`StashInput` subclasses can declare fields that may be absent on older servers.
`to_graphql()` silently strips unsupported fields when the server doesn't have them,
and raises `ValueError` for unlisted unsupported fields.
