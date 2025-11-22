"""Integration tests for complete waypoint flow.

These tests verify the full flow from route creation in the database
through to posting waypoints to the drone via Mission Planner.

Key considerations:
- Mission Planner adds a default "Home" waypoint at position 0
- Mission Planner doesn't preserve waypoint names
- Tests validate lat/lon/alt fields but skip name validation
"""

import pytest
from helpers import (
    create_route_with_waypoints,
    transform_db_waypoints_to_drone_format,
    assert_route_contains_waypoints,
    assert_waypoints_match,
    filter_home_waypoint,
    assert_queue_upload_successful,
    assert_queue_empty,
)


@pytest.mark.critical
def test_basic_route_to_drone_flow(api_client, sample_route_data):
    """Test complete flow: create route, add waypoints, post to drone.

    This test verifies the integration from database storage through
    to drone queue:
    1. Create route with waypoints in database
    2. Retrieve route
    3. Transform waypoints to drone format
    4. Post to drone
    5. Verify waypoints in drone queue

    Note: MAVLink missions always include a home waypoint, so uploading
    1 waypoint results in a queue with 2 items (home + uploaded waypoint).

    Args:
        api_client: API client fixture
        sample_route_data: Sample route data fixture
    """
    # Step 1: Create route with waypoints
    route, waypoints = create_route_with_waypoints(
        api_client,
        sample_route_data["name"],
        num_waypoints=3
    )

    # Step 2: Retrieve route from database
    retrieved_route = api_client.get_route(route["id"])
    assert_route_contains_waypoints(retrieved_route, 3)

    # Step 3: Transform waypoints to drone format
    drone_waypoints = transform_db_waypoints_to_drone_format(
        retrieved_route["waypoints"]
    )

    # Step 4: Post to drone
    response = api_client.post_queue(drone_waypoints)
    assert response.status_code == 200, f"Failed to post to drone: {response.text}"

    # Step 5: Verify drone queue (exclude name - Mission Planner doesn't preserve)
    queue = api_client.get_queue()
    filtered = filter_home_waypoint(queue)
    assert_waypoints_match(
        filtered,
        drone_waypoints,
        check_fields=["latitude", "longitude", "altitude"]
    )


def test_empty_route_to_drone_flow(api_client, sample_route_data):
    """Test posting empty route clears drone queue.

    Verifies that posting a route with no waypoints correctly
    clears the drone queue (excluding the home waypoint).

    Args:
        api_client: API client fixture
        sample_route_data: Sample route data fixture
    """
    # Step 1: Create empty route
    route_response = api_client.create_route(sample_route_data)
    assert route_response.status_code == 201
    route = route_response.json()

    # Step 2: Retrieve empty route
    retrieved_route = api_client.get_route(route["id"])
    assert_route_contains_waypoints(retrieved_route, 0)

    # Step 3: Transform empty waypoint list
    drone_waypoints = transform_db_waypoints_to_drone_format(
        retrieved_route["waypoints"]
    )
    assert len(drone_waypoints) == 0

    # Step 4: Post empty list to drone
    response = api_client.post_queue(drone_waypoints)
    assert response.status_code == 200, "Should accept empty waypoint list"

    # Step 5: Verify queue is empty (excluding home waypoint)
    queue = api_client.get_queue()
    filtered = filter_home_waypoint(queue)
    assert len(filtered) == 0, "Drone queue should be empty (excluding home waypoint)"


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

    # Wait for waypoints to persist (home + uploaded waypoints)
    from helpers import wait_for_waypoint_count
    wait_for_waypoint_count(api_client, len(sample_waypoints) + 1, timeout=10)

    # Retrieve queue multiple times to verify persistence
    queue1 = api_client.get_queue()
    time.sleep(1)
    queue2 = api_client.get_queue()

    # Assert: Queue is consistent across calls (filter home waypoint, don't check names)
    filtered1 = filter_home_waypoint(queue1)
    filtered2 = filter_home_waypoint(queue2)
    assert_waypoints_match(
        filtered1,
        sample_waypoints,
        check_fields=["latitude", "longitude", "altitude"]
    )
    assert_waypoints_match(
        filtered2,
        sample_waypoints,
        check_fields=["latitude", "longitude", "altitude"]
    )


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

    # Assert: Both services return the same queue (all fields should match exactly)
    assert_waypoints_match(web_backend_queue, mission_planner_queue)
