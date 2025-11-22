"""HTTP API client for integration tests.

This client provides a clean interface for making requests to the web-backend
and mission-planner APIs. All integration tests should go through web-backend
to test the full stack.
"""

import requests
from typing import List, Dict, Optional, Any
from requests import Response


class APIClient:
    """Client for interacting with GCOM services during integration tests."""

    def __init__(self, web_backend_url: str, mission_planner_url: str):
        """Initialize API client with base URLs.

        Args:
            web_backend_url: Base URL for web-backend (e.g., http://localhost:8000)
            mission_planner_url: Base URL for mission-planner (e.g., http://localhost:9000)
        """
        self.web_backend_url = web_backend_url.rstrip("/")
        self.mission_planner_url = mission_planner_url.rstrip("/")

    # ==================== Web-Backend API Methods ====================
    # These are the primary methods for integration tests - they hit web-backend
    # which then forwards to mission-planner, testing the full integration.

    def get_status(self) -> Dict[str, Any]:
        """Get current drone status via web-backend.

        Returns:
            Status dictionary with telemetry data
        """
        response = requests.get(f"{self.web_backend_url}/api/drone/status")
        response.raise_for_status()
        return response.json()

    def get_queue(self) -> List[Dict[str, Any]]:
        """Get current waypoint queue via web-backend.

        Returns:
            List of waypoint dictionaries
        """
        response = requests.get(f"{self.web_backend_url}/api/drone/queue")
        response.raise_for_status()
        return response.json()

    def post_queue(self, waypoints: List[Dict[str, Any]]) -> Response:
        """Upload waypoint queue via web-backend.

        Args:
            waypoints: List of waypoint dictionaries

        Returns:
            Response object
        """
        response = requests.post(
            f"{self.web_backend_url}/api/drone/queue",
            json=waypoints,
            headers={"Content-Type": "application/json"},
        )
        return response

    def clear_queue(self) -> Response:
        """Clear waypoint queue via web-backend.

        Returns:
            Response object
        """
        response = requests.get(f"{self.web_backend_url}/api/drone/clear")
        return response

    def takeoff(self, altitude: float) -> Response:
        """Send takeoff command via web-backend.

        Args:
            altitude: Target altitude in meters

        Returns:
            Response object
        """
        response = requests.post(
            f"{self.web_backend_url}/api/drone/takeoff",
            json={"altitude": altitude},
            headers={"Content-Type": "application/json"},
        )
        return response

    def arm(self, arm_value: bool) -> Response:
        """Arm or disarm motors via web-backend.

        Args:
            arm_value: True to arm, False to disarm

        Returns:
            Response object
        """
        response = requests.put(
            f"{self.web_backend_url}/api/drone/arm",
            json={"arm": arm_value},
            headers={"Content-Type": "application/json"},
        )
        return response

    def land(self) -> Response:
        """Send land command via web-backend.

        Returns:
            Response object
        """
        response = requests.get(f"{self.web_backend_url}/api/drone/land")
        return response

    def rtl(self, altitude: Optional[float] = None) -> Response:
        """Send return-to-launch command via web-backend.

        Args:
            altitude: Optional altitude to maintain during RTL

        Returns:
            Response object
        """
        if altitude is not None:
            response = requests.post(
                f"{self.web_backend_url}/api/drone/rtl",
                json={"altitude": altitude},
                headers={"Content-Type": "application/json"},
            )
        else:
            response = requests.get(f"{self.web_backend_url}/api/drone/rtl")
        return response

    def post_home(self, waypoint: Dict[str, Any]) -> Response:
        """Set home position via web-backend.

        Args:
            waypoint: Waypoint dictionary with lat/lon/alt

        Returns:
            Response object
        """
        response = requests.post(
            f"{self.web_backend_url}/api/drone/home",
            json=waypoint,
            headers={"Content-Type": "application/json"},
        )
        return response

    def insert_waypoints(self, waypoints: List[Dict[str, Any]]) -> Response:
        """Insert waypoints before current position via web-backend.

        Args:
            waypoints: List of waypoint dictionaries

        Returns:
            Response object
        """
        response = requests.post(
            f"{self.web_backend_url}/api/drone/insert",
            json=waypoints,
            headers={"Content-Type": "application/json"},
        )
        return response

    # ==================== Mission-Planner Direct Access ====================
    # These methods bypass web-backend and hit mission-planner directly.
    # Use sparingly - only for verification or debugging, not primary test flow.

    def get_mission_planner_queue(self) -> List[Dict[str, Any]]:
        """Get queue directly from mission-planner (for verification).

        Returns:
            List of waypoint dictionaries
        """
        response = requests.get(f"{self.mission_planner_url}/queue")
        response.raise_for_status()
        return response.json()

    def get_mission_planner_status(self) -> Dict[str, Any]:
        """Get status directly from mission-planner (for verification).

        Returns:
            Status dictionary
        """
        response = requests.get(f"{self.mission_planner_url}/status")
        response.raise_for_status()
        return response.json()

    def mission_planner_health_check(self) -> bool:
        """Check if mission-planner server is responding.

        Returns:
            True if server is healthy
        """
        try:
            response = requests.get(f"{self.mission_planner_url}/", timeout=5)
            return response.status_code == 200
        except:
            return False

    def web_backend_health_check(self) -> bool:
        """Check if web-backend server is responding.

        Returns:
            True if server is healthy
        """
        try:
            response = requests.get(
                f"{self.web_backend_url}/api/drone/status", timeout=5
            )
            return response.status_code == 200
        except (requests.RequestException, ConnectionError, TimeoutError):
            return False
