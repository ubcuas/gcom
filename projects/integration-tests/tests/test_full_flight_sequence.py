"""Integration tests for complete flight sequences.

These tests verify end-to-end flight operations that take longer to execute
but provide validation of flight behavior with SITL.
"""

import pytest
from helpers import wait_for_altitude


@pytest.mark.slow
@pytest.mark.critical
def test_takeoff_and_rtl(api_client):
    """Test complete takeoff and RTL (return-to-launch) cycle.

    A simple flight sequence. It uses:
    - Takeoff command execution (automatically arms the drone as well) 
    - Altitude control and stabilization
    - RTL command execution
    - Autonomous return and landing
    - Auto-disarm on landing 

    Expected Timeline:
    - Arming + Takeoff to 25m: ~10-15 seconds
    - RTL return + descent: ~15-25 seconds
    - Total test duration: ~30-45 seconds (timeouts set with safety margins)

    Args:
        api_client: API client fixture
    """
    relative_altitude = 25.0  # meters - low enough for quick test, high enough to be meaningful

    # Step 1: Capture baseline altitude (MSL at ground level)
    initial_status = api_client.get_status()
    baseline_altitude = initial_status["altitude"]
    target_altitude = baseline_altitude + relative_altitude

    # Step 2: Send takeoff command (automatically arms the drone)
    response = api_client.takeoff(relative_altitude)
    assert response.status_code == 200, f"Takeoff command failed: {response.text}"

    # Step 3: Wait for drone to reach target altitude (baseline + 25m)
    # ArduPilot climbs at ~2.5 m/s, so 25m takes ~10s, we allow 60s timeout
    wait_for_altitude(
        api_client,
        target_altitude,
        timeout=60,
        tolerance=2.0,
    )

    # Step 4: Verify drone is at target altitude
    status_at_altitude = api_client.get_status()
    assert abs(status_at_altitude["altitude"] - target_altitude) <= 2.0, (
        f"Drone altitude {status_at_altitude['altitude']}m not within 2m of target {target_altitude}m"
    )

    # Step 5: Trigger RTL (Return-to-Launch)
    # This will make the drone return to home position and auto-land
    response = api_client.rtl()
    assert response.status_code == 200, f"RTL command failed: {response.text}"

    # Step 6: Wait for drone to return and land (back to baseline altitude)
    # RTL involves: return flight + descent + landing, allow 120s timeout
    wait_for_altitude(
        api_client,
        target_altitude=baseline_altitude,
        timeout=120,
        tolerance=2.0,
    )

    # Step 7: Verify drone has landed (back at baseline)
    final_status = api_client.get_status()
    assert abs(final_status["altitude"] - baseline_altitude) <= 2.0, (
        f"Drone should have landed at baseline {baseline_altitude}m, but altitude is {final_status['altitude']}m"
    )
