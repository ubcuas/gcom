from pymavlink import mavutil
from server.services.mavlink_receiver import MavlinkReceiver

def set_message_streaming_rates(receiver: MavlinkReceiver):
    GPS_RATE_HZ = 0.25
    ATTITUDE_RATE_HZ = 1
    VFR_HUD_RATE_HZ = 1
    SYS_STATUS_RATE_HZ = 5
    MISSION_ITEM_REACHED_RATE_HZ = 1
    WIND_COV_RATE_HZ = 10

    message = receiver.mav.command_long_encode(
        receiver.target_system,  # Target system ID
        receiver.target_component,  # Target component ID
        mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL,  # ID of command to send
        0,  # Confirmation
        mavutil.mavlink.MAVLINK_MSG_ID_GLOBAL_POSITION_INT,  # param1: Message ID to be streamed
        int(GPS_RATE_HZ * 1000000), # param2: Interval in microseconds
        0,       # param3 (unused)
        0,       # param4 (unused)
        0,       # param5 (unused)
        0,       # param6 (unused)
        2        # param7: Response Target: (2 - broadcast)
    )

    receiver.mav.send(message)

    response = receiver.wait_for_message(
        'COMMAND_ACK',
        timeout=3.0,
        filter_func=lambda msg: msg.command == mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL
    )
    if (response and response.result == mavutil.mavlink.MAV_RESULT_ACCEPTED):
        print(f"Setting {GPS_RATE_HZ = } Hz")
    else:
        print(f"Setting {GPS_RATE_HZ = } failed")

    message = receiver.mav.command_long_encode(
        receiver.target_system,  # Target system ID
        receiver.target_component,  # Target component ID
        mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL,  # ID of command to send
        0,  # Confirmation
        mavutil.mavlink.MAVLINK_MSG_ID_ATTITUDE,  # param1: Message ID to be streamed
        int(ATTITUDE_RATE_HZ * 1000000), # param2: Interval in microseconds
        0,       # param3 (unused)
        0,       # param4 (unused)
        0,       # param5 (unused)
        0,       # param6 (unused)
        2        # param7: Response Target: (2 - broadcast)
    )

    receiver.mav.send(message)

    response = receiver.wait_for_message(
        'COMMAND_ACK',
        timeout=3.0,
        filter_func=lambda msg: msg.command == mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL
    )
    if (response and response.result == mavutil.mavlink.MAV_RESULT_ACCEPTED):
        print(f"Setting {ATTITUDE_RATE_HZ = } Hz")
    else:
        print(f"Setting {ATTITUDE_RATE_HZ = } failed")
    
    message = receiver.mav.command_long_encode(
        receiver.target_system,  # Target system ID
        receiver.target_component,  # Target component ID
        mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL,  # ID of command to send
        0,  # Confirmation
        mavutil.mavlink.MAVLINK_MSG_ID_VFR_HUD,  # param1: Message ID to be streamed
        int(VFR_HUD_RATE_HZ * 1000000), # param2: Interval in microseconds
        0,       # param3 (unused)
        0,       # param4 (unused)
        0,       # param5 (unused)
        0,       # param6 (unused)
        2        # param7: Response Target: (2 - broadcast)
    )

    receiver.mav.send(message)

    response = receiver.wait_for_message(
        'COMMAND_ACK',
        timeout=3.0,
        filter_func=lambda msg: msg.command == mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL
    )
    if (response and response.result == mavutil.mavlink.MAV_RESULT_ACCEPTED):
        print(f"Setting {VFR_HUD_RATE_HZ = } Hz")
    else:
        print(f"Setting {VFR_HUD_RATE_HZ = } failed")

    message = receiver.mav.command_long_encode(
        receiver.target_system,  # Target system ID
        receiver.target_component,  # Target component ID
        mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL,  # ID of command to send
        0,  # Confirmation
        mavutil.mavlink.MAVLINK_MSG_ID_SYS_STATUS,  # param1: Message ID to be streamed
        int(SYS_STATUS_RATE_HZ * 1000000), # param2: Interval in microseconds
        0,       # param3 (unused)
        0,       # param4 (unused)
        0,       # param5 (unused)
        0,       # param6 (unused)
        2        # param7: Response Target: (2 - broadcast)
    )

    receiver.mav.send(message)

    response = receiver.wait_for_message(
        'COMMAND_ACK',
        timeout=3.0,
        filter_func=lambda msg: msg.command == mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL
    )
    if (response and response.result == mavutil.mavlink.MAV_RESULT_ACCEPTED):
        print(f"Setting {SYS_STATUS_RATE_HZ = } Hz")
    else:
        print(f"Setting {SYS_STATUS_RATE_HZ = } failed")
    
    message = receiver.mav.command_long_encode(
        receiver.target_system,  # Target system ID
        receiver.target_component,  # Target component ID
        mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL,  # ID of command to send
        0,  # Confirmation
        mavutil.mavlink.MAVLINK_MSG_ID_MISSION_ITEM_REACHED,  # param1: Message ID to be streamed
        int(MISSION_ITEM_REACHED_RATE_HZ * 1000000), # param2: Interval in microseconds
        0,       # param3 (unused)
        0,       # param4 (unused)
        0,       # param5 (unused)
        0,       # param6 (unused)
        2        # param7: Response Target: (2 - broadcast)
    )

    receiver.mav.send(message)

    response = receiver.wait_for_message(
        'COMMAND_ACK',
        timeout=3.0,
        filter_func=lambda msg: msg.command == mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL
    )
    if (response and response.result == mavutil.mavlink.MAV_RESULT_ACCEPTED):
        print(f"Setting {MISSION_ITEM_REACHED_RATE_HZ = } Hz")
    else:
        print(f"Setting {MISSION_ITEM_REACHED_RATE_HZ = } failed")
    
    message = receiver.mav.command_long_encode(
        receiver.target_system,  # Target system ID
        receiver.target_component,  # Target component ID
        mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL,  # ID of command to send
        0,  # Confirmation
        mavutil.mavlink.MAVLINK_MSG_ID_WIND_COV,  # param1: Message ID to be streamed
        int(WIND_COV_RATE_HZ * 1000000), # param2: Interval in microseconds
        0,       # param3 (unused)
        0,       # param4 (unused)
        0,       # param5 (unused)
        0,       # param6 (unused)
        2        # param7: Response Target: (2 - broadcast)
    )

    receiver.mav.send(message)

    response = receiver.wait_for_message(
        'COMMAND_ACK',
        timeout=3.0,
        filter_func=lambda msg: msg.command == mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL
    )
    if (response and response.result == mavutil.mavlink.MAV_RESULT_ACCEPTED):
        print(f"Setting {WIND_COV_RATE_HZ = } Hz")
    else:
        print(f"Setting {WIND_COV_RATE_HZ = } failed")



def request_messages(receiver: MavlinkReceiver, message_types: list) -> bool:
    for message_type in message_types:
        message = receiver.mav.command_long_encode(
            receiver.target_system,  # Target system ID
            receiver.target_component,  # Target component ID
            mavutil.mavlink.MAV_CMD_REQUEST_MESSAGE,  # ID of command to send
            0,  # Confirmation
            message_type,  # param1: Message ID to be streamed
            0,       # param2 (unused)
            0,       # param3 (unused)
            0,       # param4 (unused)
            0,       # param5 (unused)
            0,       # param6 (unused)
            0        # param7: Response Target (0 - default, 1 - requestor, 2 - broadcast)
        )

        receiver.mav.send(message)

        response = receiver.wait_for_message(
            'COMMAND_ACK',
            timeout=3.0,
            filter_func=lambda msg: msg.command == mavutil.mavlink.MAV_CMD_REQUEST_MESSAGE
        )
        if (response and response.result == mavutil.mavlink.MAV_RESULT_ACCEPTED):
            # print(f"Request for Message of type {message_type} ACCEPTED")
            pass
        else:
            print(f"Request for Message of type {message_type} DENIED")


def set_parameter(receiver: MavlinkReceiver, param_id, param_value) -> bool:
    param_id = bytes(param_id, "ascii")
    # obtain parameter type
    receiver.mav.param_request_read_send(
        receiver.target_system,
        receiver.target_component,
        param_id,
        -1
    )

    param_value_msg = receiver.wait_for_message('PARAM_VALUE', timeout=3.0)
    print(param_value_msg)

    if param_value_msg is None:
        return False
    before = param_value_msg.param_value
    param_type = param_value_msg.param_type

    receiver.mav.param_set_send(
        receiver.target_system,
        receiver.target_component,
        param_id,
        param_value,
        param_type
    )

    param_value_msg = receiver.wait_for_message('PARAM_VALUE', timeout=3.0)
    print(param_value_msg)

    if param_value_msg is None:
        return False
    after = param_value_msg.param_value

    print(f"Value of parameter {param_id} changed from {before} to {after}")
    
    return before != after and after == param_value
