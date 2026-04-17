# Batch Operations

Data structures and helpers for batched GraphQL mutations. These low-level
primitives underlie the three-layer batch API:

- **`client.execute_batch(operations)`** — executes a list of `BatchOperation`s
  in a single aliased GraphQL request. Handles chunking (default 250 ops),
  aliasing, and partial-failure propagation. Returns a `BatchResult`.
- **`store.save_batch(entities)`** — takes entity objects and builds the
  appropriate operations automatically, including any queued side-mutations.
- **`store.save_all()`** — flushes every dirty or new entity the store is
  currently tracking.

For end-to-end usage patterns, see the
[Batched Mutations guide](../guide/batched-mutations.md).

::: stash_graphql_client.client.batch
    options:
      show_root_heading: false
      show_source: false
      heading_level: 2
      members:
        - BatchOperation
        - BatchResult
        - build_batch_document
