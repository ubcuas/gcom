"""Polling and waiting utilities for async drone operations.

Drone operations like takeoff, landing, and waypoint navigation are asynchronous.
These utilities help tests wait for conditions to be met with proper timeouts.
"""

import time
from typing import Callable, Any, Optional
from .api_client import APIClient


def wait_for_condition(
    condition_fn: Callable[[], bool],
    timeout: float = 60.0,
    poll_interval: float = 1.0,
    error_message: str = "Condition not met within timeout"
) -> None:
    """Generic wait function that polls until condition is met.

    Args:
        condition_fn: Function that returns True when condition is met
        timeout: Maximum time to wait in seconds
        poll_interval: Time between checks in seconds
        error_message: Error message if timeout occurs

    Raises:
        TimeoutError: If condition not met within timeout
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        if condition_fn():
            return
        time.sleep(poll_interval)

    raise TimeoutError(f"{error_message} (waited {timeout}s)")


def wait_for_altitude(
    api_client: APIClient,
    target_altitude: float,
    timeout: float = 60.0,
    tolerance: float = 5.0
) -> None:
    """Wait for drone to reach target altitude.

    Args:
        api_client: API client instance
        target_altitude: Target altitude in meters
        timeout: Maximum time to wait in seconds
        tolerance: Acceptable altitude difference in meters

    Raises:
        TimeoutError: If altitude not reached within timeout
    """
    def check_altitude() -> bool:
        try:
            status = api_client.get_status()
            current_altitude = status.get("altitude", 0)
            return abs(current_altitude - target_altitude) <= tolerance
        except:
            return False

    wait_for_condition(
        check_altitude,
        timeout=timeout,
        poll_interval=1.0,
        error_message=f"Drone did not reach altitude {target_altitude}m (±{tolerance}m)"
    )


def wait_for_waypoint_count(
    api_client: APIClient,
    expected_count: int,
    timeout: float = 30.0
) -> None:
    """Wait for waypoint queue to have expected number of waypoints.

    Args:
        api_client: API client instance
        expected_count: Expected number of waypoints
        timeout: Maximum time to wait in seconds

    Raises:
        TimeoutError: If count not reached within timeout
    """
    def check_count() -> bool:
        try:
            queue = api_client.get_queue()
            return len(queue) == expected_count
        except:
            return False

    wait_for_condition(
        check_count,
        timeout=timeout,
        poll_interval=0.5,
        error_message=f"Waypoint queue does not contain {expected_count} waypoints"
    )


def wait_for_drone_armed(
    api_client: APIClient,
    armed: bool = True,
    timeout: float = 30.0
) -> None:
    """Wait for drone to be armed or disarmed.

    Args:
        api_client: API client instance
        armed: True to wait for armed, False for disarmed
        timeout: Maximum time to wait in seconds

    Raises:
        TimeoutError: If state not reached within timeout
    """
    def check_armed() -> bool:
        try:
            status = api_client.get_status()
            # Check if status has armed field - may vary by implementation
            is_armed = status.get("armed", False)
            return is_armed == armed
        except:
            return False

    state_str = "armed" if armed else "disarmed"
    wait_for_condition(
        check_armed,
        timeout=timeout,
        poll_interval=1.0,
        error_message=f"Drone did not become {state_str}"
    )


def wait_for_status_field(
    api_client: APIClient,
    field_name: str,
    expected_value: Any,
    timeout: float = 30.0,
    tolerance: Optional[float] = None
) -> None:
    """Wait for a specific status field to reach expected value.

    Args:
        api_client: API client instance
        field_name: Name of the status field to check
        expected_value: Expected value for the field
        timeout: Maximum time to wait in seconds
        tolerance: For numeric values, acceptable difference

    Raises:
        TimeoutError: If value not reached within timeout
    """
    def check_field() -> bool:
        try:
            status = api_client.get_status()
            current_value = status.get(field_name)

            if current_value is None:
                return False

            if tolerance is not None and isinstance(current_value, (int, float)):
                return abs(current_value - expected_value) <= tolerance

            return current_value == expected_value
        except:
            return False

    wait_for_condition(
        check_field,
        timeout=timeout,
        poll_interval=1.0,
        error_message=f"Status field '{field_name}' did not reach value {expected_value}"
    )
