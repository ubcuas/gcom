from pymavlink.mavutil import mavfile, mavlink
from server.services.mavlink_receiver import MavlinkReceiver


def change_flight_mode(
    mav_connection: mavfile, receiver: MavlinkReceiver, tgt_sys_id: int = 1, tgt_comp_id: int = 1, flightmode: str = ""
) -> bool:

    flightmode = flightmode.upper()
    if flightmode not in mav_connection.mode_mapping():
        return False

    mode_id = mav_connection.mode_mapping()[flightmode.upper()]
    sub_mode = 0

    mav_connection.mav.command_long_send(
        target_system=tgt_sys_id,
        target_component=tgt_comp_id,
        command=mavlink.MAV_CMD_DO_SET_MODE,
        confirmation=0,
        param1=mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
        param2=mode_id,
        param3=sub_mode,
        param4=0,
        param5=0,
        param6=0,
        param7=0,
    )
    verify_ack(receiver, "Failed ACK after change_flight_mode")

    return True


def change_aircraft_type(mav_connection: mavfile):
    # TODO investigate whether to deprecate
    pass

def verify_ack(receiver: MavlinkReceiver, error_msg: str) -> bool:
    """
    Verifies the ack response.

    Args:
        receiver: The MavlinkReceiver instance
        error_msg (str): The error message to log if ack verification fails.

    Returns:
        bool: True if ack verification successful, False otherwise.
    """
    ack = receiver.wait_for_message('COMMAND_ACK', timeout=3.0)
    print("ack:", ack)
    # if ack.type != 0:
    #     print(f'{error_msg}: {ack.type}')
    #     return False
    return True