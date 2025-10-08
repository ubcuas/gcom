# Mission Planner (pymavlink) System Architecture

## System Overview

The pymavlink-based mission planner is a **cross-platform HTTP API server** that bridges web applications with drone autopilots using the MAVLink protocol. It runs independently without requiring the Mission Planner desktop application.

## Architecture Components

```
┌─────────────────┐
│  SITL (Docker)  │  Port 5760 (TCP)
│  ArduPilot/PX4  │
└────────┬────────┘
         │
         ▼
    ┌─────────┐
    │ Mavproxy│  Forwards MAVLink messages
    └────┬────┘
         │
         ├──────────────────────────┐
         │                          │
         ▼                          ▼
    Port 14550 (UDP)           Port 14551 (UDP)
    Mission Planner GUI        pymavlink script
    (Optional viewing)         (This project)
                                    │
                                    ▼
                            ┌───────────────────┐
                            │  HTTP Server      │
                            │  Port 9000        │
                            │  Flask + SocketIO │
                            └───────────────────┘
                                    │
                                    ▼
                            ┌───────────────────┐
                            │  Web Backend/     │
                            │  Client Apps      │
                            └───────────────────┘
```

## Ports & Endpoints

### Infrastructure Ports

| Port  | Protocol | Purpose | Component |
|-------|----------|---------|-----------|
| **5760** | TCP | SITL autopilot output | Docker container |
| **14550** | UDP | Mission Planner GUI (optional) | Mavproxy output |
| **14551** | UDP | pymavlink script input | Mavproxy output |
| **9000** | HTTP/WS | API server | Flask application |
| **1323** | WebSocket | Status updates (optional, disabled by default) | External status listener |

### HTTP API Endpoints

**Health & Status:**
- `GET /` - Server health check
- `GET /status` - Current drone telemetry (lat/lon/alt, attitude, speeds, battery, wind, current waypoint)

**Mission Queue Management:**
- `GET /queue` - Get remaining waypoints
- `POST /queue` - Replace entire mission
- `POST /insert` - Insert waypoints before current position
- `GET /clear` - Clear mission

**Flight Control:**
- `POST /takeoff` - Takeoff to altitude (requires `{"altitude": <meters>}`)
- `PUT /arm` - Arm/disarm motors (requires `{"arm": 1 or 0}`)
- `GET|POST /rtl` - Return to launch (optional altitude param)
- `GET /land` - Land immediately at current position
- `POST /land` - Land at specific coordinates
- `POST /home` - Set home position
- `PUT /flightmode` - Change flight mode (GUIDED, AUTO, LOITER, RTL, etc.)

**Competition Features:**
- `POST /aeac_scan` - Generate spiral scan pattern
- `POST /aeac_deliver` - Water delivery operation

## Getting Up and Running

### 1. Prerequisites
```bash
# Install Docker (for SITL)
# Install Mavproxy
pip install mavproxy

# Install project dependencies
cd projects/mission-planner
poetry install --no-root
```

### 2. Start SITL (Docker)
```bash
# Pull the image (choose plane or copter, x86 or ARM)
docker pull ubcuas/uasitl:copter-4.5.0  # example version

# Run SITL container
docker run --rm -d -p 5760:5760 --name acom-sitl ubcuas/uasitl:copter-4.5.0
```

**What this does:** Starts a simulated autopilot that outputs MAVLink telemetry on TCP port 5760.

### 3. Start Mavproxy (Message Forwarder)

**Linux:**
```bash
mavproxy.py --master=tcp:127.0.0.1:5760 \
  --out=udp:127.0.0.1:14550 \
  --out=udp:127.0.0.1:14551
```

**Windows:**
```bash
mavproxy --master=tcp:127.0.0.1:5760 \
  --out=udp:127.0.0.1:14550 \
  --out=udp:127.0.0.1:14551
```

**What this does:**
- Connects to SITL via TCP:5760
- Forwards MAVLink messages to two UDP endpoints:
  - `14550`: For Mission Planner GUI (optional visualization)
  - `14551`: For this pymavlink script

### 4. Start the pymavlink Server
```bash
poetry run python src_pymav/main.py
```

**What this does:**
1. Connects to MAVLink stream at `udpin:localhost:14551` (configurable via `--mavlink-conn`)
2. Waits for heartbeat from system ID 1
3. Starts Flask HTTP server on `0.0.0.0:9000`

### 5. Optional: Connect Mission Planner GUI
- Open Mission Planner application
- Set connection to `UDP` port `14550`
- Connect to visualize the drone

## Command-Line Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--dev` | Production | Run in development mode |
| `--port` | 9000 | HTTP server port |
| `--socket-port` | 9001 | Socket.IO port (not actively used) |
| `--status-host` | localhost | Status WebSocket host |
| `--status-port` | 1323 | Status WebSocket port |
| `--disable-status` | false | Disable status WebSocket |
| `--mavlink-conn` | `udpin:localhost:14551` | MAVLink connection string |

## Core Flow

### System Initialization (`src_pymav/main.py:54-58`)
1. **Connect to MAVLink:** `connect_to_sysid('udpin:localhost:14551', 1)`
   - Establishes UDP connection
   - Waits for heartbeat (3s timeout)
   - Confirms system ID matches target (1)

2. **Create HTTP Server:** `HTTP_Server(mav_connection)`
   - Stores MAVLink connection
   - Sets up Flask routes

3. **Start Server Thread:** Runs Flask on `0.0.0.0:9000`

### Example: Takeoff Sequence
When you call `POST /takeoff {"altitude": 50}`:

1. **Wait for GPS Lock:** `wait_until_position_aiding()` - Ensures EKF has position
2. **Detect Autopilot:** Determines ArduPilot vs PX4
3. **Set GUIDED Mode:** Sends `MAV_CMD_DO_SET_MODE` command
4. **Arm Motors:** `arm_disarm(True)` - Sends `MAV_CMD_COMPONENT_ARM_DISARM`
5. **Send Takeoff Command:** `MAV_CMD_NAV_TAKEOFF` with altitude parameter
6. **Wait for ACK:** Receives `COMMAND_ACK` message confirming execution

All communication happens via the `mav_connection` object (pymavlink's `mavfile` instance).

### Example: Mission Upload
When you call `POST /queue [waypoint_array]`:

1. **Parse Waypoints:** Converts JSON to `Waypoint` objects
2. **Build Mission:** Creates `WaypointQueue`
3. **Upload via MAVLink:** `new_mission()` function:
   - Sends `MISSION_COUNT` message
   - Waits for `MISSION_REQUEST_INT` from autopilot
   - Sends each waypoint as `MISSION_ITEM_INT`
   - Receives `MISSION_ACK` confirmation

## Key Differences from Legacy System

| Aspect | **pymavlink (New)** | Legacy (Deprecated) |
|--------|-------------------|---------------------|
| Platform | Cross-platform | Windows only |
| Dependencies | pymavlink only | Mission Planner desktop app |
| MAVLink Access | Direct via socket | Mission Planner scripting API |
| Connection | UDP/TCP network | IronPython scripting |
| Mission Planner | Optional (visualization) | Required (runtime) |

## Summary

The pymavlink system is a **standalone HTTP API gateway** that:
- Receives MAVLink telemetry from SITL/drone via UDP port 14551
- Exposes REST endpoints on HTTP port 9000
- Uses pymavlink library for direct MAVLink protocol communication
- Supports ArduPilot and PX4 autopilots
- Requires Mavproxy as a message forwarder between SITL and the application
