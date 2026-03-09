# Server Capabilities & Dynamic Fragments

## Problem

The Stash GraphQL client needs to work against servers at different versions. The upstream Stash project adds new fields, renames types, and deprecates old ones across releases. If the client requests a field the server doesn't know about, the query fails.

| Component              | Risk                                     | Example                                                                          |
| ---------------------- | ---------------------------------------- | -------------------------------------------------------------------------------- |
| **Response fragments** | Query fails if requesting unknown fields | `custom_fields` on Scene (appSchema < 79)                                        |
| **Input variables**    | Server rejects unknown input fields      | `custom_fields` in SceneFilterType                                               |
| **Type renames**       | Old type name gone on new servers        | `PHashDuplicationCriterionInput` removed in favor of `DuplicationCriterionInput` |

## Design

### Architecture

```
                         ┌─────────────────────┐
                         │   StashClient        │
                         │   initialize()       │
                         └──────┬──────────────┘
                                │
                    1. establish session
                                │
                    2. detect_capabilities()
                                │ single query: version + appSchema + __schema
                                ▼
                    ┌───────────────────────────┐
                    │  ServerCapabilities       │
                    │  (frozen dataclass)       │
                    │                           │
                    │  app_schema: 84           │
                    │  version: "v0.30.1-*"     │
                    │  query_names: frozenset   │
                    │  mutation_names: frozenset │
                    │  type_names: frozenset    │
                    │  type_fields: Mapping     │
                    └───────────┬───────────────┘
                                │
                    3. fragment_store.rebuild(capabilities)
                                │
                                ▼
                    ┌───────────────────────┐
                    │    FragmentStore       │
                    │    (singleton)         │
                    │                       │
                    │  SCENE_FIELDS         │ ← base + custom_fields (if >= 79)
                    │  FIND_SCENES_QUERY    │ ← rebuilt from SCENE_FIELDS
                    │  PERFORMER_FIELDS     │ ← base + career_start/end (if >= 78)
                    │  _capabilities        │ ← stored ref for input gating
                    │  ...                  │
                    └───────────────────────┘
```

### Detection Query

A single GraphQL request at connect time that combines system status with full schema introspection:

```graphql
{
  version {
    version
  }
  systemStatus {
    appSchema
    status
  }
  __schema {
    queryType {
      name
      fields {
        name
      }
    }
    mutationType {
      name
      fields {
        name
      }
    }
    types {
      name
      kind
      fields {
        name
      }
      inputFields {
        name
      }
    }
  }
}
```

This replaces the previous approach of individual `__type(name: "...")` probes. A single `__schema` introspection gives the client a complete picture of the server's schema — no need to add new probes when new capabilities are introduced.

This works with `fetch_schema_from_transport=False` (required because Stash's deprecated required arguments violate the GraphQL spec, causing gql's schema validation to reject the introspection result).

### Why Not Full Schema Validation?

Stash deprecates **required arguments** on mutations (e.g., `Mutation.movieCreate(input:)`), which violates the GraphQL spec. The `gql` library correctly rejects this:

```
TypeError: Required argument Mutation.sceneIncrementO(id:) cannot be deprecated.
Required argument Mutation.movieCreate(input:) cannot be deprecated.
...
```

Until Stash removes or makes these arguments optional, `fetch_schema_from_transport=True` will not work. Our `__schema` introspection approach sidesteps this entirely.

## Server Version Map

### Minimum Supported Version

**v0.30.0** (appSchema >= 75). If the detected `appSchema` is below 75, the client raises `StashVersionError` during initialization and refuses to connect. This is a hard requirement — the client is not designed to work with older servers.

### appSchema Feature Map

| appSchema | Feature                                        | Stash Release    |
| --------- | ---------------------------------------------- | ---------------- |
| 75        | Date precision, tag StashID, multi-URL studios | v0.30.0 (stable) |
| 76        | Studio custom fields                           | develop          |
| 77        | Tag custom fields                              | develop          |
| 78        | Career start/end (replaces career_length)      | develop          |
| 79        | Scene custom fields                            | develop          |
| 80        | Studio `organized` flag                        | develop          |
| 81        | Gallery custom fields                          | develop          |
| 82        | Group custom fields                            | develop          |
| 83        | Image custom fields                            | develop          |
| 84        | Folder basename + parent_folders               | develop          |

### What appSchema Tracks vs Doesn't

`appSchema` is a **database migration counter** — it increments when the SQLite schema changes (new tables, columns, indexes). It does **not** increment for GraphQL-only additions like new mutations, config fields, or filter type renames.

| Detectable via appSchema         | Not detectable via appSchema                           |
| -------------------------------- | ------------------------------------------------------ |
| custom_fields (entity storage)   | New mutations (destroyFiles, revealFile\*)             |
| career_start/end (column change) | Config fields (sprite settings, disableCustomizations) |
| Studio organized (column)        | Filter type renames (PHash -> Duplication)             |
| Folder basename (column + index) | New scan options (imagePhashes)                        |

For non-appSchema features, the client now uses `__schema` introspection. Lookup methods on `ServerCapabilities` (`has_mutation()`, `has_query()`, `has_type()`, `type_has_field()`, `input_has_field()`) provide dynamic queries against the parsed schema data.

## Components

### `ServerCapabilities` (frozen dataclass)

```python
@dataclass(frozen=True)
class ServerCapabilities:
    app_schema: int
    version_string: str = ""
    query_names: frozenset[str] = frozenset()
    mutation_names: frozenset[str] = frozenset()
    type_names: frozenset[str] = frozenset()
    type_fields: MappingProxyType[str, frozenset[str]] = MappingProxyType({})

    # Dynamic lookup methods
    def has_query(self, name: str) -> bool: ...
    def has_mutation(self, name: str) -> bool: ...
    def has_type(self, name: str) -> bool: ...
    def type_has_field(self, type_name: str, field_name: str) -> bool: ...
    def input_has_field(self, type_name: str, field_name: str) -> bool: ...

    # appSchema-derived properties
    @property
    def has_scene_custom_fields(self) -> bool:
        return self.app_schema >= 79

    @property
    def has_performer_career_start_end(self) -> bool:
        return self.app_schema >= 78

    # ... one property per appSchema-gated feature
```

The parsed `__schema` data is stored as immutable collections. Lookup methods check against these sets. appSchema-derived properties remain for features tied to database migrations. Frozen to prevent mutation after detection.

### `FragmentStore` (singleton)

Holds all query/mutation strings as instance attributes. Initialized with base (minimum-version-safe) fields at import time, then rebuilt when capabilities are detected. Also stores a reference to `_capabilities` for use by `StashInput.to_graphql()`.

```python
class FragmentStore:
    def __init__(self):
        self._capabilities = None
        self._build_base()

    def rebuild(self, capabilities: ServerCapabilities):
        self._capabilities = capabilities
        self._build_fields()
        self._build_queries()
```

Consumers import the singleton directly:

```python
from stash_graphql_client.fragments import fragment_store

result = await self.execute(
    fragment_store.FIND_SCENES_QUERY,
    {"filter": filter_, "scene_filter": scene_filter},
)
```

### Gated Field Constants

Each entity has a `_BASE_*_FIELDS` constant (unconditionally safe) and conditional additions:

| Entity    | Base Constant            | Conditional Fields                           |
| --------- | ------------------------ | -------------------------------------------- |
| Scene     | `_BASE_SCENE_FIELDS`     | `custom_fields` (>= 79)                      |
| Performer | `_BASE_PERFORMER_FIELDS` | `career_start`, `career_end` (>= 78)         |
| Studio    | `_BASE_STUDIO_FIELDS`    | `custom_fields` (>= 76), `organized` (>= 80) |
| Tag       | `_BASE_TAG_FIELDS`       | `custom_fields` (>= 77)                      |
| Gallery   | `_BASE_GALLERY_FIELDS`   | `custom_fields` (>= 81)                      |
| Image     | `_BASE_IMAGE_FIELDS`     | `custom_fields` (>= 83)                      |
| Group     | `_BASE_GROUP_FIELDS`     | `custom_fields` (>= 82)                      |
| Folder    | `_BASE_FOLDER_FIELDS`    | `basename`, `parent_folders` (>= 84)         |

Queries that don't embed gated fields (VERSION_QUERY, SYSTEM_STATUS_QUERY, destroy mutations, SQL queries) are static and never rebuilt.

## Input Capability Gating (`__safe_to_eat__`)

### Problem

The upstream Stash schema evolves faster than client releases. When the client sends unknown fields in GraphQL input types, the server rejects the request with a validation error. The UNSET system handles this for **optional fields users don't set**, but doesn't protect against **fields the client always includes** (e.g., new fields with default values that older servers don't recognize).

### Solution

`StashInput` subclasses can declare a `__safe_to_eat__` class variable listing GraphQL field names (as they appear in the schema) that are known to be absent on older server versions:

```python
class GenerateMetadataInput(StashInput):
    __safe_to_eat__: ClassVar[frozenset[str]] = frozenset({
        "paths", "imageIDs", "galleryIDs", "imagePhashes",
    })

    paths: list[str] | None | UnsetType = UNSET
    # ...
```

### How It Works

When `to_graphql()` is called, after building the aliased dict (field names matching the GraphQL schema), it checks every key against the server schema (via `fragment_store._capabilities`):

1. **Type unknown to server** → skip gating entirely (don't blow up on unrecognized types)
2. **Field supported** → pass through normally
3. **Field unsupported + in `__safe_to_eat__`** → silently strip with a `warnings.warn()`
4. **Field unsupported + NOT in `__safe_to_eat__`** → raise `ValueError`

```python
def _apply_capability_gating(self, result: dict[str, Any], caps: Any) -> None:
    type_name = type(self).__name__
    if not caps.has_type(type_name):
        return  # Type not in schema — skip gating

    for key in list(result.keys()):
        if not caps.input_has_field(type_name, key):
            if key in self.__safe_to_eat__:
                warnings.warn(f"Server lacks '{key}' on {type_name}; stripping")
                del result[key]
            else:
                raise ValueError(f"Server does not support '{key}' on {type_name}")
```

### Zero Call-Site Changes

`fragment_store` already holds `_capabilities` after `rebuild()`. All existing `to_graphql()` calls remain parameterless — gating is applied transparently.

## Pydantic Type Strategy

### Superset Models

Pydantic models contain **all fields** for all supported versions. Fields default to `UNSET`. When the server doesn't return a field (because the fragment didn't request it), it stays `UNSET`.

```python
class Scene(StashObject):
    title: str | None | UnsetType = UNSET
    custom_fields: Map | UnsetType = UNSET  # Only populated on >= 79
```

### Input Safety

The three-level UNSET system handles inputs automatically:

- `UNSET` -> field excluded from `to_graphql()` -> never sent to server
- `None` -> field sent as `null`
- Value -> field sent with value

Users who don't set new fields never trigger server errors, regardless of version. For fields that _are_ set but the server doesn't support, `__safe_to_eat__` provides graceful degradation.

### Type Rename Handling

**Policy:** Only track current and future renames via capabilities. Past renames (movie -> group) are already handled in the codebase with wrapper types and are not retrofitted.

For `PHashDuplicationCriterionInput` -> `DuplicationCriterionInput`:

```python
class DuplicationCriterionInput(StashInput):
    """Canonical name (appSchema >= 76+)."""
    duplicated: bool | None | UnsetType = UNSET
    distance: int | None | UnsetType = UNSET
    phash: bool | None | UnsetType = UNSET
    url: bool | None | UnsetType = UNSET
    stash_id: bool | None | UnsetType = UNSET
    title: bool | None | UnsetType = UNSET

# Deprecated alias for backward compatibility
PHashDuplicationCriterionInput = DuplicationCriterionInput
```

## Client Integration

### Init Flow

```
StashClient.__init__()
    |-- super().__init__() (StashClientBase)

StashClient.initialize()
    |-- super().initialize()
    |   |-- Create transports, gql clients, sessions
    |   |-- Set _initialized = True
    |-- detect_capabilities(self._raw_execute, self.log)
    |   |-- Execute CAPABILITY_DETECTION_QUERY
    |   |-- Parse __schema into frozensets
    |   |-- Raise StashVersionError if appSchema < 75
    |   |-- Return ServerCapabilities
    |-- fragment_store.rebuild(self._capabilities)
        |-- Store _capabilities reference
        |-- Rebuild all gated field strings
        |-- Rebuild all dependent query strings
```

### `_raw_execute()`

A private method on `StashClientBase` that bypasses the `_ensure_initialized()` check, used only during capability detection (the session is established but `_initialized` hasn't been set yet in the override flow):

```python
async def _raw_execute(self, query, variables=None):
    operation = gql(query)
    if variables:
        operation.variable_values = variables
    result = await self._session.execute(operation)
    return dict(result)
```

## Error Handling

### `StashVersionError`

Raised during `detect_capabilities()` when `appSchema < MIN_SUPPORTED_APP_SCHEMA (75)`:

```python
class StashVersionError(StashError):
    """Server version is below the minimum supported version."""
```

This surfaces during `StashClient.initialize()`, preventing the client from operating against an incompatible server. The error message includes both the detected version/appSchema and the minimum required.

## Testing

- **Unit tests** for `ServerCapabilities` lookup methods and property derivation
- **Unit tests** for `__safe_to_eat__` gating (strip, pass-through, ValueError, no-gating-when-None)
- **Unit tests** for `FragmentStore` with different capability levels (appSchema 75 vs 84)
- **Integration tests** cross-validating lookup methods against live server introspection
- **Regression** on existing mixin tests (unchanged behavior for minimum-version servers)
