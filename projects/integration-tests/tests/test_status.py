"""Integration tests for drone status/telemetry endpoints.

These tests verify that telemetry data flows correctly through the full stack:
web-backend → mission-planner → SITL → back through the stack.
"""

import pytest
from helpers import assert_status_valid


@pytest.mark.critical
def test_get_status_via_web_backend(api_client):
    """Test that status can be retrieved through web-backend.

    This verifies the full integration:
    1. Test requests status from web-backend
    2. Web-backend forwards to mission-planner
    3. Mission-planner queries SITL via MAVLink
    4. Response flows back through the stack

    Args:
        api_client: API client fixture
    """
    # Act: Get status through web-backend API
    status = api_client.get_status()

    # Assert: Status contains required fields
    assert_status_valid(status)


def test_status_contains_telemetry_data(api_client):
    """Test that status includes all expected telemetry fields with correct types.

    Validates that core telemetry fields have the expected data types.
    Field presence is validated by assert_status_valid.

    Args:
        api_client: API client fixture
    """
    # Act
    status = api_client.get_status()

    # Assert: Status contains required fields
    assert_status_valid(status)

    # Validate data types for key fields
    assert isinstance(status["latitude"], (int, float)), "Latitude should be numeric"
    assert isinstance(status["longitude"], (int, float)), "Longitude should be numeric"
    assert isinstance(status["altitude"], (int, float)), "Altitude should be numeric"
    assert isinstance(status["heading"], (int, float)), "Heading should be numeric"
    assert isinstance(status["timestamp"], int), "Timestamp should be integer (milliseconds since epoch)"


def test_status_updates_over_time(api_client):
    """Test that status endpoint returns fresh data over time.

    This test verifies that the status endpoint is not returning cached data
    and that telemetry is being continuously updated from SITL.

    Args:
        api_client: API client fixture
    """
    import time

    # Get initial status
    status1 = api_client.get_status()

    # Wait a moment
    time.sleep(2)

    # Get status again
    status2 = api_client.get_status()

    # Assert: Both responses are valid
    assert_status_valid(status1)
    assert_status_valid(status2)

    # Assert: Timestamp should update between calls
    assert (
        status1["timestamp"] != status2["timestamp"]
    ), "Timestamp should update between calls"


@pytest.mark.slow
def test_status_matches_between_services(api_client):
    """Verify that web-backend and mission-planner return consistent status.

    This test hits both services and ensures data consistency, validating
    that web-backend is correctly proxying mission-planner data.

    Args:
        api_client: API client fixture
    """
    # Get status from both services
    web_backend_status = api_client.get_status()
    mission_planner_status = api_client.get_mission_planner_status()

    # Assert: Core telemetry fields match
    core_fields = ["latitude", "longitude", "altitude", "heading"]

    for field in core_fields:
        if field in web_backend_status and field in mission_planner_status:
            wb_value = web_backend_status[field]
            mp_value = mission_planner_status[field]

            # Allow small floating point differences
            if isinstance(wb_value, (int, float)) and isinstance(
                mp_value, (int, float)
            ):
                assert (
                    abs(wb_value - mp_value) < 0.001
                ), f"Status field {field} mismatch between services: {wb_value} != {mp_value}"
            else:
                assert (
                    wb_value == mp_value
                ), f"Status field {field} mismatch between services: {wb_value} != {mp_value}"
