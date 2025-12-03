"""Test configuration and fixtures for StashClient tests."""

import contextlib
import warnings
from collections.abc import AsyncGenerator, AsyncIterator
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest_asyncio
import respx

from stash_graphql_client import StashClient
from stash_graphql_client.context import StashContext


__all__ = [
    "stash_context",
    "stash_client",
    "respx_stash_client",
    "stash_cleanup_tracker",
    "mock_ws_transport",
    "mock_gql_ws_connect",
]


class StashCleanupWarning(UserWarning):
    """Warning issued when stash_cleanup_tracker encounters issues."""


@pytest_asyncio.fixture
async def mock_ws_transport():
    """Mock the WebsocketsTransport to avoid real websocket connections.

    This fixture patches the WebsocketsTransport class used by StashClient
    to prevent actual websocket connection attempts during testing.

    Yields:
        MagicMock: The mocked WebsocketsTransport class
    """
    with patch("stash_graphql_client.client.base.WebsocketsTransport") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_class


@pytest_asyncio.fixture
async def mock_gql_ws_connect():
    """Mock the GQL client's connect_async for websocket connections.

    This fixture patches the gql.Client.connect_async method to return
    a mock session, preventing actual connection attempts.

    Yields:
        AsyncMock: The mocked connect_async method
    """
    with patch("gql.Client.connect_async", new_callable=AsyncMock) as mock:
        mock.return_value = MagicMock()
        yield mock


@pytest_asyncio.fixture
async def stash_context() -> AsyncGenerator[StashContext, None]:
    """Create a StashContext for testing.

    This is a core fixture that provides a configured StashContext for interacting with
    a Stash server. It handles connection setup and cleanup after tests are complete.

    Yields:
        StashContext: A configured context for Stash API interactions
    """
    # Create connection config
    conn = {
        "Scheme": "http",
        "Host": "localhost",
        "Port": 9999,
    }

    context = StashContext(
        conn=conn,
        verify_ssl=False,
    )

    yield context
    await context.close()


@pytest_asyncio.fixture
async def stash_client(
    stash_context: StashContext,
) -> AsyncGenerator[StashClient, None]:
    """Get the StashClient from the StashContext.

    This fixture depends on the stash_context fixture and provides a properly initialized
    StashClient instance. It ensures that the client is created through the context's
    get_client() method and properly cleaned up after tests.

    Args:
        stash_context: The StashContext fixture

    Yields:
        StashClient: An initialized client for Stash API interactions
    """
    client = await stash_context.get_client()
    yield client
    # Ensure we explicitly clean up after each test
    await client.close()


@pytest_asyncio.fixture
async def respx_stash_client(
    stash_context: StashContext,
) -> AsyncGenerator[StashClient, None]:
    """Get a StashClient with respx HTTP mocking enabled.

    This is for unit tests that want to mock HTTP responses to Stash GraphQL API.
    The fixture sets up respx mocking and provides the client within that context.

    Tests using this fixture should set up their own respx routes for specific
    GraphQL responses. The fixture provides a default empty response for any
    unmatched requests.

    Args:
        stash_context: The StashContext fixture

    Yields:
        StashClient: A client with respx mocking enabled

    Example:
        ```python
        @pytest.mark.asyncio
        async def test_find_studio(respx_stash_client):
            # Set up mock response
            respx.post("http://localhost:9999/graphql").mock(
                return_value=httpx.Response(200, json={
                    "data": {"findStudio": {"id": "123", "name": "Test"}}
                })
            )

            # Now the client will use your mocked response
            studio = await respx_stash_client.find_studio("123")
            assert studio.id == "123"
        ```
    """
    with respx.mock:
        # Default response for any unmatched GraphQL requests
        respx.post("http://localhost:9999/graphql").mock(
            return_value=httpx.Response(200, json={"data": {}})
        )

        # Initialize the client (will use mocked HTTP)
        client = await stash_context.get_client()

        yield client

        # Reset respx to prevent route pollution
        respx.reset()

        # Close the client
        await client.close()


@pytest_asyncio.fixture
async def stash_cleanup_tracker():
    """Fixture that provides a cleanup context manager for Stash objects.

    IMPORTANT: Any test using stash_client MUST also use stash_cleanup_tracker.
    This requirement is enforced automatically via pytest hook. Tests that use
    stash_client without stash_cleanup_tracker will fail with strict xfail.

    This fixture helps ensure test isolation by providing a context manager that
    automatically cleans up any Stash objects created during tests. It tracks objects
    by their IDs and deletes them in the correct order to handle dependencies.

    Returns:
        async_context_manager: A context manager for tracking and cleaning up Stash objects

    Usage:
        ```python
        async def test_something(stash_client, stash_cleanup_tracker):
            async with stash_cleanup_tracker(stash_client) as cleanup:
                # Create test objects
                performer = await stash_client.create_performer(...)
                cleanup['performers'].append(performer.id)

                # Create more objects that depend on performer
                scene = await stash_client.create_scene(...)
                cleanup['scenes'].append(scene.id)

                # Test logic here...

                # Cleanup happens automatically when exiting the context
        ```
    """

    @contextlib.asynccontextmanager
    async def cleanup_context(
        client: StashClient,
        auto_capture: bool = True,
    ) -> AsyncIterator[dict[str, list[str]]]:
        """Context manager for tracking and cleaning up Stash objects.

        Args:
            client: StashClient instance to track
            auto_capture: If True, automatically capture IDs from create mutations.
                         If False, require manual tracking via cleanup[type].append(id).
                         Default True for convenience, set False for performance.
        """
        created_objects: dict[str, list[str]] = {
            "scenes": [],
            "performers": [],
            "studios": [],
            "tags": [],
            "galleries": [],
            "markers": [],
            "groups": [],
        }
        capture_mode = "with auto-capture" if auto_capture else "manual tracking"
        print(f"\n{'=' * 60}")
        print(f"CLEANUP TRACKER: Context entered ({capture_mode})")
        print(f"{'=' * 60}")

        if auto_capture:
            original_execute = client._session.execute

            async def execute_with_capture(document, *args, **kwargs):
                """Execute GraphQL and auto-capture created object IDs."""
                result = await original_execute(document, *args, **kwargs)

                # Quick check - only process if result is a dict and has data
                if not (result and isinstance(result, dict)):
                    return result

                # Fast string check: only inspect if result contains "Create" mutations
                result_keys = result.keys()
                has_create = any("Create" in key for key in result_keys)
                if not has_create:
                    return result

                # Check specific create mutations
                if "sceneCreate" in result:
                    if (
                        (obj_data := result["sceneCreate"])
                        and (scene_id := obj_data.get("id"))
                        and scene_id not in created_objects["scenes"]
                    ):
                        created_objects["scenes"].append(scene_id)
                elif "performerCreate" in result:
                    if (
                        (obj_data := result["performerCreate"])
                        and (performer_id := obj_data.get("id"))
                        and performer_id not in created_objects["performers"]
                    ):
                        created_objects["performers"].append(performer_id)
                elif "studioCreate" in result:
                    if (
                        (obj_data := result["studioCreate"])
                        and (studio_id := obj_data.get("id"))
                        and studio_id not in created_objects["studios"]
                    ):
                        created_objects["studios"].append(studio_id)
                elif "tagCreate" in result:
                    if (
                        (obj_data := result["tagCreate"])
                        and (tag_id := obj_data.get("id"))
                        and tag_id not in created_objects["tags"]
                    ):
                        created_objects["tags"].append(tag_id)
                elif "galleryCreate" in result:
                    if (
                        (obj_data := result["galleryCreate"])
                        and (gallery_id := obj_data.get("id"))
                        and gallery_id not in created_objects["galleries"]
                    ):
                        created_objects["galleries"].append(gallery_id)
                elif "sceneMarkerCreate" in result:
                    if (
                        (obj_data := result["sceneMarkerCreate"])
                        and (marker_id := obj_data.get("id"))
                        and marker_id not in created_objects["markers"]
                    ):
                        created_objects["markers"].append(marker_id)
                elif "groupCreate" in result and (
                    (obj_data := result["groupCreate"])
                    and (group_id := obj_data.get("id"))
                    and group_id not in created_objects["groups"]
                ):
                    created_objects["groups"].append(group_id)

                return result

        # Use patch.object for safer patching with automatic cleanup
        try:
            if auto_capture:
                with patch.object(client._session, "execute", execute_with_capture):
                    yield created_objects
            else:
                # No patching - manual tracking only
                yield created_objects
        finally:
            print(f"\n{'=' * 60}")
            print("CLEANUP TRACKER: Finally block entered")
            print("CLEANUP TRACKER: Objects to clean up:")
            for obj_type, ids in created_objects.items():
                if ids:
                    print(f"  - {obj_type}: {ids}")
            print(f"{'=' * 60}\n")

            # Warn about auto-captured objects
            if auto_capture and any(created_objects.values()):
                tracked_items = []
                for obj_type, ids in created_objects.items():
                    if ids:
                        tracked_items.append(f"  - {obj_type}: {ids}")

                if tracked_items:
                    warning_msg = "Auto-captured objects:\n" + "\n".join(tracked_items)
                    warnings.warn(
                        warning_msg,
                        StashCleanupWarning,
                        stacklevel=3,
                    )

            # Clean up created objects in correct dependency order
            # Markers reference scenes - delete first
            # Galleries reference scenes/performers/studios/tags - delete second
            # Scenes reference performers/studios/tags - delete third
            # Performers/Studios/Tags have no cross-dependencies - delete last
            errors = []

            try:
                # Delete markers first (they reference scenes)
                for marker_id in created_objects["markers"]:
                    try:
                        await client.execute(
                            """
                            mutation DeleteMarker($id: ID!) {
                                sceneMarkerDestroy(id: $id)
                            }
                            """,
                            {"id": marker_id},
                        )
                    except Exception as e:
                        errors.append(f"Marker {marker_id}: {e}")

                # Delete galleries second (they can reference scenes)
                for gallery_id in created_objects["galleries"]:
                    try:
                        await client.execute(
                            """
                            mutation DeleteGallery($id: ID!) {
                                galleryDestroy(input: { ids: [$id] })
                            }
                            """,
                            {"id": gallery_id},
                        )
                    except Exception as e:
                        errors.append(f"Gallery {gallery_id}: {e}")

                # Delete scenes third (they reference performers/studios/tags)
                for scene_id in created_objects["scenes"]:
                    try:
                        await client.execute(
                            """
                            mutation DeleteScene($id: ID!) {
                                sceneDestroy(input: { id: $id })
                            }
                            """,
                            {"id": scene_id},
                        )
                    except Exception as e:
                        errors.append(f"Scene {scene_id}: {e}")

                # Delete groups (they reference studios/tags)
                for group_id in created_objects["groups"]:
                    try:
                        await client.execute(
                            """
                            mutation DeleteGroup($id: ID!) {
                                groupDestroy(input: { id: $id })
                            }
                            """,
                            {"id": group_id},
                        )
                    except Exception as e:
                        errors.append(f"Group {group_id}: {e}")

                # Delete performers
                for performer_id in created_objects["performers"]:
                    try:
                        await client.execute(
                            """
                            mutation DeletePerformer($id: ID!) {
                                performerDestroy(input: { id: $id })
                            }
                            """,
                            {"id": performer_id},
                        )
                    except Exception as e:
                        errors.append(f"Performer {performer_id}: {e}")

                # Delete studios
                for studio_id in created_objects["studios"]:
                    try:
                        await client.execute(
                            """
                            mutation DeleteStudio($id: ID!) {
                                studioDestroy(input: { id: $id })
                            }
                            """,
                            {"id": studio_id},
                        )
                    except Exception as e:
                        errors.append(f"Studio {studio_id}: {e}")

                # Delete tags
                for tag_id in created_objects["tags"]:
                    try:
                        await client.execute(
                            """
                            mutation DeleteTag($id: ID!) {
                                tagDestroy(input: { id: $id })
                            }
                            """,
                            {"id": tag_id},
                        )
                    except Exception as e:
                        errors.append(f"Tag {tag_id}: {e}")

                # Report any errors that occurred
                if errors:
                    error_msg = f"Cleanup had {len(errors)} error(s):\n" + "\n".join(
                        f"  - {error}" for error in errors
                    )
                    print(f"Warning: {error_msg}")

                    warnings.warn(
                        f"stash_cleanup_tracker: {error_msg}",
                        StashCleanupWarning,
                        stacklevel=3,
                    )
                else:
                    print("CLEANUP TRACKER: All objects deleted successfully")
            except Exception as e:
                error_msg = f"Cleanup failed catastrophically: {e}"
                print(f"Warning: {error_msg}")
                warnings.warn(
                    f"stash_cleanup_tracker: {error_msg}",
                    StashCleanupWarning,
                    stacklevel=3,
                )

            print(f"\n{'=' * 60}")
            print("CLEANUP TRACKER: Finally block completed")
            print(f"{'=' * 60}\n")

    return cleanup_context
