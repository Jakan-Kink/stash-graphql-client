# Quick Reference: UNSET & UUID4 Patterns

One-page reference for developers using the UNSET sentinel and UUID4 auto-generation patterns.

---

## UNSET Sentinel

### Import

```python
from stash_graphql_client.types import UNSET, UnsetType
```

### Three Field States

```python
scene.title = "Test"   # Level 1: Set to value
scene.title = None     # Level 2: Set to null
scene.title = UNSET    # Level 3: Never touched
```

### Checking Field State

```python
# ✅ CORRECT - Use identity comparison (is)
if scene.title is UNSET:
    print("Never touched")
elif scene.title is None:
    print("Explicitly null")
else:
    print(f"Value: {scene.title}")

# ❌ WRONG - Don't use equality or boolean
if not scene.title:  # Ambiguous! Could be UNSET, None, or empty string
    pass
```

### Field Definitions

```python
class MyEntity(StashObject):
    # Required field with UNSET default
    name: str | UnsetType = UNSET

    # Optional field (can be null)
    description: str | None | UnsetType = UNSET

    # Required field (no default)
    id: str
```

### to_input() Pattern

```python
async def to_input(self) -> dict[str, Any]:
    data = {}

    # Only include non-UNSET fields
    if self.name is not UNSET:
        data["name"] = self.name

    if self.description is not UNSET:
        data["description"] = self.description  # Could be None or value

    return data
```

### Common Patterns

```python
# Describe field state
def describe(value):
    if value is UNSET:
        return "UNSET"
    elif value is None:
        return "NULL"
    else:
        return f"VALUE: {value}"

# Build GraphQL input excluding UNSET
def build_input(**fields):
    return {k: v for k, v in fields.items() if v is not UNSET}

# Set field conditionally
if some_condition:
    scene.rating = 85
else:
    scene.rating = UNSET  # Don't touch this field
```

---

## UUID4 Auto-Generation

### Creating New Objects

```python
# UUID4 is auto-generated
scene = Scene(title="Test")
print(scene.id)        # "a1b2c3d4e5f6789012345678901234ab"
print(scene.is_new())  # True

# Explicit ID (no UUID generated)
scene = Scene(id="123", title="Test")
print(scene.is_new())  # False
```

### Checking if New

```python
if scene.is_new():
    print("This is a new object with temporary UUID")
else:
    print("This is an existing object with server ID")
```

### Save Workflow

```python
# Create new object
scene = Scene(title="Test")
temp_id = scene.id  # UUID4

# Save to server
await scene.save(client)

# ID is now server-assigned
print(scene.id)        # "456" (server ID)
print(scene.is_new())  # False
print(temp_id != scene.id)  # True
```

### Manual ID Update

```python
# Normally done automatically by save()
scene = Scene(title="Test")
scene.update_id("789")  # Replace UUID with server ID
```

### Detection Logic

```python
# is_new() returns True if:
# - ID is 32 hex characters (UUID4)
# - ID is legacy "new" marker
# - ID is empty/None

# Examples:
Scene(title="Test").is_new()     # True (UUID4)
Scene(id="new", ...).is_new()    # True (legacy marker)
Scene(id="123", ...).is_new()    # False (server ID)
Scene(id="", ...).is_new()       # True (empty)
```

---

## Combined Usage

### Creating and Saving New Object

```python
from stash_graphql_client.types import Scene, UNSET

# Create new scene with partial data
scene = Scene(
    title="My Scene",       # Set
    rating100=None,         # Explicitly null
    # details = UNSET      # Never touched (implicit)
)

print(scene.is_new())      # True
print(scene.id[:8])        # "a1b2c3d4" (UUID4 prefix)

# to_input() includes only set fields
input_dict = await scene.to_input()
# {"title": "My Scene", "rating100": null}
# "details" excluded because UNSET

# Save to server
await scene.save(client)

print(scene.is_new())      # False
print(scene.id)            # "123" (server ID)
```

### Partial Update

```python
# Fetch existing object
scene = await client.find_scene("123")

# Update only one field
scene.title = "Updated Title"
# Other fields remain unchanged (not marked dirty)

# to_input() only includes changed fields + ID
input_dict = await scene.to_input()
# {"id": "123", "title": "Updated Title"}

# Save sends minimal update
await scene.save(client)
```

### Explicit Null vs UNSET

```python
scene = await client.find_scene("123")

# Set to null (clear server value)
scene.rating100 = None
await scene.save(client)
# Server: rating100 = null

# Leave UNSET (don't touch server value)
scene.details = UNSET
await scene.save(client)
# Server: details unchanged
```

---

## Testing Patterns

### Test UNSET

```python
def test_unset_excluded():
    scene = Scene(id="123", title="Test")
    scene.rating = UNSET

    input_dict = await scene.to_input()

    assert "title" in input_dict
    assert "rating" not in input_dict  # UNSET excluded
```

### Test UUID4

```python
def test_new_object_gets_uuid():
    scene = Scene(title="Test")

    assert scene.id is not None
    assert len(scene.id) == 32
    assert scene.is_new() is True

def test_save_updates_id(respx_mock, client):
    scene = Scene(title="Test")
    original_id = scene.id

    # Mock response
    respx.post("http://localhost:9999/graphql").mock(
        return_value=httpx.Response(200, json={"data": {"sceneCreate": {"id": "456"}}})
    )

    await scene.save(client)

    assert scene.id == "456"
    assert scene.id != original_id
    assert scene.is_new() is False
```

---

## Common Mistakes

### ❌ Wrong: Using == with UNSET

```python
# Don't do this
if field == UNSET:  # Works but 'is' is better for singletons
    pass
```

### ✅ Right: Using is with UNSET

```python
# Do this
if field is UNSET:
    pass
```

### ❌ Wrong: Boolean check for UNSET

```python
# Don't do this - ambiguous!
if not field:  # Could be UNSET, None, 0, empty string, etc.
    pass
```

### ✅ Right: Explicit UNSET check

```python
# Do this
if field is UNSET:
    pass
elif field is None:
    pass
else:
    pass
```

### ❌ Wrong: Manually setting UUID

```python
# Don't do this
scene = Scene(id=uuid.uuid4().hex, title="Test")
```

### ✅ Right: Let it auto-generate

```python
# Do this
scene = Scene(title="Test")  # UUID auto-generated
```

---

## Type Annotations

### For Fields

```python
from stash_graphql_client.types.unset import UnsetType

# Required field with UNSET default
title: str | UnsetType = UNSET

# Optional field (nullable)
description: str | None | UnsetType = UNSET

# Required field (no UNSET)
id: str
```

### For Functions

```python
from typing import Any

def process_field(value: str | None | UnsetType) -> Any:
    if value is UNSET:
        return None
    elif value is None:
        return "NULL"
    else:
        return value.upper()  # mypy knows it's str here
```

---

## Performance Notes

- **UUID4 generation**: ~0.1μs per object
- **UNSET check**: O(1) identity comparison
- **Memory**: UNSET is a singleton (minimal overhead)

---

## Summary

| Pattern          | Use When                    | Example                       |
| ---------------- | --------------------------- | ----------------------------- |
| **Set to value** | Field has a value           | `scene.title = "Test"`        |
| **Set to null**  | Want to clear server value  | `scene.rating = None`         |
| **UNSET**        | Don't touch server value    | `scene.details = UNSET`       |
| **Auto UUID**    | Creating new object         | `scene = Scene(title="Test")` |
| **is_new()**     | Check if saved              | `if scene.is_new(): ...`      |
| **update_id()**  | After create (auto in save) | `scene.update_id("123")`      |

---

## Convenience Helper Methods

Some entity types provide convenience methods for relationship management.

### Scene Helpers (5 methods)

```python
# Add entities to scene
scene.add_to_gallery(gallery)        # Add scene to gallery
scene.remove_from_gallery(gallery)   # Remove scene from gallery
scene.add_performer(performer)       # Add performer to scene
scene.add_tag(tag)                   # Add tag to scene
scene.set_studio(studio)             # Set scene's studio

# To remove performers/tags, use direct list manipulation:
scene.performers.remove(performer)   # Remove performer
scene.tags.remove(tag)               # Remove tag
await scene.save(client)             # Save changes
```

### Tag Helpers (6 methods)

```python
# Parent/child relationships (bidirectional)
tag.add_parent(parent_tag)           # Add parent tag (syncs both sides)
tag.remove_parent(parent_tag)        # Remove parent tag (syncs both sides)
tag.add_child(child_tag)             # Add child tag (syncs both sides)
tag.remove_child(child_tag)          # Remove child tag (syncs both sides)

# Recursive hierarchy traversal
descendants = tag.get_all_descendants()  # Get all descendant tags
ancestors = tag.get_all_ancestors()      # Get all ancestor tags
```

### Entity Mapping Helpers

Convert entity names to IDs with auto-creation support:

```python
# Map tag names to IDs
tag_ids = await client.map_tag_ids(
    ["Action", "Drama", "NewTag"],
    create=True  # Auto-create missing tags
)

# Map studio names to IDs
studio_ids = await client.map_studio_ids(
    ["Studio A", "Studio B"],
    create=True
)

# Map performer names to IDs (includes alias search)
performer_ids = await client.map_performer_ids(
    ["Jane Doe", "John Smith"],
    create=True,
    on_multiple=OnMultipleMatch.RETURN_FIRST  # Handle duplicates
)
```

### Studio Hierarchy Helpers

```python
# Get full parent chain from root to studio
hierarchy = await client.find_studio_hierarchy(studio_id)
# Returns: [<Root Studio>, <Parent Studio>, <Child Studio>]

# Find the top-level parent studio
root = await client.find_studio_root(studio_id)
```

### Notes

- **Group convenience helpers** are documented in [Bidirectional Relationships](../architecture/bidirectional-relationships.md) but not yet implemented. Currently, manage group relationships using direct field assignment with `containing_groups` and `sub_groups` fields.
- **Other entity types** (Performer, Gallery, Image, etc.) do not have convenience helpers - use direct field assignment instead.

---

## Additional Resources

- **Full Guide**: [UNSET & UUID4 Patterns](../guide/unset-pattern.md) - Comprehensive guide with examples
- **Usage Examples**: [Convenience Methods](../guide/usage-examples.md) - ID mapping, hierarchy navigation
- **Architecture**: [Bidirectional Relationships](../architecture/bidirectional-relationships.md) - Entity relationship patterns
- **API Reference**: [StashEntityStore](../api/store.md) - Identity map and caching
