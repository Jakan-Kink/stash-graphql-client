# UNSET Sentinel and UUID4 Auto-Generation Patterns

This document describes the architectural patterns for field tracking, dirty detection, and identity management in the StashObject base class.

## Overview

Four critical architectural patterns are implemented in the `StashObject` base class:

1. **UUID4 Auto-Generation**: New objects receive a temporary UUID4 identifier that is replaced with the server-assigned ID after save operations
2. **UNSET Sentinel Pattern**: Three-level field system to distinguish between "set to value", "set to null", and "never touched"
3. **Field Tracking (\_received_fields)**: Tracks which fields were actually loaded from GraphQL responses
4. **Dirty Tracking (\_snapshot)**: Snapshot-based change detection for minimal update payloads

These patterns work together to enable:

- **Partial GraphQL fragments**: Load only needed fields, track what was loaded
- **Minimal mutations**: Send only changed fields to server
- **Null vs unset distinction**: Explicitly set null vs never touched
- **Identity management**: Track new vs existing objects with UUID transition

## UUID4 Auto-Generation for New Objects

### The Problem (Before)

Previously, new objects used the magic string `"new"` as a marker:

```python
# OLD PATTERN - DO NOT USE
scene = Scene(id="new", title="Test Scene")
```

This had several issues:

- Not type-safe (any string could be an ID)
- Required explicit `id="new"` in every new object creation
- Unclear intention (is "new" a valid ID or a marker?)

### The Solution (After)

New objects automatically receive a UUID4 hex string (32 characters) when created without an ID:

```python
# NEW PATTERN - RECOMMENDED
from stash_graphql_client.types import Scene

# Create new object - UUID4 auto-generated
scene = Scene(title="Test Scene")
print(scene.id)  # "a1b2c3d4e5f6789012345678901234ab"
print(scene.is_new())  # True

# After save, server assigns real ID
await scene.save(client)
print(scene.id)  # "123" (server-assigned)
print(scene.is_new())  # False
```

### UUID4 Methods

#### `is_new() -> bool`

Check if an object has a temporary UUID (not yet saved to server):

```python
scene = Scene(title="Example")
scene.is_new()  # True - has UUID4

scene.id = "123"  # Manually assign server ID
scene.is_new()  # False - numeric ID from server
```

**Detection Logic:**

- Returns `True` if ID is 32 hex characters (UUID4) and not all digits
- Returns `True` if ID is the legacy `"new"` marker
- Returns `False` for numeric IDs (typical server IDs)

#### `update_id(server_id: str) -> None`

Replace temporary UUID with server-assigned ID:

```python
scene = Scene(title="Example")
old_id = scene.id  # UUID4 hex string

# Manually update after server returns ID
scene.update_id("456")
print(scene.id)  # "456"
```

**Note:** The `save()` method automatically calls `update_id()` after successful create operations.

### Auto-Generation Behavior

The UUID4 is generated in `StashObject.__init__()`:

```python
def __init__(self, **data: Any) -> None:
    # Auto-generate UUID4 for new objects without an ID
    if "id" not in data or data.get("id") is None:
        data["id"] = uuid.uuid4().hex
        log.debug(
            f"Auto-generated UUID4 for new {self.__class__.__name__}: {data['id']}"
        )
    super().__init__(**data)
```

**When UUID4 is Generated:**

- ✅ No `id` parameter provided: `Scene(title="Test")`
- ✅ `id=None` explicitly passed: `Scene(id=None, title="Test")`
- ❌ `id` with any string value: `Scene(id="123", title="Test")`

## UNSET Sentinel Pattern (Three-Level Field System)

### The Problem (Before)

Traditional two-level field systems only have:

1. Set to a value: `field = "value"`
2. Set to null: `field = None`

This makes partial updates impossible without sending all fields:

```python
# TWO-LEVEL SYSTEM PROBLEM
scene.title = "Updated Title"
scene.rating100 = None  # Want to set to null
# scene.details = ??? How to say "don't touch this field"?

# to_input() has to include ALL fields to be safe
await scene.save(client)  # Overwrites details even though we didn't touch it!
```

### The Solution (After)

The UNSET sentinel provides a third state for "never touched":

```python
from stash_graphql_client.types import Scene, UNSET

# Three possible states for each field:
scene.title = "Updated Title"  # 1. Set to value
scene.rating100 = None          # 2. Set to null
scene.details = UNSET           # 3. Never touched (don't include in input)

# to_input() only includes fields that are NOT UNSET
input_dict = await scene.to_input()
# {"id": "123", "title": "Updated Title", "rating100": null}
# "details" is excluded because it's UNSET
```

### UNSET Sentinel Implementation

The `UNSET` sentinel is a singleton instance defined in `types/unset.py`:

```python
class UnsetType:
    """Sentinel value representing an unset field."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "UNSET"

    def __bool__(self) -> bool:
        return False  # UNSET is always falsy

    def __eq__(self, other) -> bool:
        return isinstance(other, UnsetType)

    def __hash__(self) -> int:
        return hash("UNSET")

# Singleton instance - use this throughout the codebase
UNSET = UnsetType()
```

### Field Definition Pattern

Entity types should define fields with UNSET as the default:

```python
from pydantic import BaseModel
from stash_graphql_client.types.unset import UNSET, UnsetType

class Scene(StashObject):
    """Scene entity with UNSET sentinel support."""

    # Required in schema, but UNSET if not in GraphQL fragment
    title: str | UnsetType = UNSET

    # Optional in schema, can be null, value, or UNSET
    rating100: int | None | UnsetType = UNSET
    details: str | None | UnsetType = UNSET

    # Required fields without defaults (always provided)
    id: str
```

**Type Annotation Pattern:**

- For required fields: `field: Type | UnsetType = UNSET`
- For optional fields: `field: Type | None | UnsetType = UNSET`
- For always-required fields: `field: Type` (no default)

### Using UNSET in to_input() Methods

When converting to GraphQL input types, exclude UNSET fields:

```python
async def to_input(self) -> dict[str, Any]:
    """Convert to GraphQL input, excluding UNSET fields."""
    input_dict = {}

    # Only include fields that are NOT UNSET
    if self.title is not UNSET:
        input_dict["title"] = self.title

    if self.rating100 is not UNSET:
        input_dict["rating100"] = self.rating100  # Could be None or a value

    if self.details is not UNSET:
        input_dict["details"] = self.details  # Could be None or a value

    return input_dict
```

**Note:** The base `StashObject.to_input()` method handles this automatically when using Pydantic's `exclude_none=True`. For full UNSET support, entity types need custom serialization logic.

### Checking for UNSET

Use identity comparison (`is`) to check for UNSET:

```python
# ✅ CORRECT - use identity comparison
if scene.title is UNSET:
    print("Title was never set")

if scene.title is not UNSET:
    print(f"Title is: {scene.title}")  # Could be value or None

# ❌ WRONG - don't use equality comparison
if scene.title == UNSET:  # This works but 'is' is preferred for singletons
    print("Title was never set")

# ❌ WRONG - don't use boolean check
if not scene.title:  # This is True for UNSET, None, and empty string!
    print("Ambiguous - could be UNSET, None, or empty")
```

## Field Tracking with \_received_fields

### The Problem

When loading partial GraphQL fragments, we need to know which fields were actually included in the response:

```python
# Partial fragment - only loaded id and title
scene_data = {"id": "123", "title": "Test Scene"}
scene = Scene.from_graphql(scene_data)

# How do we know that rating100 wasn't loaded vs was loaded as null?
print(scene.rating100)  # UNSET or None?
```

### The Solution

The `_received_fields` attribute tracks which fields were actually present in the GraphQL response:

```python
from stash_graphql_client.types import Scene

# Load from GraphQL with partial data
scene = Scene.from_graphql({
    "id": "123",
    "title": "Test Scene",
    "rating100": None  # Explicitly null in response
})

print(scene._received_fields)  # {"id", "title", "rating100"}
print(scene.title)  # "Test Scene"
print(scene.rating100)  # None (was in response)
print(scene.details)  # UNSET (not in response)
```

### How \_received_fields Works

1. **Set during from_graphql()**: When data comes from GraphQL, the `_identity_map_validator` tracks field names
2. **Merged on cache hits**: If cached object receives new fields, they're merged into existing `_received_fields`
3. **Empty for manual construction**: Objects created with constructors have empty `_received_fields`

```python
# From GraphQL - tracks received fields
scene1 = Scene.from_graphql({"id": "123", "title": "Test"})
print(scene1._received_fields)  # {"id", "title"}

# Direct construction - no tracking
scene2 = Scene(id="456", title="Test")
print(scene2._received_fields)  # set() - empty
```

### Use Cases for \_received_fields

**1. Detecting partial loads:**

```python
if "rating100" not in scene._received_fields:
    print("Rating was not loaded - fetch it if needed")
    await scene.populate(client, ["rating100"])
```

**2. Merging partial fragments:**

```python
# First query loads basic fields
scene = await client.find_scene("123")  # id, title
print(scene._received_fields)  # {"id", "title", ...}

# Second query loads additional fields
detailed = await client.find_scene_with_files("123")  # id, title, files
# Identity map merges: same object, more fields
print(scene._received_fields)  # {"id", "title", "files", ...}
assert scene is detailed  # Same cached object!
```

**3. Debugging GraphQL queries:**

```python
def validate_fields(obj: StashObject, required: set[str]):
    """Ensure all required fields were loaded."""
    missing = required - obj._received_fields
    if missing:
        raise ValueError(f"Missing required fields: {missing}")
```

## Dirty Tracking with \_snapshot

### The Problem

When updating existing objects, we only want to send changed fields to avoid overwriting server data:

```python
scene = await client.find_scene("123")
scene.title = "Updated Title"  # Changed
scene.rating100 = scene.rating100  # Not changed (same value)

# How do we know which fields actually changed?
# We need to compare current state to original state
```

### The Solution

The `_snapshot` attribute stores the original state after object construction. Dirty tracking methods compare current state to snapshot:

```python
from stash_graphql_client.types import Scene

# Load from server
scene = await client.find_scene("123")
# _snapshot is automatically created with original values

print(scene.is_dirty())  # False - no changes yet

scene.title = "Updated Title"
print(scene.is_dirty())  # True - title changed

dirty_fields = scene.get_changed_fields()
print(dirty_fields)  # {"title": "Updated Title"}
```

### Dirty Tracking Methods

#### `is_dirty() -> bool`

Check if object has unsaved changes:

```python
scene = await client.find_scene("123")
print(scene.is_dirty())  # False

scene.title = "New Title"
print(scene.is_dirty())  # True

await scene.save(client)
print(scene.is_dirty())  # False - save() calls mark_clean()
```

#### `get_changed_fields() -> dict[str, Any]`

Get dictionary of changed fields and their current values:

```python
scene.title = "Updated Title"
scene.rating100 = 90

changed = scene.get_changed_fields()
print(changed)  # {"title": "Updated Title", "rating100": 90}
```

**Note:** Only fields in `__tracked_fields__` are included in change detection.

#### `mark_clean() -> None`

Mark object as clean (no unsaved changes). Updates snapshot to current state:

```python
scene.title = "Updated"
print(scene.is_dirty())  # True

scene.mark_clean()  # Update snapshot
print(scene.is_dirty())  # False
print(scene.get_changed_fields())  # {}
```

#### `mark_dirty() -> None`

Force object to be considered dirty by clearing the snapshot:

```python
scene = await client.find_scene("123")
print(scene.is_dirty())  # False

scene.mark_dirty()  # Clear snapshot
print(scene.is_dirty())  # True
print(scene.get_changed_fields())  # All tracked fields
```

### How \_snapshot Works

1. **Created in model_post_init()**: After Pydantic initializes all fields, snapshot is taken
2. **Uses model_dump()**: Leverages Pydantic's serialization for accurate state capture
3. **Updated on mark_clean()**: Save operations call `mark_clean()` to update snapshot
4. **Compared by get_changed_fields()**: Compares current `model_dump()` to `_snapshot`

```python
class StashObject(BaseModel):
    def model_post_init(self, _context: Any) -> None:
        """Called after Pydantic initialization."""
        # Capture initial state
        self._snapshot = self.model_dump()

    def is_dirty(self) -> bool:
        """Compare current state to snapshot."""
        return self.model_dump() != self._snapshot

    def get_changed_fields(self) -> dict[str, Any]:
        """Find fields that differ from snapshot."""
        current = self.model_dump()
        changed = {}
        for field in self.__tracked_fields__:
            if current.get(field) != self._snapshot.get(field):
                changed[field] = current[field]
        return changed
```

## How to_input() Uses UNSET, \_received_fields, and \_snapshot

### The Complete Flow

The `to_input()` method combines all three tracking mechanisms to generate minimal GraphQL mutation inputs:

```python
async def to_input(self) -> dict[str, Any]:
    """Convert to GraphQL input type.

    For new objects: Uses _to_input_all() - all non-UNSET fields
    For existing objects: Uses _to_input_dirty() - only changed fields
    """
    input_obj = (
        await self._to_input_all()   # New object path
        if self.is_new()
        else await self._to_input_dirty()  # Existing object path
    )

    return input_obj.model_dump(exclude_none=True)
```

### New Objects: \_to_input_all()

For new objects (UUID id, `_is_new=True`), include all fields that are not UNSET:

```python
scene = Scene.new(
    title="New Scene",
    rating100=85,
    # details left as UNSET
)

input_dict = await scene.to_input()
# {
#   "title": "New Scene",
#   "rating100": 85
#   # "details" excluded (UNSET)
# }
```

**Behavior:**

- Processes all `__field_conversions__` fields
- Processes all `__relationships__` fields
- **Excludes UNSET fields** (never set)
- **Includes None fields** (explicitly set to null)
- Uses `__create_input_type__` for validation

### Existing Objects: \_to_input_dirty()

For existing objects, only include changed fields based on snapshot comparison:

```python
scene = await client.find_scene("123")
# _snapshot = {"id": "123", "title": "Original", "rating100": 70, ...}

scene.title = "Updated Title"  # Changed
# scene.rating100 unchanged

input_dict = await scene.to_input()
# {
#   "id": "123",
#   "title": "Updated Title"
#   # rating100 NOT included (not dirty)
# }
```

**Behavior:**

1. Get changed fields: `dirty_fields = set(self.get_changed_fields().keys())`
2. Process only dirty fields from `__field_conversions__`
3. Process only dirty relationships from `__relationships__`
4. **Always include ID** (required for updates)
5. **Exclude UNSET fields** (unchanged or never loaded)
6. **Include None fields if dirty** (changed to null)
7. Uses `__update_input_type__` for validation

### Example: All Three Systems Together

```python
# 1. Load from GraphQL (sets _received_fields and _snapshot)
scene = Scene.from_graphql({
    "id": "123",
    "title": "Original Title",
    "rating100": 70,
    "details": None  # Explicitly null
    # "url" not in fragment
})

print(scene._received_fields)  # {"id", "title", "rating100", "details"}
print(scene._snapshot)  # {"id": "123", "title": "Original Title", ...}
print(scene.url)  # UNSET (not loaded)
print(scene.details)  # None (was null in response)

# 2. Make changes
scene.title = "Updated Title"  # Change tracked field
scene.rating100 = None  # Change to null
scene.url = UNSET  # Explicitly keep as UNSET (don't send)
# scene.details unchanged (still None)

# 3. Check dirty state
print(scene.is_dirty())  # True
print(scene.get_changed_fields())  # {"title": "Updated Title", "rating100": None}

# 4. Generate minimal input (only dirty fields)
input_dict = await scene.to_input()
print(input_dict)
# {
#   "id": "123",
#   "title": "Updated Title",  # Changed
#   "rating100": None          # Changed to null - INCLUDED
#   # details NOT included (unchanged)
#   # url NOT included (UNSET)
# }

# 5. Save and mark clean
await scene.save(client)
print(scene.is_dirty())  # False
```

### Decision Matrix for to_input()

| Field State              | New Object  | Existing Object | Sent to Server? |
| ------------------------ | ----------- | --------------- | --------------- |
| Set to value             | ✅ Included | Only if dirty   | Yes             |
| Set to None              | ✅ Included | Only if dirty   | Yes (null)      |
| UNSET                    | ❌ Excluded | ❌ Excluded     | No              |
| Unchanged value          | ✅ Included | ❌ Excluded     | Depends         |
| Not in \_received_fields | N/A         | ❌ Excluded     | No              |

**Key insight:** UNSET exclusion happens at field processing level, dirty detection happens at change tracking level.

## Practical Examples

### Example 1: Creating a New Scene

```python
from stash_graphql_client import StashClient
from stash_graphql_client.types import Scene, UNSET

# Create new scene - UUID4 auto-generated
scene = Scene(
    title="My New Scene",
    rating100=85,
    # details left as UNSET - will be excluded from create input
)

print(scene.id)        # "a1b2c3d4..." (UUID4)
print(scene.is_new())  # True
print(scene.title)     # "My New Scene"
print(scene.details)   # UNSET

# Save to server
await scene.save(client)

print(scene.id)        # "123" (server-assigned)
print(scene.is_new())  # False
```

### Example 2: Partial Update (Only Changed Fields)

```python
# Fetch existing scene from server
scene = await client.find_scene("123")

print(scene.title)     # "Original Title"
print(scene.rating100) # 70
print(scene.details)   # "Original details"

# Update only one field
scene.title = "Updated Title"

# to_input() only includes changed field + ID
input_dict = await scene.to_input()
# {"id": "123", "title": "Updated Title"}
# rating100 and details are NOT included (not dirty)

# Save sends only the changed field
await scene.save(client)
```

### Example 3: Setting Field to Null vs Unsetting

```python
scene = await client.find_scene("123")

# Set field to null (explicit null in GraphQL)
scene.rating100 = None
input_dict = await scene.to_input()
# {"id": "123", "rating100": null}
# Server will set rating100 to null

# vs. leaving field UNSET (omit from GraphQL input)
scene.details = UNSET
input_dict = await scene.to_input()
# {"id": "123"}
# Server keeps existing details value unchanged
```

### Example 4: Checking Field State

```python
scene = Scene(title="Test")

# Check the three states
if scene.title is not UNSET:
    if scene.title is None:
        print("Title is explicitly null")
    else:
        print(f"Title is set to: {scene.title}")
else:
    print("Title was never touched")

# Using a helper function
def describe_field(field_value):
    if field_value is UNSET:
        return "UNSET (never touched)"
    elif field_value is None:
        return "NULL (explicitly set to null)"
    else:
        return f"VALUE: {field_value}"

print(describe_field(scene.title))     # "VALUE: Test"
print(describe_field(scene.rating100)) # "UNSET (never touched)"
```

## Migration Guide for Entity Types

When migrating entity types to use the UNSET pattern:

### Step 1: Import UNSET

```python
from stash_graphql_client.types.unset import UNSET, UnsetType
```

### Step 2: Update Field Definitions

**Before:**

```python
class Scene(StashObject):
    title: str | None = None
    rating100: int | None = None
```

**After:**

```python
class Scene(StashObject):
    title: str | UnsetType = UNSET
    rating100: int | None | UnsetType = UNSET
```

### Step 3: Update to_input() Method

Add UNSET checks when converting to input:

```python
async def to_input(self) -> dict[str, Any]:
    data = {"id": self.id}

    # Only include non-UNSET fields
    if self.title is not UNSET:
        data["title"] = self.title

    if self.rating100 is not UNSET:
        data["rating100"] = self.rating100

    return data
```

### Step 4: Update Tests

Test all three states:

```python
def test_unset_field_not_in_input():
    """UNSET fields should be excluded from input."""
    scene = Scene(id="123", title="Test")
    scene.rating100 = UNSET  # Explicitly UNSET

    input_dict = await scene.to_input()

    assert "title" in input_dict
    assert "rating100" not in input_dict  # UNSET fields excluded

def test_null_field_in_input():
    """None fields should be included in input."""
    scene = Scene(id="123", title="Test")
    scene.rating100 = None  # Explicitly null

    input_dict = await scene.to_input()

    assert "title" in input_dict
    assert "rating100" in input_dict
    assert input_dict["rating100"] is None
```

## Implementation Notes

### Identity Map Compatibility

The UNSET pattern is compatible with the identity map (entity cache):

```python
# Cached objects preserve UNSET state
scene1 = await store.get(Scene, "123")  # Fetched with partial fragment
print(scene1.details)  # UNSET (not in fragment)

# Same object from cache
scene2 = await store.get(Scene, "123")
assert scene1 is scene2  # Same reference
print(scene2.details)  # Still UNSET

# populate() can fetch missing fields
await store.populate(scene1, ["details"])
print(scene1.details)  # "Details from server" (no longer UNSET)
```

### Performance Considerations

- **UUID4 generation**: Minimal overhead (~0.1μs per object)
- **UNSET checks**: Identity comparison (`is`) is O(1)
- **Memory**: UNSET is a singleton, so only one instance exists in memory

### Type Checking with mypy

The UNSET pattern is fully type-safe with mypy:

```python
scene = Scene(title="Test")

# mypy knows title could be str or UnsetType
if scene.title is not UNSET:
    # In this block, mypy narrows type to just str
    print(scene.title.upper())  # ✅ OK - mypy knows it's str

# mypy error if you don't check first
print(scene.title.upper())  # ❌ Error - UnsetType has no attribute 'upper'
```

## Testing Patterns

### Test UUID4 Generation

```python
def test_new_object_gets_uuid():
    """New objects should auto-generate UUID4."""
    scene = Scene(title="Test")

    assert scene.id is not None
    assert len(scene.id) == 32  # UUID4 hex is 32 chars
    assert scene.is_new() is True

def test_existing_object_no_uuid():
    """Objects with server IDs should not be marked as new."""
    scene = Scene(id="123", title="Test")

    assert scene.id == "123"
    assert scene.is_new() is False

def test_update_id_after_save(respx_mock, stash_client):
    """save() should update UUID with server ID."""
    scene = Scene(title="Test")
    original_id = scene.id  # UUID4

    # Mock GraphQL response
    respx.post("http://localhost:9999/graphql").mock(
        return_value=httpx.Response(
            200, json={"data": {"sceneCreate": {"id": "456"}}}
        )
    )

    await scene.save(stash_client)

    assert scene.id == "456"
    assert scene.id != original_id
    assert scene.is_new() is False
```

### Test UNSET Pattern

```python
def test_unset_field_excluded():
    """UNSET fields should be excluded from to_input()."""
    scene = Scene(id="123", title="Test")
    scene.rating100 = UNSET

    input_dict = await scene.to_input()

    assert "rating100" not in input_dict

def test_null_field_included():
    """None fields should be included in to_input()."""
    scene = Scene(id="123", title="Test")
    scene.rating100 = None

    input_dict = await scene.to_input()

    assert "rating100" in input_dict
    assert input_dict["rating100"] is None

def test_value_field_included():
    """Value fields should be included in to_input()."""
    scene = Scene(id="123", title="Test")
    scene.rating100 = 85

    input_dict = await scene.to_input()

    assert "rating100" in input_dict
    assert input_dict["rating100"] == 85
```

## Future Enhancements

### Pydantic v2 Serialization

When fully migrated to Pydantic v2, we can use custom serializers:

```python
from pydantic import field_serializer

class Scene(StashObject):
    title: str | UnsetType = UNSET

    @field_serializer("title", when_used="json")
    def serialize_title(self, value):
        if value is UNSET:
            raise ValueError("UNSET should be excluded")
        return value
```

### msgspec Migration

For msgspec migration, UNSET integrates with `dec_hook`:

```python
import msgspec

def dec_hook(type, obj):
    """Custom decoder hook for msgspec."""
    if isinstance(obj, dict) and "id" in obj:
        # Check cache, return cached instance or construct new
        # UNSET is preserved for fields not in response
        pass
```

## Summary

### UUID4 Auto-Generation

- ✅ New objects get UUID4 automatically
- ✅ `is_new()` checks if object has temporary ID
- ✅ `update_id()` replaces UUID with server ID
- ✅ `save()` handles ID updates automatically
- ✅ `_is_new` attribute tracks new vs existing objects

### UNSET Sentinel Pattern

- ✅ Three-level field system: value, null, UNSET
- ✅ Partial updates only send changed fields
- ✅ Type-safe with mypy
- ✅ Compatible with identity map caching
- ✅ Minimal performance overhead
- ✅ Distinguishes "not set" from "set to null"

### Field Tracking with \_received_fields

- ✅ Tracks which fields came from GraphQL responses
- ✅ Set automatically by `from_graphql()`
- ✅ Merged on identity map cache hits
- ✅ Empty for manually constructed objects
- ✅ Enables partial fragment detection
- ✅ Supports progressive field loading

### Dirty Tracking with \_snapshot

- ✅ Stores original state after construction
- ✅ `is_dirty()` detects any unsaved changes
- ✅ `get_changed_fields()` returns modified fields
- ✅ `mark_clean()` updates snapshot after save
- ✅ `mark_dirty()` forces dirty state
- ✅ Enables minimal update payloads

### to_input() Integration

- ✅ `_to_input_all()` for new objects (all non-UNSET fields)
- ✅ `_to_input_dirty()` for existing objects (only changed fields)
- ✅ Combines UNSET filtering with dirty detection
- ✅ Always includes ID for updates
- ✅ Respects both snapshot changes and UNSET exclusions

### Best Practices

1. **Always use `is` for UNSET checks**: `if field is UNSET:`
2. **Set UNSET as default**: `field: Type | UnsetType = UNSET`
3. **Use from_graphql() for GraphQL data**: Enables `_received_fields` tracking
4. **Check is_dirty() before save**: Avoid unnecessary mutations
5. **Use get_changed_fields() for debugging**: See exactly what changed
6. **Let UUID4 auto-generate**: Don't manually set for new objects
7. **Test all three field states**: value, None, UNSET
8. **Trust the snapshot**: `mark_clean()` called automatically by `save()`
