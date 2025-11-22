"""Pytest configuration and shared fixtures for integration tests.

This module provides fixtures that are automatically available to all tests.
The fixtures handle service URLs, API client setup, and state reset.
"""

import os
import pytest
from dotenv import load_dotenv
from helpers import APIClient

# Load environment variables from .env file if it exists
load_dotenv()


@pytest.fixture(scope="session")
def web_backend_url():
    """Get web-backend URL from environment.

    Returns:
        str: Web-backend base URL
    """
    return os.getenv("WEB_BACKEND_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def mission_planner_url():
    """Get mission-planner URL from environment.

    Returns:
        str: Mission-planner base URL
    """
    return os.getenv("MISSION_PLANNER_URL", "http://localhost:9000")


@pytest.fixture(scope="session")
def api_client(web_backend_url, mission_planner_url):
    """Create API client instance for the test session.

    This client is shared across all tests in the session.

    Args:
        web_backend_url: Web-backend URL from fixture
        mission_planner_url: Mission-planner URL from fixture

    Returns:
        APIClient: Configured API client instance
    """
    client = APIClient(web_backend_url, mission_planner_url)

    # Verify services are running before starting tests
    if not client.web_backend_health_check():
        pytest.exit(
            "Web-backend is not responding. Please start the service.", returncode=1
        )

    if not client.mission_planner_health_check():
        pytest.exit(
            "Mission-planner is not responding. Please start the service.", returncode=1
        )

    return client


@pytest.fixture(autouse=True)
def reset_drone_state(api_client):
    """Reset drone state before each test.

    This fixture runs automatically before every test to ensure a clean state.
    It clears the waypoint queue and resets any test-specific state.

    Args:
        api_client: API client from fixture

    Yields:
        None: Control returns to test after setup
    """
    # Setup: Clear state before test
    try:
        response = api_client.clear_queue()
        # Only acceptable failures are queue already empty or endpoint quirks
        if response.status_code not in [200, 204]:
            print(f"Warning: Clear queue returned {response.status_code} during setup")
    except (ConnectionError, TimeoutError) as e:
        # Connection failures should fail the test setup
        pytest.fail(f"Failed to connect to services during test setup: {e}")

    # Run the test
    yield

    # Teardown: Clean up after test
    try:
        # Clear waypoint queue
        response = api_client.clear_queue()
        if response.status_code not in [200, 204]:
            print(
                f"Warning: Clear queue returned {response.status_code} during teardown"
            )
    except (ConnectionError, TimeoutError):
        # Connection failures during teardown are logged but don't fail the test
        # as the test itself may have already completed successfully
        print("Warning: Failed to connect to services during teardown")


@pytest.fixture
def sample_waypoint():
    """Provide a sample waypoint for testing.

    Returns:
        dict: Waypoint dictionary with valid test data
    """
    return {
        "name": "TestWP1",
        "latitude": -35.363261,
        "longitude": 149.165230,
        "altitude": 50.0,
    }


@pytest.fixture
def sample_waypoints():
    """Provide a list of sample waypoints for testing.

    Returns:
        list: List of waypoint dictionaries with valid test data
    """
    return [
        {
            "name": "WP1",
            "latitude": -35.363261,
            "longitude": 149.165230,
            "altitude": 50.0,
        },
        {
            "name": "WP2",
            "latitude": -35.363361,
            "longitude": 149.165330,
            "altitude": 55.0,
        },
        {
            "name": "WP3",
            "latitude": -35.363461,
            "longitude": 149.165430,
            "altitude": 60.0,
        },
    ]


@pytest.fixture
def sample_route_data():
    """Provide sample route data for testing.

    Returns:
        dict: Route dictionary with name
    """
    return {"name": "Test Route"}


@pytest.fixture
def sample_waypoint_db_data():
    """Provide a sample waypoint for database testing.

    This includes fields specific to database waypoints (OrderedWaypoint).
    Note: 'route' field should be added when creating waypoint.

    Returns:
        dict: Waypoint dictionary with database-specific fields
    """
    return {
        "name": "TestWP1",
        "latitude": -35.363261,
        "longitude": 149.165230,
        "altitude": 50.0,
        "radius": 5.0,
        "pass_radius": 5.0,
        "pass_option": 0,
        "order": 0,
    }


@pytest.fixture(autouse=True)
def reset_database_state(api_client):
    """Reset database state before and after each test.

    This fixture runs automatically before every test to ensure a clean database.
    It clears all routes (which cascades to waypoints) and individual waypoints.

    Args:
        api_client: API client from fixture

    Yields:
        None: Control returns to test after setup
    """
    # Setup: Clear database before test
    try:
        # Delete all routes (cascades to waypoints)
        routes = api_client.list_routes()
        for route in routes:
            api_client.delete_route(route["id"])

        # Delete any orphaned waypoints
        waypoints = api_client.list_waypoints()
        for waypoint in waypoints:
            api_client.delete_waypoint(waypoint["id"])
    except Exception as e:
        # Log but don't fail on cleanup errors
        print(f"Warning: Database cleanup failed during setup: {e}")

    # Run the test
    yield

    # Teardown: Clean up after test
    try:
        # Delete all routes (cascades to waypoints)
        routes = api_client.list_routes()
        for route in routes:
            api_client.delete_route(route["id"])

        # Delete any orphaned waypoints
        waypoints = api_client.list_waypoints()
        for waypoint in waypoints:
            api_client.delete_waypoint(waypoint["id"])
    except Exception as e:
        # Log but don't fail on cleanup errors
        print(f"Warning: Database cleanup failed during teardown: {e}")
