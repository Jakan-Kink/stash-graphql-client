# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
