"""Integration tests for tag mixin functionality.

Tests tag operations against a real Stash instance.
"""

import pytest

from stash_graphql_client import StashClient
from stash_graphql_client.types import Tag
from stash_graphql_client.types.unset import is_set
from tests.fixtures import capture_graphql_calls


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_tags_returns_results(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding tags returns results (may be empty)."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        result = await stash_client.find_tags()

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_tags"
        assert "findTags" in calls[0]["query"]
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Result should be valid even if empty
        assert result.count >= 0
        assert isinstance(result.tags, list)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_tags_with_pagination(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test tag pagination works correctly."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        result = await stash_client.find_tags(filter_={"per_page": 10, "page": 1})

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_tags"
        assert "findTags" in calls[0]["query"]
        assert calls[0]["variables"]["filter"]["per_page"] == 10
        assert calls[0]["variables"]["filter"]["page"] == 1
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify response
        assert len(result.tags) <= 10


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_nonexistent_tag_returns_none(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding a nonexistent tag returns None."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        tag = await stash_client.find_tag("99999999")

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_tag"
        assert "findTag" in calls[0]["query"]
        assert calls[0]["variables"]["id"] == "99999999"
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Verify response
        assert tag is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_tags_with_q_parameter(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test finding tags using q search parameter."""
    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False),
        capture_graphql_calls(stash_client) as calls,
    ):
        result = await stash_client.find_tags(q="test")

        # Verify GraphQL call
        assert len(calls) == 1, "Expected 1 GraphQL call for find_tags"
        assert "findTags" in calls[0]["query"]
        # q parameter is added to filter dict
        assert calls[0]["variables"]["filter"]["q"] == "test"
        assert calls[0]["result"] is not None
        assert calls[0]["exception"] is None

        # Should return valid result (may or may not have matches)
        assert result.count >= 0
        assert isinstance(result.tags, list)


# =============================================================================
# Tag mutation lifecycle tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="tag_mutations")
async def test_create_and_find_tag(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test creating a tag and retrieving it by ID."""
    async with (
        stash_cleanup_tracker(stash_client),
        capture_graphql_calls(stash_client) as calls,
    ):
        tag = await stash_client.create_tag(Tag(name="sgc-inttest-create"))

        assert len(calls) == 1, "Expected 1 GraphQL call for create_tag"
        assert "tagCreate" in calls[0]["query"]
        assert calls[0]["exception"] is None

        assert tag.id is not None
        assert is_set(tag.name)
        assert tag.name == "sgc-inttest-create"

        calls.clear()

        found = await stash_client.find_tag(tag.id)

        assert len(calls) == 1, "Expected 1 GraphQL call for find_tag"
        assert "findTag" in calls[0]["query"]
        assert calls[0]["exception"] is None

        assert found is not None
        assert found.id == tag.id
        assert found.name == "sgc-inttest-create"


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="tag_mutations")
async def test_update_tag(stash_client: StashClient, stash_cleanup_tracker) -> None:
    """Test creating a tag and updating its description."""
    async with (
        stash_cleanup_tracker(stash_client),
        capture_graphql_calls(stash_client) as calls,
    ):
        tag = await stash_client.create_tag(Tag(name="sgc-inttest-update"))
        assert tag.id is not None

        calls.clear()

        tag.description = "integration test description"
        updated = await stash_client.update_tag(tag)

        assert len(calls) == 1, "Expected 1 GraphQL call for update_tag"
        assert "tagUpdate" in calls[0]["query"]
        assert calls[0]["exception"] is None

        assert updated.id == tag.id
        assert is_set(updated.description)
        assert updated.description == "integration test description"


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="tag_mutations")
async def test_tag_destroy(stash_client: StashClient, stash_cleanup_tracker) -> None:
    """Test creating a tag and then destroying it."""
    async with (
        stash_cleanup_tracker(stash_client) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        tag = await stash_client.create_tag(Tag(name="sgc-inttest-destroy"))
        assert tag.id is not None

        calls.clear()

        result = await stash_client.tag_destroy({"id": tag.id})

        assert len(calls) == 1, "Expected 1 GraphQL call for tag_destroy"
        assert "tagDestroy" in calls[0]["query"]
        assert calls[0]["exception"] is None
        assert result is True

        # Remove from cleanup so the tracker doesn't attempt a double-delete
        cleanup["tags"].remove(tag.id)

        calls.clear()

        # Confirm the tag is gone
        gone = await stash_client.find_tag(tag.id)
        assert gone is None


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="tag_mutations")
async def test_tags_destroy_bulk(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test bulk-destroying multiple tags in a single call."""
    async with (
        stash_cleanup_tracker(stash_client) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        tag_a = await stash_client.create_tag(Tag(name="sgc-inttest-bulk-destroy-a"))
        tag_b = await stash_client.create_tag(Tag(name="sgc-inttest-bulk-destroy-b"))
        assert tag_a.id is not None
        assert tag_b.id is not None

        calls.clear()

        result = await stash_client.tags_destroy([tag_a.id, tag_b.id])

        assert len(calls) == 1, "Expected 1 GraphQL call for tags_destroy"
        assert "tagsDestroy" in calls[0]["query"]
        assert calls[0]["exception"] is None
        assert result is True

        # Remove from cleanup — already destroyed
        cleanup["tags"].remove(tag_a.id)
        cleanup["tags"].remove(tag_b.id)


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="tag_mutations")
async def test_bulk_tag_update(
    stash_client: StashClient, stash_cleanup_tracker
) -> None:
    """Test updating multiple tags' description in a single bulk call."""
    async with (
        stash_cleanup_tracker(stash_client),
        capture_graphql_calls(stash_client) as calls,
    ):
        tag_a = await stash_client.create_tag(Tag(name="sgc-inttest-bulk-update-a"))
        tag_b = await stash_client.create_tag(Tag(name="sgc-inttest-bulk-update-b"))
        assert tag_a.id is not None
        assert tag_b.id is not None

        calls.clear()

        updated_tags = await stash_client.bulk_tag_update(
            ids=[tag_a.id, tag_b.id],
            description="bulk-updated",
        )

        assert len(calls) == 1, "Expected 1 GraphQL call for bulk_tag_update"
        assert "bulkTagUpdate" in calls[0]["query"]
        assert calls[0]["exception"] is None

        assert len(updated_tags) == 2
        for t in updated_tags:
            assert is_set(t.description)
            assert t.description == "bulk-updated"


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="tag_mutations")
async def test_tags_merge(stash_client: StashClient, stash_cleanup_tracker) -> None:
    """Test merging a source tag into a destination tag."""
    async with (
        stash_cleanup_tracker(stash_client) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        source = await stash_client.create_tag(Tag(name="sgc-inttest-merge-source"))
        dest = await stash_client.create_tag(Tag(name="sgc-inttest-merge-dest"))
        assert source.id is not None
        assert dest.id is not None

        calls.clear()

        merged = await stash_client.tags_merge(
            source=[source.id],
            destination=dest.id,
        )

        assert len(calls) == 1, "Expected 1 GraphQL call for tags_merge"
        assert "tagsMerge" in calls[0]["query"]
        assert calls[0]["exception"] is None

        assert merged.id == dest.id

        # The source tag is consumed by the merge — remove from cleanup
        cleanup["tags"].remove(source.id)
