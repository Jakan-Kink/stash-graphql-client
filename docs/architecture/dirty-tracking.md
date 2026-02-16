# Dirty Tracking: Selective Snapshot Update After Identity Map Merge

This document explains why server-populated fields must update the dirty tracking snapshot, and why a selective (per-field) approach is required instead of a blanket `mark_clean()`.

**Fixed in**: v0.11.0b2
**Location**: `stash_graphql_client/types/base.py` (`_update_snapshot_for_fields`), `stash_graphql_client/store.py` (`populate()`)

**Related docs**:

- [Pydantic Internals](pydantic-internals.md) — Issue 1 covers how `_snapshot` is stored via `PrivateAttr`
- [Identity Map](identity-map.md) — covers the cache-hit merge path
- [UnsetType Pattern](../guide/unset-pattern.md) — user-facing guide to `is_dirty()`, `mark_clean()`, and `_snapshot`

---

## The Problem: Phantom Dirty Fields After Population

When a `StashObject` is first cached as a minimal stub (e.g., a Scene nested inside a Performer response with just `id` + `title`), its `_snapshot` captures all tracked fields at their initial state — mostly `UNSET`. When the object is later populated with full server data via identity map merge or `store.populate()`, the snapshot is never updated. Every populated field appears dirty.

### The Sequence

```
1. Performer query returns Scene(id='44167', title='Happy Friday...')
   └─ Identity map caches Scene stub
   └─ model_post_init snapshots: {performers: UNSET, studio: UNSET, files: UNSET, ...}

2. store.populate(scene, fields=['files__path']) re-fetches Scene 44167
   └─ Server returns full data → identity map cache hit → merge path
   └─ setattr(cached_scene, 'files', [...])
   └─ setattr(cached_scene, 'performers', [...])
   └─ setattr(cached_scene, 'studio', Studio(...))
   └─ ... all tracked fields now have real values
   └─ _snapshot STILL has {performers: UNSET, studio: UNSET, ...}

3. Consumer checks scene.is_dirty() → True (ALL fields dirty)
   └─ get_changed_fields() returns every tracked field
   └─ save() sends a full update mutation for a scene nobody modified
```

### Why the Snapshot Isn't Updated

The identity map merge path (lines 936–963 in `_identity_map_validator`) returns the **existing cached object** — it does not construct a new instance. This means:

- `model_post_init` does **not** run again (it only runs during Pydantic construction)
- The snapshot taken at original construction time is never refreshed
- The `setattr` calls used for merging are indistinguishable from user modifications

### Real-World Impact

A downstream consumer had to manually call `mark_clean()` at the top of every update method:

```python
async def update_scene(self, store, scene, ...):
    scene.mark_clean()  # WORKAROUND: reset phantom dirty state
    scene.title = new_title
    await store.save(scene)
```

Without the workaround, `save()` sends full update mutations for every entity on every pass — even when nothing changed. On a dataset with 3,000 posts, that's 3,000+ unnecessary GraphQL mutations per run.

---

## Why Not Blanket `mark_clean()`?

A blanket `mark_clean()` after every merge would snapshot **all** tracked fields — including fields the user has locally modified but that weren't part of the merge response. This silently discards pending user changes.

### The Edge Case

```
1. Scene cached fully → snapshot = {title: "A", code: "abc", ...}
2. User sets scene.title = "B" → title is dirty (snapshot "A" ≠ current "B")
3. Another query returns Scene with just {id, code} (no title in response)
   └─ Identity map merge: setattr(scene, 'code', 'abc') — title "B" preserved
   └─ mark_clean() snapshots ALL fields: {title: "B", code: "abc", ...}
   └─ title is now "clean" — user's change silently lost
```

The merge didn't touch `title`, but `mark_clean()` snapshotted it anyway.

---

## The Fix: `_update_snapshot_for_fields()`

Instead of `mark_clean()` (which snapshots all tracked fields), a new method updates the snapshot **only for fields that were in the merge data**:

```python
def _update_snapshot_for_fields(self, field_names: set[str] | frozenset[str]) -> None:
    """Update snapshot for specific fields only."""
    for field in field_names & self.__tracked_fields__:
        self._snapshot[field] = self._snapshot_value(getattr(self, field, UNSET))
```

The set intersection (`field_names & __tracked_fields__`) ensures only declared tracked fields are touched — non-tracked fields and fields not in the merge data are left alone.

### Call Site 1: Identity Map Merge (`base.py`)

After merging server data into a cached instance:

```python
# Update field values from new data
for field_name, field_value in processed_data.items():
    if hasattr(cached_obj, field_name):
        setattr(cached_obj, field_name, field_value)

# Merge received fields
cached_obj._received_fields = old_received | new_fields

# Selectively update snapshot for merged fields only.
cached_obj._update_snapshot_for_fields(set(processed_data.keys()))
```

### Call Site 2: `populate()` Return Path (`store.py`)

After `populate()` fetches and merges fields:

```python
obj._received_fields = final_received

if fields_to_fetch:
    obj._update_snapshot_for_fields(set(fields_to_fetch))

return obj
```

The `if fields_to_fetch` guard avoids unnecessary work when `populate()` determined nothing needed fetching.

### Behavior Matrix

| Scenario                  | Field in merge? | User modified? | Result                                            |
| ------------------------- | --------------- | -------------- | ------------------------------------------------- |
| Server provides new value | Yes             | No             | Snapshot updated → clean                          |
| Server provides new value | Yes             | Yes            | Server overwrites value, snapshot updated → clean |
| Field not in merge        | No              | Yes            | Snapshot NOT updated → stays dirty                |
| Field not in merge        | No              | No             | Snapshot NOT updated → unchanged                  |

Row 3 is the critical case: user modifications to fields not in the merge are preserved as dirty.

Row 2 (server overwriting a user modification) is pre-existing behavior of the identity map merge — the merge loop does `setattr()` unconditionally for all fields in the response. Protecting user-modified fields from merge overwrite would be a separate concern.

---

## Interaction Between the Two Call Sites

The two call sites are complementary, not redundant:

| Path               | When                                      | What gets snapshotted                |
| ------------------ | ----------------------------------------- | ------------------------------------ |
| Identity map merge | Same entity returned in a different query | Fields present in the query response |
| `populate()`       | Explicit field population request         | Fields that were actually fetched    |

Both paths selectively update only the fields they touched.

Note: `populate()` delegates to `store.get()` which calls `from_graphql()` which triggers the identity map merge (call site 1). Call site 2 then runs after any additional nested population is complete, capturing the final state.

---

## Impact on Downstream Consumers

With this fix, consumers no longer need manual `mark_clean()` workarounds:

```python
# Before (workaround):
async def update_scene(self, store, scene, ...):
    scene.mark_clean()  # Reset phantom dirty state
    scene.title = new_title
    await store.save(scene)

# After (clean):
async def update_scene(self, store, scene, ...):
    scene.title = new_title
    await store.save(scene)  # Only title is dirty, only title gets sent
```
