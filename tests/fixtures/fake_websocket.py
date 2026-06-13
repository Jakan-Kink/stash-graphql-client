"""Transport-level fake websocket for gql's WebsocketsTransport.

``FakeSocket`` stands in for the ``websockets.asyncio.client.ClientConnection``
that gql's ``WebsocketsTransport`` obtains from ``await websockets.connect(...)``.
Patched at that seam (``fake_ws_connection``), it lets the REAL gql transport and
the real ``StashClient`` subscription code run against scripted traffic with no
network and no live Stash — the WebSocket parallel to respx for HTTP. Every client
frame is recorded in ``.sent`` for ``dump_ws_calls()`` (mirrors
``dump_graphql_calls()``).

It is a faithful protocol negotiator: it reproduces the subprotocol selection a
real Stash server performs, then speaks that protocol's codec.

* Stash registers gqlgen's ``transport.Websocket`` with no override, so the
  server's supported list is ``["graphql-ws", "graphql-transport-ws"]`` and
  gorilla's ``selectSubprotocol`` is server-order-wins: the first server entry the
  client *also* offers wins (default ``graphql-ws`` when nothing matches).
* The Python ``gql`` client offers ``["graphql-ws", "graphql-transport-ws"]``
  (apollo first) -> negotiates apollo ``graphql-ws`` (``start`` / ``data`` /
  ``stop``).
* A browser graphql-ws client offers only ``graphql-transport-ws`` -> negotiates
  ``graphql-transport-ws`` (``subscribe`` / ``next`` / ``complete``) — which is
  what shows up in DevTools.

The fake negotiates from the client's offered ``subprotocols`` (passed to
``websockets.connect``), advertises the result via the ``Sec-WebSocket-Protocol``
handshake response header (gql reads the negotiated protocol from there), and
emits ``data`` vs ``next`` accordingly — so it matches whichever client connects.

Fixtures and helpers live here per CLAUDE.md (fixtures under ``tests/fixtures/``).
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Sequence
from contextlib import contextmanager
from typing import Any
from unittest.mock import patch

from websockets.datastructures import Headers
from websockets.exceptions import ConnectionClosedOK
from websockets.frames import Close


_APOLLO_SUBPROTOCOL = "graphql-ws"
_TRANSPORT_WS_SUBPROTOCOL = "graphql-transport-ws"
# gqlgen's supportedSubprotocols, in order. gorilla's selectSubprotocol is
# server-order-wins, so this order (not the client's) breaks ties.
_SERVER_SUBPROTOCOLS = (_APOLLO_SUBPROTOCOL, _TRANSPORT_WS_SUBPROTOCOL)
_CLEAN_CLOSE = Close(code=1000, reason="")
_CLOSED = object()  # sentinel placed on the inbox by close() to end recv()


def _select_subprotocol(offered: Sequence[str] | None) -> str:
    """Pick the subprotocol a real Stash (gqlgen + gorilla) would negotiate.

    Server-order-wins over ``_SERVER_SUBPROTOCOLS``; defaults to apollo
    ``graphql-ws`` when the client offered nothing we support (gqlgen's
    documented backward-compatible default).
    """
    offered_set = set(offered or [])
    for server_protocol in _SERVER_SUBPROTOCOLS:
        if server_protocol in offered_set:
            return server_protocol
    return _APOLLO_SUBPROTOCOL


class _HandshakeResponse:
    """Minimal stand-in for ``ClientConnection.response`` (the upgrade response)."""

    def __init__(self, headers: Headers) -> None:
        self.headers = headers


class FakeSocket:
    """Reactive fake websocket — a tiny in-process Stash subscription server.

    Reacts to the client frames gql sends and enqueues the server frames a real
    Stash would return, so the real transport + subscription code path executes.
    Speaks whichever subprotocol it negotiates from the client's offer.

    Args:
        events: GraphQL ``data`` payloads emitted in order (as ``data``/``next``
            frames, per negotiated protocol) in response to the client's
            ``start``/``subscribe``, then a ``complete``. Each entry is the
            ``data`` dict, e.g. ``{"jobsSubscribe": {...}}``.

    Attributes:
        sent: every client frame, decoded to dicts, in send order (for dumps).
        subprotocol: the negotiated subprotocol (set when the client connects).
    """

    def __init__(self, events: Sequence[dict[str, Any]] | None = None) -> None:
        self.events: list[dict[str, Any]] = list(events or [])
        # complete=False keeps the subscription open after the events (recv
        # blocks) — used to exercise client-side timeouts. error, when set, is
        # emitted as a server ``error`` frame instead of data (gql raises
        # TransportQueryError) — used to exercise subscription-failure paths.
        self.complete = True
        self.error: Any = None
        self.sent: list[dict[str, Any]] = []
        self.subprotocol = _APOLLO_SUBPROTOCOL
        self.response = _HandshakeResponse(Headers())
        self.close_code: int | None = None
        self._closed = False
        # Loop binds lazily on first get/put, so constructing outside a running
        # loop is safe; all queue ops happen inside the test's event loop.
        self._inbox: asyncio.Queue[Any] = asyncio.Queue()
        self.negotiate(None)

    def negotiate(self, offered: Sequence[str] | None) -> None:
        """Select + advertise the subprotocol exactly as real Stash would."""
        self.subprotocol = _select_subprotocol(offered)
        headers = Headers()
        headers["Sec-WebSocket-Protocol"] = self.subprotocol
        self.response = _HandshakeResponse(headers)

    @property
    def _data_message_type(self) -> str:
        """``next`` for graphql-transport-ws, ``data`` for apollo graphql-ws."""
        if self.subprotocol == _TRANSPORT_WS_SUBPROTOCOL:
            return "next"
        return "data"

    async def send(self, message: str) -> None:
        """Client -> server frame. Records it and enqueues scripted responses."""
        frame = json.loads(message)
        self.sent.append(frame)
        msg_type = frame.get("type")
        if msg_type == "connection_init":
            self._emit({"type": "connection_ack"})
        elif msg_type in ("start", "subscribe"):  # apollo / graphql-transport-ws
            query_id = frame["id"]
            if self.error is not None:
                self._emit({"id": query_id, "type": "error", "payload": self.error})
                return
            for event in self.events:
                self._emit(
                    {
                        "id": query_id,
                        "type": self._data_message_type,
                        "payload": {"data": event},
                    }
                )
            if self.complete:
                self._emit({"id": query_id, "type": "complete"})
            # complete=False: no trailing complete, so recv blocks (open stream).
        # "stop" / "complete" / "connection_terminate": already queued on start.

    async def recv(self) -> str:
        """Server -> client frame. Blocks until one is available; raises on close."""
        item = await self._inbox.get()
        if item is _CLOSED:
            # websockets >=15 requires rcvd_then_sent (True/False) when both the
            # received and sent close frames are present.
            raise ConnectionClosedOK(_CLEAN_CLOSE, _CLEAN_CLOSE, True)
        return item

    async def close(self, code: int = 1000, reason: str = "") -> None:
        """Mark closed and unblock a pending ``recv`` so the listen loop exits."""
        if not self._closed:
            self._closed = True
            self.close_code = code
            self._inbox.put_nowait(_CLOSED)

    def _emit(self, frame: dict[str, Any]) -> None:
        self._inbox.put_nowait(json.dumps(frame))


def get_fake_ws(client: Any) -> FakeSocket:
    """Return the FakeSocket the respx client fixtures attached to a StashClient.

    Typed accessor for the dynamically-injected ``_fake_ws`` test attribute, so
    subscription tests get a real ``FakeSocket`` type instead of ``Any``.
    """
    return client._fake_ws


def dump_ws_calls(fake: FakeSocket, label: str = "WebSocket frames") -> None:
    """Print the client frames a ``FakeSocket`` recorded (mirrors dump_graphql_calls)."""
    print(f"\n{'=' * 70}\n  {label} ({len(fake.sent)} total)\n{'=' * 70}")
    for index, frame in enumerate(fake.sent):
        print(f"  [{index}] {json.dumps(frame)}")
    print(f"{'=' * 70}\n")


@contextmanager
def fake_ws_connection(events: Sequence[dict[str, Any]] | None = None):
    """Patch ``websockets.connect`` so gql's ws transport receives a ``FakeSocket``.

    The fake negotiates the subprotocol from the offered list gql passes to
    ``websockets.connect``, exactly as real Stash would.

    Args:
        events: scripted ``data`` payloads for the subscription (see ``FakeSocket``).

    Yields:
        The ``FakeSocket`` instance, so tests can script ``.events`` and inspect
        ``.sent`` / ``.subprotocol``.
    """
    fake = FakeSocket(events=events)

    async def _connect(*_args: Any, **kwargs: Any) -> FakeSocket:
        fake.negotiate(kwargs.get("subprotocols"))
        return fake

    with patch("websockets.connect", _connect):
        yield fake
