from pymavlink import mavutil
from server.services.mavlink_receiver import MavlinkReceiver

# return value of 0 indicates success
def land_in_place(mavlink_connection: mavutil.mavlink_connection, receiver: MavlinkReceiver, timeout: int = 10) -> int:
    # Send a land command
    mavlink_connection.mav.command_long_send(
        mavlink_connection.target_system,
        mavlink_connection.target_component,
        mavutil.mavlink.MAV_CMD_NAV_LAND,
        0, 0, 0, 0, 0, 0, 0, 0
    )

    # Wait for the acknowledgment
    ack = receiver.wait_for_message('COMMAND_ACK', timeout=float(timeout))
    if ack is None:
        print('No acknowledgment received within the timeout period.')
        return -1

    return ack.result

# return value of 0 indicates success
def land_at_position(mavlink_connection: mavutil.mavlink_connection, receiver: MavlinkReceiver, latitude: float, longitude: float, timeout: int = 10) -> int:
    # Send a land command
    mavlink_connection.mav.command_long_send(
        mavlink_connection.target_system,
        mavlink_connection.target_component,
        mavutil.mavlink.MAV_CMD_NAV_LAND,
        0, 0, 0, 0, 0, latitude, longitude, 0
    )

    # Wait for the acknowledgment
    ack = receiver.wait_for_message('COMMAND_ACK', timeout=float(timeout))
    if ack is None:
        print('No acknowledgment received within the timeout period.')
        return -1

    print(f"land at position command ack: {ack}")

    return ack.result
