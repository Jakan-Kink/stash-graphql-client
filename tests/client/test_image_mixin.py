"""Unit tests for ImageClientMixin.

These tests mock at the HTTP boundary using respx, allowing real code execution
through the entire GraphQL client stack including serialization/deserialization.
"""

import json

import httpx
import pytest
import respx

from stash_graphql_client import StashClient
from tests.fixtures import (
    create_find_images_result,
    create_graphql_response,
    create_image_dict,
    create_performer_dict,
    create_studio_dict,
    create_tag_dict,
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

    image = await respx_stash_client.find_image("123")

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

    image = await respx_stash_client.find_image("999")

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

    image = await respx_stash_client.find_image("error_image")

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

    result = await respx_stash_client.find_images()

    # Verify the results
    assert result.count == 1
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

    result = await respx_stash_client.find_images()

    assert result.count == 0
    assert len(result.images) == 0

    # Verify GraphQL call
    assert len(graphql_route.calls) == 1


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

    result = await respx_stash_client.find_images(filter_={"per_page": 10, "page": 1})

    assert result.count == 1
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

    result = await respx_stash_client.find_images(q="Search Result")

    assert result.count == 1
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

    result = await respx_stash_client.find_images(image_filter={"organized": True})

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

    result = await respx_stash_client.find_images()

    assert result.count == 0
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

    image = await respx_stash_client.find_image("123")

    assert image is not None
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

    image = await respx_stash_client.find_image("123")

    assert image is not None
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

    image = await respx_stash_client.find_image("123")

    assert image is not None
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

    result = await respx_stash_client.image_destroy({"id": "123"})

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

    result = await respx_stash_client.image_destroy(
        {"id": "123", "delete_file": True, "delete_generated": False}
    )

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
    from stash_graphql_client.types import ImageDestroyInput

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("imageDestroy", True))
        ]
    )

    input_data = ImageDestroyInput(id="123", delete_file=True)
    result = await respx_stash_client.image_destroy(input_data)

    assert result is True

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["input"]["id"] == "123"
    assert req["variables"]["input"]["delete_file"] is True


@pytest.mark.asyncio
@pytest.mark.unit
async def test_images_destroy(respx_stash_client: StashClient) -> None:
    """Test destroying multiple images."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("imagesDestroy", True))
        ]
    )

    result = await respx_stash_client.images_destroy({"ids": ["123", "456", "789"]})

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

    result = await respx_stash_client.images_destroy(
        {"ids": ["123", "456"], "delete_file": True, "delete_generated": True}
    )

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
    from stash_graphql_client.types import ImagesDestroyInput

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("imagesDestroy", True))
        ]
    )

    input_data = ImagesDestroyInput(ids=["123", "456"], delete_file=False)
    result = await respx_stash_client.images_destroy(input_data)

    assert result is True

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["input"]["ids"] == ["123", "456"]
    assert req["variables"]["input"]["delete_file"] is False


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

    result = await respx_stash_client.create_image(mock_image)

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

    result = await respx_stash_client.update_image(mock_image)

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

    with pytest.raises(Exception, match="Failed to create image"):
        await respx_stash_client.create_image(mock_image)

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

    with pytest.raises(Exception, match="Failed to update image"):
        await respx_stash_client.update_image(mock_image)

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

    with pytest.raises(Exception, match="Failed to delete image"):
        await respx_stash_client.image_destroy({"id": "123"})

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

    with pytest.raises(Exception, match="Failed to delete images"):
        await respx_stash_client.images_destroy({"ids": ["123", "456"]})

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_bulk_image_update_error(respx_stash_client: StashClient) -> None:
    """Test bulk_image_update error handling."""
    from stash_graphql_client.types import BulkImageUpdateInput, BulkUpdateIds

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json={"errors": [{"message": "Failed to bulk update images"}]}
            )
        ]
    )

    input_data = BulkImageUpdateInput(
        ids=["1", "2"], tag_ids=BulkUpdateIds(ids=["tag1"], mode="ADD")
    )

    with pytest.raises(Exception, match="Failed to bulk update images"):
        await respx_stash_client.bulk_image_update(input_data)

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_bulk_image_update_success(respx_stash_client: StashClient) -> None:
    """Test bulk_image_update with model input."""
    from stash_graphql_client.types import (
        BulkImageUpdateInput,
        BulkUpdateIdMode,
        BulkUpdateIds,
    )

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

    result = await respx_stash_client.bulk_image_update(input_data)

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

    result = await respx_stash_client.bulk_image_update(input_data)

    assert len(result) == 2
    assert result[0].id == "1"
    assert result[1].id == "2"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "bulkImageUpdate" in req["query"]
    assert req["variables"]["input"]["ids"] == ["1", "2"]
