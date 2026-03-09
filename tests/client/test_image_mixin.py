"""Unit tests for ImageClientMixin.

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
    BulkImageUpdateInput,
    BulkUpdateIdMode,
    BulkUpdateIds,
    ImageDestroyInput,
    ImagesDestroyInput,
    ImageUpdateInput,
)
from stash_graphql_client.types.unset import is_set
from tests.fixtures import (
    create_find_images_result,
    create_graphql_response,
    create_image_dict,
    create_performer_dict,
    create_studio_dict,
    create_tag_dict,
    dump_graphql_calls,
)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_image(respx_stash_client: StashClient) -> None:
    """Test finding an image by ID."""
    image_data = create_image_dict(
        id="123",
        title="Test Image",
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("findImage", image_data))
        ]
    )

    try:
        image = await respx_stash_client.find_image("123")
    finally:
        dump_graphql_calls(graphql_route.calls)

    # Verify the result
    assert image is not None
    assert image.id == "123"
    assert image.title == "Test Image"

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "findImage" in req["query"]
    assert req["variables"]["id"] == "123"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_image_not_found(respx_stash_client: StashClient) -> None:
    """Test finding an image that doesn't exist."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("findImage", None))
        ]
    )

    try:
        image = await respx_stash_client.find_image("999")
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert image is None

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_image_error_returns_none(respx_stash_client: StashClient) -> None:
    """Test handling errors when finding an image returns None."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(500, json={"errors": [{"message": "Test error"}]})]
    )

    try:
        image = await respx_stash_client.find_image("error_image")
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert image is None

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_images(respx_stash_client: StashClient) -> None:
    """Test finding images with filters."""
    image_data = create_image_dict(
        id="123",
        title="Test Image",
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findImages",
                    create_find_images_result(
                        count=1, images=[image_data], megapixels=5.0, filesize=1024000
                    ),
                ),
            )
        ]
    )

    try:
        result = await respx_stash_client.find_images()
    finally:
        dump_graphql_calls(graphql_route.calls)

    # Verify the results
    assert result.count == 1
    assert is_set(result.images)
    assert len(result.images) == 1
    assert result.images[0].id == "123"
    assert result.images[0].title == "Test Image"
    assert result.megapixels == 5.0
    assert result.filesize == 1024000

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "findImages" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_images_empty(respx_stash_client: StashClient) -> None:
    """Test finding images when none exist."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findImages",
                    create_find_images_result(count=0, images=[]),
                ),
            )
        ]
    )

    try:
        result = await respx_stash_client.find_images()
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert result.count == 0
    assert is_set(result.images)
    assert len(result.images) == 0

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_images_invalid_direction_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test find_images rejects invalid direction values."""
    with pytest.raises(ValueError, match="direction must be 'ASC' or 'DESC'"):
        await respx_stash_client.find_images(filter_={"direction": "UP"})


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_images_with_filter(respx_stash_client: StashClient) -> None:
    """Test finding images with custom filter parameters."""
    image_data = create_image_dict(id="123", title="Filtered Image")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findImages",
                    create_find_images_result(count=1, images=[image_data]),
                ),
            )
        ]
    )

    try:
        result = await respx_stash_client.find_images(
            filter_={"per_page": 10, "page": 1}
        )
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert result.count == 1
    assert is_set(result.images)
    assert result.images[0].title == "Filtered Image"

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["filter"]["per_page"] == 10
    assert req["variables"]["filter"]["page"] == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_images_with_query(respx_stash_client: StashClient) -> None:
    """Test finding images with search query."""
    image_data = create_image_dict(id="123", title="Search Result Image")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findImages",
                    create_find_images_result(count=1, images=[image_data]),
                ),
            )
        ]
    )

    try:
        result = await respx_stash_client.find_images(q="Search Result")
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert result.count == 1
    assert is_set(result.images)
    assert result.images[0].title == "Search Result Image"

    # Verify GraphQL call includes q parameter
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["filter"]["q"] == "Search Result"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_images_with_image_filter(respx_stash_client: StashClient) -> None:
    """Test finding images with image-specific filter."""
    image_data = create_image_dict(id="123", title="Organized Image")

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response(
                    "findImages",
                    create_find_images_result(count=1, images=[image_data]),
                ),
            )
        ]
    )

    try:
        result = await respx_stash_client.find_images(image_filter={"organized": True})
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert result.count == 1

    # Verify GraphQL call includes image_filter
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["image_filter"]["organized"] is True


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_images_error_returns_empty(respx_stash_client: StashClient) -> None:
    """Test that find_images returns empty result on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    try:
        result = await respx_stash_client.find_images()
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert result.count == 0
    assert is_set(result.images)
    assert len(result.images) == 0
    assert result.megapixels == 0.0
    assert result.filesize == 0.0

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_image_with_studio(respx_stash_client: StashClient) -> None:
    """Test finding an image with studio relationship."""
    studio_data = create_studio_dict(id="studio_123", name="Test Studio")
    image_data = create_image_dict(
        id="123",
        title="Image with Studio",
        studio=studio_data,
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("findImage", image_data))
        ]
    )

    try:
        image = await respx_stash_client.find_image("123")
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert image is not None
    assert is_set(image.studio)
    assert image.studio is not None
    assert image.studio.id == "studio_123"
    assert image.studio.name == "Test Studio"

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_image_with_performers(respx_stash_client: StashClient) -> None:
    """Test finding an image with performers."""
    performer_data = [
        create_performer_dict(id="perf_1", name="Performer 1"),
        create_performer_dict(id="perf_2", name="Performer 2"),
    ]
    image_data = create_image_dict(
        id="123",
        title="Image with Performers",
        performers=performer_data,
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("findImage", image_data))
        ]
    )

    try:
        image = await respx_stash_client.find_image("123")
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert image is not None
    assert is_set(image.performers)
    assert len(image.performers) == 2
    assert image.performers[0].id == "perf_1"
    assert image.performers[1].id == "perf_2"

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_find_image_with_tags(respx_stash_client: StashClient) -> None:
    """Test finding an image with tags."""
    tag_data = [
        create_tag_dict(id="tag_1", name="Tag 1"),
        create_tag_dict(id="tag_2", name="Tag 2"),
    ]
    image_data = create_image_dict(
        id="123",
        title="Image with Tags",
        tags=tag_data,
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("findImage", image_data))
        ]
    )

    try:
        image = await respx_stash_client.find_image("123")
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert image is not None
    assert is_set(image.tags)
    assert len(image.tags) == 2
    assert image.tags[0].id == "tag_1"
    assert image.tags[1].id == "tag_2"

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_image_destroy(respx_stash_client: StashClient) -> None:
    """Test destroying an image."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("imageDestroy", True))
        ]
    )

    try:
        result = await respx_stash_client.image_destroy({"id": "123"})
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert result is True

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "imageDestroy" in req["query"]
    assert req["variables"]["input"]["id"] == "123"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_image_destroy_with_options(respx_stash_client: StashClient) -> None:
    """Test destroying an image with delete options."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("imageDestroy", True))
        ]
    )

    try:
        result = await respx_stash_client.image_destroy(
            {"id": "123", "delete_file": True, "delete_generated": False}
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
async def test_image_destroy_with_model_input(respx_stash_client: StashClient) -> None:
    """Test destroying an image using ImageDestroyInput model."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("imageDestroy", True))
        ]
    )

    input_data = ImageDestroyInput(id="123", delete_file=True)
    try:
        result = await respx_stash_client.image_destroy(input_data)
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert result is True

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["input"]["id"] == "123"
    assert req["variables"]["input"]["delete_file"] is True  # Schema uses snake_case


@pytest.mark.asyncio
@pytest.mark.unit
async def test_images_destroy(respx_stash_client: StashClient) -> None:
    """Test destroying multiple images."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("imagesDestroy", True))
        ]
    )

    try:
        result = await respx_stash_client.images_destroy({"ids": ["123", "456", "789"]})
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert result is True

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "imagesDestroy" in req["query"]
    assert req["variables"]["input"]["ids"] == ["123", "456", "789"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_images_destroy_with_options(respx_stash_client: StashClient) -> None:
    """Test destroying multiple images with delete options."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("imagesDestroy", True))
        ]
    )

    try:
        result = await respx_stash_client.images_destroy(
            {"ids": ["123", "456"], "delete_file": True, "delete_generated": True}
        )
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert result is True

    # Verify GraphQL call includes options
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["input"]["ids"] == ["123", "456"]
    assert req["variables"]["input"]["delete_file"] is True
    assert req["variables"]["input"]["delete_generated"] is True


@pytest.mark.asyncio
@pytest.mark.unit
async def test_images_destroy_with_model_input(respx_stash_client: StashClient) -> None:
    """Test destroying multiple images using ImagesDestroyInput model."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("imagesDestroy", True))
        ]
    )

    input_data = ImagesDestroyInput(ids=["123", "456"], delete_file=False)
    try:
        result = await respx_stash_client.images_destroy(input_data)
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert result is True

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["input"]["ids"] == ["123", "456"]
    assert req["variables"]["input"]["delete_file"] is False  # Schema uses snake_case


# =============================================================================
# Create and Update tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_image(respx_stash_client: StashClient, mock_image) -> None:
    """Test creating a new image."""
    created_image_data = create_image_dict(
        id="new_123",
        title="New Image",
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("imageCreate", created_image_data)
            )
        ]
    )

    try:
        result = await respx_stash_client.create_image(mock_image)
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert result is not None
    assert result.id == "new_123"
    assert result.title == "New Image"

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "imageCreate" in req["query"]
    assert "input" in req["variables"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_image(respx_stash_client: StashClient, mock_image) -> None:
    """Test updating an existing image."""
    updated_image_data = create_image_dict(
        id="123",
        title="Updated Image",
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("imageUpdate", updated_image_data)
            )
        ]
    )

    try:
        result = await respx_stash_client.update_image(mock_image)
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert result is not None
    assert result.id == "123"
    assert result.title == "Updated Image"

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "imageUpdate" in req["query"]
    assert "input" in req["variables"]


# =============================================================================
# Error handling tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_image_error(respx_stash_client: StashClient, mock_image) -> None:
    """Test create_image error handling."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json={"errors": [{"message": "Failed to create image"}]}
            )
        ]
    )

    try:
        with pytest.raises(StashGraphQLError, match="Failed to create image"):
            await respx_stash_client.create_image(mock_image)
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_image_error(respx_stash_client: StashClient, mock_image) -> None:
    """Test update_image error handling."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json={"errors": [{"message": "Failed to update image"}]}
            )
        ]
    )

    try:
        with pytest.raises(StashGraphQLError, match="Failed to update image"):
            await respx_stash_client.update_image(mock_image)
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_image_destroy_error(respx_stash_client: StashClient) -> None:
    """Test image_destroy error handling."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json={"errors": [{"message": "Failed to delete image"}]}
            )
        ]
    )

    try:
        with pytest.raises(StashGraphQLError, match="Failed to delete image"):
            await respx_stash_client.image_destroy({"id": "123"})
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_images_destroy_error(respx_stash_client: StashClient) -> None:
    """Test images_destroy error handling."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json={"errors": [{"message": "Failed to delete images"}]}
            )
        ]
    )

    try:
        with pytest.raises(StashGraphQLError, match="Failed to delete images"):
            await respx_stash_client.images_destroy({"ids": ["123", "456"]})
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_bulk_image_update_error(respx_stash_client: StashClient) -> None:
    """Test bulk_image_update error handling."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json={"errors": [{"message": "Failed to bulk update images"}]}
            )
        ]
    )

    input_data = BulkImageUpdateInput(
        ids=["1", "2"], tag_ids=BulkUpdateIds(ids=["tag1"], mode=BulkUpdateIdMode.ADD)
    )

    try:
        with pytest.raises(StashGraphQLError, match="Failed to bulk update images"):
            await respx_stash_client.bulk_image_update(input_data)
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_bulk_image_update_success(respx_stash_client: StashClient) -> None:
    """Test bulk_image_update with model input."""
    updated_images = [
        create_image_dict(id="1", title="Image 1"),
        create_image_dict(id="2", title="Image 2"),
    ]

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json={"data": {"bulkImageUpdate": updated_images}})
        ]
    )

    input_data = BulkImageUpdateInput(
        ids=["1", "2"], tag_ids=BulkUpdateIds(ids=["tag1"], mode=BulkUpdateIdMode.ADD)
    )

    try:
        result = await respx_stash_client.bulk_image_update(input_data)
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert len(result) == 2
    assert result[0].id == "1"
    assert result[1].id == "2"

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_bulk_image_update_with_dict(respx_stash_client: StashClient) -> None:
    """Test bulk_image_update with dict input.

    This covers line 250: else branch when input_data is a dict.
    """
    updated_images = [
        create_image_dict(id="1", title="Image 1"),
        create_image_dict(id="2", title="Image 2"),
    ]

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json={"data": {"bulkImageUpdate": updated_images}})
        ]
    )

    # Use a raw dict instead of BulkImageUpdateInput
    input_data = {
        "ids": ["1", "2"],
        "rating100": 80,
    }

    try:
        result = await respx_stash_client.bulk_image_update(input_data)
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert len(result) == 2
    assert result[0].id == "1"
    assert result[1].id == "2"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "bulkImageUpdate" in req["query"]
    assert req["variables"]["input"]["ids"] == ["1", "2"]


# =============================================================================
# Image O-count tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_image_increment_o_success(respx_stash_client: StashClient) -> None:
    """Test incrementing image O-count."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(200, json={"data": {"imageIncrementO": 5}})]
    )

    try:
        new_count = await respx_stash_client.image_increment_o("123")
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert new_count == 5
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "imageIncrementO" in req["query"]
    assert req["variables"]["id"] == "123"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_image_increment_o_error(respx_stash_client: StashClient) -> None:
    """Test image_increment_o error handling."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json={"errors": [{"message": "Failed to increment O-count"}]}
            )
        ]
    )

    try:
        with pytest.raises(StashGraphQLError, match="Failed to increment O-count"):
            await respx_stash_client.image_increment_o("123")
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_image_decrement_o_success(respx_stash_client: StashClient) -> None:
    """Test decrementing image O-count."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(200, json={"data": {"imageDecrementO": 3}})]
    )

    try:
        new_count = await respx_stash_client.image_decrement_o("123")
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert new_count == 3
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "imageDecrementO" in req["query"]
    assert req["variables"]["id"] == "123"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_image_decrement_o_error(respx_stash_client: StashClient) -> None:
    """Test image_decrement_o error handling."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json={"errors": [{"message": "Failed to decrement O-count"}]}
            )
        ]
    )

    try:
        with pytest.raises(StashGraphQLError, match="Failed to decrement O-count"):
            await respx_stash_client.image_decrement_o("123")
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_image_reset_o_success(respx_stash_client: StashClient) -> None:
    """Test resetting image O-count."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(200, json={"data": {"imageResetO": 0}})]
    )

    try:
        new_count = await respx_stash_client.image_reset_o("123")
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert new_count == 0
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "imageResetO" in req["query"]
    assert req["variables"]["id"] == "123"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_image_reset_o_error(respx_stash_client: StashClient) -> None:
    """Test image_reset_o error handling."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json={"errors": [{"message": "Failed to reset O-count"}]}
            )
        ]
    )

    try:
        with pytest.raises(StashGraphQLError, match="Failed to reset O-count"):
            await respx_stash_client.image_reset_o("123")
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert len(graphql_route.calls) == 1


# =============================================================================
# Images Update tests (individual updates, not bulk)
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_images_update_success(respx_stash_client: StashClient) -> None:
    """Test imagesUpdate mutation with multiple individual updates."""
    updated_images = [
        create_image_dict(id="1", title="Updated Image 1", organized=True),
        create_image_dict(id="2", title="Updated Image 2", rating100=90),
    ]

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json={"data": {"imagesUpdate": updated_images}})
        ]
    )

    # Create list of individual update inputs
    updates = [
        ImageUpdateInput(id="1", title="Updated Image 1", organized=True),
        ImageUpdateInput(id="2", title="Updated Image 2", rating100=90),
    ]

    try:
        result = await respx_stash_client.images_update(updates)
    finally:
        dump_graphql_calls(graphql_route.calls)

    # Verify results
    assert len(result) == 2
    assert result[0].id == "1"
    assert result[0].title == "Updated Image 1"
    assert result[1].id == "2"
    assert result[1].title == "Updated Image 2"

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "imagesUpdate" in req["query"]
    assert isinstance(req["variables"]["input"], list)
    assert len(req["variables"]["input"]) == 2
    assert req["variables"]["input"][0]["id"] == "1"
    assert req["variables"]["input"][1]["id"] == "2"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_images_update_with_dicts(respx_stash_client: StashClient) -> None:
    """Test imagesUpdate with dictionary inputs."""
    updated_images = [
        create_image_dict(id="1", organized=True),
        create_image_dict(id="2", rating100=75),
    ]

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json={"data": {"imagesUpdate": updated_images}})
        ]
    )

    # Pass list of dicts
    updates = [
        {"id": "1", "organized": True},
        {"id": "2", "rating100": 75},
    ]

    try:
        result = await respx_stash_client.images_update(updates)
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert len(result) == 2
    assert result[0].id == "1"
    assert result[1].id == "2"

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "imagesUpdate" in req["query"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_images_update_empty_list(respx_stash_client: StashClient) -> None:
    """Test imagesUpdate with empty list returns empty list."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(200, json={"data": {"imagesUpdate": []}})]
    )

    try:
        result = await respx_stash_client.images_update([])
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert len(result) == 0
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_images_update_error(respx_stash_client: StashClient) -> None:
    """Test imagesUpdate error handling."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json={"errors": [{"message": "Failed to update images"}]}
            )
        ]
    )

    updates = [ImageUpdateInput(id="1", title="Test")]

    try:
        with pytest.raises(StashGraphQLError, match="Failed to update images"):
            await respx_stash_client.images_update(updates)
    finally:
        dump_graphql_calls(graphql_route.calls)

    assert len(graphql_route.calls) == 1
