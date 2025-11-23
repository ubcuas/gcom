#!/usr/bin/env python3
"""
Simple test script to verify MavlinkReceiver and StatusCache services.

This script connects to a MAVLink source and tests that:
1. The receiver thread starts and runs
2. Status messages are cached properly
3. wait_for_message works with timeouts and filtering
4. The receiver shuts down cleanly

Usage:
    python test_services.py <connection_string>

Example:
    python test_services.py udp:127.0.0.1:14550
    python test_services.py /dev/ttyUSB0
"""

import sys
import time
from pymavlink import mavutil

# Add parent directory to path to import server modules
sys.path.insert(0, '../../')

from server.services.status_cache import StatusCache
from server.services.mavlink_receiver import MavlinkReceiver
from server.operations.get_info import get_status


def test_services(connection_string: str):
    print(f"Connecting to MAVLink at {connection_string}...")
    mav_connection = mavutil.mavlink_connection(connection_string)

    print("Waiting for heartbeat...")
    mav_connection.wait_heartbeat()
    print(f"Heartbeat received from system {mav_connection.target_system} component {mav_connection.target_component}")

    # Create services
    print("\n=== Creating services ===")
    status_cache = StatusCache()
    receiver = MavlinkReceiver(mav_connection, status_cache)

    # Start receiver
    print("\n=== Starting receiver ===")
    receiver.start()
    time.sleep(1)  # Give it a moment to start

    if receiver.is_running():
        print("Receiver is running")
    else:
        print("ERROR: Receiver failed to start")
        return

    # Wait for status messages to populate
    print("\n=== Waiting for status messages (5 seconds) ===")
    time.sleep(5)

    # Check status cache
    print("\n=== Checking status cache ===")
    cached_messages = status_cache.get_all()
    print(f"Cached {len(cached_messages)} message types:")
    for msg_type, (msg, age) in cached_messages.items():
        print(f"  {msg_type}: age={age:.2f}s")

    # Test specific message retrieval
    print("\n=== Testing specific message retrieval ===")
    gps_msg = status_cache.get_message('GLOBAL_POSITION_INT')
    if gps_msg:
        print(f"GLOBAL_POSITION_INT: lat={gps_msg.lat/1e7:.6f}, lon={gps_msg.lon/1e7:.6f}, alt={gps_msg.alt/1000:.1f}m")
    else:
        print("GLOBAL_POSITION_INT not yet cached")

    # Test wait_for_message with timeout
    print("\n=== Testing wait_for_message (HEARTBEAT, 3s timeout) ===")
    start = time.time()
    heartbeat = receiver.wait_for_message('HEARTBEAT', timeout=3.0)
    elapsed = time.time() - start
    if heartbeat:
        print(f"Received HEARTBEAT in {elapsed:.2f}s from system {heartbeat.get_srcSystem()}")
    else:
        print(f"Timeout waiting for HEARTBEAT after {elapsed:.2f}s")

    # Test wait_for_message with filter
    print("\n=== Testing wait_for_message with filter (HEARTBEAT from specific system) ===")
    target_system = mav_connection.target_system
    start = time.time()
    filtered_heartbeat = receiver.wait_for_message(
        'HEARTBEAT',
        timeout=5.0,
        filter_func=lambda msg: msg.get_srcSystem() == target_system
    )
    elapsed = time.time() - start
    if filtered_heartbeat:
        print(f"Received filtered HEARTBEAT in {elapsed:.2f}s")
    else:
        print(f"Timeout waiting for filtered HEARTBEAT after {elapsed:.2f}s")

    # Test wait_for_any_message
    print("\n=== Testing wait_for_any_message (HEARTBEAT or SYS_STATUS) ===")
    start = time.time()
    any_msg = receiver.wait_for_any_message(['HEARTBEAT', 'SYS_STATUS'], timeout=3.0)
    elapsed = time.time() - start
    if any_msg:
        print(f"Received {any_msg.get_type()} in {elapsed:.2f}s")
    else:
        print(f"Timeout waiting for any message after {elapsed:.2f}s")

    # Test get_status function
    print("\n=== Testing get_status() with status_cache ===")
    try:
        status = get_status(status_cache)
        status_dict = status.as_dictionary()
        print(f"Status retrieved successfully:")
        print(f"  Position: lat={status_dict.get('latitude', 0):.6f}, lon={status_dict.get('longitude', 0):.6f}, alt={status_dict.get('altitude', 0):.1f}m")
        print(f"  Attitude: roll={status_dict.get('roll', 0):.1f}°, pitch={status_dict.get('pitch', 0):.1f}°, yaw={status_dict.get('yaw', 0):.1f}°")
        print(f"  Speed: airspeed={status_dict.get('airspeed', 0):.1f} m/s, groundspeed={status_dict.get('groundspeed', 0):.1f} m/s")
        print(f"  Battery: {status_dict.get('voltage', 0):.1f}V")
    except Exception as e:
        print(f"ERROR getting status: {e}")
        import traceback
        traceback.print_exc()

    # Stop receiver
    print("\n=== Stopping receiver ===")
    receiver.stop()

    if not receiver.is_running():
        print("Receiver stopped successfully")
    else:
        print("WARNING: Receiver still running")

    print("\n=== Test complete ===")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    connection_string = sys.argv[1]

    try:
        test_services(connection_string)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
