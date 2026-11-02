"""Persistent rosbridge WebSocket client for calling ROS services on the aircraft (ACMS).

rosbridge speaks JSON over a WebSocket. A service call is one `call_service` message tagged
with an `id`; rosbridge answers with a `service_response` carrying the same `id`. One
connection is shared by the whole process, opened on the first call and reopened on the
next call after it drops.
"""

import asyncio
import itertools
import json
import logging
from typing import Any

from django.conf import settings
from websockets.asyncio.client import ClientConnection, connect
from websockets.exceptions import ConnectionClosed

logger = logging.getLogger(__name__)


class RosbridgeError(Exception):
    """rosbridge could not be reached, the connection dropped, or the call failed."""


class RosbridgeTimeout(RosbridgeError):
    """No response arrived within the timeout."""


class RosbridgeClient:
    def __init__(self, url: str, connect_timeout: float = 5.0):
        self.url = url
        self.connect_timeout = connect_timeout
        self._ws: ClientConnection | None = None
        self._reader_task: asyncio.Task | None = None
        self._pending: dict[str, asyncio.Future] = {}
        self._ids = itertools.count(1)
        self._lock: asyncio.Lock | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    async def call_service(
        self, service: str, args: dict[str, Any] | None = None, timeout: float = 15.0
    ) -> dict[str, Any]:
        """Call a ROS service and return its response fields (`values`).

        Raises RosbridgeTimeout if no answer arrives in `timeout` seconds and RosbridgeError
        if rosbridge is unreachable, the connection drops, or rosbridge reports the call failed
        (e.g. the service does not exist).
        """
        ws = await self._ensure_connected()
        call_id = f"gcom_{next(self._ids)}"
        future = asyncio.get_running_loop().create_future()
        self._pending[call_id] = future
        message = {"op": "call_service", "id": call_id, "service": service, "args": args or {}}
        try:
            await ws.send(json.dumps(message))
            response = await asyncio.wait_for(future, timeout)
        except asyncio.TimeoutError as e:
            raise RosbridgeTimeout(f"{service}: no response within {timeout:.0f} s") from e
        except ConnectionClosed as e:
            raise RosbridgeError(f"{service}: connection to rosbridge closed") from e
        finally:
            self._pending.pop(call_id, None)

        # result is false when rosbridge itself could not complete the call; values is then
        # an error string instead of the response fields.
        if not response.get("result", False):
            raise RosbridgeError(f"{service}: {response.get('values')}")
        return response.get("values") or {}

    async def _ensure_connected(self) -> ClientConnection:
        loop = asyncio.get_running_loop()
        if self._loop is not loop:
            # First call, or the server restarted its event loop. Anything tied to the old
            # loop is unusable from this one, so start fresh.
            self._reset(loop)

        async with self._lock:
            if self._ws is not None:
                return self._ws
            logger.info("Connecting to rosbridge at %s", self.url)
            try:
                self._ws = await asyncio.wait_for(connect(self.url), self.connect_timeout)
            except (OSError, asyncio.TimeoutError) as e:
                raise RosbridgeError(f"cannot connect to rosbridge at {self.url}: {e}") from e
            self._reader_task = loop.create_task(self._read(self._ws))
            return self._ws

    async def _read(self, ws: ClientConnection) -> None:
        """Hand each service_response to the call waiting on its id until the socket closes."""
        try:
            async for raw in ws:
                try:
                    message = json.loads(raw)
                except json.JSONDecodeError:
                    logger.warning("Ignoring non-JSON message from rosbridge")
                    continue
                if message.get("op") != "service_response":
                    continue
                future = self._pending.get(message.get("id"))
                if future is not None and not future.done():
                    future.set_result(message)
        except ConnectionClosed:
            pass
        finally:
            logger.warning("rosbridge connection closed; reconnecting on next call")
            if self._ws is ws:
                self._ws = None
            for future in self._pending.values():
                if not future.done():
                    future.set_exception(RosbridgeError("connection to rosbridge closed"))

    def _reset(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop
        self._lock = asyncio.Lock()
        self._ws = None
        self._reader_task = None
        self._pending = {}


_client: RosbridgeClient | None = None


def get_client() -> RosbridgeClient:
    """The process-wide client for settings.ROSBRIDGE_URL."""
    global _client
    if _client is None:
        _client = RosbridgeClient(settings.ROSBRIDGE_URL)
    return _client
