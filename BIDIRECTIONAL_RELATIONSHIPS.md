# Bi-Directional Relationship Implementation

**Last Updated:** 2025-12-14
**Status:** Implemented - Tier 1 (Automatic Backend Sync)

## Executive Summary

Empirical testing confirms that **Stash's backend automatically maintains bidirectional referential integrity for ALL relationship types**. No dual mutation coordination is required. This document details the findings and implementation approach.

## Empirical Verification Results

All tests passed (8/8) confirming automatic bidirectional synchronization:

| Test | Relationship | Pattern | Result |
|------|-------------|---------|--------|
| Gallery → Scene (forward) | Many-to-Many | Direct field | ✅ Auto-sync |
| Scene → Gallery (reverse) | Many-to-Many | Direct field | ✅ Auto-sync |
| Tag Parent → Child | Self-referential | Direct field | ✅ Auto-sync |
| Scene → Performer | Many-to-Many | Direct field | ✅ Auto-sync |
| Scene → Studio | Many-to-One | Filter query | ✅ Auto-sync |
| Group Hierarchy | Complex metadata | Nested objects | ✅ Auto-sync |
| **Edge Case:** Removal | Deletion propagation | N/A | ✅ Auto-sync |
| **Edge Case:** Bulk Update | Multiple relationships | N/A | ✅ Auto-sync |

### Test Details

**Test Script:** `verify_bidirectional_relationships.py`
**Verification Date:** 2025-12-14
**Stash Version:** Latest (as of test date)

Each test:
1. Created entities with relationships
2. Updated one side of the relationship
3. Verified the inverse side automatically updated
4. Cleaned up all test data

## Relationship Query Patterns

### Pattern A: Direct Nested Fields

**Used by:** Gallery, Performer, Tag, Group

**Reading:**
```graphql
query {
  findGallery(id: "123") {
    scenes {        # Direct field returns [Scene!]!
      id
      title
    }
  }
}
```

**Writing:**
```graphql
mutation {
  sceneUpdate(input: {
    id: "456"
    gallery_ids: ["123"]  # Updates scene → gallery link
  }) {
    id
  }
}
# Backend automatically updates gallery.scenes
```

**Python Example:**
```python
# Reading
scene = await client.find_scene("456")
galleries = scene.galleries  # [Gallery, Gallery, ...]

# Writing - both directions sync automatically
scene.galleries.append(new_gallery)
await scene.save(client)
# new_gallery.scenes now includes this scene (no second save needed!)
```

### Pattern B: Filter-Based Queries

**Used by:** Studio (and potentially others)

**Why this pattern?**
- More flexible (supports pagination, sorting, complex filters)
- Studio doesn't have a direct `scenes` field
- Instead, query scenes BY studio using filters

**Reading:**
```graphql
query {
  findScenes(
    scene_filter: {
      studios: {
        value: ["studio_id"]
        modifier: INCLUDES
      }
    }
  ) {
    count
    scenes {
      id
      title
    }
  }
}
```

**Writing:**
```graphql
mutation {
  sceneUpdate(input: {
    id: "456"
    studio_id: "studio_id"
  }) {
    id
  }
}
# Backend automatically updates studio.scene_count and filter results
```

**Python Example:**
```python
# Reading - use filter query
scenes = await client.find_scenes(
    scene_filter={"studios": {"value": [studio.id]}}
)

# Writing - same as Pattern A
scene.studio = new_studio
await scene.save(client)
# Filter queries now return this scene for new_studio
```

### Pattern C: Complex Objects with Metadata

**Used by:** Group hierarchies

**Why this pattern?**
- Relationships have additional metadata (e.g., description)
- Not just a simple ID list

**Schema:**
```graphql
type GroupDescription {
  group: Group!         # The related group
  description: String   # Metadata about this relationship
}

type Group {
  sub_groups: [GroupDescription!]!
  containing_groups: [GroupDescription!]!
}
```

**Reading:**
```graphql
query {
  findGroup(id: "123") {
    sub_groups {
      group {
        id
        name
      }
      description  # Why this sub-group exists
    }
  }
}
```

**Writing:**
```graphql
mutation {
  groupUpdate(input: {
    id: "123"
    sub_groups: [{
      group_id: "456"
      description: "Season 1"
    }]
  }) {
    id
  }
}
# Backend automatically updates group 456's containing_groups
```

**Python Example:**
```python
# Reading - nested structure
group = await client.find_group("123")
for sub_group_desc in group.sub_groups:
    sub_group = sub_group_desc.group
    notes = sub_group_desc.description

# Writing
group.sub_groups = [
    GroupDescriptionInput(group_id="456", description="Season 1")
]
await group.save(client)
# Group 456's containing_groups now includes group 123
```

## Implementation Architecture

### RelationshipMetadata Class

```python
from dataclasses import dataclass
from typing import Callable, Literal

@dataclass(frozen=True)
class RelationshipMetadata:
    """Metadata describing a bidirectional relationship.

    All relationships in Stash auto-sync bidirectionally via backend
    referential integrity. This metadata documents how to read/write
    each relationship and provides convenience helpers.
    """

    # ===== Write Configuration (Mutations) =====
    target_field: str
    """Field name in *UpdateInput/*CreateInput (e.g., 'gallery_ids')."""

    is_list: bool
    """True for many-to-many, False for many-to-one."""

    transform: Callable[[Any], Any] | None = None
    """Optional transform for complex types (e.g., StashID → StashIDInput)."""

    # ===== Read Configuration (Queries) =====
    query_field: str | None = None
    """Field name when reading (e.g., 'galleries'). Defaults to relationship name."""

    inverse_type: type | None = None
    """Type of the related entity (e.g., Gallery)."""

    inverse_query_field: str | None = None
    """Field name on inverse type (e.g., 'scenes' on Gallery)."""

    # ===== Query Strategy =====
    query_strategy: Literal["direct_field", "filter_query", "complex_object"] = "direct_field"
    """How to query the inverse relationship:
    - 'direct_field': Use nested field (e.g., gallery.scenes)
    - 'filter_query': Use find* with filter (e.g., findScenes(scene_filter))
    - 'complex_object': Nested object with metadata (e.g., group.sub_groups[].group)
    """

    filter_query_hint: str | None = None
    """For filter_query strategy, example filter usage."""

    # ===== Documentation =====
    auto_sync: bool = True
    """Backend maintains referential integrity (always True for Stash)."""

    notes: str = ""
    """Additional implementation notes or caveats."""

    def __post_init__(self):
        """Set defaults after init."""
        # Default query_field to target_field if not provided
        if self.query_field is None:
            object.__setattr__(self, 'query_field', self.target_field.replace('_ids', 's').replace('_id', ''))
```

### Usage in Entity Types

#### Example 1: Scene (Multiple Patterns)

```python
class Scene(StashObject):
    __type_name__ = "Scene"
    __update_input_type__ = SceneUpdateInput

    __relationships__ = {
        # Pattern A: Direct field (many-to-many)
        "galleries": RelationshipMetadata(
            target_field="gallery_ids",
            is_list=True,
            query_field="galleries",
            inverse_type="Gallery",  # Forward ref to avoid circular import
            inverse_query_field="scenes",
            query_strategy="direct_field",
            notes="Both scene.galleries and gallery.scenes auto-sync"
        ),

        # Pattern A: Direct field (many-to-many)
        "performers": RelationshipMetadata(
            target_field="performer_ids",
            is_list=True,
            query_field="performers",
            inverse_type="Performer",
            inverse_query_field="scenes",
            query_strategy="direct_field",
        ),

        # Pattern B: Filter query (many-to-one)
        "studio": RelationshipMetadata(
            target_field="studio_id",
            is_list=False,
            query_field="studio",
            inverse_type="Studio",
            inverse_query_field=None,  # No direct field on Studio
            query_strategy="filter_query",
            filter_query_hint='findScenes(scene_filter={studios: {value: [studio_id]}})',
            notes="Studio has scene_count and filter queries, not direct scenes field"
        ),

        # Pattern A: Direct field (many-to-many)
        "tags": RelationshipMetadata(
            target_field="tag_ids",
            is_list=True,
            query_field="tags",
            inverse_type="Tag",
            inverse_query_field=None,  # Tag has scene_count only
            query_strategy="direct_field",
            notes="Tag has scene_count resolver, not scenes list"
        ),

        # Complex: StashID requires transform
        "stash_ids": RelationshipMetadata(
            target_field="stash_ids",
            is_list=True,
            transform=lambda s: StashIDInput(endpoint=s.endpoint, stash_id=s.stash_id),
            query_field="stash_ids",
            notes="Requires transform to StashIDInput"
        ),
    }
```

#### Example 2: Group (Complex Objects)

```python
class Group(StashObject):
    __type_name__ = "Group"
    __update_input_type__ = GroupUpdateInput

    __relationships__ = {
        # Pattern C: Complex objects with metadata
        "sub_groups": RelationshipMetadata(
            target_field="sub_groups",
            is_list=True,
            transform=lambda g: GroupDescriptionInput(
                group_id=g.group.id if isinstance(g, GroupDescription) else g.id,
                description=g.description if isinstance(g, GroupDescription) else None
            ),
            query_field="sub_groups",
            inverse_type="Group",
            inverse_query_field="containing_groups",
            query_strategy="complex_object",
            notes="Uses GroupDescription wrapper with nested group + description"
        ),

        "containing_groups": RelationshipMetadata(
            target_field="containing_groups",
            is_list=True,
            transform=lambda g: GroupDescriptionInput(
                group_id=g.group.id if isinstance(g, GroupDescription) else g.id,
                description=g.description if isinstance(g, GroupDescription) else None
            ),
            query_field="containing_groups",
            inverse_type="Group",
            inverse_query_field="sub_groups",
            query_strategy="complex_object",
        ),
    }
```

## Convenience Helper Methods

### Direct Field Helpers

```python
class Scene(StashObject):
    async def add_to_gallery(self, gallery: "Gallery") -> None:
        """Add this scene to a gallery (auto-syncs both sides).

        Backend automatically updates gallery.scenes - no second mutation needed.
        """
        if gallery not in self.galleries:
            self.galleries.append(gallery)
            await self.save()

    async def remove_from_gallery(self, gallery: "Gallery") -> None:
        """Remove this scene from a gallery (auto-syncs both sides)."""
        if gallery in self.galleries:
            self.galleries.remove(gallery)
            await self.save()
```

### Filter Query Helpers

```python
class Studio(StashObject):
    async def get_scenes(
        self,
        page: int = 1,
        per_page: int = 40,
        sort: str = "date",
        direction: str = "DESC",
        **additional_filters
    ) -> "FindScenesResultType":
        """Query all scenes for this studio using filter-based query.

        This is more powerful than a direct field since it supports:
        - Pagination
        - Sorting
        - Additional filters

        Args:
            page: Page number (1-indexed)
            per_page: Results per page
            sort: Sort field (date, title, rating, etc.)
            direction: Sort direction (ASC/DESC)
            **additional_filters: Additional scene filters

        Returns:
            FindScenesResultType with count and scenes
        """
        from .client import StashClient  # Avoid circular import

        client = self._get_client()
        return await client.find_scenes(
            filter={"page": page, "per_page": per_page, "sort": sort, "direction": direction},
            scene_filter={"studios": {"value": [self.id], "modifier": "INCLUDES"}, **additional_filters}
        )

    async def get_scene_count(self) -> int:
        """Get count of scenes for this studio (uses resolver field)."""
        # If already loaded, return cached
        if self.scene_count is not UNSET:
            return self.scene_count

        # Otherwise re-fetch with scene_count field
        client = self._get_client()
        fresh = await client.find_studio(self.id, fields=["scene_count"])
        return fresh.scene_count
```

### Complex Object Helpers

```python
class Group(StashObject):
    async def add_sub_group(
        self,
        sub_group: "Group",
        description: str | None = None
    ) -> None:
        """Add a sub-group to this group (auto-syncs both sides).

        Args:
            sub_group: The group to add as a sub-group
            description: Optional description of this relationship
        """
        sub_group_desc = GroupDescriptionInput(
            group_id=sub_group.id,
            description=description
        )

        if not any(sg.group.id == sub_group.id for sg in self.sub_groups):
            self.sub_groups.append(sub_group_desc)
            await self.save()
```

## Migration Notes

### Before (Old Pattern)

```python
__relationships__ = {
    "studio": ("studio_id", False, None),  # (target_field, is_list, transform)
    "performers": ("performer_ids", True, None),
    "galleries": ("gallery_ids", True, None),
}
```

### After (New Pattern)

```python
__relationships__ = {
    "studio": RelationshipMetadata(
        target_field="studio_id",
        is_list=False,
        inverse_type="Studio",
        query_strategy="filter_query",
        filter_query_hint='findScenes(scene_filter={studios: {value: [studio_id]}})',
    ),
    "performers": RelationshipMetadata(
        target_field="performer_ids",
        is_list=True,
        inverse_type="Performer",
        inverse_query_field="scenes",
    ),
    "galleries": RelationshipMetadata(
        target_field="gallery_ids",
        is_list=True,
        inverse_type="Gallery",
        inverse_query_field="scenes",
    ),
}
```

### Backward Compatibility

The new `RelationshipMetadata` class is designed to be backward compatible with the existing tuple pattern during migration:

1. Both patterns will coexist during transition
2. Helper methods will check metadata type and handle both
3. Gradual migration: update one entity type at a time
4. Full backward compatibility maintained until all types migrated

## Key Takeaways

1. ✅ **All relationships auto-sync** - Backend maintains referential integrity
2. ✅ **No dual mutations needed** - Single update syncs both sides
3. ✅ **Three query patterns** - Direct fields, filters, complex objects
4. ✅ **Edge cases work** - Removals and bulk updates both auto-sync
5. ✅ **Metadata for documentation** - Not for sync coordination
6. ✅ **Convenience helpers** - Simplify common operations

## Future Enhancements

- [ ] Auto-generate relationship metadata from GraphQL schema
- [ ] Add type hints for forward references (avoid circular imports)
- [ ] Generate convenience helpers automatically
- [ ] Add relationship validation (ensure IDs exist)
- [ ] Performance optimization for bulk relationship queries

## References

- **Verification Script:** `verify_bidirectional_relationships.py`
- **Test Results:** See "Empirical Verification Results" above
- **Implementation PR:** TBD
- **Related Issues:** TBD
