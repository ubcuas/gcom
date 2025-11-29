"""Integration test for autonomous navigation with waypoint missions.

This test verifies complex flight sequences including waypoint navigation,
mid-flight mode changes, and air-start scenarios.
"""

import pytest
from helpers import (
    wait_for_altitude,
    wait_for_flight_mode,
    wait_for_position,
    wait_for_stationary,
    filter_home_waypoint,
)


@pytest.mark.slow
@pytest.mark.critical
@pytest.mark.timeout(240)
def test_autonomous_navigation(api_client, flight_cleanup):
    """Test autonomous waypoint navigation with air start.

    This test validates:
    - Takeoff and altitude achievement
    - Mid-flight mode switching (AUTO -> GUIDED -> AUTO)
    - Air start waypoint navigation
    - Waypoint mission execution (3 waypoints + return home + loiter)
    - RTL parameter preparation without mode change
    - Manual RTL initiation and landing

    Test Sequence:
    PHASE 1: Initial Takeoff
    1. Prepare takeoff to altitude 50m
    2. Arm drone
    3. Switch to AUTO mode
    4. Verify altitude reached
    5. Switch to GUIDED mode (mid-flight)

    PHASE 2: Mission Setup
    6. Upload waypoint mission:
       - 3 navigation waypoints
       - Return to start position
       - Loiter indefinitely
    7. Switch to AUTO mode (air start)

    PHASE 3: Mission Execution
    8. Verify drone navigates to each waypoint
    9. Verify drone returns to start
    10. Verify drone loiters at final waypoint

    PHASE 4: Landing
    11. Prepare RTL parameters (verify no mode change)
    12. Trigger RTL mode manually
    13. Verify drone returns home and lands

    Expected Timeline:
    - Takeoff: ~20 seconds
    - Waypoint navigation: ~2-3 minutes
    - Loiter verification: ~30 seconds
    - RTL and landing: ~30 seconds
    - Total: ~4-5 minutes

    Cleanup:
    - Automatic cleanup via flight_cleanup fixture

    Args:
        api_client: API client fixture
        flight_cleanup: Flight cleanup fixture
    """
    # Configuration
    takeoff_altitude = 50.0
    rtl_altitude = 30.0

    # PHASE 1: Initial Takeoff
    print("\n=== PHASE 1: Initial Takeoff ===")

    # Get baseline altitude
    initial_status = api_client.get_status()
    baseline_altitude = initial_status["altitude"]
    start_lat = initial_status["latitude"]
    start_lon = initial_status["longitude"]
    target_altitude = baseline_altitude + takeoff_altitude

    print(f"Start position: ({start_lat:.6f}, {start_lon:.6f})")
    print(f"Baseline altitude: {baseline_altitude}m")
    print(f"Target altitude: {target_altitude}m")

    # Prepare takeoff
    response = api_client.prepare_takeoff(target_altitude)
    assert response.status_code == 200, f"Prepare takeoff failed: {response.text}"
    print(f"Prepare takeoff command sent (altitude: {target_altitude}m)")

    # Arm drone
    response = api_client.arm(True)
    assert response.status_code == 200, f"Arm command failed: {response.text}"
    print("Drone armed")

    # Switch to AUTO mode to initiate takeoff
    response = api_client.set_flight_mode_direct("AUTO")
    assert response.status_code == 200, f"AUTO mode failed: {response.text}"
    print("Switched to AUTO mode - initiating takeoff")

    # Wait for target altitude
    wait_for_altitude(api_client, target_altitude, timeout=120, tolerance=2.0)
    print(f"Takeoff complete - altitude: {target_altitude}m")

    # Switch to GUIDED mode (mid-flight mode change)
    print("Switching to GUIDED mode (mid-flight)...")
    response = api_client.set_flight_mode_direct("GUIDED")
    assert response.status_code == 200, f"GUIDED mode failed: {response.text}"

    wait_for_flight_mode(api_client, "GUIDED", timeout=10)
    print("GUIDED mode active")

    # PHASE 2: Mission Setup
    print("\n=== PHASE 2: Mission Setup ===")

    # Create waypoint mission
    # Using offsets to create a simple box pattern around start position
    lat_offset = 0.0001  # ~11 meters
    lon_offset = 0.0001  # ~11 meters

    waypoints = [
        # WP1: North
        {
            "id": 1,
            "name": "WP1 North",
            "latitude": start_lat + lat_offset,
            "longitude": start_lon,
            "altitude": target_altitude,
        },
        # WP2: North-East
        {
            "id": 2,
            "name": "WP2 North-East",
            "latitude": start_lat + lat_offset,
            "longitude": start_lon + lon_offset,
            "altitude": target_altitude,
        },
        # WP3: East
        {
            "id": 3,
            "name": "WP3 East",
            "latitude": start_lat,
            "longitude": start_lon + lon_offset,
            "altitude": target_altitude,
        },
        # WP4: Return to start
        {
            "id": 4,
            "name": "WP4 Return",
            "latitude": start_lat,
            "longitude": start_lon,
            "altitude": target_altitude,
        },
        # WP5: Loiter indefinitely at start position
        {
            "id": 5,
            "name": "WP5 Loiter",
            "latitude": start_lat,
            "longitude": start_lon,
            "altitude": target_altitude,
            "command": "LOITER_UNLIM",
        },
    ]

    print(f"Uploading mission with {len(waypoints)} waypoints...")
    response = api_client.post_queue(waypoints)
    assert response.status_code == 200, f"Failed to upload waypoints: {response.text}"

    # Verify queue
    queue = api_client.get_queue()
    filtered_queue = filter_home_waypoint(queue)
    assert len(filtered_queue) == len(waypoints), (
        f"Expected {len(waypoints)} waypoints in queue, got {len(filtered_queue)}"
    )
    print(f"Mission uploaded: {len(filtered_queue)} waypoints")

    # PHASE 3: Mission Execution (Air Start)
    print("\n=== PHASE 3: Mission Execution (Air Start) ===")

    # Switch to AUTO mode while airborne (air start)
    print("Switching to AUTO mode (air start)...")
    response = api_client.set_flight_mode_direct("AUTO")
    assert response.status_code == 200, f"AUTO mode failed: {response.text}"

    wait_for_flight_mode(api_client, "AUTO", timeout=10)
    print("AUTO mode active - drone should proceed to first waypoint")

    # Navigate through waypoints
    print("\nNavigating to waypoints...")

    for i, wp in enumerate(waypoints[:-1], start=1):  # Exclude loiter waypoint
        print(f"Waypoint {i}/{len(waypoints)-1}: ({wp['latitude']:.6f}, {wp['longitude']:.6f})")
        wait_for_position(
            api_client,
            wp["latitude"],
            wp["longitude"],
            timeout=120,
            tolerance_meters=15.0,
        )
        print(f"Reached waypoint {i}")

    # Verify loiter at final waypoint
    print("\nVerifying loiter at final waypoint...")
    final_wp = waypoints[-1]
    wait_for_position(
        api_client,
        final_wp["latitude"],
        final_wp["longitude"],
        timeout=120,
        tolerance_meters=15.0,
    )
    print("Reached final waypoint (loiter position)")

    # Verify drone is hovering/loitering
    print("Verifying loiter behavior (stationary for 20s)...")
    wait_for_stationary(
        api_client,
        duration=20.0,
        speed_threshold=1.0,
        vertical_speed_threshold=0.5,
        timeout=60.0,
    )
    print("Loiter confirmed - drone hovering at final waypoint")

    # PHASE 4: Landing
    print("\n=== PHASE 4: Landing ===")

    # Prepare RTL parameters
    print(f"Preparing RTL parameters (altitude: {rtl_altitude}m)...")
    current_mode_before = api_client.get_flight_mode()
    response = api_client.prepare_rtl_params(rtl_altitude)
    assert response.status_code == 200, f"Prepare RTL params failed: {response.text}"
    print("RTL parameters set")

    # Verify mode did NOT change
    current_mode_after = api_client.get_flight_mode()
    assert current_mode_after == current_mode_before, (
        f"Flight mode should not change after prepare_rtl_params. "
        f"Expected: {current_mode_before}, Got: {current_mode_after}"
    )
    print(f"Flight mode unchanged: {current_mode_after}")

    # Trigger RTL manually
    print("Triggering RTL mode manually...")
    response = api_client.set_flight_mode_direct("RTL")
    assert response.status_code == 200, f"RTL mode failed: {response.text}"

    wait_for_flight_mode(api_client, "RTL", timeout=10)
    print("RTL mode active - drone returning home")

    # Wait for drone to return to baseline altitude (landed)
    print(f"Waiting for landing (baseline altitude: {baseline_altitude}m)...")
    wait_for_altitude(
        api_client,
        baseline_altitude,
        timeout=180,
        tolerance=2.0,
    )
    print("Drone landed")

    # Verify final position near start
    final_status = api_client.get_status()
    final_lat = final_status["latitude"]
    final_lon = final_status["longitude"]

    # Calculate distance from start
    lat_diff_m = abs(final_lat - start_lat) * 111000
    lon_diff_m = abs(final_lon - start_lon) * 111000
    distance_from_start = (lat_diff_m**2 + lon_diff_m**2) ** 0.5

    print(
        f"Final position: ({final_lat:.6f}, {final_lon:.6f}), "
        f"Distance from start: {distance_from_start:.1f}m"
    )

    assert distance_from_start <= 20.0, (
        f"Drone should land near start position, but is {distance_from_start:.1f}m away"
    )

    print("\n=== Test Complete ===")
    print(f"Mission executed successfully:")
    print(f"  - Navigated {len(waypoints)} waypoints")
    print(f"  - Loitered at final position")
    print(f"  - Returned home and landed")
