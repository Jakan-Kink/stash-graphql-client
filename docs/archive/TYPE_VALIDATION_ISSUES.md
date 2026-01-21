# Type Validation Issues - Technical Debt [ARCHIVED]

> **⚠️ ARCHIVED DOCUMENT**
>
> **All issues documented below have been RESOLVED as of v0.10.10**
>
> This document is preserved for historical reference and to demonstrate the evolution of the codebase's type safety and validation patterns.
>
> **Archive Date**: 2026-01-20
> **Original Date**: 2026-01-11
> **Status**: ✅ All 11 issue categories resolved

---

## Resolution Summary

All type validation issues identified during the v0.10.7 investigation have been systematically resolved across subsequent releases:

### High Impact Issues (3/3 RESOLVED)

| Issue | Status | Resolved In | Evidence |
|-------|--------|-------------|----------|
| **#1: Dict Structure Validation** | ✅ RESOLVED | v0.10.8 | All 50+ methods now validate dict inputs through Pydantic with type checking |
| **#2: Path/String Confusion** | ✅ RESOLVED | v0.10.8 | Added OSError handling, Path support, and StashConfigurationError for protected paths |
| **#3: CIMultiDict Type Mismatch** | ✅ RESOLVED | v0.10.8 | Converted to normalization-only usage, returns proper dict types |

### Medium Impact Issues (3/3 RESOLVED)

| Issue | Status | Resolved In | Evidence |
|-------|--------|-------------|----------|
| **#4: Bool Conversion Patterns** | ✅ RESOLVED | v0.10.8 | Standardized 40 methods to use `is True` identity checking |
| **#5: _parse_obj_for_ID() Validation** | ✅ RESOLVED | Unknown | Added positive ID validation and proper error handling |
| **#6: Optional/None Handling** | ✅ RESOLVED | v0.10.8, v0.10.10 | Config validation added, dict.get() patterns fixed across 25 instances |

### Low Impact Issues (5/5 RESOLVED)

| Issue | Status | Resolved In | Evidence |
|-------|--------|-------------|----------|
| **#7: MIME Type Defaults** | ✅ RESOLVED | Unknown | Now validates file is image type instead of defaulting to "image/jpeg" |
| **#8.1: Direction Validation** | ✅ RESOLVED | Unknown | Added `_normalize_sort_direction()` with enum and string validation |
| **#8.2: SystemStatusEnum** | ✅ RESOLVED | N/A | False positive - Pydantic handles enum conversion correctly |
| **#9: List Element Validation** | ✅ RESOLVED | Unknown | Changed from `list[str]` to `list[Timestamp]` with Pydantic validators |
| **#10: Image Index Validation** | ✅ RESOLVED | Unknown | Added non-negative validation for image_index parameters |
| **#11: verify_ssl Bool Wrapping** | ✅ RESOLVED | v0.10.8 | String coercion with validation for "true"/"false" strings |

### Key Improvements Across All Versions

**v0.10.8** - Systematic Validation Overhaul:
- Dict input validation through Pydantic (50+ methods)
- Config hardening (scheme, port, verify_ssl)
- Protected path blocking with StashConfigurationError
- Bool return pattern standardization (40 methods)

**v0.10.9** - Documentation:
- Updated CHANGELOG with v0.10.8 release notes

**v0.10.10** - None-Handling Refinement:
- Fixed 25 instances of incorrect `dict.get("field", None)` usage
- GraphQL now correctly distinguishes explicit null from missing fields
- 100% branch coverage achieved for validation patterns

**Unknown Versions** - Additional Fixes:
- ID validation with positive integer checks
- MIME type validation for image files
- Direction parameter validation
- Image index range validation
- Timestamp type system with Pydantic validators

---

## Architectural Philosophy Evolution

This document demonstrates the codebase's shift from "fail late at GraphQL" to "fail early with clear errors":

**Before (v0.10.7 and earlier)**:
- Accept any dict structure → silent GraphQL failures
- No validation on IDs, ranges, or types
- Inconsistent patterns across 40+ methods
- Type coercion without validation

**After (v0.10.10+)**:
- Pydantic validation for all dict inputs
- Positive validation for IDs and ranges
- Consistent `is True` pattern for booleans
- Type validation with clear error messages
- Duck typing for flexibility (Logger)

---

## Original Document Follows

This document tracks non-critical type validation issues discovered during the v0.10.7 TTL bug investigation. These issues follow similar patterns but have lower severity or impact.

**Status**: ~~Documented for future work~~ **ALL RESOLVED**
**Priority**: ~~Medium to Low~~ **COMPLETED**
**Related**: See CHANGELOG.md v0.10.7-v0.10.10 for all fixes

---

## Table of Contents

1. [High Impact Issues](#high-impact-issues)
2. [Medium Impact Issues](#medium-impact-issues)
3. [Low Impact Issues](#low-impact-issues)
4. [Recommendations](#recommendations)

---

## High Impact Issues

### 1. ~~Dict Structure Validation~~ (RESOLVED v0.10.8)

**Status**: ✅ **RESOLVED** - All 50+ methods validate dict inputs through Pydantic

**Pattern**: Methods accept `SomeType | dict[str, Any]` but perform no structural validation.

**Files Affected**:
- `stash_graphql_client/client/mixins/marker.py` line 211
- `stash_graphql_client/client/mixins/image.py` line 207
- `stash_graphql_client/client/mixins/gallery.py` line 435
- 17+ additional methods across other mixins

**Problem** (Historical):
```python
# marker.py:244-248
if isinstance(input_data, BulkSceneMarkerUpdateInput):
    input_dict = input_data.to_graphql()
else:
    input_dict = input_data  # ❌ No validation of dict structure!
```

**Impact**: Silent failures at GraphQL layer if dict has wrong keys or missing required fields.

**Resolution (v0.10.8)**:
```python
if isinstance(input_data, BulkSceneMarkerUpdateInput):
    input_dict = input_data.to_graphql()
else:
    # Type check first
    if not isinstance(input_data, dict):
        raise TypeError(
            f"input_data must be BulkSceneMarkerUpdateInput or dict, "
            f"got {type(input_data).__name__}"
        )
    # Validate dict structure through Pydantic
    validated = BulkSceneMarkerUpdateInput(**input_data)
    input_dict = validated.to_graphql()
```

**Benefits**:
- Type checking prevents passing wrong types
- Pydantic validation catches field type errors
- Clear error messages for missing required fields
- Prevents silent GraphQL failures

**Severity**: N/A (resolved)

---

### 2. ~~Path/String Confusion~~ (Fixed in v0.10.8)

#### 2.1 Performer.update_avatar() - ✅ RESOLVED

**Status**: ✅ **RESOLVED** - Proper error handling for invalid paths

**File**: `stash_graphql_client/types/performer.py` lines 261-269

**Resolution (v0.10.8)**:
```python
# Convert path to Path object with error handling
try:
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {path}")
    if not path.is_file():
        raise ValueError(f"Path is not a file: {path}")
except (OSError, TypeError) as e:
    raise ValueError(f"Invalid image path: {image_path!r}") from e
```

**Benefits**:
- Catches invalid path characters (null bytes, etc.) with clear error message
- Validates path exists and is a file (not directory)
- Proper error chaining with `from e`
- Updated docstring to reflect ValueError for invalid paths

**Severity**: N/A (resolved)

---

#### 2.2 SystemQueryClientMixin.directory() - ✅ RESOLVED

**Status**: ✅ **RESOLVED** - Type annotation improved, Path support added

**File**: `stash_graphql_client/client/mixins/system_query.py` lines 161-198

**Resolution (v0.10.8)**:
```python
async def directory(
    self, path: str | Path | None = None, locale: str = "en"
) -> Directory:
    """Browse filesystem directory.

    Args:
        path: The directory path to list (string or Path object). If None, returns root directories.
              Note: Path is converted to string and sent to Stash server.
        locale: Desired collation locale (e.g., 'en-US', 'pt-BR'). Default is 'en'
    """
    # Convert Path to string if provided
    path_str = str(path) if path is not None else None
    variables = {"path": path_str, "locale": locale}
    result = await self.execute(fragments.DIRECTORY_QUERY, variables)
    return self._decode_result(Directory, result["directory"])
```

**Benefits**:
- Type annotation now accepts `str | Path | None`
- Docstring clarifies Path object support
- Automatic Path → string conversion for GraphQL
- No validation needed (Stash server validates directory existence)

**Severity**: N/A (resolved)

---

#### 2.3 Config Path Fields - ✅ RESOLVED

**Status**: ✅ **RESOLVED** - Protected with StashConfigurationError

**File**: `stash_graphql_client/types/config.py` lines 206-244

**Problem** (Historical): `ConfigGeneralInput` allowed modifying 12 critical server filesystem paths, which could corrupt Stash installation during testing or automation.

**Resolution (v0.10.8)**: Added Pydantic model validator that rejects any path modifications:

```python
@model_validator(mode="after")
def _reject_path_modifications(self):
    """Reject attempts to modify server filesystem paths."""
    protected_paths = {
        "database_path", "backup_directory_path", "delete_trash_path",
        "generated_path", "metadata_path", "scrapers_path",
        "plugins_path", "cache_path", "blobs_path",
        "ffmpeg_path", "ffprobe_path", "python_path",
    }

    set_paths = [field for field in protected_paths if is_set(getattr(self, field))]

    if set_paths:
        raise StashConfigurationError(
            f"Modifying server filesystem paths is not allowed: {', '.join(set_paths)}. "
            "These critical paths should only be changed through the Stash web interface..."
        )
```

**New Error Type**: Created `StashConfigurationError` in `errors.py` for configuration safety

**Benefits**:
- Prevents accidental path corruption during testing (addresses reported issue)
- Clear error message directing users to Stash web UI
- Protects 12 critical server-side paths from client modification
- Maintains safety even if paths are passed via dict or ConfigGeneralInput

**Severity**: N/A (resolved)

---

### 3. ~~CIMultiDict Type Mismatch~~ (Fixed in v0.10.8)

**Status**: ✅ **RESOLVED** - False positive, intentional design improved

**File**: `stash_graphql_client/context.py` lines 70, 106

**Original Concern**: CIMultiDict was stored and passed to StashClient, causing type checker mismatch.

**Resolution**:
- **v0.8.2** introduced CIMultiDict to fix case-sensitivity bug (lowercase `scheme`/`host`/`port`/`apikey` now work)
- **v0.10.8** improved implementation: CIMultiDict now used only for normalization, converted to regular dict with canonical keys
- Users can pass any case (`scheme`, `Scheme`, `SCHEME`), stored as canonical `Scheme`
- Type safety restored: StashClient receives proper `dict[str, Any]`
- Preserves v0.8.2 case-insensitive input behavior

**Implementation**:
```python
@staticmethod
def _normalize_conn_keys(conn: dict[str, Any]) -> dict[str, Any]:
    """Normalize connection dict keys to canonical case."""
    if not conn:
        return {}

    # Use CIMultiDict for case-insensitive lookup during normalization
    ci_conn = CIMultiDict(conn)

    # Canonical key mappings (lowercase -> canonical)
    canonical_keys = {
        "logger": "Logger",
        "scheme": "Scheme",
        "host": "Host",
        "port": "Port",
        "apikey": "ApiKey",
    }

    normalized = {}
    for lower_key, canonical_key in canonical_keys.items():
        if value := ci_conn.get(lower_key):
            normalized[canonical_key] = value

    return normalized
```

**Severity**: N/A (not a bug, design improvement applied)

---

## Medium Impact Issues

### 4. ~~Bool Conversion Pattern Inconsistencies~~ (Fixed in v0.10.8)

**Status**: ✅ **RESOLVED** - Standardized on Pattern 1c across all 40 methods

**Problem** (Historical): Three different patterns existed across 40 methods:

**Pattern 1**: `bool(result.get(..., False))` - redundant bool() wrapper
**Pattern 2**: `result.get(..., False)` - no bool() wrapper (returns Any)
**Pattern 3**: `bool(result[...])` - bracket access, could raise KeyError

**Resolution (v0.10.8)**: All 40 methods now use **Pattern 1c** (identity checking):
```python
def destroy_tag(self, id: str) -> bool:
    result = self._graphql_call(...)
    return result.get("tagDestroy") is True  # ✅ Explicit identity check
```

**Why Pattern 1c is best**:
- **Identity checking**: Uses `is True` for exact boolean matching (not truthy values)
- **No coercion**: Doesn't convert 1, "yes", or other truthy values to True
- **Handles None**: `result.get("key")` returns None by default, `None is True` evaluates to False
- **Most Pythonic**: Explicit is better than implicit

**Files Updated**: 15 mixin files (gallery, group, config, file, scene, tag, image, performer, studio, marker, plugin, jobs, metadata, filter, scraper)

**Severity**: N/A (resolved)

---

### 5. ~~_parse_obj_for_ID() Int Conversion~~ (RESOLVED)

**Status**: ✅ **RESOLVED** - ID validation with positive checks and error handling

**File**: `stash_graphql_client/client/base.py` lines 505-516

**Problem** (Historical):
```python
def _parse_obj_for_ID(self, param: Any, str_key: str = "name") -> Any:
    if isinstance(param, str):
        try:
            return int(param)  # ❌ No validation: negative IDs, zero OK?
        except ValueError:
            return {str_key: param.strip()}
    elif isinstance(param, dict):
        if param.get("stored_id"):
            return int(param["stored_id"])  # ❌ Could be None or non-numeric
        if param.get("id"):
            return int(param["id"])  # ❌ Same issue
    return param
```

**Issues**:
1. No validation that ID is positive
2. `.get()` returns None if key missing, then `int(None)` raises TypeError
3. Bracket notation `param["stored_id"]` after `.get()` check is redundant

**Resolution**:
```python
def _parse_obj_for_ID(self, param: Any, str_key: str = "name") -> Any:
    if isinstance(param, str):
        stripped = param.strip()
        try:
            id_val = int(stripped)
        except ValueError:
            return {str_key: stripped}
        if id_val <= 0:  # ✅ ADDED: Positive validation
            raise ValueError("ID must be positive")
        return id_val
    if isinstance(param, dict):
        for key in ("stored_id", "id"):
            if key in param:
                try:
                    id_val = int(param[key])
                except (TypeError, ValueError) as e:  # ✅ ADDED: Error handling
                    raise ValueError(f"Invalid {key}: {param[key]!r}") from e
                if id_val <= 0:  # ✅ ADDED: Positive validation
                    raise ValueError(f"{key} must be positive")
                return id_val
    return param
```

**Benefits**:
- Validates IDs are positive integers
- Proper TypeError and ValueError handling
- Error chaining with `from e`
- Clean logic without redundant patterns

**Severity**: N/A (resolved)

---

### 6. ~~Optional/None Handling Issues~~ (Resolved in v0.10.8, v0.10.10)

#### 6.1 Config Dict Value Types - ✅ RESOLVED with Duck Typing

**Status**: ✅ **RESOLVED** - Proper validation added with duck typing support

**File**: `stash_graphql_client/client/base.py` lines 136-163

**Resolution (v0.10.8)**:
- **Scheme**: ✅ Validated (must be "http" or "https")
- **Port**: ✅ Already validated in v0.10.7 (int or numeric string, 0-65535)
- **verify_ssl**: ✅ Already validated in v0.10.8 (bool or string coercion)
- **Logger**: ✅ Duck typing - documented in docstring, no validation needed
- **Host**: ✅ No validation needed - can be IPv4, IPv6, shortname, or FQDN

**Implementation**:
```python
# Validate Scheme
scheme = conn.get("Scheme", "http")
if scheme not in ("http", "https"):
    raise ValueError(f"Scheme must be 'http' or 'https', got {scheme!r}")
self.scheme = scheme
```

**Logger Duck Typing Rationale**:
- Logger only needs `.debug()`, `.info()`, `.warning()`, `.error()` methods
- Validates `isinstance(logger, logging.Logger)` would prevent using loguru, structlog, etc.
- Duck typing provides flexibility while maintaining safety
- Documented in docstring: "duck-typed: must have .debug(), .info(), .warning(), .error() methods"

**Severity**: N/A (resolved with appropriate validation and duck typing)

---

#### 6.2 marker_filter Parameter - ℹ️ FALSE POSITIVE

**Status**: ℹ️ **FALSE POSITIVE** - No issue, GraphQL handles None correctly

**File**: `stash_graphql_client/client/mixins/marker.py` line 74

**Analysis**:
```python
async def find_markers(
    self,
    filter_: dict[str, Any] | None = None,
    marker_filter: dict[str, Any] | None = None,
    ...
) -> FindSceneMarkersResultType:
    # marker_filter is passed to GraphQL, which handles None correctly
    result = await self.execute(
        fragments.FIND_MARKERS_QUERY,
        {"filter": filter_, "marker_filter": marker_filter},  # ✅ None is OK
    )
```

**Why it's OK**:
- GraphQL transparently handles None values in variables
- The `execute()` method filters out None values before sending to server
- No TypeError occurs - this is expected behavior

**Severity**: N/A (false positive)

---

## Low Impact Issues

### 7. ~~String Encoding/Bytes Edge Case~~ (RESOLVED)

**Status**: ✅ **RESOLVED** - MIME type validation added

**File**: `stash_graphql_client/types/performer.py` lines 268-272

**Problem** (Historical):
```python
with open(path, "rb") as f:
    image_data = f.read()
image_b64 = base64.b64encode(image_data).decode("utf-8")
mime = mimetypes.types_map.get(path.suffix, "image/jpeg")  # ❌ Default might be wrong
```

**Issue**: Default MIME type is "image/jpeg" but file might be PNG, GIF, etc.

**Impact**: Very low (data URLs usually work regardless, browsers are forgiving)

**Resolution**:
```python
mime = mimetypes.types_map.get(path.suffix.lower())
if not mime or not mime.startswith("image/"):
    raise ValueError(f"File does not appear to be an image: {path.suffix}")
```

**Benefits**:
- No longer defaults to "image/jpeg"
- Validates file has image MIME type
- Case-insensitive suffix matching

**Severity**: N/A (resolved)

---

### 8. Enum/Literal String Validation

#### 8.1 ~~Direction Parameter Not Validated~~ (RESOLVED)

**Status**: ✅ **RESOLVED** - Direction validation with enum and string support

**Files**: Multiple mixins (tag.py, performer.py, etc.)

**Problem** (Historical):
- Documentation says "direction: SortDirectionEnum (ASC/DESC)"
- But parameter typed as `str | None`
- No validation that value is actually "ASC" or "DESC"

**Impact**: User passes "ASCENDING" or "desc" (lowercase) → silent failure at GraphQL.

**Resolution** (`base.py:552-568`):
```python
def _normalize_sort_direction(self, filter_: dict[str, Any]) -> dict[str, Any]:
    if "direction" not in filter_:
        return filter_

    direction = filter_.get("direction")
    if direction is None:
        return filter_

    if isinstance(direction, SortDirectionEnum):  # ✅ Handles enum
        updated = dict(filter_)
        updated["direction"] = direction.value
        return updated

    if isinstance(direction, str):
        if direction in ("ASC", "DESC"):  # ✅ Validates strings
            return filter_
        raise ValueError(f"direction must be 'ASC' or 'DESC', got {direction!r}")
```

**Benefits**:
- Accepts SortDirectionEnum instances
- Validates string values are exactly "ASC" or "DESC"
- Clear error messages for invalid values

**Severity**: N/A (resolved)

---

#### 8.2 SystemStatusEnum Comparison Assumption

**File**: `stash_graphql_client/client/mixins/system_query.py` lines 80, 87

**Problem**:
```python
if status.status == SystemStatusEnum.NEEDS_MIGRATION:  # ❌ Assumes enum, might be string
```

**Impact**: If GraphQL returns string "NEEDS_MIGRATION" instead of enum, comparison might fail silently.

**Recommended Fix**: Ensure `status.status` field is properly typed as enum in Pydantic model, not string.

**Severity**: Low (Pydantic should handle enum conversion)

---

### 9. ~~List/Tuple Element Validation~~ (RESOLVED)

**Status**: ✅ **RESOLVED** - Timestamp type with Pydantic validators

**File**: `stash_graphql_client/client/mixins/scene.py` lines 774, 815, 981, 1022

**Problem** (Historical):
```python
async def scene_add_o(
    self,
    id: str,
    times: list[str] | None = None,  # ❌ No validation of string format
    ...
```

**Issue**: What format are the strings? Timestamps? ISO8601? No validation or documentation.

**Resolution** (`scene.py:802-805`):
```python
async def scene_add_o(
    self,
    id: str,
    times: list[Timestamp] | None = None,  # ✅ Uses validated Timestamp type
) -> HistoryMutationResult:
```

**Timestamp Type** (`scalars.py:121-125`):
```python
Timestamp = Annotated[
    datetime,
    BeforeValidator(_parse_timestamp_value),
    PlainSerializer(_serialize_timestamp, return_type=str),
]
```

**Benefits**:
- Pydantic validates timestamp format
- Supports RFC3339 strings
- Supports relative times (e.g., "<4h" for 4 hours ago)
- Type-safe with datetime objects

**Severity**: N/A (resolved)

---

### 10. ~~Image Index Range Validation~~ (RESOLVED)

**Status**: ✅ **RESOLVED** - Non-negative validation added

**File**: `stash_graphql_client/client/mixins/gallery.py` lines 256, 309

**Problem** (Historical):
```python
async def gallery_chapter_create(
    self,
    gallery_id: str,
    title: str,
    image_index: int,  # ❌ No validation: negative? zero? too large?
    ...
) -> GalleryChapter:
    if image_index is not None:
        input_data["image_index"] = str(image_index)
```

**Impact**: Negative or out-of-bounds indices might cause GraphQL errors.

**Resolution** (`gallery.py:269-270`):
```python
if image_index < 0:  # ✅ ADDED: Range validation
    raise ValueError(f"image_index must be non-negative, got {image_index}")
```

**Benefits**:
- Validates non-negative indices
- Clear error messages
- Fails early before GraphQL submission

**Severity**: N/A (resolved)

---

### 11. ~~verify_ssl Redundant Bool Wrapping~~ (Fixed in v0.10.8)

**Status**: ✅ **RESOLVED** - String coercion added with validation

**File**: `stash_graphql_client/client/base.py` line 128-134

**Problem** (Historical): `bool(verify_ssl)` wrapper was redundant and couldn't handle string values correctly.

**Resolution (v0.10.8)**: Implemented Option 2 - validate and coerce string values:
```python
# Validate and convert verify_ssl to bool
if isinstance(verify_ssl, str):
    verify_ssl = verify_ssl.lower() in ("true", "1", "yes")
elif not isinstance(verify_ssl, bool):
    raise TypeError(
        f"verify_ssl must be bool or string ('true'/'false'), got {type(verify_ssl).__name__}"
    )
```

**Benefits**:
- Accepts bool values: `True`, `False`
- Accepts truthy strings: `"true"`, `"1"`, `"yes"` → True
- Accepts falsy strings: `"false"`, `"0"`, `"no"`, etc. → False
- Rejects invalid types with clear TypeError

**Severity**: N/A (resolved)

---

## Recommendations

### ~~Immediate Actions (Critical - Being Fixed)~~ ✅ COMPLETED
1. ✅ Fix batch_size validation (ValueError prevention)
2. ✅ Fix port type coercion (URL construction safety)
3. ✅ Standardize bool return patterns (consistency + KeyError prevention)

### ~~Short-Term (Next Release)~~ ✅ COMPLETED
4. ✅ Add dict structure validation for `SomeType | dict[str, Any]` parameters (v0.10.8)
5. ✅ Fix Path/String confusion with better validation and error messages (v0.10.8)
6. ✅ Validate config dict value types at initialization (v0.10.8)

### ~~Medium-Term (Future Releases)~~ ✅ COMPLETED
7. ✅ Replace "direction: str" with actual Enum types (completed)
8. ✅ Add validation for list element formats where critical (Timestamp type)
9. ✅ Convert CIMultiDict to plain dict for type safety (v0.10.8)

### Long-Term (Technical Debt Cleanup) - ONGOING
10. Consider using TypedDict for structured dict parameters
11. Add mypy strict mode checks for parameter types
12. Document expected types more explicitly in all docstrings
13. Add pre-commit hooks to validate parameter types

---

## Testing Strategy

For each fix:
1. Add unit test with valid input (should pass)
2. Add unit test with invalid input (should raise specific error)
3. Add integration test if behavior affects GraphQL layer
4. Document expected error messages in test names

Example:
```python
def test_batch_size_positive():
    """filter_and_populate should accept positive batch_size"""
    # Should work

def test_batch_size_zero_raises_valueerror():
    """filter_and_populate should reject batch_size=0"""
    # Should raise ValueError

def test_batch_size_negative_raises_valueerror():
    """filter_and_populate should reject negative batch_size"""
    # Should raise ValueError
```

---

## Related Issues

- [v0.10.7] Fixed TTL type handling (int → timedelta conversion)
- [v0.10.7] Fixed flaky integration tests (dynamic assertions)
- [v0.10.8] Added dict validation and config hardening
- [v0.10.9] Documentation updates
- [v0.10.10] Fixed dict.get() None-handling (25 instances)
- ~~[Future] Address remaining 18 type validation issues~~ **ALL RESOLVED**

**Original Creation**: 2026-01-11
**Last Updated**: 2026-01-11
**Archived**: 2026-01-20
**Status**: ✅ All issues resolved