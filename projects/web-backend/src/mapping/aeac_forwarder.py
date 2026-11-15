import asyncio
import json
import os
import time
from urllib.parse import quote

from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed

DEFAULT_URL = "wss://o61e21rvtd.execute-api.ca-central-1.amazonaws.com/prod"
RECONNECT_DELAY_S = 2
MAX_RECONNECT_DELAY_S = 30


class AeacForwarder:
    def __init__(self, url, token, on_traffic=None):
        separator = "&" if "?" in url else "?"
        self.url = f"{url}{separator}Authorization={quote(token, safe='')}"
        self.ws = None
        self.on_traffic = on_traffic
        self.latest_traffic = None
        self.latest_traffic_at = None
        self.sent = 0
        self.acked = 0

    async def send_telemetry(self, telemetry):
        if self.ws is None:
            return False

        try:
            await self.ws.send(json.dumps({"action": "telemetry", "data": telemetry}))
            self.sent += 1
            return True
        except ConnectionClosed:
            return False

    async def run(self):
        delay = RECONNECT_DELAY_S

        while True:
            try:
                async with connect(self.url, ping_interval=None) as ws:
                    self.ws = ws
                    delay = RECONNECT_DELAY_S
                    print("[AEAC] Connected")

                    async for raw in ws:
                        await self.handle(raw)

            except asyncio.CancelledError:
                raise
            except Exception as e:
                print(f"[AEAC] Connection lost: {type(e).__name__}: {e}")
            finally:
                self.ws = None

            await asyncio.sleep(delay)
            delay = min(delay * 2, MAX_RECONNECT_DELAY_S)

    async def handle(self, raw):
        try:
            message = json.loads(raw)
        except json.JSONDecodeError:
            print(f"[AEAC] Non-JSON message: {raw!r}")
            return

        event = message.get("event")

        if event == "telemetry_ack":
            self.acked += 1
        elif event == "traffic":
            self.latest_traffic = message.get("payload")
            self.latest_traffic_at = time.time()
            if self.on_traffic:
                await self.on_traffic(self.latest_traffic)
        elif event == "infraction":
            print(f"[AEAC] INFRACTION: {message}")
        elif event == "error":
            print(f"[AEAC] Server error: {message.get('message', message)}")
        else:
            print(f"[AEAC] {event}: {message}")


forwarder = None
task = None
disabled = False


def get_forwarder():
    return forwarder


def ensure_started(on_traffic=None):
    global forwarder, task, disabled

    if disabled:
        return None

    if forwarder is None:
        token = os.getenv("AEAC_CONNECTION_TOKEN", "").strip()
        if not token:
            print("[AEAC] AEAC_CONNECTION_TOKEN not set; forwarding disabled")
            disabled = True
            return None

        url = os.getenv("AEAC_WEBSOCKET_URL", DEFAULT_URL)
        forwarder = AeacForwarder(url, token, on_traffic)

    if task is None or task.done():
        task = asyncio.get_running_loop().create_task(forwarder.run())

    return forwarder
