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
