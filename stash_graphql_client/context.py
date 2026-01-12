"""Context manager for Stash client."""

from __future__ import annotations

import asyncio
from typing import Any

from multidict import CIMultiDict

from .client import StashClient
from .logging import client_logger as logger
from .store import StashEntityStore
from .types.base import StashObject


class StashContext:
    """Context manager for Stash client.

    This class provides a high-level interface for managing Stash client
    connections, including:
    - Connection configuration
    - Client lifecycle management
    - Interface access
    - Reference counting for safe concurrent usage

    Example:
        ```python
        # Create context with connection details
        context = StashContext(conn={
            "Scheme": "http",
            "Host": "localhost",
            "Port": 9999,
            "ApiKey": "your_api_key",
        })

        # Use context manager (safe for concurrent tasks with singleton)
        async with context as client:
            performer = await client.find_performer("123")

            # Access entity store for caching and advanced queries
            store = context.store
            scene = await store.get(Scene, "456")

        # Or use directly
        client = context.client
        store = context.store
        performer = await client.find_performer("123")
        await context.close()

        # Safe for concurrent tasks when using singleton
        await asyncio.gather(
            task1(context),  # Each task uses async with
            task2(context),  # Reference counting prevents premature closure
        )
        ```
    """

    def __init__(
        self,
        conn: dict[str, Any] | None = None,
        verify_ssl: bool = True,
    ) -> None:
        """Initialize context.

        Args:
            conn: Connection details dictionary (case-insensitive keys)
            verify_ssl: Whether to verify SSL certificates
        """
        # Normalize connection keys to canonical case
        self.conn = self._normalize_conn_keys(conn or {})
        self.verify_ssl = verify_ssl
        self._client: StashClient | None = None
        self._store: StashEntityStore | None = None
        self._ref_count: int = 0
        self._ref_lock: asyncio.Lock = asyncio.Lock()

    @staticmethod
    def _normalize_conn_keys(conn: dict[str, Any]) -> dict[str, Any]:
        """Normalize connection dict keys to canonical case.

        Accepts case-insensitive input keys and returns dict with
        canonical key names (Logger, Scheme, Host, Port, ApiKey).

        Args:
            conn: Connection dict with any case keys

        Returns:
            dict with normalized canonical keys
        """
        if not conn:
            return {}

        # Use CIMultiDict for case-insensitive lookup during normalization
        ci_conn = CIMultiDict(conn)

        # Canonical key mappings (lowercase -> canonical)
        canonical_keys = {
            "logger": "Logger",
            "scheme": "Scheme",
            "host": "Host",
            "port": "Port",
            "apikey": "ApiKey",
        }

        normalized = {}
        for lower_key, canonical_key in canonical_keys.items():
            # Use case-insensitive lookup, store with canonical key
            # Check key exists (not value truthiness) to preserve falsy values like port=0
            if lower_key in ci_conn:
                normalized[canonical_key] = ci_conn[lower_key]

        return normalized

    @property
    def interface(self) -> StashClient:
        """Get Stash interface (alias for client).

        Returns:
            StashClient instance

        Raises:
            RuntimeError: If client is not initialized
        """
        if self._client is None:
            logger.error("Client not initialized - use get_client() first")
            raise RuntimeError("Client not initialized - use get_client() first")
        return self._client

    async def get_client(self) -> StashClient:
        """Get initialized Stash client.

        Returns:
            StashClient instance

        Raises:
            RuntimeError: If client initialization fails
        """
        logger.debug(
            f"get_client called on {id(self)}, current _client: {self._client}"
        )
        if self._client is None:
            # Normalize conn keys in case someone modified self.conn directly
            normalized_conn = self._normalize_conn_keys(self.conn)
            self._client = StashClient(
                conn=normalized_conn if normalized_conn else None,
                verify_ssl=self.verify_ssl,
            )
            try:
                await self._client.initialize()
                logger.debug(
                    f"Client initialization complete, _client set to {self._client}"
                )

                # Initialize entity store and wire it to StashObject
                self._store = StashEntityStore(self._client)
                StashObject._store = self._store
                logger.debug("Entity store initialized and wired to StashObject")

            except Exception as e:
                logger.error(f"Client initialization failed: {e}")
                self._client = None
                raise RuntimeError(f"Failed to initialize Stash client: {e}")
        return self._client

    @property
    def client(self) -> StashClient:
        """Get client instance.

        Returns:
            StashClient instance

        Raises:
            RuntimeError: If client is not initialized
        """
        logger.debug(
            f"client property accessed on {id(self)}, current _client: {self._client}"
        )
        if self._client is None:
            logger.error("Client not initialized - use get_client() first")
            raise RuntimeError("Client not initialized - use get_client() first")
        return self._client

    @property
    def store(self) -> StashEntityStore:
        """Get entity store instance.

        Returns:
            StashEntityStore instance wired to StashObject identity map

        Raises:
            RuntimeError: If store is not initialized
        """
        logger.debug(
            f"store property accessed on {id(self)}, current _store: {self._store}"
        )
        if self._store is None:
            logger.error("Store not initialized - use get_client() first")
            raise RuntimeError("Store not initialized - use get_client() first")
        return self._store

    @property
    def ref_count(self) -> int:
        """Get current reference count.

        Returns:
            Number of active async context managers using this context
        """
        return self._ref_count

    async def close(self, force: bool = False, _internal: bool = False) -> None:
        """Close client connection.

        Args:
            force: If True, force close even if reference count > 0.
                   Use with caution as this may break concurrent tasks.
            _internal: Internal flag indicating call from __aexit__ (already has lock)

        Note:
            When using the singleton context with async context managers,
            manual close() is not needed - reference counting handles cleanup.
            Only call manually when you created the context directly and are
            done with it.
        """
        # If called internally from __aexit__, we already have the lock
        if _internal:
            if self._client is not None:
                await self._client.close()
                self._client = None
                logger.debug("StashClient closed")
            if self._store is not None:
                # Clear store cache and unwire from StashObject
                self._store.invalidate_all()
                StashObject._store = None
                self._store = None
                logger.debug("Entity store cleared and unwired")
            return

        # Manual call - need to acquire lock
        async with self._ref_lock:
            if self._ref_count > 0 and not force:
                logger.warning(
                    f"Attempted to close StashContext with {self._ref_count} active references. "
                    "Close will be deferred until all context managers exit. "
                    "Use force=True to override (not recommended)."
                )
                return

            if self._client is not None:
                await self._client.close()
                self._client = None
                logger.debug("StashClient closed")

            if self._store is not None:
                # Clear store cache and unwire from StashObject
                self._store.invalidate_all()
                StashObject._store = None
                self._store = None
                logger.debug("Entity store cleared and unwired")

    async def __aenter__(self) -> StashClient:
        """Enter async context manager.

        Increments reference count to track concurrent usage.
        Safe for use with singleton context in concurrent tasks.
        """
        async with self._ref_lock:
            self._ref_count += 1
            logger.debug(
                f"StashContext entered, ref_count: {self._ref_count} (id: {id(self)})"
            )
        return await self.get_client()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Exit async context manager.

        Decrements reference count and only closes client when count reaches 0.
        This prevents premature closure when multiple concurrent tasks use the
        same singleton context.
        """
        async with self._ref_lock:
            self._ref_count -= 1
            logger.debug(
                f"StashContext exiting, ref_count: {self._ref_count} (id: {id(self)})"
            )

            # Only close if no one else is using the client
            if self._ref_count == 0:
                logger.debug("Reference count reached 0, closing client")
                # Call with _internal=True since we already have the lock
                await self.close(_internal=True)
            else:
                logger.debug(
                    f"Reference count still {self._ref_count}, keeping client open"
                )
