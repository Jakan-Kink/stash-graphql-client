"""Unit tests for GalleryClientMixin.

These tests mock at the HTTP boundary using respx, allowing real code execution
through the entire GraphQL client stack including serialization/deserialization.
"""

import json

import httpx
import pytest
import respx

from stash_graphql_client import StashClient
from stash_graphql_client.errors import StashGraphQLError
from stash_graphql_client.types import (
    BulkGalleryUpdateInput,
    BulkUpdateIdMode,
    BulkUpdateIds,
    Gallery,
)
from stash_graphql_client.types.unset import is_set
from tests.fixtures import (
    create_find_galleries_result,
    create_gallery_dict,
    create_graphql_response,
    create_performer_dict,
    create_studio_dict,
    create_tag_dict,
    dump_graphql_calls,
)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_gallery(respx_stash_client: StashClient) -> None:
    """Test finding a gallery by ID."""
    gallery_data = create_gallery_dict(
        id="123",
        title="Test Gallery",
        code="GALLERY-001",
        urls=["https://example.com/gallery"],
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("findGallery", gallery_data)
            )
        ]
    )

    try:
        gallery = await respx_stash_client.find_gallery("123")
    finally:
        dump_graphql_calls(graphql_route.calls)

    # Verify the result
    assert gallery is not None
    assert gallery.id == "123"
    assert gallery.title == "Test Gallery"
    assert gallery.code == "GALLERY-001"
    assert gallery.urls == ["https://example.com/gallery"]

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "findGallery" in req["query"]
    assert req["variables"]["id"] == "123"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_gallery_not_found(respx_stash_client: StashClient) -> None:
    """Test finding a gallery that doesn't exist."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("findGallery", None))
        ]
    )

    try:
        gallery = await respx_stash_client.find_gallery("999")
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert gallery is None

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_gallery_error_returns_none(respx_stash_client: StashClient) -> None:
    """Test handling errors when finding a gallery returns None."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(500, json={"errors": [{"message": "Test error"}]})]
    )

    try:
        gallery = await respx_stash_client.find_gallery("error_gallery")
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert gallery is None

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_galleries(respx_stash_client: StashClient) -> None:
    """Test finding galleries with filters."""
    gallery_data = create_gallery_dict(
        id="123",
        title="Test Gallery",
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findGalleries",
                    create_find_galleries_result(count=1, galleries=[gallery_data]),
                ),
            )
        ]
    )

    try:
        result = await respx_stash_client.find_galleries()
    finally:
        dump_graphql_calls(graphql_route.calls)

    # Verify the results
    assert result.count == 1
    assert len(result.galleries) == 1
    assert result.galleries[0].id == "123"
    assert result.galleries[0].title == "Test Gallery"

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "findGalleries" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_galleries_empty(respx_stash_client: StashClient) -> None:
    """Test finding galleries when none exist."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findGalleries",
                    create_find_galleries_result(count=0, galleries=[]),
                ),
            )
        ]
    )

    try:
        result = await respx_stash_client.find_galleries()
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert result.count == 0
    assert len(result.galleries) == 0

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_galleries_with_filter(respx_stash_client: StashClient) -> None:
    """Test finding galleries with custom filter parameters."""
    gallery_data = create_gallery_dict(id="123", title="Filtered Gallery")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findGalleries",
                    create_find_galleries_result(count=1, galleries=[gallery_data]),
                ),
            )
        ]
    )

    try:
        result = await respx_stash_client.find_galleries(
            filter_={"per_page": 10, "page": 1}
        )
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert result.count == 1
    assert result.galleries[0].title == "Filtered Gallery"

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["filter"]["per_page"] == 10
    assert req["variables"]["filter"]["page"] == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_galleries_with_query(respx_stash_client: StashClient) -> None:
    """Test finding galleries with search query."""
    gallery_data = create_gallery_dict(id="123", title="Search Result Gallery")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findGalleries",
                    create_find_galleries_result(count=1, galleries=[gallery_data]),
                ),
            )
        ]
    )

    try:
        result = await respx_stash_client.find_galleries(q="Search Result")
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert result.count == 1
    assert result.galleries[0].title == "Search Result Gallery"

    # Verify GraphQL call includes q parameter
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["filter"]["q"] == "Search Result"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_galleries_with_gallery_filter(
    respx_stash_client: StashClient,
) -> None:
    """Test finding galleries with gallery-specific filter."""
    gallery_data = create_gallery_dict(id="123", title="Organized Gallery")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findGalleries",
                    create_find_galleries_result(count=1, galleries=[gallery_data]),
                ),
            )
        ]
    )

    try:
        result = await respx_stash_client.find_galleries(
            gallery_filter={"organized": True}
        )
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert result.count == 1

    # Verify GraphQL call includes gallery_filter
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["gallery_filter"]["organized"] is True


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_galleries_error_returns_empty(
    respx_stash_client: StashClient,
) -> None:
    """Test that find_galleries returns empty result on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    try:
        result = await respx_stash_client.find_galleries()
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert result.count == 0
    assert len(result.galleries) == 0

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_gallery_with_studio(respx_stash_client: StashClient) -> None:
    """Test finding a gallery with studio relationship."""
    studio_data = create_studio_dict(id="201", name="Test Studio")
    gallery_data = create_gallery_dict(
        id="123",
        title="Gallery with Studio",
        studio=studio_data,
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("findGallery", gallery_data)
            )
        ]
    )

    try:
        gallery = await respx_stash_client.find_gallery("123")
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert gallery is not None
    assert gallery.studio is not None
    assert is_set(gallery.studio)
    assert gallery.studio.id == "201"
    assert gallery.studio.name == "Test Studio"

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_gallery_with_performers(respx_stash_client: StashClient) -> None:
    """Test finding a gallery with performers."""
    performer_data = [
        create_performer_dict(id="101", name="Performer 1"),
        create_performer_dict(id="102", name="Performer 2"),
    ]
    gallery_data = create_gallery_dict(
        id="123",
        title="Gallery with Performers",
        performers=performer_data,
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("findGallery", gallery_data)
            )
        ]
    )

    try:
        gallery = await respx_stash_client.find_gallery("123")
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert gallery is not None
    assert is_set(gallery.performers)
    assert len(gallery.performers) == 2
    assert gallery.performers[0].id == "101"
    assert gallery.performers[1].id == "102"

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_gallery_with_tags(respx_stash_client: StashClient) -> None:
    """Test finding a gallery with tags."""
    tag_data = [
        create_tag_dict(id="301", name="Tag 1"),
        create_tag_dict(id="302", name="Tag 2"),
    ]
    gallery_data = create_gallery_dict(
        id="123",
        title="Gallery with Tags",
        tags=tag_data,
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("findGallery", gallery_data)
            )
        ]
    )

    try:
        gallery = await respx_stash_client.find_gallery("123")
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert gallery is not None
    assert is_set(gallery.tags)
    assert len(gallery.tags) == 2
    assert gallery.tags[0].id == "301"
    assert gallery.tags[1].id == "302"

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_gallery_destroy(respx_stash_client: StashClient) -> None:
    """Test destroying galleries."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("galleryDestroy", True))
        ]
    )

    try:
        result = await respx_stash_client.gallery_destroy(ids=["123", "456"])
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert result is True

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "galleryDestroy" in req["query"]
    assert req["variables"]["input"]["ids"] == ["123", "456"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_gallery_destroy_with_options(respx_stash_client: StashClient) -> None:
    """Test destroying galleries with delete options."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("galleryDestroy", True))
        ]
    )

    try:
        result = await respx_stash_client.gallery_destroy(
            ids=["123"], delete_file=True, delete_generated=False
        )
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert result is True

    # Verify GraphQL call includes options
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["input"]["delete_file"] is True
    assert req["variables"]["input"]["delete_generated"] is False


@pytest.mark.asyncio
@pytest.mark.unit
async def test_add_gallery_images(respx_stash_client: StashClient) -> None:
    """Test adding images to a gallery."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("addGalleryImages", True))
        ]
    )

    try:
        result = await respx_stash_client.add_gallery_images(
            gallery_id="123", image_ids=["img_1", "img_2", "img_3"]
        )
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert result is True

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "addGalleryImages" in req["query"]
    assert req["variables"]["input"]["gallery_id"] == "123"
    assert req["variables"]["input"]["image_ids"] == ["img_1", "img_2", "img_3"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_remove_gallery_images(respx_stash_client: StashClient) -> None:
    """Test removing images from a gallery."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("removeGalleryImages", True)
            )
        ]
    )

    try:
        result = await respx_stash_client.remove_gallery_images(
            gallery_id="123", image_ids=["img_1", "img_2"]
        )
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert result is True

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "removeGalleryImages" in req["query"]
    assert req["variables"]["input"]["gallery_id"] == "123"
    assert req["variables"]["input"]["image_ids"] == ["img_1", "img_2"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_set_gallery_cover(respx_stash_client: StashClient) -> None:
    """Test setting a gallery cover image."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("setGalleryCover", True))
        ]
    )

    try:
        result = await respx_stash_client.set_gallery_cover(
            gallery_id="123", cover_image_id="601"
        )
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert result is True

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "setGalleryCover" in req["query"]
    assert req["variables"]["input"]["gallery_id"] == "123"
    assert req["variables"]["input"]["cover_image_id"] == "601"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_reset_gallery_cover(respx_stash_client: StashClient) -> None:
    """Test resetting a gallery cover image."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("resetGalleryCover", True))
        ]
    )

    try:
        result = await respx_stash_client.reset_gallery_cover(gallery_id="123")
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert result is True

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "resetGalleryCover" in req["query"]
    assert req["variables"]["input"]["gallery_id"] == "123"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_gallery_chapter_create(respx_stash_client: StashClient) -> None:
    """Test creating a gallery chapter."""
    chapter_data = {
        "id": "801",
        "title": "Chapter 1",
        "image_index": 0,
        "gallery": {"id": "501"},
    }

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("galleryChapterCreate", chapter_data)
            )
        ]
    )

    try:
        result = await respx_stash_client.gallery_chapter_create(
            gallery_id="501", title="Chapter 1", image_index=0
        )
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert result is not None
    assert result.id == "801"
    assert result.title == "Chapter 1"
    assert result.image_index == 0

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "galleryChapterCreate" in req["query"]
    assert req["variables"]["input"]["gallery_id"] == "501"
    assert req["variables"]["input"]["title"] == "Chapter 1"
    assert req["variables"]["input"]["image_index"] == 0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_gallery_chapter_create_negative_index_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test gallery_chapter_create rejects negative image_index."""
    with pytest.raises(ValueError, match="image_index must be non-negative"):
        await respx_stash_client.gallery_chapter_create(
            gallery_id="501", title="Chapter 1", image_index=-1
        )


@pytest.mark.asyncio
@pytest.mark.unit
async def test_gallery_chapter_update(respx_stash_client: StashClient) -> None:
    """Test updating a gallery chapter."""
    chapter_data = {
        "id": "801",
        "title": "Updated Chapter",
        "image_index": 5,
        "gallery": {"id": "501"},
    }

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("galleryChapterUpdate", chapter_data)
            )
        ]
    )

    try:
        result = await respx_stash_client.gallery_chapter_update(
            id="801", title="Updated Chapter", image_index=5
        )
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert result is not None
    assert result.id == "801"
    assert result.title == "Updated Chapter"
    assert result.image_index == 5

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "galleryChapterUpdate" in req["query"]
    assert req["variables"]["input"]["id"] == "801"
    assert req["variables"]["input"]["title"] == "Updated Chapter"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_gallery_chapter_update_negative_index_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test gallery_chapter_update rejects negative image_index."""
    with pytest.raises(ValueError, match="image_index must be non-negative"):
        await respx_stash_client.gallery_chapter_update(id="801", image_index=-5)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_gallery_chapter_destroy(respx_stash_client: StashClient) -> None:
    """Test deleting a gallery chapter."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("galleryChapterDestroy", True)
            )
        ]
    )

    try:
        result = await respx_stash_client.gallery_chapter_destroy(id="801")
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert result is True

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "galleryChapterDestroy" in req["query"]
    assert req["variables"]["id"] == "801"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_gallery(respx_stash_client: StashClient) -> None:
    """Test creating a new gallery."""
    created_gallery_data = create_gallery_dict(
        id="9001",
        title="New Gallery",
        code="NEW-001",
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("galleryCreate", created_gallery_data)
            )
        ]
    )

    # Create a new gallery object with id="9999" for new objects
    gallery = Gallery(
        id="9999",
        title="New Gallery",
        code="NEW-001",
    )

    try:
        result = await respx_stash_client.create_gallery(gallery)
    finally:
        dump_graphql_calls(graphql_route.calls)

    # Verify the result
    assert result is not None
    assert result.id == "9001"
    assert result.title == "New Gallery"

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "galleryCreate" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_gallery_error_raises(respx_stash_client: StashClient) -> None:
    """Test that create_gallery raises on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    gallery = Gallery(id="9999", title="Fail Gallery")

    try:
        with pytest.raises(StashGraphQLError):
            await respx_stash_client.create_gallery(gallery)
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_gallery(respx_stash_client: StashClient) -> None:
    """Test updating an existing gallery."""
    updated_gallery_data = create_gallery_dict(
        id="501",
        title="Updated Gallery",
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("galleryUpdate", updated_gallery_data)
            )
        ]
    )

    # Create an existing gallery and modify it
    gallery = Gallery(id="501", title="Original Gallery")
    gallery.title = "Updated Gallery"

    try:
        result = await respx_stash_client.update_gallery(gallery)
    finally:
        dump_graphql_calls(graphql_route.calls)

    # Verify the result
    assert result is not None
    assert result.id == "501"
    assert result.title == "Updated Gallery"

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "galleryUpdate" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_gallery_error_raises(respx_stash_client: StashClient) -> None:
    """Test that update_gallery raises on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    gallery = Gallery(id="501", title="Fail Gallery")
    gallery.title = "Updated Title"

    try:
        with pytest.raises(StashGraphQLError):
            await respx_stash_client.update_gallery(gallery)
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert len(graphql_route.calls) == 1


# ============================================================================
# galleries_update tests
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_galleries_update_success(respx_stash_client: StashClient) -> None:
    """Test updating multiple galleries with individual data."""
    updated_galleries_data = [
        create_gallery_dict(id="502", title="Updated Gallery 1"),
        create_gallery_dict(id="503", title="Updated Gallery 2"),
    ]

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response("galleriesUpdate", updated_galleries_data),
            )
        ]
    )

    # Create gallery objects to update
    galleries = [
        Gallery(id="502", title="Updated Gallery 1"),
        Gallery(id="503", title="Updated Gallery 2"),
    ]

    try:
        result = await respx_stash_client.galleries_update(galleries)
    finally:
        dump_graphql_calls(graphql_route.calls)

    # Verify the results
    assert len(result) == 2
    assert result[0].id == "502"
    assert result[0].title == "Updated Gallery 1"
    assert result[1].id == "503"
    assert result[1].title == "Updated Gallery 2"

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "galleriesUpdate" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_galleries_update_error_raises(respx_stash_client: StashClient) -> None:
    """Test that galleries_update raises on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    galleries = [Gallery(id="502", title="Fail Gallery")]

    try:
        with pytest.raises(StashGraphQLError):
            await respx_stash_client.galleries_update(galleries)
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert len(graphql_route.calls) == 1


# ============================================================================
# Error handling tests for gallery operations
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_gallery_destroy_error_raises(respx_stash_client: StashClient) -> None:
    """Test that gallery_destroy raises on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    try:
        with pytest.raises(StashGraphQLError):
            await respx_stash_client.gallery_destroy(ids=["123"])
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_remove_gallery_images_error_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test that remove_gallery_images raises on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    try:
        with pytest.raises(StashGraphQLError):
            await respx_stash_client.remove_gallery_images(
                gallery_id="123", image_ids=["img_1"]
            )
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_set_gallery_cover_error_raises(respx_stash_client: StashClient) -> None:
    """Test that set_gallery_cover raises on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    try:
        with pytest.raises(StashGraphQLError):
            await respx_stash_client.set_gallery_cover(
                gallery_id="123", cover_image_id="601"
            )
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_reset_gallery_cover_error_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test that reset_gallery_cover raises on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    try:
        with pytest.raises(StashGraphQLError):
            await respx_stash_client.reset_gallery_cover(gallery_id="123")
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_add_gallery_images_error_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test that add_gallery_images raises on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    try:
        with pytest.raises(StashGraphQLError):
            await respx_stash_client.add_gallery_images(
                gallery_id="123", image_ids=["img_1"]
            )
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert len(graphql_route.calls) == 1


# ============================================================================
# Gallery chapter error handling tests
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_gallery_chapter_create_error_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test that gallery_chapter_create raises on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    try:
        with pytest.raises(StashGraphQLError):
            await respx_stash_client.gallery_chapter_create(
                gallery_id="123", title="Chapter 1", image_index=0
            )
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_gallery_chapter_update_with_gallery_id(
    respx_stash_client: StashClient,
) -> None:
    """Test updating a gallery chapter with gallery_id parameter.

    This exercises the conditional branch where gallery_id is provided.
    """
    chapter_data = {
        "id": "801",
        "title": "Chapter 1",
        "image_index": 0,
        "gallery": {"id": "9002"},
    }

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("galleryChapterUpdate", chapter_data)
            )
        ]
    )

    try:
        result = await respx_stash_client.gallery_chapter_update(
            id="801", gallery_id="9002"
        )
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert result is not None
    assert result.id == "801"

    # Verify GraphQL call includes gallery_id
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["input"]["id"] == "801"
    assert req["variables"]["input"]["gallery_id"] == "9002"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_gallery_chapter_update_error_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test that gallery_chapter_update raises on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    try:
        with pytest.raises(StashGraphQLError):
            await respx_stash_client.gallery_chapter_update(
                id="801", title="Updated Chapter"
            )
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_gallery_chapter_destroy_error_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test that gallery_chapter_destroy raises on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    try:
        with pytest.raises(StashGraphQLError):
            await respx_stash_client.gallery_chapter_destroy(id="801")
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert len(graphql_route.calls) == 1


# =============================================================================
# Bulk Gallery Update tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_bulk_gallery_update_success(respx_stash_client: StashClient) -> None:
    """Test bulk_gallery_update with model input."""
    updated_galleries = [
        create_gallery_dict(id="1", title="Gallery 1", organized=True),
        create_gallery_dict(id="2", title="Gallery 2", organized=True),
    ]

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json={"data": {"bulkGalleryUpdate": updated_galleries}})
        ]
    )

    input_data = BulkGalleryUpdateInput(
        ids=["1", "2"],
        tag_ids=BulkUpdateIds(ids=["tag1"], mode=BulkUpdateIdMode.ADD),
        organized=True,
    )

    try:
        result = await respx_stash_client.bulk_gallery_update(input_data)
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert len(result) == 2
    assert result[0].id == "1"
    assert result[1].id == "2"
    assert result[0].organized is True
    assert result[1].organized is True

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "bulkGalleryUpdate" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_bulk_gallery_update_with_dict(respx_stash_client: StashClient) -> None:
    """Test bulk_gallery_update with dict input."""
    updated_galleries = [
        create_gallery_dict(id="1", rating100=80),
        create_gallery_dict(id="2", rating100=80),
    ]

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json={"data": {"bulkGalleryUpdate": updated_galleries}})
        ]
    )

    # Use a raw dict instead of BulkGalleryUpdateInput
    input_data = {
        "ids": ["1", "2"],
        "rating100": 80,
    }

    try:
        result = await respx_stash_client.bulk_gallery_update(input_data)
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert len(result) == 2
    assert result[0].id == "1"
    assert result[1].id == "2"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "bulkGalleryUpdate" in req["query"]
    assert req["variables"]["input"]["ids"] == ["1", "2"]
    assert req["variables"]["input"]["rating100"] == 80


@pytest.mark.asyncio
@pytest.mark.unit
async def test_bulk_gallery_update_error(respx_stash_client: StashClient) -> None:
    """Test bulk_gallery_update error handling."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json={"errors": [{"message": "Failed to bulk update galleries"}]}
            )
        ]
    )

    input_data = BulkGalleryUpdateInput(ids=["1", "2"], organized=True)

    try:
        with pytest.raises(StashGraphQLError, match="Failed to bulk update galleries"):
            await respx_stash_client.bulk_gallery_update(input_data)
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert len(graphql_route.calls) == 1


# =============================================================================
# update_gallery_images tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_gallery_images_mode_set(respx_stash_client: StashClient) -> None:
    """Test update_gallery_images with SET mode - should call addGalleryImages."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("addGalleryImages", True))
        ]
    )

    try:
        result = await respx_stash_client.update_gallery_images(
            gallery_id="123", image_ids=["img_1", "img_2"], mode="SET"
        )
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert result is True

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "addGalleryImages" in req["query"]
    assert req["variables"]["input"]["gallery_id"] == "123"
    assert req["variables"]["input"]["image_ids"] == ["img_1", "img_2"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_gallery_images_mode_add(respx_stash_client: StashClient) -> None:
    """Test update_gallery_images with ADD mode - should call addGalleryImages."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("addGalleryImages", True))
        ]
    )

    try:
        result = await respx_stash_client.update_gallery_images(
            gallery_id="456", image_ids=["img_3"], mode="ADD"
        )
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert result is True

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "addGalleryImages" in req["query"]
    assert req["variables"]["input"]["gallery_id"] == "456"
    assert req["variables"]["input"]["image_ids"] == ["img_3"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_gallery_images_mode_remove(
    respx_stash_client: StashClient,
) -> None:
    """Test update_gallery_images with REMOVE mode - should call removeGalleryImages."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("removeGalleryImages", True)
            )
        ]
    )

    try:
        result = await respx_stash_client.update_gallery_images(
            gallery_id="789", image_ids=["img_4", "img_5"], mode="REMOVE"
        )
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert result is True

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "removeGalleryImages" in req["query"]
    assert req["variables"]["input"]["gallery_id"] == "789"
    assert req["variables"]["input"]["image_ids"] == ["img_4", "img_5"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_gallery_images_default_mode_set(
    respx_stash_client: StashClient,
) -> None:
    """Test update_gallery_images defaults to SET mode when mode not specified."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("addGalleryImages", True))
        ]
    )

    # Call without mode parameter - should default to SET
    try:
        result = await respx_stash_client.update_gallery_images(
            gallery_id="504", image_ids=["602"]
        )
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert result is True

    # Verify it called addGalleryImages (SET mode behavior)
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "addGalleryImages" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_gallery_images_invalid_mode_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test update_gallery_images raises ValueError for invalid mode."""
    with pytest.raises(ValueError, match="mode must be one of"):
        await respx_stash_client.update_gallery_images(
            gallery_id="123", image_ids=["img_1"], mode="INVALID"
        )


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_gallery_images_error_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test update_gallery_images raises on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    try:
        with pytest.raises(StashGraphQLError):
            await respx_stash_client.update_gallery_images(
                gallery_id="505", image_ids=["603"], mode="SET"
            )
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert len(graphql_route.calls) == 1
