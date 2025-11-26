from pymavlink import mavutil
from server.utilities.connect_to_sysid import connect_to_sysid
from server.utilities.wait_for_position_aiding import wait_until_position_aiding
from server.utilities.get_autopilot_info import get_autopilot_info
from server.services.mavlink_receiver import MavlinkReceiver

def takeoff(receiver: MavlinkReceiver, takeoff_altitude, tgt_sys_id: int = 1, tgt_comp_id: int = 1) -> int:
    # TODO: what's the difference between these tgt_sys_id and tgt_comp_id parameters, and receiver.target_system & receiver.target_component?
    print("Heartbeat from system (system %u component %u)" %
          (receiver.target_system, receiver.target_component))

    wait_until_position_aiding(receiver)

    autopilot_info = get_autopilot_info(receiver, tgt_sys_id)

    if autopilot_info["autopilot"] == "ardupilotmega":
        print("Connected to ArduPilot autopilot")
        mode_id = receiver.mode_mapping()["GUIDED"]
        takeoff_params = [0, 0, 0, 0, 0, 0, takeoff_altitude]

    elif autopilot_info["autopilot"] == "px4":
        print("Connected to PX4 autopilot")
        print(receiver.mode_mapping())
        mode_id = receiver.mode_mapping()["TAKEOFF"][1]
        print(mode_id)
        msg = receiver.wait_for_message('GLOBAL_POSITION_INT', timeout=3.0)
        starting_alt = msg.alt / 1000
        takeoff_params = [0, 0, 0, 0, float("NAN"), float("NAN"), starting_alt + takeoff_altitude]

    else:
        raise ValueError("Autopilot not supported")

    # Change mode to guided (Ardupilot) or takeoff (PX4)
    receiver.mav.command_long_send(tgt_sys_id, tgt_comp_id, mavutil.mavlink.MAV_CMD_DO_SET_MODE,
                                0, mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED, mode_id, 0, 0, 0, 0, 0)
    ack_msg = receiver.wait_for_message('COMMAND_ACK', timeout=3.0)
    print(f"Change Mode ACK:  {ack_msg}")
    # ! Commented out fail handling because we are going to completely rewrite the takeoff logic
    # if ack_msg.result != 0:
    #     return ack_msg.result

    # Arm the UAS
    if arm_disarm(receiver, True) != 0:
        return 1

    # Command Takeoff
    receiver.mav.command_long_send(tgt_sys_id, tgt_comp_id,
                                         mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, 0, takeoff_params[0], takeoff_params[1], takeoff_params[2], takeoff_params[3], takeoff_params[4], takeoff_params[5], takeoff_params[6])

    takeoff_msg = receiver.wait_for_message('COMMAND_ACK', timeout=3.0)
    print(f"Takeoff ACK:  {takeoff_msg}")

    return takeoff_msg.result

def arm_disarm(receiver: MavlinkReceiver, arm_disarm: bool) -> int:

    receiver.mav.command_long_send(receiver.target_system, receiver.target_component,
                                         mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 0, 1 if arm_disarm else 0, 0, 0, 0, 0, 0, 0)

    arm_msg = receiver.wait_for_message('COMMAND_ACK', timeout=3.0)
    print(f"Arm ACK:  {arm_msg}")

    return arm_msg.result