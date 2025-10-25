# Waypoint System Architecture

## Overview

The GCOM waypoint system consists of two independent subsystems that serve different purposes in mission planning and drone control. Understanding the distinction between these systems is critical for safe operation and proper system usage.

## System Components

### High-Level Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                       Web Frontend                            │
│                      (React + Redux)                          │
└───────────────┬──────────────────────┬───────────────────────┘
                │                      │
                │ HTTP REST            │ HTTP REST
                │                      │
        ┌───────▼────────┐     ┌──────▼─────────┐
        │ /api/waypoint/ │     │ /api/drone/*   │
        │   (Database)   │     │    (Proxy)     │
        └───────┬────────┘     └──────┬─────────┘
                │                     │
                ▼                     ▼
        ┌───────────────┐     ┌──────────────────┐
        │  PostgreSQL   │     │ Mission Planner  │
        │   Database    │     │  Flask Server    │
        │               │     │  (localhost:9000)│
        └───────────────┘     └──────┬───────────┘
                                     │ UDP
                                     ▼
                              ┌──────────────┐
                              │ Drone/SITL   │
                              │ (MAVLink)    │
                              └──────────────┘
```

---

## The Two Waypoint Systems

### System 1: Database Waypoint Storage (`/api/waypoint/`)

**Purpose**: Long-term storage for mission planning library

**Location**: `projects/web-backend/src/nav/`

**Technology Stack**:
- Django REST Framework ModelViewSet
- PostgreSQL database
- Django ORM

**Key Characteristics**:
- Persistent storage (survives server restarts)
- Full CRUD operations (Create, Read, Update, Delete)
- Organized into Routes containing ordered Waypoints
- No connection to live drone operations
- Used for pre-flight planning and scenario preparation

---

### System 2: Live Drone Queue (`/api/drone/queue`)

**Purpose**: Real-time drone mission control and execution

**Location**:
- Web-backend proxy: `projects/web-backend/src/drone/`
- Mission-planner: `projects/mission-planner/src/server/gcomhandler.py`

**Technology Stack**:
- Django view (proxy layer)
- Flask REST API (mission-planner)
- Shared memory state (mission-planner SharedObject)
- UDP protocol to drone

**Key Characteristics**:
- Volatile (mission lost on mission-planner restart)
- Directly controls physical/simulated drone
- Single active mission at a time
- Real-time execution status
- Cannot be edited via standard CRUD (use specialized endpoints: insert, clear, diversion)

---

## Data Models

### Database Waypoint Model

**File**: `projects/web-backend/src/nav/models.py`

```python
class Waypoint(models.Model):
    """Base waypoint with geographic data"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=32)
    latitude = models.FloatField()
    longitude = models.FloatField()
    altitude = models.FloatField()

    # MAVLink parameters
    class PassOptions(models.IntegerChoices):
        PASSTHROUGH = 0, "Passthrough"
        ORBIT_CWISE = 1, "Orbit Clockwise"
        ORBIT_CCWISE = -1, "Orbit Counter-Clockwise"

    radius = models.FloatField(default=5)
    pass_radius = models.FloatField(default=5)
    pass_option = models.IntegerField(default=PassOptions.PASSTHROUGH)


class OrderedWaypoint(Waypoint):
    """Waypoint within a route, with ordering"""
    order = models.IntegerField()
    route = models.ForeignKey(Route, on_delete=models.CASCADE)


class Route(models.Model):
    """Collection of ordered waypoints forming a mission"""
    name = models.CharField(max_length=32)
    # waypoints = reverse relation from OrderedWaypoint
```

### Live Queue Waypoint Format

**File**: `projects/mission-planner/src/server/gcomhandler.py` (lines 104-136)

```python
# Format expected by mission-planner
{
    'id': int | str,           # Waypoint identifier
    'name': str,               # Waypoint name
    'latitude': float,         # Decimal degrees
    'longitude': float,        # Decimal degrees
    'altitude': float,         # Meters (AGL or ASL based on config)
    'command': str,            # MAVLink command type
    'param1': float,           # Command-specific parameter 1
    'param2': float,           # Command-specific parameter 2
    'param3': float,           # Command-specific parameter 3
    'param4': float            # Command-specific parameter 4
}
```

**Supported Commands**:
- `WAYPOINT` - Navigate to position
- `TAKEOFF` - Takeoff command
- `LAND` - Land at position
- `LOITER_UNLIM` - Loiter indefinitely
- `LOITER_TIME` - Loiter for specified time
- `LOITER_TURNS` - Loiter for specified turns
- Custom commands per MAVLink specification

---

## API Endpoints

### Database Waypoint Endpoints

**Base URL**: `http://web-backend/api/`

#### Waypoint Operations

```
GET    /api/waypoint/
POST   /api/waypoint/
GET    /api/waypoint/{id}/
PUT    /api/waypoint/{id}/
PATCH  /api/waypoint/{id}/
DELETE /api/waypoint/{id}/
```

**Example - Create Waypoint**:
```bash
POST /api/waypoint/
Content-Type: application/json

{
  "name": "Launch Point",
  "latitude": 49.2606,
  "longitude": -123.2460,
  "altitude": 100.0,
  "radius": 5.0,
  "pass_radius": 5.0,
  "pass_option": 0,
  "order": 0,
  "route": 1
}
```

#### Route Operations

```
GET    /api/route/
POST   /api/route/
GET    /api/route/{id}/
PUT    /api/route/{id}/
DELETE /api/route/{id}/
POST   /api/route/{id}/reorder-waypoints/
```

**Example - Create Route**:
```bash
POST /api/route/
Content-Type: application/json

{
  "name": "Mission Alpha"
}
```

**Example - Reorder Waypoints**:
```bash
POST /api/route/1/reorder-waypoints/
Content-Type: application/json

[3, 1, 2, 4]  # Array of waypoint IDs in new order
```

---

### Live Drone Queue Endpoints

**Base URL**: `http://web-backend/api/drone/`

#### Queue Operations

```
GET  /api/drone/queue       # Get current mission from drone
POST /api/drone/queue       # Upload new mission to drone
GET  /api/drone/clear       # Clear drone mission
POST /api/drone/insert      # Insert waypoints into current mission
POST /api/drone/diversion   # Execute geofence diversion
```

**Example - Upload Mission**:
```bash
POST /api/drone/queue
Content-Type: application/json

[
  {
    "id": 1,
    "name": "Takeoff",
    "latitude": 49.2606,
    "longitude": -123.2460,
    "altitude": 50.0,
    "command": "TAKEOFF",
    "param1": 0,
    "param2": 0,
    "param3": 0,
    "param4": 0
  },
  {
    "id": 2,
    "name": "Waypoint 1",
    "latitude": 49.2650,
    "longitude": -123.2500,
    "altitude": 75.0,
    "command": "WAYPOINT",
    "param1": 0,
    "param2": 0,
    "param3": 0,
    "param4": 0
  }
]
```

**Example - Get Current Queue**:
```bash
GET /api/drone/queue

# Response: Current waypoints from drone (excludes already-passed waypoints)
[
  {
    "id": 2,
    "name": "Waypoint 1",
    "latitude": 49.2650,
    "longitude": -123.2500,
    "altitude": 75.0,
    "command": "WAYPOINT",
    ...
  }
]
```

**Example - Insert Waypoints**:
```bash
POST /api/drone/insert
Content-Type: application/json

[
  {
    "id": 99,
    "name": "Emergency Landing",
    "latitude": 49.2620,
    "longitude": -123.2470,
    "altitude": 0.0,
    "command": "LAND",
    "param1": 0,
    "param2": 0,
    "param3": 0,
    "param4": 0
  }
]

# Waypoints inserted at current position in mission queue
```

---

## Data Flow

### Scenario 1: Planning a Mission (Database Storage)

```
┌──────────┐
│ Operator │
└─────┬────┘
      │ 1. Create route
      ▼
┌────────────────┐
│   Frontend     │
│  POST /route/  │
└───────┬────────┘
        │ 2. HTTP Request
        ▼
┌────────────────┐
│  Web Backend   │
│ RoutesViewset  │
└───────┬────────┘
        │ 3. ORM Save
        ▼
┌────────────────┐
│   PostgreSQL   │
│  Route stored  │
└────────────────┘

[Waypoints added to route via POST /waypoint/]
[Route persists in database]
[No drone interaction]
```

### Scenario 2: Executing a Mission (Live Drone Queue)

```
┌──────────┐
│ Operator │
└─────┬────┘
      │ 1. Select route from database
      ▼
┌──────────────────┐
│    Frontend      │
│ GET /route/{id}/ │
└────────┬─────────┘
         │ 2. Retrieve waypoints
         ▼
┌──────────────────┐
│   Frontend       │
│ Review waypoints │
│ (queuedWaypoints)│
└────────┬─────────┘
         │ 3. Click "Upload to Drone"
         ▼
┌──────────────────────┐
│      Frontend        │
│ POST /drone/queue    │
└────────┬─────────────┘
         │ 4. HTTP to web-backend
         ▼
┌──────────────────────┐
│    Web Backend       │
│  drone/views.py      │
│  post_queue()        │
└────────┬─────────────┘
         │ 5. Proxy to mission-planner
         │ POST localhost:9000/queue
         ▼
┌──────────────────────┐
│  Mission Planner     │
│  gcomhandler.py      │
│  /queue endpoint     │
└────────┬─────────────┘
         │ 6. SharedObject.gcom_newmission_set()
         ▼
┌──────────────────────┐
│  Mission Planner     │
│  SharedObject        │
│  (in-memory state)   │
└────────┬─────────────┘
         │ 7. MPS_Server checks state
         ▼
┌──────────────────────┐
│  Mission Planner     │
│  mps_server.py       │
│  check_shared_object()│
└────────┬─────────────┘
         │ 8. Send "NEW_MISSION" command
         │ UDP to drone client
         ▼
┌──────────────────────┐
│   Drone Client       │
│   client.py          │
│   (Mission Planner)  │
└────────┬─────────────┘
         │ 9. upload_mission()
         ▼
┌──────────────────────┐
│   MAVLink/Drone      │
│   Mission uploaded   │
└──────────────────────┘
```

### Scenario 3: Monitoring Active Mission

```
┌──────────┐
│ Frontend │
└─────┬────┘
      │ Periodic polling
      ▼
GET /drone/queue
      │
      ▼
┌──────────────────┐
│  Web Backend     │
│  drone/views.py  │
└────────┬─────────┘
         │ GET localhost:9000/queue
         ▼
┌──────────────────┐
│ Mission Planner  │
│ gcomhandler.py   │
└────────┬─────────┘
         │ Trigger queue update
         │ SharedObject.gcom_currentmission_trigger_update()
         ▼
┌──────────────────┐
│ MPS_Server       │
│ mps_server.py    │
└────────┬─────────┘
         │ Send "QUEUE_GET" command
         ▼
┌──────────────────┐
│  Drone Client    │
│  client.py       │
└────────┬─────────┘
         │ Read mission from MAVLink
         │ getWP() for each waypoint
         ▼
┌──────────────────┐
│ Mission Planner  │
│ Receives QI msg  │
│ (Queue Info)     │
└────────┬─────────┘
         │ Parse waypoints
         │ SharedObject.mps_currentmission_updatequeue()
         ▼
┌──────────────────┐
│ Web Backend      │
│ Returns JSON     │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   Frontend       │
│ Display mission  │
└──────────────────┘
```

---

## Frontend Integration

### Redux State Management

The frontend maintains two distinct waypoint states:

**File**: `projects/web-frontend/src/store/slices/appSlice.ts`

```typescript
// Temporary working queue (pending upload)
queuedWaypoints: Waypoint[]
```

**File**: `projects/web-frontend/src/store/slices/dataSlice.ts`

```typescript
// Live drone mission or loaded database route (for display)
route: {
  id: number,
  waypoints: Waypoint[]
}
```

### Key Functions

**File**: `projects/web-frontend/src/api/endpoints.ts`

```typescript
// Upload waypoints to drone
export const postWaypointsToDrone = async (waypoints: Waypoint[]) => {
    return await api.post("/drone/queue", waypoints);
};

// Get current drone queue
export const getGCOM = async (): Promise<Waypoint[]> => {
    return (await api.get("/drone/queue")) as Waypoint[];
};

// Load saved route from database
export const getRoute = async (): Promise<Waypoint[]> => {
    return (await api.get("/route")) as Waypoint[];
};
```

### Usage Patterns

**Loading Database Route** (`DroneStatus/MPSControlSection.tsx:88-91`):
```typescript
getRoute().then((response) => {
    manualUpdateMPSQueue(response);  // Updates display only
});
```

**Uploading Mission to Drone** (`WaypointStatusCard.tsx:94`):
```typescript
await postWaypointsToDrone(waypointQueue);
if (autoClearWaypoints) {
    dispatch(clearQueuedWaypoints());
}
```

---

## Use Cases and Workflows

### Use Case 1: Pre-Flight Planning

**Objective**: Create and save reusable missions

**Steps**:
1. Operator uses frontend map to place waypoints
2. Frontend sends `POST /api/waypoint/` for each waypoint
3. Waypoints saved to database with route association
4. Can create multiple routes for different scenarios
5. Routes persist indefinitely in database

**System Used**: Database Storage (`/api/waypoint/`)

**Result**: Library of missions ready for execution

---

### Use Case 2: Mission Execution

**Objective**: Fly a planned mission

**Steps**:
1. Operator selects route from database
2. Frontend sends `GET /api/route/{id}/`
3. Waypoints loaded into `queuedWaypoints` state
4. Operator reviews mission on map
5. Operator clicks "Upload to Drone"
6. Frontend sends `POST /api/drone/queue` with waypoints
7. Mission uploaded to drone via mission-planner
8. Drone begins executing waypoints

**Systems Used**:
- Database Storage (retrieval)
- Live Queue (execution)

**Result**: Drone flying planned mission

---

### Use Case 3: In-Flight Mission Modification

**Objective**: Insert waypoints during active flight

**Steps**:
1. Drone executing mission
2. Operator identifies need for additional waypoint
3. Frontend creates new waypoint
4. Frontend sends `POST /api/drone/insert` with new waypoint
5. Mission-planner inserts waypoint at current position
6. Drone mission updated without interruption

**System Used**: Live Queue (`/api/drone/insert`)

**Result**: Modified mission without flight abort

---

### Use Case 4: Geofence Violation Response

**Objective**: Automatically divert around exclusion zone

**Steps**:
1. Geofence violation detected
2. Frontend sends `POST /api/drone/diversion` with:
   - Exclusion zone waypoints
   - Rejoin target waypoint
3. Mission-planner calculates diversion path
4. New mission uploaded to drone
5. Drone flies around exclusion zone

**System Used**: Live Queue (`/api/drone/diversion`)

**Result**: Safe autonomous diversion

---

## Critical Distinctions

### Independence of Systems

**NO AUTOMATIC SYNCHRONIZATION EXISTS**

| Aspect | Database Storage | Live Drone Queue |
|--------|------------------|------------------|
| **Trigger** | Manual CRUD operations | Manual upload command |
| **Persistence** | Permanent (PostgreSQL) | Volatile (in-memory) |
| **Affect on Drone** | None | Immediate |
| **Primary Use** | Planning & library | Execution & control |
| **Data Source** | User input | Drone telemetry |
| **Editing** | Full CRUD | Specialized commands only |

### Why No Automatic Sync?

1. **Safety**: Prevents accidental drone control during planning
2. **Intentionality**: Requires explicit operator command to affect drone
3. **Flexibility**: Can plan multiple scenarios without affecting live operations
4. **Compliance**: Meets UAV regulations requiring positive control
5. **Isolation**: Database issues don't crash drone operations

---

## Web-Backend Proxy Pattern

### Why Proxy Through Web-Backend?

The frontend does not communicate directly with mission-planner. All requests go through web-backend.

**Architecture**:
```
Frontend → Web-Backend → Mission-Planner → Drone
   (HTTP)      (HTTP)         (UDP)
```

**Reasons**:

1. **Single API Surface**: Frontend only needs to know web-backend URL
2. **Authentication**: Django middleware can enforce auth/permissions
3. **Request Validation**: Django validates data before forwarding
4. **Logging/Audit**: Central point for tracking all drone commands
5. **Error Handling**: Unified error response format
6. **Service Abstraction**: Mission-planner can be moved/scaled without frontend changes

**Implementation** (`projects/web-backend/src/drone/mps_api.py`):
```python
class DroneApiClient:
    _mission_planner_api_url = "http://localhost:9000"

    @staticmethod
    def _fetch_from_mission_planner(endpoint, method="GET", data=None):
        url = f"{DroneApiClient._mission_planner_api_url}/{endpoint}"
        headers = {"Content-Type": "application/json"}
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, headers=headers, data=json.dumps(data))
        return response
```

---

## Best Practices

### For Operators

1. **Always review missions before upload**
   - Load route from database into working queue
   - Verify on map
   - Then explicitly upload to drone

2. **Save tested missions to database**
   - After successful flight, save waypoints as route
   - Reuse proven missions

3. **Use descriptive naming**
   - Route names: "Survey_North_Field_v2"
   - Waypoint names: "Launch_Point", "Photo_Target_1"

4. **Clear queue between missions**
   - Use `GET /api/drone/clear` before uploading new mission
   - Prevents waypoint contamination

### For Developers

1. **Never automatically upload to drone**
   - Database saves should never trigger drone commands
   - Always require explicit user action

2. **Validate before proxying**
   - Check waypoint format in web-backend before forwarding
   - Return clear error messages

3. **Handle mission-planner failures gracefully**
   - Mission-planner may be unreachable
   - Return 503 Service Unavailable with clear message

4. **Log all drone control commands**
   - Audit trail for post-flight analysis
   - Critical for incident investigation

5. **Separate concerns**
   - Database code in `nav/` module
   - Drone control code in `drone/` module
   - No cross-imports

---

## Error Handling

### Database Endpoint Errors

**Validation Errors**:
```json
{
  "latitude": ["This field is required."],
  "altitude": ["Ensure this value is greater than 0."]
}
```

**Not Found**:
```json
{
  "detail": "Not found."
}
```

### Drone Queue Endpoint Errors

**Mission-Planner Unreachable**:
```
Status: 500 Internal Server Error
Message: "Failed to connect to mission-planner"
```

**Invalid Mission Format**:
```
Status: 400 Bad Request
Message: "Invalid input"
```

**Drone Not Ready**:
```
Status: 400 Bad Request
Message: "Drone not armed/ready for mission"
```

---

## Testing Considerations

### Unit Testing Database Endpoints

```python
# Test waypoint creation
def test_create_waypoint(self):
    data = {
        'name': 'Test WP',
        'latitude': 49.0,
        'longitude': -123.0,
        'altitude': 100.0,
        'route': self.route.id
    }
    response = self.client.post('/api/waypoint/', data)
    self.assertEqual(response.status_code, 201)
```

### Integration Testing Drone Endpoints

```python
# Test mission upload (requires mission-planner running)
def test_upload_mission(self):
    waypoints = [
        {
            'id': 1,
            'name': 'WP1',
            'latitude': 49.0,
            'longitude': -123.0,
            'altitude': 50.0,
            'command': 'WAYPOINT',
            'param1': 0, 'param2': 0, 'param3': 0, 'param4': 0
        }
    ]
    response = self.client.post('/api/drone/queue',
                                 json.dumps(waypoints),
                                 content_type='application/json')
    self.assertEqual(response.status_code, 200)
```

### Mocking Mission-Planner

For tests that don't need real mission-planner:

```python
from unittest.mock import patch

@patch('drone.mps_api.DroneApiClient.post_queue')
def test_queue_proxy(self, mock_post):
    mock_post.return_value = Mock(status_code=200)
    response = self.client.post('/api/drone/queue', data)
    self.assertTrue(mock_post.called)
```

---

## Security Considerations

### Database Endpoints

- Implement Django authentication/permissions
- Validate user can only access their own routes
- Sanitize waypoint names to prevent SQL injection
- Rate limit creation to prevent DoS

### Drone Control Endpoints

- Require elevated permissions (operator role)
- Log all commands with timestamp and user
- Implement emergency abort endpoint
- Add confirmation for destructive operations (clear queue)
- Validate waypoint coordinates are within permitted operating area

---

## Performance Considerations

### Database Queries

Optimize route retrieval:
```python
# Use prefetch_related to avoid N+1 queries
Route.objects.all().prefetch_related("waypoints")
```

### Polling Strategy

Frontend should poll drone status judiciously:
- Status: Every 1 second (via WebSocket, not polling)
- Queue: On-demand only (user action)
- Don't poll mission-planner continuously

### Mission Upload Size

Limit mission size to prevent:
- UDP packet fragmentation
- Drone memory overflow
- Excessive processing time

Recommended: Max 200 waypoints per mission

---

## Debugging Tips

### Database Issues

```bash
# Check database state
docker exec -it gcom-db psql -U postgres -d gcom
SELECT * FROM nav_route;
SELECT * FROM nav_orderedwaypoint WHERE route_id = 1 ORDER BY "order";
```

### Mission-Planner Communication

```bash
# Check if mission-planner is running
curl http://localhost:9000/

# Get current queue
curl http://localhost:9000/queue

# Check mission-planner logs
docker logs gcom-mission-planner
```

### Drone Connection

```bash
# Check UDP communication
sudo tcpdump -i lo0 -n udp port 14550

# Monitor MAVLink messages
mavproxy.py --master=udp:127.0.0.1:14550
```

---

## Related Documentation

- [API Endpoints and Drone Control](./api-endpoints-and-drone-control.md)
- [PyMAVLink System Architecture](./pymavlink-system-architecture.md)
- Django REST Framework Documentation: https://www.django-rest-framework.org/
- MAVLink Protocol: https://mavlink.io/en/

---

## Appendix: Complete Example Workflow

### Planning and Executing a Survey Mission

**Step 1: Create Route in Database**
```bash
POST /api/route/
{
  "name": "Building_Survey_2024_01_15"
}

Response: { "id": 5, "name": "Building_Survey_2024_01_15", "waypoints": [] }
```

**Step 2: Add Waypoints**
```bash
POST /api/waypoint/
{
  "name": "Launch",
  "latitude": 49.2606,
  "longitude": -123.2460,
  "altitude": 0.0,
  "order": 0,
  "route": 5
}

POST /api/waypoint/
{
  "name": "Survey_Point_1",
  "latitude": 49.2620,
  "longitude": -123.2470,
  "altitude": 75.0,
  "order": 1,
  "route": 5
}

# ... add more waypoints
```

**Step 3: Load Route for Flight**
```bash
GET /api/route/5/

Response: {
  "id": 5,
  "name": "Building_Survey_2024_01_15",
  "waypoints": [
    {
      "id": "uuid-1",
      "name": "Launch",
      "latitude": 49.2606,
      "longitude": -123.2460,
      "altitude": 0.0,
      "order": 0
    },
    {
      "id": "uuid-2",
      "name": "Survey_Point_1",
      "latitude": 49.2620,
      "longitude": -123.2470,
      "altitude": 75.0,
      "order": 1
    }
  ]
}
```

**Step 4: Convert to Mission Format and Upload**
```bash
POST /api/drone/queue
[
  {
    "id": 1,
    "name": "Takeoff",
    "latitude": 49.2606,
    "longitude": -123.2460,
    "altitude": 50.0,
    "command": "TAKEOFF",
    "param1": 0, "param2": 0, "param3": 0, "param4": 0
  },
  {
    "id": 2,
    "name": "Survey_Point_1",
    "latitude": 49.2620,
    "longitude": -123.2470,
    "altitude": 75.0,
    "command": "WAYPOINT",
    "param1": 0, "param2": 0, "param3": 0, "param4": 0
  }
]

Response: 200 OK
```

**Step 5: Monitor Execution**
```bash
GET /api/drone/queue

Response: [
  # Returns remaining waypoints (excludes already passed)
]
```

**Step 6: After Flight**
- Mission data automatically stored in database via telemetry
- Route remains in database for future use
- Drone queue cleared on landing
