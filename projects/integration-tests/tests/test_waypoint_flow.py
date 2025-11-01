"""Integration tests for waypoint management through the full stack.

These tests verify waypoint operations flow correctly:
web-backend → mission-planner → SITL → back through the stack.
"""

import pytest
from helpers import (
    assert_waypoint_match,
    assert_waypoints_match,
    assert_queue_empty,
    assert_queue_not_empty,
    assert_queue_upload_successful,
    wait_for_waypoint_count,
)


@pytest.mark.critical
def test_upload_single_waypoint_via_web_backend(api_client, sample_waypoint):
    """Test uploading a single waypoint through web-backend.

    This verifies the full integration:
    1. Test uploads waypoint to web-backend
    2. Web-backend forwards to mission-planner
    3. Mission-planner converts to MAVLink and sends to SITL
    4. Waypoint is stored in SITL flight plan
    5. Retrieve and verify waypoint through the same path

    Args:
        api_client: API client fixture
        sample_waypoint: Sample waypoint fixture
    """
    # Act & Assert: Upload waypoint and verify it's stored correctly
    queue = assert_queue_upload_successful(api_client, [sample_waypoint])

    # Additional verification for single waypoint
    assert len(queue) == 1, f"Expected 1 waypoint in queue, found {len(queue)}"
    assert_waypoint_match(queue[0], sample_waypoint)


@pytest.mark.critical
def test_upload_multiple_waypoints_via_web_backend(api_client, sample_waypoints):
    """Test uploading multiple waypoints through web-backend.

    Args:
        api_client: API client fixture
        sample_waypoints: List of sample waypoints fixture
    """
    # Act & Assert: Upload waypoints and verify they're stored correctly
    assert_queue_upload_successful(api_client, sample_waypoints)


def test_clear_waypoint_queue(api_client, sample_waypoints):
    """Test clearing the waypoint queue through web-backend.

    Args:
        api_client: API client fixture
        sample_waypoints: Sample waypoints fixture
    """
    # Setup: Upload some waypoints first
    assert_queue_upload_successful(api_client, sample_waypoints)

    # Act: Clear the queue
    response = api_client.clear_queue()
    assert (
        response.status_code == 200
    ), f"Failed to clear queue: {response.status_code} - {response.text}"

    # Verify: Queue is now empty
    queue = api_client.get_queue()
    assert_queue_empty(queue)


def test_overwrite_waypoint_queue(api_client, sample_waypoint, sample_waypoints):
    """Test that posting new waypoints overwrites the existing queue.

    Args:
        api_client: API client fixture
        sample_waypoint: Single waypoint fixture
        sample_waypoints: Multiple waypoints fixture
    """
    # Setup: Upload single waypoint
    queue = assert_queue_upload_successful(api_client, [sample_waypoint])
    assert len(queue) == 1

    # Act: Upload different set of waypoints (should overwrite)
    queue = assert_queue_upload_successful(api_client, sample_waypoints)

    # Verify: Queue now contains the new waypoints
    assert len(queue) == len(
        sample_waypoints
    ), "Queue should be overwritten with new waypoints"


@pytest.mark.slow
def test_waypoint_queue_persists_across_requests(api_client, sample_waypoints):
    """Test that waypoint queue persists between API calls.

    This verifies that waypoints are actually stored in SITL, not just
    cached by the intermediate services.

    Args:
        api_client: API client fixture
        sample_waypoints: Sample waypoints fixture
    """
    import time

    # Upload waypoints
    assert_queue_upload_successful(api_client, sample_waypoints)

    # Wait for waypoints to persist
    wait_for_waypoint_count(api_client, len(sample_waypoints), timeout=10)

    # Retrieve queue multiple times to verify persistence
    queue1 = api_client.get_queue()
    time.sleep(1)
    queue2 = api_client.get_queue()

    # Assert: Queue is consistent across calls
    assert_waypoints_match(queue1, sample_waypoints)
    assert_waypoints_match(queue2, sample_waypoints)


def test_empty_queue_returns_empty_list(api_client):
    """Test that getting an empty queue returns an empty list.

    Args:
        api_client: API client fixture
    """
    # Ensure queue is empty
    api_client.clear_queue()

    # Act
    queue = api_client.get_queue()

    # Assert
    assert_queue_empty(queue)


@pytest.mark.slow
def test_waypoint_consistency_between_services(api_client, sample_waypoints):
    """Verify waypoint queue is consistent between web-backend and mission-planner.

    This ensures web-backend is correctly proxying mission-planner data.

    Args:
        api_client: API client fixture
        sample_waypoints: Sample waypoints fixture
    """
    # Upload waypoints through web-backend
    assert_queue_upload_successful(api_client, sample_waypoints)

    # Get queue from both services
    web_backend_queue = api_client.get_queue()
    mission_planner_queue = api_client.get_mission_planner_queue()

    # Assert: Waypoints match between services
    assert_waypoints_match(web_backend_queue, mission_planner_queue)
