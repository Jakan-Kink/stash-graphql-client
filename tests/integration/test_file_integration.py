"""Integration tests for file mixin functionality.

Tests file and folder operations against a real Stash instance.
"""

import pytest

from stash_graphql_client import StashClient
from stash_graphql_client.errors import StashGraphQLError
from tests.fixtures import capture_graphql_calls


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_files_returns_results(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding files returns results."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        result = await stash_client.find_files()
        if result.count == 0:
            pytest.skip("No files in test Stash instance")

        assert result.count > 0
        assert len(result.files) > 0

        # Verify GraphQL call
        assert len(calls) == 1
        assert "findFiles" in calls[0]["query"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_files_with_pagination(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test file pagination works correctly."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        result = await stash_client.find_files(filter_={"per_page": 10, "page": 1})

        assert len(result.files) <= 10

        # Verify GraphQL call
        assert len(calls) == 1
        assert "findFiles" in calls[0]["query"]
        assert calls[0]["variables"]["filter"]["per_page"] == 10
        assert calls[0]["variables"]["filter"]["page"] == 1
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_file_by_id(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding a specific file by ID."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        # First get a file ID from the list
        result = await stash_client.find_files(filter_={"per_page": 1})
        if result.count == 0:
            pytest.skip("No files in test Stash instance")

        # Verify first GraphQL call
        assert len(calls) == 1
        assert "findFiles" in calls[0]["query"]
        assert calls[0]["variables"]["filter"]["per_page"] == 1
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        file_id = result.files[0].id
        calls.clear()

        file = await stash_client.find_file(file_id)

        assert file is not None
        assert file.id == file_id

        # Verify second GraphQL call
        assert len(calls) == 1
        assert "findFile" in calls[0]["query"]
        assert calls[0]["variables"]["id"] == file_id
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_folders_returns_results(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding folders returns results."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        result = await stash_client.find_folders()
        if result.count == 0:
            pytest.skip("No files in test Stash instance")

        assert result.count > 0
        assert len(result.folders) > 0

        # Verify GraphQL call
        assert len(calls) == 1
        assert "findFolders" in calls[0]["query"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_folder_by_id(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding a specific folder by ID."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        result = await stash_client.find_folders(filter_={"per_page": 1})
        if result.count == 0:
            pytest.skip("No folders in test Stash instance")

        # Verify first GraphQL call
        assert len(calls) == 1
        assert "findFolders" in calls[0]["query"]
        assert calls[0]["variables"]["filter"]["per_page"] == 1
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        folder_id = result.folders[0].id
        calls.clear()

        folder = await stash_client.find_folder(folder_id)

        assert folder is not None
        assert folder.id == folder_id

        # Verify second GraphQL call
        assert len(calls) == 1
        assert "findFolder" in calls[0]["query"]
        assert calls[0]["variables"]["id"] == folder_id
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_nonexistent_file_returns_none(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding a nonexistent file returns None."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        file = await stash_client.find_file("99999999")

        assert file is None

        # Verify GraphQL call
        assert len(calls) == 1
        assert "findFile" in calls[0]["query"]
        assert calls[0]["variables"]["id"] == "99999999"
        # Exception is expected for nonexistent file
        assert calls[0]["exception"] is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_nonexistent_folder_returns_none(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding a nonexistent folder returns None."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        folder = await stash_client.find_folder("99999999")

        assert folder is None

        # Verify GraphQL call
        assert len(calls) == 1
        assert "findFolder" in calls[0]["query"]
        assert calls[0]["variables"]["id"] == "99999999"
        # Exception is expected for nonexistent folder
        assert calls[0]["exception"] is not None


# =============================================================================
# Mutation-gated file operations
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_reveal_file_in_file_manager(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test that revealFileInFileManager sends the correct mutation.

    Requires has_reveal_file_in_file_manager capability. If present, calls the
    mutation against a real file ID. The server triggers an OS file-manager reveal
    and returns True regardless of desktop availability, so we only verify the
    round-trip succeeds.
    """
    if not stash_client._capabilities.has_mutation("revealFileInFileManager"):
        pytest.skip("Server does not support revealFileInFileManager")

    async with (
        stash_cleanup_tracker(stash_client),
        capture_graphql_calls(stash_client) as calls,
    ):
        result = await stash_client.find_files(filter_={"per_page": 1})
        if result.count == 0:
            pytest.skip("No files in test Stash instance")

        file_id = result.files[0].id
        calls.clear()

        try:
            outcome = await stash_client.reveal_file_in_file_manager(file_id)
        except StashGraphQLError as e:
            if "access denied" in str(e).lower():
                pytest.skip("Server denied revealFileInFileManager (headless/Docker)")
            raise

        assert len(calls) == 1, (
            "Expected 1 GraphQL call for reveal_file_in_file_manager"
        )
        assert "revealFileInFileManager" in calls[0]["query"]
        assert calls[0]["variables"]["id"] == file_id
        assert calls[0]["exception"] is None
        assert isinstance(outcome, bool)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_reveal_folder_in_file_manager(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test that revealFolderInFileManager sends the correct mutation.

    Requires has_reveal_folder_in_file_manager capability. If present, calls the
    mutation against a real folder ID. The server triggers an OS file-manager reveal
    and returns True regardless of desktop availability, so we only verify the
    round-trip succeeds.
    """
    if not stash_client._capabilities.has_mutation("revealFolderInFileManager"):
        pytest.skip("Server does not support revealFolderInFileManager")

    async with (
        stash_cleanup_tracker(stash_client),
        capture_graphql_calls(stash_client) as calls,
    ):
        result = await stash_client.find_folders(filter_={"per_page": 1})
        if result.count == 0:
            pytest.skip("No folders in test Stash instance")

        folder_id = result.folders[0].id
        calls.clear()

        try:
            outcome = await stash_client.reveal_folder_in_file_manager(folder_id)
        except StashGraphQLError as e:
            if "access denied" in str(e).lower():
                pytest.skip("Server denied revealFolderInFileManager (headless/Docker)")
            raise

        assert len(calls) == 1, (
            "Expected 1 GraphQL call for reveal_folder_in_file_manager"
        )
        assert "revealFolderInFileManager" in calls[0]["query"]
        assert calls[0]["variables"]["id"] == folder_id
        assert calls[0]["exception"] is None
        assert isinstance(outcome, bool)
