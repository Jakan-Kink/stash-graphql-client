# Entity Store

Identity map and caching for Stash entities. Same-ID objects returned from any
query share a single Python reference, so updates made anywhere propagate
everywhere. See the [Architecture Overview](../architecture/overview.md) for
design rationale.

The store also provides batched and bulk operations:

- **`save_batch(entities)`** — persist many entities in a single GraphQL
  round-trip, respecting creates-before-updates ordering and side-mutations.
- **`save_all()`** — flush every dirty or new entity the store is tracking.
- **`filter_and_populate(...)`** — query with filter + batched relationship
  population in one call, with nested field specs (e.g. `files__path`).

::: stash_graphql_client.store.StashEntityStore
    options:
      show_root_heading: true
      show_source: false
      heading_level: 2
