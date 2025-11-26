import math

from pymavlink import mavutil

from server.common.status import Status
from server.common.wpqueue import WaypointQueue, Waypoint
from server.common.encoders import command_int_to_string
from server.services.status_cache import StatusCache
from server.services.mavlink_handler import MavlinkHandler

"""
    Get current status of a drone
    Type of message can be found on https://mavlink.io/en/messages/common.html

"""
def get_status(status_cache: StatusCache) -> Status:
    """
    Get current drone status from the status cache.

    This function reads from the status cache which is continuously updated
    by the global MAVLink handler thread. Returns near-instantaneously without
    any blocking network I/O.

    Args:
        status_cache: The StatusCache instance containing latest MAVLink messages

    Returns:
        Status object with current drone state
    """

    # Helper to create default objects for missing messages
    Object = lambda **kwargs: type("Object", (), kwargs)

    # Retrieve cached messages with their ages
    system_time_data = status_cache.get('SYSTEM_TIME')
    system_time = system_time_data[0] if system_time_data else Object(time_unix_usec=0, time_boot_ms=0)
    latency_time = system_time_data[1] if system_time_data else 0

    status_gps_data = status_cache.get('GLOBAL_POSITION_INT')
    status_gps = status_gps_data[0] if status_gps_data else Object(lat=0, lon=0, alt=0)
    latency_gps = status_gps_data[1] if status_gps_data else 0

    status_att_data = status_cache.get('ATTITUDE')
    status_att = status_att_data[0] if status_att_data else Object(roll=0, pitch=0, yaw=0)
    latency_att = status_att_data[1] if status_att_data else 0

    status_vfr_data = status_cache.get('VFR_HUD')
    status_vfr = status_vfr_data[0] if status_vfr_data else Object(airspeed=0, groundspeed=0, climb=0)
    latency_vfr = status_vfr_data[1] if status_vfr_data else 0

    status_sys_data = status_cache.get('SYS_STATUS')
    status_sys = status_sys_data[0] if status_sys_data else Object(voltage_battery=0)
    latency_sys = status_sys_data[1] if status_sys_data else 0

    status_wpn_data = status_cache.get('MISSION_CURRENT')
    status_wpn = status_wpn_data[0] if status_wpn_data else Object(seq=0, total=0, mission_state=0, mission_mode=0, mission_id=0)
    latency_wpn = status_wpn_data[1] if status_wpn_data else 0

    status_wind_data = status_cache.get('WIND_COV')
    status_wind = status_wind_data[0] if status_wind_data else Object(wind_x=0, wind_y=0)
    latency_wind = status_wind_data[1] if status_wind_data else 0

    # print(f"Latencies: {latency_time:.2f}s, {latency_gps:.2f}s, {latency_att:.2f}s, {latency_vfr:.2f}s, {latency_sys:.2f}s, {latency_wpn:.2f}s, {latency_wind:.2f}s")

    # wind calculations in the horizontal plane TODO determine if vertical windspeed is needed
    winddirection = math.degrees(math.atan(status_wind.wind_x / status_wind.wind_y)) if status_wind.wind_y != 0 else (0 if status_wind.wind_x > 0 else 180)
    windvelocity = math.sqrt(status_wind.wind_x * status_wind.wind_x + status_wind.wind_y * status_wind.wind_y)

    return Status(
        system_time.time_unix_usec / 1000000, # seconds

        status_wpn.seq,

        status_gps.lat / 10000000,
        status_gps.lon / 10000000,
        status_gps.alt / 1000, # meters

        math.degrees(status_att.roll),
        math.degrees(status_att.pitch),
        math.degrees(status_att.yaw) % 360,

        status_vfr.airspeed,
        status_vfr.groundspeed,
        status_vfr.climb,

        status_sys.voltage_battery,

        winddirection,
        windvelocity
    )

def get_current_mission(handler: MavlinkHandler) -> WaypointQueue:

    ret = WaypointQueue()

    handler.mav.mission_request_list_send(
        handler.target_system,
        handler.target_component,
        mavutil.mavlink.MAV_MISSION_TYPE_MISSION
    )

    msg = handler.wait_for_message('MISSION_COUNT', timeout=3.0)
    if not msg:
        raise TimeoutError('No MISSION_COUNT received within timeout period')
    if msg and msg.get_type() != "BAD_DATA":
        print(f"Recieved {msg}")

    # use MISSION_REQUEST_INT for all mission items
    for current in range(msg.count):
        msg = handler.mav.mission_request_int_send(
            handler.target_system,
            handler.target_component,
            current,
            mavutil.mavlink.MAV_MISSION_TYPE_MISSION
        )

        # receive MISSION_ITEM_INT
        msg = handler.wait_for_message('MISSION_ITEM_INT', timeout=3.0)
        print(f"Received MISSION_ITEM_INT: {msg}")
        if msg and msg.get_type() != "BAD_DATA":
            # print(f"Recieved the {current}th Mission Item: {msg}")

            ret.push(Waypoint(msg.seq, f"Mission Waypoint {msg.seq}" if msg.seq != 0 else "Home Waypoint",
                            msg.x / 10000000,
                            msg.y / 10000000,
                            msg.z,
                            command_int_to_string(msg.command),
                            msg.param1,
                            msg.param2,
                            msg.param3,
                            msg.param4))
        else:
            raise TimeoutError(f"Failed to receive MISSION_ITEM_INT for waypoint {current}")

    return ret