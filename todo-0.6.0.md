# TODO: Version 0.6.0 - UNSET Type Narrowing Refactoring

**Status**: Deferred to v0.6.0
**Current State**: 100% test coverage, all tests passing
**Proven Solutions**: `is_set()` TypeGuard and `isinstance(x, UnsetType)` both work for type narrowing

## Background

The codebase uses a three-state field system with `UNSET` sentinel:

- `UNSET`: Field was never queried (default)
- `None`: Field explicitly set to null
- Actual value: Field has data

**Type Narrowing Issue**: Type checkers (Pylance, mypy) don't narrow types for `if x is UNSET` checks, but DO narrow for `isinstance(x, UnsetType)` and `is_set(x)` (TypeGuard).

**Proven Solutions**:

1. **Negative checks**: Use `isinstance(x, UnsetType)` instead of `if x is UNSET`
2. **Positive checks**: Use `is_set(x)` instead of `if x is not UNSET`

## Refactoring Statistics

**Total UNSET checks: 160 occurrences**

| Category                         | Count | Refactoring Approach                    |
| -------------------------------- | ----- | --------------------------------------- |
| Negative checks (`is UNSET`)     | 83    | Replace with `isinstance(x, UnsetType)` |
| Positive checks (`is not UNSET`) | 74    | Replace with `is_set(x)`                |
| Equality checks (`== UNSET`)     | 3     | Case-by-case evaluation                 |

## Refactoring Priority

### Priority 1: Helper Methods (16 occurrences)

**Impact**: High user visibility, moderate complexity
**Risk**: Low - well-tested with 100% coverage

#### Scene Helpers (`stash_graphql_client/types/scene.py`)

**6 occurrences** - Lines 313, 331, 347, 364, 380, 398

Current patterns:

```python
# Line 313 (negative check)
if self.galleries is UNSET:
    self.galleries = []

# Line 331 (positive check with AND)
if self.galleries is not UNSET and gallery in self.galleries:
    self.galleries.remove(gallery)
```

Refactored:

```python
# Line 313 (negative check)
if isinstance(self.galleries, UnsetType):
    self.galleries = []

# Line 331 (positive check with AND)
if is_set(self.galleries) and gallery in self.galleries:
    self.galleries.remove(gallery)
```

#### Performer Helpers (`stash_graphql_client/types/performer.py`)

**2 occurrences** - Lines 288, 306

Current patterns:

```python
# Line 288 (negative check)
if self.tags is UNSET:
    self.tags = []

# Line 306 (positive check with AND)
if self.tags is not UNSET and tag in self.tags:
    self.tags.remove(tag)
```

Refactored:

```python
# Line 288 (negative check)
if isinstance(self.tags, UnsetType):
    self.tags = []

# Line 306 (positive check with AND)
if is_set(self.tags) and tag in self.tags:
    self.tags.remove(tag)
```

#### Gallery Helpers (`stash_graphql_client/types/gallery.py`)

**3 occurrences** - Lines 229, 245, 263

Current patterns:

```python
# Line 229 (positive check with AND)
if self.performers is not UNSET and performer in self.performers:
    self.performers.remove(performer)

# Line 245 (negative check)
if self.scenes is UNSET:
    self.scenes = []
```

Refactored:

```python
# Line 229 (positive check with AND)
if is_set(self.performers) and performer in self.performers:
    self.performers.remove(performer)

# Line 245 (negative check)
if isinstance(self.scenes, UnsetType):
    self.scenes = []
```

#### Image Helpers (`stash_graphql_client/types/image.py`)

**4 occurrences** - Lines 195, 213, 229, 247

Current patterns:

```python
# Line 195 (negative check)
if self.performers is UNSET:
    self.performers = []

# Line 213 (positive check with AND)
if self.performers is not UNSET and performer in self.performers:
    self.performers.remove(performer)
```

Refactored:

```python
# Line 195 (negative check)
if isinstance(self.performers, UnsetType):
    self.performers = []

# Line 213 (positive check with AND)
if is_set(self.performers) and performer in self.performers:
    self.performers.remove(performer)
```

#### Studio Helpers (`stash_graphql_client/types/studio.py`)

**2 occurrences** - Lines 204, 224

Current patterns:

```python
# Line 204 (negative check with OR for None handling)
if self.child_studios is UNSET or self.child_studios is None:
    self.child_studios = []

# Line 224 (positive check in compound condition)
if (self.child_studios is not UNSET and
    self.child_studios is not None and
    child in self.child_studios):
```

Refactored:

```python
# Line 204 (negative check with OR for None handling)
if isinstance(self.child_studios, UnsetType) or self.child_studios is None:
    self.child_studios = []

# Line 224 (positive check in compound condition)
if (is_set(self.child_studios) and
    self.child_studios is not None and
    child in self.child_studios):
```

#### Group Helpers (`stash_graphql_client/types/group.py`)

**4 occurrences** - Lines 230, 243, 260, 270

Current patterns:

```python
# Line 230 (negative check)
if self.sub_groups is UNSET:
    self.sub_groups = []

# Line 243 (positive checks chained with AND)
if sg.group is not UNSET and sg.group.id is not UNSET:
    # ...

# Line 270 (negative checks chained with OR)
if sg.group is UNSET or sg.group.id is UNSET or sg.group.id != group_id:
    # ...
```

Refactored:

```python
# Line 230 (negative check)
if isinstance(self.sub_groups, UnsetType):
    self.sub_groups = []

# Line 243 (positive checks chained with AND)
if is_set(sg.group) and is_set(sg.group.id):
    # ...

# Line 270 (negative checks chained with OR)
if isinstance(sg.group, UnsetType) or isinstance(sg.group.id, UnsetType) or sg.group.id != group_id:
    # ...
```

### Priority 2: Scrape Parser (43 occurrences)

**Impact**: Critical for scraping functionality
**Risk**: High - complex compound conditions
**Recommendation**: Defer until after helper methods proven stable

#### File: `stash_graphql_client/utils/scrape_parser.py`

**43 occurrences** - Complex patterns requiring careful refactoring

**Pattern 1: Compound Negative Checks**

Lines 194, 206, 222, 234-245, 293, 306, 311, 316, 323, 330, 333-356

Current:

```python
# Line 194
if (
    studio_id is UNSET
    and scraped.studio is not None
    and scraped.studio is not UNSET
    and hasattr(scraped.studio, "stored_id")
    and scraped.studio.stored_id is not UNSET
    and scraped.studio.stored_id is not None
):
```

Refactored:

```python
# Line 194
if (
    isinstance(studio_id, UnsetType)
    and scraped.studio is not None
    and is_set(scraped.studio)
    and hasattr(scraped.studio, "stored_id")
    and is_set(scraped.studio.stored_id)
    and scraped.studio.stored_id is not None
):
```

**Pattern 2: Ternary Operator Assignments**

Lines 564, 571 (and many others in compound dict creation)

Current:

```python
title=scraped.title if scraped.title is not UNSET else UNSET,
```

Refactored:

```python
title=scraped.title if is_set(scraped.title) else UNSET,
```

**Note**: This file requires integration testing before/after refactoring to ensure scraping logic remains correct.

### Priority 3: Client Code (2 occurrences)

**Impact**: Low
**Risk**: Low

#### File: `stash_graphql_client/client/mixins/metadata.py`

**1 occurrence** - Line 202

Current:

```python
if config and config.defaults is not UNSET:
```

Refactored:

```python
if config and is_set(config.defaults):
```

#### File: `stash_graphql_client/client/mixins/studio.py`

**1 occurrence** - Line 276 (comment only, no action needed)

### Priority 4: Test Files (94 occurrences)

**Impact**: Low - tests work correctly
**Risk**: Low
**Recommendation**: Refactor opportunistically during test maintenance

#### Test Files with UNSET Checks

| File                                          | Count | Notes                    |
| --------------------------------------------- | ----- | ------------------------ |
| `tests/types/test_unset_and_uuid_patterns.py` | 17    | Pattern validation tests |
| `tests/utils/test_scrape_parser.py`           | 13    | Scraping logic tests     |
| `tests/types/test_image_helpers.py`           | 10    | Helper method tests      |
| `tests/types/test_gallery_helpers.py`         | 10    | Helper method tests      |
| `tests/types/test_scene_helpers.py`           | 7     | Helper method tests      |
| `tests/types/test_studio_helpers.py`          | 5     | Helper method tests      |
| `tests/types/test_studio.py`                  | 5     | Studio type tests        |
| `tests/types/test_unset.py`                   | 5     | UNSET behavior tests     |
| `tests/types/test_performer_helpers.py`       | 5     | Helper method tests      |
| `tests/types/test_group_helpers.py`           | 5     | Helper method tests      |
| `tests/types/test_validator_edge_cases.py`    | 2     | Edge case tests          |
| `tests/types/test_performer.py`               | 2     | Performer type tests     |
| `tests/types/test_files.py`                   | 2     | File handling tests      |
| `tests/types/test_inverse_sync.py`            | 1     | Relationship sync tests  |

**Refactoring Approach**: Update test assertions to use `is_set()` and `isinstance()` during normal test maintenance.

### Priority 5: Base Infrastructure (1 occurrence)

**Impact**: None (comment only)
**Risk**: None

#### File: `stash_graphql_client/types/base.py`

**1 occurrence** - Line 503 (comment only, no action needed)

## Implementation Plan

### Phase 1: Helper Methods (v0.6.0-alpha.1)

1. ✅ Verify `is_set()` and `isinstance()` work correctly (DONE - 100% tests passing)
2. Update all 16 helper method UNSET checks
3. Run full test suite to verify behavior unchanged
4. Update helper method tests if needed

**Expected changes:**

- 6 files modified (scene.py, performer.py, gallery.py, image.py, studio.py, group.py)
- ~16 lines changed
- 0 new test failures expected

### Phase 2: Scrape Parser (v0.6.0-alpha.2)

1. Review all 43 occurrences in scrape_parser.py
2. Create integration tests for scraping if not already present
3. Refactor compound conditions systematically
4. Verify scraping behavior with real-world test cases

**Expected changes:**

- 1 file modified (scrape_parser.py)
- ~43 lines changed
- Requires careful testing

### Phase 3: Client & Remaining Code (v0.6.0-alpha.3)

1. Update client mixin code (2 occurrences)
2. Opportunistically update test files during maintenance
3. Update any remaining edge cases

**Expected changes:**

- 2 client files modified
- ~94 test file changes (low priority)

### Phase 4: Documentation (v0.6.0-beta.1)

1. Update CLAUDE.md with type narrowing best practices
2. Add examples to type system documentation
3. Create migration guide for external users

## Type Narrowing Examples

### Negative Checks (Initialize Lists)

```python
# ❌ OLD: No type narrowing
if self.performers is UNSET:
    self.performers = []
if performer not in self.performers:  # ERROR: type checker doesn't know it's a list
    self.performers.append(performer)

# ✅ NEW: Type narrowing works
if isinstance(self.performers, UnsetType):
    self.performers = []
if performer not in self.performers:  # OK: type checker knows it's list[Performer]
    self.performers.append(performer)
```

### Positive Checks (Guard Access)

```python
# ❌ OLD: No type narrowing
if self.tags is not UNSET and tag in self.tags:  # Type checker unsure
    self.tags.remove(tag)

# ✅ NEW: Type narrowing works
if is_set(self.tags) and tag in self.tags:  # OK: type checker knows it's list[Tag]
    self.tags.remove(tag)
```

### Chained Checks

```python
# ❌ OLD: No type narrowing
if sg.group is not UNSET and sg.group.id is not UNSET:
    # Access sg.group.id - type checker unsure

# ✅ NEW: Type narrowing works
if is_set(sg.group) and is_set(sg.group.id):
    # Access sg.group.id - type checker knows it's str
```

### Compound Conditions

```python
# ❌ OLD: Mixed checks
if field is UNSET and scraped.field is not None and scraped.field is not UNSET:
    # Complex logic

# ✅ NEW: Consistent pattern
if isinstance(field, UnsetType) and scraped.field is not None and is_set(scraped.field):
    # Type-safe logic
```

## Testing Strategy

### Unit Tests

All existing tests should continue passing without modification:

- ✅ `tests/types/test_unset.py` - UNSET behavior tests
- ✅ `tests/types/test_*_helpers.py` - Helper method tests (100% coverage)

### Integration Tests

Add if not already present:

- Scrape parser integration tests
- Type narrowing validation tests

### Type Checking

Run mypy/pylance to verify improvements:

```bash
poetry run mypy stash_graphql_client/types/
```

Expected improvement: Reduction in type errors related to UNSET checks.

## Migration Notes for External Users

If this library has external users, provide migration guide:

### Breaking Changes: None

The refactoring is internal only - public API unchanged.

### Recommended Updates

If external code uses UNSET checks:

```python
# Consider updating from:
if scene.tags is not UNSET:
    process_tags(scene.tags)

# To:
from stash_graphql_client.types import is_set

if is_set(scene.tags):
    process_tags(scene.tags)  # Better type inference in your IDE!
```

## Success Criteria

- ✅ All 160 UNSET checks refactored
- ✅ 100% test coverage maintained
- ✅ All tests passing
- ✅ Mypy/pylance type errors reduced
- ✅ No behavioral changes to public API
- ✅ Documentation updated with best practices

## Current Status (as of feat/gap-coverage branch)

- ✅ `is_set()` TypeGuard implemented and tested
- ✅ `isinstance(x, UnsetType)` proven to work for type narrowing
- ✅ 100% test coverage (1700 tests passing)
- ✅ All quality checks passing (ruff, mypy, bandit)
- ⏸️ Refactoring deferred to v0.6.0

## References

- `stash_graphql_client/types/unset.py` - UNSET implementation and `is_set()` TypeGuard
- `tests/types/test_unset.py` - UNSET behavior tests
- Python TypeGuard documentation: https://docs.python.org/3/library/typing.html#typing.TypeGuard
- PEP 647: User-Defined Type Guards: https://peps.python.org/pep-0647/

---

**Last Updated**: 2025-12-26
**Next Review**: v0.6.0 planning phase
