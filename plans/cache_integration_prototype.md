# Cache Integration Prototype: Field-Aware Entity Store

## Overview

Evolve from binary "stub vs complete" detection to a field-aware caching system where:
1. All entities track which fields were received from GraphQL
2. Nested objects are extracted, cached, and linked (identity map pattern)
3. `populate()` fetches only genuinely missing fields

## Current State

```python
# GraphQL returns:
{"id": "1", "title": "Scene", "studio": {"id": "5", "name": "Test"}}

# Current behavior:
scene = Scene(id="1", title="Scene", studio=Studio(id="5", name="Test"))
# - Studio is embedded inside Scene
# - No link to cache
# - Binary stub detection via _is_stub marker
```

## Target State

```python
# Same GraphQL response, new behavior:
scene = Scene(id="1", title="Scene", studio_id="5")  # OR studio=cached_studio
# - Studio extracted and cached: store._cache[("Studio", "5")] = Studio(id="5", name="Test")
# - scene.studio returns the CACHED Studio object (same reference)
# - Studio tracks _received_fields={"id", "name"}
# - populate(studio, "urls") only fetches if "urls" not in _received_fields
```

## Design Decisions

### 1. Field Tracking in StashObject

Add `_received_fields: set[str]` to extras during construction:

```python
@model_validator(mode="before")
@classmethod
def track_received_fields(cls, data: Any) -> Any:
    if isinstance(data, dict):
        data["_received_fields"] = set(data.keys())
    return data
```

This replaces the binary `_is_stub` marker with granular field tracking.

### 2. Cache Reference Injection

Two options for cache integration:

**Option A: Store reference on StashObject (chosen for prototype)**
- Add `_store: StashEntityStore | None` to StashObject extras
- When constructing via store, inject the store reference
- Nested objects can register themselves with the store

**Option B: Context-based store (deferred)**
- Use contextvars for thread-local store access
- More magical, less explicit

### 3. Nested Object Extraction

During `model_validator`, extract and cache nested StashObjects:

```python
@model_validator(mode="before")
@classmethod
def extract_nested_objects(cls, data: Any, info: ValidationInfo) -> Any:
    if not isinstance(data, dict):
        return data

    store = info.context.get("store") if info.context else None
    if not store:
        return data  # No caching without store context

    for field_name, field_info in cls.model_fields.items():
        if field_name not in data:
            continue
        value = data[field_name]

        # Check if field type is a StashObject subclass
        field_type = get_origin(field_info.annotation) or field_info.annotation
        if is_stash_object_type(field_type) and isinstance(value, dict):
            # Create and cache the nested object
            nested_obj = field_type(**value)
            store._cache_entity(nested_obj)
            # Keep the nested object reference (it IS the cached object)
            data[field_name] = nested_obj
        elif is_list_of_stash_objects(field_info.annotation) and isinstance(value, list):
            # Handle list of StashObjects
            cached_list = []
            for item in value:
                if isinstance(item, dict):
                    nested_obj = item_type(**item)
                    store._cache_entity(nested_obj)
                    cached_list.append(nested_obj)
            data[field_name] = cached_list

    return data
```

### 4. Enhanced Populate

**API Change**: Switch from `*fields: str` to `fields: list[str] | set[str]` for explicit kwargs:

```python
async def populate(
    self,
    obj: T,
    fields: list[str] | set[str] | None = None,
    force_refetch: bool = False,
) -> T:
    """Populate specific fields on an entity.

    Args:
        obj: Entity to populate (can be scene.studio, scene.performers[0], etc.)
        fields: Fields to populate. If None, uses heuristic for incomplete objects.
        force_refetch: If True, invalidates cache for these fields and re-fetches.

    Returns:
        The populated entity (may be same or new instance from cache).

    Examples:
        # Populate specific fields on nested object
        scene.studio = await store.populate(scene.studio, fields=["name", "urls"])

        # Force refresh from server
        scene = await store.populate(scene, fields=["studio", "performers"], force_refetch=True)

        # Access nested object directly - works because scene.studio IS a StashObject
        studio = await store.populate(scene.studio, fields=["urls", "details"])
    """
    if fields is None:
        fields = set()
    elif isinstance(fields, list):
        fields = set(fields)

    received = getattr(obj, "_received_fields", set())

    # Determine which fields genuinely need fetching
    if force_refetch:
        # Force refetch all requested fields
        fields_to_fetch = list(fields)
    else:
        # Only fetch fields not already received
        fields_to_fetch = [f for f in fields if f not in received]

    if not fields_to_fetch:
        return obj  # All requested fields already present

    # Invalidate cache entry if force_refetch
    if force_refetch:
        self.invalidate(type(obj), obj.id)

    # Fetch with specific fields
    refreshed = await self.get(type(obj), obj.id, fields=fields_to_fetch)
    if refreshed:
        # Merge received fields (existing + newly fetched)
        new_received = received | getattr(refreshed, "_received_fields", set())
        object.__setattr__(refreshed, "_received_fields", new_received)
        return refreshed

    return obj
```

**Key Point**: `scene.studio` CAN be passed to populate because it's a `StashObject`:
```python
# All of these work:
await store.populate(scene, fields=["studio", "performers"])
await store.populate(scene.studio, fields=["urls", "details"])
await store.populate(scene.performers[0], fields=["scenes", "images"])
```

## Implementation Phases

### Phase 1: Field Tracking (this prototype)

1. Add `_received_fields` tracking to `StashObject.handle_stub_data` (or new validator)
2. Remove `_is_stub` marker (replaced by field tracking)
3. Update `StashEntityStore._needs_population()` to check `_received_fields`

### Phase 2: Cache Integration

1. Add store context injection during entity construction
2. Implement nested object extraction and caching
3. Ensure `scene.studio` returns cached reference

### Phase 3: Enhanced Populate

1. Update `populate()` to check `_received_fields`
2. Merge received fields on refetch
3. Add field-aware `is_complete(*fields)` check

## Files to Modify

1. `stash_graphql_client/types/base.py`
   - Add `_received_fields` tracking in validator
   - Remove/deprecate `_is_stub` marker

2. `stash_graphql_client/store.py`
   - Update `_needs_population()` for field awareness
   - Add context injection for entity construction
   - Enhance `populate()` for field-aware fetching

3. `stash_graphql_client/types/scene.py` (prototype target)
   - Test integration with Scene.studio and Scene.performers

## Testing Strategy

1. Unit test: `_received_fields` is correctly populated
2. Unit test: Nested objects are cached on construction
3. Unit test: `populate("field")` only fetches if field missing
4. Integration test: Scene with studio/performers round-trip

## Questions to Resolve

1. Should `_received_fields` include nested object fields (e.g., "studio") or just scalar fields?
   - Recommendation: Include all top-level fields that were present in the dict

2. How to handle partial updates when cache has richer data than current response?
   - Recommendation: Merge strategy - keep existing data, add new fields

3. Should we use Pydantic's validation context for store injection?
   - Yes, via `model_validate(data, context={"store": store})`
