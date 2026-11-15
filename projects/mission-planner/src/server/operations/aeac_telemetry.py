from pymavlink import mavutil

from server.services.status_cache import StatusCache

UAV_ID = "ubc-uas"
UNKNOWN_ACCURACY = 99.0

LINK_STRONG_S = 1.5
LINK_LOST_S = 3.0

AUTO_MODES = {"AUTO", "GUIDED", "RTL", "SMART_RTL", "LAND", "BRAKE", "FOLLOW"}
FAILSAFE_STATES = {
    mavutil.mavlink.MAV_STATE_CRITICAL,
    mavutil.mavlink.MAV_STATE_EMERGENCY,
}

STREAM_RATES_HZ = {
    mavutil.mavlink.MAVLINK_MSG_ID_GLOBAL_POSITION_INT: 5,
    mavutil.mavlink.MAVLINK_MSG_ID_SYSTEM_TIME: 2,
    mavutil.mavlink.MAVLINK_MSG_ID_GPS_RAW_INT: 2,
    mavutil.mavlink.MAVLINK_MSG_ID_SYS_STATUS: 2,
    mavutil.mavlink.MAVLINK_MSG_ID_RC_CHANNELS: 2,
}


def request_streams(mav_connection):
    for msg_id, hz in STREAM_RATES_HZ.items():
        mav_connection.mav.command_long_send(
            mav_connection.target_system,
            mav_connection.target_component,
            mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL,
            0,
            msg_id,
            int(1_000_000 / hz),
            0,
            0,
            0,
            0,
            0,
        )


def position_unix_time(position, sys_time):
    if sys_time is None or sys_time.time_unix_usec == 0:
        return None

    offset_s = (sys_time.time_boot_ms - position.time_boot_ms) / 1000
    return sys_time.time_unix_usec / 1e6 - offset_s


def position_accuracy(gps):
    if gps is None:
        return UNKNOWN_ACCURACY, UNKNOWN_ACCURACY

    h = getattr(gps, "h_acc", 0) / 1000
    v = getattr(gps, "v_acc", 0) / 1000
    return (
        h if h > 0 else UNKNOWN_ACCURACY,
        v if v > 0 else UNKNOWN_ACCURACY,
    )


def battery_percentage(sys_status):
    if sys_status is None or sys_status.battery_remaining < 0:
        return 0.0

    return float(min(100, sys_status.battery_remaining))


def flight_status(cache: StatusCache, heartbeat_age):
    if heartbeat_age > LINK_LOST_S:
        return "link-lost"

    heartbeat = cache.get_message("HEARTBEAT")
    if heartbeat.system_status in FAILSAFE_STATES:
        return "failsafe"

    if not heartbeat.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED:
        return "idle"

    if cache.get_flight_mode() in AUTO_MODES:
        return "armed-automatic"

    return "armed-pilot"


def telemetry_link(heartbeat_age):
    if heartbeat_age < LINK_STRONG_S:
        return 1.0

    if heartbeat_age < LINK_LOST_S:
        return 0.5

    return 0.0


def rc_link(cache: StatusCache):
    rc = cache.get_message("RC_CHANNELS")
    rc_age = cache.get_age("RC_CHANNELS")

    if (
        rc is not None
        and rc.rssi != 255
        and rc_age is not None
        and rc_age < LINK_LOST_S
    ):
        return round(rc.rssi / 254, 2)

    sys_status = cache.get_message("SYS_STATUS")
    if sys_status is None:
        return 0.0

    rc_bit = mavutil.mavlink.MAV_SYS_STATUS_SENSOR_RC_RECEIVER
    return 1.0 if sys_status.onboard_control_sensors_health & rc_bit else 0.0


def build_telemetry(cache: StatusCache):
    position = cache.get_message("GLOBAL_POSITION_INT")
    heartbeat_age = cache.get_age("HEARTBEAT")

    if position is None or heartbeat_age is None:
        return None

    unix_time = position_unix_time(position, cache.get_message("SYSTEM_TIME"))

    if unix_time is None:
        return None

    h_acc, v_acc = position_accuracy(cache.get_message("GPS_RAW_INT"))

    return {
        "uavId": UAV_ID,
        "latitude": position.lat / 1e7,
        "longitude": position.lon / 1e7,
        "unixTime": unix_time,
        "altitudeAGL": max(0.0, position.relative_alt / 1000),
        "horizontalPositionAccuracy": h_acc,
        "verticalPositionAccuracy": v_acc,
        "batteryPercentage": battery_percentage(cache.get_message("SYS_STATUS")),
        "mode": flight_status(cache, heartbeat_age),
        "rcLinkStatus": rc_link(cache),
        "telemetryLinkStatus": telemetry_link(heartbeat_age),
    }
