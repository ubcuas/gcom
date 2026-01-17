import threading
import time
from typing import Any, Dict, Optional, Tuple


class StatusCache:
    """
    Thread-safe cache for MAVLink status messages.

    Stores the latest received status messages along with their receipt timestamps.
    This allows get_status() to return near-instantaneous results without blocking
    on network I/O.
    """

    STATUS_MESSAGE_TYPES = [
        "SYSTEM_TIME",
        "GLOBAL_POSITION_INT",
        "ATTITUDE",
        "VFR_HUD",
        "SYS_STATUS",
        "MISSION_CURRENT",
        "WIND_COV",
        "HEARTBEAT",
    ]

    def __init__(self):
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._lock = threading.Lock()
        self._mode_mapping: Optional[Dict[str, int]] = None

    def update(self, msg_type: str, message: Any) -> None:
        """
        Update the cache with a new message.

        Args:
            msg_type: The MAVLink message type (e.g., 'SYSTEM_TIME')
            message: The MAVLink message object
        """
        timestamp = time.time()
        with self._lock:
            self._cache[msg_type] = (message, timestamp)

    def get(self, msg_type: str) -> Optional[Tuple[Any, float]]:
        """
        Get a cached message and its age.

        Args:
            msg_type: The MAVLink message type to retrieve

        Returns:
            Tuple of (message, age_in_seconds) or None if not cached
        """
        with self._lock:
            if msg_type not in self._cache:
                return None

            message, timestamp = self._cache[msg_type]
            age = time.time() - timestamp
            return (message, age)

    def get_message(self, msg_type: str) -> Optional[Any]:
        """
        Get just the cached message object.

        Args:
            msg_type: The MAVLink message type to retrieve

        Returns:
            The message object or None if not cached
        """
        result = self.get(msg_type)
        return result[0] if result else None

    def get_age(self, msg_type: str) -> Optional[float]:
        """
        Get the age of a cached message in seconds.

        Args:
            msg_type: The MAVLink message type

        Returns:
            Age in seconds or None if not cached
        """
        result = self.get(msg_type)
        return result[1] if result else None

    def get_all(self) -> Dict[str, Tuple[Any, float]]:
        """
        Get all cached messages with their ages.

        Returns:
            Dictionary mapping message types to (message, age) tuples
        """
        with self._lock:
            current_time = time.time()
            return {
                msg_type: (msg, current_time - timestamp)
                for msg_type, (msg, timestamp) in self._cache.items()
            }

    def has(self, msg_type: str) -> bool:
        """
        Check if a message type is cached.

        Args:
            msg_type: The MAVLink message type

        Returns:
            True if the message type is in the cache
        """
        with self._lock:
            return msg_type in self._cache

    def clear(self) -> None:
        """Clear all cached messages."""
        with self._lock:
            self._cache.clear()

    def set_mode_mapping(self, mode_mapping: Dict[str, int]) -> None:
        """
        Set the mode mapping for flight mode lookups.

        Args:
            mode_mapping: Dictionary mapping mode names to mode IDs
        """
        with self._lock:
            self._mode_mapping = mode_mapping

    def get_flight_mode(self) -> Optional[str]:
        """
        Get the current flight mode from the cached HEARTBEAT message.

        Returns:
            Flight mode name (e.g., 'GUIDED', 'RTL') or None if not available
        """
        heartbeat_msg = self.get_message("HEARTBEAT")
        if not heartbeat_msg or not self._mode_mapping:
            return None

        custom_mode = heartbeat_msg.custom_mode

        # Reverse lookup: find mode name from mode ID
        for mode_name, mode_id in self._mode_mapping.items():
            if mode_id == custom_mode:
                return mode_name

        return None
