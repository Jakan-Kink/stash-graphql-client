# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/Jakan-Kink/stash-graphql-client/compare/v0.5.0b7...HEAD
[0.5.0b7]: https://github.com/Jakan-Kink/stash-graphql-client/compare/v0.5.0b5...v0.5.0b7
[0.5.0b5]: https://github.com/Jakan-Kink/stash-graphql-client/compare/v0.5.0b4...v0.5.0b5
[0.5.0b4]: https://github.com/Jakan-Kink/stash-graphql-client/compare/v0.5.0b3...v0.5.0b4
[0.5.0b3]: https://github.com/Jakan-Kink/stash-graphql-client/compare/v0.5.0b2...v0.5.0b3
[0.5.0b2]: https://github.com/Jakan-Kink/stash-graphql-client/compare/v0.5.0b1...v0.5.0b2
[0.5.0b1]: https://github.com/Jakan-Kink/stash-graphql-client/releases/tag/v0.5.0b1
