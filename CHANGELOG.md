<!-- markdownlint-configure-file { "MD024": { "siblings_only": true } } -->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.12.1] - 2026-04-22

### Added

- **Side Mutations user guide** (`docs/guide/side-mutations.md`): comprehensive coverage of
  the `__side_mutations__` dict, `_queue_side_op()`, built-in handlers, bulk relationship
  handler factory, interaction with `save_batch`, and custom handler subclassing
- **Relationship DSL user guide** (`docs/guide/relationship-dsl.md`): covers `belongs_to` /
  `habtm` / `has_many` / `has_many_through` with decision tree, auto-derivation behavior,
  and an explicit note that `has_many_through` is **not** Rails-style `through: :model` —
  here it means "through a wrapper input type carrying relationship-level metadata"
  (e.g., `SceneGroupInput` with `scene_index`, `GroupDescriptionInput` with `description`)
- **Narrative intros** on `docs/api/batch.md` and `docs/api/store.md` explaining the
  three-layer batch API (`execute_batch` → `save_batch` → `save_all`) and cross-linking
  the relevant guides
- **"See also" admonition** at the top of
  `docs/architecture/bidirectional-relationships.md` pointing readers at the new user-facing
  DSL and side-mutations guides
- **Module-level docstring** on `stash_graphql_client/client_helpers.py` describing
  `async_lru_cache`, `normalize_str` / `str_compare`, and the `AsyncCachedFunction` protocol
- `FromGraphQLMixin` added to `ConfigScrapingResult`, bringing it in line with all sibling
  `ConfigXxxResult` classes (previously the only one without it)
- `BatchResult.__getitem__` / `__len__` / `__iter__`: one-line docstrings

### Changed

- **Project-wide docstring rule**: `Returns:` and `Args:` sections for methods that
  accept or return Pydantic types now name the type without bulleting its fields. The
  type definition is the single source of truth. Eliminates the drift class that caused
  issue #25 (`get_configuration()` docstring listed 6 of 7 `ConfigResult` fields, silently
  omitting `plugins` after PR #26). Applied across ~35 mixin methods and 4 class-level
  docstrings
- **Entity class docstrings** for `SceneMarker`, `Tag`, `Image` rewritten from schema-echo
  one-liners to behavioral-quirk summaries (relationship-object construction, hierarchical
  - bulk-update side mutations, `visual_files` union + `o_counter` side handler +
    scanner-only creation, respectively)
- **Filter criterion class docstrings** (`IntCriterionInput`, `FloatCriterionInput`,
  `StringCriterionInput`, `DateCriterionInput`, `TimestampCriterionInput`,
  `MultiCriterionInput`, `HierarchicalMultiCriterionInput`, `PhashDistanceCriterionInput`,
  `CustomFieldCriterionInput`) now describe modifier semantics, `value2` / `depth` /
  `distance` meaning, and cross-reference `CriterionModifier`
- **`fragments.py` module docstring** expanded to reflect the v0.12 `FragmentStore`
  architecture and introspection-based version gating
- **`PluginConfigMap` scalar alias**: inline comment documents the structure — outer key
  is plugin ID, inner dict is that plugin's configuration
- **`ScrapedTag.parent` inline comment** now annotates the field's introspection-gated
  status (`ServerCapabilities.has_scraped_tag_parent`), consistent with sibling
  `appSchema >=` annotations on the same class
- Navigation entries for the new user guides registered in `mkdocs.yml`

### Fixed

- `get_configuration()` docstring: `plugins` field now surfaced via the type reference
  (previously omitted — the plugin-inspection example mis-directed users to `config.ui`,
  the exact misdirection reported in issue #25)
- `get_configuration()` examples: `databasePath` / `parallelTasks` / `scraperCertCheck`
  corrected to snake_case attribute names (previous camelCase would raise `AttributeError`
  at runtime — those are Pydantic serialization aliases, not accessors)
- `Scene.rating100` and `Scene.o_counter`: removed misleading
  `# not used in this client` inline comments. `rating100` IS used via
  `__field_conversions__`; `o_counter` IS managed via the `_save_o` side handler
- `reorder_sub_groups()` docstring example: syntax error (dict-key string mixed into a
  keyword-argument call) corrected — would have raised `SyntaxError` if copy-pasted
- `find_tags()` docstring: empty trailing `Note:` block removed
- `README.md` Quick Example: wrapped in `async def main()` + `asyncio.run(main())` with
  correct indentation (previously would not run — bare `await` at module scope)
- `docs/guide/getting-started.md` Stash version floor: raised from "v0.25.0+" to
  "v0.30.0+ (appSchema 75+); currently tracking v0.31.x" to match the hard floor in
  `capabilities.MIN_SUPPORTED_APP_SCHEMA = 75`
- `tests/integration/test_subscription_integration`: assertion no longer requires
  `JobStatus.FINISHED` — any terminal state (`FINISHED` / `CANCELLED` / `FAILED`) passes,
  since `metadata_generate(covers=True)` against an empty test Stash legitimately ends
  `CANCELLED`. Also collapsed a dead-code branch in the break logic
- `tests/integration/test_find_scenes_with_pagination`: removed racy cross-query count
  comparison. Per-query invariants (`page size ≤ per_page`, `count ≥ page size`) replace
  the tolerance-based total-count check that couldn't survive parallel test activity

## [0.12.0] - 2026-04-15

### Added

- **Generic `__side_mutations__` mechanism on `StashObject`**: Fields persisted via separate GraphQL
  mutations instead of the main create/update input. Handlers fire AFTER the main mutation so new
  objects have their real server ID. Multiple fields sharing the same handler are deduplicated by
  identity
- **Queued side operations** (`_pending_side_ops`): Entity methods can queue async closures via
  `_queue_side_op()` that fire during `save()` after field-based side mutations. Enables operations
  like `scene.reset_play_count()` or `scene.generate_screenshot()` that don't map to a trackable
  field change
- **Side mutation implementations**:
  - `Gallery.cover`: `setGalleryCover` / `resetGalleryCover`
  - `Gallery.images`: `addGalleryImages` / `removeGalleryImages` with `add_image()` /
    `remove_image()` convenience methods and automatic inverse sync
  - `Scene.resume_time` + `Scene.play_duration`: `sceneSaveActivity` (deduplicated handler)
  - `Scene.o_counter` + `Scene.o_history`: `sceneAddO` / `sceneDeleteO` (list-diff handler)
  - `Scene.play_count` + `Scene.play_history`: `sceneAddPlay` / `sceneDeletePlay`
  - `Image.o_counter`: `imageIncrementO` / `imageDecrementO` / `imageResetO` (delta-computing)
  - Scene queued operations: `reset_play_count()`, `reset_o()`, `reset_activity()`,
    `generate_screenshot()`
- **Bulk-update side mutations** for bidirectional relationship writes where the upstream API has
  no direct write path from the entity's side:
  - `Performer`: `scenes` / `galleries` / `images` via bulk updates with `performer_ids`
  - `Studio`: `scenes` / `images` / `galleries` / `groups` via bulk updates with scalar `studio_id`
  - `Tag`: `scenes` / `images` / `galleries` / `performers` / `groups` / `scene_markers` via bulk
    updates with `tag_ids` — all 6 content types
- **`_make_bulk_relationship_handler()` factory** on `StashObject`: shared diff + bulk-update logic
  with configurable `batch_size` (default 500, respects SQLite's `SQLITE_MAX_VARIABLE_NUMBER`)
- **`StashObject` ID validator**: `id` field now enforces numeric-string or UUID4 format via
  `@field_validator`, matching actual Stash server behavior
- **Batched GraphQL mutations** — collapse N individual mutations into a single aliased HTTP request:
  - `client.execute_batch(operations)`: low-level API with automatic chunking (`max_batch_size=250`),
    per-operation error mapping, and `_convert_datetime()` pre-processing
  - `store.save_batch(objects)`: entity-aware batch save with cascade saves, creates-before-updates
    ordering, UUID→real-ID cache key remapping, and sequential per-entity side mutations
  - `store.save_all()`: ORM flush — scans identity map for dirty/new entities, delegates to
    `save_batch()`
- **`BatchOperation`**, **`BatchResult`**, and **`StashBatchError`** in
  `stash_graphql_client.client.batch`
- **`return_fields` override on all bulk update methods**: `bulk_image_update()`,
  `bulk_scene_update()`, `bulk_gallery_update()`, `bulk_group_update()`,
  `bulk_performer_update()`, `bulk_studio_update()`, `bulk_scene_marker_update()` now accept
  an optional `return_fields` keyword argument, avoiding server-side resolution of all
  relationship fields for every entity in the batch
- **ActiveRecord-style relationship DSL**: new factory helpers `belongs_to()`, `habtm()`,
  `has_many()`, and `has_many_through()` for declaring `__relationships__` with minimal
  boilerplate. Auto-derives `target_field`, `query_field`, and `filter_query_hint` via
  `__init_subclass__`
- **`populate()` filter-query resolution**: `StashEntityStore.populate()` now detects
  `filter_query` strategy relationships (e.g., `Tag.scenes`, `Studio.scenes`) and fetches
  them via lightweight `find*` queries resolved through the identity map cache
- **Configurable client timeout**: `StashClientBase` reads a `Timeout` key from the connection
  dict (default 30s) and propagates it to all transports
- **`plugins` field on `ConfigResult`**: Exposes `plugins: PluginConfigMap` from the GraphQL
  schema for retrieval of per-plugin configuration maps (closes #25, ports PR #26)
- **`ScrapedTag.parent` field**: Introspection-gated via `has_scraped_tag_parent` capability
  for tag hierarchy support in scraped data (stashapp/stash#6620)
- **`Folder.sub_folders` field**: Introspection-gated via `has_folder_sub_folders` capability
  (Stash v0.31.0+, stashapp/stash#6494)
- **Documentation**: Batched Mutations user guide, Batch Operations API reference,
  architecture design history document

### Changed

- All entity types refactored from verbose `RelationshipMetadata(...)` declarations to the
  new DSL helpers (`belongs_to`, `habtm`, `has_many`, `has_many_through`)
- `populate()` now separates direct fields from filter-query fields, fetching each category
  through the appropriate strategy
- Side mutation handlers use `return_fields="id __typename"` for all bulk calls, significantly
  reducing server load on large bulk relationship writes
- Delayed `StashInput` unknown-field enforcement (`extra="forbid"`) from v0.12.0 to v0.13.0;
  deprecation warnings updated accordingly
- Bumped ruff pre-commit hook v0.15.7 → v0.15.10
- CI: test matrix expanded to Python 3.14 and 3.15 (prerelease)
- CI: `codecov/codecov-action` upgraded v5 → v6
- Updated Stash GraphQL schema from upstream (v0.31.0)

### Fixed

- Identity map merge path corruption on union-typed list fields (`visual_files` and other
  `list[UnionType]` fields corrupted to raw dicts after a second `from_graphql()` call)
- `_process_nested_graphql` and `_process_nested_cache_lookups` skipping union list types
  (`isinstance(UnionType, type)` is `False` — now builds `__typename → subclass` maps)
- `_received_fields` empty on nested union-typed file objects (discriminator validators now
  pass `from_graphql` context)
- `populate()` snapshot updates now include filter-query fields, preventing phantom dirty state
- `Image.galleries` missing `inverse_query_field` (asymmetric inverse sync bug)
- `Group.studio` missing `inverse_query_field` for bidirectional sync
- `Scene.groups` not serialized by `to_input()` (was in `__tracked_fields__` but not
  `__relationships__`)
- `_process_list_relationship()` `BaseModel` transforms now call `model_dump()` instead of
  `str()` (fixes `Scene.groups` serialization)
- Graceful inverse sync when inverse field stays UNSET after `populate()`
- `Studio.groups` type annotation: `list[Any]` → `list[Group]`

## [0.11.2] - 2026-04-03

### Changed

- Updated Stash GraphQL schema from upstream (v0.31.0)
- Added `Folder.sub_folders` field (introspection-gated via `type_has_field`; upstream added as a
  pure resolver with no appSchema bump)
- Added `has_folder_sub_folders` capability property to `ServerCapabilities`
- `FragmentStore` conditionally injects `sub_folders` into `FolderFields` fragment when server
  reports the field

## [0.11.1] - 2026-03-21

### Changed

- Migrated 17 inline scraper queries to `FragmentStore` with capability-gated field assembly (missed
  during original 0.11.0 `FragmentStore` refactor)
- Synced Stash GraphQL schema from upstream (appSchema updates, `Group.custom_fields`,
  `CircumisedEnum` → `CircumcisedEnum` rename, career date fields `Int` → `String` with coercion
  validators)
- Use env var for Stash config instead of editing `config.yml` in CI workflow

### Fixed

- Fixed missing `penis_length`/`circumcised` fields in `scrapeMultiPerformers` and
  `career_start`/`career_end` in scraper fragments (discovered during `FragmentStore` migration)
- Fixed `job_queue()` crashing when Stash returns null entries within the job list (e.g.,
  `jobQueue: [{...}, null, {...}]` during job cleanup race conditions)

## [0.11.0] - 2026-03-09

### Added

- **Server capability detection** (`capabilities.py`): `ServerCapabilities` frozen dataclass with
  dynamic lookup methods (`has_query()`, `has_mutation()`, `has_type()`, `type_has_field()`,
  `input_has_field()`); `detect_capabilities()` issues a single `__schema` introspection query at
  connect time; raises `StashVersionError` for servers below appSchema 75 (pre-v0.30.0)
  (see [architecture/capabilities-and-fragments](docs/architecture/capabilities-and-fragments.md))
- **Dynamic `FragmentStore`**: rebuilt at connect time via `fragment_store.rebuild(capabilities)` so
  version-gated fields are included only when supported; all client mixins reference
  `fragment_store.*` instead of module-level `fragments.*` constants
  (see [architecture/capabilities-and-fragments](docs/architecture/capabilities-and-fragments.md))
- **Entity lifecycle methods on `StashObject`**: `entity.delete(client)`,
  `EntityType.bulk_destroy(client, ids)`, `EntityType.merge(client, source_ids, destination_id)` —
  replaces manual mutation calls; auto-invalidates cache on delete
- **`StashEntityStore` additions**: `get_cached()` (sync cache-only lookup), `delete()` (delete +
  invalidate), `invalidate(entity)` overload
- **`__safe_to_eat__` input gating**: `StashInput` subclasses can declare fields that may be absent
  on older servers; `to_graphql()` silently strips them when unsupported
- **Selective snapshot update after identity map merge**: `_update_snapshot_for_fields()` prevents
  phantom dirty state after cache-hit merges or `store.populate()` while preserving user
  modifications to unrelated fields
  (see [architecture/dirty-tracking](docs/architecture/dirty-tracking.md))
- **Shallow `__repr__`**: Two-tier repr system that prevents exponential recursive expansion with
  bidirectional relationships; `_short_repr()` for compact nested display
- **`StashUnmappedFieldWarning`**: Emitted when `StashObject` receives fields not declared in the
  model (server newer than client); purely informational
- **`StashError` / `StashVersionError`**: Exported from top-level `stash_graphql_client` package
- **BaseFile `__typename` discrimination**: Dispatches to correct subclass (`VideoFile`, `ImageFile`,
  `GalleryFile`, `BasicFile`) based on `__typename`
- **Schema alignment** (Stash appSchema 71–84):
  - New client methods: `destroy_files()`, `reveal_file_in_file_manager()`,
    `reveal_folder_in_file_manager()`, `stashbox_batch_tag_tag()`
  - Filter additions: `PerformerFilterType` (`marker_count`, `markers_filter`, `career_start`,
    `career_end`); `GroupFilterType` (`scene_count`, `custom_fields`); `ImageFilterType`
    (`phash_distance`); `FolderFilterType` (`basename`); `GalleryFilterType` (`parent_folder`)
  - Input additions: `BulkPerformerUpdateInput` (`career_start`, `career_end`);
    Scene/Gallery/Image/Group bulk inputs (`custom_fields`); `StudioCreateInput`/`UpdateInput`
    (`organized`); `TagsMergeInput` (`values`); `CustomFieldsInput` (`remove`);
    `GenerateMetadataInput` (`paths`, `imagePhashes`, `imageIDs`, `galleryIDs`)
  - Config: sprite fields on `ConfigGeneralResult`; `disableCustomizations` on
    `ConfigInterfaceInput`/`Result`; `gallery` on `ConfigDisableDropdownCreate*`;
    `disableAnimation` on `ConfigImageLightbox*`
  - Scraped types: `ScrapedPerformer`/`ScrapedPerformerInput` (`career_start`, `career_end`);
    `ScrapedTag` (`description`, `alias_list`)
- **Architecture documentation**:
  [capabilities-and-fragments](docs/architecture/capabilities-and-fragments.md),
  [dirty-tracking](docs/architecture/dirty-tracking.md),
  [pydantic-internals](docs/architecture/pydantic-internals.md)
- **[`MIGRATION.md`](MIGRATION.md)**: Migration guide for 0.10.x → 0.11.0

### Changed

- **`StashEntityStore` renames**: `clear_type()` → `invalidate_type()`; `ttl_seconds` → `default_ttl`
- **StrEnum Migration**: Migrated 33 string enum classes from `(str, Enum)` to `StrEnum`
- **`itertools.batched()` Migration**: Replaced manual batching (Python 3.12+)
- `log.error()` → `log.exception()` in all exception handlers (preserves full tracebacks)
- Subscription teardown: explicit `aclose()` in `finally` blocks prevents C-level crashes on
  Python 3.14+ under xdist
- Performer/Studio dirty tracking: added missing `__tracked_fields__` / `__field_conversions__`
  entries
- `dump_graphql_calls()` debug utility across all 64 test files — auto-prints GraphQL
  request/response details on failure
- Comprehensive test coverage for capabilities, fragment store, entity lifecycle, dirty tracking,
  shallow repr, input deprecation warnings, safe-to-eat gating
- Integration tests for file, folder, marker, performer, studio, tag CRUD and bulk operations
- Stash setup/init step in CI workflow (systemStatus check + setup mutation)
- Skip tests gracefully: `revealFile`/`revealFolder` on access denied, subscriptions without ffmpeg
- `NO_PROXY=*` for xdist stability; gallery/image tests serialized with `xdist_group`
- Project-level `ResourceWarning` suppression for async transport teardown on Python 3.14

### Fixed

- **~30 incorrect Pydantic aliases** verified against live server across `ScrapedPerformerInput`,
  `ScrapedSceneInput`, `Scene`, multiple `Scraped*` types, `PluginSetting`, `Package`/`PackageSource`
- **`StashObject.to_input()` UNSET serialization**: Replaced `model_dump(exclude_none=True)` with
  `input_obj.to_graphql()` — UNSET sentinels no longer leak into gql transport
- **`_BASE_STUDIO_FIELDS`**: Added missing `rating100`, `favorite`, `stash_ids`
- **`Performer.custom_fields`** fragment: moved to base fields (available since appSchema 71)
- **Pydantic v2 `UserWarning`** in `StashObject`: replaced `__init__` override with
  `model_validator`s (`_inject_uuid`, `_set_is_new`)
- **Folder fragment**: Replaced deprecated `parent_folder_id`/`zip_file_id` with object references
- **Studio `handle_deprecated_url`**: Guard for non-dict data in before validator
- **Performer relationship metadata**: Corrected Tag `inverse_query_field` to `None`
- **StashInput `_warn_extra_fields`**: Excludes `_`-prefixed internal fields
- **`types/__init__.py` `__all__`**: Removed 42 duplicate entries
- **6 mypy errors**: Fixed overload signatures and `BaseModel`-typed ClassVar attribute access

### Deprecated

- **Extra Fields Behavior**: Unknown fields in dict inputs now emit `DeprecationWarning`.
  In v0.13.0+, these will be rejected with `ValidationError`.

## [0.10.14] - 2026-02-15

### Fixed

- **Private Attribute Survival**: Fixed Pydantic v2 `validate_assignment=True` silently destroying internal state (`_snapshot`, `_is_new`, `_received_fields`) on every field assignment
  - Root cause: `object.__setattr__()` stores values in `__dict__`, which Pydantic rebuilds on each validated assignment — combined with `extra="allow"`, stale fallback values from `__pydantic_extra__` would be returned instead
  - Converted all three private attributes to Pydantic `PrivateAttr` declarations (stored in `__pydantic_private__`, which is never rebuilt)
  - Replaced all `object.__setattr__` calls for `_received_fields` across production and test code with direct assignment
  - Symptoms: phantom dirty fields after identity map cache-hit merges, `_is_new` flag lost after field assignment, `_received_fields` tracking lost after field assignment
  - Location: `stash_graphql_client/types/base.py`, `stash_graphql_client/store.py`

### Added

- **Regression Tests**: Added `TestPrivateAttrSurvival` class with 5 tests verifying private attributes survive `validate_assignment` `__dict__` rebuilds
  - Tests snapshot survival through identity map merge + assignment, `_is_new` survival (both True and False), `_received_fields` survival, and snapshot survival across multiple consecutive assignments

## [0.10.13] - 2026-02-11

### Fixed

- **Store Memory Leak**: Fixed `store.filter()` creating full-cache snapshots on every call, causing memory exhaustion during batch processing
  - Added `_type_index: dict[str, set[str]]` secondary index mapping type names to entity IDs
  - `filter()`, `filter_strict()`, `filter_and_populate()`, and `filter_and_populate_with_stats()` now iterate only the relevant type's entries directly under the lock — zero intermediate copies
  - `invalidate_type()` improved from O(n) full-cache scan to O(k) type-only lookup
  - Expired entries are proactively cleaned during `filter()` iteration
  - All cache mutation paths (`_cache_entity`, `invalidate`, `invalidate_type`, `invalidate_all`, `save`) maintain the type index
  - Location: `stash_graphql_client/store.py`

### Added

- **Test Coverage**: Added tests for type index edge cases, orphaned index cleanup, and `job_queue()` unexpected type handling
  - Restored 100% line and branch coverage

## [0.10.12] - 2026-02-04

### Fixed

- **Job Queue Null Handling**: Fixed `job_queue()` method crashing with "'NoneType' object is not iterable" when no jobs are running
  - Stash returns `jobQueue: null` in GraphQL response when no jobs are active
  - Replaced implicit truthiness check (`or []`) with explicit None checking
  - Added defensive type validation to handle malformed responses gracefully
  - Location: `stash_graphql_client/client/mixins/jobs.py`

## [0.10.10] - 2026-01-19

### Fixed

- **GraphQL None Handling**: Fixed 25 instances across client mixins where `dict.get()` incorrectly used `None` as default value
  - GraphQL distinguishes between explicit null values and missing fields
  - Changed pattern from `data.get("field", None)` to `data.get("field")` (returns `None` if missing)
  - Affected methods: job queue operations, config mutations, scene/image/gallery/performer operations, tag updates, and more
  - Prevents sending unintended null values to GraphQL mutations
  - Locations: `client/mixins/*.py`, `context.py`, `store.py`, `types/performer.py`, `types/tag.py`
- **Test Coverage**: Added tests to achieve 100% branch coverage
  - Added test for `verify_ssl` string-to-bool conversion in `StashClient.initialize()`
  - Added test for mixed-type list handling in store's nested field population
  - Fixed datetime serialization in scene activity mutation tests
  - Fixed field name references in nested filter tests (files → visual_files)

## [0.10.9] - 2026-01-12

### Fixed

- **Documentation**: Updated CHANGELOG.md to include release notes for v0.10.8.

## [0.10.8] - 2026-01-12

### Changed

- **Dict Input Validation**: Methods accepting `SomeInput | dict[str, Any]` now validate dicts through Pydantic before sending to GraphQL
  - Type checking ensures `input_data` is actually a dict (not other types)
  - Pydantic validation catches field type errors, required field issues, and invalid values
  - Provides clear error messages instead of silent GraphQL failures
  - Affects 50+ methods across all client mixins (scene, image, gallery, tag, studio, performer, group, etc.)
  - Examples: `bulk_image_update()`, `scene_destroy()`, `tag_destroy()`, etc.
  - Location: All files in `stash_graphql_client/client/mixins/*.py`
- **Config Hardening**: Tightened connection parsing (scheme, port, verify_ssl) and context key normalization
- **Security**: Blocked protected config path edits with `StashConfigurationError`
- **Store**: Added batch-size guards and performer avatar file checks

### Deprecated

- **Extra Fields Behavior**: Currently, extra/unknown fields in dict inputs are silently ignored (Pydantic default)
  - **Future Change**: In a future release, passing unknown fields will raise a validation error (`extra="forbid"`)
  - **Action Required**: Review your code for typos or outdated field names in dict inputs
  - **Example**: `{"ids": [...], "tag_id": "x"}` instead of `"tag_ids"` will be rejected

## [0.10.7] - 2026-01-11

### Fixed

- **TTL Type Handling**: `set_ttl()` and `__init__()` now accept `int` (seconds) in addition to `timedelta`, fixing `AttributeError: 'int' object has no attribute 'total_seconds'`
- **Integration Tests**: Fixed flaky gallery count assertions to use dynamic checks instead of hardcoded values

## [0.10.6] - 2026-01-10

### Fixed

- **Store Filter Criteria**: Fixed critical bug where string list fields (`aliases`, `urls`, `captions`) were incorrectly wrapped in lists for filtering
  - These fields use `StringCriterionInput` for substring matching within list items, not `MultiCriterionInput` for ID membership
  - Removed 6 incorrect fields from `multi_value_fields` set: `aliases`, `child_studios`, `markers`, `files`, `stash_ids`, `folders`
  - Fixes queries like `store.find_one(Performer, aliases__contains="name")` which were sending `{"value": ["name"]}` instead of `{"value": "name"}`
  - Location: `stash_graphql_client/store.py:1968-1999`

### Changed

- Added 8 tests verifying string list fields use single-string values while relationship fields still use lists
  - Location: `tests/store/test_string_list_filters.py`

## [0.10.5] - 2026-01-09

### Fixed

- **List Dirty Tracking**: Fixed critical bug where in-place list modifications weren't detected as dirty
  - Snapshot system now creates shallow copies of lists instead of storing references
  - In-place operations like `append()`, `remove()`, `extend()`, `pop()`, `clear()`, and item assignment now correctly mark objects as dirty
  - Affects all tracked list fields: `urls`, `aliases`, `alias_list`, `stash_ids`, and relationship lists
  - Added `_snapshot_value()` helper method to handle mutable collection copying
  - Location: `stash_graphql_client/types/base.py:994-1011,1027,1076`

### Changed

- **Dirty Tracking Tests**: Added comprehensive test suite for dirty tracking functionality
  - 28 tests covering list operations, basic dirty tracking, relationship lists, and edge cases
  - Tests verify all list modification methods are detected (append, extend, remove, pop, clear, item assignment)
  - Tests cover multiple entity types (Performer, Studio, Tag, Scene) and relationship lists
  - Location: `tests/types/test_dirty_tracking.py`

- **Version Integration Tests**: Mocked external GitHub API calls to prevent rate limiting failures
  - `test_latestversion_returns_github_version` now fully mocked with respx
  - `test_version_and_latestversion_compatibility` uses hybrid approach (real Stash version, mocked GitHub response)
  - Tests no longer make external API calls, improving reliability and speed
  - Location: `tests/integration/test_version_integration.py`

## [0.10.4] - 2026-01-08

### Fixed

- **Relationship Metadata**: Corrected invalid `inverse_query_field` declarations that caused AttributeError in helper methods
  - `Image.performers`: Removed `inverse_query_field="images"` (Performer only has `image_count` resolver)
  - `Image.galleries`: Removed `inverse_query_field="images"` (Gallery has `image_count` and `image(index)` method, not list)
  - `Gallery.performers`: Removed `inverse_query_field="galleries"` (Performer only has `gallery_count` resolver)
  - `Group.tags`: Removed `inverse_query_field="groups"` (Tag only has `group_count` resolver)
  - Helper methods like `add_performer()` and `add_tag()` no longer attempt to sync non-existent inverse fields
  - Location: `stash_graphql_client/types/image.py:139,156`, `gallery.py:339`, `group.py:181`

### Changed

- Updated relationship metadata tests to expect `None` for invalid inverse fields
- Removed flawed `test_populate_list_multiple_nested_specs` with incorrect caching expectations
- Removed forbidden operations from integration tests:
  - Deleted `test_metadata_identify_*` tests (can trigger external StashDB API calls)
  - Deleted `test_metadata_export_starts_job` test (writes to metadata directory)
  - Updated documentation to clarify forbidden vs safe operations
  - Location: `tests/integration/test_metadata_integration.py`

## [0.10.3] - 2026-01-07

### Fixed

- Fixed `fingerprints` field selection in entity store - now properly includes subfields `{ __typename type value }` (resolves GraphQL validation error when filtering with `files` field)

## [0.10.2] - 2026-01-07

### Fixed

- **Polymorphic Type Fetching**: ImageFile and VideoFile now correctly fetched via BaseFile's `findFile` query
  - Added `_get_concrete_type()`: Resolves polymorphic types based on `__typename` field in GraphQL responses
  - Added `_get_query_name()`: Maps type names to correct GraphQL query names (e.g., BaseFile → findFile)
  - Enhanced `_get_fetchable_type()`: Improved error handling for edge cases (non-class types, missing attributes)
  - Fixed issue where `sanitize_model_data()` was removing `__typename` before polymorphic type resolution
  - Location: `stash_graphql_client/store.py:820-931, 1758-1780`

### Changed

- **Nested Field Filtering**: Enhanced to support polymorphic types in nested relationships
  - `populate()` now correctly handles ImageFile/VideoFile in Image.files and Image.visual_files
  - Nested field specs like `'files__path'` and `'visual_files__size'` work correctly with mixed file types
  - Location: `stash_graphql_client/store.py:1103-1104, 1164-1183`
- **Coverage**: Returned project to 100% test pass / 100% code coverage

## [0.10.1] - 2026-01-07

### Added

- **Nested Field Filtering**: Django-style double-underscore syntax for filtering on related object properties
  - Syntax: `'files__path'`, `'studio__parent__name'`, `'studio__parent__parent__name'` (arbitrary depth)
  - Supported by all advanced filter methods: `filter_strict()`, `filter_and_populate()`, `filter_and_populate_with_stats()`, `populated_filter_iter()`
  - New helper methods:
    - `_parse_nested_field()`: Parses `'files__path'` → `['files', 'path']`
    - `_check_nested_field_present()`: Recursively checks if nested path is populated
    - `missing_fields_nested()`: Returns set of missing nested field specifications
  - Enhanced `populate()` to recursively load nested field paths
  - Example: `await store.filter_and_populate(Image, required_fields=['files__path', 'files__size'], predicate=lambda i: any(f.size > 10_000_000 for f in i.files))`
  - Location: `stash_graphql_client/store.py:806-872, 940-1066`

### Changed

- Added "Nested Field Filtering" section to Advanced Filtering guide
  - Comprehensive examples with Images, Scenes, Studios, Performers
  - Explains how nested field resolution works (parse → check root → recurse → auto-populate)
  - Performance tips for optimal nested field usage
  - Location: `docs/guide/advanced-filtering.md:428-571`
- Added 22 comprehensive tests for nested field functionality
  - Tests for `_parse_nested_field()`, `_check_nested_field_present()`, `missing_fields_nested()`
  - Tests for all filter methods with nested field specs
  - Edge cases: empty lists, three-level nesting, mixed regular/nested specs
  - Location: `tests/store/test_nested_filters.py`

## [0.10.0] - 2026-01-06

### Added

- **Advanced Filter Methods**: Four new field-aware repository methods for smart caching
  - `filter_strict()`: Fail-fast filtering, raises if required fields missing (sync)
  - `filter_and_populate()`: Auto-fetches missing fields, 10x faster than `find()` on partial cache
  - `filter_and_populate_with_stats()`: Returns `(results, stats)` for performance debugging
  - `populated_filter_iter()`: Lazy async iterator for large datasets with early exit support
  - All leverage UNSET pattern + field tracking for surgical fetching
  - Location: `stash_graphql_client/store.py:385-721`

### Changed

- Added "Advanced Filtering" guide (`docs/guide/advanced-filtering.md`) with performance examples
- **Coverage**: 99.99% overall
- Added 27 tests for new filter methods using spy pattern for race conditions

## [0.9.0] - 2026-01-06

### Added

- **Performer Merge Feature**: Added `performer_merge()` method for merging multiple performers into one
  - Requires Stash v0.30.2+ (or development builds with commit `65e82a0+`)
  - Merges source performers into destination performer (source performers are deleted)
  - Optional `values` parameter to override destination performer fields during merge
  - Helpful error messages for older Stash versions that don't support the mutation
  - Added `PerformerMergeInput` type for type-safe merge operations
  - Added `PERFORMER_MERGE_MUTATION` GraphQL fragment
  - Comprehensive test coverage with 5 tests (basic merge, dict input, value overrides, error handling, version check)
  - Location: `stash_graphql_client/client/mixins/performer.py:585-654`
  - Schema: Updated from upstream Stash commit `65e82a0`

## [0.8.2] - 2026-01-06

### Fixed

- **Connection Configuration**: Fixed case-sensitivity bug in connection configuration handling
  - Lowercase connection keys (`scheme`, `host`, `port`, `apikey`) now work correctly
  - Previously, converting `CIMultiDict` to regular `dict` lost case-insensitivity
  - Bug caused clients with lowercase config keys to fall back to default `localhost:9999`
  - Users parsing config files with lowercase keys (common pattern) were silently connecting to wrong server
  - Added regression test `test_lowercase_keys_work_with_client_initialization()`
  - Location: `stash_graphql_client/context.py:105-108`

## [0.8.1] - 2026-01-06

### Fixed

- **GraphQL Filter Translation**: Fixed `'cannot use slice as String'` error when using `path__contains` and other string field filters
  - INCLUDES modifier now correctly distinguishes between string fields (single value) and multi-value fields (list of IDs)
  - String fields (`path`, `title`, `details`, etc.) with `__contains` now send single string value instead of wrapping in list
  - Multi-value fields (`tags`, `performers`, `studios`, etc.) continue to work correctly with list values
  - Affects all Django-style filter operations: `find()`, `find_iter()`, and filter translation
  - Location: `stash_graphql_client/store.py:1193-1237`

- **GraphQL Error Handling**: Fixed `KeyError: "'message'"` when GraphQL returns malformed error responses
  - Added safe error extraction in `_handle_gql_error()` to catch KeyError during error stringification
  - Now provides informative fallback error message when error structure is unexpected
  - Added debug logging to capture raw error structure for troubleshooting
  - Affects all GraphQL query operations via `store.find()`, `store.find_iter()`, and direct client calls
  - Location: `stash_graphql_client/client/base.py:326-342`

### Changed

- **Comprehensive Documentation Overhaul**: Restructured documentation into three-tier system
  - **README.md**: Streamlined to concise landing page with quick examples
  - **User Guides**: New comprehensive guides for developers and LLM agents
    - Getting Started guide with installation, configuration, and first scripts
    - Usage Patterns guide with 8 structured patterns and best practices
    - Overview guide explaining architecture, design philosophy, and core concepts
  - **Architecture Documentation**: Deep technical documentation
    - Identity Map implementation deep-dive (Pydantic v2 wrap validators)
    - Library comparisons (vs raw gql, Apollo Client, SQLAlchemy, Django ORM)
    - Architecture overview with layer descriptions and usage guidelines
  - **Visual Diagrams**: Added Mermaid diagrams for architecture visualization
    - Three-layer architecture diagram
    - Identity map flow (wrap validator pattern)
    - UNSET pattern state diagram
    - Nested cache lookup process
    - Relationship sync flow
    - Field-aware population
    - Django-style filter translation
  - **MkDocs Configuration**: Fixed Mermaid rendering with custom_fences configuration

## [0.8.0] - 2026-01-04

### Added

- **StashContext API Enhancement**: Added public `.store` property for accessing StashEntityStore
  - Matches existing `.client` property pattern with initialization checks
  - Provides clean access to singleton store instance instead of private `._store`
  - Updated documentation to show correct usage: `store = context.store`
  - Eliminates need to create separate `StashEntityStore(client)` instances (which breaks identity map)
  - Location: `stash_graphql_client/context.py:141-157`

### Fixed

- **Testing**: Fixed `mock_entity_store` fixture to properly support async methods
  - Changed from `MagicMock` to `AsyncMock` for mocking `populate()` method
  - Resolves `TypeError: object MagicMock can't be used in 'await' expression` in helper method tests
  - Affects all test files using `@pytest.mark.usefixtures("mock_entity_store")`
  - Location: `tests/fixtures/client.py:320`

### Changed

- **Coverage**: Achieved 100% coverage on `stash_graphql_client/__init__.py` (previously 81.82%)
  - Added `test_version_fallback_on_package_not_found()` to test PackageNotFoundError handler
  - Tests version fallback to "0.0.0.dev0" when package not installed
  - Added 8 additional tests for public API exports and version validation
  - New test file: `tests/test_init.py`

## [0.7.2] - 2026-01-01

### Fixed

- **Critical Bug**: Fixed `ValueError: ssl argument is incompatible with a ws:// URI` when connecting to HTTP-configured Stash servers
  - WebSocket transport now conditionally passes SSL parameter based on URL scheme
  - HTTP (`ws://`) connections: SSL parameter is NOT passed (per websockets library requirements)
  - HTTPS (`wss://`) connections: SSL parameter is passed for certificate validation
  - Affects Docker/Kubernetes deployments with reverse proxy SSL termination, development environments, and internal service-to-service communication
  - Location: `stash_graphql_client/client/base.py:169-185`

### Changed

- **Version Management**: Implemented automatic version synchronization with poetry-dynamic-versioning
  - `__version__` now dynamically loads from package metadata via `importlib.metadata`
  - Single source of truth: only `pyproject.toml` needs updating (`poetry version patch`)
  - Eliminates manual version sync between `pyproject.toml` and `__init__.py`
  - Build system integration ensures consistency across development and PyPI releases
- **WebSocket SSL Tests**: Added 4 comprehensive test cases for WebSocket connection handling
  - HTTP (`ws://`) connections without SSL parameter
  - HTTPS (`wss://`) connections with SSL parameter
  - HTTPS with `verify_ssl=False` (self-signed certificates)
  - Scheme attribute storage during initialization
- **Coverage Gaps**: Added 8 targeted tests for previously uncovered code paths

### Added

- **Thread-Safety**: StashEntityStore now supports concurrent access from multi-threaded applications
  - Uses reentrant lock (RLock) for all cache operations
  - Lock-free async patterns prevent event loop blocking
  - Snapshot-based predicate evaluation for safe concurrent access
  - Full thread-safety test coverage with ThreadPoolExecutor
- **SceneMarker Helpers**: Added missing convenience methods for tag management
  - `add_tag()`: Add tag to marker with automatic deduplication
  - `remove_tag()`: Remove tag from marker (no-op if not present)
  - UNSET-aware initialization (converts UNSET to empty list)
  - Consistent with Scene and Tag helper method patterns
  - scraper.py: `scrape_single_tag()` error handling (empty results, exceptions)
  - scalars.py: `_serialize_time()` success and error paths
  - base.py: `save()` create vs update branches, `_process_fields()` skip logic
  - Returns to 100% test coverage (1720 tests passing)

- **Type Compliance**: Returns to 100% mypy compliance (164 source files checked)

## [0.7.1] - 2025-12-31

### Fixed

- **Critical Bug**: Fixed `ValueError: Circular reference detected` in dirty checking when saving objects with bidirectional relationships
  - `is_dirty()`, `get_changed_fields()`, and `mark_clean()` now use direct field comparison instead of `model_dump()` serialization
  - Prevents circular reference errors when Scene.performers ↔ Performer.scenes or similar relationships exist
  - `save()` now works correctly on existing objects with relationships (previously failed with ValueError)
  - No performance impact - direct field access is faster than serialization

## [0.7.0] - 2025-12-31

### Changed

- **BREAKING**: `find_scenes_by_path_regex()` now returns `FindScenesResultType` instead of `list[Scene]`
  - Provides consistent API with other find methods (`find_scenes()`, `find_performers()`, etc.)
  - Exposes result metadata: `count`, `duration`, `filesize`
  - Uses `result_type` parameter for automatic type-safe deserialization
  - **Migration**: Change `scenes = await client.find_scenes_by_path_regex(filter_)` to `result = await client.find_scenes_by_path_regex(filter_)` and access scenes via `result.scenes`

### Fixed

- **Critical Bug**: `find_scenes_by_path_regex()` was incorrectly iterating over result wrapper dict instead of nested scenes list
  - Previously returned empty list on all calls (silent failure)
  - Now correctly extracts and returns scenes from GraphQL response
  - Affects downstream projects relying on this method (e.g., fansly-downloader-ng)

## [0.6.0] - 2025-12-30

### Added

- **Complete Type Safety**: Achieved 0 mypy errors across entire codebase (163 source files)
  - Full type annotations for all test files (102 test modules)
  - Strict type checking with no suppressions or ignores (except intentional test cases)
  - Enhanced type narrowing with `is_set()` TypeGuard throughout codebase

### Changed

- **UNSET Type Narrowing**: Comprehensive use of `is_set()` guards in helper methods
  - All `map_*_ids()` helper methods now properly narrow UNSET types before operations
  - Studio, Tag, Performer, Gallery, Image, and Group mixins updated with type guards
  - Prevents runtime errors when accessing potentially UNSET fields
  - Improved type inference for IDEs (Pylance, mypy)

- **GraphQL Input Type Naming**: Fixed parameter naming consistency
  - INPUT types now consistently use camelCase (matching GraphQL schema)
  - OUTPUT types continue using snake_case with Pydantic aliases
  - Examples: `backupPath`, `deleteFiles`, `deleteOld` instead of snake_case variants

- **Protocol Enhancements**: Added missing attributes to AsyncCachedFunction Protocol
  - Added `__name__` and `__doc__` attributes to match functools.wraps behavior
  - Enables proper type checking for decorated async functions
- **Improved Test Coverage**: Achieved 100% branch coverage on critical mixins
  - Studio mixin: 100.00% coverage (118 statements, 38 branches)
  - Tag mixin: 100.00% coverage (129 statements, 46 branches)
  - Performer mixin: 100.00% coverage (174 statements, 72 branches)
  - Added 9 new tests for UNSET field handling edge cases
  - All 1686 tests passing with enhanced type safety
- **Test Pattern Improvements**: Consistent use of type narrowing in test assertions
  - Added `is_set()` guards before list operations (len, indexing, iteration)
  - Added `is not None` checks before attribute access
  - Two-stage narrowing for `T | UnsetType | None` types
- **Code Quality**: Enhanced maintainability and type safety
  - Zero mypy errors across entire project
  - Consistent type narrowing patterns throughout
  - Better error messages with type guards
  - Improved IDE support and autocomplete

### Fixed

- **Type Annotation Errors**: Resolved 700+ mypy errors across codebase
  - Fixed UnsetType narrowing in 78+ integration tests
  - Corrected None checks in client mixins
  - Added proper type annotations for test variables
  - Fixed lambda return types in entity store filters

- **Test Type Safety**: Enhanced test suite with proper type handling
  - Added `type: ignore[arg-type]` for intentional ValidationError tests
  - Fixed argument order in method calls (client-first pattern)
  - Resolved @classmethod + TypeVar mypy limitations with explanatory comments

- **Coverage Gaps**: Added tests for edge cases in helper methods
  - 100% branch coverage on Studio, Tag, and Performer mixins
  - Tests for NEW objects with UNSET name fields
  - Tests for UNSET performers in search results
  - 9 new edge-case tests covering falsy path branches

## [0.5.1] - 2025-12-29

### Added

- **Type Stubs Support**: Added `py.typed` marker file for mypy compatibility
  - Enables type checkers to recognize inline type annotations
  - Eliminates "missing library stubs" warnings in mypy
  - No code changes - purely packaging improvement for better IDE/mypy integration

### Changed

- Updated dependencies via `poetry update` for security patches

## [0.5.0] - 2025-12-26

### Added

- **Pydantic v2 with wrap validators**: All entity types extend `StashObject` with
  `@model_validator(mode='wrap')` for identity map integration
  (see [architecture/pydantic-internals](docs/architecture/pydantic-internals.md))
- **Identity map caching** via [`StashEntityStore`](docs/api/store.md): Same entity ID returns same
  object reference across all queries; nested cache lookups automatically share references
  (see [architecture/identity-map](docs/architecture/identity-map.md))
- **[UNSET pattern](docs/guide/unset-pattern.md)**: Three-state field system distinguishing unqueried
  fields (UNSET), null values (None), and actual values
- **[Dirty tracking](docs/architecture/dirty-tracking.md)**: Snapshot-based change detection for
  surgical saves
- **`__typename` discrimination**: All GraphQL fragments include `__typename`; `FromGraphQLMixin`
  validates response types and dispatches to correct subclasses for polymorphic types
- **Convenience Helper Methods**: 15 synchronous relationship helper methods across 5 entity types
  - **Performer** (2 methods): `add_tag()`, `remove_tag()`
  - **Gallery** (4 methods): `add_performer()`, `remove_performer()`, `add_scene()`, `remove_scene()`
  - **Image** (4 methods): `add_performer()`, `remove_performer()`, `add_gallery()`, `remove_gallery()`
  - **Studio** (3 methods): `set_parent_studio()`, `add_child_studio()`, `remove_child_studio()` with bidirectional sync
  - **Group** (2 methods): `add_sub_group()`, `remove_sub_group()` with GroupDescription wrapper support
- **Type Narrowing Support**: `is_set()` TypeGuard function for improved type safety
  - Uses PEP 695 syntax (`def is_set[T](value: T | UnsetType) -> TypeGuard[T]`)
  - Exported from `stash_graphql_client.types` for public use
- **PyPI publishing** via GitHub Actions with Trusted Publishers (OIDC)
- Complete type coverage for Stash GraphQL schema; Python 3.12+

### Changed

- Changed license from MIT to AGPL-3.0-or-later to match Stash upstream
- TTL-based entity caching with thread-safe RLock
- Factory-based test fixtures with Faker integration; respx for GraphQL HTTP mocking
- 70%+ test coverage requirement

[Unreleased]: https://github.com/Jakan-Kink/stash-graphql-client/compare/v0.12.0...HEAD
[0.12.0]: https://github.com/Jakan-Kink/stash-graphql-client/compare/v0.11.2...v0.12.0
[0.11.2]: https://github.com/Jakan-Kink/stash-graphql-client/compare/v0.11.1...v0.11.2
[0.11.1]: https://github.com/Jakan-Kink/stash-graphql-client/compare/v0.11.0...v0.11.1
[0.11.0]: https://github.com/Jakan-Kink/stash-graphql-client/compare/v0.10.14...v0.11.0
[0.10.14]: https://github.com/Jakan-Kink/stash-graphql-client/compare/v0.10.13...v0.10.14
[0.10.13]: https://github.com/Jakan-Kink/stash-graphql-client/compare/v0.10.12...v0.10.13
[0.10.12]: https://github.com/Jakan-Kink/stash-graphql-client/compare/v0.10.10...v0.10.12
[0.10.10]: https://github.com/Jakan-Kink/stash-graphql-client/compare/v0.10.9...v0.10.10
[0.10.9]: https://github.com/Jakan-Kink/stash-graphql-client/compare/v0.10.8...v0.10.9
[0.10.8]: https://github.com/Jakan-Kink/stash-graphql-client/compare/v0.10.7...v0.10.8
[0.10.7]: https://github.com/Jakan-Kink/stash-graphql-client/compare/v0.10.6...v0.10.7
[0.10.6]: https://github.com/Jakan-Kink/stash-graphql-client/compare/v0.10.5...v0.10.6
[0.10.5]: https://github.com/Jakan-Kink/stash-graphql-client/compare/v0.10.4...v0.10.5
[0.10.4]: https://github.com/Jakan-Kink/stash-graphql-client/compare/v0.10.3...v0.10.4
[0.10.3]: https://github.com/Jakan-Kink/stash-graphql-client/compare/v0.10.2...v0.10.3
[0.10.2]: https://github.com/Jakan-Kink/stash-graphql-client/compare/v0.10.1...v0.10.2
[0.10.1]: https://github.com/Jakan-Kink/stash-graphql-client/compare/v0.10.0...v0.10.1
[0.10.0]: https://github.com/Jakan-Kink/stash-graphql-client/compare/v0.9.0...v0.10.0
[0.9.0]: https://github.com/Jakan-Kink/stash-graphql-client/compare/v0.8.2...v0.9.0
[0.8.2]: https://github.com/Jakan-Kink/stash-graphql-client/compare/v0.8.1...v0.8.2
[0.8.1]: https://github.com/Jakan-Kink/stash-graphql-client/compare/v0.8.0...v0.8.1
[0.8.0]: https://github.com/Jakan-Kink/stash-graphql-client/compare/v0.7.2...v0.8.0
[0.7.2]: https://github.com/Jakan-Kink/stash-graphql-client/compare/v0.7.1...v0.7.2
[0.7.1]: https://github.com/Jakan-Kink/stash-graphql-client/compare/v0.7.0...v0.7.1
[0.7.0]: https://github.com/Jakan-Kink/stash-graphql-client/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/Jakan-Kink/stash-graphql-client/compare/v0.5.1...v0.6.0
[0.5.1]: https://github.com/Jakan-Kink/stash-graphql-client/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/Jakan-Kink/stash-graphql-client/releases/tag/v0.5.0
