"""Custom assertion helpers for drone-specific validations.

These functions provide clear, reusable validation logic for common
test assertions related to waypoints, status, and drone state.
"""

from typing import Dict, Any, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .api_client import APIClient


def assert_status_valid(status: Dict[str, Any]) -> None:
    """Assert that status dictionary contains required fields with valid values.

    Validates core telemetry fields that must be present in status responses.
    Required fields validated:
    - timestamp: Status timestamp
    - current_wpn: Current waypoint number
    - latitude, longitude, altitude: Position data
    - heading, groundspeed: Navigation data
    - batteryvoltage: Power status

    Args:
        status: Status dictionary from API

    Raises:
        AssertionError: If status is invalid
    """
    required_fields = [
        "timestamp",
        "current_wpn",
        "latitude",
        "longitude",
        "altitude",
        "heading",
        "groundspeed",
        "batteryvoltage",
    ]

    for field in required_fields:
        assert field in status, f"Status missing required field: {field}"
        value = status[field]
        assert value is not None, f"Status field {field} is None"

    # Validate numeric ranges
    assert -90 <= status["latitude"] <= 90, f"Invalid latitude: {status['latitude']}"
    assert (
        -180 <= status["longitude"] <= 180
    ), f"Invalid longitude: {status['longitude']}"
    assert 0 <= status["heading"] <= 360, f"Invalid heading: {status['heading']}"


def assert_waypoint_match(
    actual: Dict[str, Any],
    expected: Dict[str, Any],
    check_fields: Optional[List[str]] = None,
) -> None:
    """Assert that actual waypoint matches expected waypoint.

    Args:
        actual: Actual waypoint from API
        expected: Expected waypoint values
        check_fields: List of fields to check (default: name, lat, lon, alt)

    Raises:
        AssertionError: If waypoints don't match
    """
    if check_fields is None:
        check_fields = ["name", "latitude", "longitude", "altitude"]

    for field in check_fields:
        if field in expected:
            assert field in actual, f"Waypoint missing field: {field}"
            actual_value = actual[field]
            expected_value = expected[field]

            # For floating point coordinates, allow small tolerance
            if field in ["latitude", "longitude", "altitude"] and isinstance(
                expected_value, (int, float)
            ):
                tolerance = 0.0001  # ~11 meters for lat/lon
                assert (
                    abs(actual_value - expected_value) < tolerance
                ), f"Waypoint {field} mismatch: {actual_value} != {expected_value}"
            else:
                assert (
                    actual_value == expected_value
                ), f"Waypoint {field} mismatch: {actual_value} != {expected_value}"


def assert_waypoints_match(
    actual_list: List[Dict[str, Any]],
    expected_list: List[Dict[str, Any]],
    check_fields: Optional[List[str]] = None,
) -> None:
    """Assert that list of waypoints matches expected list.

    Args:
        actual_list: List of actual waypoints
        expected_list: List of expected waypoints
        check_fields: List of fields to check in each waypoint

    Raises:
        AssertionError: If lists don't match
    """
    assert len(actual_list) == len(
        expected_list
    ), f"Waypoint count mismatch: {len(actual_list)} != {len(expected_list)}"

    for i, (actual, expected) in enumerate(zip(actual_list, expected_list)):
        try:
            assert_waypoint_match(actual, expected, check_fields)
        except AssertionError as e:
            raise AssertionError(f"Waypoint {i} mismatch: {e}") from e


def assert_position_near(
    pos1: Dict[str, Any], pos2: Dict[str, Any], tolerance_meters: float = 10.0
) -> None:
    """Assert that two positions are within tolerance of each other.

    Uses simple Euclidean approximation (acceptable for small distances).

    Args:
        pos1: First position with lat/lon fields
        pos2: Second position with lat/lon fields
        tolerance_meters: Maximum distance in meters

    Raises:
        AssertionError: If positions are too far apart
    """
    lat1, lon1 = pos1["latitude"], pos1["longitude"]
    lat2, lon2 = pos2["latitude"], pos2["longitude"]

    # Rough conversion: 1 degree lat/lon ≈ 111km at equator
    lat_diff_m = abs(lat1 - lat2) * 111000
    lon_diff_m = abs(lon1 - lon2) * 111000

    distance = (lat_diff_m**2 + lon_diff_m**2) ** 0.5

    assert (
        distance <= tolerance_meters
    ), f"Positions too far apart: {distance:.2f}m > {tolerance_meters}m"


def assert_altitude_near(
    actual_altitude: float, expected_altitude: float, tolerance: float = 5.0
) -> None:
    """Assert that actual altitude is within tolerance of expected.

    Args:
        actual_altitude: Actual altitude in meters
        expected_altitude: Expected altitude in meters
        tolerance: Acceptable difference in meters

    Raises:
        AssertionError: If altitude difference exceeds tolerance
    """
    diff = abs(actual_altitude - expected_altitude)
    assert (
        diff <= tolerance
    ), f"Altitude mismatch: {actual_altitude}m != {expected_altitude}m (±{tolerance}m)"


def assert_queue_empty(queue: List[Dict[str, Any]]) -> None:
    """Assert that waypoint queue is empty.

    Args:
        queue: Waypoint queue from API

    Raises:
        AssertionError: If queue is not empty
    """
    assert len(queue) == 0, f"Expected empty queue but found {len(queue)} waypoints"


def assert_queue_not_empty(queue: List[Dict[str, Any]]) -> None:
    """Assert that waypoint queue is not empty.

    Args:
        queue: Waypoint queue from API

    Raises:
        AssertionError: If queue is empty
    """
    assert len(queue) > 0, "Expected non-empty queue but found 0 waypoints"


def assert_field_values_match(
    actual: Dict[str, Any],
    expected: Dict[str, Any],
    fields: List[str],
    tolerance: float = 0.001,
) -> None:
    """Assert that specified fields match between two dictionaries.

    For numeric fields, uses tolerance-based comparison.
    For other types, uses exact equality.

    Args:
        actual: Actual dictionary from API
        expected: Expected dictionary values
        fields: List of field names to compare
        tolerance: Tolerance for floating point comparison

    Raises:
        AssertionError: If any field values don't match
    """
    for field in fields:
        if field in expected and field in actual:
            actual_value = actual[field]
            expected_value = expected[field]

            if isinstance(actual_value, (int, float)) and isinstance(
                expected_value, (int, float)
            ):
                assert (
                    abs(actual_value - expected_value) < tolerance
                ), f"Field {field} mismatch: {actual_value} != {expected_value} (tolerance: {tolerance})"
            else:
                assert (
                    actual_value == expected_value
                ), f"Field {field} mismatch: {actual_value} != {expected_value}"


def assert_queue_upload_successful(
    api_client: "APIClient",
    waypoints: List[Dict[str, Any]],
    check_response: bool = True,
) -> List[Dict[str, Any]]:
    """Upload waypoints and verify they are correctly stored.

    This helper consolidates the common pattern of:
    1. Uploading waypoints to the queue
    2. Checking response status
    3. Retrieving and validating the queue contents

    Args:
        api_client: API client instance
        waypoints: List of waypoints to upload
        check_response: Whether to assert response status code is 200

    Returns:
        The queue retrieved after upload

    Raises:
        AssertionError: If upload fails or waypoints don't match
    """
    response = api_client.post_queue(waypoints)

    if check_response:
        assert (
            response.status_code == 200
        ), f"Failed to upload waypoints: {response.status_code} - {response.text}"

    queue = api_client.get_queue()
    assert_waypoints_match(queue, waypoints)
    return queue
