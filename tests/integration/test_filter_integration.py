"""Integration tests for filter mixin functionality.

Tests filter operations against a real Stash instance with GraphQL call verification.

These tests cover the core filter CRUD operations including saving, updating,
and destroying saved filters across different filter modes (scenes, performers, etc.).
"""

import uuid

import pytest

from stash_graphql_client import StashClient
from stash_graphql_client.errors import StashGraphQLError
from stash_graphql_client.types import (
    DestroyFilterInput,
    FilterMode,
    FindFilterType,
    SavedFilter,
    SaveFilterInput,
)
from tests.fixtures import capture_graphql_calls


# =============================================================================
# Filter Save/Create Integration Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_save_filter_scenes_mode(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test saving a new filter for scenes mode."""
    async with (
        stash_cleanup_tracker(stash_client) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        # Save a new filter
        unique_name = f"Test Scenes Filter {uuid.uuid4()}"
        input_data = SaveFilterInput(
            mode=FilterMode.SCENES,
            name=unique_name,
        )

        saved_filter = await stash_client.save_filter(input_data)
        cleanup["saved_filters"].append(saved_filter.id)

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for save_filter"
        assert "saveFilter" in calls[0]["query"]
        assert calls[0]["variables"]["input"]["mode"] == "SCENES"
        assert calls[0]["variables"]["input"]["name"] == unique_name
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify saved filter
        assert saved_filter is not None
        assert isinstance(saved_filter, SavedFilter)
        assert saved_filter.id is not None
        assert saved_filter.name == unique_name


@pytest.mark.integration
@pytest.mark.asyncio
async def test_save_filter_performers_mode(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test saving a new filter for performers mode."""
    async with (
        stash_cleanup_tracker(stash_client) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        # Save a new filter
        unique_name = f"Test Performers Filter {uuid.uuid4()}"
        input_data = SaveFilterInput(
            mode=FilterMode.PERFORMERS,
            name=unique_name,
        )

        saved_filter = await stash_client.save_filter(input_data)
        cleanup["saved_filters"].append(saved_filter.id)

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for save_filter"
        assert "saveFilter" in calls[0]["query"]
        assert calls[0]["variables"]["input"]["mode"] == "PERFORMERS"
        assert calls[0]["variables"]["input"]["name"] == unique_name
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify saved filter
        assert saved_filter is not None
        assert isinstance(saved_filter, SavedFilter)
        assert saved_filter.id is not None
        assert saved_filter.name == unique_name


@pytest.mark.integration
@pytest.mark.asyncio
async def test_save_filter_galleries_mode(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test saving a new filter for galleries mode."""
    async with (
        stash_cleanup_tracker(stash_client) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        # Save a new filter
        unique_name = f"Test Galleries Filter {uuid.uuid4()}"
        input_data = SaveFilterInput(
            mode=FilterMode.GALLERIES,
            name=unique_name,
        )

        saved_filter = await stash_client.save_filter(input_data)
        cleanup["saved_filters"].append(saved_filter.id)

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for save_filter"
        assert "saveFilter" in calls[0]["query"]
        assert calls[0]["variables"]["input"]["mode"] == "GALLERIES"
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify saved filter
        assert saved_filter is not None
        assert saved_filter.name == unique_name


@pytest.mark.integration
@pytest.mark.asyncio
async def test_save_filter_with_dict_input(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test saving a filter using dictionary input instead of SaveFilterInput."""
    async with (
        stash_cleanup_tracker(stash_client) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        # Save filter using dict
        unique_name = f"Studios Filter via Dict {uuid.uuid4()}"
        input_dict = {
            "mode": FilterMode.STUDIOS,
            "name": unique_name,
        }

        saved_filter = await stash_client.save_filter(input_dict)
        cleanup["saved_filters"].append(saved_filter.id)

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for save_filter"
        assert "saveFilter" in calls[0]["query"]
        assert calls[0]["variables"]["input"]["mode"] == "STUDIOS"
        assert calls[0]["variables"]["input"]["name"] == unique_name
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify result
        assert saved_filter is not None
        assert saved_filter.id is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_save_filter_with_find_filter(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test saving a filter with find_filter parameters."""
    async with (
        stash_cleanup_tracker(stash_client) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        # Save filter with find_filter options
        unique_name = f"Scenes Filter with Pagination {uuid.uuid4()}"
        input_data = SaveFilterInput(
            mode=FilterMode.SCENES,
            name=unique_name,
            find_filter=FindFilterType(per_page=50, page=1),
        )

        saved_filter = await stash_client.save_filter(input_data)
        cleanup["saved_filters"].append(saved_filter.id)

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for save_filter"
        assert "saveFilter" in calls[0]["query"]
        assert calls[0]["variables"]["input"]["find_filter"]["per_page"] == 50
        assert calls[0]["variables"]["input"]["find_filter"]["page"] == 1
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify result
        assert saved_filter is not None
        assert saved_filter.id is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_save_filter_with_object_filter(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test saving a filter with object_filter parameters."""
    async with (
        stash_cleanup_tracker(stash_client) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        # Save filter with object_filter options
        unique_name = f"Organized Scenes Filter {uuid.uuid4()}"
        input_data = SaveFilterInput(
            mode=FilterMode.SCENES,
            name=unique_name,
            object_filter={"organized": True},
        )

        saved_filter = await stash_client.save_filter(input_data)
        cleanup["saved_filters"].append(saved_filter.id)

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for save_filter"
        assert "saveFilter" in calls[0]["query"]
        assert calls[0]["variables"]["input"]["object_filter"]["organized"] is True
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify result
        assert saved_filter is not None
        assert saved_filter.id is not None


# =============================================================================
# Filter Update Integration Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_save_filter_update_existing(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test updating an existing filter by providing an id."""
    async with (
        stash_cleanup_tracker(stash_client) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        # Create initial filter
        original_name = f"Original Filter Name {uuid.uuid4()}"
        input_data = SaveFilterInput(
            mode=FilterMode.SCENES,
            name=original_name,
        )

        created_filter = await stash_client.save_filter(input_data)
        cleanup["saved_filters"].append(created_filter.id)
        filter_id = created_filter.id

        # Verify creation
        assert len(calls) == 1
        assert "saveFilter" in calls[0]["query"]
        calls.clear()

        # Update the filter by providing id
        updated_name = f"Updated Filter Name {uuid.uuid4()}"
        update_data = SaveFilterInput(
            id=filter_id,
            mode=FilterMode.SCENES,
            name=updated_name,
        )

        updated_filter = await stash_client.save_filter(update_data)

        # Verify update call
        assert len(calls) == 1, "Expected 1 GraphQL call for filter update"
        assert "saveFilter" in calls[0]["query"]
        assert calls[0]["variables"]["input"]["id"] == filter_id
        assert calls[0]["variables"]["input"]["name"] == updated_name
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify updated filter
        assert updated_filter.id == filter_id
        assert updated_filter.name == updated_name


@pytest.mark.integration
@pytest.mark.asyncio
async def test_save_filter_update_with_ui_options(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test updating filter ui_options."""
    async with (
        stash_cleanup_tracker(stash_client) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        # Create initial filter
        unique_name = f"Filter with UI Options {uuid.uuid4()}"
        input_data = SaveFilterInput(
            mode=FilterMode.PERFORMERS,
            name=unique_name,
            ui_options={"display_mode": "grid"},
        )

        created_filter = await stash_client.save_filter(input_data)
        cleanup["saved_filters"].append(created_filter.id)
        filter_id = created_filter.id

        calls.clear()

        # Update ui_options
        update_data = SaveFilterInput(
            id=filter_id,
            mode=FilterMode.PERFORMERS,
            name=unique_name,
            ui_options={"display_mode": "list", "sort_by": "name"},
        )

        updated_filter = await stash_client.save_filter(update_data)

        # Verify update call
        assert len(calls) == 1, "Expected 1 GraphQL call for ui_options update"
        assert "saveFilter" in calls[0]["query"]
        assert calls[0]["variables"]["input"]["ui_options"]["display_mode"] == "list"
        assert calls[0]["variables"]["input"]["ui_options"]["sort_by"] == "name"
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify result
        assert updated_filter.id == filter_id


# =============================================================================
# Filter Destroy/Delete Integration Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_destroy_saved_filter(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test destroying a saved filter."""
    async with (
        stash_cleanup_tracker(stash_client) as _,
        capture_graphql_calls(stash_client) as calls,
    ):
        # Create a filter to destroy
        unique_name = f"Filter to be destroyed {uuid.uuid4()}"
        input_data = SaveFilterInput(
            mode=FilterMode.IMAGES,
            name=unique_name,
        )

        created_filter = await stash_client.save_filter(input_data)
        filter_id = created_filter.id

        # Verify creation
        assert len(calls) == 1
        calls.clear()

        # Destroy the filter
        destroy_input = DestroyFilterInput(id=filter_id)
        success = await stash_client.destroy_saved_filter(destroy_input)

        # Verify destroy call
        assert len(calls) == 1, "Expected 1 GraphQL call for destroy_saved_filter"
        assert "destroySavedFilter" in calls[0]["query"]
        assert calls[0]["variables"]["input"]["id"] == filter_id
        assert calls[0]["exception"] is None

        # Verify destruction
        assert success is True
        # Note: We don't add to cleanup since it's destroyed


@pytest.mark.integration
@pytest.mark.asyncio
async def test_destroy_saved_filter_with_dict(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test destroying a filter using dictionary input."""
    async with (
        stash_cleanup_tracker(stash_client) as _,
        capture_graphql_calls(stash_client) as calls,
    ):
        # Create a filter to destroy
        unique_name = f"Filter to destroy via dict {uuid.uuid4()}"
        input_data = SaveFilterInput(
            mode=FilterMode.TAGS,
            name=unique_name,
        )

        created_filter = await stash_client.save_filter(input_data)
        filter_id = created_filter.id

        calls.clear()

        # Destroy using dict
        success = await stash_client.destroy_saved_filter({"id": filter_id})

        # Verify destroy call
        assert len(calls) == 1, "Expected 1 GraphQL call for destroy_saved_filter"
        assert "destroySavedFilter" in calls[0]["query"]
        assert calls[0]["variables"]["input"]["id"] == filter_id
        assert calls[0]["exception"] is None

        # Verify destruction
        assert success is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_destroy_nonexistent_filter_raises_error(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test destroying a nonexistent filter raises an error."""
    async with (
        stash_cleanup_tracker(stash_client),
        capture_graphql_calls(stash_client) as calls,
    ):
        # Try to destroy a filter that doesn't exist
        destroy_input = DestroyFilterInput(id="99999999")

        # Should raise an error since the filter doesn't exist
        with pytest.raises(StashGraphQLError):
            await stash_client.destroy_saved_filter(destroy_input)

        # Verify destroy call was attempted
        assert len(calls) == 1, "Expected 1 GraphQL call for destroy_saved_filter"
        assert "destroySavedFilter" in calls[0]["query"]
        assert calls[0]["exception"] is not None  # Error was captured


# =============================================================================
# Filter Multi-Mode Integration Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_save_filters_multiple_modes(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test creating filters for multiple different modes."""
    async with (
        stash_cleanup_tracker(stash_client) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        # Save filters for different modes
        modes_to_test = [
            (FilterMode.SCENES, f"Scenes Filter {uuid.uuid4()}"),
            (FilterMode.PERFORMERS, f"Performers Filter {uuid.uuid4()}"),
            (FilterMode.GALLERIES, f"Galleries Filter {uuid.uuid4()}"),
            (FilterMode.TAGS, f"Tags Filter {uuid.uuid4()}"),
        ]

        for mode, name in modes_to_test:
            input_data = SaveFilterInput(mode=mode, name=name)
            saved_filter = await stash_client.save_filter(input_data)
            cleanup["saved_filters"].append(saved_filter.id)

        # Verify all calls were made
        assert len(calls) == 4, "Expected 4 GraphQL calls for 4 filters"

        # Verify each call
        for i, (mode, name) in enumerate(modes_to_test):
            assert "saveFilter" in calls[i]["query"]
            assert calls[i]["variables"]["input"]["mode"] == mode.value
            assert calls[i]["variables"]["input"]["name"] == name
            assert calls[i]["result"] is not None
            assert calls[i]["exception"] is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_save_update_destroy_filter_lifecycle(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test complete filter lifecycle: save, update, and destroy."""
    async with (
        stash_cleanup_tracker(stash_client) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        # 1. Create filter
        original_name = f"Lifecycle Test Filter {uuid.uuid4()}"
        input_data = SaveFilterInput(
            mode=FilterMode.SCENES,
            name=original_name,
        )

        created_filter = await stash_client.save_filter(input_data)
        filter_id = created_filter.id
        cleanup["saved_filters"].append(filter_id)

        # Verify creation
        assert len(calls) == 1
        assert "saveFilter" in calls[0]["query"]
        calls.clear()

        # 2. Update filter
        updated_name = f"Updated Lifecycle Filter {uuid.uuid4()}"
        update_data = SaveFilterInput(
            id=filter_id,
            mode=FilterMode.SCENES,
            name=updated_name,
        )

        updated_filter = await stash_client.save_filter(update_data)

        # Verify update
        assert len(calls) == 1
        assert "saveFilter" in calls[0]["query"]
        assert updated_filter.name == updated_name
        calls.clear()

        # 3. Destroy filter
        destroy_input = DestroyFilterInput(id=filter_id)
        success = await stash_client.destroy_saved_filter(destroy_input)

        # Verify destruction
        assert len(calls) == 1
        assert "destroySavedFilter" in calls[0]["query"]
        assert success is True
        cleanup["saved_filters"].remove(filter_id)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_save_multiple_filters_same_mode(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test creating multiple filters for the same mode."""
    async with (
        stash_cleanup_tracker(stash_client) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        # Create multiple filters for the same mode
        filter_names = [
            f"Scenes Filter 1 {uuid.uuid4()}",
            f"Scenes Filter 2 {uuid.uuid4()}",
            f"Scenes Filter 3 {uuid.uuid4()}",
        ]

        for name in filter_names:
            input_data = SaveFilterInput(mode=FilterMode.SCENES, name=name)
            saved_filter = await stash_client.save_filter(input_data)
            cleanup["saved_filters"].append(saved_filter.id)

        # Verify all calls were made
        assert len(calls) == 3, "Expected 3 GraphQL calls for 3 filters"

        # Verify each call
        for i, name in enumerate(filter_names):
            assert "saveFilter" in calls[i]["query"]
            assert calls[i]["variables"]["input"]["mode"] == "SCENES"
            assert calls[i]["variables"]["input"]["name"] == name
            assert calls[i]["result"] is not None
            assert calls[i]["exception"] is None
