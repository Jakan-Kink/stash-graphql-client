"""Unit tests for PackageClientMixin mutation operations.

These tests mock at the HTTP boundary using respx, allowing real code execution
through the entire GraphQL client stack including serialization/deserialization.
"""

import json

import httpx
import pytest
import respx

from stash_graphql_client import StashClient
from stash_graphql_client.errors import StashGraphQLError
from stash_graphql_client.types import PackageSpecInput, PackageType
from tests.fixtures import create_graphql_response


# =============================================================================
# Helper functions for creating package mutation test data
# =============================================================================


def create_package_spec_dict(
    package_id: str = "test-package",
    source_url: str = "https://example.com/package.yml",
) -> dict:
    """Create a PackageSpecInput dictionary for testing."""
    return {
        "id": package_id,
        "sourceURL": source_url,
    }


# =============================================================================
# install_packages tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_install_packages_scraper_enum_dict(
    respx_stash_client: StashClient,
) -> None:
    """Test installing scraper packages using PackageType enum and dict input."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("installPackages", "job-123")
            )
        ]
    )

    packages = [{"id": "scraper-1", "sourceURL": "https://example.com/scraper1.yml"}]

    job_id = await respx_stash_client.install_packages(PackageType.SCRAPER, packages)

    assert job_id == "job-123"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "installPackages" in req["query"]
    assert req["variables"]["type"] == "Scraper"
    assert req["variables"]["packages"] == packages


@pytest.mark.asyncio
@pytest.mark.unit
async def test_install_packages_plugin_string_input_objects(
    respx_stash_client: StashClient,
) -> None:
    """Test installing plugin packages using string type and PackageSpecInput objects."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("installPackages", "job-456")
            )
        ]
    )

    packages = [
        PackageSpecInput(id="plugin-1", source_url="https://example.com/plugin1.yml"),
        PackageSpecInput(id="plugin-2", source_url="https://example.com/plugin2.yml"),
    ]

    job_id = await respx_stash_client.install_packages("Plugin", packages)

    assert job_id == "job-456"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["type"] == "Plugin"
    # PackageSpecInput objects should be converted to dicts with camelCase
    assert len(req["variables"]["packages"]) == 2
    assert req["variables"]["packages"][0]["id"] == "plugin-1"
    assert (
        req["variables"]["packages"][0]["sourceURL"]
        == "https://example.com/plugin1.yml"
    )


@pytest.mark.asyncio
@pytest.mark.unit
async def test_install_packages_multiple(respx_stash_client: StashClient) -> None:
    """Test installing multiple packages."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("installPackages", "job-789")
            )
        ]
    )

    packages = [
        {"id": "pkg-1", "sourceURL": "https://example.com/pkg1.yml"},
        {"id": "pkg-2", "sourceURL": "https://example.com/pkg2.yml"},
        {"id": "pkg-3", "sourceURL": "https://example.com/pkg3.yml"},
    ]

    job_id = await respx_stash_client.install_packages(PackageType.SCRAPER, packages)

    assert job_id == "job-789"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert len(req["variables"]["packages"]) == 3


@pytest.mark.asyncio
@pytest.mark.unit
async def test_install_packages_no_job_id_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test that install_packages raises when no job ID returned."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("installPackages", None))
        ]
    )

    packages = [{"id": "pkg-1", "sourceURL": "https://example.com/pkg1.yml"}]

    with pytest.raises(ValueError, match="No job ID returned from server"):
        await respx_stash_client.install_packages(PackageType.PLUGIN, packages)

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_install_packages_invalid_response_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test that install_packages raises on invalid response format."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(200, json={"data": {"installPackages": None}})]
    )

    packages = [{"id": "pkg-1", "sourceURL": "https://example.com/pkg1.yml"}]

    with pytest.raises(ValueError, match="No job ID returned from server"):
        await respx_stash_client.install_packages(PackageType.SCRAPER, packages)

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_install_packages_server_error_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test that install_packages raises on server error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    packages = [{"id": "pkg-1", "sourceURL": "https://example.com/pkg1.yml"}]

    with pytest.raises(StashGraphQLError, match="GraphQL query error"):
        await respx_stash_client.install_packages(PackageType.PLUGIN, packages)

    # Verify route was called with correct mutation
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "installPackages" in req["query"]


# =============================================================================
# update_packages tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_packages_all_scrapers(respx_stash_client: StashClient) -> None:
    """Test updating all scraper packages (no specific packages)."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("updatePackages", "job-update-1")
            )
        ]
    )

    job_id = await respx_stash_client.update_packages(PackageType.SCRAPER)

    assert job_id == "job-update-1"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "updatePackages" in req["query"]
    assert req["variables"]["type"] == "Scraper"
    assert req["variables"]["packages"] is None


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_packages_all_plugins_string(
    respx_stash_client: StashClient,
) -> None:
    """Test updating all plugin packages using string type."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("updatePackages", "job-update-2")
            )
        ]
    )

    job_id = await respx_stash_client.update_packages("Plugin")

    assert job_id == "job-update-2"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["type"] == "Plugin"
    assert req["variables"]["packages"] is None


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_packages_specific_dict(respx_stash_client: StashClient) -> None:
    """Test updating specific packages using dict input."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("updatePackages", "job-update-3")
            )
        ]
    )

    packages = [{"id": "scraper-1", "sourceURL": "https://example.com/scraper1.yml"}]

    job_id = await respx_stash_client.update_packages(PackageType.SCRAPER, packages)

    assert job_id == "job-update-3"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["packages"] == packages


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_packages_specific_input_objects(
    respx_stash_client: StashClient,
) -> None:
    """Test updating specific packages using PackageSpecInput objects."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("updatePackages", "job-update-4")
            )
        ]
    )

    packages = [
        PackageSpecInput(id="plugin-1", source_url="https://example.com/plugin1.yml"),
        PackageSpecInput(id="plugin-2", source_url="https://example.com/plugin2.yml"),
    ]

    job_id = await respx_stash_client.update_packages(PackageType.PLUGIN, packages)

    assert job_id == "job-update-4"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert len(req["variables"]["packages"]) == 2
    assert (
        req["variables"]["packages"][0]["sourceURL"]
        == "https://example.com/plugin1.yml"
    )


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_packages_no_job_id_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test that update_packages raises when no job ID returned."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("updatePackages", None))
        ]
    )

    with pytest.raises(ValueError, match="No job ID returned from server"):
        await respx_stash_client.update_packages(PackageType.SCRAPER)

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_packages_invalid_response_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test that update_packages raises on invalid response format."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(200, json={"data": {"updatePackages": None}})]
    )

    with pytest.raises(ValueError, match="No job ID returned from server"):
        await respx_stash_client.update_packages(PackageType.PLUGIN)

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_packages_server_error_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test that update_packages raises on server error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    with pytest.raises(StashGraphQLError, match="GraphQL query error"):
        await respx_stash_client.update_packages(PackageType.SCRAPER)

    # Verify route was called with correct mutation
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "updatePackages" in req["query"]


# =============================================================================
# uninstall_packages tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_uninstall_packages_scraper_enum_dict(
    respx_stash_client: StashClient,
) -> None:
    """Test uninstalling scraper packages using PackageType enum and dict input."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response("uninstallPackages", "job-uninstall-1"),
            )
        ]
    )

    packages = [{"id": "scraper-1", "sourceURL": "https://example.com/scraper1.yml"}]

    job_id = await respx_stash_client.uninstall_packages(PackageType.SCRAPER, packages)

    assert job_id == "job-uninstall-1"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "uninstallPackages" in req["query"]
    assert req["variables"]["type"] == "Scraper"
    assert req["variables"]["packages"] == packages


@pytest.mark.asyncio
@pytest.mark.unit
async def test_uninstall_packages_plugin_string_input_objects(
    respx_stash_client: StashClient,
) -> None:
    """Test uninstalling plugin packages using string type and PackageSpecInput objects."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response("uninstallPackages", "job-uninstall-2"),
            )
        ]
    )

    packages = [
        PackageSpecInput(id="plugin-1", source_url="https://example.com/plugin1.yml"),
        PackageSpecInput(id="plugin-2", source_url="https://example.com/plugin2.yml"),
    ]

    job_id = await respx_stash_client.uninstall_packages("Plugin", packages)

    assert job_id == "job-uninstall-2"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["type"] == "Plugin"
    # PackageSpecInput objects should be converted to dicts with camelCase
    assert len(req["variables"]["packages"]) == 2
    assert req["variables"]["packages"][0]["id"] == "plugin-1"
    assert (
        req["variables"]["packages"][0]["sourceURL"]
        == "https://example.com/plugin1.yml"
    )


@pytest.mark.asyncio
@pytest.mark.unit
async def test_uninstall_packages_multiple(respx_stash_client: StashClient) -> None:
    """Test uninstalling multiple packages."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200,
                json=create_graphql_response("uninstallPackages", "job-uninstall-3"),
            )
        ]
    )

    packages = [
        {"id": "pkg-1", "sourceURL": "https://example.com/pkg1.yml"},
        {"id": "pkg-2", "sourceURL": "https://example.com/pkg2.yml"},
        {"id": "pkg-3", "sourceURL": "https://example.com/pkg3.yml"},
    ]

    job_id = await respx_stash_client.uninstall_packages(PackageType.SCRAPER, packages)

    assert job_id == "job-uninstall-3"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert len(req["variables"]["packages"]) == 3


@pytest.mark.asyncio
@pytest.mark.unit
async def test_uninstall_packages_no_job_id_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test that uninstall_packages raises when no job ID returned."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("uninstallPackages", None))
        ]
    )

    packages = [{"id": "pkg-1", "sourceURL": "https://example.com/pkg1.yml"}]

    with pytest.raises(ValueError, match="No job ID returned from server"):
        await respx_stash_client.uninstall_packages(PackageType.PLUGIN, packages)

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_uninstall_packages_invalid_response_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test that uninstall_packages raises on invalid response format."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[httpx.Response(200, json={"data": {"uninstallPackages": None}})]
    )

    packages = [{"id": "pkg-1", "sourceURL": "https://example.com/pkg1.yml"}]

    with pytest.raises(ValueError, match="No job ID returned from server"):
        await respx_stash_client.uninstall_packages(PackageType.SCRAPER, packages)

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_uninstall_packages_server_error_raises(
    respx_stash_client: StashClient,
) -> None:
    """Test that uninstall_packages raises on server error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    packages = [{"id": "pkg-1", "sourceURL": "https://example.com/pkg1.yml"}]

    with pytest.raises(StashGraphQLError, match="GraphQL query error"):
        await respx_stash_client.uninstall_packages(PackageType.PLUGIN, packages)

    # Verify route was called with correct mutation
    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "uninstallPackages" in req["query"]
