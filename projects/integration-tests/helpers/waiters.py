"""Polling and waiting utilities for async drone operations.

Drone operations like takeoff, landing, and waypoint navigation are asynchronous.
These utilities help tests wait for conditions to be met with proper timeouts.
"""

import time
from collections.abc import Callable
from typing import Any

from .api_client import APIClient


def wait_for_condition(
    condition_fn: Callable[[], bool],
    timeout: float = 60.0,
    poll_interval: float = 1.0,
    error_message: str = "Condition not met within timeout",
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
    tolerance: float = 5.0,
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
            print(f"Current Altitude: {current_altitude}, Target: {target_altitude}m")
            return abs(current_altitude - target_altitude) <= tolerance
        except:
            return False

    wait_for_condition(
        check_altitude,
        timeout=timeout,
        poll_interval=1.0,
        error_message=f"Drone did not reach altitude {target_altitude}m (±{tolerance}m)",
    )


def wait_for_waypoint_count(
    api_client: APIClient, expected_count: int, timeout: float = 30.0
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
        error_message=f"Waypoint queue does not contain {expected_count} waypoints",
    )


def wait_for_drone_armed(
    api_client: APIClient, armed: bool = True, timeout: float = 30.0
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
            is_armed = status.get("armed", False)
            return is_armed == armed
        except:
            return False

    state_str = "armed" if armed else "disarmed"
    wait_for_condition(
        check_armed,
        timeout=timeout,
        poll_interval=1.0,
        error_message=f"Drone did not become {state_str}",
    )


def wait_for_status_field(
    api_client: APIClient,
    field_name: str,
    expected_value: Any,
    timeout: float = 30.0,
    tolerance: float | None = None,
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
        error_message=f"Status field '{field_name}' did not reach value {expected_value}",
    )


def wait_for_flight_mode(
    api_client: APIClient, mode: str, timeout: float = 30.0
) -> None:
    """Wait for drone to enter specified flight mode.

    Args:
        api_client: API client instance
        mode: Expected flight mode (e.g., "GUIDED", "AUTO", "LOITER")
        timeout: Maximum time to wait in seconds

    Raises:
        TimeoutError: If mode not reached within timeout
    """

    def check_mode() -> bool:
        try:
            current_mode = api_client.get_flight_mode()
            print(f"Current flight mode: {current_mode}, Target: {mode}")
            return current_mode == mode
        except:
            return False

    wait_for_condition(
        check_mode,
        timeout=timeout,
        poll_interval=1.0,
        error_message=f"Drone did not enter {mode} mode",
    )


def wait_for_position(
    api_client: APIClient,
    target_lat: float,
    target_lon: float,
    timeout: float = 60.0,
    tolerance_meters: float = 10.0,
) -> None:
    """Wait for drone to reach target position.

    Args:
        api_client: API client instance
        target_lat: Target latitude
        target_lon: Target longitude
        timeout: Maximum time to wait in seconds
        tolerance_meters: Acceptable distance from target in meters

    Raises:
        TimeoutError: If position not reached within timeout
    """

    def check_position() -> bool:
        try:
            status = api_client.get_status()
            current_lat = status.get("latitude")
            current_lon = status.get("longitude")

            if current_lat is None or current_lon is None:
                return False

            # Rough conversion: 1 degree lat/lon ≈ 111km at equator
            lat_diff_m = abs(current_lat - target_lat) * 111000
            lon_diff_m = abs(current_lon - target_lon) * 111000
            distance = (lat_diff_m**2 + lon_diff_m**2) ** 0.5

            print(
                f"Current position: ({current_lat:.6f}, {current_lon:.6f}), "
                f"Target: ({target_lat:.6f}, {target_lon:.6f}), "
                f"Distance: {distance:.1f}m"
            )

            return distance <= tolerance_meters
        except:
            return False

    wait_for_condition(
        check_position,
        timeout=timeout,
        poll_interval=2.0,
        error_message=f"Drone did not reach position ({target_lat}, {target_lon}) within {tolerance_meters}m",
    )


def wait_for_stationary(
    api_client: APIClient,
    duration: float = 10.0,
    speed_threshold: float = 0.5,
    vertical_speed_threshold: float = 0.5,
    timeout: float = 60.0,
) -> None:
    """Wait for drone to be stationary (hovering).

    Verifies drone maintains low speed for specified duration.

    Args:
        api_client: API client instance
        duration: How long drone must remain stationary in seconds
        speed_threshold: Maximum groundspeed in m/s to be considered stationary
        vertical_speed_threshold: Maximum vertical speed in m/s
        timeout: Maximum time to wait in seconds

    Raises:
        TimeoutError: If drone doesn't become stationary within timeout
    """
    stationary_start = None

    def check_stationary() -> bool:
        nonlocal stationary_start
        try:
            status = api_client.get_status()
            groundspeed = status.get("groundspeed", float("inf"))
            verticalspeed = abs(status.get("verticalspeed", float("inf")))

            is_stationary = (
                groundspeed < speed_threshold
                and verticalspeed < vertical_speed_threshold
            )

            if is_stationary:
                if stationary_start is None:
                    stationary_start = time.time()
                    print(f"Drone stationary, monitoring for {duration}s...")

                elapsed = time.time() - stationary_start
                print(
                    f"Stationary for {elapsed:.1f}s (groundspeed: {groundspeed:.2f} m/s, "
                    f"verticalspeed: {verticalspeed:.2f} m/s)"
                )

                if elapsed >= duration:
                    return True
            else:
                if stationary_start is not None:
                    print(
                        f"Drone moving (groundspeed: {groundspeed:.2f} m/s, "
                        f"verticalspeed: {verticalspeed:.2f} m/s), resetting timer..."
                    )
                stationary_start = None

            return False
        except:
            stationary_start = None
            return False

    wait_for_condition(
        check_stationary,
        timeout=timeout,
        poll_interval=1.0,
        error_message=f"Drone did not remain stationary for {duration}s",
    )
