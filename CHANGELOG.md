# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.10.4] - 2026-01-08

### Fixed

- **Relationship Metadata**: Corrected invalid `inverse_query_field` declarations that caused AttributeError in helper methods
  - `Image.performers`: Removed `inverse_query_field="images"` (Performer only has `image_count` resolver)
  - `Image.galleries`: Removed `inverse_query_field="images"` (Gallery has `image_count` and `image(index)` method, not list)
  - `Gallery.performers`: Removed `inverse_query_field="galleries"` (Performer only has `gallery_count` resolver)
  - `Group.tags`: Removed `inverse_query_field="groups"` (Tag only has `group_count` resolver)
  - Helper methods like `add_performer()` and `add_tag()` no longer attempt to sync non-existent inverse fields
  - Location: `stash_graphql_client/types/image.py:139,156`, `gallery.py:339`, `group.py:181`

### Testing

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

### Testing

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

### Documentation

- Added "Nested Field Filtering" section to Advanced Filtering guide
  - Comprehensive examples with Images, Scenes, Studios, Performers
  - Explains how nested field resolution works (parse → check root → recurse → auto-populate)
  - Performance tips for optimal nested field usage
  - Location: `docs/guide/advanced-filtering.md:428-571`

### Testing

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

### Documentation

- Added "Advanced Filtering" guide (`docs/guide/advanced-filtering.md`) with performance examples

### Testing

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

### Documentation

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

### Testing

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

### Testing

- **WebSocket SSL Tests**: Added 4 comprehensive test cases for WebSocket connection handling

  - HTTP (`ws://`) connections without SSL parameter
  - HTTPS (`wss://`) connections with SSL parameter
  - HTTPS with `verify_ssl=False` (self-signed certificates)
  - Scheme attribute storage during initialization

- **Coverage Gaps**: Added 8 targeted tests for previously uncovered code paths

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

### Testing

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

### Internal

- **Code Quality**: Enhanced maintainability and type safety
  - Zero mypy errors across entire project
  - Consistent type narrowing patterns throughout
  - Better error messages with type guards
  - Improved IDE support and autocomplete

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

- **Convenience Helper Methods**: 15 synchronous relationship helper methods across 5 entity types

  - **Performer** (2 methods): `add_tag()`, `remove_tag()`
  - **Gallery** (4 methods): `add_performer()`, `remove_performer()`, `add_scene()`, `remove_scene()`
  - **Image** (4 methods): `add_performer()`, `remove_performer()`, `add_gallery()`, `remove_gallery()`
  - **Studio** (3 methods): `set_parent_studio()`, `add_child_studio()`, `remove_child_studio()` with bidirectional sync
  - **Group** (2 methods): `add_sub_group()`, `remove_sub_group()` with GroupDescription wrapper support
  - All helpers are in-memory operations with UNSET-aware initialization and ID-based deduplication
  - Follows established patterns from Scene and Tag types

- **Type Narrowing Support**: `is_set()` TypeGuard function for improved type safety
  - Uses PEP 695 syntax (`def is_set[T](value: T | UnsetType) -> TypeGuard[T]`)
  - Enables type checkers (Pylance, mypy) to narrow UNSET types in conditional checks
  - Improves IDE autocomplete and type inference for field access after UNSET validation
  - Exported from `stash_graphql_client.types` for public use

### Changed

- Enhanced type exports in `stash_graphql_client.types.__init__.py` to include `is_set` function

### Testing

- Added 6 new comprehensive test files with 55 tests total:
  - `tests/types/test_performer_helpers.py` (7 tests)
  - `tests/types/test_gallery_helpers.py` (13 tests)
  - `tests/types/test_image_helpers.py` (13 tests)
  - `tests/types/test_studio_helpers.py` (11 tests)
  - `tests/types/test_group_helpers.py` (11 tests)
  - `tests/types/test_unset.py` (11 tests including TypeGuard validation)
- Maintained 100% test coverage (1700 tests passing, 6664/6664 statements, 1154/1154 branches)

### Documentation

- Fixed API signature errors in `docs/index.md` and `docs/guide/fuzzy-dates.md`
- Corrected examples to use object-based parameters instead of kwargs
- Reorganized documentation structure with enhanced reference materials

### Notes

- First stable release (0.5.0) after 7 beta iterations
- Type narrowing refactoring for remaining codebase deferred to v0.6.0
  - Would address 160 UNSET checks across codebase
  - Would fix 110/170 mypy errors (65% reduction)
  - Comprehensive migration plan documented in project

## [0.5.0b7] - 2025-12-22

### Changed

- **Integration Test Coverage**: Added comprehensive GraphQL call assertions to all 43 existing integration tests
  - Tests now verify both request structure (query content, variables) and response handling (result, exception)
  - Updated 9 integration test files: base, config, marker, performer, studio, tag, client, file
  - Fixed test assertions to match actual client behavior:
    - `find_job`: Corrected variable path to `input.id` wrapper structure
    - `find_marker`: Updated to reflect v0.5.0b7 fix (now uses `findSceneMarkers` plural with `ids` filter)
    - Query parameter tests: Fixed to expect `filter.q` nested structure
  - All tests follow TESTING_REQUIREMENTS.md pattern: verify call count, query operation, variables, result, and exception
  - Tests catch GraphQL schema issues early (e.g., invalid operation names, incorrect variable structures)

### Removed

- **CRITICAL - Destructive Integration Tests Removed**: Removed 14 dangerous integration tests that ran destructive operations against real Stash instances
  - **Removed operations**:
    - Metadata: `metadata_import`, `anonymise_database`, `migrate`, `migrate_hash_naming`, `migrate_scene_screenshots`, `migrate_blobs`, `optimise_database`, `setup` (11 tests)
    - Configuration: `configure_general`, `configure_interface`, `configure_defaults` (3 tests)
  - **Why removed**: These operations call GraphQL MUTATIONS that modify Stash settings, databases, and files
    - Metadata operations: Anonymize databases, delete files, migrate schemas, reconfigure Stash instances
    - Configuration operations: Modify settings (even with empty `{}` dicts - relies on undocumented API behavior)
  - **Test instance impact**: A test Docker instance had its database path reconfigured and data deleted by `test_setup_with_config`
  - **Lesson learned**: Integration tests must ONLY test safe, reversible operations (queries, exports, backups with dryRun=True). Never rely on undocumented API behavior for "safe" mutations.
  - **Coverage maintained**: These operations are fully tested via unit tests with mocked GraphQL responses
    - Metadata operations: `tests/client/test_metadata_client.py`
    - Configuration operations: `tests/client/test_config_client.py`
  - **Files affected**:
    - `tests/integration/test_metadata_integration.py` - reduced from 24 tests to 13 safe tests
    - `tests/integration/test_config_integration.py` - reduced from 4 tests to 1 safe test
  - **Safe operations kept**:
    - Metadata: Queries, exports, backups, auto-tagging, metadata identification, clean with dryRun=True
    - Configuration: Read-only configuration defaults query only

## [0.5.0b5] - 2025-12-21

### Changed

- **PEP 8 Compliance**: Moved all function-level imports to module level across 13 production files (24 violations fixed)
  - Refactored `types/tag.py`, `types/performer.py`, `types/unset.py`, `types/base.py`, `types/scene.py`
  - Refactored `client/mixins/metadata.py`, `client/mixins/scene.py`, `client/__init__.py`, `client/base.py`
  - Refactored `store.py`, `context.py`
  - Removed outdated "circular import" workarounds - testing confirmed no circular dependencies exist
  - Removed redundant inline imports where types were already imported at module level

### Technical Details

- All imports verified for circular dependencies with no issues found
- `fragments.py` contains only string constants, safe to import anywhere
- All 1547 tests pass with 100% coverage maintained
- Code quality checks passing (ruff, formatting)

## [0.5.0b4] - 2025-12-21

### Added

- `__typename` field to all GraphQL fragments and queries for improved type safety
- Type validation in `FromGraphQLMixin.from_graphql()` to verify GraphQL response types match Python classes
- Polymorphic type support via `cls.__subclasses__()` check for interface/union types
- Test coverage for type mismatch validation error paths

### Fixed

- pytest-xdist worker state sharing bug that caused integration tests to skip in parallel mode
- Added `pytest_configure_node()` hook to properly share Stash availability state between controller and workers

### Changed

- All 16 fragment definitions now include `__typename` as first field
- All nested inline objects in fragments include `__typename`
- Dynamic query generation in `StashEntityStore.populate()` includes `__typename`
- All test fixtures (12 `create_*_dict()` functions and 10 Factory classes) include `__typename`

## [0.5.0b3] - 2025-12-21

### Fixed

- Updated README.md license section from MIT to AGPL-3.0 (badge was correct, text section was outdated)
- Regenerated poetry.lock after removing keyrings-codeartifact (-425 lines of AWS dependencies)

### Changed

- Cleaned up transitive dependencies from poetry.lock after PyPI migration

## [0.5.0b2] - 2025-12-21

### Added

- PyPI publishing support via GitHub Actions with Trusted Publishers (OIDC)
- Automated publishing to TestPyPI on every push to `main`
- Automated publishing to PyPI on version tags
- Comprehensive PyPI metadata (classifiers, keywords, project URLs)
- CHANGELOG.md for tracking version history
- PyPI badges in README (version, Python version, license, codecov)

### Changed

- Migrated from AWS CodeArtifact to PyPI for package distribution
- Changed license from MIT to AGPL-3.0-or-later to match Stash upstream
- Updated README installation instructions to prioritize PyPI
- Enhanced CONTRIBUTING.md with release process documentation

### Removed

- AWS CodeArtifact repository source configuration
- `keyrings-codeartifact` development dependency

## [0.5.0b1] - 2024-12-15

### Added

- Full Pydantic v2 support with wrap validators
- Identity map caching via `StashEntityStore`
- UNSET pattern for distinguishing unqueried fields from null values
- Nested cache lookups for automatic object reference sharing
- Dirty tracking with snapshot-based change detection
- Comprehensive test suite with HTTP-only mocking
- Complete type coverage for Stash GraphQL schema
- Support for Python 3.12+

### Technical Details

- All entity types extend `StashObject` with `@model_validator(mode='wrap')`
- Three-state field system: UNSET (not queried), None (null), or actual value
- TTL-based entity caching with thread-safe RLock
- Factory-based test fixtures with Faker integration
- respx for GraphQL HTTP mocking
- 70%+ test coverage requirement

[Unreleased]: https://github.com/Jakan-Kink/stash-graphql-client/compare/v0.6.0...HEAD
[0.6.0]: https://github.com/Jakan-Kink/stash-graphql-client/compare/v0.5.1...v0.6.0
[0.5.1]: https://github.com/Jakan-Kink/stash-graphql-client/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/Jakan-Kink/stash-graphql-client/compare/v0.5.0b7...v0.5.0
[0.5.0b7]: https://github.com/Jakan-Kink/stash-graphql-client/compare/v0.5.0b5...v0.5.0b7
[0.5.0b5]: https://github.com/Jakan-Kink/stash-graphql-client/compare/v0.5.0b4...v0.5.0b5
[0.5.0b4]: https://github.com/Jakan-Kink/stash-graphql-client/compare/v0.5.0b3...v0.5.0b4
[0.5.0b3]: https://github.com/Jakan-Kink/stash-graphql-client/compare/v0.5.0b2...v0.5.0b3
[0.5.0b2]: https://github.com/Jakan-Kink/stash-graphql-client/compare/v0.5.0b1...v0.5.0b2
[0.5.0b1]: https://github.com/Jakan-Kink/stash-graphql-client/releases/tag/v0.5.0b1
