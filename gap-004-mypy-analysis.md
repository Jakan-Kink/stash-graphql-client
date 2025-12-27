# GAP-004: Mypy Type Checking Analysis

**Current Status**: 170 mypy errors in 23 files
**Date**: 2025-12-26
**Branch**: feat/gap-coverage

## Executive Summary

Of the **170 total mypy errors**, approximately **110 errors (~65%)** are directly caused by UNSET type narrowing issues that would be **automatically fixed** by the v0.6.0 type narrowing refactoring documented in `todo-0.6.0.md`.

The remaining **~60 errors (~35%)** are unrelated to UNSET and require separate investigation.

## Error Breakdown by Category

| Error Type           | Count   | UNSET-Related | Would Fix in v0.6.0 | Notes                                                   |
| -------------------- | ------- | ------------- | ------------------- | ------------------------------------------------------- |
| **union-attr**       | 54      | 54 (100%)     | ✅ Yes              | `Item "UnsetType" has no attribute "append"` etc.       |
| **operator**         | 33      | 29 (88%)      | ✅ Yes              | `Unsupported right operand type for in`                 |
| **assignment**       | 21      | 16 (76%)      | ✅ Yes              | Type assignment after conditional checks                |
| **index**            | 12      | 11 (92%)      | ✅ Yes              | `Value of type "list[X] \| UnsetType" is not indexable` |
| **return-value**     | 23      | 0 (0%)        | ❌ No               | Unrelated to UNSET                                      |
| **attr-defined**     | 7       | 0 (0%)        | ❌ No               | Unrelated to UNSET                                      |
| **call-arg**         | 6       | 0 (0%)        | ❌ No               | Unrelated to UNSET                                      |
| **var-annotated**    | 4       | 0 (0%)        | ❌ No               | Missing type annotations                                |
| **misc**             | 4       | 0 (0%)        | ❌ No               | Miscellaneous issues                                    |
| **arg-type**         | 3       | 0 (0%)        | ❌ No               | Argument type mismatches                                |
| **override**         | 2       | 0 (0%)        | ❌ No               | Method override issues                                  |
| **import-not-found** | 1       | 0 (0%)        | ❌ No               | Missing import                                          |
| **Total**            | **170** | **110 (65%)** |                     |                                                         |

## UNSET-Related Errors by File (110 total)

### Helper Methods (69 errors - High Priority)

These are in user-facing helper methods and would be fixed by Phase 1 of v0.6.0 refactoring:

| File                 | Errors | Error Types                                                  |
| -------------------- | ------ | ------------------------------------------------------------ |
| `types/tag.py`       | 28     | union-attr (24), operator (4) - Tag parent/child helpers     |
| `types/scene.py`     | 12     | union-attr (8), operator (4) - Gallery/performer/tag helpers |
| `types/image.py`     | 8      | union-attr (6), operator (2) - Performer/gallery helpers     |
| `types/group.py`     | 8      | union-attr (8) - Sub-group hierarchy helpers                 |
| `types/gallery.py`   | 6      | union-attr (4), operator (2) - Performer/scene helpers       |
| `types/performer.py` | 4      | union-attr (2), operator (2) - Tag helpers                   |
| `types/studio.py`    | 4      | union-attr (2), operator (2) - Child studio helpers          |

**Subtotal: 69 errors** - All would be fixed by updating 16 helper methods with `isinstance()`/`is_set()`

### Client Code (13 errors - Medium Priority)

| File                         | Errors | Error Types               |
| ---------------------------- | ------ | ------------------------- |
| `client/mixins/performer.py` | 11     | index (8), union-attr (3) |
| `client/mixins/studio.py`    | 2      | index (2)                 |

**Subtotal: 13 errors** - Would be fixed by adding type guards in client code

### Utility Code (28 errors - High Risk)

| File                     | Errors | Error Types                                                            |
| ------------------------ | ------ | ---------------------------------------------------------------------- |
| `utils/scrape_parser.py` | 28     | assignment (16), union-attr (7), index (1), arg-type (3), operator (1) |

**Subtotal: 28 errors** - Complex compound conditions, requires careful refactoring

### Total UNSET-Related: 110 errors

## Non-UNSET Errors by Category (60 total)

These errors are **NOT** related to UNSET type narrowing and require separate investigation:

### 1. Return Value Errors (23 errors)

Files affected:

- `types/base.py` (likely generic type issues)
- Various type files

**Root Cause**: Return type mismatches, likely related to generic type handling.

### 2. Attribute Errors (7 errors)

Files affected:

- `types/base.py` (3) - `"type[FromGraphQLMixin]" has no attribute "model_fields"`
- `types/files.py` (2) - `"ModelMetaclass" has no attribute "model_validate"`
- `types/image.py` (2) - Similar ModelMetaclass issues

**Root Cause**: Pydantic metaclass attribute access issues, possibly version-related.

### 3. Call Argument Errors (6 errors)

**Root Cause**: Function/method signature mismatches.

### 4. Variable Annotation Errors (4 errors)

Files affected:

- `types/base.py` (3)
- `store.py` (1)

**Root Cause**: Missing type hints on variable declarations.

Example:

```python
# Line 247 in base.py
processed = {}  # Error: Need type annotation
# Should be:
processed: dict[str, Any] = {}
```

### 5. Misc/Override/Import Errors (10 errors)

Various issues including:

- Method override signature mismatches
- Missing imports
- Generic type issues

## Impact Analysis

### v0.6.0 Refactoring Impact

If we complete the v0.6.0 type narrowing refactoring:

**Before**: 170 errors
**After v0.6.0**: ~60 errors (65% reduction)

### Remaining Work After v0.6.0

The 60 remaining errors would need separate fixes:

1. **Variable annotations** (4 errors) - Easy, low risk

   - Add explicit type hints to dict/list initializations

2. **Pydantic metaclass** (7 errors) - Medium complexity

   - May require Pydantic version upgrade or alternative approaches
   - Investigate `model_fields` access patterns

3. **Return value types** (23 errors) - Medium to high complexity

   - Review generic type handling in base.py
   - May require refactoring type signatures

4. **Call arguments** (6 errors) - Low to medium complexity

   - Fix function signature mismatches

5. **Other** (20 errors) - Varies

   - Case-by-case investigation needed

## Detailed Examples

### Example 1: Helper Method Errors (FIXED by v0.6.0)

**Current Code** (scene.py:315-316):

```python
if self.galleries is not UNSET:
    if gallery not in self.galleries:  # ERROR: Unsupported right operand
        self.galleries.append(gallery)  # ERROR: Item "UnsetType" has no attribute "append"
```

**Mypy Errors**:

```
scene.py:315: error: Unsupported right operand type for in ("list[Gallery] | UnsetType")  [operator]
scene.py:316: error: Item "UnsetType" of "list[Gallery] | UnsetType" has no attribute "append"  [union-attr]
```

**After v0.6.0 Refactoring**:

```python
if is_set(self.galleries):
    if gallery not in self.galleries:  # OK: mypy knows it's list[Gallery]
        self.galleries.append(gallery)  # OK: mypy knows it's list[Gallery]
```

**Mypy Errors**: 0 ✅

### Example 2: Scrape Parser Errors (FIXED by v0.6.0)

**Current Code** (scrape_parser.py:212-218):

```python
if (
    performer_ids is UNSET
    and scraped.performers is not None
    and scraped.performers is not UNSET
):
    # ERROR: Item "UnsetType" has no attribute "__iter__"
    for scraped_performer in scraped.performers:
        performer_ids.append(...)  # ERROR: Incompatible types in assignment
```

**Mypy Errors**:

```
scrape_parser.py:212: error: Item "UnsetType" of "list[ScrapedPerformer] | UnsetType" has no attribute "__iter__"  [union-attr]
scrape_parser.py:218: error: Incompatible types in assignment (expression has type "list[str | Any | UnsetType]", variable has type "UnsetType")  [assignment]
```

**After v0.6.0 Refactoring**:

```python
if (
    isinstance(performer_ids, UnsetType)
    and scraped.performers is not None
    and is_set(scraped.performers)
):
    for scraped_performer in scraped.performers:  # OK: mypy knows it's list
        performer_ids.append(...)  # OK: mypy flow analysis works
```

**Mypy Errors**: Reduced significantly ✅

### Example 3: Variable Annotation Error (NOT fixed by v0.6.0)

**Current Code** (base.py:247):

```python
processed = {}  # ERROR: Need type annotation
```

**Mypy Error**:

```
base.py:247: error: Need type annotation for "processed" (hint: "processed: dict[<type>, <type>] = ...")  [var-annotated]
```

**Fix** (separate from v0.6.0):

```python
processed: dict[str, Any] = {}
```

This requires manual annotation, unrelated to UNSET refactoring.

### Example 4: Pydantic Metaclass Error (NOT fixed by v0.6.0)

**Current Code** (base.py:255):

```python
for field_name, field_info in cls.model_fields.items():
```

**Mypy Error**:

```
base.py:255: error: "type[FromGraphQLMixin]" has no attribute "model_fields"  [attr-defined]
```

**Root Cause**: Type checker doesn't recognize Pydantic's metaclass-provided attributes.

**Potential Fixes**:

1. Add explicit type annotations for Pydantic models
2. Use type: ignore comments (not ideal)
3. Upgrade Pydantic version with better type stubs
4. Use alternative attribute access pattern

## Recommended Approach

### Phase 1: v0.6.0 Type Narrowing Refactoring

**Target**: Fix 110 UNSET-related errors (65% of total)
**Effort**: Medium (documented in todo-0.6.0.md)
**Risk**: Low to medium (well-tested patterns)

**Sub-phases**:

1. Helper methods (69 errors) - Low risk, high value
2. Client code (13 errors) - Medium risk
3. Scrape parser (28 errors) - High risk, requires careful testing

**Expected Outcome**: 170 → 60 errors

### Phase 2: Variable Annotations

**Target**: Fix 4 var-annotated errors
**Effort**: Low
**Risk**: Very low

**Approach**: Add explicit type annotations to variable declarations.

**Expected Outcome**: 60 → 56 errors

### Phase 3: Pydantic Metaclass Issues

**Target**: Fix 7 attr-defined errors
**Effort**: Medium
**Risk**: Medium

**Approach**:

1. Research Pydantic type stubs
2. Consider version upgrade
3. Add type: ignore if necessary

**Expected Outcome**: 56 → 49 errors

### Phase 4: Return Value & Other Errors

**Target**: Fix remaining 49 errors
**Effort**: High
**Risk**: Medium to high

**Approach**: Case-by-case investigation and fixes.

**Expected Outcome**: 49 → 0 errors (hopefully!)

## Success Criteria

### v0.6.0 Goals

- ✅ Reduce mypy errors from 170 to ~60 (65% reduction)
- ✅ Eliminate all UNSET type narrowing errors in helper methods
- ✅ Improve type safety in client code
- ✅ Better IDE autocomplete and type hints

### Long-term Goals (GAP-004 Complete)

- ✅ Zero mypy errors (`poetry run mypy stash_graphql_client`)
- ✅ Strict type checking enabled
- ✅ All Pydantic patterns properly typed
- ✅ Comprehensive type annotations throughout

## Commands for Tracking Progress

```bash
# Total error count
poetry run mypy stash_graphql_client 2>&1 | tail -1

# UNSET-related errors
poetry run mypy stash_graphql_client 2>&1 | grep "UnsetType" | wc -l

# Errors by category
poetry run mypy stash_graphql_client 2>&1 | grep "error:" | sed 's/.*\[\([^]]*\)\].*/\1/' | sort | uniq -c | sort -rn

# Errors by file
poetry run mypy stash_graphql_client 2>&1 | grep "error:" | cut -d: -f1 | sort | uniq -c | sort -rn
```

## References

- `todo-0.6.0.md` - UNSET type narrowing refactoring plan
- Python TypeGuard: https://docs.python.org/3/library/typing.html#typing.TypeGuard
- Mypy documentation: https://mypy.readthedocs.io/
- Pydantic type checking: https://docs.pydantic.dev/latest/concepts/type_checking/

---

**Last Updated**: 2025-12-26
**Next Steps**: Complete v0.6.0 type narrowing refactoring (see todo-0.6.0.md)
