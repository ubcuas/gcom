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
    # print(f"Comparing {json.dumps(actual_list, indent=2)} actual waypoints to {json.dumps(expected_list, indent=2)} expected waypoints")
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


def filter_home_waypoint(queue: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter out the home waypoint from a queue.

    The home waypoint is identified by having id == 0 and "home" in the name.

    Args:
        queue: Waypoint queue from API

    Returns:
        Queue with home waypoint removed
    """
    return [
        wp for wp in queue
        if not (wp.get("id") == 0 and "home" in wp.get("name", "").lower())
    ]


def assert_queue_empty(queue: List[Dict[str, Any]]) -> None:
    """Assert that waypoint queue is empty (excluding home waypoint).

    Args:
        queue: Waypoint queue from API

    Raises:
        AssertionError: If queue is not empty
    """
    filtered = filter_home_waypoint(queue)
    assert len(filtered) == 0, f"Expected empty queue but found {len(filtered)} waypoints"


def assert_queue_not_empty(queue: List[Dict[str, Any]]) -> None:
    """Assert that waypoint queue is not empty (excluding home waypoint).

    Args:
        queue: Waypoint queue from API

    Raises:
        AssertionError: If queue is empty
    """
    filtered = filter_home_waypoint(queue)
    assert len(filtered) > 0, "Expected non-empty queue but found 0 waypoints"


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
    3. Retrieving and validating the queue contents (excluding home waypoint)

    Args:
        api_client: API client instance
        waypoints: List of waypoints to upload
        check_response: Whether to assert response status code is 200

    Returns:
        The queue retrieved after upload (with home waypoint filtered out)

    Raises:
        AssertionError: If upload fails or waypoints don't match
    """
    response = api_client.post_queue(waypoints)

    if check_response:
        assert (
            response.status_code == 200
        ), f"Failed to upload waypoints: {response.status_code} - {response.text}"

    queue = api_client.get_queue()
    filtered_queue = filter_home_waypoint(queue)
    assert_waypoints_match(filtered_queue, waypoints)
    return filtered_queue


def assert_waypoint_db_match(
    actual: Dict[str, Any],
    expected: Dict[str, Any],
    ignore_id: bool = True,
) -> None:
    """Assert that database waypoint matches expected values.

    Compares waypoints from database API responses. Handles UUID fields
    and database-specific fields like order, route, radius, etc.

    Args:
        actual: Actual waypoint from database API
        expected: Expected waypoint values
        ignore_id: If True, skip comparing the 'id' field (useful for new waypoints)

    Raises:
        AssertionError: If waypoints don't match
    """
    check_fields = ["name", "latitude", "longitude", "altitude"]

    # Add database-specific fields if present in expected
    if "order" in expected:
        check_fields.append("order")
    if "route" in expected:
        check_fields.append("route")
    if "radius" in expected:
        check_fields.append("radius")
    if "pass_radius" in expected:
        check_fields.append("pass_radius")
    if "pass_option" in expected:
        check_fields.append("pass_option")

    for field in check_fields:
        if field in expected:
            assert field in actual, f"Waypoint missing field: {field}"
            actual_value = actual[field]
            expected_value = expected[field]

            # For floating point fields, allow small tolerance
            if field in ["latitude", "longitude", "altitude", "radius", "pass_radius"]:
                tolerance = 0.0001
                assert (
                    abs(actual_value - expected_value) < tolerance
                ), f"Waypoint {field} mismatch: {actual_value} != {expected_value}"
            else:
                assert (
                    actual_value == expected_value
                ), f"Waypoint {field} mismatch: {actual_value} != {expected_value}"

    # Check ID exists if not ignoring it
    if not ignore_id:
        assert "id" in actual, "Waypoint missing 'id' field"


def assert_route_contains_waypoints(
    route: Dict[str, Any],
    expected_count: int,
) -> None:
    """Assert that route contains expected number of waypoints.

    Args:
        route: Route dictionary from API (should include 'waypoints' field)
        expected_count: Expected number of waypoints in the route

    Raises:
        AssertionError: If waypoint count doesn't match
    """
    assert "waypoints" in route, "Route missing 'waypoints' field"
    waypoints = route["waypoints"]
    actual_count = len(waypoints)

    assert (
        actual_count == expected_count
    ), f"Route waypoint count mismatch: {actual_count} != {expected_count}"


def assert_waypoints_ordered(waypoints: List[Dict[str, Any]]) -> None:
    """Assert that waypoints are in correct order (0, 1, 2, ...).

    Verifies that the 'order' field in each waypoint is sequential starting from 0.

    Args:
        waypoints: List of waypoint dictionaries with 'order' field

    Raises:
        AssertionError: If waypoints are not in correct order
    """
    for i, waypoint in enumerate(waypoints):
        assert "order" in waypoint, f"Waypoint {i} missing 'order' field"
        actual_order = waypoint["order"]
        assert (
            actual_order == i
        ), f"Waypoint order mismatch at index {i}: {actual_order} != {i}"
