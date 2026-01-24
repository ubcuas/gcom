"""Integration test for basic takeoff and hover sequence.

This test verifies that prepare_takeoff clears existing waypoints and the drone
can takeoff and maintain a stable hover at the target altitude.
"""

import pytest

from helpers import (
    filter_home_waypoint,
    wait_for_altitude,
    wait_for_flight_mode,
    wait_for_stationary,
)


@pytest.mark.slow
@pytest.mark.critical
def test_basic_takeoff_and_hover(api_client, flight_cleanup):
    """Test basic takeoff and hover sequence.

    This test validates:
    - Prepare takeoff clears existing waypoints
    - Prepare takeoff does not change flight mode
    - Operator can arm and set GUIDED mode manually
    - Switching to AUTO initiates takeoff
    - Drone reaches target altitude and hovers stably

    Test Sequence:
    1. Add a test waypoint to mission queue
    2. Send prepare_takeoff command (altitude 40m)
       - Verify queue cleared (only home + takeoff waypoint)
       - Verify flight mode unchanged
    3. Arm drone and switch to GUIDED mode (emulating pilot)
       - Verify GUIDED mode active
    4. Switch to AUTO mode (emulating pilot)
       - Drone should takeoff to 40m
    5. Verify drone maintains stable hover

    Expected Timeline:
    - Arming + Takeoff to 40m: ~15-20 seconds
    - Hover verification: ~10 seconds
    - Total test duration: ~30-45 seconds

    Cleanup:
    - Automatic cleanup via flight_cleanup fixture

    Args:
        api_client: API client fixture
        flight_cleanup: Flight cleanup fixture
    """
    target_relative_altitude = 40.0

    # Step 1: Get initial status and baseline altitude
    initial_status = api_client.get_status()
    baseline_altitude = initial_status["altitude"]
    target_altitude = baseline_altitude + target_relative_altitude
    initial_mode = api_client.get_flight_mode()

    print(f"Initial altitude: {baseline_altitude}m, Initial mode: {initial_mode}")
    print(f"Target altitude: {target_altitude}m ({target_relative_altitude}m relative)")

    # Step 2: Add a dummy waypoint to test that prepare_takeoff clears it
    dummy_waypoint = [
        {
            "id": 1,
            "name": "Dummy Waypoint",
            "latitude": -35.363261,
            "longitude": 149.165230,
            "altitude": 100.0,
        }
    ]
    response = api_client.post_queue(dummy_waypoint)
    assert response.status_code == 200, f"Failed to add dummy waypoint: {response.text}"
    print("Dummy waypoint added to queue")

    # Verify dummy waypoint exists
    queue = api_client.get_queue()
    filtered_queue = filter_home_waypoint(queue)
    assert len(filtered_queue) == 1, "Dummy waypoint should be in queue"

    # Step 3: Prepare takeoff (should clear dummy waypoint and add takeoff waypoint)
    response = api_client.prepare_takeoff(target_altitude)
    assert response.status_code == 200, f"Prepare takeoff failed: {response.text}"
    print(f"Prepare takeoff command sent (altitude: {target_altitude}m)")

    # Step 4: Verify queue cleared and only contains home + takeoff waypoint
    queue = api_client.get_queue()
    filtered_queue = filter_home_waypoint(queue)
    assert (
        len(filtered_queue) == 1
    ), f"Queue should only contain 1 waypoint (takeoff), found {len(filtered_queue)}"
    print("Queue verified: dummy waypoint cleared, only takeoff waypoint present")

    # Step 5: Verify flight mode did NOT change
    current_mode = api_client.get_flight_mode()
    assert current_mode == initial_mode, (
        f"Flight mode should not change after prepare_takeoff. "
        f"Expected: {initial_mode}, Got: {current_mode}"
    )
    print(f"Flight mode unchanged: {current_mode}")

    # Step 6: Arm the drone (emulating pilot action)
    response = api_client.arm(True)
    assert response.status_code == 200, f"Arm command failed: {response.text}"
    print("Drone armed")

    # Step 7: Set to GUIDED mode (emulating pilot action via mission-planner)
    response = api_client.set_flight_mode_direct("GUIDED")
    assert response.status_code == 200, f"GUIDED mode command failed: {response.text}"
    print("Switched to GUIDED mode via mission-planner")

    # Wait and verify GUIDED mode is active
    wait_for_flight_mode(api_client, "GUIDED", timeout=10)
    print("GUIDED mode confirmed")

    # Step 8: Switch to AUTO mode (emulating pilot action)
    response = api_client.set_flight_mode_direct("AUTO")
    assert response.status_code == 200, f"AUTO mode command failed: {response.text}"
    print("Switched to AUTO mode - drone should now takeoff")

    # Step 9: Wait for drone to reach target altitude
    wait_for_altitude(
        api_client,
        target_altitude,
        timeout=120,
        tolerance=2.0,
    )
    print(f"Drone reached target altitude: {target_altitude}m")

    # Step 10: Verify altitude is correct
    status = api_client.get_status()
    assert (
        abs(status["altitude"] - target_altitude) <= 2.0
    ), f"Altitude mismatch: {status['altitude']}m != {target_altitude}m"

    # Step 11: Verify drone is hovering (stationary for 10 seconds)
    print("Verifying stable hover...")
    wait_for_stationary(
        api_client,
        duration=10.0,
        speed_threshold=0.5,
        vertical_speed_threshold=0.5,
        timeout=60.0,
    )
    print("Drone hovering stably at target altitude")

    # Final verification
    final_status = api_client.get_status()
    print(
        f"Final state - Altitude: {final_status['altitude']:.1f}m, "
        f"Groundspeed: {final_status['groundspeed']:.2f} m/s, "
        f"Vertical speed: {final_status['verticalspeed']:.2f} m/s"
    )
