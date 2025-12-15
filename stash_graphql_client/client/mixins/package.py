"""Package operations client functionality."""

from typing import Any

from ...types import Package, PackageSpecInput, PackageType
from ..protocols import StashClientProtocol


class PackageClientMixin(StashClientProtocol):
    """Mixin for package-related client methods."""

    async def install_packages(
        self,
        package_type: PackageType | str,
        packages: list[PackageSpecInput] | list[dict[str, Any]],
    ) -> str:
        """Install packages.

        Args:
            package_type: Type of packages to install (PackageType.SCRAPER or PackageType.PLUGIN)
            packages: List of PackageSpecInput objects or dictionaries containing:
                - id: Package ID (required)
                - sourceURL: Source URL for the package (required)

        Returns:
            Job ID for the installation task

        Raises:
            ValueError: If the input data is invalid
            gql.TransportError: If the request fails

        Examples:
            Install a scraper package:
            ```python
            from stash_graphql_client.types import PackageType, PackageSpecInput

            packages = [
                PackageSpecInput(id="package-id", source_url="https://example.com/package.yml")
            ]
            job_id = await client.install_packages(PackageType.SCRAPER, packages)
            print(f"Installation job started: {job_id}")
            ```

            Install multiple plugin packages using dictionaries:
            ```python
            packages = [
                {"id": "plugin-1", "sourceURL": "https://example.com/plugin1.yml"},
                {"id": "plugin-2", "sourceURL": "https://example.com/plugin2.yml"}
            ]
            job_id = await client.install_packages("Plugin", packages)
            ```
        """
        try:
            # Convert PackageType enum to string if needed
            type_str = (
                package_type.value
                if isinstance(package_type, PackageType)
                else package_type
            )

            # Convert PackageSpecInput objects to dicts if needed
            packages_data = []
            for pkg in packages:
                if isinstance(pkg, PackageSpecInput):
                    packages_data.append(pkg.to_graphql())
                else:
                    packages_data.append(pkg)

            result = await self.execute(
                """
                mutation InstallPackages($type: PackageType!, $packages: [PackageSpecInput!]!) {
                    installPackages(type: $type, packages: $packages)
                }
                """,
                {"type": type_str, "packages": packages_data},
            )

            job_id = result.get("installPackages")
            if not job_id:
                raise ValueError("No job ID returned from server")

            return str(job_id)

        except Exception as e:
            self.log.error(f"Failed to install packages: {e}")
            raise

    async def update_packages(
        self,
        package_type: PackageType | str,
        packages: list[PackageSpecInput] | list[dict[str, Any]] | None = None,
    ) -> str:
        """Update packages.

        Args:
            package_type: Type of packages to update (PackageType.SCRAPER or PackageType.PLUGIN)
            packages: Optional list of PackageSpecInput objects or dictionaries containing:
                - id: Package ID (required)
                - sourceURL: Source URL for the package (required)
                If None, all packages of the given type will be updated.

        Returns:
            Job ID for the update task

        Raises:
            ValueError: If the input data is invalid
            gql.TransportError: If the request fails

        Examples:
            Update all scraper packages:
            ```python
            from stash_graphql_client.types import PackageType

            job_id = await client.update_packages(PackageType.SCRAPER)
            print(f"Update job started: {job_id}")
            ```

            Update specific plugin packages:
            ```python
            from stash_graphql_client.types import PackageType, PackageSpecInput

            packages = [
                PackageSpecInput(id="plugin-id", source_url="https://example.com/plugin.yml")
            ]
            job_id = await client.update_packages(PackageType.PLUGIN, packages)
            ```

            Update using dictionaries:
            ```python
            packages = [
                {"id": "scraper-1", "sourceURL": "https://example.com/scraper1.yml"}
            ]
            job_id = await client.update_packages("Scraper", packages)
            ```
        """
        try:
            # Convert PackageType enum to string if needed
            type_str = (
                package_type.value
                if isinstance(package_type, PackageType)
                else package_type
            )

            # Convert PackageSpecInput objects to dicts if needed
            packages_data = None
            if packages is not None:
                packages_data = []
                for pkg in packages:
                    if isinstance(pkg, PackageSpecInput):
                        packages_data.append(pkg.to_graphql())
                    else:
                        packages_data.append(pkg)

            result = await self.execute(
                """
                mutation UpdatePackages($type: PackageType!, $packages: [PackageSpecInput!]) {
                    updatePackages(type: $type, packages: $packages)
                }
                """,
                {"type": type_str, "packages": packages_data},
            )

            job_id = result.get("updatePackages")
            if not job_id:
                raise ValueError("No job ID returned from server")

            return str(job_id)

        except Exception as e:
            self.log.error(f"Failed to update packages: {e}")
            raise

    async def uninstall_packages(
        self,
        package_type: PackageType | str,
        packages: list[PackageSpecInput] | list[dict[str, Any]],
    ) -> str:
        """Uninstall packages.

        Args:
            package_type: Type of packages to uninstall (PackageType.SCRAPER or PackageType.PLUGIN)
            packages: List of PackageSpecInput objects or dictionaries containing:
                - id: Package ID (required)
                - sourceURL: Source URL for the package (required)

        Returns:
            Job ID for the uninstallation task

        Raises:
            ValueError: If the input data is invalid
            gql.TransportError: If the request fails

        Examples:
            Uninstall a scraper package:
            ```python
            from stash_graphql_client.types import PackageType, PackageSpecInput

            packages = [
                PackageSpecInput(id="package-id", source_url="https://example.com/package.yml")
            ]
            job_id = await client.uninstall_packages(PackageType.SCRAPER, packages)
            print(f"Uninstallation job started: {job_id}")
            ```

            Uninstall multiple plugin packages using dictionaries:
            ```python
            packages = [
                {"id": "plugin-1", "sourceURL": "https://example.com/plugin1.yml"},
                {"id": "plugin-2", "sourceURL": "https://example.com/plugin2.yml"}
            ]
            job_id = await client.uninstall_packages("Plugin", packages)
            ```
        """
        try:
            # Convert PackageType enum to string if needed
            type_str = (
                package_type.value
                if isinstance(package_type, PackageType)
                else package_type
            )

            # Convert PackageSpecInput objects to dicts if needed
            packages_data = []
            for pkg in packages:
                if isinstance(pkg, PackageSpecInput):
                    packages_data.append(pkg.to_graphql())
                else:
                    packages_data.append(pkg)

            result = await self.execute(
                """
                mutation UninstallPackages($type: PackageType!, $packages: [PackageSpecInput!]!) {
                    uninstallPackages(type: $type, packages: $packages)
                }
                """,
                {"type": type_str, "packages": packages_data},
            )

            job_id = result.get("uninstallPackages")
            if not job_id:
                raise ValueError("No job ID returned from server")

            return str(job_id)

        except Exception as e:
            self.log.error(f"Failed to uninstall packages: {e}")
            raise

    async def installed_packages(
        self,
        package_type: PackageType | str,
    ) -> list[Package]:
        """List installed packages.

        Args:
            package_type: Type of packages to list (PackageType.SCRAPER or PackageType.PLUGIN)

        Returns:
            List of Package objects representing installed packages

        Raises:
            gql.TransportError: If the request fails

        Examples:
            List all installed scrapers:
            ```python
            from stash_graphql_client.types import PackageType

            packages = await client.installed_packages(PackageType.SCRAPER)
            for pkg in packages:
                print(f"{pkg.name} v{pkg.version} - {pkg.package_id}")
            ```

            List all installed plugins:
            ```python
            packages = await client.installed_packages("Plugin")
            print(f"Found {len(packages)} installed plugins")
            ```
        """
        try:
            # Convert PackageType enum to string if needed
            type_str = (
                package_type.value
                if isinstance(package_type, PackageType)
                else package_type
            )

            result = await self.execute(
                """
                query InstalledPackages($type: PackageType!) {
                    installedPackages(type: $type) {
                        package_id
                        name
                        version
                        date
                        requires {
                            package_id
                            name
                            version
                            date
                            sourceURL
                        }
                        sourceURL
                        source_package {
                            package_id
                            name
                            version
                            date
                            sourceURL
                        }
                        metadata
                    }
                }
                """,
                {"type": type_str},
            )

            package_data_list = result.get("installedPackages", [])
            return [
                self._decode_result(Package, pkg_data) for pkg_data in package_data_list
            ]

        except Exception as e:
            self.log.error(f"Failed to list installed packages: {e}")
            return []

    async def available_packages(
        self,
        package_type: PackageType | str,
        source: str,
    ) -> list[Package]:
        """List available packages from a source.

        Args:
            package_type: Type of packages to list (PackageType.SCRAPER or PackageType.PLUGIN)
            source: Source URL to query for available packages

        Returns:
            List of Package objects representing available packages

        Raises:
            gql.TransportError: If the request fails

        Examples:
            List available scrapers from official source:
            ```python
            from stash_graphql_client.types import PackageType

            packages = await client.available_packages(
                PackageType.SCRAPER,
                "https://stashapp.github.io/scrapers"
            )
            for pkg in packages:
                print(f"{pkg.name} v{pkg.version} - {pkg.package_id}")
            ```

            List available plugins:
            ```python
            packages = await client.available_packages(
                "Plugin",
                "https://stashapp.github.io/plugins"
            )
            print(f"Found {len(packages)} available plugins")
            ```
        """
        try:
            # Convert PackageType enum to string if needed
            type_str = (
                package_type.value
                if isinstance(package_type, PackageType)
                else package_type
            )

            result = await self.execute(
                """
                query AvailablePackages($type: PackageType!, $source: String!) {
                    availablePackages(type: $type, source: $source) {
                        package_id
                        name
                        version
                        date
                        requires {
                            package_id
                            name
                            version
                            date
                            sourceURL
                        }
                        sourceURL
                        source_package {
                            package_id
                            name
                            version
                            date
                            sourceURL
                        }
                        metadata
                    }
                }
                """,
                {"type": type_str, "source": source},
            )

            package_data_list = result.get("availablePackages", [])
            return [
                self._decode_result(Package, pkg_data) for pkg_data in package_data_list
            ]

        except Exception as e:
            self.log.error(f"Failed to list available packages: {e}")
            return []
