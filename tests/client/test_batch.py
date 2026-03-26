"""Unit tests for batched GraphQL mutation support.

Tests cover:
- build_batch_document() document construction
- execute_batch() HTTP execution, result mapping, chunking, and error handling
"""

import json

import httpx
import pytest
import respx

from stash_graphql_client import BatchOperation, BatchResult, StashClient
from stash_graphql_client.client.batch import build_batch_document
from stash_graphql_client.errors import StashBatchError, StashGraphQLError
from tests.fixtures import dump_graphql_calls


# =============================================================================
# build_batch_document tests (pure unit, no HTTP)
# =============================================================================


class TestBuildBatchDocument:
    """Tests for the document builder function."""

    def test_single_operation(self) -> None:
        """Single operation still gets aliased as op0."""
        ops = [
            BatchOperation(
                mutation_name="sceneUpdate",
                input_type_name="SceneUpdateInput!",
                variables={"input": {"id": "1", "title": "New"}},
            )
        ]
        query, variables = build_batch_document(ops)

        assert "$input0: SceneUpdateInput!" in query
        assert "op0: sceneUpdate(input: $input0)" in query
        assert "id __typename" in query
        assert variables["input0"] == {"id": "1", "title": "New"}

    def test_two_heterogeneous_operations(self) -> None:
        """Two different mutation types produce correct aliases and vars."""
        ops = [
            BatchOperation(
                mutation_name="sceneUpdate",
                input_type_name="SceneUpdateInput!",
                variables={"input": {"id": "1", "title": "A"}},
            ),
            BatchOperation(
                mutation_name="tagCreate",
                input_type_name="TagCreateInput!",
                variables={"input": {"name": "Action"}},
            ),
        ]
        query, variables = build_batch_document(ops)

        assert "$input0: SceneUpdateInput!" in query
        assert "$input1: TagCreateInput!" in query
        assert "op0: sceneUpdate(input: $input0)" in query
        assert "op1: tagCreate(input: $input1)" in query
        assert variables["input0"] == {"id": "1", "title": "A"}
        assert variables["input1"] == {"name": "Action"}

    def test_custom_return_fields(self) -> None:
        """Custom return_fields appear in the selection."""
        ops = [
            BatchOperation(
                mutation_name="tagCreate",
                input_type_name="TagCreateInput!",
                variables={"input": {"name": "X"}},
                return_fields="id name description",
            )
        ]
        query, _ = build_batch_document(ops)
        assert "{ id name description }" in query

    def test_five_homogeneous_operations(self) -> None:
        """Five operations of the same type produce op0..op4."""
        ops = [
            BatchOperation(
                mutation_name="imageUpdate",
                input_type_name="ImageUpdateInput!",
                variables={"input": {"id": str(i), "title": f"Image {i}"}},
            )
            for i in range(5)
        ]
        query, variables = build_batch_document(ops)

        for i in range(5):
            assert f"$input{i}: ImageUpdateInput!" in query
            assert f"op{i}: imageUpdate(input: $input{i})" in query
            assert variables[f"input{i}"]["id"] == str(i)

    def test_variables_extraction_from_input_key(self) -> None:
        """Variables nested under 'input' key are extracted correctly."""
        ops = [
            BatchOperation(
                mutation_name="tagCreate",
                input_type_name="TagCreateInput!",
                variables={"input": {"name": "Test"}},
            )
        ]
        _, variables = build_batch_document(ops)
        # Should extract the value from the "input" key
        assert variables["input0"] == {"name": "Test"}


# =============================================================================
# execute_batch tests (HTTP-mocked)
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_empty_batch(respx_stash_client: StashClient) -> None:
    """Empty operations list returns empty BatchResult without HTTP call."""
    result = await respx_stash_client.execute_batch([])

    assert isinstance(result, BatchResult)
    assert len(result) == 0
    assert result.all_succeeded is True
    assert result.succeeded == []
    assert result.failed == []


@pytest.mark.asyncio
@pytest.mark.unit
async def test_single_operation_succeeds(respx_stash_client: StashClient) -> None:
    """Single operation executes and maps result correctly."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json={"data": {"op0": {"id": "42", "__typename": "Tag"}}},
            )
        ]
    )

    ops = [
        BatchOperation(
            mutation_name="tagCreate",
            input_type_name="TagCreateInput!",
            variables={"input": {"name": "Action"}},
        )
    ]

    try:
        result = await respx_stash_client.execute_batch(ops)
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert result.all_succeeded
    assert len(result) == 1
    assert result[0].result == {"id": "42", "__typename": "Tag"}

    # Verify request content
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "op0: tagCreate(input: $input0)" in req["query"]
    assert req["variables"]["input0"]["name"] == "Action"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_homogeneous_batch_five_updates(
    respx_stash_client: StashClient,
) -> None:
    """Five sceneUpdate operations in a single HTTP request."""
    response_data = {
        f"op{i}": {"id": str(i + 1), "__typename": "Scene"} for i in range(5)
    }
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(200, json={"data": response_data})]
    )

    ops = [
        BatchOperation(
            mutation_name="sceneUpdate",
            input_type_name="SceneUpdateInput!",
            variables={"input": {"id": str(i + 1), "title": f"Scene {i}"}},
        )
        for i in range(5)
    ]

    try:
        result = await respx_stash_client.execute_batch(ops)
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert result.all_succeeded
    assert len(result.succeeded) == 5
    for i, op in enumerate(result.operations):
        assert op.result["id"] == str(i + 1)

    # Single HTTP request
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    for i in range(5):
        assert f"op{i}: sceneUpdate(input: $input{i})" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_heterogeneous_batch(respx_stash_client: StashClient) -> None:
    """Mix of different mutation types in one batch."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "data": {
                        "op0": {"id": "1", "__typename": "Scene"},
                        "op1": {"id": "99", "__typename": "Tag"},
                        "op2": {"id": "50", "__typename": "Performer"},
                    }
                },
            )
        ]
    )

    ops = [
        BatchOperation(
            "sceneUpdate",
            "SceneUpdateInput!",
            {"input": {"id": "1", "title": "X"}},
        ),
        BatchOperation(
            "tagCreate",
            "TagCreateInput!",
            {"input": {"name": "Action"}},
        ),
        BatchOperation(
            "performerUpdate",
            "PerformerUpdateInput!",
            {"input": {"id": "50", "name": "Jane"}},
        ),
    ]

    try:
        result = await respx_stash_client.execute_batch(ops)
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert result.all_succeeded
    assert result[0].result["__typename"] == "Scene"
    assert result[1].result["id"] == "99"
    assert result[2].result["__typename"] == "Performer"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_chunking_two_requests(respx_stash_client: StashClient) -> None:
    """Operations exceeding max_batch_size produce multiple HTTP requests."""
    # 8 operations, max_batch_size=5 → 2 chunks (5 + 3)
    chunk1_data = {f"op{i}": {"id": str(i), "__typename": "Image"} for i in range(5)}
    chunk2_data = {
        f"op{i}": {"id": str(i + 5), "__typename": "Image"} for i in range(3)
    }

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json={"data": chunk1_data}),
            httpx.Response(200, json={"data": chunk2_data}),
        ]
    )

    ops = [
        BatchOperation(
            "imageUpdate",
            "ImageUpdateInput!",
            {"input": {"id": str(i), "title": f"Img {i}"}},
        )
        for i in range(8)
    ]

    try:
        result = await respx_stash_client.execute_batch(ops, max_batch_size=5)
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert result.all_succeeded
    assert len(result) == 8
    # Two HTTP requests
    assert len(graphql_route.calls) == 2

    # First chunk: op0..op4
    req1 = json.loads(graphql_route.calls[0].request.content)
    assert "op4: imageUpdate" in req1["query"]

    # Second chunk: op0..op2 (chunk-local aliases)
    req2 = json.loads(graphql_route.calls[1].request.content)
    assert "op0: imageUpdate" in req2["query"]
    assert "op2: imageUpdate" in req2["query"]

    # Results mapped correctly across chunks
    for i in range(8):
        assert result[i].result["id"] == str(i)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_partial_failure_raises_batch_error(
    respx_stash_client: StashClient,
) -> None:
    """Partial failure raises StashBatchError with partial results."""
    from gql.transport.exceptions import TransportQueryError

    # Mock the session.execute to raise TransportQueryError with partial data
    partial_data = {
        "op0": {"id": "1", "__typename": "Scene"},
        "op1": None,  # Failed
        "op2": {"id": "3", "__typename": "Scene"},
    }
    errors = [{"message": "Scene not found", "path": ["op1"]}]

    original_execute = respx_stash_client._session.execute

    async def mock_execute(operation):
        raise TransportQueryError(
            "Partial failure",
            errors=errors,
            data=partial_data,
        )

    respx_stash_client._session.execute = mock_execute

    ops = [
        BatchOperation(
            "sceneUpdate",
            "SceneUpdateInput!",
            {"input": {"id": str(i), "title": f"S{i}"}},
        )
        for i in range(3)
    ]

    try:
        with pytest.raises(StashBatchError) as exc_info:
            await respx_stash_client.execute_batch(ops)

        batch_result = exc_info.value.batch_result
        assert len(batch_result.succeeded) == 2
        assert len(batch_result.failed) == 1
        assert batch_result.failed[0] is ops[1]
        assert isinstance(batch_result.failed[0].error, StashGraphQLError)
        assert "Scene not found" in str(batch_result.failed[0].error)
    finally:
        respx_stash_client._session.execute = original_execute


@pytest.mark.asyncio
@pytest.mark.unit
async def test_all_fail_raises_batch_error(
    respx_stash_client: StashClient,
) -> None:
    """All operations failing raises StashBatchError with all in .failed."""
    from gql.transport.exceptions import TransportQueryError

    errors = [
        {"message": "Error for op0", "path": ["op0"]},
        {"message": "Error for op1", "path": ["op1"]},
    ]

    async def mock_execute(operation):
        raise TransportQueryError(
            "All failed",
            errors=errors,
            data={},
        )

    original_execute = respx_stash_client._session.execute
    respx_stash_client._session.execute = mock_execute

    ops = [
        BatchOperation(
            "tagCreate",
            "TagCreateInput!",
            {"input": {"name": f"Tag{i}"}},
        )
        for i in range(2)
    ]

    try:
        with pytest.raises(StashBatchError) as exc_info:
            await respx_stash_client.execute_batch(ops)

        batch_result = exc_info.value.batch_result
        assert len(batch_result.failed) == 2
        assert len(batch_result.succeeded) == 0
        assert "2/2 operations had errors" in str(exc_info.value)
    finally:
        respx_stash_client._session.execute = original_execute


@pytest.mark.asyncio
@pytest.mark.unit
async def test_nested_error_path_maps_by_first_element(
    respx_stash_client: StashClient,
) -> None:
    """Nested error paths like ['op1', 'input', 'title'] map to op1."""
    from gql.transport.exceptions import TransportQueryError

    partial_data = {"op0": {"id": "1", "__typename": "Scene"}}
    errors = [
        {
            "message": "Invalid title",
            "path": ["op1", "input", "title"],
        }
    ]

    async def mock_execute(operation):
        raise TransportQueryError(
            "Validation error",
            errors=errors,
            data=partial_data,
        )

    original_execute = respx_stash_client._session.execute
    respx_stash_client._session.execute = mock_execute

    ops = [
        BatchOperation(
            "sceneUpdate", "SceneUpdateInput!", {"input": {"id": "1", "title": "OK"}}
        ),
        BatchOperation(
            "sceneUpdate",
            "SceneUpdateInput!",
            {"input": {"id": "2", "title": "BAD"}},
        ),
    ]

    try:
        with pytest.raises(StashBatchError) as exc_info:
            await respx_stash_client.execute_batch(ops)

        batch_result = exc_info.value.batch_result
        assert batch_result[0].result == {"id": "1", "__typename": "Scene"}
        assert batch_result[1].error is not None
        assert "Invalid title" in str(batch_result[1].error)
    finally:
        respx_stash_client._session.execute = original_execute


@pytest.mark.asyncio
@pytest.mark.unit
async def test_datetime_and_unset_conversion(
    respx_stash_client: StashClient,
) -> None:
    """Variables with datetime and UNSET values are converted before execution."""
    from datetime import UTC, datetime

    from stash_graphql_client.types.unset import UNSET

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json={"data": {"op0": {"id": "1", "__typename": "Scene"}}},
            )
        ]
    )

    dt = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)
    ops = [
        BatchOperation(
            "sceneUpdate",
            "SceneUpdateInput!",
            variables={"input": {"id": "1", "date": dt, "details": UNSET}},
        )
    ]

    try:
        result = await respx_stash_client.execute_batch(ops)
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert result.all_succeeded

    # Verify the converted variables were sent
    req = json.loads(graphql_route.calls[0].request.content)
    sent_vars = req["variables"]["input0"]
    assert sent_vars["date"] == "2024-01-15T12:00:00+00:00"
    assert "details" not in sent_vars  # UNSET filtered out


@pytest.mark.asyncio
@pytest.mark.unit
async def test_batch_result_iteration(respx_stash_client: StashClient) -> None:
    """BatchResult supports iteration and indexing."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "data": {
                        "op0": {"id": "1", "__typename": "Tag"},
                        "op1": {"id": "2", "__typename": "Tag"},
                    }
                },
            )
        ]
    )

    ops = [
        BatchOperation("tagCreate", "TagCreateInput!", {"input": {"name": f"T{i}"}})
        for i in range(2)
    ]

    try:
        result = await respx_stash_client.execute_batch(ops)
    finally:
        dump_graphql_calls(graphql_route.calls)

    # Indexing
    assert result[0].result["id"] == "1"
    assert result[1].result["id"] == "2"

    # Iteration
    ids = [op.result["id"] for op in result]
    assert ids == ["1", "2"]

    # len
    assert len(result) == 2


# =============================================================================
# Edge-case error path tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_response_missing_alias_key(respx_stash_client: StashClient) -> None:
    """Response missing an expected alias key marks that op as errored."""
    # Server returns op0 but not op1
    respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json={"data": {"op0": {"id": "1", "__typename": "Tag"}}},
            )
        ]
    )

    ops = [
        BatchOperation("tagCreate", "TagCreateInput!", {"input": {"name": "A"}}),
        BatchOperation("tagCreate", "TagCreateInput!", {"input": {"name": "B"}}),
    ]

    with pytest.raises(StashBatchError) as exc_info:
        await respx_stash_client.execute_batch(ops)

    batch_result = exc_info.value.batch_result
    assert batch_result[0].result == {"id": "1", "__typename": "Tag"}
    assert batch_result[1].error is not None
    assert "No response for alias" in str(batch_result[1].error)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_error_without_alias_path(respx_stash_client: StashClient) -> None:
    """Error without a mappable alias path is assigned to all unresolved ops."""
    from gql.transport.exceptions import TransportQueryError

    async def mock_execute(operation):
        raise TransportQueryError(
            "Generic error",
            errors=[{"message": "Something broke"}],  # no "path" key
            data={},
        )

    original = respx_stash_client._session.execute
    respx_stash_client._session.execute = mock_execute

    ops = [
        BatchOperation("tagCreate", "TagCreateInput!", {"input": {"name": "A"}}),
    ]

    try:
        with pytest.raises(StashBatchError) as exc_info:
            await respx_stash_client.execute_batch(ops)

        assert "Something broke" in str(exc_info.value.batch_result[0].error)
    finally:
        respx_stash_client._session.execute = original


@pytest.mark.asyncio
@pytest.mark.unit
async def test_unmappable_error_path(respx_stash_client: StashClient) -> None:
    """Error with unparseable alias like 'opXYZ' logs warning."""
    from gql.transport.exceptions import TransportQueryError

    async def mock_execute(operation):
        raise TransportQueryError(
            "Bad path",
            errors=[{"message": "Boom", "path": ["opNotANumber"]}],
            data={},
        )

    original = respx_stash_client._session.execute
    respx_stash_client._session.execute = mock_execute

    ops = [
        BatchOperation("tagCreate", "TagCreateInput!", {"input": {"name": "A"}}),
    ]

    try:
        with pytest.raises(StashBatchError) as exc_info:
            await respx_stash_client.execute_batch(ops)

        # The op should get the fallback "No response or error" since the path
        # couldn't be mapped
        assert exc_info.value.batch_result[0].error is not None
    finally:
        respx_stash_client._session.execute = original


@pytest.mark.asyncio
@pytest.mark.unit
async def test_gql_parse_error_raises_value_error(
    respx_stash_client: StashClient,
) -> None:
    """Malformed mutation name that produces invalid GraphQL raises ValueError."""
    ops = [
        BatchOperation(
            mutation_name="!!!invalid",  # Will produce invalid GraphQL syntax
            input_type_name="Foo!",
            variables={"input": {}},
        )
    ]

    with pytest.raises(ValueError, match="Invalid batch GraphQL query syntax"):
        await respx_stash_client.execute_batch(ops)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_session_none_raises_runtime_error(
    respx_stash_client: StashClient,
) -> None:
    """execute_batch with None session raises RuntimeError."""
    original = respx_stash_client._session
    respx_stash_client._session = None

    ops = [
        BatchOperation("tagCreate", "TagCreateInput!", {"input": {"name": "A"}}),
    ]

    try:
        with pytest.raises(RuntimeError, match="GQL session not initialized"):
            await respx_stash_client.execute_batch(ops)
    finally:
        respx_stash_client._session = original


@pytest.mark.asyncio
@pytest.mark.unit
async def test_pathless_error_skips_ops_with_results(
    respx_stash_client: StashClient,
) -> None:
    """Pathless error only assigns to ops that don't already have results."""
    from gql.transport.exceptions import TransportQueryError

    async def mock_execute(operation):
        raise TransportQueryError(
            "Mixed",
            errors=[{"message": "Global failure"}],  # No path
            data={"op0": {"id": "1", "__typename": "Tag"}},  # op0 succeeded
        )

    original = respx_stash_client._session.execute
    respx_stash_client._session.execute = mock_execute

    ops = [
        BatchOperation("tagCreate", "TagCreateInput!", {"input": {"name": "A"}}),
        BatchOperation("tagCreate", "TagCreateInput!", {"input": {"name": "B"}}),
    ]

    try:
        with pytest.raises(StashBatchError) as exc_info:
            await respx_stash_client.execute_batch(ops)

        br = exc_info.value.batch_result
        # op0 has a result, so pathless error should NOT overwrite it
        assert br[0].result == {"id": "1", "__typename": "Tag"}
        assert br[0].error is None
        # op1 has no result, so pathless error SHOULD be assigned
        assert br[1].error is not None
        assert "Global failure" in str(br[1].error)
    finally:
        respx_stash_client._session.execute = original


@pytest.mark.asyncio
@pytest.mark.unit
async def test_error_path_out_of_range_ignored(
    respx_stash_client: StashClient,
) -> None:
    """Error with valid alias format but out-of-range index is handled."""
    from gql.transport.exceptions import TransportQueryError

    async def mock_execute(operation):
        raise TransportQueryError(
            "Out of range",
            errors=[{"message": "Bad index", "path": ["op999"]}],
            data={},
        )

    original = respx_stash_client._session.execute
    respx_stash_client._session.execute = mock_execute

    ops = [
        BatchOperation("tagCreate", "TagCreateInput!", {"input": {"name": "A"}}),
    ]

    try:
        with pytest.raises(StashBatchError) as exc_info:
            await respx_stash_client.execute_batch(ops)

        # op999 is out of range — op[0] gets fallback error
        assert exc_info.value.batch_result[0].error is not None
    finally:
        respx_stash_client._session.execute = original


@pytest.mark.asyncio
@pytest.mark.unit
async def test_network_error_raises_connection_error(
    respx_stash_client: StashClient,
) -> None:
    """Non-GraphQL transport error (e.g. network failure) raises StashConnectionError."""
    from gql.transport.exceptions import TransportError

    from stash_graphql_client.errors import StashConnectionError

    async def mock_execute(operation):
        raise TransportError("Connection refused")

    original = respx_stash_client._session.execute
    respx_stash_client._session.execute = mock_execute

    ops = [
        BatchOperation("tagCreate", "TagCreateInput!", {"input": {"name": "A"}}),
    ]

    try:
        with pytest.raises(StashConnectionError):
            await respx_stash_client.execute_batch(ops)
    finally:
        respx_stash_client._session.execute = original
