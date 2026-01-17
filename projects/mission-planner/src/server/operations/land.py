from pymavlink import mavutil

from server.logging_config import logger
from server.services.mavlink_handler import MavlinkHandler


# return value of 0 indicates success
def land_in_place(handler: MavlinkHandler, timeout: int = 10) -> int:
    # Send a land command
    handler.mav.command_long_send(
        handler.target_system,
        handler.target_component,
        mavutil.mavlink.MAV_CMD_NAV_LAND,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
    )

    # Wait for the acknowledgment
    ack = handler.wait_for_message("COMMAND_ACK", timeout=float(timeout))
    if ack is None:
        logger.warning("No acknowledgment received within the timeout period.")
        return -1

    return ack.result


# return value of 0 indicates success
def land_at_position(
    handler: MavlinkHandler, latitude: float, longitude: float, timeout: int = 10
) -> int:
    # Send a land command
    handler.mav.command_long_send(
        handler.target_system,
        handler.target_component,
        mavutil.mavlink.MAV_CMD_NAV_LAND,
        0,
        0,
        0,
        0,
        0,
        latitude,
        longitude,
        0,
    )

    # Wait for the acknowledgment
    ack = handler.wait_for_message("COMMAND_ACK", timeout=float(timeout))
    if ack is None:
        logger.warning("No acknowledgment received within the timeout period.")
        return -1

    logger.debug(f"land at position command ack: {ack}")

    return ack.result
