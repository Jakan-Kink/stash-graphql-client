"""Batched GraphQL mutation support.

This module provides data structures and helpers for combining multiple
GraphQL mutations into a single aliased document, reducing HTTP round-trips.

Example::

    from stash_graphql_client.client.batch import BatchOperation, build_batch_document

    ops = [
        BatchOperation("sceneUpdate", "SceneUpdateInput!", {"input": {"id": "1", "title": "New"}}),
        BatchOperation("tagCreate", "TagCreateInput!", {"input": {"name": "Action"}}),
    ]
    query, variables = build_batch_document(ops)
    # query = 'mutation Batch($input0: SceneUpdateInput!, $input1: TagCreateInput!) {
    #   op0: sceneUpdate(input: $input0) { id __typename }
    #   op1: tagCreate(input: $input1) { id __typename }
    # }'
    # variables = {"input0": {"id": "1", "title": "New"}, "input1": {"name": "Action"}}
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class BatchOperation:
    """A single operation within a batch request.

    Attributes:
        mutation_name: The GraphQL mutation field name (e.g. ``"sceneUpdate"``).
        input_type_name: The GraphQL input type with ``!`` suffix
            (e.g. ``"SceneUpdateInput!"``).
        variables: Variables dict, typically ``{"input": {...}}``.
        return_fields: Space-separated fields to request in the response.
            Defaults to ``"id __typename"`` so callers can validate the
            returned type.
        result: Populated after execution with the mutation's response dict,
            or ``None`` if the operation hasn't run or had an error.
        error: Populated after execution with the exception if this specific
            operation failed, or ``None`` on success.
    """

    mutation_name: str
    input_type_name: str
    variables: dict[str, Any]
    return_fields: str = "id __typename"
    # Populated after execution:
    result: dict[str, Any] | None = field(default=None, repr=False)
    error: Exception | None = field(default=None, repr=False)


@dataclass
class BatchResult:
    """Result of a batch execution.

    Contains the full list of operations (in the same order they were
    submitted) with each operation's ``.result`` and ``.error`` populated.

    Attributes:
        operations: The operations list with results/errors filled in.
        raw_response: The raw aggregated GraphQL response dict(s), or
            ``None`` for empty batches.
    """

    operations: list[BatchOperation]
    raw_response: dict[str, Any] | None = field(default=None, repr=False)

    @property
    def succeeded(self) -> list[BatchOperation]:
        """Operations that completed successfully."""
        return [
            op for op in self.operations if op.error is None and op.result is not None
        ]

    @property
    def failed(self) -> list[BatchOperation]:
        """Operations that encountered errors."""
        return [op for op in self.operations if op.error is not None]

    @property
    def all_succeeded(self) -> bool:
        """True if every operation succeeded."""
        return len(self.failed) == 0

    def __getitem__(self, index: int) -> BatchOperation:
        return self.operations[index]

    def __len__(self) -> int:
        return len(self.operations)

    def __iter__(self):
        return iter(self.operations)


def build_batch_document(
    operations: list[BatchOperation],
) -> tuple[str, dict[str, Any]]:
    """Build an aliased GraphQL mutation document from a list of operations.

    Each operation gets a unique alias (``op0``, ``op1``, ...) and a
    unique variable name (``$input0``, ``$input1``, ...).

    Args:
        operations: Non-empty list of :class:`BatchOperation` instances.

    Returns:
        A ``(query_string, merged_variables)`` tuple ready for execution.

    Example output for 2 operations::

        mutation Batch($input0: SceneUpdateInput!, $input1: TagCreateInput!) {
          op0: sceneUpdate(input: $input0) { id __typename }
          op1: tagCreate(input: $input1) { id __typename }
        }
        {"input0": {"id": "1", "title": "New"}, "input1": {"name": "Action"}}
    """
    var_declarations: list[str] = []
    selections: list[str] = []
    merged_vars: dict[str, Any] = {}

    for i, op in enumerate(operations):
        var_name = f"input{i}"
        alias = f"op{i}"

        var_declarations.append(f"${var_name}: {op.input_type_name}")
        selections.append(
            f"{alias}: {op.mutation_name}(input: ${var_name}) {{ {op.return_fields} }}"
        )
        # Extract the "input" key if present, otherwise use the whole dict
        merged_vars[var_name] = op.variables.get("input", op.variables)

    vars_str = ", ".join(var_declarations)
    body = "\n  ".join(selections)
    query = f"mutation Batch({vars_str}) {{\n  {body}\n}}"
    return query, merged_vars
