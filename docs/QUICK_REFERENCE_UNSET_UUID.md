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

| Pattern | Use When | Example |
|---------|----------|---------|
| **Set to value** | Field has a value | `scene.title = "Test"` |
| **Set to null** | Want to clear server value | `scene.rating = None` |
| **UNSET** | Don't touch server value | `scene.details = UNSET` |
| **Auto UUID** | Creating new object | `scene = Scene(title="Test")` |
| **is_new()** | Check if saved | `if scene.is_new(): ...` |
| **update_id()** | After create (auto in save) | `scene.update_id("123")` |

---

## Additional Resources

- **Full Guide**: `/docs/UNSET_AND_UUID_PATTERNS.md`
- **Architecture**: `/docs/ARCHITECTURAL_CHANGES_SUMMARY.md`
- **Implementation**: `/IMPLEMENTATION_REPORT.md`
- **Tests**: `/tests/types/test_unset_and_uuid_patterns.py`
