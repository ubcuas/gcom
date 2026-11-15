import time

import socketio

from server.logging_config import logger
from server.operations.get_info import get_status
from server.operations.aeac_telemetry import build_telemetry
from server.services.status_cache import StatusCache

DELAY = 1
# DELAY = 2
RECONNECT = 15

AEAC_PERIOD = 0.6
STATUS_PERIOD = 1.0


class Status_Client:
    def __init__(self, status_cache: StatusCache):
        self.status_cache = status_cache
        self._url = ""
        self.sio = None
        self._running = True

    def handle_error(self, data):
        logger.error(f"Error sending status data: {data}")

    def stop(self):
        self._running = False
        if self.sio:
            self.sio.disconnect()

    def connect_to(self, production: bool, host: str, port: int):
        logger.info("Status Websocket Client starting...")
        self._url = f"ws://{host}:{port}"
        self.sio = socketio.Client()
        self.sio.on("error", self.handle_error)

        while self._running:
            try:
                self.sio.connect(self._url)
                logger.info("Connected to websocket server.")
                break
            except Exception as e:
                logger.warning(
                    f"Connection failed: {e}. Retrying in {RECONNECT} second(s)"
                )
                if not self._running:
                    return
                time.sleep(RECONNECT)

        next_tick = time.monotonic()
        next_status = next_tick

        while self._running:
            try:
                telemetry = build_telemetry(self.status_cache)
                if telemetry is not None:
                    self.sio.emit("aeac_telemetry", telemetry)

                if time.monotonic() >= next_status:
                    self.sio.emit(
                        "drone_update",
                        get_status(self.status_cache).as_reduced_status(),
                    )
                    next_status += STATUS_PERIOD

                next_tick += AEAC_PERIOD
                time.sleep(max(0.0, next_tick - time.monotonic()))

            except Exception as e:
                logger.warning(f"Emit failed: {e}. Waiting {RECONNECT} second(s)")
                if not self._running:
                    return
                time.sleep(RECONNECT)
                next_tick = next_status = time.monotonic()
