"""Tests for SQL query methods in SystemQueryClientMixin."""

import json

import httpx
import pytest
import respx

from stash_graphql_client import StashClient
from stash_graphql_client.types.unset import is_set
from tests.fixtures.stash.graphql_responses import create_graphql_response


@pytest.mark.asyncio
@pytest.mark.unit
async def test_sql_query_basic(respx_stash_client: StashClient) -> None:
    """Test sql_query() method with basic SELECT query."""
    sql_result_data = {
        "columns": ["id", "title", "rating100"],
        "rows": [
            ["1", "Scene 1", 85],
            ["2", "Scene 2", 90],
            ["3", "Scene 3", 95],
        ],
    }

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("querySQL", sql_result_data)
            )
        ]
    )

    result = await respx_stash_client.sql_query(
        "SELECT id, title, rating100 FROM scenes WHERE rating100 > ?", args=[80]
    )

    # Verify response data
    assert result.columns == ["id", "title", "rating100"]
    assert is_set(result.rows)
    assert result.rows is not None
    assert len(result.rows) == 3
    assert result.rows[0] == ["1", "Scene 1", 85]
    assert result.rows[1] == ["2", "Scene 2", 90]
    assert result.rows[2] == ["3", "Scene 3", 95]

    # Verify call count
    assert len(graphql_route.calls) == 1

    # Verify request content
    req = json.loads(graphql_route.calls[0].request.content)
    assert "querySQL" in req["query"]
    assert (
        req["variables"]["sql"]
        == "SELECT id, title, rating100 FROM scenes WHERE rating100 > ?"
    )
    assert req["variables"]["args"] == [80]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_sql_query_no_args(respx_stash_client: StashClient) -> None:
    """Test sql_query() method without arguments."""
    sql_result_data = {
        "columns": ["gender", "count"],
        "rows": [
            ["MALE", 15],
            ["FEMALE", 25],
            ["NON_BINARY", 3],
        ],
    }

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("querySQL", sql_result_data)
            )
        ]
    )

    result = await respx_stash_client.sql_query(
        "SELECT gender, COUNT(*) as count FROM performers GROUP BY gender"
    )

    # Verify response data
    assert result.columns == ["gender", "count"]
    assert is_set(result.rows)
    assert result.rows is not None
    assert len(result.rows) == 3
    assert result.rows[0] == ["MALE", 15]
    assert result.rows[1] == ["FEMALE", 25]
    assert result.rows[2] == ["NON_BINARY", 3]

    # Verify call count
    assert len(graphql_route.calls) == 1

    # Verify request content - should have empty args array
    req = json.loads(graphql_route.calls[0].request.content)
    assert "querySQL" in req["query"]
    assert (
        req["variables"]["sql"]
        == "SELECT gender, COUNT(*) as count FROM performers GROUP BY gender"
    )
    assert req["variables"]["args"] == []


@pytest.mark.asyncio
@pytest.mark.unit
async def test_sql_query_empty_result(respx_stash_client: StashClient) -> None:
    """Test sql_query() method with empty result set."""
    sql_result_data = {
        "columns": ["id", "name"],
        "rows": [],
    }

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("querySQL", sql_result_data)
            )
        ]
    )

    result = await respx_stash_client.sql_query(
        "SELECT id, name FROM tags WHERE name LIKE ?", args=["%nonexistent%"]
    )

    # Verify response data
    assert result.columns == ["id", "name"]
    assert result.rows == []

    # Verify call count
    assert len(graphql_route.calls) == 1

    # Verify request content
    req = json.loads(graphql_route.calls[0].request.content)
    assert "querySQL" in req["query"]
    assert req["variables"]["args"] == ["%nonexistent%"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_sql_query_multiple_args(respx_stash_client: StashClient) -> None:
    """Test sql_query() method with multiple arguments."""
    sql_result_data = {
        "columns": ["id", "title", "rating100", "date"],
        "rows": [
            ["10", "High Rated Scene", 95, "2024-01-15"],
            ["15", "Another Great Scene", 90, "2024-02-20"],
        ],
    }

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("querySQL", sql_result_data)
            )
        ]
    )

    result = await respx_stash_client.sql_query(
        "SELECT id, title, rating100, date FROM scenes WHERE rating100 > ? AND date > ? ORDER BY rating100 DESC",
        args=[85, "2024-01-01"],
    )

    # Verify response data
    assert result.columns == ["id", "title", "rating100", "date"]
    assert is_set(result.rows)
    assert result.rows is not None
    assert len(result.rows) == 2
    assert result.rows[0][1] == "High Rated Scene"
    assert result.rows[1][1] == "Another Great Scene"

    # Verify call count
    assert len(graphql_route.calls) == 1

    # Verify request content
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["args"] == [85, "2024-01-01"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_sql_exec_update(respx_stash_client: StashClient) -> None:
    """Test sql_exec() method with UPDATE statement."""
    sql_exec_result_data = {
        "rows_affected": 5,
        "last_insert_id": None,
    }

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("execSQL", sql_exec_result_data)
            )
        ]
    )

    result = await respx_stash_client.sql_exec(
        "UPDATE scenes SET rating100 = ? WHERE id IN (?, ?, ?, ?, ?)",
        args=[100, "1", "2", "3", "4", "5"],
    )

    # Verify response data
    assert result.rows_affected == 5
    assert result.last_insert_id is None

    # Verify call count
    assert len(graphql_route.calls) == 1

    # Verify request content
    req = json.loads(graphql_route.calls[0].request.content)
    assert "execSQL" in req["query"]
    assert (
        req["variables"]["sql"]
        == "UPDATE scenes SET rating100 = ? WHERE id IN (?, ?, ?, ?, ?)"
    )
    assert req["variables"]["args"] == [100, "1", "2", "3", "4", "5"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_sql_exec_delete(respx_stash_client: StashClient) -> None:
    """Test sql_exec() method with DELETE statement."""
    sql_exec_result_data = {
        "rows_affected": 3,
        "last_insert_id": None,
    }

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("execSQL", sql_exec_result_data)
            )
        ]
    )

    result = await respx_stash_client.sql_exec(
        "DELETE FROM tags WHERE id NOT IN (SELECT DISTINCT tag_id FROM scene_tags)"
    )

    # Verify response data
    assert result.rows_affected == 3
    assert result.last_insert_id is None

    # Verify call count
    assert len(graphql_route.calls) == 1

    # Verify request content - should have empty args
    req = json.loads(graphql_route.calls[0].request.content)
    assert "execSQL" in req["query"]
    assert req["variables"]["args"] == []


@pytest.mark.asyncio
@pytest.mark.unit
async def test_sql_exec_insert_with_last_insert_id(
    respx_stash_client: StashClient,
) -> None:
    """Test sql_exec() method with INSERT statement returning last_insert_id."""
    sql_exec_result_data = {
        "rows_affected": 1,
        "last_insert_id": 42,
    }

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("execSQL", sql_exec_result_data)
            )
        ]
    )

    result = await respx_stash_client.sql_exec(
        "INSERT INTO custom_metadata (entity_id, key, value) VALUES (?, ?, ?)",
        args=["scene-123", "custom_field", "custom_value"],
    )

    # Verify response data
    assert result.rows_affected == 1
    assert result.last_insert_id == 42

    # Verify call count
    assert len(graphql_route.calls) == 1

    # Verify request content
    req = json.loads(graphql_route.calls[0].request.content)
    assert "execSQL" in req["query"]
    assert req["variables"]["args"] == ["scene-123", "custom_field", "custom_value"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_sql_exec_no_rows_affected(respx_stash_client: StashClient) -> None:
    """Test sql_exec() method with statement that affects no rows."""
    sql_exec_result_data = {
        "rows_affected": 0,
        "last_insert_id": None,
    }

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("execSQL", sql_exec_result_data)
            )
        ]
    )

    result = await respx_stash_client.sql_exec(
        "UPDATE performers SET rating100 = ? WHERE id = ?", args=[100, "nonexistent-id"]
    )

    # Verify response data
    assert result.rows_affected == 0
    assert result.last_insert_id is None

    # Verify call count
    assert len(graphql_route.calls) == 1

    # Verify request content
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["args"] == [100, "nonexistent-id"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_sql_query_error_handling(respx_stash_client: StashClient) -> None:
    """Test sql_query() method error handling."""
    # Mock GraphQL error response
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "data": None,
                    "errors": [
                        {
                            "message": "SQL syntax error near 'SLECT'",
                            "path": ["querySQL"],
                        }
                    ],
                },
            )
        ]
    )

    # Should raise exception on SQL error
    with pytest.raises(Exception):  # noqa: B017, PT011
        await respx_stash_client.sql_query("SLECT * FROM scenes")

    # Verify call was made
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_sql_exec_error_handling(respx_stash_client: StashClient) -> None:
    """Test sql_exec() method error handling."""
    # Mock GraphQL error response
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "data": None,
                    "errors": [
                        {
                            "message": "Cannot delete rows due to foreign key constraint",
                            "path": ["execSQL"],
                        }
                    ],
                },
            )
        ]
    )

    # Should raise exception on SQL error
    with pytest.raises(Exception):  # noqa: B017, PT011
        await respx_stash_client.sql_exec(
            "DELETE FROM studios WHERE id = ?", args=["1"]
        )

    # Verify call was made
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_sql_query_complex_data_types(respx_stash_client: StashClient) -> None:
    """Test sql_query() with various data types in results."""
    sql_result_data = {
        "columns": ["id", "title", "rating", "duration", "date", "organized"],
        "rows": [
            ["1", "Scene 1", 85.5, 1800.0, "2024-01-15", True],
            ["2", "Scene 2", 90.0, 2400.5, "2024-02-20", False],
            ["3", None, None, None, None, None],  # Test NULL values
        ],
    }

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("querySQL", sql_result_data)
            )
        ]
    )

    result = await respx_stash_client.sql_query(
        "SELECT id, title, rating, duration, date, organized FROM scenes"
    )

    # Verify response data with various types
    assert is_set(result.rows)
    assert result.rows is not None
    assert len(result.rows) == 3
    assert result.rows[0] == ["1", "Scene 1", 85.5, 1800.0, "2024-01-15", True]
    assert result.rows[1] == ["2", "Scene 2", 90.0, 2400.5, "2024-02-20", False]
    # NULL values should be None
    assert result.rows[2] == ["3", None, None, None, None, None]

    # Verify call count
    assert len(graphql_route.calls) == 1
