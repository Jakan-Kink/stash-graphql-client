"""Comprehensive spy-wrapped test for debugging find_scenes execution pipeline.

This test instruments every step of the GraphQL execution flow with detailed logging
to trace the complete request/response cycle without any assumptions.

Note: This is adapted for the Pydantic implementation. The msgspec-specific
decoder spies are not applicable here.
"""

import json
import logging
from unittest.mock import patch

import httpx
import pytest
import respx

from stash_graphql_client import StashClient
from stash_graphql_client.types import (
    FindScenesResultType,
)
from tests.fixtures import (
    create_find_scenes_result,
    create_graphql_response,
    create_scene_dict,
)


# Configure logging to TRACE level
logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_scenes_with_comprehensive_spies(
    respx_stash_client: StashClient,
) -> None:
    """Test find_scenes with spy wrappers at execution steps.

    This test traces:
    1. HTTP request/response from respx mock
    2. GQL session.execute call
    3. StashClient.execute call

    All steps are logged with TRACE/DEBUG level detail showing:
    - Input parameters
    - Return values
    - Data transformations

    Note: msgspec-specific decoder spies removed for Pydantic implementation.
    """
    # =========================================================================
    # Setup test data
    # =========================================================================
    scene_data = create_scene_dict(
        id="123",
        title="Test Scene",
    )

    full_response = create_graphql_response(
        "findScenes",
        create_find_scenes_result(
            count=1, scenes=[scene_data], duration=120.5, filesize=1024000
        ),
    )

    print("=" * 80)
    print("SETUP: Full mock response structure:")
    print(json.dumps(full_response, indent=2))
    print("=" * 80)

    # =========================================================================
    # Setup HTTP mock with spy
    # =========================================================================
    http_call_count = 0

    def http_spy(request: httpx.Request) -> httpx.Response:
        nonlocal http_call_count
        http_call_count += 1

        print("=" * 80)
        print(f"HTTP SPY: Call #{http_call_count}")
        print(f"URL: {request.url}")
        print(f"Method: {request.method}")
        print("Request content:")
        req_data = json.loads(request.content)
        print(json.dumps(req_data, indent=2))
        print("-" * 80)
        print("Returning response:")
        print(json.dumps(full_response, indent=2))
        print("=" * 80)

        return httpx.Response(200, json=full_response)

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=http_spy
    )

    # =========================================================================
    # Spy on GQL session.execute
    # =========================================================================
    original_session_execute = respx_stash_client._session.execute
    gql_execute_count = 0

    async def spy_session_execute(operation, *args, **kwargs):
        nonlocal gql_execute_count
        gql_execute_count += 1

        print("=" * 80)
        print(f"GQL SESSION EXECUTE SPY: Call #{gql_execute_count}")
        print(f"Operation: {operation}")
        print(f"Args: {args}")
        print(f"Kwargs: {kwargs}")
        print("-" * 80)

        result = await original_session_execute(operation, *args, **kwargs)

        print("GQL SESSION EXECUTE RESULT:")
        print(f"Type: {type(result)}")
        if isinstance(result, dict):
            print(json.dumps(result, indent=2, default=str))
        else:
            print(f"Value: {result}")
        print("=" * 80)

        return result

    # =========================================================================
    # Spy on StashClient.execute (base.py)
    # =========================================================================
    original_client_execute = respx_stash_client.execute
    client_execute_count = 0

    async def spy_client_execute(
        query: str, variables: dict | None = None, result_type=None
    ):
        nonlocal client_execute_count
        client_execute_count += 1

        print("=" * 80)
        print(f"CLIENT EXECUTE SPY: Call #{client_execute_count}")
        print(f"Query snippet: {query[:100]}...")
        print(f"Variables: {variables}")
        print(f"Result type: {result_type}")
        print("-" * 80)

        # Call original with all parameters
        result = await original_client_execute(query, variables, result_type)

        print("CLIENT EXECUTE RESULT:")
        print(f"Type: {type(result)}")
        if isinstance(result, dict):
            print(f"Dict keys: {list(result.keys())}")
            print(json.dumps(result, indent=2, default=str))
        elif hasattr(result, "__class__"):
            print(f"Object class: {result.__class__.__name__}")
            print(f"Object attrs: {dir(result)}")
            if hasattr(result, "count"):
                print(f"  count={result.count}")
            if hasattr(result, "scenes"):
                print(f"  scenes={result.scenes}")
            if hasattr(result, "duration"):
                print(f"  duration={result.duration}")
            if hasattr(result, "filesize"):
                print(f"  filesize={result.filesize}")
        else:
            print(f"Value: {result}")
        print("=" * 80)

        return result

    # =========================================================================
    # Note: msgspec-specific spies removed for Pydantic implementation
    # =========================================================================
    # The Pydantic implementation doesn't use msgspec.json.encode or
    # StoreAwareDecoder, so those spy points are not applicable here.

    # =========================================================================
    # Apply all patches (Pydantic version - no msgspec/decoder patches)
    # =========================================================================
    with (
        patch.object(respx_stash_client._session, "execute", wraps=spy_session_execute),
        patch.object(respx_stash_client, "execute", wraps=spy_client_execute),
    ):
        # =====================================================
        # Execute the actual test
        # =====================================================
        print("=" * 80)
        print("STARTING TEST EXECUTION")
        print("=" * 80)

        result = await respx_stash_client.find_scenes()

        print("=" * 80)
        print("TEST EXECUTION COMPLETE")
        print("=" * 80)

    # =========================================================================
    # Print call count summary (Pydantic version)
    # =========================================================================
    print("=" * 80)
    print("CALL COUNT SUMMARY:")
    print(f"  HTTP calls: {http_call_count}")
    print(f"  GQL session.execute calls: {gql_execute_count}")
    print(f"  Client.execute calls: {client_execute_count}")
    print("=" * 80)

    # =========================================================================
    # Verify results
    # =========================================================================
    assert result is not None
    assert isinstance(result, FindScenesResultType)
    assert result.count == 1
    assert len(result.scenes) == 1
    assert result.scenes[0].id == "123"
    assert result.scenes[0].title == "Test Scene"
    assert result.duration == 120.5
    assert result.filesize == 1024000

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1

    print("=" * 80)
    print("ALL ASSERTIONS PASSED")
    print("=" * 80)
