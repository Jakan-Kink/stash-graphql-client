"""Integration tests for file mixin functionality.

Tests file and folder operations against a real Stash instance.
"""

import pytest

from stash_graphql_client import StashClient


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_files_returns_results(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding files returns results."""
    async with stash_cleanup_tracker(stash_client, auto_capture=False):
        result = await stash_client.find_files()

        # Should have files from the 45 scenes + 202 images
        assert result.count > 0
        assert len(result.files) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_files_with_pagination(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test file pagination works correctly."""
    async with stash_cleanup_tracker(stash_client, auto_capture=False):
        result = await stash_client.find_files(filter_={"per_page": 10, "page": 1})

        assert len(result.files) <= 10


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_file_by_id(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding a specific file by ID."""
    async with stash_cleanup_tracker(stash_client, auto_capture=False):
        # First get a file ID from the list
        result = await stash_client.find_files(filter_={"per_page": 1})
        if result.count == 0:
            pytest.skip("No files in test Stash instance")

        file_id = result.files[0].id
        file = await stash_client.find_file(file_id)

        assert file is not None
        assert file.id == file_id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_folders_returns_results(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding folders returns results."""
    async with stash_cleanup_tracker(stash_client, auto_capture=False):
        result = await stash_client.find_folders()

        # Should have folders containing the media
        assert result.count > 0
        assert len(result.folders) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_folder_by_id(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding a specific folder by ID."""
    async with stash_cleanup_tracker(stash_client, auto_capture=False):
        result = await stash_client.find_folders(filter_={"per_page": 1})
        if result.count == 0:
            pytest.skip("No folders in test Stash instance")

        folder_id = result.folders[0].id
        folder = await stash_client.find_folder(folder_id)

        assert folder is not None
        assert folder.id == folder_id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_nonexistent_file_returns_none(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding a nonexistent file returns None."""
    async with stash_cleanup_tracker(stash_client, auto_capture=False):
        file = await stash_client.find_file("99999999")

        assert file is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_nonexistent_folder_returns_none(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding a nonexistent folder returns None."""
    async with stash_cleanup_tracker(stash_client, auto_capture=False):
        folder = await stash_client.find_folder("99999999")

        assert folder is None
