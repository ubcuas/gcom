import sys
import signal
from threading import Thread, Event

from server.utilities.connect_to_sysid import connect_to_sysid
from server.httpserver import HTTP_Server
from server.status_wsclient import Status_Client

stop_event = Event()

def run_http_server(mav_connection, production, host, port):
    http_server = HTTP_Server(mav_connection)
    http_server.serve_forever(production, host, port)

def run_status_client(mav_connection, production, host, port):
    ws_client = Status_Client(mav_connection)
    while not stop_event.is_set():
        ws_client.connect_to(production, host, port)
    
    # for some reason, only after hitting keyboard interrupt ctrl-c THREE times to interupt sio
    # not a clean disconnect, not calling this code for some reason
    ws_client.stop()

# def signal_handler(sig, frame):
#     print("Caught Ctrl+C, shutting down...")
#     stop_event.set()

if __name__ == "__main__":
    # Simplified argument parsing here, replace with your own
    production = True
    HOST, PORT = "localhost", 9000
    STATUS_HOST, STATUS_PORT = "localhost", 8000
    DISABLE_STATUS = False
    MAVLINK_CONNECTION_STRING = 'udpin:localhost:14551'

    mav_connection = connect_to_sysid(MAVLINK_CONNECTION_STRING, 1)
    if mav_connection is None:
        print("MAV connection failed")
        sys.exit(1)
    print("MAV connection successful")

    # Setup Ctrl+C handler
    # signal.signal(signal.SIGINT, signal_handler)

    # Start HTTP server thread
    http_thread = Thread(target=run_http_server, args=(mav_connection, production, HOST, PORT))
    http_thread.start()

    # Start status websocket client thread if enabled
    status_thread = None
    if not DISABLE_STATUS:
        status_thread = Thread(target=run_status_client, args=(mav_connection, production, STATUS_HOST, STATUS_PORT))
        status_thread.start()

    try:
        # Wait for stop event
        while not stop_event.is_set():
            stop_event.wait(1)
    except KeyboardInterrupt:
        stop_event.set()

    print("Shutting down threads...")

    # Flask's server doesn't provide a clean stop API,
    # but exiting main thread will kill the app.
    # You might want to set socketio.stop() inside HTTP_Server to support this.

    http_thread.join(timeout=3)
    if status_thread:
        status_thread.join(timeout=3)

    print("Exited cleanly.")
