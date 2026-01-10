import queue
import threading
import time
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional

from pymavlink import mavutil

from server.logging_config import logger
from server.services.status_cache import StatusCache


class MavlinkHandler:
    """
    Global MAVLink message handler thread.

    This service runs a single background thread that continuously receives MAVLink
    messages and distributes them to:
    1. Status cache for status messages
    2. Registered listeners for command/response messages

    It also provides convenient access to the MAVLink connection for sending messages.

    This eliminates blocking recv_match calls and prevents message interference
    between different parts of the codebase.
    """

    def __init__(self, mav_connection: mavutil.mavfile, status_cache: StatusCache):
        self.mav_connection = mav_connection
        self.status_cache = status_cache

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._shutdown_flag = threading.Event()

        # Listener registry: msg_type -> list of queues
        self._listeners: Dict[str, List[queue.Queue]] = defaultdict(list)
        self._listeners_lock = threading.Lock()

    # Convenience properties for cleaner access to MAVLink connection
    @property
    def connection(self) -> mavutil.mavfile:
        """Get the underlying MAVLink connection."""
        return self.mav_connection

    @property
    def mav(self):
        """Get the MAVLink protocol handler for sending messages."""
        return self.mav_connection.mav

    @property
    def target_system(self) -> int:
        """Get the target system ID."""
        return self.mav_connection.target_system

    @property
    def target_component(self) -> int:
        """Get the target component ID."""
        return self.mav_connection.target_component

    @property
    def mode_mapping(self):
        """Get the flight mode mapping."""
        return self.mav_connection.mode_mapping

    def start(self) -> None:
        """Start the handler thread."""
        if self._running:
            logger.warning("MavlinkHandler already running")
            return

        self._running = True
        self._shutdown_flag.clear()
        self._thread = threading.Thread(target=self._receiver_loop, daemon=True)
        self._thread.start()
        logger.info("MavlinkHandler started")

    def stop(self) -> None:
        """Stop the handler thread gracefully."""
        if not self._running:
            return

        logger.info("Stopping MavlinkHandler...")
        self._running = False
        self._shutdown_flag.set()

        if self._thread:
            self._thread.join(timeout=5.0)
            if self._thread.is_alive():
                logger.warning("MavlinkHandler thread did not stop cleanly")
            else:
                logger.info("MavlinkHandler stopped")

        self._thread = None

    def _receiver_loop(self) -> None:
        """
        Main receiver loop that runs in background thread.

        Continuously receives messages and routes them to status cache
        and/or registered listeners.
        """
        logger.info("MavlinkHandler loop starting")
        error_count = 0
        max_consecutive_errors = 10

        while self._running and not self._shutdown_flag.is_set():
            try:
                # Receive next message with a timeout to allow checking shutdown flag
                msg = self.mav_connection.recv_match(blocking=True, timeout=1.0)

                if msg is None:
                    # Timeout, continue to check shutdown flag
                    continue

                msg_type = msg.get_type()

                if msg_type == "BAD_DATA":
                    continue

                # Reset error count on successful receive
                error_count = 0

                # Log STATUSTEXT messages
                if msg_type == "STATUSTEXT":
                    logger.info(f"STATUSTEXT: {msg.text}")

                # Route to status cache if it's a status message
                if msg_type in StatusCache.STATUS_MESSAGE_TYPES:
                    self.status_cache.update(msg_type, msg)

                # Route to registered listeners
                self._notify_listeners(msg_type, msg)

            except Exception as e:
                error_count += 1
                logger.error(f"Error in handler loop: {e}", exc_info=True)

                if error_count >= max_consecutive_errors:
                    logger.critical(
                        f"Too many consecutive errors ({error_count}), stopping handler"
                    )
                    self._running = False
                    break

                # Exponential backoff on errors
                backoff = min(2**error_count, 5)
                time.sleep(backoff)

        logger.info("MavlinkHandler loop exiting")

    def _notify_listeners(self, msg_type: str, message: Any) -> None:
        """
        Notify all registered listeners for a given message type.

        Args:
            msg_type: The message type
            message: The message object
        """
        with self._listeners_lock:
            if msg_type not in self._listeners:
                return

            # Send to all listeners, removing any that are full
            listeners_to_remove = []
            for listener_queue in self._listeners[msg_type]:
                try:
                    # Use put_nowait to avoid blocking the receiver thread
                    listener_queue.put_nowait(message)
                except queue.Full:
                    # Queue is full, this listener may be dead
                    listeners_to_remove.append(listener_queue)

            # Clean up full queues
            for dead_queue in listeners_to_remove:
                self._listeners[msg_type].remove(dead_queue)

    def wait_for_message(
        self,
        msg_type: str,
        timeout: Optional[float] = None,
        filter_func: Optional[Callable[[Any], bool]] = None,
    ) -> Optional[Any]:
        """
        Wait for a specific message type with optional filtering.

        Args:
            msg_type: The MAVLink message type to wait for
            timeout: Maximum time to wait in seconds (None = wait forever)
            filter_func: Optional function to filter messages. Should return True
                        to accept the message, False to continue waiting.

        Returns:
            The received message or None if timeout occurred
        """
        # Create a queue for this listener
        listener_queue = queue.Queue(maxsize=50)

        # Register the listener
        with self._listeners_lock:
            self._listeners[msg_type].append(listener_queue)

        try:
            end_time = time.time() + timeout if timeout is not None else None

            while True:
                # Calculate remaining timeout
                if end_time is not None:
                    remaining = end_time - time.time()
                    if remaining <= 0:
                        return None
                else:
                    remaining = None

                try:
                    # Wait for a message with timeout
                    message = listener_queue.get(timeout=remaining)

                    # Apply filter if provided
                    if filter_func is None or filter_func(message):
                        return message

                    # Filter rejected the message, keep waiting

                except queue.Empty:
                    # Timeout occurred
                    return None

        finally:
            # Always unregister the listener
            with self._listeners_lock:
                if msg_type in self._listeners:
                    try:
                        self._listeners[msg_type].remove(listener_queue)
                    except ValueError:
                        # Already removed (e.g., due to full queue cleanup)
                        pass

    def wait_for_any_message(
        self,
        msg_types: List[str],
        timeout: Optional[float] = None,
        filter_func: Optional[Callable[[Any], bool]] = None,
    ) -> Optional[Any]:
        """
        Wait for any of the specified message types.

        Args:
            msg_types: List of MAVLink message types to wait for
            timeout: Maximum time to wait in seconds (None = wait forever)
            filter_func: Optional function to filter messages

        Returns:
            The first matching message or None if timeout occurred
        """
        # Create a single shared queue for all message types
        listener_queue = queue.Queue(maxsize=50)

        # Register listener for all message types
        with self._listeners_lock:
            for msg_type in msg_types:
                self._listeners[msg_type].append(listener_queue)

        try:
            end_time = time.time() + timeout if timeout is not None else None

            while True:
                # Calculate remaining timeout
                if end_time is not None:
                    remaining = end_time - time.time()
                    if remaining <= 0:
                        return None
                else:
                    remaining = None

                try:
                    # Wait for a message
                    message = listener_queue.get(timeout=remaining)

                    # Apply filter if provided
                    if filter_func is None or filter_func(message):
                        return message

                except queue.Empty:
                    return None

        finally:
            # Unregister from all message types
            with self._listeners_lock:
                for msg_type in msg_types:
                    if msg_type in self._listeners:
                        try:
                            self._listeners[msg_type].remove(listener_queue)
                        except ValueError:
                            pass

    def subscribe(self, msg_type: str, callback: Callable[[Any], None]) -> None:
        """
        Subscribe to a message type with a callback.

        Note: This is for permanent subscriptions. For temporary waits,
        use wait_for_message() instead.

        Args:
            msg_type: The MAVLink message type
            callback: Function to call with each received message
        """
        # For now, this could be implemented with a background thread per callback
        # that calls wait_for_message in a loop. We can add this in the future if needed.
        raise NotImplementedError(
            "subscribe() not yet implemented - use wait_for_message()"
        )

    def is_running(self) -> bool:
        """Check if the handler thread is running."""
        return self._running
