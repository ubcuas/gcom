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
    # Act: Upload waypoint through web-backend
    response = api_client.post_queue([sample_waypoint])

    # Assert: Request succeeded
    assert (
        response.status_code == 200
    ), f"Failed to upload waypoint: {response.status_code} - {response.text}"

    # Verify: Retrieve queue and check waypoint is there
    queue = api_client.get_queue()

    assert len(queue) == 1, f"Expected 1 waypoint in queue, found {len(queue)}"
    assert_waypoint_match(queue[0], sample_waypoint)


@pytest.mark.critical
def test_upload_multiple_waypoints_via_web_backend(api_client, sample_waypoints):
    """Test uploading multiple waypoints through web-backend.

    Args:
        api_client: API client fixture
        sample_waypoints: List of sample waypoints fixture
    """
    # Act: Upload waypoints through web-backend
    response = api_client.post_queue(sample_waypoints)

    # Assert: Request succeeded
    assert (
        response.status_code == 200
    ), f"Failed to upload waypoints: {response.status_code} - {response.text}"

    # Verify: Retrieve queue and check all waypoints
    queue = api_client.get_queue()

    assert len(queue) == len(
        sample_waypoints
    ), f"Expected {len(sample_waypoints)} waypoints, found {len(queue)}"

    # Verify each waypoint matches
    assert_waypoints_match(queue, sample_waypoints)


def test_clear_waypoint_queue(api_client, sample_waypoints):
    """Test clearing the waypoint queue through web-backend.

    Args:
        api_client: API client fixture
        sample_waypoints: Sample waypoints fixture
    """
    # Setup: Upload some waypoints first
    response = api_client.post_queue(sample_waypoints)
    assert response.status_code == 200

    # Verify waypoints are there
    queue = api_client.get_queue()
    assert_queue_not_empty(queue)

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
    response = api_client.post_queue([sample_waypoint])
    assert response.status_code == 200

    queue = api_client.get_queue()
    assert len(queue) == 1

    # Act: Upload different set of waypoints (should overwrite)
    response = api_client.post_queue(sample_waypoints)
    assert response.status_code == 200

    # Verify: Queue now contains the new waypoints
    queue = api_client.get_queue()
    assert len(queue) == len(
        sample_waypoints
    ), "Queue should be overwritten with new waypoints"

    # Verify the new waypoints match
    assert_waypoints_match(queue, sample_waypoints)


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
    response = api_client.post_queue(sample_waypoints)
    assert response.status_code == 200

    # Wait a moment
    time.sleep(2)

    # Retrieve queue multiple times
    queue1 = api_client.get_queue()
    time.sleep(1)
    queue2 = api_client.get_queue()

    # Assert: Queue is consistent across calls
    assert len(queue1) == len(sample_waypoints)
    assert len(queue2) == len(sample_waypoints)
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
    assert isinstance(queue, list), "Queue should be a list"
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
    response = api_client.post_queue(sample_waypoints)
    assert response.status_code == 200

    # Get queue from both services
    web_backend_queue = api_client.get_queue()
    mission_planner_queue = api_client.get_mission_planner_queue()

    # Assert: Both queues have same length
    assert len(web_backend_queue) == len(
        mission_planner_queue
    ), "Queue length mismatch between services"

    # Assert: Waypoints match
    for i, (wb_wp, mp_wp) in enumerate(zip(web_backend_queue, mission_planner_queue)):
        try:
            assert_waypoint_match(wb_wp, mp_wp)
        except AssertionError as e:
            raise AssertionError(f"Waypoint {i} mismatch between services: {e}") from e
