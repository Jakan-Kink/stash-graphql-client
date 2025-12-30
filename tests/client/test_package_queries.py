"""Unit tests for PackageClientMixin query operations.

These tests mock at the HTTP boundary using respx, allowing real code execution
through the entire GraphQL client stack including serialization/deserialization.
"""

import json

import httpx
import pytest
import respx

from stash_graphql_client import StashClient
from stash_graphql_client.types import PackageType
from stash_graphql_client.types.unset import is_set
from tests.fixtures import create_graphql_response


# =============================================================================
# Helper functions for creating package test data
# =============================================================================


def create_package_dict(
    package_id: str = "test-package",
    name: str = "Test Package",
    version: str | None = "1.0.0",
    date: str | None = "2024-01-01T00:00:00Z",
    requires: list[dict] | None = None,
    source_url: str = "https://example.com/package.yml",
    source_package: dict | None = None,
    metadata: dict | None = None,
) -> dict:
    """Create a Package dictionary for testing."""
    return {
        "package_id": package_id,
        "name": name,
        "version": version,
        "date": date,
        "requires": requires or [],
        "sourceURL": source_url,
        "source_package": source_package,
        "metadata": metadata or {},
    }


# =============================================================================
# installed_packages tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_installed_packages_scraper_enum(respx_stash_client: StashClient) -> None:
    """Test getting installed scraper packages using PackageType enum."""
    package_data = create_package_dict(
        package_id="scraper-1",
        name="IAFD Scraper",
        version="1.2.3",
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("installedPackages", [package_data])
            )
        ]
    )

    packages = await respx_stash_client.installed_packages(PackageType.SCRAPER)

    assert len(packages) == 1
    assert packages[0].package_id == "scraper-1"
    assert packages[0].name == "IAFD Scraper"
    assert packages[0].version == "1.2.3"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "installedPackages" in req["query"]
    assert req["variables"]["type"] == "Scraper"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_installed_packages_plugin_string(
    respx_stash_client: StashClient,
) -> None:
    """Test getting installed plugin packages using string type."""
    package_data = create_package_dict(
        package_id="plugin-1",
        name="Test Plugin",
        version="2.0.0",
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("installedPackages", [package_data])
            )
        ]
    )

    packages = await respx_stash_client.installed_packages("Plugin")

    assert len(packages) == 1
    assert packages[0].package_id == "plugin-1"
    assert packages[0].name == "Test Plugin"
    assert packages[0].version == "2.0.0"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["type"] == "Plugin"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_installed_packages_multiple(respx_stash_client: StashClient) -> None:
    """Test getting multiple installed packages."""
    packages_data = [
        create_package_dict(
            package_id="pkg-1",
            name="Package One",
            version="1.0.0",
        ),
        create_package_dict(
            package_id="pkg-2",
            name="Package Two",
            version="2.0.0",
        ),
        create_package_dict(
            package_id="pkg-3",
            name="Package Three",
            version="3.0.0",
        ),
    ]

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("installedPackages", packages_data)
            )
        ]
    )

    packages = await respx_stash_client.installed_packages(PackageType.SCRAPER)

    assert len(packages) == 3
    assert packages[0].package_id == "pkg-1"
    assert packages[1].package_id == "pkg-2"
    assert packages[2].package_id == "pkg-3"

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_installed_packages_with_dependencies(
    respx_stash_client: StashClient,
) -> None:
    """Test installed packages with dependency information."""
    dep_package = create_package_dict(
        package_id="dep-1",
        name="Dependency Package",
        version="1.0.0",
    )

    package_data = create_package_dict(
        package_id="main-pkg",
        name="Main Package",
        version="2.0.0",
        requires=[dep_package],
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("installedPackages", [package_data])
            )
        ]
    )

    packages = await respx_stash_client.installed_packages(PackageType.PLUGIN)

    assert is_set(packages)
    assert len(packages) == 1
    assert packages[0].package_id == "main-pkg"
    assert is_set(packages[0].requires)
    assert len(packages[0].requires) == 1
    assert packages[0].requires[0].package_id == "dep-1"

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_installed_packages_with_source_package(
    respx_stash_client: StashClient,
) -> None:
    """Test installed packages with source package information."""
    source_pkg = create_package_dict(
        package_id="source-1",
        name="Source Package",
        version="1.5.0",
    )

    package_data = create_package_dict(
        package_id="derived-pkg",
        name="Derived Package",
        version="1.5.1",
        source_package=source_pkg,
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("installedPackages", [package_data])
            )
        ]
    )

    packages = await respx_stash_client.installed_packages(PackageType.SCRAPER)

    assert is_set(packages)
    assert len(packages) == 1
    assert packages[0].package_id == "derived-pkg"
    assert packages[0].source_package is not None
    assert is_set(packages[0].source_package)
    assert packages[0].source_package.package_id == "source-1"
    assert packages[0].source_package.version == "1.5.0"

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_installed_packages_with_metadata(
    respx_stash_client: StashClient,
) -> None:
    """Test installed packages with metadata."""
    package_data = create_package_dict(
        package_id="pkg-meta",
        name="Package With Metadata",
        version="1.0.0",
        metadata={
            "author": "Test Author",
            "description": "A test package",
            "tags": ["test", "example"],
        },
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("installedPackages", [package_data])
            )
        ]
    )

    packages = await respx_stash_client.installed_packages(PackageType.PLUGIN)

    assert is_set(packages)
    assert len(packages) == 1
    assert packages[0].package_id == "pkg-meta"
    assert is_set(packages[0].metadata)
    assert packages[0].metadata["author"] == "Test Author"
    assert "test" in packages[0].metadata["tags"]

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_installed_packages_empty(respx_stash_client: StashClient) -> None:
    """Test getting installed packages when none are installed."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("installedPackages", []))
        ]
    )

    packages = await respx_stash_client.installed_packages(PackageType.SCRAPER)

    assert len(packages) == 0
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_installed_packages_error_returns_empty(
    respx_stash_client: StashClient,
) -> None:
    """Test that installed_packages returns empty list on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    packages = await respx_stash_client.installed_packages(PackageType.PLUGIN)

    assert len(packages) == 0
    assert len(graphql_route.calls) == 1


# =============================================================================
# available_packages tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_available_packages_scraper_enum(respx_stash_client: StashClient) -> None:
    """Test getting available scraper packages using PackageType enum."""
    package_data = create_package_dict(
        package_id="scraper-available-1",
        name="Available Scraper",
        version="1.5.0",
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("availablePackages", [package_data])
            )
        ]
    )

    packages = await respx_stash_client.available_packages(
        PackageType.SCRAPER,
        "https://stashapp.github.io/scrapers",
    )

    assert len(packages) == 1
    assert packages[0].package_id == "scraper-available-1"
    assert packages[0].name == "Available Scraper"
    assert packages[0].version == "1.5.0"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert "availablePackages" in req["query"]
    assert req["variables"]["type"] == "Scraper"
    assert req["variables"]["source"] == "https://stashapp.github.io/scrapers"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_available_packages_plugin_string(
    respx_stash_client: StashClient,
) -> None:
    """Test getting available plugin packages using string type."""
    package_data = create_package_dict(
        package_id="plugin-available-1",
        name="Available Plugin",
        version="2.1.0",
    )

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("availablePackages", [package_data])
            )
        ]
    )

    packages = await respx_stash_client.available_packages(
        "Plugin",
        "https://stashapp.github.io/plugins",
    )

    assert len(packages) == 1
    assert packages[0].package_id == "plugin-available-1"
    assert packages[0].name == "Available Plugin"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["type"] == "Plugin"
    assert req["variables"]["source"] == "https://stashapp.github.io/plugins"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_available_packages_multiple(respx_stash_client: StashClient) -> None:
    """Test getting multiple available packages."""
    packages_data = [
        create_package_dict(
            package_id="avail-1",
            name="Available One",
            version="1.0.0",
        ),
        create_package_dict(
            package_id="avail-2",
            name="Available Two",
            version="2.0.0",
        ),
        create_package_dict(
            package_id="avail-3",
            name="Available Three",
            version="3.0.0",
        ),
    ]

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("availablePackages", packages_data)
            )
        ]
    )

    packages = await respx_stash_client.available_packages(
        PackageType.SCRAPER,
        "https://example.com/packages",
    )

    assert len(packages) == 3
    assert packages[0].package_id == "avail-1"
    assert packages[1].package_id == "avail-2"
    assert packages[2].package_id == "avail-3"

    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_available_packages_custom_source(
    respx_stash_client: StashClient,
) -> None:
    """Test getting available packages from custom source URL."""
    package_data = create_package_dict(
        package_id="custom-pkg",
        name="Custom Package",
        version="1.0.0",
    )

    custom_source = "https://mycustomrepo.com/packages.json"

    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(
                200, json=create_graphql_response("availablePackages", [package_data])
            )
        ]
    )

    packages = await respx_stash_client.available_packages(
        PackageType.PLUGIN,
        custom_source,
    )

    assert len(packages) == 1
    assert packages[0].package_id == "custom-pkg"

    assert len(graphql_route.calls) == 1
    req = json.loads(graphql_route.calls[0].request.content)
    assert req["variables"]["source"] == custom_source


@pytest.mark.asyncio
@pytest.mark.unit
async def test_available_packages_empty(respx_stash_client: StashClient) -> None:
    """Test getting available packages when none are available."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(200, json=create_graphql_response("availablePackages", []))
        ]
    )

    packages = await respx_stash_client.available_packages(
        PackageType.SCRAPER,
        "https://empty.com/packages",
    )

    assert len(packages) == 0
    assert len(graphql_route.calls) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_available_packages_error_returns_empty(
    respx_stash_client: StashClient,
) -> None:
    """Test that available_packages returns empty list on error."""
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        side_effect=[
            httpx.Response(500, json={"errors": [{"message": "Server error"}]})
        ]
    )

    packages = await respx_stash_client.available_packages(
        PackageType.PLUGIN,
        "https://failing.com/packages",
    )

    assert len(packages) == 0
    assert len(graphql_route.calls) == 1
