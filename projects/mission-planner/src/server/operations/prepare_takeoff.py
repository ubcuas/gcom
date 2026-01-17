from server.common.wpqueue import Waypoint, WaypointQueue
from server.logging_config import logger
from server.operations.get_info import get_status
from server.operations.queue import new_mission
from server.services.mavlink_handler import MavlinkHandler
from server.services.status_cache import StatusCache
from server.utilities.request_message_streaming import set_parameter
from server.utilities.wait_for_position_aiding import wait_until_position_aiding


def prepare_takeoff(
    handler: MavlinkHandler, status_cache: StatusCache, altitude: float
) -> bool:
    """
    Prepares the drone for takeoff by clearing the waypoint queue and adding a single waypoint at the current drone position with the specified altitude.

    This prepares the takeoff sequence because when the drone is armed and switched to AUTO mode
    by the pilot, the drone will automatically takeoff to this first waypoint.

    Args:
        handler: The MavlinkHandler instance
        status_cache: The StatusCache instance to get current position
        altitude: Target altitude in meters for the takeoff waypoint

    Returns:
        bool: True if mission was successfully prepared, False otherwise
    """
    # Get current drone position
    wait_until_position_aiding(handler)
    status = get_status(status_cache)
    current_lat = status._lat
    current_lng = status._lng

    # Set AUTO_OPTIONS to 3
    if not set_parameter(handler, "AUTO_OPTIONS", 3):
        logger.warning("Failed to set AUTO_OPTIONS parameter to 3")

    # Create a mission with a single waypoint at current position with target altitude
    takeoff_mission = WaypointQueue()
    takeoff_mission.push(
        Waypoint(
            id=0,
            name="Takeoff",
            lat=current_lat,
            lng=current_lng,
            alt=altitude,
            command="TAKEOFF",
        )
    )

    # Upload the new mission (this clears existing mission first)
    return new_mission(handler, takeoff_mission)
