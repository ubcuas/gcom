"""Helpers for waypoint flow integration tests.

These functions support the complete flow from route creation
through database storage to drone queue operations.
"""

from typing import Dict, Any, List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .api_client import APIClient


def create_route_with_waypoints(
    api_client: "APIClient",
    route_name: str,
    num_waypoints: int = 3,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Create a route with specified number of waypoints.

    Creates a route in the database and populates it with the specified
    number of waypoints. Waypoints are created with incremental positions
    and standard test values.

    Args:
        api_client: API client instance
        route_name: Name for the route
        num_waypoints: Number of waypoints to create (default: 3)

    Returns:
        tuple: (route_dict, list_of_created_waypoints)
            - route_dict: The created route from the API
            - list_of_created_waypoints: List of waypoint dicts as returned by API

    Raises:
        AssertionError: If route or waypoint creation fails
    """
    # Create route
    route_response = api_client.create_route({"name": route_name})
    assert route_response.status_code == 201, f"Failed to create route: {route_response.text}"
    route = route_response.json()

    # Create waypoints
    created_waypoints = []
    for i in range(num_waypoints):
        waypoint_data = {
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
        response = api_client.create_waypoint(waypoint_data)
        assert response.status_code == 201, f"Failed to create waypoint {i}: {response.text}"
        created_waypoints.append(response.json())

    return route, created_waypoints


def transform_db_waypoints_to_drone_format(
    db_waypoints: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Transform database waypoints to drone API format.

    Database waypoints include fields like UUID ids, route references,
    radius values, etc. The drone API expects a simpler format with
    sequential integer IDs and core position fields only.

    Database format includes: id (UUID), name, lat, lon, alt, order, route, radius, etc.
    Drone format needs: id (int), name, latitude, longitude, altitude

    Args:
        db_waypoints: List of waypoint dicts from database API

    Returns:
        list: Waypoints formatted for drone API with sequential integer IDs
    """
    return [
        {
            "id": idx,
            "name": wp["name"],
            "latitude": wp["latitude"],
            "longitude": wp["longitude"],
            "altitude": wp["altitude"],
        }
        for idx, wp in enumerate(db_waypoints)
    ]
