# Side Mutations

Some fields on a Stash entity cannot be written through the normal
`sceneUpdate` / `imageUpdate` / `galleryUpdate` mutations. They require
_dedicated_ mutations — `sceneSaveActivity`, `sceneAddO`, `imageIncrementO`,
`setGalleryCover`, and so on. A "side mutation" is this library's automation
for firing those extra mutations on `save()` so users don't have to call them
manually.

## The Problem

Consider updating a scene's play history and rating at the same time:

```python
scene = await client.find_scene("1")
scene.rating100 = 90                            # writable via sceneUpdate
scene.resume_time = 42.0                        # NOT writable via sceneUpdate
scene.play_history = [*scene.play_history, datetime.now()]  # NOT writable via sceneUpdate
await scene.save(client)
```

Without side mutations you'd have to call three separate client methods in
the right order and track which fields changed. Side mutations let you just
set the fields and call `save()`.

## How It Works

Each entity class declares a `__side_mutations__` dict mapping field names to
async handlers:

```python
class Scene(StashObject):
    __side_mutations__: ClassVar[dict] = {
        "resume_time": _save_activity,
        "play_duration": _save_activity,
        "o_counter": _save_o,
        "o_history": _save_o,
        "play_count": _save_play,
        "play_history": _save_play,
    }
```

A handler is an `async` function that takes the client and the entity:

```python
async def handler(client: StashClient, entity: Scene) -> None: ...
```

When `save()` runs it:

1. Runs the main update mutation for all ordinary dirty fields.
2. Looks at which side-mutation fields changed.
3. **Deduplicates** handlers — if both `resume_time` and `play_duration` are
   dirty, `_save_activity` runs only once (handlers keyed by identity).
4. Fires each unique handler in field-declaration order.
5. Handlers typically read the entity's current + snapshot state, compute the
   needed mutation(s), fire them, and update local fields from the response.

The fields listed in `__side_mutations__` are automatically excluded from the
main update input so they don't get sent twice.

## Built-In Handlers

| Entity    | Fields                                                                   | Mutation(s) Fired                                     |
| --------- | ------------------------------------------------------------------------ | ----------------------------------------------------- |
| `Scene`   | `resume_time`, `play_duration`                                           | `sceneSaveActivity`                                   |
| `Scene`   | `o_counter`, `o_history`                                                 | `sceneAddO` / `sceneDeleteO` (diff-based)             |
| `Scene`   | `play_count`, `play_history`                                             | `sceneAddPlay` / `sceneDeletePlay` (diff-based)       |
| `Image`   | `o_counter`                                                              | `imageIncrementO` / `imageDecrementO` / `imageResetO` |
| `Gallery` | `cover`                                                                  | `setGalleryCover` / `resetGalleryCover`               |
| `Tag`     | `scenes`, `images`, `galleries`, `performers`, `groups`, `scene_markers` | `bulk{Type}Update` with `tag_ids=[self.id]`           |

The `Tag` handlers are produced by the factory
`StashObject._make_bulk_relationship_handler(field, client_method, id_param)`
— covered below.

## Diff-Based Handlers

History fields (`o_history`, `play_history`) use set-diff logic: the handler
compares the current list against the snapshot captured when the entity was
loaded, determines which timestamps were _added_ and which were _removed_,
and fires `sceneAddO` or `sceneDeleteO` accordingly. This lets users treat
the list as a normal Python list:

```python
scene.o_history = [*scene.o_history, datetime.utcnow()]   # adds one
scene.o_history = [t for t in scene.o_history if t.year >= 2024]  # removes old
await scene.save(client)
```

## Delta-Based Handlers

`Image.o_counter` uses delta logic: snapshot-vs-current integer difference,
incrementing or decrementing that many times. Setting `o_counter = 0` when
the snapshot was non-zero fires a single `imageResetO` instead.

## Bulk Relationship Handlers

`Tag` doesn't have a `scene_ids` field on `TagUpdateInput` — scenes are
associated with tags via `Scene.tags` (or `bulkSceneUpdate(tag_ids=...)`).
The bulk relationship handler factory builds side-mutation handlers that
fire the _inverse_ entity's bulk update:

```python
# In Tag.__side_mutations__:
"scenes": StashObject._make_bulk_relationship_handler(
    "scenes",          # Local field on the Tag
    "bulk_scene_update",  # Client method to call
    "tag_ids",         # Input field name on BulkSceneUpdateInput
),
```

When `tag.scenes = [scene1, scene2]` and `save()` runs, the handler calls
`client.bulk_scene_update({"ids": [scene1.id, scene2.id], "tag_ids": {"ids": [tag.id], "mode": "ADD"}})`.
This is how relationship fields that the owning-side's update input doesn't
support still get persisted.

## Interaction With `save_batch`

`store.save_batch(entities)` executes all main updates in a single GraphQL
round-trip. Side-mutation handlers then fire sequentially, **per entity**,
**after** the batch response returns. Failures on a main mutation skip that
entity's side mutations; failures inside a side-mutation handler are logged
but don't stop other entities' handlers from running.

See the [Batched Mutations guide](batched-mutations.md) for the full
ordering model.

## Queued Side Operations

Occasionally you want to fire an extra mutation on `save()` that isn't tied
to a field — for example, a one-shot mark-as-processed. Use
`_queue_side_op()`:

```python
async def mark_processed(client: StashClient, scene: Scene) -> None:
    await client.scene_save_activity(scene.id, resume_time=0.0)

scene._queue_side_op(mark_processed)
await scene.save(client)   # runs main update + mark_processed
```

Queued ops are FIFO and run _after_ the field-based handlers. They're
cleared once executed, so re-saving the same entity won't re-fire them.

## Defining Custom Handlers

Subclass an entity and extend its `__side_mutations__`:

```python
class MyScene(Scene):
    __side_mutations__: ClassVar[dict] = {
        **Scene.__side_mutations__,
        "my_custom_field": _my_handler,
    }

    @staticmethod
    async def _my_handler(client: StashClient, scene: "MyScene") -> None:
        # Fire whatever mutation(s) this field needs
        await client.my_custom_mutation(scene.id, scene.my_custom_field)
```

Be sure to include `"my_custom_field"` in `__tracked_fields__` so the dirty
detector notices changes to it.

## See Also

- [Relationship DSL](relationship-dsl.md) — declaring entity relationships
  with `belongs_to`, `habtm`, `has_many`, `has_many_through`.
- [Batched Mutations](batched-mutations.md) — how side mutations fit into
  the batch flow.
- [Bidirectional Relationships](../architecture/bidirectional-relationships.md)
  — architectural rationale for inverse sync.
