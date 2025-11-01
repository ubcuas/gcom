# API Endpoint Breakdown & Drone Control Model

## Core Control Philosophy

This system operates on **two distinct control modes**:

**1. IMMEDIATE COMMANDS** (Direct execution)
- `/arm`, `/takeoff`, `/land`, `/rtl`, `/flightmode`
- Execute immediately upon request
- Switch the drone into appropriate flight modes automatically

**2. MISSION QUEUE** (Autonomous waypoint navigation)
- `/queue`, `/insert`, `/clear`
- Waypoints are **uploaded to the autopilot but do NOT execute immediately**
- Drone must be in **AUTO mode** to follow the queue
- You control when to start via `/flightmode {"mode": "AUTO"}`

---

## Endpoint Breakdown

### **Queue Management** (No immediate drone movement)

#### **`POST /queue`** - Replace entire mission
- Clears existing waypoints and uploads new ones
- Drone does NOT immediately fly to them
- Must set flight mode to AUTO to begin execution
- Returns: `200 OK` or `400` on failure
- Location: `src_pymav/server/httpserver.py:55`, `src_pymav/server/operations/queue.py:23`

#### **`POST /insert`** - Insert waypoints before current position
- Inserts new waypoints ahead of current waypoint in queue
- Only affects drone if already in AUTO mode
- Returns: `200` on success, `400` on failure
- Location: `src_pymav/server/httpserver.py:102`

#### **`GET /queue`** - View remaining waypoints
- Returns: JSON array of waypoints from current position onward
- Location: `src_pymav/server/httpserver.py:37`
```json
[{
  "id": 1,
  "name": "wp1",
  "latitude": 49.26,
  "longitude": -123.25,
  "altitude": 50,
  "command": "WAYPOINT",
  "param1": 0,
  "param2": 0,
  "param3": 0,
  "param4": 0
}]
```

#### **`GET /clear`** - Empty the mission queue
- Clears all waypoints from autopilot
- Drone continues current behavior (doesn't stop mid-flight)
- Returns: `200` on success, `400` on failure
- Location: `src_pymav/server/httpserver.py:156`, `src_pymav/server/operations/queue.py:101`

---

### **Flight Control** (Immediate execution)

#### **`POST /takeoff {"altitude": 50}`** - Arm & takeoff
- **Immediate**: Arms motors → switches to GUIDED mode → takes off
- Waits for GPS lock, sets GUIDED mode, arms, sends takeoff command
- Returns: `200` on success, `400` on failure
- Location: `src_pymav/server/httpserver.py:171`, `src_pymav/server/operations/takeoff.py:5-33`

#### **`PUT /arm {"arm": 1 or 0}`** - Arm/disarm motors
- **Immediate**: Arms (1) or disarms (0) motors
- Returns: `200` if state confirmed, `418` if failed
- Location: `src_pymav/server/httpserver.py:191`, `src_pymav/server/operations/takeoff.py:36-57`

#### **`GET|POST /rtl [{"altitude": 50}]`** - Return to launch
- **Immediate**: Sets RTL_ALT parameter → switches to RTL mode
- Drone flies back to home position at specified altitude
- Default altitude: 50m if not specified
- Returns: `200` on success, `400` on failure
- Location: `src_pymav/server/httpserver.py:215`

#### **`GET /land`** - Land at current position
- **Immediate**: Switches to LOITER → sends LAND command
- Descends and lands where it is
- Returns: `200` on success, `400` on failure
- Location: `src_pymav/server/httpserver.py:242`, `src_pymav/server/operations/land.py:5-24`

#### **`POST /land {"latitude": X, "longitude": Y, "altitude": Z}`** - Land at location
- Uploads a 2-waypoint mission: approach point → land
- Drone navigates to coordinates then lands
- Altitude parameter is for approach altitude (defaults to 35m if not specified)
- Returns: `200` on success, `400` on failure
- Location: `src_pymav/server/httpserver.py:253-269`

#### **`PUT /flightmode {"mode": "AUTO"}`** - Change flight mode
- **Immediate**: Switches between modes (AUTO, GUIDED, LOITER, RTL, STABILIZE, etc.)
- **This is how you start mission execution**: set mode to "AUTO"
- Returns: `200` on mode change, `400` on invalid mode
- Available modes: All ArduPilot modes (33+ modes listed in `api_spec.yml:269`)
- Location: `src_pymav/server/httpserver.py:287`, `src_pymav/server/operations/change_modes.py:4-30`

#### **`POST /home {"latitude": X, "longitude": Y, "altitude": Z}`** - Set home position
- Sets the RTL return point
- All three parameters (lat/lon/alt) are required
- Returns: `200` on success, `400` if parameters missing or set failed
- Location: `src_pymav/server/httpserver.py:271`, `src_pymav/server/operations/queue.py:6`

---

### **Status & Info** (Read-only)

#### **`GET /status`** - Current telemetry
- Returns comprehensive drone state
- Location: `src_pymav/server/httpserver.py:165`, `src_pymav/server/operations/get_info.py:5`
```json
{
  "timestamp": 1633024800000,
  "current_wpn": 3,
  "latitude": 49.26,
  "longitude": -123.25,
  "altitude": 50,
  "roll": 0.5,
  "pitch": -1.2,
  "airspeed": 12,
  "groundspeed": 11.5,
  "heading": 180,
  "batteryvoltage": 12.6,
  "winddirection": 90,
  "windvelocity": 3.5
}
```

**Field Details:**
- `current_wpn`: Current waypoint number in the mission (0 if no mission)
- `latitude/longitude`: GPS coordinates in degrees
- `altitude`: Relative to sea level in meters
- `roll/pitch`: Attitude in degrees
- `airspeed`: Speed relative to air in m/s
- `groundspeed`: Speed relative to ground in m/s
- `heading`: Aircraft nose direction in degrees (0-360)
- `batteryvoltage`: Battery voltage in volts
- `winddirection/windvelocity`: Estimated wind in degrees and m/s

---

### **Competition Features**

#### **`POST /aeac_scan`** - Spiral scan pattern
- Generates waypoints in a spiral pattern for area scanning
- Required parameters:
  - `center_lat`: Center latitude
  - `center_lng`: Center longitude
  - `altitude`: Scan altitude
  - `target_area_radius`: Radius of scan area
- Automatically uploads mission to autopilot
- Returns: `200` if mission set, `400` on failure
- Location: `src_pymav/server/httpserver.py:303`, `src_pymav/server/features/aeac_scan.py`

#### **`POST /aeac_deliver`** - Water delivery operation
- Creates mission to descend, hover, and return to altitude
- Required parameters:
  - `current_alt`: Current altitude
  - `deliver_alt`: Altitude to descend to
  - `deliver_duration_secs`: Time to hover at delivery altitude
  - `curr_lat`: Current latitude
  - `curr_lon`: Current longitude
- Returns: `200` on success, `400` on failure
- Location: `src_pymav/server/httpserver.py:320`, `src_pymav/server/features/aeac_water_delivery.py`

---

## Control Hierarchy

```
┌─────────────────────────────────────────┐
│  Flight Mode (determines behavior)      │
└─────────────────────────────────────────┘
           │
           ├─► AUTO:      Follows /queue waypoints autonomously
           ├─► GUIDED:    Accepts individual position commands
           ├─► LOITER:    Holds position
           ├─► RTL:       Returns to home
           └─► STABILIZE: Manual control (no GPS)
```

## Typical Workflow

### 1. **Setup Phase**
```bash
# Set home position (for RTL)
POST /home {"latitude": 49.26, "longitude": -123.25, "altitude": 10}

# Upload waypoint mission (not executing yet)
POST /queue [
  {"id": 1, "name": "wp1", "latitude": 49.27, "longitude": -123.26, "altitude": 50},
  {"id": 2, "name": "wp2", "latitude": 49.28, "longitude": -123.27, "altitude": 50}
]
```

### 2. **Execution**
```bash
# Arm and takeoff (enters GUIDED mode at 50m)
POST /takeoff {"altitude": 50}

# Start autonomous waypoint navigation
PUT /flightmode {"mode": "AUTO"}
# ← Drone now flies through waypoints automatically
```

### 3. **Monitoring**
```bash
# Check current status
GET /status
# Returns: position, battery, current waypoint number, speeds, etc.

# View remaining waypoints
GET /queue
# Returns: waypoints from current position onward
```

### 4. **Interventions**

**Add urgent waypoints ahead:**
```bash
POST /insert [{"id": 99, "name": "urgent", "latitude": 49.265, ...}]
# Inserts before current waypoint
```

**Pause mission:**
```bash
PUT /flightmode {"mode": "LOITER"}
# Holds position, mission paused
```

**Resume mission:**
```bash
PUT /flightmode {"mode": "AUTO"}
# Continues from where it paused
```

**Abort and return home:**
```bash
GET /rtl
# or specify altitude: POST /rtl {"altitude": 75}
```

**Emergency land immediately:**
```bash
GET /land
# Lands at current position
```

---

## Key Insights

### Waypoints ≠ Immediate Movement
- `POST /queue` and `POST /insert` upload waypoints to the autopilot
- Waypoints sit idle until you switch to AUTO mode
- This allows you to prepare missions without immediate execution

### Two Control Systems
- **Mission Queue (AUTO mode)**: Autonomous navigation through uploaded waypoints
- **Direct Commands (GUIDED/RTL/LAND modes)**: Immediate execution of single commands

### Flight Mode is King
- The current flight mode determines which control system is active
- Switching modes is how you transition between autonomous and direct control
- Critical modes:
  - `AUTO`: Execute waypoint queue
  - `GUIDED`: Accept direct position commands (used by takeoff)
  - `LOITER`: Hold position (useful for pausing)
  - `RTL`: Return to home automatically

### Status Returns Everything
- Single endpoint provides: position, attitude, speed, battery, wind, current waypoint
- Poll this regularly (e.g., every 1-2 seconds) for monitoring
- Use `current_wpn` field to track progress through mission

### All Commands Return Success/Failure
- `200`: Command succeeded
- `400`: Command failed (check response body for reason)
- `418`: Arm/disarm specifically failed
- Always check return codes - MAVLink communication can fail

### Altitude Handling
- All altitudes in meters
- Altitude is relative to sea level (MSL) by default
- If altitude omitted in waypoint, uses previous waypoint's altitude
- For first waypoint with no altitude, uses current drone altitude

### Waypoint Command Types
- Default: `WAYPOINT` (fly through point)
- Other options: `LOITER_UNLIM`, `DO_CHANGE_SPEED`, `LAND`, etc.
- See `api_spec.yml:398` for command field details
- Parameters (param1-4) vary by command type

---

## Architecture Notes

### Communication Flow
```
HTTP Request → Flask Endpoint → pymavlink MAVLink Command → SITL/Drone
                                                    ↓
HTTP Response ← Flask ← MAVLink ACK ← SITL/Drone
```

### Synchronous Operations
- Most endpoints wait for MAVLink `COMMAND_ACK` or `MISSION_ACK` before returning
- Timeout: typically 3-5 seconds
- If ACK not received, operation reports failure

### Mission Upload Protocol
1. Clear existing mission (`MISSION_CLEAR_ALL`)
2. Send waypoint count (`MISSION_COUNT`)
3. Wait for autopilot to request each waypoint (`MISSION_REQUEST_INT`)
4. Send each waypoint as requested (`MISSION_ITEM_INT`)
5. Receive confirmation (`MISSION_ACK`)

See `src_pymav/server/operations/queue.py:23-81` for implementation.

---

## Error Handling

### Common Failure Scenarios

**Waypoint Upload Fails**
- Cause: No MAVLink connection, invalid coordinates, timeout
- Response: `400 "Error uploading mission"`
- Recovery: Check connection, retry upload

**Takeoff Fails**
- Cause: No GPS lock, already armed, invalid altitude
- Response: `400 "Takeoff unsuccessful"`
- Recovery: Check GPS status, ensure drone is disarmed first

**Mode Change Fails**
- Cause: Invalid mode name, autopilot restrictions
- Response: `400 "Unrecognized mode"`
- Recovery: Check mode spelling (must be uppercase), verify mode is available for your autopilot

**RTL Fails**
- Cause: No home position set, parameter set failure
- Response: `400 "Failed to RTL"`
- Recovery: Ensure home position is set via `POST /home`

---

## Reference Files

- **API Specification**: `api_spec.yml`
- **HTTP Server**: `src_pymav/server/httpserver.py`
- **Queue Operations**: `src_pymav/server/operations/queue.py`
- **Takeoff/Arm**: `src_pymav/server/operations/takeoff.py`
- **Landing**: `src_pymav/server/operations/land.py`
- **Mode Changes**: `src_pymav/server/operations/change_modes.py`
- **System Architecture**: `technical-documentation/pymavlink-system-architecture.md`
