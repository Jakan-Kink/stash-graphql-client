# Design History

This document captures the original motivations, architectural decisions, and trade-offs that shaped stash-graphql-client. It is adapted from the founding design document (late 2025, between Thanksgiving and Christmas).

## The Problem: Code Duplication

Four downstream projects contained nearly identical Stash integration code:

| Project | Stash Code | Lines | Types Framework |
|---|---|---|---|
| fansly-downloader-ng | `stash/` | ~14,500 | Strawberry |
| missF-downloader | `stash/` | ~17,800 | Strawberry |
| pyLoyalFans | `pyloyalfans/stash/` | ~10,700 | Pydantic |
| pyofscraperstash | `pyofscraperstash/stash/` | ~12,000 | Strawberry |

Across these projects, **95%+ of the Stash client code was identical**: the GraphQL transport layer, client mixins, query fragments, and type definitions. Only the *processing* logic (mapping platform entities to Stash entities) was project-specific.

Schema updates required identical changes in four places. Bug fixes had to be manually propagated. The Strawberry-to-Pydantic migration multiplied this cost further.

## Key Architectural Decisions

### Async-first with gql + HTTPX

**Decision**: Use `gql` with `HTTPXAsyncTransport` and `WebsocketsTransport`.

**Why**: All downstream consumers are async Python applications. A sync-first library would require wrapping in `asyncio.run()` or similar, adding complexity for no benefit. HTTPX provides HTTP/2 support and connection pooling out of the box.

### Pydantic v2 over Strawberry

**Decision**: Use Pydantic v2 BaseModel for all types, not Strawberry.

**Why**: Strawberry is designed for *building* GraphQL servers, not consuming them. Its `@strawberry.type` decorator adds unnecessary overhead when we only need deserialization and validation. Pydantic v2's `model_validator(mode='wrap')` turned out to be the key enabler for the identity map pattern — it allows intercepting object construction before Pydantic processes data, returning cached instances when available.

pyLoyalFans had already completed the Strawberry-to-Pydantic migration, making it the natural extraction source.

### Rejecting stashapp-tools / stashapi

**Decision**: Build a custom client rather than use the existing `stashapp-tools` package.

**Why**:

- `stashapp-tools` is **sync-first** — incompatible with our async architecture
- It is **opinionated** about how you interact with Stash, making it difficult to layer our own patterns (identity map, dirty tracking, UNSET fields) on top
- No Pydantic integration — returns raw dicts
- We needed full control over the type system for the identity map and entity store patterns

### Schema sync via git read-tree

**Decision**: Vendor the upstream GraphQL schema from `stashapp/stash` using `git read-tree`.

**Why**: This gives us a reproducible, version-tracked way to update the schema. The schema files live at `stash_graphql_client/schema/` and are synced from the upstream repository's `graphql/schema` directory. Consumer projects simply bump their library version to get schema updates.

### What stays in downstream projects

**Decision**: Processing logic (mapping platform entities to Stash entities) stays local to each project.

**Why**: Processing modules reference platform-specific database models (`Account`, `Media`, `Post`) and contain business logic for how that platform's data maps to Stash entities. This is inherently project-specific and does not belong in a shared library. Projects use Pydantic inheritance to extend base types with platform-specific factory methods (e.g., `FanslyStudio.from_account()`).

## Distribution

The original plan used **AWS CodeArtifact** for private package hosting. This was later replaced with **GitHub CI publishing directly to PyPI**, which simplified the distribution pipeline — no private infrastructure to manage, no token refresh mechanics, and standard `pip install` works without extra configuration.

## Migration Strategy

The library was extracted primarily from **pyLoyalFans** (already Pydantic), with gap-fills from **fansly-downloader-ng** (additional error types, WebSocket subscription helpers, and client mixin coverage).

Migration followed a phased approach:

1. **Extract** common code from pyLoyalFans into the shared library
2. **Remove** platform-specific code (factory methods, processing references)
3. **Update** import paths from `pyloyalfans.stash.*` to `stash_graphql_client.*`
4. **Fill gaps** from fansly-downloader-ng (error types, missing CRUD operations)
5. **Migrate** each downstream project one at a time, keeping processing logic local

## Evolution Since Extraction

Since the initial extraction, the library has grown significantly beyond the original plan:

- **Identity Map** with Pydantic v2 wrap validators and TTL-based caching
- **StashEntityStore** providing SQLAlchemy/Django-style data access patterns
- **Dirty tracking** for efficient partial updates
- **Bidirectional relationships** with automatic sync
- **UNSET pattern** distinguishing unqueried fields from null values
- **Batched mutations** for bulk operations
- **Dynamic capabilities and fragments** adapting queries to server version

These features are documented in their respective architecture pages:

- [Architecture Overview](overview.md)
- [Identity Map](identity-map.md)
- [Dirty Tracking](dirty-tracking.md)
- [Bidirectional Relationships](bidirectional-relationships.md)
- [Capabilities and Fragments](capabilities-and-fragments.md)
- [Library Comparisons](comparison.md)
