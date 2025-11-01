"""Integration tests for waypoint and route database API endpoints.

These tests verify database CRUD operations for waypoints and routes,
as well as integration between database waypoints and drone queue operations.
"""

import pytest
from helpers import (
    assert_waypoint_db_match,
    assert_route_contains_waypoints,
    assert_waypoints_ordered,
    assert_waypoints_match,
)


@pytest.mark.critical
def test_create_single_waypoint(api_client, sample_waypoint_db_data, sample_route_data):
    """Test creating a single waypoint in the database.

    Args:
        api_client: API client fixture
        sample_waypoint_db_data: Sample waypoint data fixture
        sample_route_data: Sample route data fixture
    """
    # Create a route first (waypoints need to belong to a route)
    route_response = api_client.create_route(sample_route_data)
    assert route_response.status_code == 201, f"Failed to create route: {route_response.text}"
    route = route_response.json()

    # Add route to waypoint data
    waypoint_data = {**sample_waypoint_db_data, "route": route["id"]}

    # Act: Create waypoint
    response = api_client.create_waypoint(waypoint_data)

    # Assert: Verify creation
    assert response.status_code == 201, f"Failed to create waypoint: {response.text}"
    created_waypoint = response.json()

    # Verify returned waypoint has ID and matches input
    assert "id" in created_waypoint, "Created waypoint missing 'id' field"
    assert_waypoint_db_match(created_waypoint, waypoint_data)

    # Verify persistence by retrieving
    retrieved_waypoint = api_client.get_waypoint(created_waypoint["id"])
    assert_waypoint_db_match(retrieved_waypoint, waypoint_data)


def test_create_multiple_waypoints(api_client, sample_route_data):
    """Test creating multiple waypoints in the database.

    Args:
        api_client: API client fixture
        sample_route_data: Sample route data fixture
    """
    # Create a route first
    route_response = api_client.create_route(sample_route_data)
    assert route_response.status_code == 201
    route = route_response.json()

    # Create multiple waypoints
    waypoints_data = [
        {
            "name": f"WP{i}",
            "latitude": -35.363261 + (i * 0.001),
            "longitude": 149.165230 + (i * 0.001),
            "altitude": 50.0 + (i * 5),
            "order": i,
            "route": route["id"],
            "radius": 5.0,
            "pass_radius": 5.0,
            "pass_option": 0,
        }
        for i in range(3)
    ]

    created_waypoints = []
    for wp_data in waypoints_data:
        response = api_client.create_waypoint(wp_data)
        assert response.status_code == 201, f"Failed to create waypoint: {response.text}"
        created_waypoints.append(response.json())

    # Verify all waypoints exist
    all_waypoints = api_client.list_waypoints()
    assert len(all_waypoints) >= 3, f"Expected at least 3 waypoints, found {len(all_waypoints)}"

    # Verify each created waypoint
    for created, expected in zip(created_waypoints, waypoints_data):
        assert_waypoint_db_match(created, expected)


def test_list_waypoints(api_client, sample_route_data):
    """Test listing all waypoints from the database.

    Args:
        api_client: API client fixture
        sample_route_data: Sample route data fixture
    """
    # Create a route
    route_response = api_client.create_route(sample_route_data)
    route = route_response.json()

    # Create several waypoints
    num_waypoints = 4
    for i in range(num_waypoints):
        waypoint_data = {
            "name": f"ListWP{i}",
            "latitude": -35.363261 + (i * 0.001),
            "longitude": 149.165230 + (i * 0.001),
            "altitude": 50.0,
            "order": i,
            "route": route["id"],
        }
        response = api_client.create_waypoint(waypoint_data)
        assert response.status_code == 201

    # Act: List all waypoints
    waypoints = api_client.list_waypoints()

    # Assert: Verify all are present
    assert len(waypoints) >= num_waypoints, f"Expected at least {num_waypoints} waypoints"
    waypoint_names = [wp["name"] for wp in waypoints]
    for i in range(num_waypoints):
        assert f"ListWP{i}" in waypoint_names


def test_get_waypoint_by_id(api_client, sample_waypoint_db_data, sample_route_data):
    """Test retrieving a specific waypoint by ID.

    Args:
        api_client: API client fixture
        sample_waypoint_db_data: Sample waypoint data fixture
        sample_route_data: Sample route data fixture
    """
    # Create route and waypoint
    route_response = api_client.create_route(sample_route_data)
    route = route_response.json()

    waypoint_data = {**sample_waypoint_db_data, "route": route["id"]}
    create_response = api_client.create_waypoint(waypoint_data)
    created_waypoint = create_response.json()

    # Act: Get waypoint by ID
    retrieved_waypoint = api_client.get_waypoint(created_waypoint["id"])

    # Assert: Verify exact match
    assert_waypoint_db_match(retrieved_waypoint, waypoint_data)
    assert retrieved_waypoint["id"] == created_waypoint["id"]


def test_update_waypoint(api_client, sample_waypoint_db_data, sample_route_data):
    """Test updating a waypoint's data.

    Args:
        api_client: API client fixture
        sample_waypoint_db_data: Sample waypoint data fixture
        sample_route_data: Sample route data fixture
    """
    # Create route and waypoint
    route_response = api_client.create_route(sample_route_data)
    route = route_response.json()

    waypoint_data = {**sample_waypoint_db_data, "route": route["id"]}
    create_response = api_client.create_waypoint(waypoint_data)
    waypoint = create_response.json()

    # Modify waypoint data
    updated_data = {
        **waypoint_data,
        "name": "UpdatedWP",
        "altitude": 100.0,
        "latitude": -35.400000,
    }

    # Act: Update waypoint
    update_response = api_client.partial_update_waypoint(waypoint["id"], updated_data)

    # Assert: Verify update succeeded
    assert update_response.status_code == 200, f"Failed to update waypoint: {update_response.text}"

    # Verify changes persisted
    retrieved_waypoint = api_client.get_waypoint(waypoint["id"])
    assert retrieved_waypoint["name"] == "UpdatedWP"
    assert abs(retrieved_waypoint["altitude"] - 100.0) < 0.001
    assert abs(retrieved_waypoint["latitude"] - (-35.400000)) < 0.0001


def test_delete_waypoint(api_client, sample_waypoint_db_data, sample_route_data):
    """Test deleting a waypoint from the database.

    Args:
        api_client: API client fixture
        sample_waypoint_db_data: Sample waypoint data fixture
        sample_route_data: Sample route data fixture
    """
    # Create route and waypoint
    route_response = api_client.create_route(sample_route_data)
    route = route_response.json()

    waypoint_data = {**sample_waypoint_db_data, "route": route["id"]}
    create_response = api_client.create_waypoint(waypoint_data)
    waypoint = create_response.json()

    # Act: Delete waypoint
    delete_response = api_client.delete_waypoint(waypoint["id"])

    # Assert: Verify deletion
    assert delete_response.status_code == 204, f"Failed to delete waypoint: {delete_response.text}"

    # Verify waypoint no longer exists (should get 404)
    try:
        api_client.get_waypoint(waypoint["id"])
        pytest.fail("Expected 404 when getting deleted waypoint")
    except Exception as e:
        assert "404" in str(e), f"Expected 404 error, got: {e}"


def test_create_route_with_waypoints(api_client, sample_route_data):
    """Test creating a route with multiple waypoints and verify nested structure.

    Args:
        api_client: API client fixture
        sample_route_data: Sample route data fixture
    """
    # Create route
    route_response = api_client.create_route(sample_route_data)
    assert route_response.status_code == 201
    route = route_response.json()

    # Create waypoints for the route
    num_waypoints = 3
    for i in range(num_waypoints):
        waypoint_data = {
            "name": f"RouteWP{i}",
            "latitude": -35.363261 + (i * 0.001),
            "longitude": 149.165230 + (i * 0.001),
            "altitude": 50.0,
            "order": i,
            "route": route["id"],
        }
        response = api_client.create_waypoint(waypoint_data)
        assert response.status_code == 201

    # Act: Get route with nested waypoints
    retrieved_route = api_client.get_route(route["id"])

    # Assert: Verify route contains waypoints
    assert_route_contains_waypoints(retrieved_route, num_waypoints)
    assert_waypoints_ordered(retrieved_route["waypoints"])


def test_reorder_waypoints_in_route(api_client, sample_route_data):
    """Test reordering waypoints within a route.

    Args:
        api_client: API client fixture
        sample_route_data: Sample route data fixture
    """
    # Create route
    route_response = api_client.create_route(sample_route_data)
    route = route_response.json()

    # Create 4 waypoints in order
    waypoint_ids = []
    for i in range(4):
        waypoint_data = {
            "name": f"OrderWP{i}",
            "latitude": -35.363261 + (i * 0.001),
            "longitude": 149.165230 + (i * 0.001),
            "altitude": 50.0,
            "order": i,
            "route": route["id"],
        }
        response = api_client.create_waypoint(waypoint_data)
        waypoint = response.json()
        waypoint_ids.append(waypoint["id"])

    # Act: Reorder waypoints [0,1,2,3] -> [3,1,0,2]
    new_order = [waypoint_ids[3], waypoint_ids[1], waypoint_ids[0], waypoint_ids[2]]
    reorder_response = api_client.reorder_route_waypoints(route["id"], new_order)

    # Assert: Verify reorder succeeded
    assert reorder_response.status_code == 200, f"Failed to reorder: {reorder_response.text}"

    # Verify new order
    retrieved_route = api_client.get_route(route["id"])
    waypoints = retrieved_route["waypoints"]

    assert len(waypoints) == 4
    assert waypoints[0]["id"] == waypoint_ids[3]
    assert waypoints[1]["id"] == waypoint_ids[1]
    assert waypoints[2]["id"] == waypoint_ids[0]
    assert waypoints[3]["id"] == waypoint_ids[2]

    # Verify order field is updated correctly
    assert_waypoints_ordered(waypoints)


def test_delete_route_cascades_to_waypoints(api_client, sample_route_data):
    """Test that deleting a route also deletes its waypoints (cascade).

    Args:
        api_client: API client fixture
        sample_route_data: Sample route data fixture
    """
    # Create route with waypoints
    route_response = api_client.create_route(sample_route_data)
    route = route_response.json()

    waypoint_ids = []
    for i in range(3):
        waypoint_data = {
            "name": f"CascadeWP{i}",
            "latitude": -35.363261 + (i * 0.001),
            "longitude": 149.165230 + (i * 0.001),
            "altitude": 50.0,
            "order": i,
            "route": route["id"],
        }
        response = api_client.create_waypoint(waypoint_data)
        waypoint = response.json()
        waypoint_ids.append(waypoint["id"])

    # Act: Delete route
    delete_response = api_client.delete_route(route["id"])
    assert delete_response.status_code == 204

    # Assert: Verify waypoints are also deleted
    for waypoint_id in waypoint_ids:
        try:
            api_client.get_waypoint(waypoint_id)
            pytest.fail(f"Expected waypoint {waypoint_id} to be deleted with route")
        except Exception as e:
            assert "404" in str(e), f"Expected 404 error for waypoint {waypoint_id}"


def test_waypoint_validation(api_client, sample_route_data):
    """Test that invalid waypoint data is rejected with appropriate errors.

    Args:
        api_client: API client fixture
        sample_route_data: Sample route data fixture
    """
    # Create route
    route_response = api_client.create_route(sample_route_data)
    route = route_response.json()

    # Test missing required fields
    incomplete_waypoint = {
        "name": "IncompleteWP",
        # Missing latitude, longitude, altitude (required fields)
        "order": 0,
        "route": route["id"],
    }

    response = api_client.create_waypoint(incomplete_waypoint)
    assert response.status_code == 400, "Expected 400 for missing required fields"


def test_load_saved_route_to_drone(api_client, sample_route_data):
    """Test loading a saved route from database to drone queue.

    This test verifies the integration between database waypoints and drone control:
    1. Create route with waypoints in database
    2. Retrieve route
    3. Transform waypoints to drone format
    4. Load to drone queue
    5. Verify drone has the waypoints

    Args:
        api_client: API client fixture
        sample_route_data: Sample route data fixture
    """
    # Step 1: Create route in database
    route_response = api_client.create_route(sample_route_data)
    route = route_response.json()

    # Create waypoints in database
    db_waypoints_data = []
    for i in range(3):
        waypoint_data = {
            "name": f"DroneWP{i}",
            "latitude": -35.363261 + (i * 0.001),
            "longitude": 149.165230 + (i * 0.001),
            "altitude": 50.0 + (i * 5),
            "order": i,
            "route": route["id"],
            "radius": 5.0,
            "pass_radius": 5.0,
            "pass_option": 0,
        }
        response = api_client.create_waypoint(waypoint_data)
        assert response.status_code == 201
        db_waypoints_data.append(waypoint_data)

    # Step 2: Retrieve route from database
    retrieved_route = api_client.get_route(route["id"])
    assert_route_contains_waypoints(retrieved_route, 3)

    # Step 3: Transform database waypoints to drone format
    # Drone waypoints need: id, name, latitude, longitude, altitude
    drone_waypoints = [
        {
            "id": idx,
            "name": wp["name"],
            "latitude": wp["latitude"],
            "longitude": wp["longitude"],
            "altitude": wp["altitude"],
        }
        for idx, wp in enumerate(retrieved_route["waypoints"])
    ]

    # Step 4: Load to drone queue
    upload_response = api_client.post_queue(drone_waypoints)
    assert upload_response.status_code == 200, f"Failed to upload to drone: {upload_response.text}"

    # Step 5: Verify drone queue
    drone_queue = api_client.get_queue()
    assert_waypoints_match(drone_queue, drone_waypoints)


def test_load_empty_route_to_drone(api_client, sample_route_data):
    """Test loading an empty route to the drone queue.

    Args:
        api_client: API client fixture
        sample_route_data: Sample route data fixture
    """
    # Create route with no waypoints
    route_response = api_client.create_route(sample_route_data)
    route = route_response.json()

    # Retrieve empty route
    retrieved_route = api_client.get_route(route["id"])
    assert_route_contains_waypoints(retrieved_route, 0)

    # Attempt to load empty route to drone
    drone_waypoints = []
    upload_response = api_client.post_queue(drone_waypoints)

    # Should accept empty queue (clearing the queue)
    assert upload_response.status_code == 200, "Should accept empty waypoint list"

    # Verify drone queue is empty
    drone_queue = api_client.get_queue()
    assert len(drone_queue) == 0, "Drone queue should be empty"


def test_waypoint_not_found_error(api_client):
    """Test that accessing non-existent waypoint returns 404.

    Args:
        api_client: API client fixture
    """
    fake_uuid = "00000000-0000-0000-0000-000000000000"

    # Test GET
    try:
        api_client.get_waypoint(fake_uuid)
        pytest.fail("Expected 404 when getting non-existent waypoint")
    except Exception as e:
        assert "404" in str(e), f"Expected 404 error, got: {e}"

    # Test DELETE
    delete_response = api_client.delete_waypoint(fake_uuid)
    assert delete_response.status_code == 404, "Expected 404 for delete on non-existent waypoint"

    # Test UPDATE
    update_data = {
        "name": "UpdatedWP",
        "latitude": -35.363261,
        "longitude": 149.165230,
        "altitude": 50.0,
    }
    update_response = api_client.partial_update_waypoint(fake_uuid, update_data)
    assert update_response.status_code == 404, "Expected 404 for update on non-existent waypoint"
