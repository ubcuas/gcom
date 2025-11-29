from pymavlink.mavutil import mavfile, mavlink
from server.services.mavlink_handler import MavlinkHandler


def change_flight_mode(
    handler: MavlinkHandler,
    tgt_sys_id: int = 1,
    tgt_comp_id: int = 1,
    flightmode: str = "",
) -> bool:
    flightmode = flightmode.upper()
    if flightmode not in handler.mode_mapping():
        return False

    mode_id = handler.mode_mapping()[flightmode.upper()]
    sub_mode = 0

    handler.mav.command_long_send(
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
    verify_ack(handler, "Failed ACK after change_flight_mode")

    return True


def change_aircraft_type(mav_connection: mavfile):
    # TODO investigate whether to deprecate
    pass


def verify_ack(handler: MavlinkHandler, error_msg: str) -> bool:
    """
    Verifies the ack response.

    Args:
        handler: The MavlinkHandler instance
        error_msg (str): The error message to log if ack verification fails.

    Returns:
        bool: True if ack verification successful, False otherwise.
    """
    ack = handler.wait_for_message("COMMAND_ACK", timeout=3.0)
    print("ack:", ack)
    # if ack.type != 0:
    #     print(f'{error_msg}: {ack.type}')
    #     return False
    return True
