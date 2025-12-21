# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/Jakan-Kink/stash-graphql-client/compare/v0.5.0b4...HEAD
[0.5.0b4]: https://github.com/Jakan-Kink/stash-graphql-client/compare/v0.5.0b3...v0.5.0b4
[0.5.0b3]: https://github.com/Jakan-Kink/stash-graphql-client/compare/v0.5.0b2...v0.5.0b3
[0.5.0b2]: https://github.com/Jakan-Kink/stash-graphql-client/compare/v0.5.0b1...v0.5.0b2
[0.5.0b1]: https://github.com/Jakan-Kink/stash-graphql-client/releases/tag/v0.5.0b1
