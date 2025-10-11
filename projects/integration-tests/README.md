# GCOM Integration Tests

Full end-to-end integration tests for the GCOM system that verify communication flow through the entire stack: **web-backend → mission-planner → SITL**.

## Overview

These tests validate that the complete system works together correctly by:

1. Sending requests to the **web-backend** API (the entry point)
2. Web-backend forwards requests to **mission-planner**
3. Mission-planner communicates with **SITL** via MAVLink
4. Responses flow back through the stack
5. Tests verify the results from web-backend

This ensures all integration points are tested in a realistic scenario.

## Architecture

```
┌─────────────────────────────────────────────────┐
│  Integration Tests (pytest)                     │
│  - Makes HTTP requests to web-backend           │
│  - Verifies responses and state                 │
└────────────────────┬────────────────────────────┘
                     │ HTTP (localhost:8000)
                     ▼
┌─────────────────────────────────────────────────┐
│  Web-Backend (Django)                           │
│  - Receives test requests                       │
│  - Forwards to mission-planner                  │
└────────────────────┬────────────────────────────┘
                     │ HTTP (localhost:9000)
                     ▼
┌─────────────────────────────────────────────────┐
│  Mission-Planner (Flask + pymavlink)            │
│  - Converts to MAVLink commands                 │
│  - Communicates with SITL                       │
└────────────────────┬────────────────────────────┘
                     │ MAVLink (UDP 14551)
                     ▼
┌─────────────────────────────────────────────────┐
│  Mavproxy → SITL (Docker)                       │
│  - Simulated ArduPilot firmware                 │
└─────────────────────────────────────────────────┘
```

## Prerequisites

Before running integration tests, you must have the following services running:

### 1. SITL (Simulated Drone)

```bash
docker run --rm -d -p 5760:5760 --name acom-sitl ubcuas/uasitl:copter-4.5.0
```

### 2. Mavproxy (MAVLink Message Forwarder)

**Linux/Mac:**
```bash
mavproxy.py --master=tcp:127.0.0.1:5760 --out=udp:127.0.0.1:14551
```

**Windows:**
```bash
mavproxy --master=tcp:127.0.0.1:5760 --out=udp:127.0.0.1:14551
```

### 3. Mission-Planner Server

```bash
cd ../mission-planner
poetry run python src/main.py
```

The server should start on `http://localhost:9000`

### 4. Web-Backend Server

```bash
cd ../web-backend/src
poetry run python server.py
```

The server should start on `http://localhost:8000`

## Setup

### 1. Install Dependencies

```bash
cd projects/integration-tests
pip install -r requirements.txt
```

### 2. Configure Environment (Optional)

Copy the example environment file and customize if needed:

```bash
cp .env.example .env
```

Edit `.env` if your services are running on different ports:

```env
WEB_BACKEND_URL=http://localhost:8000
MISSION_PLANNER_URL=http://localhost:9000
TEST_TIMEOUT=120
```

## Running Tests

### Run All Tests

```bash
pytest -v
```

### Run Specific Test File

```bash
pytest tests/test_status.py -v
pytest tests/test_waypoint_flow.py -v
```

### Run Specific Test

```bash
pytest tests/test_status.py::test_get_status_via_web_backend -v
```

### Run Only Critical Tests

```bash
pytest -m critical -v
```

### Run with More Detail

```bash
pytest -vv -s
```

Options:
- `-v` / `-vv`: Verbose output
- `-s`: Show print statements
- `-m critical`: Run only tests marked as critical
- `--tb=short`: Short traceback format (default in pytest.ini)

## Test Structure

### Test Files

- **`tests/test_status.py`**: Tests for drone status/telemetry endpoints
  - Verifies status data flows through full stack
  - Checks data consistency between services
  - Validates telemetry fields

- **`tests/test_waypoint_flow.py`**: Tests for waypoint management
  - Upload single/multiple waypoints
  - Clear waypoint queue
  - Verify persistence and consistency

### Helper Modules

- **`helpers/api_client.py`**: HTTP client wrapper for clean API calls
- **`helpers/waiters.py`**: Polling utilities for async drone operations
- **`helpers/assertions.py`**: Custom assertion helpers for drone-specific validations
- **`conftest.py`**: Pytest fixtures and test configuration

## Test Categories

Tests are marked with categories for selective running:

- **`@pytest.mark.critical`**: Core functionality that must always work
- **`@pytest.mark.slow`**: Tests that take >10 seconds to run

## Understanding Test Flow

### Example: `test_upload_single_waypoint_via_web_backend`

1. **Setup (automatic)**: `reset_drone_state` fixture clears waypoint queue
2. **Test uploads waypoint**: `POST http://localhost:8000/api/drone/queue`
3. **Web-backend receives request**: Forwards to mission-planner via `DroneApiClient`
4. **Mission-planner processes**: Converts to MAVLink `MISSION_ITEM_INT` messages
5. **SITL receives command**: Stores waypoint in flight plan
6. **Test verifies**: `GET http://localhost:8000/api/drone/queue` returns the waypoint
7. **Teardown (automatic)**: `reset_drone_state` clears queue for next test

## Troubleshooting

### Test Exits Immediately: "Web-backend is not responding"

**Cause**: Web-backend server is not running or not reachable.

**Solution**:
1. Start web-backend: `cd ../web-backend/src && poetry run python server.py`
2. Verify it's running: `curl http://localhost:8000/api/drone/status`

### Test Exits Immediately: "Mission-planner is not responding"

**Cause**: Mission-planner server is not running or not reachable.

**Solution**:
1. Start mission-planner: `cd ../mission-planner && poetry run python src/main.py`
2. Verify it's running: `curl http://localhost:9000/status`

### Test Fails: "Waypoint count mismatch" or "Status missing field"

**Cause**: Services are running but SITL/Mavproxy connection is broken.

**Solution**:
1. Check SITL is running: `docker ps | grep acom-sitl`
2. Check Mavproxy is running and connected
3. Restart mission-planner to re-establish MAVLink connection

### Test Times Out

**Cause**: Operation is taking too long (default timeout: 120s).

**Solution**:
1. Check if SITL is overloaded or stuck
2. Restart SITL: `docker restart acom-sitl`
3. Increase timeout in `.env`: `TEST_TIMEOUT=180`

### Tests Fail Intermittently

**Cause**: Race conditions or state not properly reset between tests.

**Solution**:
1. Run tests sequentially: `pytest -v` (default)
2. Check `conftest.py` `reset_drone_state` fixture is working
3. Add delays in test if needed

## Writing New Tests

### 1. Use Fixtures for Common Setup

```python
def test_my_feature(api_client, sample_waypoint):
    # api_client and sample_waypoint are automatically provided
    response = api_client.post_queue([sample_waypoint])
    assert response.status_code == 200
```

### 2. Test Through Web-Backend

Always hit web-backend, not mission-planner directly:

```python
# ✅ Good: Tests full integration
status = api_client.get_status()  # Hits web-backend

# ❌ Bad: Bypasses web-backend
status = api_client.get_mission_planner_status()  # Only for verification
```

### 3. Use Helper Functions

```python
from helpers import assert_waypoint_match, wait_for_altitude

# Clean assertions
assert_waypoint_match(actual, expected)

# Async operations
wait_for_altitude(api_client, target_altitude=50, timeout=60)
```

### 4. Mark Tests Appropriately

```python
@pytest.mark.critical
def test_critical_path():
    pass

@pytest.mark.slow
def test_long_operation():
    pass
```

## CI/CD Integration (Future)

For automated testing in GitHub Actions, you'll need to orchestrate services using Docker Compose. See future phases for automation setup.

## Contributing

When adding new tests:

1. Follow existing test structure and naming conventions
2. Use descriptive test names that explain what is being tested
3. Add docstrings explaining the test flow
4. Use fixtures for common setup
5. Test through web-backend (full integration)
6. Add appropriate test markers (`@pytest.mark.critical`, etc.)
7. Ensure tests clean up after themselves (or rely on `reset_drone_state`)

## Current Test Coverage

**Status Tests (4 tests):**
- ✅ Get status via web-backend
- ✅ Status contains telemetry data
- ✅ Status updates over time
- ✅ Status consistency between services

**Waypoint Tests (7 tests):**
- ✅ Upload single waypoint
- ✅ Upload multiple waypoints
- ✅ Clear waypoint queue
- ✅ Overwrite waypoint queue
- ✅ Queue persists across requests
- ✅ Empty queue returns empty list
- ✅ Queue consistency between services

**Total: 11 integration tests**

## Contact

For questions or issues with integration tests, refer to the main project documentation or contact the development team.
