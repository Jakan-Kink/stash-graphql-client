"""Cross-cutting assertions for GraphQL query-string assembly.

Used by any test that builds query strings from fragments (FragmentStore's
scene/image/gallery/file queries) and needs to verify the assembled document is
valid and self-contained — in particular that fragment-set deduplication did not
drop a needed definition or leave a duplicate.
"""

from __future__ import annotations

from graphql import FragmentDefinitionNode, Visitor, parse, visit

from stash_graphql_client.types import JsonDict, expect_dict, expect_list


class _SpreadCollector(Visitor):
    """Collect every ``...FragmentName`` spread name in a parsed document."""

    def __init__(self) -> None:
        super().__init__()
        self.names: list[str] = []

    def enter_fragment_spread(self, node, *_args):
        self.names.append(node.name.value)


def assert_query_fragments_resolve(query: str) -> None:
    """Assert ``query`` parses, declares no duplicate fragments, and that every
    fragment spread resolves to a definition in the same document.

    Args:
        query: The GraphQL query/document string to validate.

    Raises:
        AssertionError: If a fragment is declared more than once, or a
            ``...Fragment`` spread has no matching definition.
        graphql.GraphQLSyntaxError: If the query is not syntactically valid.
    """
    document = parse(query)

    defined = [
        definition.name.value
        for definition in document.definitions
        if isinstance(definition, FragmentDefinitionNode)
    ]
    duplicates = sorted({name for name in defined if defined.count(name) > 1})
    assert not duplicates, f"duplicate fragment definitions: {duplicates}"

    collector = _SpreadCollector()
    visit(document, collector)
    unresolved = sorted(set(collector.names) - set(defined))
    assert not unresolved, f"fragment spreads with no definition: {unresolved}"


def introspection_field_names(result: JsonDict, type_key: str) -> set[str]:
    """Field names from a ``__type`` introspection result keyed under ``type_key``.

    Narrows the JSON response (``execute()`` returns ``JsonDict``) to the
    ``fields`` array and collects each field's ``name``.

    Args:
        result: The ``execute()`` response, e.g. ``{"_mutations": {"fields": [...]}}``.
        type_key: The aliased ``__type`` key to read (e.g. ``"_mutations"``).

    Returns:
        The set of field-name strings under ``result[type_key]["fields"]``.
    """
    container = expect_dict(result.get(type_key) or {}, type_key)
    fields = expect_list(container.get("fields") or [], "fields")
    return {str(expect_dict(field, "field")["name"]) for field in fields}
