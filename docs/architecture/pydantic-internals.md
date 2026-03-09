# Pydantic v2 Internals: How StashObject Works Around BaseModel

This document explains two significant Pydantic v2 behaviors that required workarounds in `StashObject`, and the architectural decisions behind each fix. Both stem from the same root: Pydantic v2's internal storage model has behaviors that are safe for typical models but dangerous for StashObject's identity map + bidirectional relationship pattern.

**Relevant versions**: Private attribute fix landed in v0.10.14. Shallow repr landed in v0.11.0b1.

---

## Background: Pydantic v2's Three Storage Dicts

Every Pydantic v2 `BaseModel` instance has three internal dictionaries:

| Dict                   | Purpose                             | Rebuilt by `validate_assignment`?           |
| ---------------------- | ----------------------------------- | ------------------------------------------- |
| `__dict__`             | Declared model fields               | **YES** — rebuilt on every field assignment |
| `__pydantic_extra__`   | Extra fields (when `extra="allow"`) | Partially (extra fields may migrate here)   |
| `__pydantic_private__` | `PrivateAttr` fields                | **NO** — stable across all operations       |

StashObject uses `validate_assignment=True` (to run validators on field updates) and `extra="allow"` (to accept unknown GraphQL fields without crashing). This combination creates the conditions for both issues below.

---

## Issue 1: Private Attributes Destroyed by `validate_assignment`

**Fixed in**: v0.10.14
**Location**: `stash_graphql_client/types/base.py`

### The Problem

StashObject maintains three private attributes for internal bookkeeping:

| Attribute          | Purpose                                                           |
| ------------------ | ----------------------------------------------------------------- |
| `_snapshot`        | Dirty tracking baseline — stores field values at last clean state |
| `_is_new`          | Tracks whether object needs `create` vs `update` mutation         |
| `_received_fields` | Tracks which fields came from GraphQL responses                   |

Originally, these were stored via `object.__setattr__()`, which writes directly to `__dict__`. This works in plain Python objects, but in Pydantic v2 with `validate_assignment=True`, every field assignment **rebuilds the entire `__dict__`** — silently destroying any non-field data stored there.

### How It Manifests

The bug only appears on identity map cache hits, not on fresh object construction:

```
1. Gallery(id="123") constructed         → _snapshot stored in __dict__ (all UNSET)
2. Identity map cache hit                → fields merged via setattr()
   └─ Each setattr triggers validate_assignment → __dict__ rebuilt repeatedly
   └─ _snapshot migrates to __pydantic_extra__ (stale copy)
3. mark_clean() called                   → new _snapshot stored in __dict__ (real values)
4. gallery.title = "New"                 → validate_assignment rebuilds __dict__
   └─ New _snapshot LOST
   └─ getattr falls through to __pydantic_extra__ → finds stale all-UNSET snapshot
5. gallery.is_dirty()                    → ALL fields appear dirty (real vs UNSET)
```

This caused phantom dirty fields — every `save()` call would send unnecessary GraphQL mutations for fields that hadn't actually changed.

### Minimal Reproduction (Pre-Fix)

```python
from stash_graphql_client.types.gallery import Gallery

gallery = Gallery(id="123")
setattr(gallery, "title", "Real Title")    # Simulate identity map merge
setattr(gallery, "organized", False)

gallery.mark_clean()
snap_id = id(gallery._snapshot)

gallery.title = "New Title"                # Triggers validate_assignment
assert id(gallery._snapshot) != snap_id    # FAILS — snapshot was replaced!
# gallery._snapshot now points to the stale model_post_init snapshot (all UNSET)
```

### The Fix: Pydantic `PrivateAttr`

Convert all three attributes from `object.__setattr__()` storage to Pydantic `PrivateAttr` declarations:

```python
from pydantic import PrivateAttr

class StashObject(BaseModel):
    # Stored in __pydantic_private__ — survives validate_assignment
    _snapshot: dict = PrivateAttr(default_factory=dict)
    _is_new: bool = PrivateAttr(default=False)
    _received_fields: set = PrivateAttr(default_factory=set)
```

`PrivateAttr` stores values in `__pydantic_private__`, which is **never** rebuilt by `validate_assignment`. All `object.__setattr__()` calls were replaced with direct assignment (`self._attr = value`), which Pydantic routes to `__pydantic_private__` automatically.

### Why It Only Appeared on Cache Hits

Objects constructed with all fields populated don't exhibit this bug because:

1. `model_post_init` creates `_snapshot` with real values (not UNSET)
2. Even if `__dict__` is rebuilt and `_snapshot` falls through to `__pydantic_extra__`, the stale copy also has real values
3. So `current_value == snapshot_value` holds true — dirty tracking appears to work

The bug only manifests when:

1. Object is constructed minimally (e.g., nested fragment with just `id`)
2. Fields are populated via `setattr()` (identity map merge path)
3. `model_post_init` snapshot has UNSET for all fields
4. `mark_clean()` creates new snapshot with real values
5. Next field assignment rebuilds `__dict__`, losing the snapshot
6. Fallback finds the stale all-UNSET snapshot from step 3

This is the exact sequence that occurs in production when `find_scenes()` or `find_galleries()` returns objects already in the identity map cache.

### Key Lesson

> **Never use `object.__setattr__()` to store state on Pydantic v2 models with `validate_assignment=True`.** Use `PrivateAttr` instead — it uses `__pydantic_private__`, the only dict that is guaranteed stable across all Pydantic operations.

---

## Issue 2: Recursive `__repr__` Exponential Blowup

**Fixed in**: v0.11.0b1
**Location**: `stash_graphql_client/types/base.py`, all entity type files

### The Problem

Pydantic v2's default `BaseModel.__repr__()` recursively renders **every field** of every nested model. With StashObject's bidirectional relationships, this walks the entire object graph:

```
Gallery.performers → [Performer] → .scenes → [Scene] → .performers → [Performer] ...
                                  → .groups → [Group] → ...
Gallery.scenes     → [Scene]     → .galleries → [Gallery] → ...
```

Pydantic's cycle detection prevents infinite recursion, but the traversal fans out exponentially across non-cyclic paths.

### Real-World Impact

A downstream consumer called `repr()` on changed field values before saving. On a dataset with ~3,000 posts (~1,200 scenes, ~1,800 galleries):

| Metric                    | Value                                                                             |
| ------------------------- | --------------------------------------------------------------------------------- |
| Per-gallery `repr()` cost | ~2.2 seconds (for `performers` field alone)                                       |
| Cost growth               | Worsens as identity map accumulates entities                                      |
| Total overhead            | **~110 minutes** of CPU time generating strings immediately truncated to 80 chars |
| Memory                    | Multi-MB transient string allocations per call, contributing to OOM kills         |

Any consumer calling `repr()` — logging, debugging, REPL, pytest assertion output — hits the same problem.

### The Fix: Two-Tier Shallow Repr

StashObject now has two repr methods:

#### `_short_repr()` — Compact Nested Representation

Used when an object appears _inside_ another object's repr. Collects all set+non-None fields from the `__short_repr_fields__` tuple:

```python
def _short_repr(self) -> str:
    parts: list[str] = []
    for field in self.__short_repr_fields__:
        val = getattr(self, field, UNSET)
        if is_set(val) and val is not None:
            parts.append(f"{field}={val!r}")
    if not parts:
        return f"{self.__type_name__}(id={self.id!r})"
    return f"{self.__type_name__}({', '.join(parts)})"
```

If no fields match, falls back to `TypeName(id='...')`. Multi-field tuples show all matching fields — e.g., `__short_repr_fields__ = ("id", "name")` produces `Performer(id='123', name='Jane')`.

Each entity subclass declares which fields to include:

| Type      | `__short_repr_fields__` | Example                          |
| --------- | ----------------------- | -------------------------------- |
| Performer | `("name",)`             | `Performer(name='Jane')`         |
| Scene     | `("title",)`            | `Scene(title='Test Scene')`      |
| Tag       | `("name",)`             | `Tag(name='tag 1')`              |
| Studio    | `("name",)`             | `Studio(name='Acme')`            |
| Gallery   | `("title",)`            | `Gallery(title='2024 Post')`     |
| Group     | `("name",)`             | `Group(name='Series 1')`         |
| Image     | `("title",)`            | `Image(title='Photo')`           |
| VideoFile | `("basename",)`         | `VideoFile(basename='clip.mp4')` |
| Folder    | `("path",)`             | `Folder(path='/media/videos')`   |

Fallback: if label field is UNSET or None, falls back to `TypeName(id='123')`.

#### `__repr__()` — Full Representation

Shows **all non-UNSET model fields** (not just tracked fields), with relationship fields rendered shallowly:

```python
def __repr__(self) -> str:
    parts: list[str] = [f"id={self.id!r}"]

    for field_name in sorted(self.__class__.model_fields):
        if field_name == "id":
            continue
        val = getattr(self, field_name, UNSET)
        if not is_set(val):
            continue

        if isinstance(val, StashObject):
            parts.append(f"{field_name}={val._short_repr()}")
        elif isinstance(val, list) and val and isinstance(val[0], StashObject):
            limit = self._SHORT_REPR_LIST_LIMIT  # default: 2
            items = [item._short_repr() for item in val[:limit]]
            suffix = f", ..{len(val) - limit} more" if len(val) > limit else ""
            parts.append(f"{field_name}=[{', '.join(items)}{suffix}]")
        else:
            r = repr(val)
            if len(r) > 200:
                r = r[:197] + "..."
            parts.append(f"{field_name}={r}")

    return f"{self.__type_name__}({', '.join(parts)})"
```

### Example Output

**Before** (Pydantic default — truncated, actual output is megabytes):

```
Performer(id='abc123', name='Jane', alias_list=['JD'], tags=[Tag(id='t1', name='blonde',
parents=[Tag(id='t2', name='hair', parents=[...], children=[Tag(id='t1', ...)])],
children=[...])], scenes=[Scene(id='s1', title='...', performers=[Performer(id='abc123',
name='Jane', alias_list=['JD'], tags=[...], scenes=[Scene(id='s2', ...
... (continues for megabytes)
```

**After** (shallow repr):

```
Performer(id='abc123', alias_list=['JD'], favorite=False, name='Jane',
  scenes=[Scene(title='S1'), Scene(title='S2'), ..1198 more],
  tags=[Tag(name='blonde'), Tag(name='brunette'), ..3 more])
```

### Design Decisions

**Why show all model fields, not just tracked fields?**

The initial proposal showed only `__tracked_fields__`, but the final implementation shows all non-UNSET model fields. This provides more complete debugging information — fields like `rating100`, `scene_count`, and `date` are useful in repr output even though they aren't tracked for dirty checking.

**Why `sorted()` on field names?**

Deterministic output across runs. Without sorting, dict iteration order could vary, making log diffs and test assertions unreliable.

**Why `self.__class__.model_fields` instead of `self.model_fields`?**

Pydantic v2.11 deprecated instance-level `model_fields` access. Using the class-level accessor avoids deprecation warnings.

**Why no dirty indicator (`*` suffix)?**

The original proposal included `"*"` when `is_dirty()` returns True. This was removed because `is_dirty()` does field-by-field comparison including list traversal — too much work for a `__repr__` method that might be called frequently in logging or debugging contexts. A repr should be fast and side-effect-free.

**Why not use `__repr_args__` (Pydantic's hook)?**

Pydantic v2's `__repr_args__` returns `(field_name, value)` tuples that Pydantic then `repr()`s recursively. There's no way to control relationship rendering at that level — the only solution is to override `__repr__` entirely.

**Why truncate scalars at 200 characters (not 60)?**

Fields like `details` can contain multi-paragraph text. The initial proposal used 60 chars, but this was too aggressive — URLs, file paths, and aliases are commonly 80-150 chars. 200 chars provides a better balance.

**Why first 2 items in list repr (not count-only)?**

Showing `tags=[5 Tag]` is compact but loses information. Showing `tags=[Tag(name='blonde'), Tag(name='brunette'), ..3 more]` gives immediate identification of the first two items, which is usually enough to understand the relationship contents without expanding the full list.

**What about `__str__`?**

Left as Pydantic's default (which delegates to `__repr__`). This means `str(obj)`, `f"{obj}"`, and `print(obj)` all use the shallow repr — there's no use case where a consumer wants the multi-MB recursive output.

---

## The Common Thread

Both issues stem from Pydantic v2's `BaseModel` being designed for simple data containers, not for objects with:

- **Identity map caching** — objects are mutated after construction via `setattr()`
- **Bidirectional relationships** — objects reference each other (Scene→Performer→Scene)
- **Internal bookkeeping state** — private attributes that must survive field mutations

StashObject works within Pydantic v2's constraints by:

1. Using `__pydantic_private__` (via `PrivateAttr`) for internal state that must be stable
2. Overriding `__repr__` to prevent recursive traversal of the relationship graph
3. Using `__class__.model_fields` for introspection to avoid deprecated instance access
4. Keeping `validate_assignment=True` for field validation while protecting private state from its dict-rebuilding side effect
