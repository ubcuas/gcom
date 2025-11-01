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
            print(
                f"Warning: Clear queue returned {response.status_code} during setup"
            )
    except (ConnectionError, TimeoutError) as e:
        # Connection failures should fail the test setup
        pytest.fail(f"Failed to connect to services during test setup: {e}")

    # Run the test
    yield

    # Teardown: Clean up after test
    try:
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
        "id": 0,
        "name": "Test Waypoint",
        "latitude": -35.363261,
        "longitude": 149.165230,
        "altitude": 50.0,
        "command": "WAYPOINT",
        "param1": 0,
        "param2": 0,
        "param3": 0,
        "param4": 0
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
