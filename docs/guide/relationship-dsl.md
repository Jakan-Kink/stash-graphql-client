# Relationship DSL

Every `StashObject` subclass declares its relationships to other entities via
a `__relationships__` class attribute. The DSL — four helper factories —
produces `RelationshipMetadata` entries that drive save mutations, inverse
synchronisation, lazy population, and `filter_and_populate` queries.

## The Four Helpers

```python
from stash_graphql_client.types.base import belongs_to, habtm, has_many, has_many_through
```

### `belongs_to(inverse_type, *, inverse_query_field=...)`

The FK side of a many-to-one. The entity _owns the write_ through a `*_id`
field on its update input type.

```python
"studio": belongs_to("Studio", inverse_query_field="scenes"),
"parent_studio": belongs_to("Studio", inverse_query_field="child_studios"),
```

The client writes `studio_id=<id>` on save. The inverse side (Studio.scenes)
is auto-populated by the server after any scene update, so no coordination
between sides is needed.

### `habtm(inverse_type, *, inverse_query_field=..., transform=...)`

Many-to-many written as a **list of IDs**. The entity owns the write through
a `*_ids` field on its update input.

```python
"tags": habtm("Tag", inverse_query_field="scenes"),
"performers": habtm("Performer", inverse_query_field="scenes"),
"parents": habtm("Tag", inverse_query_field="children"),  # self-referential
```

The client writes `tag_ids=[...]`, `performer_ids=[...]`, and so on.
`transform` converts the in-memory object into the exact input shape when the
wire format isn't a plain ID list — see `Scene.stash_ids`:

```python
"stash_ids": habtm(
    "StashID",
    transform=lambda s: StashIDInput(endpoint=s.endpoint, stash_id=s.stash_id),
),
```

### `has_many(inverse_type, *, inverse_query_field=...)`

The **read-only inverse side** of a relationship. No mutation input exists on
this entity's update type; the field is populated by issuing a filter query
against the inverse type.

```python
"scenes": has_many("Scene", inverse_query_field="tags"),
"child_studios": has_many("Studio", inverse_query_field="parent_studio"),
```

To fetch `tag.scenes`, the store calls
`find_scenes(scene_filter={"tags": {"value": [tag.id], ...}})`. `populate()`
and `filter_and_populate()` use this strategy automatically.

The `query_strategy` stored in the metadata is `"filter_query"`, and the
`filter_query_hint` is auto-derived.

### `has_many_through(inverse_type, *, transform, inverse_query_field=...)`

!!! warning "Not Rails `through: :model`"
This helper is **not** the Rails `has_many :through:` pattern. It does
not name an intermediate model that joins two sides. It means
**"through a wrapper input type that carries relationship-level metadata"**
— ordering, descriptions, or similar per-edge data.

Used when the relationship _itself_ has data attached. The wire format is a
list of wrapper objects instead of a list of IDs.

```python
# Scene.groups — each relation carries a scene_index (ordering)
"groups": has_many_through(
    "Group",
    transform=lambda sg: SceneGroupInput(
        group_id=sg.group.id, scene_index=sg.scene_index,
    ),
    inverse_query_field="scenes",
),

# Group.sub_groups / containing_groups — each carries a description
"sub_groups": has_many_through(
    "Group",
    transform=lambda g: GroupDescriptionInput(
        group_id=g.group.id, description=g.description,
    ),
    inverse_query_field="containing_groups",
),
```

`transform` is **required** here (unlike `habtm` where it's optional) because
the wrapper input must be constructed explicitly. `query_strategy` is
`"complex_object"`.

## Which Helper to Use

| Question                                                                            | Helper             |
| ----------------------------------------------------------------------------------- | ------------------ |
| Does this entity's update input take a single `*_id` field?                         | `belongs_to`       |
| Does it take a `*_ids` list field?                                                  | `habtm`            |
| Does it take a list of wrapper objects with metadata?                               | `has_many_through` |
| Is there _no_ input field for this relationship here? (written from the other side) | `has_many`         |

## Auto-Derivation

`RelationshipMetadata` has several fields you don't supply — they're resolved
in `__init_subclass__` from the dict key and sibling metadata:

- **`query_field`** — the dict key itself (`"studio"` → `query_field="studio"`).
- **`target_field`** — auto-derived by helper:
  - `belongs_to`: key + `"_id"` (e.g. `studio` → `studio_id`)
  - `habtm`: singularize(key) + `"_ids"` (e.g. `tags` → `tag_ids`, `galleries` → `gallery_ids`)
  - `has_many_through`: key as-is (the wrapper list field keeps its plural name)
  - `has_many`: `""` (no mutation input — read-only)
- **`filter_query_hint`** (for `has_many`) — derived from `inverse_type` +
  owner type to produce the right `find_X_filter={"owner_field": {...}}` shape.

You can override any of these explicitly when the convention doesn't fit, but
the idiomatic code relies on the derivation.

## Full Example

A hypothetical `Author` entity demonstrating all four patterns:

```python
from stash_graphql_client.types.base import (
    StashObject, belongs_to, habtm, has_many, has_many_through,
)

class Author(StashObject):
    __type_name__ = "Author"

    # Simple fields
    name: str | None | UnsetType = UNSET
    bio: str | None | UnsetType = UNSET

    # Relationship fields
    publisher: Publisher | None | UnsetType = UNSET      # many-to-one
    genres: list[Genre] | UnsetType = UNSET              # many-to-many (IDs)
    books: list[AuthoredBook] | UnsetType = UNSET        # many-to-many + order
    reviews: list[Review] | UnsetType = UNSET            # inverse (read-only)

    __relationships__ = {
        "publisher": belongs_to(
            "Publisher",
            inverse_query_field="authors",
        ),
        "genres": habtm(
            "Genre",
            inverse_query_field="authors",
        ),
        "books": has_many_through(
            "Book",
            transform=lambda ab: AuthoredBookInput(
                book_id=ab.book.id, author_order=ab.author_order,
            ),
            inverse_query_field="authors",
        ),
        "reviews": has_many(
            "Review",
            inverse_query_field="author",
        ),
    }
```

With this declaration alone, the following all work:

- `author.genres.append(sci_fi)` then `author.save(client)` → sends
  `genre_ids` on the author update.
- `author.publisher = new_pub; author.save(client)` → sends `publisher_id`.
- `await store.populate(author, ["reviews"])` → issues
  `find_reviews(filter={"author": {"value": [author.id]}})` and attaches the
  results to `author.reviews`.
- `await store.filter_and_populate(Author, filter={...}, fields=["books__book__title"])`
  → batched filter + nested population across the `has_many_through`.

## Interaction with Save and Side Mutations

For most relationship fields, `save()` just translates the relationship list
into its `target_field` on the update input. Some fields — content
relationships on `Tag`, `cover` on `Gallery` — are declared as
`has_many` (read-only) here because the _owning_ entity writes them, but the
user experience needs to feel writable. Those fields are handled by
[side mutations](side-mutations.md): assignments trigger bulk-update calls on
the inverse entity.

## See Also

- [Side Mutations](side-mutations.md) — the mechanism that backs
  "writable" `has_many` fields like `Tag.scenes`.
- [Bidirectional Relationships](../architecture/bidirectional-relationships.md)
  — architectural rationale for how these relationships stay in sync without
  dual mutations.
- [Batched Mutations](batched-mutations.md) — how relationship updates batch
  when multiple entities are saved together.
