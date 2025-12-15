"""Version client functionality."""

from ... import fragments
from ...types import LatestVersion, Version
from ..protocols import StashClientProtocol


class VersionClientMixin(StashClientProtocol):
    """Mixin for version-related methods."""

    async def version(self) -> Version:
        """Get the current Stash version information.

        Returns:
            Version object containing version, hash, and build_time

        Examples:
            Get current version:
            ```python
            version = await client.version()
            print(f"Stash version: {version.version}")
            print(f"Git hash: {version.hash}")
            print(f"Build time: {version.build_time}")
            ```
        """
        result = await self.execute(fragments.VERSION_QUERY)
        return self._decode_result(Version, result["version"])

    async def latestversion(self) -> LatestVersion:
        """Get the latest available Stash version from GitHub.

        Returns:
            LatestVersion object containing version, shorthash, release_date, and url

        Examples:
            Check for updates:
            ```python
            current = await client.version()
            latest = await client.latestversion()
            if current.version != latest.version:
                print(f"Update available: {latest.version}")
                print(f"Release date: {latest.release_date}")
                print(f"Download: {latest.url}")
            ```
        """
        result = await self.execute(fragments.LATEST_VERSION_QUERY)
        return self._decode_result(LatestVersion, result["latestversion"])
