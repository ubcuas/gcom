from pymavlink import mavutil

from server.common.wpqueue import WaypointQueue, Waypoint
from server.common.encoders import command_string_to_int, command_int_to_string
from server.services.mavlink_handler import MavlinkHandler
from server.logging_config import logger

def set_home(handler: MavlinkHandler, latitude: float, longitude: float, altitude: float): # -> int | None:
    # Send a set home command
    handler.mav.command_long_send(
        handler.target_system,
        handler.target_component,
        mavutil.mavlink.MAV_CMD_DO_SET_HOME,
        0, 0, 0, 0, 0, latitude, longitude, altitude
    )

    # Wait for the acknowledgment
    ack = handler.wait_for_message('COMMAND_ACK', timeout=5.0)
    if ack is None:
        logger.warning('No acknowledgment received within the timeout period.')
        return None

    return ack.result

def new_mission(handler: MavlinkHandler, waypoint_queue: WaypointQueue) -> bool:
    # Clear any existing mission from vehicle
    logger.info('Clearing mission')
    handler.mav.mission_clear_all_send(handler.target_system, handler.target_component)

    if not verify_ack(handler, 'Error clearing mission'):
        return False
    
    # Insert the home waypoint
    wp_list = []
    seq = 0
    wp_list.append(mavutil.mavlink.MAVLink_mission_item_int_message(
        0, 0, seq, 0, 16, 0, 0, 0, 0, 0, 0,
        0, 
        0, 
        0
    ))
    
    # Insert the rest of the waypoints
    for seq in range(1, len(waypoint_queue) + 1):
        wp: Waypoint = waypoint_queue[seq - 1]

        wp_list.append(mavutil.mavlink.MAVLink_mission_item_int_message(
        handler.target_system, handler.target_component, seq,
        0, command_string_to_int(wp._com), 0, 1,
        float(wp._param1), float(wp._param2), float(wp._param3),
        float(wp._param4), int(wp._lat * 10000000), int(wp._lng * 10000000),
        int(wp._alt)
    ))

    # Send waypoint count to the UAV
    handler.connection.waypoint_count_send(len(wp_list))

    # Upload waypoints to the UAV
    return send_waypoints(handler, wp_list)

def send_waypoints(handler: MavlinkHandler, wp_list: list) -> bool:
    """
    Send the waypoints to the UAV.

    Args:
        handler: The MavlinkHandler instance
        wploader (list): The waypoint loader list.

    Returns:
        bool: True if waypoints are successfully sent, False otherwise.
    """
    for i in range(len(wp_list)):
        msg = handler.wait_for_any_message(['MISSION_REQUEST_INT', 'MISSION_REQUEST'], timeout=3.0)
        if not msg:
            logger.warning('No waypoint request received')
            return False
        logger.info(f'Sending waypoint {msg.seq}/{len(wp_list)-1}')
        handler.mav.send(wp_list[msg.seq])

        if msg.seq == len(wp_list)-1:
            break

    return verify_ack(handler, 'Error uploading mission')

def verify_ack(handler: MavlinkHandler, error_msg: str) -> bool:
    """
    Verifies the ack response.

    Args:
        handler: The MavlinkHandler instance
        error_msg (str): The error message to log if ack verification fails.

    Returns:
        bool: True if ack verification successful, False otherwise.
    """
    ack = handler.wait_for_message('MISSION_ACK', timeout=3.0)
    logger.debug(f"Mission ACK: {ack}")
    if (ack is None):
        logger.error(f'{error_msg}: No ACK received')
    elif (ack.type != 0):
        logger.error(f'{error_msg}: {ack.type}')
        return False
    return True

def clear_mission(handler: MavlinkHandler) -> bool:
    handler.mav.mission_clear_all_send(
        handler.target_system,
        handler.target_component,
        mavutil.mavlink.MAV_MISSION_TYPE_MISSION
    )

    return verify_ack(handler, "")

