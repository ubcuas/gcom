import time
import socketio

from server.common.status import Status
from server.operations.get_info import get_status

DELAY = 0.1
# DELAY = 2
RECONNECT = 15

class Status_Client:
    def __init__(self, mav_connection):
        self.mav_connection = mav_connection
        self._url = ""
        self.sio = None
        self._running = True
    
    def handle_error(self, data):
        print(f"Error sending status data: {data}")
    
    def stop(self):
        self._running = False
        if self.sio:
            self.sio.disconnect()

    def connect_to(self, production: bool, host: str, port: int):
        print("Status Websocket Client starting...")
        self._url = f"ws://{host}:{port}"
        self.sio = socketio.Client()
        self.sio.on('error', self.handle_error)

        while self._running:
            try:
                self.sio.connect(self._url)
                print("Connected to websocket server.")
                break
            except Exception as e:
                print(f"Connection failed: {e}. Retrying in {RECONNECT} second(s)")
                for _ in range(RECONNECT):
                    if not self._running:
                        return
                    time.sleep(1)

        while self._running:
            try:
                self.sio.emit('drone_update', get_status(self.mav_connection).as_reduced_status())
                for _ in range(int(DELAY * 10)):
                    if not self._running:
                        return
                    time.sleep(0.01)
            except Exception as e:
                print(f"Emit failed: {e}. Waiting {RECONNECT} second(s)")
                for _ in range(RECONNECT):
                    if not self._running:
                        return
                    time.sleep(1)
